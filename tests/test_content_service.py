from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.domain.enums import ContentStatus, ContentType
from app.services.content import ContentService, DuplicateScheduleError
from sqlalchemy.orm import Session


def _service(session: Session) -> ContentService:
    return ContentService(session)


def test_create_defaults_to_idea(session: Session) -> None:
    item = _service(session).create(
        title="My post", content_type=ContentType.TOOL_EXPERIMENT, pillar="tool_experiment"
    )
    assert item.id is not None
    assert item.status is ContentStatus.IDEA


def test_schedule_sets_status_and_time(session: Session) -> None:
    svc = _service(session)
    item = svc.create(
        title="a", content_type=ContentType.EDUCATIONAL_POST, pillar="educational_post"
    )
    when = datetime(2026, 11, 25, 8, 0, tzinfo=UTC)
    svc.schedule(item, when)
    assert item.status is ContentStatus.SCHEDULED
    assert item.planned_publish_at == when


def test_schedule_rejects_duplicate(session: Session) -> None:
    svc = _service(session)
    a = svc.create(title="a", content_type=ContentType.TOOL_EXPERIMENT, pillar="tool_experiment")
    b = svc.create(title="b", content_type=ContentType.TOOL_EXPERIMENT, pillar="tool_experiment")
    when = datetime(2026, 11, 25, 8, 0, tzinfo=UTC)
    svc.schedule(a, when)
    with pytest.raises(DuplicateScheduleError):
        svc.schedule(b, when)


def test_publish_and_archive(session: Session) -> None:
    svc = _service(session)
    item = svc.create(title="a", content_type=ContentType.TOOL_EXPERIMENT, pillar="tool_experiment")
    svc.publish(item)
    assert item.status is ContentStatus.PUBLISHED
    assert item.actual_publish_at is not None

    svc.archive(item)
    assert item.status is ContentStatus.ARCHIVED


def test_update_field_whitelist(session: Session) -> None:
    svc = _service(session)
    item = svc.create(title="a", content_type=ContentType.TOOL_EXPERIMENT, pillar="tool_experiment")
    svc.update_field(item, "hook", "A compelling hook")
    assert item.hook == "A compelling hook"

    with pytest.raises(ValueError):
        svc.update_field(item, "not_a_field", "x")


def test_update_reference_url_accepts_valid_url(session: Session) -> None:
    svc = _service(session)
    item = svc.create(title="a", content_type=ContentType.TOOL_EXPERIMENT, pillar="tool_experiment")
    svc.update_field(item, "reference_url", "https://example.com/post")
    assert item.reference_url == "https://example.com/post"


def test_update_reference_url_rejects_invalid(session: Session) -> None:
    svc = _service(session)
    item = svc.create(title="a", content_type=ContentType.TOOL_EXPERIMENT, pillar="tool_experiment")
    with pytest.raises(ValueError):
        svc.update_field(item, "reference_url", "not-a-url")


def test_update_reference_url_clears_on_blank(session: Session) -> None:
    svc = _service(session)
    item = svc.create(title="a", content_type=ContentType.TOOL_EXPERIMENT, pillar="tool_experiment")
    svc.update_field(item, "reference_url", "https://example.com/post")
    svc.update_field(item, "reference_url", "")
    assert item.reference_url is None
