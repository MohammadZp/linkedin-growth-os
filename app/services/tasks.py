from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.database.models import Task
from app.domain.enums import TaskSource
from app.repositories.tasks import TaskRepository
from app.services.time import now_utc


class TaskService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = TaskRepository(session)

    def create(
        self,
        *,
        title: str,
        due_date: date | None = None,
        priority: int = 2,
        description: str | None = None,
        source: TaskSource = TaskSource.MANUAL,
    ) -> Task:
        task = Task(
            title=title.strip(),
            due_date=due_date,
            priority=priority,
            description=description,
            source=source,
            completed=False,
        )
        self.repo.add(task)
        self.session.flush()
        return task

    def complete(self, task: Task) -> None:
        task.completed = True
        task.completed_at = now_utc()
        self.session.flush()

    def reopen(self, task: Task) -> None:
        task.completed = False
        task.completed_at = None
        self.session.flush()

    def delete(self, task: Task) -> None:
        self.repo.delete(task)
        self.session.flush()

    def top_tasks(self, due_date: date, limit: int) -> list[Task]:
        return self.repo.list_for_date(due_date)[:limit]
