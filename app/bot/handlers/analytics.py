from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot import texts
from app.config import get_settings
from app.database import session_scope
from app.database.models import ContentItem
from app.domain.enums import ContentStatus
from app.repositories import ContentRepository
from app.repositories.analytics import AnalyticsRepository
from app.services.analytics import METRIC_FIELDS, AnalyticsService, build_weekly_performance
from app.services.time import local_date

router = Router(name="analytics")


class StatsForm(StatesGroup):
    record = State()


def _stats_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ ثبت آمار پست", callback_data="stats:record")],
            [InlineKeyboardButton(text="📈 عملکرد این هفته", callback_data="stats:week")],
            [InlineKeyboardButton(text="📋 مرور هفتگی", callback_data="stats:review")],
            [InlineKeyboardButton(text="🔙 منوی اصلی", callback_data="menu:main")],
        ]
    )


def _overview_text() -> str:
    with session_scope() as session:
        content = ContentRepository(session)
        by_status = {s: len(content.list_by_status(s)) for s in ContentStatus}
        published = content.list_published(limit=1)
    lines = ["📊 آمار محتوا:"]
    lines.append(
        " · ".join(
            f"{texts.label(texts.CONTENT_STATUS_LABELS, s.value)} {n}" for s, n in by_status.items()
        )
    )
    if published:
        lines.append("\nآخرین پست منتشرشده:")
        for c in published:
            lines.append(f"• {c.title}")
    lines.append("\nبرای ثبت بازخورد هر پست یا دیدن عملکرد هفته، از دکمه‌های زیر استفاده کن.")
    return "\n".join(lines)


def _snapshot_text(item_id: int) -> str:
    with session_scope() as session:
        snap = AnalyticsRepository(session).latest_for(item_id)
        item = session.get(ContentItem, item_id)
    title = item.title if item else str(item_id)
    if snap is None:
        return f"📊 {title}\n(هنوز آماری ثبت نشده)"
    parts = [f"📊 {title} — {snap.recorded_at.isoformat()}"]
    for field in METRIC_FIELDS:
        parts.append(f"{texts.METRIC_LABELS[field]}: {getattr(snap, field)}")
    return "\n".join(parts)


# --- Entry point ---


@router.message(Command("stats"))
async def cmd_stats(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(_overview_text(), reply_markup=_stats_menu_kb())


@router.callback_query(F.data == "menu:stats")
async def cb_stats(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.answer()
    await cb.message.edit_text(_overview_text(), reply_markup=_stats_menu_kb())


# --- Weekly performance ---


@router.callback_query(F.data == "stats:week")
async def cb_stats_week(cb: CallbackQuery) -> None:
    await cb.answer()
    with session_scope() as session:
        text = build_weekly_performance(session, get_settings())
    await cb.message.edit_text(text, reply_markup=_stats_menu_kb())


# --- Record flow ---


@router.callback_query(F.data == "stats:record")
async def cb_stats_record(cb: CallbackQuery) -> None:
    await cb.answer()
    with session_scope() as session:
        published = ContentRepository(session).list_published(limit=10)
    if not published:
        await cb.message.edit_text(
            "هنوز پست منتشرشده‌ای نداری؛ اول یک محتوا رو منتشر کن.",
            reply_markup=_stats_menu_kb(),
        )
        return
    rows = [
        [InlineKeyboardButton(text=f"{c.id}. {c.title[:40]}", callback_data=f"arecord:{c.id}")]
        for c in published
    ]
    rows.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu:stats")])
    await cb.message.edit_text(
        "برای کدوم پست آمار ثبت می‌کنی؟",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.callback_query(F.data.startswith("arecord:"))
async def cb_arecord(cb: CallbackQuery, state: FSMContext) -> None:
    item_id = int(cb.data.split(":")[1])
    await state.set_state(StatsForm.record)
    await state.update_data(item_id=item_id)
    await cb.answer()
    await cb.message.edit_text(
        "آمار امروز رو به ترتیب با فاصله بفرست:\n"
        "بازدید واکنش کامنت بازنشر بازدید_پروفایل درخواست_اتصال گفتگوی_واجد_شرایط لید\n\n"
        "مثال: 1200 45 12 3 80 10 2 1"
    )


@router.message(StatsForm.record)
async def stats_step_record(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    parts = raw.split()
    if not parts or len(parts) > len(METRIC_FIELDS):
        await message.answer(f"باید بین ۱ تا {len(METRIC_FIELDS)} عدد با فاصله بفرستی.")
        return
    try:
        values = [int(p) for p in parts]
    except ValueError:
        await message.answer("فقط عدد بفرست (مثلا: 1200 45 12 3 80 10 2 1).")
        return
    if any(v < 0 for v in values):
        await message.answer("اعداد نمی‌تونن منفی باشن.")
        return

    data = await state.get_data()
    item_id = data["item_id"]
    metrics = dict(zip(METRIC_FIELDS, values, strict=False))
    with session_scope() as session:
        AnalyticsService(session).record(item_id, local_date(), metrics=metrics)
    await state.clear()
    await message.answer("✅ آمار ثبت شد.")
    await message.answer(_snapshot_text(item_id), reply_markup=_stats_menu_kb())
