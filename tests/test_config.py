"""
Configuration unit tests.

Verifies that the Settings model loads correctly from the environment.
The DATABASE_URL override in conftest.py ensures these tests run offline
against a known value.
"""

from backend.config import settings


def test_settings_database_url_is_set() -> None:
    """DATABASE_URL must be a non-empty string."""
    assert isinstance(settings.DATABASE_URL, str)
    assert len(settings.DATABASE_URL) > 0


def test_settings_app_env_has_default() -> None:
    """APP_ENV should always have a value (default: 'development')."""
    assert settings.APP_ENV in {"development", "production", "test"}
