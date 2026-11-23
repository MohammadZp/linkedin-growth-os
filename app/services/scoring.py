"""Transparent idea prioritisation.

Each criterion is scored 1–5 (5 = best). ``effort_required`` is inverted before it
contributes to the total, so *less* effort yields a *higher* score::

    contribution = (6 - effort_required)   # for effort_required only

The final ``priority_score`` is a weighted average on the 1–5 scale using the
weights configured in ``Settings.idea_weights`` (which sum to 1.0).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.config import Settings
from app.database.models import Idea

CRITERIA = [
    "audience_relevance",
    "demonstrability",
    "technical_depth",
    "business_relevance",
    "effort_required",
]


@dataclass
class ScoreBreakdown:
    score: float
    raw: dict[str, int | None] = field(default_factory=dict)
    components: dict[str, float] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        return all(self.raw.get(c) is not None for c in CRITERIA)


class IdeaScorer:
    def __init__(self, settings: Settings) -> None:
        self.weights = settings.idea_weights

    def contribution(self, criterion: str, value: int) -> float:
        inverted = 6 - value if criterion == "effort_required" else value
        return round(inverted * self.weights.get(criterion, 0.0), 2)

    def compute(self, idea: Idea) -> ScoreBreakdown:
        raw = {c: getattr(idea, c) for c in CRITERIA}
        components: dict[str, float] = {}
        total = 0.0
        for criterion, value in raw.items():
            if value is None:
                continue
            weighted = self.contribution(criterion, value)
            components[criterion] = weighted
            total += weighted
        return ScoreBreakdown(score=round(total, 2), raw=raw, components=components)

    def apply(self, idea: Idea) -> ScoreBreakdown:
        """Compute and persist the score onto the idea, returning the breakdown."""
        breakdown = self.compute(idea)
        idea.priority_score = breakdown.score if breakdown.is_complete else None
        return breakdown
