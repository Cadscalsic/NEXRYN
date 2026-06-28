from __future__ import annotations

from typing import Any


def evaluate_truth_activation(
    context_count: int = 0,
    dependency_chain_coverage: float = 0.0,
    promotion_score: float | None = None,
    candidate_valid: bool | None = None,
    coverage_threshold: float = 0.05,
) -> dict[str, Any]:
    context_count = int(context_count or 0)
    coverage = float(dependency_chain_coverage or 0.0)
    promotion_evaluation_enabled = (
        context_count > 0 and coverage > coverage_threshold
    )
    truth_candidate_enabled = (
        promotion_score is not None if promotion_evaluation_enabled else False
    )
    truth_commit_enabled = bool(candidate_valid is True)
    return {
        "system": "truth_activation_policy",
        "report_state": "final",
        "context_count": context_count,
        "dependency_chain_coverage": coverage,
        "coverage_threshold": coverage_threshold,
        "promotion_evaluation_enabled": promotion_evaluation_enabled,
        "truth_candidate_enabled": truth_candidate_enabled,
        "truth_commit_enabled": truth_commit_enabled,
        "activation_reason": (
            "contexts_and_dependency_coverage_available"
            if promotion_evaluation_enabled
            else "awaiting_contexts_or_dependency_coverage"
        ),
    }


__all__ = ["evaluate_truth_activation"]
