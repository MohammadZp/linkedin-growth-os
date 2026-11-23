"""Shared helper for bot handlers that produce LLM text for the user to review."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from aiogram.types import Message

from app.ai.providers import LLMError, LLMNotConfiguredError
from app.config import Settings
from app.services.llm import LLMService

MSG_DISABLED = (
    "🤖 هوش مصنوعی فعال نیست. برای فعال‌سازی، AI_PROVIDER و AI_API_KEY رو در .env تنظیم کن."
)


async def run_llm(
    message: Message,
    settings: Settings,
    factory: Callable[[LLMService], Awaitable[str]],
) -> None:
    svc = LLMService(settings)
    if not svc.available:
        await message.answer(MSG_DISABLED)
        return
    try:
        text = await factory(svc)
    except LLMNotConfiguredError:
        await message.answer(MSG_DISABLED)
    except LLMError as exc:
        await message.answer(f"⚠️ خطا در تولید متن: {exc}")
    else:
        await message.answer(text)
