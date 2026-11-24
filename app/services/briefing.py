"""Pure builders for briefing and weekly-summary texts (testable without Telegram)."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.config import Settings
from app.repositories import ContentRepository, TaskRepository
from app.services.time import format_local, local_date, to_local


def build_daily_briefing(session: Session, settings: Settings) -> str:
    today = local_date()
    tasks = TaskRepository(session).list_for_date(today)
    overdue = TaskRepository(session).list_overdue(today)

    lines = [f"☀️ بریفینگ روزانه — {today.isoformat()}"]

    if tasks:
        lines.append(f"📌 اولویت‌های امروز (حداکثر {settings.max_daily_tasks}):")
        lines.extend(f"{i + 1}. {t.title}" for i, t in enumerate(tasks[: settings.max_daily_tasks]))
    else:
        lines.append("✅ امروز تسک برنامه‌ریزی‌شده‌ای نداری. روز سبکی شروع کن.")

    if overdue:
        lines.append(f"\n⚠️ {len(overdue)} تسک عقب‌افتاده:")
        lines.extend(f"• {t.title}" for t in overdue[:3])

    nxt = ContentRepository(session).next_scheduled()
    if nxt is not None and nxt.planned_publish_at is not None:
        lines.append(f"\n📅 انتشار بعدی: {format_local(nxt.planned_publish_at)} — {nxt.title}")

    lines.append("\nموفق باشی 💪")
    return "\n".join(lines)


def build_weekly_summary(session: Session, settings: Settings) -> str:
    today = local_date()
    week_start = today - timedelta(days=today.weekday())

    task_repo = TaskRepository(session)
    open_tasks = task_repo.list_open()
    overdue = [t for t in open_tasks if t.due_date is not None and t.due_date < today]
    completed_week = [
        t
        for t in task_repo.list_completed()
        if t.completed_at is not None and to_local(t.completed_at).date() >= week_start
    ]

    content_repo = ContentRepository(session)
    published_week = [
        c
        for c in content_repo.list_published()
        if c.actual_publish_at is not None and to_local(c.actual_publish_at).date() >= week_start
    ]
    upcoming = content_repo.list_scheduled()

    lines = [f"📊 مرور هفته — از {week_start.isoformat()}"]

    lines.append("\n✅ تسک‌ها:")
    lines.append(f"• تکمیل‌شده این هفته: {len(completed_week)}")
    lines.append(f"• باز (انجام‌نشده): {len(open_tasks)}")
    if overdue:
        lines.append(f"• عقب‌افتاده: {len(overdue)}")

    lines.append("\n📝 محتوا:")
    lines.append(f"• منتشرشده این هفته: {len(published_week)}")
    lines.append(f"• هدف هفتگی: {settings.publishing_target_per_week}")

    if upcoming:
        lines.append("\n📅 انتشارهای پیش‌رو:")
        lines.extend(f"• {format_local(c.planned_publish_at)} — {c.title}" for c in upcoming[:5])

    lines.append("\nبرای هفته بعد چه برنامه‌ای داری؟")
    return "\n".join(lines)
