"""Public portfolio interface for JobHunt MU recommendation matching.

The production/private project contains the complete scoring strategy, normalization
rules, weighting, tuning and evaluation logic. Those details are intentionally not
published in this recruiter-facing repository.

This module preserves the service contract and demonstrates the architecture without
exposing the project's private recommendation implementation.
"""
from __future__ import annotations

from typing import Iterable


def match_resume_to_job(*, resume_text: str, profile_skills: Iterable[str], job) -> dict:
    """Return the public shape of a JobHunt MU compatibility result.

    Private implementation stages include resume/job normalization, skill evidence
    extraction, relevance analysis, explainability and confidence calculation.
    Exact rules, weights and tuning are intentionally omitted from this showcase.
    """
    raise NotImplementedError(
        "The full JobHunt MU recommendation engine is private. "
        "See README.md and ARCHITECTURE.md for the public architecture."
    )
