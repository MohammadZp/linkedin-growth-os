from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot import keyboards as kb
from app.bot import texts
from app.bot.llm_utils import run_llm
from app.config import get_settings
from app.database import session_scope
from app.database.models import ContentItem
from app.domain.enums import ContentStatus, ContentType
from app.repositories.content import ContentRepository
from app.services.content import ContentService, DuplicateScheduleError
from app.services.time import format_local, parse_local_datetime

router = Router(name="content")

SKIP_TOKENS = {"-", "/skip"}


class ContentForm(StatesGroup):
    title = State()
    content_type = State()
    pillar = State()
    topic = State()
    edit_value = State()
    schedule = State()


def _item_text(item: ContentItem) -> str:
    return (
        f"📝 {item.title}\n"
        f"نوع: {texts.label(texts.CONTENT_TYPE_LABELS, item.content_type.value)}\n"
        f"ستون: {texts.label(texts.PILLAR_LABELS, item.pillar)}\n"
        f"وضعیت: {texts.label(texts.CONTENT_STATUS_LABELS, item.status.value)}\n"
        f"موضوع: {item.topic or '—'}\n"
        f"هوک: {item.hook or '—'}\n"
        f"رئوس مطالب: {item.outline or '—'}\n"
        f"پیش‌نویس: {item.draft or '—'}\n"
        f"CTA: {item.call_to_action or '—'}\n"
        f"لینک مرجع: {item.reference_url or '—'}\n"
        f"زمان انتشار: {format_local(item.planned_publish_at)}\n"
        f"یادداشت: {item.notes or '—'}"
    )


async def _show_item(message: Message, item_id: int, *, edit: bool = False) -> None:
    with session_scope() as session:
        item = session.get(ContentItem, item_id)
        if item is None:
            text, reply = "این محتوا پیدا نشد.", None
        else:
            text, reply = _item_text(item), kb.item_actions_kb(item.id)
    if edit:
        await message.edit_text(text, reply_markup=reply)
    else:
        await message.answer(text, reply_markup=reply)


# --- Entry points ---


@router.message(Command("content"))
async def cmd_content(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("📝 مدیریت محتوا — چه کاری انجام بدیم؟", reply_markup=kb.content_menu_kb())


@router.callback_query(F.data == "menu:content")
async def cb_content(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.answer()
    await cb.message.edit_text(
        "📝 مدیریت محتوا — چه کاری انجام بدیم؟", reply_markup=kb.content_menu_kb()
    )


# --- Create flow ---


@router.callback_query(F.data == "content:new")
async def cb_content_new(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ContentForm.title)
    await cb.answer()
    await cb.message.edit_text("عنوان محتوا رو بفرست ✍️")


@router.message(ContentForm.title)
async def step_title(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("لطفا عنوان رو به‌صورت متن بفرست.")
        return
    await state.update_data(title=message.text)
    await state.set_state(ContentForm.content_type)
    await message.answer("نوع محتوا رو انتخاب کن:", reply_markup=kb.content_type_kb())


@router.callback_query(ContentForm.content_type, F.data.startswith("ctype:"))
async def step_content_type(cb: CallbackQuery, state: FSMContext) -> None:
    value = cb.data.split(":", 1)[1]
    await state.update_data(content_type=ContentType(value))
    await state.set_state(ContentForm.pillar)
    await cb.answer()
    await cb.message.edit_text("ستون محتوا (pillar) رو انتخاب کن:", reply_markup=kb.pillar_kb())


@router.callback_query(ContentForm.pillar, F.data.startswith("pillar:"))
async def step_pillar(cb: CallbackQuery, state: FSMContext) -> None:
    pillar = cb.data.split(":", 1)[1]
    await state.update_data(pillar=pillar)
    await state.set_state(ContentForm.topic)
    await cb.answer()
    await cb.message.edit_text("موضوع (اختیاری) رو بفرست؛ برای رد شدن «-» بفرست:")


@router.message(ContentForm.topic)
async def step_topic(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    topic = None if (message.text or "").strip() in SKIP_TOKENS else (message.text or "").strip()
    with session_scope() as session:
        item = ContentService(session).create(
            title=data["title"],
            content_type=data["content_type"],
            pillar=data["pillar"],
            topic=topic or None,
        )
        item_id = item.id
    await state.clear()
    await message.answer("✅ محتوا ساخته شد.")
    await _show_item(message, item_id)


# --- List & view ---


@router.callback_query(F.data == "content:list")
async def cb_content_list(cb: CallbackQuery) -> None:
    await cb.answer()
    with session_scope() as session:
        items = list(ContentRepository(session).list_all(limit=8))
        if not items:
            await cb.message.edit_text("هنوز محتوایی ثبت نشده.", reply_markup=kb.content_menu_kb())
            return
        rows = [
            [
                InlineKeyboardButton(
                    text=f"{i.id}. {i.title[:40]}", callback_data=f"content:view:{i.id}"
                )
            ]
            for i in items
        ]
        rows.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu:content")])
        reply = InlineKeyboardMarkup(inline_keyboard=rows)
    await cb.message.edit_text("📋 محتوای اخیر:", reply_markup=reply)


@router.callback_query(F.data.startswith("content:view:"))
async def cb_content_view(cb: CallbackQuery) -> None:
    item_id = int(cb.data.split(":")[2])
    await cb.answer()
    await _show_item(cb.message, item_id, edit=True)


# --- Edit ---


@router.callback_query(F.data.startswith("content:editmenu:"))
async def cb_content_editmenu(cb: CallbackQuery) -> None:
    item_id = int(cb.data.split(":")[2])
    await cb.answer()
    rows = [
        [
            InlineKeyboardButton(
                text=texts.EDIT_FIELD_LABELS[field],
                callback_data=f"content:editfield:{item_id}:{field}",
            )
        ]
        for field in texts.EDIT_FIELD_LABELS
    ]
    rows.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"content:view:{item_id}")])
    await cb.message.edit_text(
        "کدوم فیلد رو ویرایش می‌کنی؟", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.callback_query(F.data.startswith("content:editfield:"))
async def cb_content_editfield(cb: CallbackQuery, state: FSMContext) -> None:
    _, _, item_id, field = cb.data.split(":", 3)
    await state.set_state(ContentForm.edit_value)
    await state.update_data(item_id=int(item_id), field=field)
    await cb.answer()
    await cb.message.edit_text(f"مقدار جدید برای «{texts.EDIT_FIELD_LABELS[field]}» رو بفرست:")


@router.message(ContentForm.edit_value)
async def step_edit_value(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    item_id = data["item_id"]
    if not message.text:
        await message.answer("لطفا متن بفرست.")
        return
    with session_scope() as session:
        item = session.get(ContentItem, item_id)
        if item is None:
            await state.clear()
            await message.answer("این محتوا پیدا نشد.")
            return
        try:
            ContentService(session).update_field(item, data["field"], message.text)
        except ValueError as exc:
            await message.answer(f"⚠️ {exc}")
            return
    await state.clear()
    await _show_item(message, item_id)


# --- Status ---


@router.callback_query(F.data.startswith("content:status:"))
async def cb_content_status(cb: CallbackQuery) -> None:
    item_id = int(cb.data.split(":")[2])
    await cb.answer()
    await cb.message.edit_text("وضعیت جدید:", reply_markup=kb.content_status_kb(item_id))


@router.callback_query(F.data.startswith("content:setstatus:"))
async def cb_content_setstatus(cb: CallbackQuery) -> None:
    _, _, item_id, status = cb.data.split(":", 3)
    await cb.answer()
    with session_scope() as session:
        item = session.get(ContentItem, int(item_id))
        if item is not None:
            ContentService(session).set_status(item, ContentStatus(status))
    await _show_item(cb.message, int(item_id), edit=True)


# --- Schedule ---


@router.callback_query(F.data.startswith("content:schedule:"))
async def cb_content_schedule(cb: CallbackQuery, state: FSMContext) -> None:
    item_id = int(cb.data.split(":")[2])
    await state.set_state(ContentForm.schedule)
    await state.update_data(item_id=item_id)
    await cb.answer()
    await cb.message.edit_text("زمان انتشار رو به فرمت YYYY-MM-DD HH:MM (به وقت تهران) بفرست:")


@router.message(ContentForm.schedule)
async def step_schedule(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    item_id = data["item_id"]
    if not message.text:
        await message.answer("زمان رو به‌صورت متن بفرست.")
        return
    try:
        planned = parse_local_datetime(message.text)
    except ValueError:
        await message.answer("فرمت اشتباهه. نمونه: 2026-11-25 08:30")
        return
    with session_scope() as session:
        item = session.get(ContentItem, item_id)
        if item is None:
            await state.clear()
            await message.answer("این محتوا پیدا نشد.")
            return
        try:
            ContentService(session).schedule(item, planned)
        except DuplicateScheduleError as exc:
            await state.clear()
            await message.answer(f"⚠️ {exc}")
            return
    await state.clear()
    await _show_item(message, item_id)


# --- Publish / archive / delete ---


@router.callback_query(F.data.startswith("content:publish:"))
async def cb_content_publish(cb: CallbackQuery) -> None:
    item_id = int(cb.data.split(":")[2])
    await cb.answer()
    with session_scope() as session:
        item = session.get(ContentItem, item_id)
        if item is not None:
            ContentService(session).publish(item)
    await _show_item(cb.message, item_id, edit=True)


@router.callback_query(F.data.startswith("content:archive:"))
async def cb_content_archive(cb: CallbackQuery) -> None:
    item_id = int(cb.data.split(":")[2])
    await cb.answer()
    with session_scope() as session:
        item = session.get(ContentItem, item_id)
        if item is not None:
            ContentService(session).archive(item)
    await _show_item(cb.message, item_id, edit=True)


@router.callback_query(F.data.startswith("content:delete:"))
async def cb_content_delete(cb: CallbackQuery) -> None:
    item_id = int(cb.data.split(":")[2])
    await cb.answer()
    await cb.message.edit_text(
        "مطمئنی این محتوا حذف بشه؟", reply_markup=kb.confirm_delete_kb(item_id)
    )


@router.callback_query(F.data.startswith("content:confirmdelete:"))
async def cb_content_confirmdelete(cb: CallbackQuery) -> None:
    item_id = int(cb.data.split(":")[2])
    await cb.answer()
    with session_scope() as session:
        item = session.get(ContentItem, item_id)
        if item is not None:
            ContentService(session).delete(item)
    await cb.message.edit_text("🗑 محتوا حذف شد.", reply_markup=kb.back_to_menu_kb())


# --- AI drafts (hook / angle) ---


async def _ai_draft(cb: CallbackQuery, item_id: int, kind: str) -> None:
    with session_scope() as session:
        item = session.get(ContentItem, item_id)
        if item is None:
            await cb.message.edit_text("این محتوا پیدا نشد.")
            return
        title, topic = item.title, item.topic
        audience, outcome = item.target_audience, item.business_outcome
    await cb.answer()
    settings = get_settings()
    if kind == "hook":
        await run_llm(
            cb.message,
            settings,
            lambda svc: svc.draft_hook(title=title, topic=topic, audience=audience),
        )
    else:
        await run_llm(
            cb.message,
            settings,
            lambda svc: svc.draft_angle(title=title, topic=topic, outcome=outcome),
        )


@router.callback_query(F.data.startswith("content:aihook:"))
async def cb_content_aihook(cb: CallbackQuery) -> None:
    item_id = int(cb.data.split(":")[2])
    await _ai_draft(cb, item_id, "hook")


@router.callback_query(F.data.startswith("content:aiangle:"))
async def cb_content_aiangle(cb: CallbackQuery) -> None:
    item_id = int(cb.data.split(":")[2])
    await _ai_draft(cb, item_id, "angle")
