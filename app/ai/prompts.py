"""Prompt templates for every LLM use case.

Every prompt is built from data the user has already stored; templates explicitly
forbid inventing facts, statistics, links, or claims of work that wasn't done, and ask
for plain-text output so responses are easy to show and edit before use.
"""

from __future__ import annotations

_SYSTEM = (
    "You are the writing strategist for a software engineer building a personal brand "
    "on LinkedIn around AI engineering, backend/architecture, open-source, and tooling. "
    "Rules: never invent facts, statistics, numbers, names, URLs, or claims of work that "
    "was not provided; only use the information given; be concrete and specific; "
    "respond in plain text without markdown headings or code fences."
)


def suggest_ideas(topic: str | None, pillars: str) -> tuple[str, str]:
    user = "Suggest 5 concrete LinkedIn content ideas"
    if topic:
        user += f" related to: {topic}"
    user += (
        f". Content pillars and their shares: {pillars}. "
        "For each idea give a working title and one sentence on why it is interesting and "
        "what the reader gains. Keep each realistic for a solo engineer (1-2 hours of work)."
    )
    return _SYSTEM, user


def draft_hook(title: str, topic: str | None, audience: str | None) -> tuple[str, str]:
    user = (
        f'Draft 3 short opening hooks (max 2 sentences each) for a LinkedIn post titled "{title}"'
    )
    if topic:
        user += f" about {topic}"
    if audience:
        user += f" aimed at {audience}"
    user += ". Make them specific and curiosity-driven, not clickbait. Number them 1-3."
    return _SYSTEM, user


def draft_angle(title: str, topic: str | None, outcome: str | None) -> tuple[str, str]:
    user = f'Propose 3 distinct angles for a LinkedIn post titled "{title}"'
    if topic:
        user += f" about {topic}"
    if outcome:
        user += f". The desired business outcome is: {outcome}"
    user += ". For each angle give one line on the promise and one line on the proof/story."
    return _SYSTEM, user


def draft_video_script(title: str, topic: str | None) -> tuple[str, str]:
    user = f'Write a 30-60 second talking-head script for a short video titled "{title}"'
    if topic:
        user += f" about {topic}"
    user += (
        ". Structure: hook line, 3 key points, call to action. Write it as spoken lines, "
        "one per paragraph."
    )
    return _SYSTEM, user


def draft_message(
    name: str,
    role: str | None,
    company: str | None,
    notes: str | None,
    need: str | None,
) -> tuple[str, str]:
    user = f"Write a short, genuine LinkedIn connection-note draft to {name}"
    if role:
        user += f", who is {role}"
    if company:
        user += f" at {company}"
    user += ". Use ONLY the following context; if it is thin, keep the message short and "
    user += f"honest rather than padding it. Context: {notes or 'none'}; "
    user += f"their likely need: {need or 'unknown'}."
    user += " No false familiarity, no fabricated shared interests."
    return _SYSTEM, user


def summarize_stats(stats: str) -> tuple[str, str]:
    user = (
        "Here are this week's LinkedIn performance numbers:\n"
        f"{stats}\n\n"
        "Summarize in 3-4 bullet points. Separate observations (what the data shows) from "
        "hypotheses (possible explanations). Label each line either [مشاهده] or [فرضیه]. "
        "Do not overstate small samples, and do not treat impressions as business success."
    )
    return _SYSTEM, user


def propose_experiments(review: str) -> tuple[str, str]:
    user = (
        "Here is a weekly strategy review:\n"
        f"{review}\n\n"
        "Propose 2-3 concrete, low-cost experiments for next week. For each: what to change, "
        "what single metric to watch, and how long to run it. Keep each under 3 sentences."
    )
    return _SYSTEM, user
