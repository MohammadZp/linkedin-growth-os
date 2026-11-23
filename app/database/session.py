from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def ensure_sqlite_parent_dir(database_url: str) -> None:
    """Create the parent directory for a file-based SQLite database, if needed."""
    if not database_url.startswith("sqlite"):
        return
    db_path = make_url(database_url).database
    if db_path and db_path not in ("", ":memory:"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args: dict = {}
        if settings.database_url.startswith("sqlite"):
            # SQLite is used across threads (aiogram handlers + APScheduler).
            connect_args = {"check_same_thread": False}
            ensure_sqlite_parent_dir(settings.database_url)
        _engine = create_engine(settings.database_url, connect_args=connect_args)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
    return _session_factory


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a transactional session that commits on success and rolls back on error."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create all tables if they do not yet exist (safe on an empty database)."""
    from app.database import models  # noqa: F401  (register models on Base.metadata)
    from app.database.base import Base

    Base.metadata.create_all(get_engine())
