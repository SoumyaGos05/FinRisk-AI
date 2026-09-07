"""
SQLAlchemy ORM base and declarative models.

All ORM table definitions import `Base` from here and extend it.
`Base.metadata.create_all(bind=engine)` is called once at application
startup in `backend/main.py` — not here.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""

    pass
