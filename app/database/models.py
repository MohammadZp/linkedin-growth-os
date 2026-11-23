from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, IntIdMixin, TimestampMixin
from app.domain.enums import (
    ContactStage,
    ContentStatus,
    ContentType,
    EffortLevel,
    IdeaStatus,
    OpportunityStatus,
    TaskSource,
)


def enum_type(enum_cls: type[Enum]) -> SAEnum:
    """SQLAlchemy Enum that stores the enum's string value and validates on assignment."""
    return SAEnum(
        enum_cls,
        native_enum=False,
        values_callable=lambda e: [m.value for m in e],
        validate_strings=True,
        length=60,
    )


class User(IntIdMixin, TimestampMixin, Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ContentItem(IntIdMixin, TimestampMixin, Base):
    __tablename__ = "content_items"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[ContentType] = mapped_column(enum_type(ContentType), nullable=False)
    pillar: Mapped[str] = mapped_column(String(50), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(255))
    target_audience: Mapped[str | None] = mapped_column(Text)
    business_outcome: Mapped[str | None] = mapped_column(Text)
    working_language: Mapped[str] = mapped_column(String(20), default="en", nullable=False)
    hook: Mapped[str | None] = mapped_column(Text)
    outline: Mapped[str | None] = mapped_column(Text)
    draft: Mapped[str | None] = mapped_column(Text)
    call_to_action: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ContentStatus] = mapped_column(
        enum_type(ContentStatus), default=ContentStatus.IDEA, nullable=False, index=True
    )
    planned_publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    actual_publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reference_url: Mapped[str | None] = mapped_column(String(1000))
    notes: Mapped[str | None] = mapped_column(Text)
    next_action: Mapped[str | None] = mapped_column(Text)

    analytics: Mapped[list[PostAnalytics]] = relationship(back_populates="content_item")


class Idea(IntIdMixin, TimestampMixin, Base):
    __tablename__ = "ideas"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    topic: Mapped[str | None] = mapped_column(String(255))
    why_interesting: Mapped[str | None] = mapped_column(Text)
    potential_demo: Mapped[str | None] = mapped_column(Text)
    estimated_effort: Mapped[EffortLevel | None] = mapped_column(enum_type(EffortLevel))
    relevance_to_services: Mapped[str | None] = mapped_column(Text)
    status: Mapped[IdeaStatus] = mapped_column(
        enum_type(IdeaStatus), default=IdeaStatus.INBOX, nullable=False, index=True
    )
    audience_relevance: Mapped[int | None] = mapped_column(Integer)
    demonstrability: Mapped[int | None] = mapped_column(Integer)
    technical_depth: Mapped[int | None] = mapped_column(Integer)
    business_relevance: Mapped[int | None] = mapped_column(Integer)
    effort_required: Mapped[int | None] = mapped_column(Integer)
    priority_score: Mapped[float | None] = mapped_column(Float)


class Task(IntIdMixin, TimestampMixin, Base):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=2, nullable=False)  # 1 = highest
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[TaskSource] = mapped_column(
        enum_type(TaskSource), default=TaskSource.MANUAL, nullable=False
    )
    content_item_id: Mapped[int | None] = mapped_column(ForeignKey("content_items.id"))
    contact_id: Mapped[int | None] = mapped_column(ForeignKey("contacts.id"))
    idea_id: Mapped[int | None] = mapped_column(ForeignKey("ideas.id"))


class Contact(IntIdMixin, TimestampMixin, Base):
    __tablename__ = "contacts"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_url: Mapped[str | None] = mapped_column(String(1000))
    role: Mapped[str | None] = mapped_column(String(255))
    company: Mapped[str | None] = mapped_column(String(255))
    relevance: Mapped[str | None] = mapped_column(Text)
    stage: Mapped[ContactStage] = mapped_column(
        enum_type(ContactStage), default=ContactStage.IDENTIFIED, nullable=False, index=True
    )
    opportunity_status: Mapped[OpportunityStatus] = mapped_column(
        enum_type(OpportunityStatus), default=OpportunityStatus.NONE, nullable=False
    )
    last_interaction_at: Mapped[date | None] = mapped_column(Date)
    next_follow_up_at: Mapped[date | None] = mapped_column(Date, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    business_need: Mapped[str | None] = mapped_column(Text)


class PostAnalytics(IntIdMixin, TimestampMixin, Base):
    __tablename__ = "post_analytics"
    __table_args__ = (
        UniqueConstraint("content_item_id", "recorded_at", name="uq_post_analytics_item_date"),
    )

    content_item_id: Mapped[int] = mapped_column(
        ForeignKey("content_items.id"), nullable=False, index=True
    )
    recorded_at: Mapped[date] = mapped_column(Date, nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reactions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reposts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    profile_views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    connection_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    qualified_conversations: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    leads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    opportunities: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    content_item: Mapped[ContentItem] = relationship(back_populates="analytics")


class WeeklyReview(IntIdMixin, TimestampMixin, Base):
    __tablename__ = "weekly_reviews"

    week_start: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    next_week_plan: Mapped[str | None] = mapped_column(Text)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
