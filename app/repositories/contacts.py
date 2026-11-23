from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.database.models import Contact
from app.domain.enums import ContactStage
from app.repositories.base import BaseRepository


class ContactRepository(BaseRepository[Contact]):
    model = Contact

    def list_by_stage(self, stage: ContactStage) -> list[Contact]:
        stmt = select(Contact).where(Contact.stage == stage).order_by(Contact.id.desc())
        return list(self.session.scalars(stmt).all())

    def list_due_follow_up(self, on_or_before: date) -> list[Contact]:
        """Contacts with a follow-up due, excluding closed stages."""
        stmt = (
            select(Contact)
            .where(
                Contact.next_follow_up_at.is_not(None),
                Contact.next_follow_up_at <= on_or_before,
                Contact.stage.notin_([ContactStage.WON, ContactStage.LOST]),
            )
            .order_by(Contact.next_follow_up_at.asc())
        )
        return list(self.session.scalars(stmt).all())
