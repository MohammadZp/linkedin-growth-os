from __future__ import annotations

import asyncio

import pytest
from aiogram.exceptions import TelegramRetryAfter
from app.main import _reset_webhook


class _FakeBot:
    def __init__(self, failures: int = 0) -> None:
        self.calls = 0
        self.failures = failures

    async def delete_webhook(self, drop_pending_updates: bool = False) -> None:
        self.calls += 1
        if self.calls <= self.failures:
            raise TelegramRetryAfter(None, "flood control", 0)


async def _noop_sleep(seconds: float) -> None:
    return


@pytest.mark.asyncio
async def test_reset_webhook_succeeds_immediately(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", _noop_sleep)
    bot = _FakeBot(failures=0)
    await _reset_webhook(bot)
    assert bot.calls == 1


@pytest.mark.asyncio
async def test_reset_webhook_retries_on_flood(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", _noop_sleep)
    bot = _FakeBot(failures=2)
    await _reset_webhook(bot)
    assert bot.calls == 3


@pytest.mark.asyncio
async def test_reset_webhook_gives_up_gracefully(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", _noop_sleep)
    bot = _FakeBot(failures=99)
    await _reset_webhook(bot)  # must not raise
    assert bot.calls == 5  # default attempts
