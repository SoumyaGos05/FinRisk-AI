"""
Database session factory.

Provides the SQLAlchemy engine, session factory, and the FastAPI dependency
`get_db` that should be injected via `Depends(get_db)` in route handlers.

The engine is constructed from `settings.DATABASE_URL` — this is the only
value that needs to change when moving from SQLite to PostgreSQL.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.config import settings

# connect_args is only needed for SQLite (disables the same-thread check).
# It is harmless to remove it when switching to PostgreSQL.
_connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.

    Usage in a route:
        def my_route(db: Session = Depends(get_db)): ...

    The session is always closed after the request, even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
