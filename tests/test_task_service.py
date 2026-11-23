from __future__ import annotations

from datetime import date

from app.services.tasks import TaskService
from sqlalchemy.orm import Session


def test_create_task(session: Session) -> None:
    task = TaskService(session).create(title="Draft hook", due_date=date(2026, 11, 24), priority=1)
    assert task.id is not None
    assert task.completed is False
    assert task.priority == 1


def test_complete_and_reopen(session: Session) -> None:
    svc = TaskService(session)
    task = svc.create(title="x")
    svc.complete(task)
    assert task.completed is True
    assert task.completed_at is not None

    svc.reopen(task)
    assert task.completed is False
    assert task.completed_at is None


def test_top_tasks_limits(session: Session) -> None:
    svc = TaskService(session)
    for i in range(5):
        svc.create(title=f"t{i}", due_date=date(2026, 11, 24))
    top = svc.top_tasks(date(2026, 11, 24), 3)
    assert len(top) == 3
