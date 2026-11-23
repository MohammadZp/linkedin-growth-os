"""Analytics recording and weekly performance summarization."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.config import Settings
from app.database.models import PostAnalytics
from app.repositories.analytics import AnalyticsRepository
from app.repositories.content import ContentRepository
from app.services.time import local_date, to_local

# Column names that can be recorded through the bot, in prompt order.
METRIC_FIELDS = (
    "impressions",
    "reactions",
    "comments",
    "reposts",
    "profile_views",
    "connection_requests",
    "qualified_conversations",
    "leads",
)


class AnalyticsService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = AnalyticsRepository(session)

    def record(
        self,
        content_item_id: int,
        recorded_at: date,
        *,
        metrics: dict[str, int],
        notes: str | None = None,
    ) -> PostAnalytics:
        """Create or update the snapshot for one post on one day (idempotent per date)."""
        snapshot = self.repo.get_snapshot(content_item_id, recorded_at)
        if snapshot is None:
            snapshot = PostAnalytics(content_item_id=content_item_id, recorded_at=recorded_at)
            self.session.add(snapshot)
        for field in METRIC_FIELDS:
            setattr(snapshot, field, metrics.get(field, 0))
        if notes is not None:
            snapshot.notes = notes.strip() or None
        self.session.flush()
        return snapshot


def build_weekly_performance(session: Session, settings: Settings) -> str:
    """Transparent weekly performance summary comparing posts and pillars.

    Impressions are shown as a reach signal but never framed as business success;
    qualified conversations and leads are surfaced as the outcome that matters.
    """
    today = local_date()
    week_start = today - timedelta(days=today.weekday())

    content_repo = ContentRepository(session)
    analytics_repo = AnalyticsRepository(session)

    published = [
        c
        for c in content_repo.list_published()
        if c.actual_publish_at is not None and to_local(c.actual_publish_at).date() >= week_start
    ]

    lines = [f"📈 عملکرد این هفته (از {week_start.isoformat()}):"]
    if not published:
        lines.append("هیچ محتوایی این هفته منتشر نشده.")
        return "\n".join(lines)

    rows: list[tuple] = []
    totals = dict.fromkeys(METRIC_FIELDS, 0)
    for c in published:
        snap = analytics_repo.latest_for(c.id)
        values = {f: getattr(snap, f) if snap else 0 for f in METRIC_FIELDS}
        rows.append((c, values, snap))
        for f in METRIC_FIELDS:
            totals[f] += values[f]

    lines.append(f"پست منتشرشده: {len(published)}")
    lines.append(
        f"بازدید: {totals['impressions']} · واکنش: {totals['reactions']} · "
        f"کامنت: {totals['comments']} · بازنشر: {totals['reposts']}"
    )
    lines.append(
        f"🎯 گفتگوی واجد شرایط: {totals['qualified_conversations']} · لید: {totals['leads']}"
    )
    lines.append("(بازدید فقط سیگنال دسترسی است؛ نتیجه کسب‌وکاری، گفتگو و لید است.)")

    lines.append("\nبه‌تفکیک پست:")
    for c, values, snap in rows:
        if snap is None:
            lines.append(f"• {c.title} — (بدون داده)")
        else:
            lines.append(
                f"• {c.title} — بازدید {values['impressions']} · واکنش {values['reactions']}"
                f" · کامنت {values['comments']} · گفتگو {values['qualified_conversations']}"
                f" · لید {values['leads']}"
            )

    lines.append("\nبه‌تفکیک ستون محتوا:")
    by_pillar: dict[str, list] = {}
    for c, values, _ in rows:
        by_pillar.setdefault(c.pillar, []).append(values)
    for pillar, values_list in by_pillar.items():
        n = len(values_list)
        avg_impressions = sum(v["impressions"] for v in values_list) / n
        total_leads = sum(v["leads"] for v in values_list)
        lines.append(
            f"• {pillar}: {n} پست — میانگین بازدید {avg_impressions:.0f} · لید {total_leads}"
        )

    return "\n".join(lines)
