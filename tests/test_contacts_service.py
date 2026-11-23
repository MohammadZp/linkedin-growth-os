from __future__ import annotations

from datetime import date

from app.database.models import Contact
from app.domain.enums import ContactStage, OpportunityStatus
from app.services.contacts import ContactService
from sqlalchemy.orm import Session


def test_create_contact(session: Session) -> None:
    c = ContactService(session).create(name="Jane Doe", company="Acme")
    assert c.id is not None
    assert c.stage is ContactStage.IDENTIFIED
    assert c.opportunity_status is OpportunityStatus.NONE


def test_set_stage_touches_interaction(session: Session) -> None:
    svc = ContactService(session)
    c = svc.create(name="Jane")
    svc.set_stage(c, ContactStage.CONVERSATION_STARTED)
    assert c.stage is ContactStage.CONVERSATION_STARTED
    assert c.last_interaction_at is not None


def test_follow_up_and_note_and_business_need(session: Session) -> None:
    svc = ContactService(session)
    c = svc.create(name="Jane")
    svc.set_follow_up(c, date(2026, 11, 30))
    svc.add_note(c, "wants an API review")
    svc.add_note(c, "follow up next week")
    svc.set_business_need(c, "content for their platform")

    assert c.next_follow_up_at == date(2026, 11, 30)
    assert "wants an API review" in (c.notes or "")
    assert "follow up next week" in (c.notes or "")
    assert c.business_need == "content for their platform"


def test_delete_contact(session: Session) -> None:
    svc = ContactService(session)
    c = svc.create(name="Jane")
    cid = c.id
    svc.delete(c)
    assert session.get(Contact, cid) is None
