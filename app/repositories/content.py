from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.database.models import ContentItem
from app.domain.enums import ContentStatus
from app.repositories.base import BaseRepository


class ContentRepository(BaseRepository[ContentItem]):
    model = ContentItem

    def list_by_status(self, status: ContentStatus) -> list[ContentItem]:
        stmt = (
            select(ContentItem).where(ContentItem.status == status).order_by(ContentItem.id.desc())
        )
        return list(self.session.scalars(stmt).all())

    def list_scheduled(self, *, before: datetime | None = None) -> list[ContentItem]:
        stmt = select(ContentItem).where(ContentItem.status == ContentStatus.SCHEDULED)
        if before is not None:
            stmt = stmt.where(ContentItem.planned_publish_at <= before)
        stmt = stmt.order_by(ContentItem.planned_publish_at.asc())
        return list(self.session.scalars(stmt).all())

    def next_scheduled(self) -> ContentItem | None:
        stmt = (
            select(ContentItem)
            .where(
                ContentItem.status == ContentStatus.SCHEDULED,
                ContentItem.planned_publish_at.is_not(None),
            )
            .order_by(ContentItem.planned_publish_at.asc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def has_scheduled_at(self, planned_at: datetime, *, exclude_id: int | None = None) -> bool:
        """True if another content item is already scheduled at the exact same time."""
        stmt = select(ContentItem.id).where(
            ContentItem.status == ContentStatus.SCHEDULED,
            ContentItem.planned_publish_at == planned_at,
        )
        if exclude_id is not None:
            stmt = stmt.where(ContentItem.id != exclude_id)
        return self.session.scalar(stmt) is not None

    def list_published(self, *, limit: int | None = None) -> list[ContentItem]:
        stmt = (
            select(ContentItem)
            .where(ContentItem.status == ContentStatus.PUBLISHED)
            .order_by(ContentItem.actual_publish_at.desc())
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.session.scalars(stmt).all())
