from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.database.models import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    model = Task

    def list_for_date(self, due_date: date) -> list[Task]:
        stmt = (
            select(Task)
            .where(Task.due_date == due_date)
            .order_by(Task.priority.asc(), Task.id.asc())
        )
        return list(self.session.scalars(stmt).all())

    def list_open(self, *, on_or_before: date | None = None) -> list[Task]:
        stmt = select(Task).where(Task.completed.is_(False))
        if on_or_before is not None:
            stmt = stmt.where(Task.due_date <= on_or_before)
        stmt = stmt.order_by(Task.priority.asc(), Task.due_date.asc())
        return list(self.session.scalars(stmt).all())

    def list_overdue(self, today: date) -> list[Task]:
        stmt = (
            select(Task)
            .where(Task.completed.is_(False), Task.due_date.is_not(None), Task.due_date < today)
            .order_by(Task.due_date.asc())
        )
        return list(self.session.scalars(stmt).all())

    def count_completed_between(self, start: date, end: date) -> int:
        stmt = select(Task).where(
            Task.completed.is_(True), Task.completed_at >= start, Task.completed_at < end
        )
        return len(list(self.session.scalars(stmt).all()))

    def list_completed(self, *, limit: int | None = None) -> list[Task]:
        stmt = select(Task).where(Task.completed.is_(True)).order_by(Task.completed_at.desc())
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt).all())
