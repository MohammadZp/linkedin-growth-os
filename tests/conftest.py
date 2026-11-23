from __future__ import annotations

import pytest
from app.database import models  # noqa: F401  (register models on Base.metadata)
from app.database.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def session() -> Session:
    """In-memory SQLite session with a fresh schema per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    s = factory()
    try:
        yield s
    finally:
        s.close()
        engine.dispose()
