"""Candy categories and constitutional constraints for motivation."""

from __future__ import annotations

CANDY_TYPES = {
    "truth_candy",
    "curiosity_candy",
    "efficiency_candy",
    "generalization_candy",
    "reuse_candy",
    "recovery_candy",
}

PROTECTED_CANDIES = {
    "truth_candy",
    "generalization_candy",
}

CONSTITUTIONAL_CONSTRAINTS = {
    "modifies_constitutional_identity": False,
    "overrides_truth_governance": False,
    "bypasses_cognitive_budgets": False,
    "directly_controls_execution": False,
    "influences_locked_truths": False,
    "role": "motivation_suggests_governance_decides",
}


__all__ = [
    "CANDY_TYPES",
    "PROTECTED_CANDIES",
    "CONSTITUTIONAL_CONSTRAINTS",
]
