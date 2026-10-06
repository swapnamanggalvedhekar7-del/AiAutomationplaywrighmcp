"""Login feature: manual test cases TC_001 - TC_003 (https://pos.aksharatraining.in/login).

Expected results (ER) are referenced by number so each assertion traces back to the
manual test case. Deviations between the manual ERs and the live application are listed
in README.md -> "Known deviations" (D1-D4).
"""
import allure
import pytest
from pytest_check import check

from config.config import settings
from pages.home_page import HomePage
from pages.login_page import LoginPage
from test_data.login_data import (
    APP_TITLE,
    EMPTY_CREDENTIALS,
    HOME_NAV_MODULES,
    INVALID_CREDENTIALS,
    INVALID_CREDENTIALS_MESSAGE,
    USERNAME_REQUIRED_MESSAGE,
    Credentials,
)

pytestmark = [pytest.mark.login, allure.epic("OSPOS"), allure.feature("Login")]


@pytest.mark.smoke
@allure.id("TC_001")
@allure.title("TC_001 - Successful login with valid credentials")
@allure.severity(allure.severity_level.BLOCKER)
def test_tc001_login_with_valid_credentials(
    login_page: LoginPage, home_page: HomePage, valid_credentials: Credentials
):
    login_page.open()
    login_page.login(valid_credentials.username, valid_credentials.password)

    # ER1 - hard: every other check is meaningless if the dashboard did not load. (D1)
    home_page.expect_loaded()

    # ER2-ER4 are independent of each other: soft-assert so one run reports every mismatch.
    with check:
        home_page.expect_modules(HOME_NAV_MODULES)  # ER2
    with check:
        home_page.expect_title_starts_with(APP_TITLE)  # ER3 (D2)
    with check:
        home_page.expect_user_bar(settings.display_name)  # ER4


@pytest.mark.negative
@allure.id("TC_002")
@allure.title("TC_002 - Login fails with invalid credentials")
@allure.severity(allure.severity_level.CRITICAL)
def test_tc002_login_with_invalid_credentials(login_page: LoginPage):
    login_page.open()
    login_page.login(INVALID_CREDENTIALS.username, INVALID_CREDENTIALS.password)

    # ER2 first: the alert only exists on the server's response page, so waiting for it
    # guarantees the URL checks below run after the form round-trip, not before it.
    login_page.expect_error(INVALID_CREDENTIALS_MESSAGE)
    login_page.expect_still_on_login_page()  # ER1 + ER4
    login_page.expect_fields_empty()  # ER3 - the app clears both fields (no highlighting)


@pytest.mark.negative
@allure.id("TC_003")
@allure.title("TC_003 - Login with empty credentials shows a validation error")
@allure.severity(allure.severity_level.NORMAL)
def test_tc003_login_with_empty_credentials(login_page: LoginPage):
    login_page.open()
    login_page.login(EMPTY_CREDENTIALS.username, EMPTY_CREDENTIALS.password)

    # Validation is server-side, so the error message is the check for this case (D3).
    login_page.expect_error(USERNAME_REQUIRED_MESSAGE)
