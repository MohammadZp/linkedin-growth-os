"""Contact/lead CRM business rules."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.database.models import Contact
from app.domain.enums import ContactStage, OpportunityStatus
from app.repositories.contacts import ContactRepository
from app.services.time import local_date


class ContactService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = ContactRepository(session)

    def create(
        self,
        *,
        name: str,
        profile_url: str | None = None,
        role: str | None = None,
        company: str | None = None,
    ) -> Contact:
        contact = Contact(
            name=name.strip(),
            profile_url=profile_url,
            role=role,
            company=company,
            stage=ContactStage.IDENTIFIED,
            opportunity_status=OpportunityStatus.NONE,
        )
        self.repo.add(contact)
        self.session.flush()
        return contact

    def set_stage(self, contact: Contact, stage: ContactStage) -> None:
        contact.stage = stage
        if stage in (ContactStage.CONNECTED, ContactStage.CONVERSATION_STARTED):
            contact.last_interaction_at = local_date()
        self.session.flush()

    def set_opportunity(self, contact: Contact, status: OpportunityStatus) -> None:
        contact.opportunity_status = status
        self.session.flush()

    def set_follow_up(self, contact: Contact, follow_up: date | None) -> None:
        contact.next_follow_up_at = follow_up
        self.session.flush()

    def add_note(self, contact: Contact, note: str) -> None:
        stamp = local_date().isoformat()
        entry = f"- {stamp}: {note.strip()}"
        contact.notes = f"{contact.notes}\n{entry}" if contact.notes else entry
        self.session.flush()

    def set_business_need(self, contact: Contact, business_need: str) -> None:
        contact.business_need = business_need.strip() or None
        self.session.flush()

    def delete(self, contact: Contact) -> None:
        self.repo.delete(contact)
        self.session.flush()
