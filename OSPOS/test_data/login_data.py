"""Test data for TC_001 - TC_003.

Valid credentials are secrets and come from config (env / .env / CI secrets), not from here.
Expected texts are exactly what the application shows (verified with Playwright MCP).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Credentials:
    username: str
    password: str


# TC_002
INVALID_CREDENTIALS = Credentials(username="wronguser", password="wrongpass")
INVALID_CREDENTIALS_MESSAGE = "Invalid username and/or password."

# TC_003
EMPTY_CREDENTIALS = Credentials(username="", password="")
USERNAME_REQUIRED_MESSAGE = "The username field is required."

# TC_001
APP_TITLE = "Open Source Point of Sale"
HOME_NAV_MODULES = [
    "Home",
    "Items",
    "Item Kits",
    "Suppliers",
    "Reports",
    "Receivings",
    "Gift Cards",
]
