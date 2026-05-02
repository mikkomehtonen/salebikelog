"""Validated application configuration."""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings validated at startup."""

    db_path: str | None = None
    lm_studio_url: str = "http://localhost:1234/v1"
    lm_studio_model: str = "qwen/qwen3.6-35b-a3b"
    log_level: str = "INFO"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is a recognized value."""
        allowed: set[str] = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            msg = f"log_level must be one of {allowed}, got {v!r}"
            raise ValueError(msg)
        return upper

    model_config = {"env_prefix": "", "case_sensitive": False}

    @property
    def upload_dir(self) -> Path:
        """Return the uploads directory path."""
        base = Path(__file__).resolve().parent.parent.parent
        return base / "uploads"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


def reset_settings() -> None:
    """Clear cached settings. Used in tests to pick up new env vars."""
    get_settings.cache_clear()


# Module-level compatibility shims for existing imports
_BASE_DIR = Path(__file__).resolve().parent.parent
_UPLOAD_DIR = _BASE_DIR.parent / "uploads"
_UPLOAD_DIR.mkdir(exist_ok=True)

_DB_PATH = os.environ.get("DB_PATH", str(_BASE_DIR / "database/trips.db"))
_LM_STUDIO_URL = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1")
_LM_STUDIO_MODEL = os.environ.get("LM_STUDIO_MODEL", "qwen/qwen3.6-35b-a3b")


def __getattr__(name: str) -> Path | str:
    """Backward-compatible access to legacy module-level constants."""
    if name == "BASE_DIR":
        return _BASE_DIR
    if name == "UPLOAD_DIR":
        return _UPLOAD_DIR
    if name == "DB_PATH":
        return _DB_PATH
    if name == "LM_STUDIO_URL":
        return _LM_STUDIO_URL
    if name == "LM_STUDIO_MODEL":
        return _LM_STUDIO_MODEL
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
