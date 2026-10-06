"""Shared fixtures and hooks.

pytest-playwright provides the `playwright` and `browser` (session-scoped) and `page`
fixtures, plus --browser / --headed / --slowmo. This file adds:

* `base_url`            - from config, overridable with --base-url
* `context` (override)  - a fresh, isolated context per test with tracing (and video);
                          on failure a screenshot, trace and video are kept in
                          test-results/<test>/ and attached to Allure. Passing tests keep nothing.
* page-object fixtures and the valid-credentials fixture.

A fresh context per test matters: an authenticated session makes /login redirect
straight to /home, which would leak state between tests.
"""
import re
import shutil
from pathlib import Path

import allure
import pytest
from playwright.sync_api import Browser, BrowserContext, Page, expect

from config.config import settings
from pages.home_page import HomePage
from pages.login_page import LoginPage
from test_data.login_data import Credentials
from utils.logger import get_logger

logger = get_logger(__name__)


def pytest_configure(config: pytest.Config) -> None:
    expect.set_options(timeout=settings.expect_timeout_ms)


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_makereport(item: pytest.Item, call):
    # Store each phase's report (rep_setup / rep_call) on the item so fixtures can see the outcome.
    report = yield
    setattr(item, f"rep_{report.when}", report)
    return report


def pytest_sessionfinish(session: pytest.Session) -> None:
    """Write Allure's environment widget data."""
    alluredir = session.config.getoption("allure_report_dir", default=None)
    if not alluredir or not Path(alluredir).is_dir():
        return
    env = {
        "Base.URL": session.config.getoption("base_url", default=None) or settings.base_url,
        "Browser": ",".join(session.config.getoption("browser", default=None) or ["chromium"]),
        "Headed": session.config.getoption("headed", default=False),
    }
    (Path(alluredir) / "environment.properties").write_text(
        "".join(f"{k}={v}\n" for k, v in env.items()), encoding="utf-8"
    )


def _failed(item: pytest.Item) -> bool:
    return any(getattr(getattr(item, f"rep_{phase}", None), "failed", False) for phase in ("setup", "call"))


@pytest.fixture(scope="session")
def base_url(pytestconfig: pytest.Config) -> str:
    # CLI --base-url (pytest-base-url) wins over BASE_URL from env/.env.
    return pytestconfig.getoption("base_url", default=None) or settings.base_url


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    # pytest-playwright already injects base_url from the `base_url` fixture.
    return {
        **browser_context_args,
        "viewport": {"width": settings.viewport_width, "height": settings.viewport_height},
    }


@pytest.fixture
def context(browser: Browser, browser_context_args: dict, request: pytest.FixtureRequest) -> BrowserContext:
    artifacts_dir = settings.artifacts_dir / re.sub(r"[^\w.-]+", "_", request.node.nodeid)
    context_args = dict(browser_context_args)
    if settings.record_video:
        context_args["record_video_dir"] = str(artifacts_dir / "video")

    ctx = browser.new_context(**context_args)
    ctx.set_default_timeout(settings.action_timeout_ms)
    ctx.set_default_navigation_timeout(settings.action_timeout_ms)
    ctx.tracing.start(title=request.node.nodeid, screenshots=True, snapshots=True, sources=True)

    yield ctx

    failed = _failed(request.node)
    pages = list(ctx.pages)

    if failed:
        logger.error("Test failed - saving screenshot, trace and video to %s", artifacts_dir)
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        for index, pg in enumerate(pages):
            shot = artifacts_dir / f"failure-screenshot-{index}.png"
            try:
                pg.screenshot(path=shot, full_page=True)
                allure.attach.file(shot, name=f"failure-screenshot-{index}", attachment_type=allure.attachment_type.PNG)
            except Exception:
                # Cleanup path: a crashed/closed page must not replace the real test failure,
                # so log and continue instead of re-raising.
                logger.exception("Could not capture failure screenshot")
        trace = artifacts_dir / "trace.zip"
        ctx.tracing.stop(path=trace)
        allure.attach.file(trace, name="playwright-trace.zip (playwright show-trace <file>)", extension="zip")
    else:
        ctx.tracing.stop()

    ctx.close()  # finalises video files

    if failed:
        for pg in pages:
            if pg.video:
                allure.attach.file(pg.video.path(), name="video", attachment_type=allure.attachment_type.WEBM)
    else:
        shutil.rmtree(artifacts_dir, ignore_errors=True)


@pytest.fixture
def login_page(page: Page) -> LoginPage:
    return LoginPage(page)


@pytest.fixture
def home_page(page: Page) -> HomePage:
    return HomePage(page)


@pytest.fixture(scope="session")
def valid_credentials() -> Credentials:
    if not (settings.username and settings.password):
        pytest.fail(
            "Valid credentials are not configured. Set POS_USERNAME and POS_PASSWORD "
            "as environment variables or in .env (see .env.example).",
            pytrace=False,
        )
    return Credentials(settings.username, settings.password)
