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
from app.database.models import Idea
from app.domain.enums import IdeaStatus
from app.repositories.ideas import IdeaRepository
from app.services.scoring import CRITERIA, IdeaScorer, ScoreBreakdown
from app.services.validation import is_valid_url

router = Router(name="ideas")

SKIP_TOKENS = {"-", "/skip"}


class IdeaForm(StatesGroup):
    title = State()
    source_url = State()
    topic = State()
    score_value = State()
    ai_topic = State()


def _idea_text(idea: Idea) -> str:
    effort = idea.estimated_effort.value if idea.estimated_effort else None
    score = f"{idea.priority_score:.2f}" if idea.priority_score is not None else "—"
    return (
        f"💡 {idea.title}\n"
        f"وضعیت: {texts.label(texts.IDEA_STATUS_LABELS, idea.status.value)}\n"
        f"موضوع: {idea.topic or '—'}\n"
        f"لینک: {idea.source_url or '—'}\n"
        f"چرا جالبه: {idea.why_interesting or '—'}\n"
        f"دموی احتمالی: {idea.potential_demo or '—'}\n"
        f"زحمت تخمینی: {texts.label(texts.EFFORT_LABELS, effort)}\n"
        f"امتیاز اولویت: {score}"
    )


def _breakdown_text(breakdown: ScoreBreakdown) -> str:
    lines = [f"⭐ امتیاز اولویت: {breakdown.score:.2f} از ۵\n"]
    for criterion in CRITERIA:
        raw = breakdown.raw.get(criterion)
        if raw is None:
            continue
        comp = breakdown.components.get(criterion, 0.0)
        note = " (معکوس)" if criterion == "effort_required" else ""
        lines.append(f"• {texts.CRITERION_LABELS[criterion]}: {raw}{note} → سهم {comp:.2f}")
    return "\n".join(lines)


async def _show_idea(message: Message, idea_id: int, *, edit: bool = False) -> None:
    with session_scope() as session:
        idea = session.get(Idea, idea_id)
        if idea is None:
            text, reply = "این ایده پیدا نشد.", None
        else:
            text, reply = _idea_text(idea), kb.idea_actions_kb(idea.id)
    if edit:
        await message.edit_text(text, reply_markup=reply)
    else:
        await message.answer(text, reply_markup=reply)


# --- Entry points ---


@router.message(Command("ideas"))
async def cmd_ideas(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("💡 مدیریت ایده‌ها:", reply_markup=kb.idea_menu_kb())


@router.callback_query(F.data == "menu:ideas")
async def cb_ideas(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.answer()
    await cb.message.edit_text("💡 مدیریت ایده‌ها:", reply_markup=kb.idea_menu_kb())


# --- Create flow ---


@router.callback_query(F.data == "idea:new")
async def cb_idea_new(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(IdeaForm.title)
    await cb.answer()
    await cb.message.edit_text("عنوان ایده رو بفرست 💡")


# --- AI suggestion ---


@router.callback_query(F.data == "idea:ai")
async def cb_idea_ai(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(IdeaForm.ai_topic)
    await cb.answer()
    await cb.message.edit_text("برای چه موضوعی ایده می‌خوای؟ («-» برای پیشنهاد عمومی بفرست):")


@router.message(IdeaForm.ai_topic)
async def idea_step_ai_topic(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    topic = None if text in SKIP_TOKENS else (text or None)
    await state.clear()
    settings = get_settings()
    await run_llm(message, settings, lambda svc: svc.suggest_ideas(topic))


@router.message(IdeaForm.title)
async def idea_step_title(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("لطفا عنوان رو به‌صورت متن بفرست.")
        return
    await state.update_data(title=message.text)
    await state.set_state(IdeaForm.source_url)
    await message.answer("لینک منبع (اختیاری) رو بفرست؛ برای رد شدن «-» بفرست:")


@router.message(IdeaForm.source_url)
async def idea_step_source_url(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text not in SKIP_TOKENS and text and not is_valid_url(text):
        await message.answer(
            "لینک معتبر نیست؛ باید با http یا https شروع بشه. دوباره بفرست یا «-» بزن:"
        )
        return
    source_url = None if text in SKIP_TOKENS else (text or None)
    await state.update_data(source_url=source_url)
    await state.set_state(IdeaForm.topic)
    await message.answer("موضوع (اختیاری) رو بفرست؛ برای رد شدن «-» بفرست:")


@router.message(IdeaForm.topic)
async def idea_step_topic(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    text = (message.text or "").strip()
    topic = None if text in SKIP_TOKENS else (text or None)
    with session_scope() as session:
        idea = Idea(title=data["title"], source_url=data.get("source_url"), topic=topic)
        session.add(idea)
        session.flush()
        idea_id = idea.id
    await state.clear()
    await message.answer("✅ ایده ذخیره شد.")
    await _show_idea(message, idea_id)


# --- List ---


@router.callback_query(F.data == "idea:list")
async def cb_idea_list(cb: CallbackQuery) -> None:
    await cb.answer()
    with session_scope() as session:
        ideas = list(IdeaRepository(session).list_all(limit=8))
        if not ideas:
            await cb.message.edit_text("هنوز ایده‌ای ثبت نشده.", reply_markup=kb.idea_menu_kb())
            return
        rows = [
            [
                InlineKeyboardButton(
                    text=f"{i.id}. {i.title[:40]}",
                    callback_data=f"idea:view:{i.id}",
                )
            ]
            for i in ideas
        ]
        rows.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="menu:ideas")])
        reply = InlineKeyboardMarkup(inline_keyboard=rows)
    await cb.message.edit_text("📋 ایده‌های اخیر:", reply_markup=reply)


@router.callback_query(F.data.startswith("idea:view:"))
async def cb_idea_view(cb: CallbackQuery) -> None:
    idea_id = int(cb.data.split(":")[2])
    await cb.answer()
    await _show_idea(cb.message, idea_id, edit=True)


# --- Status ---


@router.callback_query(F.data.startswith("idea:status:"))
async def cb_idea_status(cb: CallbackQuery) -> None:
    idea_id = int(cb.data.split(":")[2])
    await cb.answer()
    rows = [
        [
            InlineKeyboardButton(
                text=texts.label(texts.IDEA_STATUS_LABELS, s.value),
                callback_data=f"idea:setstatus:{idea_id}:{s.value}",
            )
        ]
        for s in IdeaStatus
    ]
    rows.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"idea:view:{idea_id}")])
    await cb.message.edit_text(
        "وضعیت جدید:", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.callback_query(F.data.startswith("idea:setstatus:"))
async def cb_idea_setstatus(cb: CallbackQuery) -> None:
    _, _, idea_id, status = cb.data.split(":", 3)
    await cb.answer()
    with session_scope() as session:
        idea = session.get(Idea, int(idea_id))
        if idea is not None:
            idea.status = IdeaStatus(status)
    await _show_idea(cb.message, int(idea_id), edit=True)


# --- Scoring ---


@router.callback_query(F.data.startswith("idea:score:"))
async def cb_idea_score(cb: CallbackQuery, state: FSMContext) -> None:
    idea_id = int(cb.data.split(":")[2])
    await state.set_state(IdeaForm.score_value)
    await state.update_data(idea_id=idea_id, pending=list(CRITERIA), scores={})
    await cb.answer()
    await cb.message.edit_text(
        f"به «{texts.CRITERION_LABELS[CRITERIA[0]]}» از ۱ تا ۵ نمره بده (سوال ۱ از ۵):",
        reply_markup=kb.score_kb(CRITERIA[0]),
    )


@router.callback_query(IdeaForm.score_value, F.data.startswith("score:"))
async def idea_step_score(cb: CallbackQuery, state: FSMContext) -> None:
    _, criterion, value = cb.data.split(":", 2)
    data = await state.get_data()
    scores: dict[str, int] = data["scores"]
    scores[criterion] = int(value)
    pending: list[str] = data["pending"]
    done = len(scores)

    if pending[1:]:
        next_criterion = pending[1]
        await state.update_data(scores=scores, pending=pending[1:])
        await cb.answer()
        await cb.message.edit_text(
            f"به «{texts.CRITERION_LABELS[next_criterion]}» از ۱ تا ۵ نمره بده "
            f"(سوال {done + 1} از ۵):",
            reply_markup=kb.score_kb(next_criterion),
        )
        return

    idea_id = data["idea_id"]
    with session_scope() as session:
        idea = session.get(Idea, idea_id)
        if idea is None:
            await state.clear()
            await cb.message.edit_text("این ایده پیدا نشد.")
            return
        for criterion_name, score_value in scores.items():
            setattr(idea, criterion_name, score_value)
        breakdown = IdeaScorer(get_settings()).apply(idea)
        text = _breakdown_text(breakdown)
    await state.clear()
    await cb.answer()
    await cb.message.edit_text(text, reply_markup=kb.idea_actions_kb(idea_id))
