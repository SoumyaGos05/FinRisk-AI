"""
Shared pytest fixtures.

- Overrides DATABASE_URL to use an in-memory SQLite database so tests
  never touch the real finrisk.db file.
- Provides a `client` fixture backed by FastAPI's TestClient (no live server).
"""

import os

import pytest
from fastapi.testclient import TestClient

# Override DATABASE_URL before the app (and its engine) is imported.
# pydantic-settings reads env vars at import time, so the override must
# happen before `backend.main` is first imported.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from backend.main import app  # noqa: E402 — must come after env override


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    Return a TestClient for the FastAPI app.

    The session scope means the app (and its in-memory DB) is created once
    for the entire test run, which is fast and sufficient for unit/API tests.
    """
    with TestClient(app) as c:
        yield c
