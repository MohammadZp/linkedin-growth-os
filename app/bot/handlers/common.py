from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.bot import keyboards as kb
from app.bot import texts
from app.database import session_scope
from app.database.models import User

router = Router(name="common")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    sender = message.from_user
    if sender is not None:
        with session_scope() as session:
            existing = session.scalar(select(User).where(User.telegram_id == sender.id))
            if existing is None:
                session.add(
                    User(
                        telegram_id=sender.id,
                        full_name=sender.full_name,
                        username=sender.username,
                    )
                )
    name = sender.first_name if sender else "دوست عزیز"
    await message.answer(texts.MSG_START.format(name=name), reply_markup=kb.main_menu_kb())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(texts.MSG_HELP)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.MSG_CANCEL, reply_markup=kb.main_menu_kb())


@router.callback_query(F.data == "menu:main")
async def cb_main_menu(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.answer()
    await cb.message.edit_text("منوی اصلی 👇", reply_markup=kb.main_menu_kb())
