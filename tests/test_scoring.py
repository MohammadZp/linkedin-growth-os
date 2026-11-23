from __future__ import annotations

from app.config import Settings
from app.database.models import Idea
from app.services.scoring import IdeaScorer
from sqlalchemy.orm import Session


def _idea(**scores: int) -> Idea:
    return Idea(title="Test idea", **scores)


def test_equal_scores_yield_same_value() -> None:
    scorer = IdeaScorer(Settings(_env_file=None))
    idea = _idea(
        audience_relevance=3,
        demonstrability=3,
        technical_depth=3,
        business_relevance=3,
        effort_required=3,
    )
    breakdown = scorer.compute(idea)
    assert breakdown.is_complete
    assert breakdown.score == 3.0


def test_perfect_scores() -> None:
    scorer = IdeaScorer(Settings(_env_file=None))
    idea = _idea(
        audience_relevance=5,
        demonstrability=5,
        technical_depth=5,
        business_relevance=5,
        effort_required=1,
    )
    assert scorer.compute(idea).score == 5.0


def test_effort_is_inverted() -> None:
    scorer = IdeaScorer(Settings(_env_file=None))
    assert scorer.contribution("effort_required", 1) == 0.5  # lowest effort -> highest share
    assert scorer.contribution("effort_required", 5) == 0.1


def test_apply_incomplete_sets_no_score(session: Session) -> None:
    scorer = IdeaScorer(Settings(_env_file=None))
    idea = _idea(audience_relevance=5)
    breakdown = scorer.apply(idea)
    assert not breakdown.is_complete
    assert idea.priority_score is None
