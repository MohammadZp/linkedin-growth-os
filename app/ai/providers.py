"""LLM provider abstraction with minimal async HTTP implementations.

Kept dependency-light on purpose: the app already ships aiohttp via aiogram, so we
call the REST endpoints directly instead of adding a provider SDK. Keys are read from
settings and never logged.
"""

from __future__ import annotations

import json
import logging
from typing import Protocol

import aiohttp

from app.config import Settings

logger = logging.getLogger(__name__)

ANTHROPIC_DEFAULT_MODEL = "claude-opus-5-5"
OPENAI_DEFAULT_MODEL = "gpt-4o-mini"


class LLMError(Exception):
    """A provider call failed or returned an unusable response."""


class LLMNotConfiguredError(Exception):
    """No provider is configured but an LLM call was requested."""


class LLMProvider(Protocol):
    name: str

    async def complete(self, prompt: str, *, system: str | None = None) -> str: ...


async def _post_json(url: str, headers: dict, body: dict) -> tuple[int, str]:
    async with (
        aiohttp.ClientSession() as session,
        session.post(url, json=body, headers=headers) as resp,
    ):
        status = resp.status
        raw = await resp.text()
    return status, raw


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.anthropic.com",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def complete(self, prompt: str, *, system: str | None = None) -> str:
        body: dict = {
            "model": self.model,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body["system"] = system
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        status, raw = await _post_json(f"{self.base_url}/v1/messages", headers, body)
        if status != 200:
            logger.warning("anthropic error HTTP %s", status)
            raise LLMError(f"anthropic returned HTTP {status}")
        data = json.loads(raw)
        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        if not text.strip():
            raise LLMError("anthropic returned no text")
        return text


class OpenAICompatibleProvider:
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def complete(self, prompt: str, *, system: str | None = None) -> str:
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        headers = {
            "authorization": f"Bearer {self.api_key}",
            "content-type": "application/json",
        }
        status, raw = await _post_json(
            f"{self.base_url}/chat/completions",
            headers,
            {"model": self.model, "messages": messages},
        )
        if status != 200:
            logger.warning("openai error HTTP %s", status)
            raise LLMError(f"openai returned HTTP {status}")
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
        if not content.strip():
            raise LLMError("openai returned empty content")
        return content


_ANTHROPIC_ALIASES = {"anthropic", "claude"}
_OPENAI_ALIASES = {"openai", "openai-compatible", "openai_compatible"}


def get_provider(settings: Settings) -> LLMProvider | None:
    """Return a provider for the configured settings, or ``None`` when not configured."""
    if not settings.ai_enabled:
        return None
    provider = settings.ai_provider.strip().lower()
    model = settings.ai_model.strip()
    base_url = settings.ai_base_url.strip()

    if provider in _ANTHROPIC_ALIASES:
        return AnthropicProvider(
            settings.ai_api_key,
            model or ANTHROPIC_DEFAULT_MODEL,
            base_url or "https://api.anthropic.com",
        )
    if provider in _OPENAI_ALIASES:
        return OpenAICompatibleProvider(
            settings.ai_api_key,
            model or OPENAI_DEFAULT_MODEL,
            base_url or "https://api.openai.com/v1",
        )
    logger.warning("Unknown ai_provider %r; AI is disabled", settings.ai_provider)
    return None
