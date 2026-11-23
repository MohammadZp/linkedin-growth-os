from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.database.models import ContentItem
from app.domain.enums import ContentStatus, ContentType
from app.repositories.content import ContentRepository
from app.services.time import now_utc, to_utc
from app.services.validation import is_valid_url

# Fields the user may edit through the bot (whitelist — never set arbitrary attrs).
EDITABLE_FIELDS = {
    "title",
    "topic",
    "hook",
    "outline",
    "draft",
    "call_to_action",
    "notes",
    "reference_url",
    "target_audience",
    "business_outcome",
    "working_language",
}


class DuplicateScheduleError(Exception):
    """Raised when scheduling would collide with an already-scheduled item."""


class ContentService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = ContentRepository(session)

    def create(
        self,
        *,
        title: str,
        content_type: ContentType,
        pillar: str,
        topic: str | None = None,
    ) -> ContentItem:
        item = ContentItem(
            title=title.strip(),
            content_type=content_type,
            pillar=pillar,
            topic=topic.strip() if topic else None,
            status=ContentStatus.IDEA,
        )
        self.repo.add(item)
        self.session.flush()
        return item

    def schedule(self, item: ContentItem, planned_at: datetime) -> ContentItem:
        """Schedule publication, preventing duplicate scheduling at the same time."""
        planned_utc = to_utc(planned_at)
        if self.repo.has_scheduled_at(planned_utc, exclude_id=item.id):
            raise DuplicateScheduleError("محتوای دیگری دقیقا در همین زمان زمان‌بندی شده است.")
        item.status = ContentStatus.SCHEDULED
        item.planned_publish_at = planned_utc
        self.session.flush()
        return item

    def publish(self, item: ContentItem) -> ContentItem:
        """Mark as published, recording the actual publish time."""
        item.status = ContentStatus.PUBLISHED
        item.actual_publish_at = now_utc()
        self.session.flush()
        return item

    def archive(self, item: ContentItem) -> ContentItem:
        item.status = ContentStatus.ARCHIVED
        self.session.flush()
        return item

    def set_status(self, item: ContentItem, status: ContentStatus) -> ContentItem:
        item.status = status
        self.session.flush()
        return item

    def update_field(self, item: ContentItem, field: str, value: str) -> ContentItem:
        if field not in EDITABLE_FIELDS:
            raise ValueError(f"field {field!r} is not editable")
        if field == "reference_url" and value.strip() and not is_valid_url(value):
            raise ValueError("لینک مرجع معتبر نیست (باید با http/https شروع بشه).")
        setattr(item, field, value.strip() if value.strip() else None)
        self.session.flush()
        return item

    def delete(self, item: ContentItem) -> None:
        self.repo.delete(item)
        self.session.flush()
