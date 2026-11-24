from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot import keyboards as kb
from app.bot import texts
from app.config import get_settings
from app.database import session_scope
from app.repositories import ContentRepository
from app.services.briefing import build_daily_briefing
from app.services.time import format_local, now_utc

router = Router(name="menu")


async def _render(message: Message, text: str, *, edit: bool = False) -> None:
    if edit:
        await message.edit_text(text, reply_markup=kb.back_to_menu_kb())
    else:
        await message.answer(text, reply_markup=kb.back_to_menu_kb())


# --- Week ---


def _week_text() -> str:
    now = now_utc()
    with session_scope() as session:
        upcoming = ContentRepository(session).list_scheduled()
        upcoming = [c for c in upcoming if c.planned_publish_at and c.planned_publish_at >= now]
    if not upcoming:
        return "📅 محتوای زمان‌بندی‌شده‌ای برای آینده ثبت نشده."
    lines = ["📅 انتشارهای پیش‌رو:"]
    for c in upcoming:
        lines.append(f"• {format_local(c.planned_publish_at)} — {c.title}")
    return "\n".join(lines)


@router.message(Command("week"))
async def cmd_week(message: Message) -> None:
    await _render(message, _week_text())


# --- Daily briefing ---


def _briefing_text() -> str:
    with session_scope() as session:
        return build_daily_briefing(session, get_settings())


@router.message(Command("briefing"))
async def cmd_briefing(message: Message) -> None:
    await _render(message, _briefing_text())


# --- Settings ---


def _settings_text() -> str:
    s = get_settings()
    pillars = " · ".join(
        f"{texts.label(texts.PILLAR_LABELS, k)} {v:.0%}" for k, v in s.content_pillars.items()
    )
    return (
        f"⚙️ تنظیمات فعلی:\n"
        f"منطقه زمانی: {s.timezone}\n"
        f"هدف انتشار هفتگی: {s.publishing_target_per_week} محتوا\n"
        f"حداکثر تسک روزانه: {s.max_daily_tasks}\n"
        f"زبان پیش‌فرض محتوا: {s.default_content_language}\n"
        f"ستون‌های محتوا: {pillars}\n"
        f"هوش مصنوعی: {'فعال' if s.ai_enabled else 'غیرفعال'}\n\n"
        f"(این مقادیر از فایل .env خوانده می‌شوند.)"
    )


@router.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    await _render(message, _settings_text())


@router.callback_query(F.data == "menu:settings")
async def cb_settings(cb: CallbackQuery) -> None:
    await cb.answer()
    await _render(cb.message, _settings_text(), edit=True)


# --- Week (callback not in main menu; kept minimal) ---
@router.callback_query(F.data == "menu:week")
async def cb_week(cb: CallbackQuery) -> None:
    await cb.answer()
    await _render(cb.message, _week_text(), edit=True)
