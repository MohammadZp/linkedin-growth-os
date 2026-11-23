from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.database.models import PostAnalytics
from app.repositories.base import BaseRepository


class AnalyticsRepository(BaseRepository[PostAnalytics]):
    model = PostAnalytics

    def for_item(self, content_item_id: int) -> list[PostAnalytics]:
        stmt = (
            select(PostAnalytics)
            .where(PostAnalytics.content_item_id == content_item_id)
            .order_by(PostAnalytics.recorded_at.asc())
        )
        return list(self.session.scalars(stmt).all())

    def latest_for(self, content_item_id: int) -> PostAnalytics | None:
        stmt = (
            select(PostAnalytics)
            .where(PostAnalytics.content_item_id == content_item_id)
            .order_by(PostAnalytics.recorded_at.desc())
            .limit(1)
        )
        return self.session.scalar(stmt)

    def get_snapshot(self, content_item_id: int, recorded_at: date) -> PostAnalytics | None:
        stmt = select(PostAnalytics).where(
            PostAnalytics.content_item_id == content_item_id,
            PostAnalytics.recorded_at == recorded_at,
        )
        return self.session.scalar(stmt)
