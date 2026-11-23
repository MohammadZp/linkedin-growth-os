from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.base import Base


class BaseRepository[ModelT: Base]:
    """Generic CRUD repository. Subclasses set ``model`` and add domain queries."""

    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        return obj

    def get(self, obj_id: int) -> ModelT | None:
        return self.session.get(self.model, obj_id)

    def list_all(self, *, limit: int | None = None, offset: int = 0) -> Sequence[ModelT]:
        stmt = select(self.model).order_by(self.model.id.desc())
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset)
        return self.session.scalars(stmt).all()

    def count(self) -> int:
        return self.session.scalar(select(func.count()).select_from(self.model)) or 0

    def delete(self, obj: ModelT) -> None:
        self.session.delete(obj)

    def flush(self) -> None:
        self.session.flush()
