"""LLM service: thin layer over the provider + prompt templates.

Each method returns the raw assistant text for the caller to display and the user to
edit/approve. Nothing here sends a message to a contact or publishes content.
"""

from __future__ import annotations

from app.ai import prompts
from app.ai.providers import (
    LLMError,
    LLMNotConfiguredError,
    LLMProvider,
    get_provider,
)
from app.config import Settings


class LLMService:
    def __init__(self, settings: Settings, provider: LLMProvider | None = None) -> None:
        self.settings = settings
        self.provider = provider if provider is not None else get_provider(settings)

    @property
    def available(self) -> bool:
        return self.provider is not None

    async def _complete(self, system: str, user: str) -> str:
        if self.provider is None:
            raise LLMNotConfiguredError("AI is not configured")
        text = (await self.provider.complete(user, system=system)).strip()
        if not text:
            raise LLMError("provider returned empty text")
        return text

    async def suggest_ideas(self, topic: str | None = None) -> str:
        pillars = ", ".join(f"{k} {v:.0%}" for k, v in self.settings.content_pillars.items())
        system, user = prompts.suggest_ideas(topic, pillars)
        return await self._complete(system, user)

    async def draft_hook(
        self, *, title: str, topic: str | None = None, audience: str | None = None
    ) -> str:
        system, user = prompts.draft_hook(title, topic, audience)
        return await self._complete(system, user)

    async def draft_angle(
        self, *, title: str, topic: str | None = None, outcome: str | None = None
    ) -> str:
        system, user = prompts.draft_angle(title, topic, outcome)
        return await self._complete(system, user)

    async def draft_video_script(self, *, title: str, topic: str | None = None) -> str:
        system, user = prompts.draft_video_script(title, topic)
        return await self._complete(system, user)

    async def draft_message(
        self,
        *,
        name: str,
        role: str | None = None,
        company: str | None = None,
        notes: str | None = None,
        need: str | None = None,
    ) -> str:
        system, user = prompts.draft_message(name, role, company, notes, need)
        return await self._complete(system, user)

    async def summarize_stats(self, stats: str) -> str:
        system, user = prompts.summarize_stats(stats)
        return await self._complete(system, user)

    async def propose_experiments(self, review: str) -> str:
        system, user = prompts.propose_experiments(review)
        return await self._complete(system, user)
