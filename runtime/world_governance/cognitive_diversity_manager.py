"""Maintain healthy cognitive diversity without weakening identity."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.world_governance.constitutional_identity import protect_core


class CognitiveDiversityManager:
    def evaluate(self, runtime_context: Mapping[str, Any] | None = None) -> dict[str, Any]:
        context = dict(runtime_context or {})
        concept_share = self._number(context.get("dominant_concept_share"))
        strategy_share = self._number(context.get("dominant_strategy_share"))
        active_paths = self._number(context.get("active_reasoning_paths"))
        explanation_count = self._number(context.get("alternative_explanations"))
        transfer_signal = self._number(context.get("transfer_learning_signal"))

        monopoly_pressure = max(concept_share, strategy_share)
        diversity_score = min(
            1.0,
            max(0.0, 0.35 * min(active_paths / 3.0, 1.0)
                + 0.25 * min(explanation_count / 3.0, 1.0)
                + 0.20 * transfer_signal
                + 0.20 * (1.0 - monopoly_pressure)),
        )
        protected = protect_core(context)

        interventions: list[str] = []
        if concept_share >= 0.65:
            interventions.append("prevent_concept_monopoly")
        if strategy_share >= 0.65:
            interventions.append("prevent_strategy_domination")
        if active_paths <= 1:
            interventions.append("encourage_alternative_strategies")
        if explanation_count <= 1:
            interventions.append("request_multiple_explanations")
        if transfer_signal < 0.25:
            interventions.append("encourage_transfer_learning")

        if protected["protected_core_touched"]:
            interventions = [
                "protect_identity_continuity",
                "protect_truth_integrity",
                "block_diversity_pressure_on_constitution",
            ]
            diversity_score = min(diversity_score, 0.25)

        return {
            "diversity_score": diversity_score,
            "monopoly_pressure": monopoly_pressure,
            "interventions": sorted(set(interventions)),
            "identity_safe": not protected["protected_core_touched"],
            "reason": (
                "diversity_pressure_touches_protected_core"
                if protected["protected_core_touched"]
                else "diversity_managed_with_identity_constraints"
            ),
        }

    def impact_for(self, target_type: str, opportunity_type: str) -> float:
        if opportunity_type in {
            "underrepresented_context",
            "missing_conceptual_coverage",
        }:
            return 0.6
        if target_type in {"context", "strategy"}:
            return 0.35
        if opportunity_type == "expensive_reasoning_loops":
            return -0.05
        return 0.15

    def _number(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


cognitive_diversity_manager = CognitiveDiversityManager()


__all__ = [
    "CognitiveDiversityManager",
    "cognitive_diversity_manager",
]
