from __future__ import annotations

from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.database import session_scope
from app.database.models import Task
from app.repositories import ContentRepository, TaskRepository
from app.services.tasks import TaskService
from app.services.time import format_local, local_date

router = Router(name="tasks")

SKIP_TOKENS = {"-", "/skip"}


class TaskForm(StatesGroup):
    title = State()
    due_date = State()
    priority = State()


def _priority_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔺 بالا (۱)", callback_data="prio:1"),
                InlineKeyboardButton(text="⚪ معمولی (۲)", callback_data="prio:2"),
                InlineKeyboardButton(text="🔻 پایین (۳)", callback_data="prio:3"),
            ]
        ]
    )


def _today_view() -> tuple[str, InlineKeyboardMarkup]:
    today = local_date()
    with session_scope() as session:
        tasks = TaskRepository(session).list_for_date(today)
        overdue = TaskRepository(session).list_overdue(today)
        nxt = ContentRepository(session).next_scheduled()

    lines = [f"✅ تسک‌های امروز ({today.isoformat()}):"]
    rows: list[list[InlineKeyboardButton]] = []
    for t in tasks:
        mark = "☑️" if t.completed else "⬜"
        lines.append(f"{mark} {t.title}")
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{mark} {t.title[:30]}", callback_data=f"task:toggle:{t.id}"
                ),
                InlineKeyboardButton(text="🗑", callback_data=f"task:delete:{t.id}"),
            ]
        )
    if not tasks:
        lines.append("(تسکی برای امروز ثبت نشده)")

    if overdue:
        lines.append(f"\n⚠️ {len(overdue)} تسک عقب‌افتاده:")
        lines.extend(f"• {t.title}" for t in overdue[:5])

    if nxt is not None and nxt.planned_publish_at is not None:
        lines.append(f"\n📅 انتشار بعدی: {format_local(nxt.planned_publish_at)} — {nxt.title}")

    rows.append(
        [
            InlineKeyboardButton(text="➕ تسک جدید", callback_data="task:new"),
            InlineKeyboardButton(text="🔙 منوی اصلی", callback_data="menu:main"),
        ]
    )
    return "\n".join(lines), InlineKeyboardMarkup(inline_keyboard=rows)


# --- Entry points ---


@router.message(Command("today"))
async def cmd_today(message: Message) -> None:
    text, reply = _today_view()
    await message.answer(text, reply_markup=reply)


@router.callback_query(F.data == "menu:today")
async def cb_today(cb: CallbackQuery) -> None:
    await cb.answer()
    text, reply = _today_view()
    await cb.message.edit_text(text, reply_markup=reply)


# --- Toggle / delete ---


@router.callback_query(F.data.startswith("task:toggle:"))
async def cb_task_toggle(cb: CallbackQuery) -> None:
    task_id = int(cb.data.split(":")[2])
    with session_scope() as session:
        task = session.get(Task, task_id)
        if task is not None:
            service = TaskService(session)
            if task.completed:
                service.reopen(task)
            else:
                service.complete(task)
    await cb.answer()
    text, reply = _today_view()
    await cb.message.edit_text(text, reply_markup=reply)


@router.callback_query(F.data.startswith("task:delete:"))
async def cb_task_delete(cb: CallbackQuery) -> None:
    task_id = int(cb.data.split(":")[2])
    with session_scope() as session:
        task = session.get(Task, task_id)
        if task is not None:
            TaskService(session).delete(task)
    await cb.answer()
    text, reply = _today_view()
    await cb.message.edit_text(text, reply_markup=reply)


# --- Create flow ---


@router.callback_query(F.data == "task:new")
async def cb_task_new(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(TaskForm.title)
    await cb.answer()
    await cb.message.edit_text("عنوان تسک رو بفرست:")


@router.message(TaskForm.title)
async def task_step_title(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("لطفا عنوان رو به‌صورت متن بفرست.")
        return
    await state.update_data(title=message.text)
    await state.set_state(TaskForm.due_date)
    await message.answer("تاریخ سررسید رو به فرمت YYYY-MM-DD بفرست، یا «-» برای امروز:")


@router.message(TaskForm.due_date)
async def task_step_due_date(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text in SKIP_TOKENS:
        due_date = local_date()
    else:
        try:
            due_date = date.fromisoformat(text)
        except ValueError:
            await message.answer("فرمت تاریخ اشتباهه. نمونه: 2026-11-24")
            return
    await state.update_data(due_date=due_date)
    await state.set_state(TaskForm.priority)
    await message.answer("اولویت تسک رو انتخاب کن:", reply_markup=_priority_kb())


@router.callback_query(TaskForm.priority, F.data.startswith("prio:"))
async def task_step_priority(cb: CallbackQuery, state: FSMContext) -> None:
    priority = int(cb.data.split(":")[1])
    data = await state.get_data()
    with session_scope() as session:
        TaskService(session).create(
            title=data["title"], due_date=data["due_date"], priority=priority
        )
    await state.clear()
    await cb.answer()
    text, reply = _today_view()
    await cb.message.edit_text(text, reply_markup=reply)
