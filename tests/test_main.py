from __future__ import annotations

import asyncio

import pytest
from aiogram.exceptions import TelegramRetryAfter
from app.main import _call_with_retry


class _FlakyCall:
    def __init__(self, failures: int = 0) -> None:
        self.calls = 0
        self.failures = failures

    async def __call__(self) -> str:
        self.calls += 1
        if self.calls <= self.failures:
            raise TelegramRetryAfter(None, "flood control", 0)
        return "ok"


async def _noop_sleep(seconds: float) -> None:
    return


@pytest.mark.asyncio
async def test_call_with_retry_succeeds_immediately(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", _noop_sleep)
    flaky = _FlakyCall(failures=0)
    assert await _call_with_retry(flaky) == "ok"
    assert flaky.calls == 1


@pytest.mark.asyncio
async def test_call_with_retry_retries_on_flood(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", _noop_sleep)
    flaky = _FlakyCall(failures=2)
    assert await _call_with_retry(flaky) == "ok"
    assert flaky.calls == 3


@pytest.mark.asyncio
async def test_call_with_retry_raises_after_exhaustion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(asyncio, "sleep", _noop_sleep)
    flaky = _FlakyCall(failures=99)
    with pytest.raises(TelegramRetryAfter):
        await _call_with_retry(flaky, attempts=5)
    assert flaky.calls == 5
