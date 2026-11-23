from __future__ import annotations

from app.config import Settings


def test_defaults() -> None:
    s = Settings(_env_file=None)
    assert s.timezone == "Asia/Tehran"
    assert s.publishing_target_per_week == 3
    assert s.max_daily_tasks == 3
    assert s.ai_enabled is False


def test_content_pillars_from_json_env() -> None:
    s = Settings(
        _env_file=None,
        content_pillars='{"tool_experiment":0.5,"educational_post":0.5}',
    )
    assert s.content_pillars == {"tool_experiment": 0.5, "educational_post": 0.5}


def test_ai_enabled_requires_provider_and_key() -> None:
    assert Settings(_env_file=None, ai_provider="anthropic", ai_api_key="k").ai_enabled is True
    assert Settings(_env_file=None, ai_provider="anthropic", ai_api_key="").ai_enabled is False
    assert Settings(_env_file=None, ai_provider="", ai_api_key="k").ai_enabled is False
