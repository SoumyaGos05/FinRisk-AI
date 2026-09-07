"""
Application configuration.

All settings are loaded from the .env file (or environment variables).
This is the ONLY module that reads from os.environ / .env — everywhere else
imports the `settings` singleton from here.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env."""

    DATABASE_URL: str
    APP_ENV: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Module-level singleton — import this everywhere you need a setting.
settings = Settings()
