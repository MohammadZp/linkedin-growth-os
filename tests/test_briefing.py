from __future__ import annotations

from app.config import Settings
from app.database.models import ContentItem, Task
from app.domain.enums import ContentStatus, ContentType
from app.services.briefing import build_daily_briefing, build_weekly_summary
from app.services.time import local_date, now_utc
from sqlalchemy.orm import Session


def test_daily_briefing_limits_to_max_tasks(session: Session) -> None:
    settings = Settings(_env_file=None)
    today = local_date()
    for i in range(5):
        session.add(Task(title=f"task {i}", due_date=today))
    session.commit()

    text = build_daily_briefing(session, settings)
    assert "task 0" in text
    assert "task 3" not in text  # limited by max_daily_tasks=3


def test_daily_briefing_empty_is_friendly(session: Session) -> None:
    text = build_daily_briefing(session, Settings(_env_file=None))
    assert "روز سبکی شروع کن" in text


def test_weekly_summary_counts_this_week(session: Session) -> None:
    settings = Settings(_env_file=None)
    session.add(Task(title="done", due_date=local_date(), completed=True, completed_at=now_utc()))
    session.add(
        ContentItem(
            title="published post",
            content_type=ContentType.EDUCATIONAL_POST,
            pillar="educational_post",
            status=ContentStatus.PUBLISHED,
            actual_publish_at=now_utc(),
        )
    )
    session.commit()

    text = build_weekly_summary(session, settings)
    assert "منتشرشده این هفته: 1" in text
    assert "تکمیل‌شده این هفته: 1" in text
