"""Transparent evidence-based candidate scoring."""

from __future__ import annotations

from typing import Any, Mapping


DEFAULT_WEIGHTS = {
    "prediction_accuracy": 0.25,
    "residual_reduction": 0.12,
    "explanatory_power": 0.10,
    "semantic_support": 0.08,
    "context_support": 0.07,
    "truth_support": 0.08,
    "dependency_support": 0.07,
    "identity_compatibility": 0.05,
    "localization_quality": 0.08,
    "cross_example_consistency": 0.07,
    "governance_compatibility": 0.03,
}


class CandidateScorer:
    """Score candidates with visible components and penalties."""

    system_name = "candidate_scorer"

    def __init__(self, weights: Mapping[str, float] | None = None):
        self.weights = dict(weights or DEFAULT_WEIGHTS)

    def score(
        self,
        candidate: Mapping[str, Any],
        simulation: Mapping[str, Any],
        governance: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        governance = governance if isinstance(governance, Mapping) else {}
        accuracy = _score(simulation.get("prediction_accuracy", 0.0))
        difference_count = int(simulation.get("difference_count", 0) or 0)
        residual_reduction = max(0.0, 1.0 - min(1.0, difference_count / max(candidate.get("target_size", 1), 1)))
        components = {
            "prediction_accuracy": accuracy,
            "residual_reduction": round(residual_reduction, 4),
            "explanatory_power": _score(candidate.get("source_confidence", 0.0)),
            "semantic_support": _score(candidate.get("semantic_support", 0.0)),
            "context_support": _score(candidate.get("context_support", 0.0)),
            "truth_support": _score(candidate.get("truth_support", 0.0)),
            "dependency_support": _score(candidate.get("dependency_support", 0.0)),
            "identity_compatibility": _score(candidate.get("identity_support", 0.0)),
            "localization_quality": _score(candidate.get("localization_support", 0.0)),
            "cross_example_consistency": _score(candidate.get("cross_example_consistency", candidate.get("source_confidence", 0.0))),
            "governance_compatibility": 1.0 if governance.get("decision", "ALLOW_COMPETITION") == "ALLOW_COMPETITION" else 0.4,
            "source_reliability": min(_score(candidate.get("source_confidence", 0.0)), 0.12),
        }
        raw_score = sum(components[key] * self.weights[key] for key in self.weights)
        penalties = self._penalties(candidate, simulation, governance)
        final = max(0.0, raw_score - sum(penalties.values()))
        blockers = []
        if governance.get("decision") == "BLOCK_CANDIDATE":
            blockers.append("governance_blocked")
        if simulation.get("simulation_errors"):
            blockers.append("execution_errors")
        if candidate.get("metadata", {}).get("identity_violation"):
            blockers.append("identity_violation")
        return {
            "system": self.system_name,
            "candidate_id": candidate.get("candidate_id"),
            "final_score": round(final, 4),
            "score_components": components,
            "penalties": penalties,
            "eligible_for_selection": not blockers and final > 0.0,
            "selection_blockers": blockers,
        }

    def _penalties(
        self,
        candidate: Mapping[str, Any],
        simulation: Mapping[str, Any],
        governance: Mapping[str, Any],
    ) -> dict[str, float]:
        program_steps = candidate.get("program", {}).get("steps", []) or []
        penalties = {
            "unsupported_operations": 0.08 * len(simulation.get("unsupported_steps", []) or []),
            "execution_errors": 0.20 * len(simulation.get("simulation_errors", []) or []),
            "unexplained_residuals": 0.10 if int(simulation.get("difference_count", 0) or 0) > 0 else 0.0,
            "identity_violations": 0.30 if candidate.get("metadata", {}).get("identity_violation") else 0.0,
            "topology_destruction": 0.18 if _score(simulation.get("topology_score")) < 0.85 else 0.0,
            "excessive_program_complexity": 0.03 * max(0, len(program_steps) - 3),
            "low_source_diversity": 0.0,
            "missing_localization_evidence": 0.04 if _score(candidate.get("localization_support")) <= 0.0 else 0.0,
            "semantic_operation_mismatch": 0.08 if candidate.get("metadata", {}).get("semantic_operation_mismatch") else 0.0,
            "governance_penalty": 0.25 if governance.get("decision") == "BLOCK_CANDIDATE" else 0.0,
        }
        return {key: round(value, 4) for key, value in penalties.items()}


def _score(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


candidate_scorer = CandidateScorer()

__all__ = ["CandidateScorer", "candidate_scorer", "DEFAULT_WEIGHTS"]
