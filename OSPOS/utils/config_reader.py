"""Read typed settings from environment variables, with an optional `.env` file.

Real environment variables (e.g. CI secrets) always take precedence over `.env`.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}


def load_env_file(path: Path) -> None:
    load_dotenv(path, override=False)


def get_str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"Environment variable {name} must be an integer, got {raw!r}") from None


def get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    value = raw.strip().lower()
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    raise ValueError(f"Environment variable {name} must be a boolean (true/false), got {raw!r}")
