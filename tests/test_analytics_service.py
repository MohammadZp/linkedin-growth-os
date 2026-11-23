from __future__ import annotations

from app.config import Settings
from app.database.models import ContentItem
from app.domain.enums import ContentStatus, ContentType
from app.services.analytics import AnalyticsService, build_weekly_performance
from app.services.time import local_date, now_utc
from sqlalchemy.orm import Session


def _published(
    session: Session, title: str = "post", pillar: str = "tool_experiment"
) -> ContentItem:
    item = ContentItem(
        title=title,
        content_type=ContentType.TOOL_EXPERIMENT,
        pillar=pillar,
        status=ContentStatus.PUBLISHED,
        actual_publish_at=now_utc(),
    )
    session.add(item)
    session.flush()
    return item


def test_record_upserts_single_snapshot_per_day(session: Session) -> None:
    item = _published(session)
    svc = AnalyticsService(session)
    today = local_date()
    svc.record(item.id, today, metrics={"impressions": 100, "reactions": 5})
    svc.record(item.id, today, metrics={"impressions": 200, "reactions": 8})

    snapshots = svc.repo.for_item(item.id)
    assert len(snapshots) == 1
    assert snapshots[0].impressions == 200
    assert snapshots[0].reactions == 8


def test_weekly_performance_reports_post_and_pillar(session: Session) -> None:
    item = _published(session, title="great post")
    AnalyticsService(session).record(
        item.id,
        local_date(),
        metrics={"impressions": 500, "reactions": 20, "qualified_conversations": 3, "leads": 1},
    )
    text = build_weekly_performance(session, Settings(_env_file=None))
    assert "great post" in text
    assert "بازدید 500" in text
    assert "لید: 1" in text
    assert "tool_experiment" in text


def test_weekly_performance_empty(session: Session) -> None:
    text = build_weekly_performance(session, Settings(_env_file=None))
    assert "هیچ محتوایی این هفته منتشر نشده" in text


def test_record_ignores_unknown_fields(session: Session) -> None:
    item = _published(session)
    svc = AnalyticsService(session)
    snap = svc.record(item.id, local_date(), metrics={"impressions": 10, "bogus": 999})
    assert snap.impressions == 10
    assert not hasattr(snap, "bogus")
