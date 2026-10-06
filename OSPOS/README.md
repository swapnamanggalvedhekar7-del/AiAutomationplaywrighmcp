# OSPOS Login – Playwright Python Test Automation Framework

UI automation for the login feature of Open Source Point of Sale (<https://pos.aksharatraining.in/login>).
It uses Python, Playwright, Pytest, the Page Object Model and Allure.

Locators and expected behaviour come from inspecting the live application with **Playwright MCP**: the accessibility tree, the DOM, the form attributes, and a manual run of TC_001–TC_003 in the browser. They were not guessed.

## Project structure

```text
OSPOS/
├── config/
│   └── config.py            # Settings: URL, credentials, timeouts, viewport, video (env-driven)
├── pages/
│   ├── login_page.py        # Login form: locators, actions, page-level assertions
│   └── home_page.py         # Dashboard: navigation, title, user bar
├── test_data/
│   └── login_data.py        # Non-secret test data + exact expected messages
├── tests/
│   └── test_login.py        # TC_001 – TC_003
├── utils/
│   ├── config_reader.py     # .env loading + typed env readers (str/int/bool, with clear errors)
│   └── logger.py            # Named loggers under the `ospos` namespace
├── conftest.py              # Fixtures, per-test context, failure artifacts, Allure hooks
├── pytest.ini               # Markers, logging, Allure output
├── requirements.txt
├── .env.example             # Template for local configuration (.env is git-ignored)
├── .github/workflows/ui-tests.yml
├── Jenkinsfile
└── .gitignore
```

## Traceability

| Manual TC | Automated test | Expected results covered |
|---|---|---|
| TC_001 Successful login | `test_tc001_login_with_valid_credentials` | ER1 hard; ER2–ER4 soft |
| TC_002 Invalid credentials | `test_tc002_login_with_invalid_credentials` | ER1–ER4 |
| TC_003 Empty credentials | `test_tc003_login_with_empty_credentials` | ER2: the error message "The username field is required." is shown |

The test code marks each assertion with its ER number. In Allure, every test has the ID `TC_00x` and a title that matches its manual case.

## Installation

You need Python 3.10 or later.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
playwright install                     # or just: playwright install chromium
cp .env.example .env                   # then fill in POS_USERNAME / POS_PASSWORD
```

**Allure CLI (separate, not installed by pip).** It is only needed to *view* reports, and it requires Java 8 or later.
Install it with one of `scoop install allure` (Windows), `brew install allure` (macOS) or `npm install -g allure-commandline`.

## Configuration

All values are read in `config/config.py`. They come from environment variables, or from `.env` if they aren't set. Real environment variables always win over `.env`.

| Variable | Default | Purpose |
|---|---|---|
| `BASE_URL` | `https://pos.aksharatraining.in` | Application host. Can also be set with `--base-url` |
| `POS_USERNAME` / `POS_PASSWORD` | *(required for TC_001)* | Valid account. These are secrets |
| `POS_DISPLAY_NAME` | `Student Demo` | Name the app shows for that account |
| `ACTION_TIMEOUT_MS` | `15000` | Action and navigation timeout |
| `EXPECT_TIMEOUT_MS` | `10000` | `expect()` assertion timeout |
| `VIEWPORT_WIDTH` / `VIEWPORT_HEIGHT` | `1366` / `768` | Browser viewport |
| `RECORD_VIDEO` | `true` | Record video and keep it for failed tests only |

If the credentials are missing, TC_001 errors at setup with a message that says how to fix it.

## Running tests

```bash
pytest                                   # all tests, headless Chromium (Allure results always written)
pytest -m smoke                          # by marker: smoke | login | negative
pytest -k tc002                          # a single test
pytest --headed --slowmo 500             # watch the browser
pytest --browser firefox --browser webkit   # cross-browser (playwright install those first)
pytest --base-url https://other-host     # different environment
pytest -o log_cli=true                   # stream logs to the console
```

**IDEs:** both PyCharm and VS Code (Python extension → Testing) pick up `pytest.ini` from the project root. Select the `.venv` interpreter and run or debug the tests from the gutter.

## Reports and debugging artifacts

- **Allure results:** each run writes them to `allure-results/` and cleans the previous results first (set in `pytest.ini`). To view them:
  ```bash
  allure serve allure-results                                   # temporary report in the browser
  allure generate allure-results -o allure-report --clean       # static report
  allure open allure-report
  ```
  The report shows status, TC ID and title, steps, the failure message, and the test's log. It also includes an environment widget with the base URL and browser.
- **When a test fails:** the framework saves a full-page screenshot, a Playwright trace and a video to `test-results/<test-id>/`. They are attached to the Allure test under **Tear down → context**, because they are collected when the browser context closes. Passing tests keep no artifacts.
- **Trace Viewer:** run `playwright show-trace test-results/<test-id>/trace.zip`, or drop the file onto <https://trace.playwright.dev>.
- **Logs:** the whole run goes to `logs/test_run.log`. Each test's log is also attached in Allure and printed for failed tests. Passwords are never logged.

## CI/CD

- **GitHub Actions:** [`.github/workflows/ui-tests.yml`](.github/workflows/ui-tests.yml). Add the repository secrets `POS_USERNAME` and `POS_PASSWORD`. You can also set the repository variables `BASE_URL` and `POS_DISPLAY_NAME`. The workflow uploads the Allure results, failure artifacts and logs as one build artifact.
- **Jenkins:** [`Jenkinsfile`](Jenkinsfile). It needs the Allure Jenkins plugin and a *Username with password* credential with the ID `ospos-login`.
- **Any other CI:**
  ```bash
  pip install -r requirements.txt && playwright install --with-deps chromium && pytest --browser chromium
  ```

## Architecture and design decisions

- **Layers:** tests contain the business flow and the ER checks. Page objects hold the locators, actions and page-level assertions. `config` and `utils` hold settings and plumbing. Each layer changes for a single reason, which is why there is no `BasePage` or other abstraction: two small pages don't need one.
- **Fixtures:** pytest-playwright provides `playwright` and `browser` (session scope) and `page`. This project overrides `base_url` (from config, or the CLI) and `context`. Every test gets a **fresh isolated context**, because MCP inspection showed that a logged-in session makes `/login` redirect straight to `/home`, which would leak state between tests. The page-object fixtures are function-scoped. `valid_credentials` is session-scoped and checks once that the credentials exist.
- **No login/session fixture yet:** these tests check login itself. When tests for other modules are added, log in once and reuse Playwright's `storage_state`.
- **Locators (verified unique with MCP):**
  - Inputs and button: `get_by_role` with an exact name, since the inputs have real `<label for>` elements. Role locators also ignore the form's hidden anti-bot "honeypot" input.
  - Navigation: `navigation → list → link`. The dashboard body repeats every module name as a link, and the "OSPOS" brand link sits outside the list.
  - Error message: CSS `.alert-danger`. The alert has no role, label or test ID, and the class targets the error container rather than matching text anywhere on the page.
  - User bar: `.navbar-right` filtered to the one that contains the Logout link, because the module list also carries that class.
  - No XPath, `nth()` or sleeps anywhere.
- **Assertions:** all are auto-waiting `expect()` calls. TC_001 ER1, the redirect, is a hard assertion. ER2–ER4 are soft assertions (`pytest-check`), so one run reports every mismatch. In TC_002 the error message is asserted *first*, because it only exists on the server's response page. That makes the URL checks run after the round trip instead of passing early on the original page. TC_003 asserts only the error message, by decision of the test owner.
- **Test data:** three scenarios fit in plain constants. For more credential combinations, use `@pytest.mark.parametrize`, and switch to a CSV/JSON-driven loader only once the dataset grows. Valid credentials stay out of the code and come from env, `.env` or CI secrets.
- **Error handling:** failures propagate naturally. The only `try/except` is around the failure screenshot during teardown, where it logs the problem and continues so a closed page can't replace the real failure.
- **Artifacts:** tracing and video run for every test but are kept **only on failure**. Playwright can't decide in advance which tests will fail.
- **Retries:** none are configured, so flaky behaviour is never hidden. If a real infrastructure issue requires retries, add `pytest-rerunfailures`. Each failed attempt then still produces its own artifacts.
- **Known deviations:** these are not handled by self-healing. They are reported explicitly (see below).

## Known deviations: manual test cases vs. live application

These were observed with Playwright MCP on 2026-10-06 (OSPOS 3.4.1). The tests assert the real behaviour, and each deviation is marked in the code with its ID.

| ID | TC / ER | Manual expectation | Actual behaviour | How the test handles it |
|---|---|---|---|---|
| D1 | TC_001 ER1 | Redirect to `/home` | `/login` → `/public/` → after login `/public/home` | The URL is matched on `/home` at the end |
| D2 | TC_001 ER3 | Title is `Open Source Point of Sale` | `Open Source Point of Sale \| Powered by OSPOS 3.4.1` | The title is checked as a **prefix** |
| D3 | TC_003 ER1 | Form submission is prevented | The inputs have no `required` attribute, so the browser **submits** the empty form and the server replies "The username field is required." | By decision of the test owner, TC_003 asserts only the error message. ER1 (submission prevented) and ER3 (stays on the login page) are not automated |
| D4 | TC_002 ER3 | Fields cleared *or* highlighted | Both fields are **cleared**, with no highlighting | Asserts that both fields are empty |

D3 is the one worth raising with the product owner: it may be a defect or a design choice. The other deviations are cosmetic or covered by the "based on actual behaviour" wording in the test cases.
