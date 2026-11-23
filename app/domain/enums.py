"""Domain enums.

Values are stored in the database as their lowercase string ``.value``.
"""

from __future__ import annotations

from enum import StrEnum


class ContentType(StrEnum):
    OPEN_SOURCE_ANALYSIS = "open_source_analysis"
    TOOL_EXPERIMENT = "tool_experiment"
    PERSONAL_PROJECT = "personal_project"
    EDUCATIONAL_POST = "educational_post"
    SHORT_VIDEO = "short_video"


class ContentStatus(StrEnum):
    IDEA = "idea"
    RESEARCHING = "researching"
    DRAFTING = "drafting"
    REVIEW = "review"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class IdeaStatus(StrEnum):
    INBOX = "inbox"
    SHORTLISTED = "shortlisted"
    SELECTED = "selected"
    REJECTED = "rejected"


class EffortLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ContactStage(StrEnum):
    IDENTIFIED = "identified"
    CONNECTION_PLANNED = "connection_planned"
    CONNECTED = "connected"
    CONVERSATION_STARTED = "conversation_started"
    QUALIFIED_LEAD = "qualified_lead"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"


class OpportunityStatus(StrEnum):
    NONE = "none"
    EXPLORING = "exploring"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATING = "negotiating"
    WON = "won"
    LOST = "lost"


class TaskSource(StrEnum):
    MANUAL = "manual"
    GENERATED = "generated"
    SYSTEM = "system"
