from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Telegram ---
    telegram_bot_token: str = ""
    telegram_allowed_user_id: int = 0

    # --- Database ---
    database_url: str = "sqlite:///./data/linkedin_growth.db"

    # --- Time & scheduling ---
    timezone: str = "Asia/Tehran"
    daily_briefing_time: str = "08:00"
    weekly_review_day: int = 4  # 0=Monday .. 6=Sunday (Friday)
    weekly_review_time: str = "18:00"

    # --- Strategy ---
    publishing_target_per_week: int = 3
    max_daily_tasks: int = 3
    default_content_language: str = "en"
    content_pillars: dict[str, float] = {
        "open_source_deep_dive": 0.30,
        "tool_experiment": 0.30,
        "personal_project": 0.25,
        "educational_post": 0.15,
    }
    idea_weights: dict[str, float] = {
        "audience_relevance": 0.25,
        "demonstrability": 0.20,
        "technical_depth": 0.20,
        "business_relevance": 0.25,
        "effort_required": 0.10,
    }

    # --- Optional LLM ---
    ai_provider: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_base_url: str = ""

    @property
    def ai_enabled(self) -> bool:
        return bool(self.ai_provider and self.ai_api_key)

    @field_validator("content_pillars", "idea_weights", mode="before")
    @classmethod
    def _parse_json_dict(cls, value: Any) -> Any:
        if isinstance(value, str):
            return json.loads(value)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
