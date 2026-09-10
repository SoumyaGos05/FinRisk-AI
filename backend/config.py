"""
Application configuration.

All settings are loaded from the .env file (or environment variables).
This is the ONLY module that reads from os.environ / .env — everywhere else
imports the `settings` singleton from here.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env."""

    DATABASE_URL: str
    APP_ENV: str = "development"

    # ---------------------------------------------------------------------------
    # AI Explanation Engine — Google Gemini (optional)
    # ---------------------------------------------------------------------------
    # Leave GEMINI_API_KEY unset or empty to disable AI explanations entirely.
    # The deterministic financial engine always works without these settings.
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.6-flash"
    AI_TIMEOUT_SECONDS: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Module-level singleton — import this everywhere you need a setting.
settings = Settings()
