from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.llm_utils import run_llm
from app.config import get_settings
from app.database import session_scope
from app.services.review import build_weekly_review

router = Router(name="review")

_MAX_LEN = 4000  # stay under Telegram's 4096-char message limit


def _review_text() -> str:
    with session_scope() as session:
        text = build_weekly_review(session, get_settings())
    return text if len(text) <= _MAX_LEN else text[:_MAX_LEN]


def _review_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤖 آزمایش‌های پیشنهادی (AI)", callback_data="review:ai")],
            [InlineKeyboardButton(text="🔙 آمار", callback_data="menu:stats")],
        ]
    )


@router.message(Command("review"))
async def cmd_review(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(_review_text(), reply_markup=_review_kb())


@router.callback_query(F.data == "stats:review")
async def cb_review(cb: CallbackQuery) -> None:
    await cb.answer()
    await cb.message.edit_text(_review_text(), reply_markup=_review_kb())


@router.callback_query(F.data == "review:ai")
async def cb_review_ai(cb: CallbackQuery) -> None:
    text = _review_text()
    await cb.answer()
    await run_llm(cb.message, get_settings(), lambda svc: svc.propose_experiments(text))
