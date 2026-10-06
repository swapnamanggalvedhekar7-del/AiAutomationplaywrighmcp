import re

import allure
from playwright.sync_api import Page, expect

from utils.logger import get_logger

logger = get_logger(__name__)


class LoginPage:
    # `/login` redirects to the app entry point `/public/`; the form posts to
    # `/public/login`, which is where the page re-renders after a rejected attempt.
    PATH = "/login"
    SUBMITTED_URL = re.compile(r"/login$")
    DASHBOARD_URL = re.compile(r"/home/?$")

    def __init__(self, page: Page):
        self.page = page
        self.heading = page.get_by_role("heading", name="Welcome to OSPOS!")
        # Inputs have real <label for=...> elements, so their accessible names are stable.
        # Role locators also skip the hidden anti-bot "honeypot" input on this form.
        self.username_input = page.get_by_role("textbox", name="Username", exact=True)
        self.password_input = page.get_by_role("textbox", name="Password", exact=True)
        self.go_button = page.get_by_role("button", name="Go", exact=True)
        # Server-rendered Bootstrap alert with no ARIA role, label or test id - CSS is the
        # most specific option that still targets the error container (not any text match).
        self.error_alert = page.locator(".alert-danger")

    @allure.step("Open the login page")
    def open(self) -> "LoginPage":
        logger.info("Opening %s", self.PATH)
        self.page.goto(self.PATH)
        self.expect_displayed()
        return self

    @allure.step("Log in with username '{username}'")
    def login(self, username: str, password: str) -> None:
        # Never log the password.
        logger.info("Submitting login form, username=%r", username)
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.go_button.click()

    def expect_displayed(self) -> None:
        expect(self.heading).to_be_visible()
        expect(self.username_input).to_be_visible()
        expect(self.password_input).to_be_visible()
        expect(self.go_button).to_be_visible()

    @allure.step("Verify error message: '{message}'")
    def expect_error(self, message: str) -> None:
        expect(self.error_alert).to_have_text(message)

    @allure.step("Verify the user is still on the login page and not on the dashboard")
    def expect_still_on_login_page(self) -> None:
        expect(self.page).to_have_url(self.SUBMITTED_URL)
        expect(self.page).not_to_have_url(self.DASHBOARD_URL)
        self.expect_displayed()

    @allure.step("Verify username and password fields are empty")
    def expect_fields_empty(self) -> None:
        expect(self.username_input).to_have_value("")
        expect(self.password_input).to_have_value("")
