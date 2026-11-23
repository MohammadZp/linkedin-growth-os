from __future__ import annotations

from datetime import UTC, date, datetime

from app.database.models import AppSetting, Contact, ContentItem, Idea, PostAnalytics, Task
from app.domain.enums import ContentStatus, ContentType, IdeaStatus
from sqlalchemy import text
from sqlalchemy.orm import Session


def test_content_item_roundtrip(session: Session) -> None:
    item = ContentItem(
        title="FastAPI dependency injection deep dive",
        content_type=ContentType.OPEN_SOURCE_ANALYSIS,
        pillar="open_source_deep_dive",
        status=ContentStatus.DRAFTING,
    )
    session.add(item)
    session.commit()
    session.refresh(item)

    assert item.id is not None
    assert item.status is ContentStatus.DRAFTING
    assert item.working_language == "en"
    assert item.created_at is not None


def test_enum_stored_as_value_string(session: Session) -> None:
    item = ContentItem(
        title="x", content_type=ContentType.TOOL_EXPERIMENT, pillar="tool_experiment"
    )
    session.add(item)
    session.commit()
    raw = session.execute(
        text("SELECT content_type FROM content_items WHERE id = :id"), {"id": item.id}
    ).scalar()
    assert raw == "tool_experiment"


def test_idea_with_scores(session: Session) -> None:
    idea = Idea(
        title="Instrument an OSS project with tracing",
        status=IdeaStatus.INBOX,
        audience_relevance=4,
        demonstrability=5,
        technical_depth=4,
        business_relevance=3,
        effort_required=2,
        priority_score=3.7,
    )
    session.add(idea)
    session.commit()
    session.refresh(idea)
    assert idea.priority_score == 3.7


def test_post_analytics_unique_snapshot(session: Session) -> None:
    item = ContentItem(
        title="post", content_type=ContentType.EDUCATIONAL_POST, pillar="educational_post"
    )
    session.add(item)
    session.flush()

    a1 = PostAnalytics(content_item_id=item.id, recorded_at=date(2026, 11, 23), impressions=100)
    session.add(a1)
    session.commit()
    assert a1.id is not None

    a2 = PostAnalytics(content_item_id=item.id, recorded_at=date(2026, 11, 23), impressions=120)
    session.add(a2)
    try:
        session.commit()
    except Exception as exc:
        session.rollback()
        assert "unique" in str(exc).lower() or "constraint" in str(exc).lower()
    else:
        raise AssertionError("expected unique constraint violation")


def test_contact_and_task_defaults(session: Session) -> None:
    contact = Contact(name="Jane Doe")
    task = Task(title="Draft hook", due_date=date(2026, 11, 24))
    session.add_all([contact, task])
    session.commit()

    assert contact.stage.value == "identified"
    assert contact.opportunity_status.value == "none"
    assert task.completed is False
    assert task.priority == 2


def test_app_setting_upsert(session: Session) -> None:
    session.add(AppSetting(key="pillars", value="{}"))
    session.commit()
    assert session.get(AppSetting, "pillars").value == "{}"  # type: ignore[union-attr]


def test_datetime_timezone_roundtrip(session: Session) -> None:
    when = datetime(2026, 11, 23, 8, 0, tzinfo=UTC)
    item = ContentItem(
        title="scheduled",
        content_type=ContentType.SHORT_VIDEO,
        pillar="tool_experiment",
        status=ContentStatus.SCHEDULED,
        planned_publish_at=when,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    assert item.planned_publish_at is not None
    assert item.planned_publish_at.year == 2026
