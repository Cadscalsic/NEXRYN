"""Compare original candidate evidence against counterfactual simulations."""

from __future__ import annotations

from typing import Any, Mapping


class CounterfactualEvidenceComparator:
    system_name = "counterfactual_evidence_comparator"

    def compare(self, original_candidate_id: str, original_simulation: Mapping[str, Any], simulations: list[Mapping[str, Any]]) -> dict[str, Any]:
        original_accuracy = _score(original_simulation.get("prediction_accuracy"))
        original_residual = int(original_simulation.get("difference_count", 0) or 0)
        rows = []
        best = None
        for sim in simulations:
            accuracy_delta = round(_score(sim.get("prediction_accuracy")) - original_accuracy, 4)
            residual_delta = original_residual - int(sim.get("difference_count", 0) or 0)
            evidence = self._class(accuracy_delta, residual_delta, sim)
            row = {
                "counterfactual_id": sim.get("counterfactual_id"),
                "evidence_class": evidence,
                "accuracy_delta": accuracy_delta,
                "residual_delta": residual_delta,
                "structural_delta": round(_score(sim.get("structural_score")) - _score(original_simulation.get("structural_score")), 4),
                "color_delta": round(_score(sim.get("color_score")) - _score(original_simulation.get("color_score")), 4),
                "topology_delta": round(_score(sim.get("topology_score")) - _score(original_simulation.get("topology_score")), 4),
                "identity_delta": round(_score(sim.get("identity_score", 1.0)) - _score(original_simulation.get("identity_score", 1.0)), 4),
                "explanation_delta": accuracy_delta,
                "program_complexity_delta": len(sim.get("execution_trace", []) or []) - len(original_simulation.get("execution_trace", []) or []),
                "localization_delta": residual_delta,
                "execution_cost_delta": _score(sim.get("simulation_duration")),
                "explanation": f"accuracy_delta={accuracy_delta}; residual_delta={residual_delta}",
                "significance": round(abs(accuracy_delta) + max(0, residual_delta) * 0.05, 4),
            }
            rows.append(row)
            if best is None or _score(sim.get("prediction_accuracy")) > _score(best.get("prediction_accuracy")):
                best = sim
        best_id = best.get("counterfactual_id") if best else None
        original_best = not best or _score(best.get("prediction_accuracy")) <= original_accuracy
        return {
            "system": self.system_name,
            "original_candidate_id": original_candidate_id,
            "counterfactual_comparisons": rows,
            "best_counterfactual_id": best_id,
            "original_candidate_still_best": original_best,
        }

    def _class(self, accuracy_delta, residual_delta, sim):
        if _score(sim.get("identity_score", 1.0)) < 0.8:
            return "INCONCLUSIVE"
        if accuracy_delta >= 0.05 or residual_delta > 0:
            return "SUPPORTS_ALTERNATIVE"
        if accuracy_delta <= -0.05 or residual_delta < 0:
            return "SUPPORTS_ORIGINAL"
        return "INCONCLUSIVE"


def _score(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


counterfactual_evidence_comparator = CounterfactualEvidenceComparator()

__all__ = ["CounterfactualEvidenceComparator", "counterfactual_evidence_comparator"]
