from __future__ import annotations

from app.config import Settings
from app.database.models import Contact, ContentItem, Task
from app.domain.enums import ContentStatus, ContentType
from app.services.analytics import AnalyticsService
from app.services.review import build_weekly_review
from app.services.time import local_date, now_utc
from sqlalchemy.orm import Session


def test_review_has_nine_sections_and_labels(session: Session) -> None:
    session.add(Task(title="done", due_date=local_date(), completed=True, completed_at=now_utc()))
    item = ContentItem(
        title="post",
        content_type=ContentType.TOOL_EXPERIMENT,
        pillar="tool_experiment",
        status=ContentStatus.PUBLISHED,
        actual_publish_at=now_utc(),
    )
    session.add(item)
    session.flush()
    AnalyticsService(session).record(
        item.id, local_date(), metrics={"impressions": 100, "qualified_conversations": 1}
    )
    session.add(Contact(name="Jane"))
    session.commit()

    text = build_weekly_review(session, Settings(_env_file=None))
    for marker in ("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"):
        assert marker in text
    assert "مشاهده" in text
    assert "فرضیه" in text


def test_review_handles_empty_database(session: Session) -> None:
    text = build_weekly_review(session, Settings(_env_file=None))
    assert "1️⃣" in text
    assert "هیچ محتوایی منتشر نشده" in text
