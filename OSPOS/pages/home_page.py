import re

import allure
from playwright.sync_api import Page, expect


class HomePage:
    URL = re.compile(r"/home/?$")

    def __init__(self, page: Page):
        self.page = page
        # The dashboard body repeats the module names as links, so scope to the top
        # navigation's list; that also excludes the "OSPOS" brand link outside the list.
        self.module_links = page.get_by_role("navigation").get_by_role("list").get_by_role("link")
        self.logout_link = page.get_by_role("link", name="Logout", exact=True)
        # "<user> | Logout" block: no role/label of its own and `.navbar-right` is also on the
        # module list, so narrow it to the one containing the Logout link (verified unique).
        self.user_bar = page.locator(".navbar-right").filter(has=self.logout_link)

    @allure.step("Verify the Home dashboard is loaded")
    def expect_loaded(self) -> None:
        expect(self.page).to_have_url(self.URL)

    @allure.step("Verify navigation bar modules")
    def expect_modules(self, modules: list[str]) -> None:
        # Exact list, in order.
        expect(self.module_links).to_have_text(modules)

    @allure.step("Verify page title starts with '{prefix}'")
    def expect_title_starts_with(self, prefix: str) -> None:
        expect(self.page).to_have_title(re.compile(rf"^{re.escape(prefix)}"))

    @allure.step("Verify '{display_name} | Logout' is visible")
    def expect_user_bar(self, display_name: str) -> None:
        expect(self.user_bar).to_be_visible()
        expect(self.user_bar).to_have_text(f"{display_name} | Logout")
