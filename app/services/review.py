"""Weekly strategy review: a transparent, evidence-based nine-section report.

Observations are separated from hypotheses. Small samples are flagged, impressions are
never treated as business success, and nothing is fabricated when data is missing.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.bot import texts
from app.config import Settings
from app.repositories.analytics import AnalyticsRepository
from app.repositories.contacts import ContactRepository
from app.repositories.content import ContentRepository
from app.repositories.tasks import TaskRepository
from app.services.analytics import METRIC_FIELDS
from app.services.time import local_date, to_local


def _week_bounds():
    today = local_date()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return today, start, end


def build_weekly_review(session: Session, settings: Settings) -> str:
    today, week_start, week_end = _week_bounds()
    task_repo = TaskRepository(session)
    content_repo = ContentRepository(session)
    contact_repo = ContactRepository(session)
    analytics_repo = AnalyticsRepository(session)

    # 1) Tasks done vs planned.
    completed_week = [
        t
        for t in task_repo.list_completed()
        if t.completed_at is not None and to_local(t.completed_at).date() >= week_start
    ]
    planned_week = [
        t
        for t in task_repo.list_all()
        if t.due_date is not None and week_start <= t.due_date <= week_end
    ]
    open_tasks = task_repo.list_open()
    overdue = [t for t in open_tasks if t.due_date is not None and t.due_date < today]

    # 2) Published content this week.
    published = [
        c
        for c in content_repo.list_published()
        if c.actual_publish_at is not None and to_local(c.actual_publish_at).date() >= week_start
    ]

    # 3) Performance by post and pillar.
    totals = dict.fromkeys(METRIC_FIELDS, 0)
    post_rows: list[tuple] = []
    for c in published:
        snap = analytics_repo.latest_for(c.id)
        values = {f: getattr(snap, f) if snap else 0 for f in METRIC_FIELDS}
        post_rows.append((c, values, snap))
        for f in METRIC_FIELDS:
            totals[f] += values[f]

    # 4) Networking.
    new_contacts = [
        c for c in contact_repo.list_all() if to_local(c.created_at).date() >= week_start
    ]

    # Build text.
    lines = [f"📋 مرور راهبردی هفته — از {week_start.isoformat()} تا {week_end.isoformat()}"]

    lines.append("\n1️⃣ تسک‌ها:")
    lines.append(f"• انجام‌شده این هفته: {len(completed_week)}")
    lines.append(f"• برنامه‌ریزی‌شده این هفته: {len(planned_week)}")
    lines.append(f"• باز (انجام‌نشده): {len(open_tasks)}")
    if overdue:
        lines.append(f"• عقب‌افتاده: {len(overdue)}")

    lines.append("\n2️⃣ محتوای منتشرشده:")
    if published:
        lines.extend(f"• {c.title}" for c in published)
    else:
        lines.append("• هیچ محتوایی منتشر نشده.")

    lines.append("\n3️⃣ عملکرد:")
    if published:
        lines.append(
            f"• بازدید: {totals['impressions']} · واکنش: {totals['reactions']} · "
            f"کامنت: {totals['comments']} · بازنشر: {totals['reposts']}"
        )
        lines.append(
            f"• گفتگوی واجد شرایط: {totals['qualified_conversations']} · لید: {totals['leads']}"
        )
        lines.append("  (بازدید سیگنال دسترسی است، نه موفقیت کسب‌وکاری.)")
        lines.append("  به‌تفکیک پست:")
        for c, values, snap in post_rows:
            if snap is None:
                lines.append(f"  • {c.title} — بدون داده")
            else:
                lines.append(
                    f"  • {c.title} — بازدید {values['impressions']} · "
                    f"گفتگو {values['qualified_conversations']} · لید {values['leads']}"
                )
        # Per-pillar aggregation.
        pillar_agg: dict[str, dict] = {}
        for c, values, _ in post_rows:
            agg = pillar_agg.setdefault(c.pillar, {"n": 0, "impressions": 0, "leads": 0})
            agg["n"] += 1
            agg["impressions"] += values["impressions"]
            agg["leads"] += values["leads"]
        lines.append("  به‌تفکیک ستون:")
        for pillar, agg in pillar_agg.items():
            avg = agg["impressions"] / agg["n"]
            lines.append(
                f"  • {texts.label(texts.PILLAR_LABELS, pillar)} — {agg['n']} پست، "
                f"میانگین بازدید {avg:.0f}، لید {agg['leads']}"
            )
    else:
        lines.append("• داده‌ای برای مقایسه وجود ندارد.")

    lines.append("\n4️⃣ شبکه‌سازی:")
    lines.append(f"• مخاطب جدید این هفته: {len(new_contacts)}")

    lines.append("\n5️⃣ گفتگوهای واجد شرایط:")
    lines.append(f"• {totals['qualified_conversations']} گفتگو، {totals['leads']} لید.")

    # 6) What's working (observations only).
    lines.append("\n6️⃣ چه چیزی جواب می‌دهد (مشاهده):")
    observations: list[str] = []
    if published:
        for pillar, agg in pillar_agg.items():
            observations.append(
                f"• {texts.label(texts.PILLAR_LABELS, pillar)} منتشر شده ({agg['n']} پست)."
            )
    if totals["qualified_conversations"] > 0 or totals["leads"] > 0:
        observations.append("• محتوا به گفتگو/لید رسیده است.")
    else:
        observations.append("• هنوز به گفتگو یا لید نرسیده‌ایم.")
    lines.extend(observations or ["• داده‌ای برای مشاهده وجود ندارد."])

    # 7) What needs evidence.
    lines.append("\n7️⃣ چه چیزی به شواهد بیشتری نیاز دارد:")
    gaps: list[str] = []
    missing = [c.title for c, _, snap in post_rows if snap is None]
    if missing:
        gaps.append(f"• این پست‌ها داده‌ی عملکرد ندارند: {', '.join(missing)}.")
    if len(published) < 3:
        gaps.append("• حجم نمونه کم است؛ نتیجه‌گیری قابل‌اتکا نیست.")
    if published and totals["qualified_conversations"] == 0 and totals["leads"] == 0:
        gaps.append("• بازدید بدون گفتگو: معلوم نیست مخاطب درست را می‌زنیم یا نه.")
    lines.extend(gaps or ["• همه‌ی بخش‌ها داده دارند."])

    # 8) Recommended experiments (hypotheses).
    lines.append("\n8️⃣ آزمایش‌های پیشنهادی (فرضیه):")
    hypotheses: list[str] = []
    if totals["impressions"] > 0 and totals["qualified_conversations"] == 0:
        hypotheses.append(
            "• فرضیه: CTA یا انتخاب مخاطب باید تغییر کند؛ هفته بعد CTA صریح‌تر را امتحان کن."
        )
    if not missing and published:
        hypotheses.append(
            "• فرضیه: ستونی که بیشترین لید را داده ارزش تقویت دارد؛ یک پست دیگر در همان ستون."
        )
    hypotheses.append(
        f"• فرضیه: رسیدن به هدف {settings.publishing_target_per_week} پست در هفته، "
        "سیگنال بهتری از «کیفیت» می‌دهد؛ روی ثبات تمرکز کن."
    )
    lines.extend(hypotheses)

    # 9) Realistic next-week plan.
    lines.append("\n9️⃣ برنامه واقع‌بینانه هفته بعد:")
    lines.append(f"• انتشار {settings.publishing_target_per_week} محتوا (هدف جاری).")
    lines.append(f"• {len(open_tasks)} تسک باز در صف؛ اولویت با قدیمی‌ترین‌ها.")
    lines.append("• ثبت آمار هر پست پس از انتشار تا بخش ۷ هفته بعد داده داشته باشد.")

    lines.append("\n(موارد ۶ تا ۸ بر اساس داده ثبت‌شده است؛ فرضیه‌ها را با داده بسنج.)")
    return "\n".join(lines)
