from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot import texts
from app.config import get_settings
from app.domain.enums import ContentStatus, ContentType


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 محتوا", callback_data="menu:content")],
            [InlineKeyboardButton(text="💡 ایده‌ها", callback_data="menu:ideas")],
            [InlineKeyboardButton(text="✅ تسک‌های امروز", callback_data="menu:today")],
            [InlineKeyboardButton(text="📊 آمار", callback_data="menu:stats")],
            [InlineKeyboardButton(text="🤝 لیدها", callback_data="menu:leads")],
            [InlineKeyboardButton(text="⚙️ تنظیمات", callback_data="menu:settings")],
        ]
    )


def content_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ محتوای جدید", callback_data="content:new")],
            [InlineKeyboardButton(text="📋 فهرست محتوا", callback_data="content:list")],
            [InlineKeyboardButton(text="🔙 منوی اصلی", callback_data="menu:main")],
        ]
    )


def content_type_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=texts.label(texts.CONTENT_TYPE_LABELS, t.value),
                callback_data=f"ctype:{t.value}",
            )
        ]
        for t in ContentType
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def pillar_kb() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=texts.label(texts.PILLAR_LABELS, p),
                callback_data=f"pillar:{p}",
            )
        ]
        for p in get_settings().content_pillars
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def content_status_kb(item_id: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=texts.label(texts.CONTENT_STATUS_LABELS, s.value),
                callback_data=f"content:setstatus:{item_id}:{s.value}",
            )
        ]
        for s in ContentStatus
    ]
    rows.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"content:view:{item_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def item_actions_kb(item_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ ویرایش", callback_data=f"content:editmenu:{item_id}"),
                InlineKeyboardButton(text="🔄 وضعیت", callback_data=f"content:status:{item_id}"),
            ],
            [
                InlineKeyboardButton(
                    text="📅 زمان‌بندی", callback_data=f"content:schedule:{item_id}"
                ),
                InlineKeyboardButton(text="✅ انتشار", callback_data=f"content:publish:{item_id}"),
            ],
            [
                InlineKeyboardButton(text="🗄 بایگانی", callback_data=f"content:archive:{item_id}"),
                InlineKeyboardButton(text="🗑 حذف", callback_data=f"content:delete:{item_id}"),
            ],
            [
                InlineKeyboardButton(text="🤖 هوک (AI)", callback_data=f"content:aihook:{item_id}"),
                InlineKeyboardButton(
                    text="🤖 زاویه (AI)", callback_data=f"content:aiangle:{item_id}"
                ),
            ],
            [InlineKeyboardButton(text="🔙 فهرست", callback_data="content:list")],
        ]
    )


def confirm_delete_kb(item_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="بله، حذف کن", callback_data=f"content:confirmdelete:{item_id}"
                ),
                InlineKeyboardButton(text="خیر", callback_data=f"content:view:{item_id}"),
            ]
        ]
    )


def idea_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💡 ایده جدید", callback_data="idea:new")],
            [InlineKeyboardButton(text="📋 فهرست ایده‌ها", callback_data="idea:list")],
            [InlineKeyboardButton(text="🤖 پیشنهاد ایده (AI)", callback_data="idea:ai")],
            [InlineKeyboardButton(text="🔙 منوی اصلی", callback_data="menu:main")],
        ]
    )


def idea_actions_kb(idea_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ امتیازدهی", callback_data=f"idea:score:{idea_id}")],
            [InlineKeyboardButton(text="🔄 تغییر وضعیت", callback_data=f"idea:status:{idea_id}")],
            [InlineKeyboardButton(text="🔙 فهرست", callback_data="idea:list")],
        ]
    )


def score_kb(criterion: str) -> InlineKeyboardMarkup:
    row = [
        InlineKeyboardButton(text=str(v), callback_data=f"score:{criterion}:{v}")
        for v in range(1, 6)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[row])


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 منوی اصلی", callback_data="menu:main")]]
    )
