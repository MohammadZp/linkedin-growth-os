from __future__ import annotations

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

BLOCK_MESSAGE = "⛔️ دسترسی برای این حساب مجاز نیست."


def is_authorized(user_id: int | None, allowed_user_id: int) -> bool:
    """Fail-closed: access is denied unless an allowed id is configured and matches."""
    return bool(allowed_user_id and user_id is not None and user_id == allowed_user_id)


def _extract_user_and_target(
    event: TelegramObject,
) -> tuple[int | None, Message | CallbackQuery | None]:
    if isinstance(event, Update):
        obj: Message | CallbackQuery | None = event.message or event.callback_query
    elif isinstance(event, (Message, CallbackQuery)):
        obj = event
    else:
        obj = None
    user_id = obj.from_user.id if obj is not None and obj.from_user is not None else None
    return user_id, obj


class AccessControlMiddleware(BaseMiddleware):
    def __init__(self, allowed_user_id: int) -> None:
        self.allowed_user_id = allowed_user_id

    async def __call__(self, handler, event, data):
        user_id, obj = _extract_user_and_target(event)
        if not is_authorized(user_id, self.allowed_user_id):
            if isinstance(obj, Message):
                await obj.answer(BLOCK_MESSAGE)
            elif isinstance(obj, CallbackQuery):
                await obj.answer(BLOCK_MESSAGE, show_alert=True)
            return None
        return await handler(event, data)
