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
        penalty_total = sum(penalties.values())
        final = max(0.0, raw_score - penalty_total)
        blockers = []
        if governance.get("decision") == "BLOCK_CANDIDATE":
            blockers.append("governance_blocked")
        if simulation.get("simulation_errors"):
            blockers.append("execution_errors")
        if candidate.get("metadata", {}).get("identity_violation"):
            blockers.append("identity_violation")
        weighted_contributions = {
            key: components[key] * weight
            for key, weight in self.weights.items()
        }
        raw_inputs = {
            "prediction_accuracy": simulation.get("prediction_accuracy"),
            "difference_count": simulation.get("difference_count"),
            "target_size": candidate.get("target_size"),
            "source_confidence": candidate.get("source_confidence"),
            "semantic_support": candidate.get("semantic_support"),
            "context_support": candidate.get("context_support"),
            "truth_support": candidate.get("truth_support"),
            "dependency_support": candidate.get("dependency_support"),
            "identity_support": candidate.get("identity_support"),
            "localization_support": candidate.get("localization_support"),
            "truth_support_metric": candidate.get("truth_support_metric"),
            "localization_quality_metric": candidate.get(
                "localization_quality_metric"
            ),
            "cross_example_consistency": candidate.get("cross_example_consistency"),
            "governance_decision": governance.get("decision", "ALLOW_COMPETITION"),
            "unsupported_step_count": len(simulation.get("unsupported_steps", []) or []),
            "simulation_error_count": len(simulation.get("simulation_errors", []) or []),
            "topology_score": simulation.get("topology_score"),
            "program_step_count": len(candidate.get("program", {}).get("steps", []) or []),
            "identity_violation": bool(candidate.get("metadata", {}).get("identity_violation")),
            "semantic_operation_mismatch": bool(candidate.get("metadata", {}).get("semantic_operation_mismatch")),
        }
        return {
            "system": self.system_name,
            "candidate_id": candidate.get("candidate_id"),
            "final_score": round(final, 4),
            "score_components": components,
            "penalties": penalties,
            "score_composition": {
                "schema_version": "candidate_score_composition.v1",
                "producer": self.system_name,
                "raw_inputs": raw_inputs,
                "normalized_components": dict(components),
                "weights": dict(self.weights),
                "weighted_contributions": weighted_contributions,
                "diagnostic_unweighted_components": [
                    key for key in components if key not in self.weights
                ],
                "raw_score_unrounded": raw_score,
                "penalty_inputs": {
                    "unsupported_step_count": raw_inputs["unsupported_step_count"],
                    "simulation_error_count": raw_inputs["simulation_error_count"],
                    "difference_count": raw_inputs["difference_count"],
                    "identity_violation": raw_inputs["identity_violation"],
                    "topology_score": raw_inputs["topology_score"],
                    "program_step_count": raw_inputs["program_step_count"],
                    "localization_support": raw_inputs["localization_support"],
                    "semantic_operation_mismatch": raw_inputs["semantic_operation_mismatch"],
                    "governance_decision": raw_inputs["governance_decision"],
                },
                "penalties": dict(penalties),
                "penalty_total": penalty_total,
                "nonnegative_clamp_applied": raw_score - penalty_total < 0.0,
                "final_score_unrounded": final,
                "rounding_policy": "python_round_half_even_4_decimal_places",
                "rounding_places": 4,
                "authority": "OBSERVATION_ONLY",
                "behavioral_authority": "NONE",
            },
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
