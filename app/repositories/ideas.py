from __future__ import annotations

from sqlalchemy import select

from app.database.models import Idea
from app.domain.enums import IdeaStatus
from app.repositories.base import BaseRepository


class IdeaRepository(BaseRepository[Idea]):
    model = Idea

    def list_by_status(self, status: IdeaStatus) -> list[Idea]:
        stmt = select(Idea).where(Idea.status == status).order_by(Idea.id.desc())
        return list(self.session.scalars(stmt).all())

    def list_scored(self) -> list[Idea]:
        """Ideas that have a computed priority score, highest first."""
        stmt = (
            select(Idea)
            .where(Idea.priority_score.is_not(None))
            .order_by(Idea.priority_score.desc())
        )
        return list(self.session.scalars(stmt).all())
