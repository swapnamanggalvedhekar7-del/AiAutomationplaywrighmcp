"""Central, environment-driven configuration. Nothing environment-specific is hard-coded elsewhere."""
from dataclasses import dataclass, field
from pathlib import Path

from utils.config_reader import get_bool, get_int, get_str, load_env_file

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_env_file(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    base_url: str = field(default_factory=lambda: get_str("BASE_URL", "https://pos.aksharatraining.in").rstrip("/"))

    # Valid account for TC_001. Secrets: supply via env / .env / CI secret store.
    username: str = field(default_factory=lambda: get_str("POS_USERNAME"))
    password: str = field(default_factory=lambda: get_str("POS_PASSWORD"))
    # Name the app displays for that account in the top bar.
    display_name: str = field(default_factory=lambda: get_str("POS_DISPLAY_NAME", "Student Demo"))

    action_timeout_ms: int = field(default_factory=lambda: get_int("ACTION_TIMEOUT_MS", 15_000))
    expect_timeout_ms: int = field(default_factory=lambda: get_int("EXPECT_TIMEOUT_MS", 10_000))
    viewport_width: int = field(default_factory=lambda: get_int("VIEWPORT_WIDTH", 1366))
    viewport_height: int = field(default_factory=lambda: get_int("VIEWPORT_HEIGHT", 768))
    # Video is recorded for every test but only kept when the test fails.
    record_video: bool = field(default_factory=lambda: get_bool("RECORD_VIDEO", True))

    artifacts_dir: Path = PROJECT_ROOT / "test-results"


settings = Settings()
