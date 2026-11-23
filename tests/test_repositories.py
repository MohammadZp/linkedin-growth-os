from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from app.database.models import Contact, ContentItem, Idea, PostAnalytics, Task
from app.domain.enums import ContactStage, ContentStatus, ContentType, IdeaStatus
from app.repositories import (
    AnalyticsRepository,
    ContactRepository,
    ContentRepository,
    IdeaRepository,
    SettingsRepository,
    TaskRepository,
)
from sqlalchemy.orm import Session


def _content(
    title: str,
    status: ContentStatus = ContentStatus.IDEA,
    planned_at: datetime | None = None,
) -> ContentItem:
    return ContentItem(
        title=title,
        content_type=ContentType.TOOL_EXPERIMENT,
        pillar="tool_experiment",
        status=status,
        planned_publish_at=planned_at,
    )


def test_content_next_scheduled_orders_by_time(session: Session) -> None:
    repo = ContentRepository(session)
    later = datetime(2026, 11, 26, 12, 0, tzinfo=UTC)
    sooner = datetime(2026, 11, 24, 9, 0, tzinfo=UTC)
    session.add_all(
        [
            _content("a", ContentStatus.SCHEDULED, later),
            _content("b", ContentStatus.SCHEDULED, sooner),
            _content("c", ContentStatus.DRAFTING),
        ]
    )
    session.commit()

    nxt = repo.next_scheduled()
    assert nxt is not None and nxt.title == "b"


def test_content_duplicate_schedule_detection(session: Session) -> None:
    repo = ContentRepository(session)
    when = datetime(2026, 11, 25, 8, 0, tzinfo=UTC)
    session.add(_content("existing", ContentStatus.SCHEDULED, when))
    session.commit()

    assert repo.has_scheduled_at(when) is True
    assert repo.has_scheduled_at(when + timedelta(hours=1)) is False


def test_idea_repository_scored_ordering(session: Session) -> None:
    repo = IdeaRepository(session)
    session.add_all(
        [
            Idea(title="low", status=IdeaStatus.INBOX, priority_score=1.0),
            Idea(title="high", status=IdeaStatus.SHORTLISTED, priority_score=4.5),
            Idea(title="unscored", status=IdeaStatus.INBOX),
        ]
    )
    session.commit()

    scored = repo.list_scored()
    assert [i.title for i in scored] == ["high", "low"]
    assert repo.list_by_status(IdeaStatus.INBOX)[0].title == "unscored"


def test_task_repository_overdue_and_for_date(session: Session) -> None:
    repo = TaskRepository(session)
    today = date(2026, 11, 23)
    session.add_all(
        [
            Task(title="due today", due_date=today),
            Task(title="overdue", due_date=today - timedelta(days=2)),
            Task(title="done", due_date=today - timedelta(days=1), completed=True),
            Task(title="future", due_date=today + timedelta(days=3)),
        ]
    )
    session.commit()

    overdue = repo.list_overdue(today)
    assert [t.title for t in overdue] == ["overdue"]

    for_today = repo.list_for_date(today)
    assert [t.title for t in for_today] == ["due today"]

    open_tasks = repo.list_open(on_or_before=today)
    assert {t.title for t in open_tasks} == {"due today", "overdue"}


def test_contact_repository_due_follow_up(session: Session) -> None:
    repo = ContactRepository(session)
    today = date(2026, 11, 23)
    session.add_all(
        [
            Contact(name="due", stage=ContactStage.CONNECTED, next_follow_up_at=today),
            Contact(
                name="future",
                stage=ContactStage.CONNECTED,
                next_follow_up_at=today + timedelta(days=1),
            ),
            Contact(name="closed", stage=ContactStage.WON, next_follow_up_at=today),
        ]
    )
    session.commit()

    due = repo.list_due_follow_up(today)
    assert [c.name for c in due] == ["due"]


def test_analytics_repository_latest_snapshot(session: Session) -> None:
    item = _content("post", ContentStatus.PUBLISHED)
    session.add(item)
    session.flush()

    repo = AnalyticsRepository(session)
    session.add_all(
        [
            PostAnalytics(content_item_id=item.id, recorded_at=date(2026, 11, 22), impressions=100),
            PostAnalytics(content_item_id=item.id, recorded_at=date(2026, 11, 23), impressions=180),
        ]
    )
    session.commit()

    latest = repo.latest_for(item.id)
    assert latest is not None and latest.impressions == 180
    assert len(repo.for_item(item.id)) == 2
    assert repo.get_snapshot(item.id, date(2026, 11, 22)).impressions == 100  # type: ignore[union-attr]


def test_settings_repository_upsert(session: Session) -> None:
    repo = SettingsRepository(session)
    assert repo.get("missing", default="dflt") == "dflt"

    repo.set("pillars", "0.5")
    session.commit()
    assert repo.get("pillars") == "0.5"

    repo.set("pillars", "0.6")
    session.commit()
    assert repo.all() == {"pillars": "0.6"}
