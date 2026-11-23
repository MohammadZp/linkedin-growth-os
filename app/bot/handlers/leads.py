from __future__ import annotations

from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot import texts
from app.bot.llm_utils import run_llm
from app.config import get_settings
from app.database import session_scope
from app.database.models import Contact
from app.domain.enums import ContactStage, OpportunityStatus
from app.repositories import ContactRepository
from app.services.contacts import ContactService
from app.services.time import local_date
from app.services.validation import is_valid_url

router = Router(name="leads")

SKIP_TOKENS = {"-", "/skip"}


class ContactForm(StatesGroup):
    name = State()
    role = State()
    company = State()
    profile_url = State()
    value = State()


def _leads_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ مخاطب جدید", callback_data="leads:new")],
            [InlineKeyboardButton(text="📋 فهرست مخاطبان", callback_data="leads:list")],
            [InlineKeyboardButton(text="🔙 منوی اصلی", callback_data="menu:main")],
        ]
    )


def _contact_text(c: Contact) -> str:
    return (
        f"🤝 {c.name}\n"
        f"نقش: {c.role or '—'}\n"
        f"شرکت: {c.company or '—'}\n"
        f"لینک پروفایل: {c.profile_url or '—'}\n"
        f"مرحله: {texts.label(texts.CONTACT_STAGE_LABELS, c.stage.value)}\n"
        f"وضعیت فرصت: {texts.label(texts.OPPORTUNITY_STATUS_LABELS, c.opportunity_status.value)}\n"
        f"آخرین تعامل: {c.last_interaction_at.isoformat() if c.last_interaction_at else '—'}\n"
        f"فالوآپ بعدی: {c.next_follow_up_at.isoformat() if c.next_follow_up_at else '—'}\n"
        f"نیاز کسب‌وکاری: {c.business_need or '—'}\n"
        f"یادداشت‌ها:\n{c.notes or '—'}"
    )


def _contact_actions_kb(contact_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 مرحله", callback_data=f"lead:stage:{contact_id}"),
                InlineKeyboardButton(text="💰 فرصت", callback_data=f"lead:opp:{contact_id}"),
            ],
            [
                InlineKeyboardButton(text="📅 فالوآپ", callback_data=f"lead:followup:{contact_id}"),
                InlineKeyboardButton(text="📝 یادداشت", callback_data=f"lead:note:{contact_id}"),
            ],
            [
                InlineKeyboardButton(
                    text="🎯 نیاز کسب‌وکار", callback_data=f"lead:businessneed:{contact_id}"
                ),
                InlineKeyboardButton(text="🗑 حذف", callback_data=f"lead:delete:{contact_id}"),
            ],
            [
                InlineKeyboardButton(
                    text="✉️ پیشنهاد پیام (AI)", callback_data=f"lead:aimsg:{contact_id}"
                )
            ],
            [InlineKeyboardButton(text="🔙 فهرست", callback_data="leads:list")],
        ]
    )


async def _show_contact(message: Message, contact_id: int, *, edit: bool = False) -> None:
    with session_scope() as session:
        contact = session.get(Contact, contact_id)
        if contact is None:
            text, reply = "این مخاطب پیدا نشد.", None
        else:
            text, reply = _contact_text(contact), _contact_actions_kb(contact.id)
    if edit:
        await message.edit_text(text, reply_markup=reply)
    else:
        await message.answer(text, reply_markup=reply)


def _due_follow_ups() -> list[Contact]:
    with session_scope() as session:
        return list(ContactRepository(session).list_due_follow_up(local_date()))


# --- Entry point ---


@router.message(Command("leads"))
async def cmd_leads(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(_overview_text(), reply_markup=_leads_menu_kb())


@router.callback_query(F.data == "menu:leads")
async def cb_leads(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.answer()
    await cb.message.edit_text(_overview_text(), reply_markup=_leads_menu_kb())


def _overview_text() -> str:
    with session_scope() as session:
        contacts = list(ContactRepository(session).list_all(limit=8))
        total = ContactRepository(session).count()
    due = _due_follow_ups()
    lines = ["🤝 مدیریت لیدها و شبکه‌سازی:"]
    lines.append(f"کل مخاطبان: {total}")
    if due:
        lines.append(f"\n📅 فالوآپ سررسید ({len(due)}):")
        lines.extend(f"• {c.name}" for c in due[:5])
    if contacts:
        lines.append("\nآخرین مخاطبان:")
        lines.extend(
            f"• {c.name} — {texts.label(texts.CONTACT_STAGE_LABELS, c.stage.value)}"
            + (f" ({c.company})" if c.company else "")
            for c in contacts
        )
    return "\n".join(lines)


# --- Create flow ---


@router.callback_query(F.data == "leads:new")
async def cb_leads_new(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ContactForm.name)
    await cb.answer()
    await cb.message.edit_text("نام مخاطب رو بفرست:")


@router.message(ContactForm.name)
async def lead_step_name(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("نام مخاطب الزامی‌ست.")
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(ContactForm.role)
    await message.answer("نقش/سمت (اختیاری)؛ برای رد شدن «-»:")


@router.message(ContactForm.role)
async def lead_step_role(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    await state.update_data(role=None if text in SKIP_TOKENS else (text or None))
    await state.set_state(ContactForm.company)
    await message.answer("شرکت (اختیاری)؛ برای رد شدن «-»:")


@router.message(ContactForm.company)
async def lead_step_company(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    await state.update_data(company=None if text in SKIP_TOKENS else (text or None))
    await state.set_state(ContactForm.profile_url)
    await message.answer("لینک پروفایل لینکدین (اختیاری)؛ برای رد شدن «-»:")


@router.message(ContactForm.profile_url)
async def lead_step_profile_url(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    text = (message.text or "").strip()
    if text not in SKIP_TOKENS and text and not is_valid_url(text):
        await message.answer(
            "لینک پروفایل معتبر نیست؛ باید با http یا https شروع بشه. دوباره بفرست یا «-» بزن:"
        )
        return
    profile_url = None if text in SKIP_TOKENS else (text or None)
    with session_scope() as session:
        contact = ContactService(session).create(
            name=data["name"],
            role=data.get("role"),
            company=data.get("company"),
            profile_url=profile_url,
        )
        contact_id = contact.id
    await state.clear()
    await message.answer("✅ مخاطب ثبت شد.")
    await _show_contact(message, contact_id)


# --- List / view ---


@router.callback_query(F.data == "leads:list")
async def cb_leads_list(cb: CallbackQuery) -> None:
    await cb.answer()
    with session_scope() as session:
        contacts = list(ContactRepository(session).list_all(limit=8))
    if not contacts:
        await cb.message.edit_text("هنوز مخاطبی ثبت نشده.", reply_markup=_leads_menu_kb())
        return
    rows = [
        [InlineKeyboardButton(text=f"{c.id}. {c.name[:40]}", callback_data=f"lead:view:{c.id}")]
        for c in contacts
    ]
    rows.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu:leads")])
    await cb.message.edit_text(
        "📋 مخاطبان اخیر:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.callback_query(F.data.startswith("lead:view:"))
async def cb_lead_view(cb: CallbackQuery) -> None:
    contact_id = int(cb.data.split(":")[2])
    await cb.answer()
    await _show_contact(cb.message, contact_id, edit=True)


# --- Stage ---


@router.callback_query(F.data.startswith("lead:stage:"))
async def cb_lead_stage(cb: CallbackQuery) -> None:
    contact_id = int(cb.data.split(":")[2])
    await cb.answer()
    rows = [
        [
            InlineKeyboardButton(
                text=texts.label(texts.CONTACT_STAGE_LABELS, s.value),
                callback_data=f"lead:setstage:{contact_id}:{s.value}",
            )
        ]
        for s in ContactStage
    ]
    rows.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"lead:view:{contact_id}")])
    await cb.message.edit_text(
        "مرحله جدید:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.callback_query(F.data.startswith("lead:setstage:"))
async def cb_lead_setstage(cb: CallbackQuery) -> None:
    _, _, contact_id, stage = cb.data.split(":", 3)
    with session_scope() as session:
        contact = session.get(Contact, int(contact_id))
        if contact is not None:
            ContactService(session).set_stage(contact, ContactStage(stage))
    await cb.answer()
    await _show_contact(cb.message, int(contact_id), edit=True)


# --- Opportunity ---


@router.callback_query(F.data.startswith("lead:opp:"))
async def cb_lead_opp(cb: CallbackQuery) -> None:
    contact_id = int(cb.data.split(":")[2])
    await cb.answer()
    rows = [
        [
            InlineKeyboardButton(
                text=texts.label(texts.OPPORTUNITY_STATUS_LABELS, s.value),
                callback_data=f"lead:setopp:{contact_id}:{s.value}",
            )
        ]
        for s in OpportunityStatus
    ]
    rows.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"lead:view:{contact_id}")])
    await cb.message.edit_text(
        "وضعیت فرصت:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.callback_query(F.data.startswith("lead:setopp:"))
async def cb_lead_setopp(cb: CallbackQuery) -> None:
    _, _, contact_id, status = cb.data.split(":", 3)
    with session_scope() as session:
        contact = session.get(Contact, int(contact_id))
        if contact is not None:
            ContactService(session).set_opportunity(contact, OpportunityStatus(status))
    await cb.answer()
    await _show_contact(cb.message, int(contact_id), edit=True)


# --- Free-text edits (follow-up / note / business need) ---


@router.callback_query(F.data.startswith("lead:followup:"))
async def cb_lead_followup(cb: CallbackQuery, state: FSMContext) -> None:
    contact_id = int(cb.data.split(":")[2])
    await state.set_state(ContactForm.value)
    await state.update_data(mode="followup", contact_id=contact_id)
    await cb.answer()
    await cb.message.edit_text(
        "تاریخ فالوآپ بعدی رو به فرمت YYYY-MM-DD بفرست، یا «-» برای پاک کردن:"
    )


@router.callback_query(F.data.startswith("lead:note:"))
async def cb_lead_note(cb: CallbackQuery, state: FSMContext) -> None:
    contact_id = int(cb.data.split(":")[2])
    await state.set_state(ContactForm.value)
    await state.update_data(mode="note", contact_id=contact_id)
    await cb.answer()
    await cb.message.edit_text("یادداشت رو بفرست (به یادداشت‌های قبلی اضافه می‌شه):")


@router.callback_query(F.data.startswith("lead:businessneed:"))
async def cb_lead_businessneed(cb: CallbackQuery, state: FSMContext) -> None:
    contact_id = int(cb.data.split(":")[2])
    await state.set_state(ContactForm.value)
    await state.update_data(mode="businessneed", contact_id=contact_id)
    await cb.answer()
    await cb.message.edit_text("نیاز کسب‌وکاری مخاطب رو بفرست:")


@router.message(ContactForm.value)
async def lead_step_value(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    contact_id = data["contact_id"]
    mode = data["mode"]
    text = (message.text or "").strip()

    with session_scope() as session:
        contact = session.get(Contact, contact_id)
        if contact is None:
            await state.clear()
            await message.answer("این مخاطب پیدا نشد.")
            return
        service = ContactService(session)
        if mode == "followup":
            follow_up = None
            if text not in SKIP_TOKENS:
                try:
                    follow_up = date.fromisoformat(text)
                except ValueError:
                    await message.answer("فرمت تاریخ اشتباهه. نمونه: 2026-11-30")
                    return
            service.set_follow_up(contact, follow_up)
        elif mode == "note":
            if not text or text in SKIP_TOKENS:
                await message.answer("متن یادداشت خالی بود.")
                return
            service.add_note(contact, text)
        elif mode == "businessneed":
            service.set_business_need(contact, text)
    await state.clear()
    await message.answer("✅ ذخیره شد.")
    await _show_contact(message, contact_id)


# --- AI message draft ---


@router.callback_query(F.data.startswith("lead:aimsg:"))
async def cb_lead_aimsg(cb: CallbackQuery) -> None:
    contact_id = int(cb.data.split(":")[2])
    with session_scope() as session:
        contact = session.get(Contact, contact_id)
        if contact is None:
            await cb.message.edit_text("این مخاطب پیدا نشد.")
            return
        name, role = contact.name, contact.role
        company, notes, need = contact.company, contact.notes, contact.business_need
    await cb.answer()
    settings = get_settings()
    await run_llm(
        cb.message,
        settings,
        lambda svc: svc.draft_message(
            name=name, role=role, company=company, notes=notes, need=need
        ),
    )


# --- Delete ---


@router.callback_query(F.data.startswith("lead:delete:"))
async def cb_lead_delete(cb: CallbackQuery) -> None:
    contact_id = int(cb.data.split(":")[2])
    await cb.answer()
    reply = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="بله، حذف کن", callback_data=f"lead:confirmdelete:{contact_id}"
                ),
                InlineKeyboardButton(text="خیر", callback_data=f"lead:view:{contact_id}"),
            ]
        ]
    )
    await cb.message.edit_text("مطمئنی این مخاطب حذف بشه؟", reply_markup=reply)


@router.callback_query(F.data.startswith("lead:confirmdelete:"))
async def cb_lead_confirmdelete(cb: CallbackQuery) -> None:
    contact_id = int(cb.data.split(":")[2])
    with session_scope() as session:
        contact = session.get(Contact, contact_id)
        if contact is not None:
            ContactService(session).delete(contact)
    await cb.answer()
    await cb.message.edit_text("🗑 مخاطب حذف شد.", reply_markup=_leads_menu_kb())
