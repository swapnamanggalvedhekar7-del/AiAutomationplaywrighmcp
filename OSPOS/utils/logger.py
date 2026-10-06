"""Project logger factory.

Handlers and formats are owned by pytest (see `log_*` options in pytest.ini), so the
same records reach the console (`-o log_cli=true`), `logs/test_run.log` and the
per-test "log" attachment in Allure. Framework code only needs a named logger under
one `ospos` namespace, which makes it easy to filter or raise its level in one place.
"""
import logging

ROOT_LOGGER_NAME = "ospos"


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")
