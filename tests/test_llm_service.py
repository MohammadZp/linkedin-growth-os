from __future__ import annotations

import pytest
from app.ai.providers import (
    AnthropicProvider,
    LLMNotConfiguredError,
    OpenAICompatibleProvider,
    get_provider,
)
from app.config import Settings
from app.services.llm import LLMService


class FakeProvider:
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    async def complete(self, prompt: str, *, system: str | None = None) -> str:
        self.calls.append((prompt, system))
        return "Fake output"


def test_get_provider_none_when_disabled() -> None:
    assert get_provider(Settings(_env_file=None)) is None


def test_get_provider_anthropic_defaults_to_opus() -> None:
    p = get_provider(Settings(_env_file=None, ai_provider="anthropic", ai_api_key="k"))
    assert isinstance(p, AnthropicProvider)
    assert p.model == "claude-opus-5-5"


def test_get_provider_openai_uses_configured_model() -> None:
    p = get_provider(
        Settings(_env_file=None, ai_provider="openai", ai_api_key="k", ai_model="gpt-x")
    )
    assert isinstance(p, OpenAICompatibleProvider)
    assert p.model == "gpt-x"


async def test_service_available_and_passes_data_to_prompt() -> None:
    fake = FakeProvider()
    svc = LLMService(Settings(_env_file=None), provider=fake)
    assert svc.available is True
    text = await svc.suggest_ideas("agents")
    assert text == "Fake output"
    assert fake.calls and "agents" in fake.calls[0][0]


async def test_service_not_configured_raises() -> None:
    svc = LLMService(Settings(_env_file=None))
    assert svc.available is False
    with pytest.raises(LLMNotConfiguredError):
        await svc.suggest_ideas()
