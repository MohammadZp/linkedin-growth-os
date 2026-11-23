from __future__ import annotations

from app.ai import prompts


def test_suggest_ideas_includes_topic_and_no_fabrication() -> None:
    system, user = prompts.suggest_ideas("RAG", "open_source_deep_dive 30%")
    assert "never invent" in system
    assert "RAG" in user


def test_draft_message_uses_only_provided_info() -> None:
    system, user = prompts.draft_message("Jane", "CTO", "Acme", "loves AI", "content")
    assert "never invent" in system
    assert "Jane" in user
    assert "Acme" in user
    assert "false familiarity" in user


def test_summarize_stats_separates_observation_and_hypothesis() -> None:
    _, user = prompts.summarize_stats("impressions 100, leads 0")
    assert "مشاهده" in user
    assert "فرضیه" in user


def test_propose_experiments_is_grounded() -> None:
    _, user = prompts.propose_experiments("week 1 review")
    assert "metric to watch" in user
    assert "week 1 review" in user
