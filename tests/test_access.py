from __future__ import annotations

from datetime import datetime

import pytest
from aiogram.types import Chat, Message, User
from app.bot.middlewares.access import (
    AccessControlMiddleware,
    _extract_user_and_target,
    is_authorized,
)


def test_is_authorized() -> None:
    assert is_authorized(123, 123) is True
    assert is_authorized(123, 456) is False
    assert is_authorized(None, 123) is False
    assert is_authorized(123, 0) is False  # fail closed when unconfigured


def _make_message(user_id: int) -> Message:
    user = User(id=user_id, is_bot=False, first_name="Test")
    chat = Chat(id=user_id, type="private")
    return Message(message_id=1, date=datetime.now(), chat=chat, from_user=user)


def test_extract_user_from_message() -> None:
    msg = _make_message(123)
    user_id, obj = _extract_user_and_target(msg)
    assert user_id == 123
    assert obj is msg


@pytest.mark.asyncio
async def test_middleware_allows_authorized_user() -> None:
    called: list[int] = []

    async def handler(event, data):
        called.append(1)
        return "ok"

    middleware = AccessControlMiddleware(123)
    result = await middleware(handler, _make_message(123), {})
    assert result == "ok"
    assert called == [1]
