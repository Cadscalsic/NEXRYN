"""Generate bounded one-assumption counterfactual alternatives."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


class CounterfactualGenerator:
    system_name = "counterfactual_generator"

    def generate(
        self,
        candidate: Mapping[str, Any],
        assumptions: list[Mapping[str, Any]],
        arena_alternatives: list[Mapping[str, Any]] | None = None,
        residual_cells: list[list[int]] | None = None,
        budget: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        budget = budget if isinstance(budget, Mapping) else {}
        limit = int(budget.get("max_counterfactuals", 4) or 4)
        generated = []
        for assumption in assumptions:
            if len(generated) >= limit:
                break
            if not assumption.get("challengeable"):
                continue
            cf = self._from_assumption(candidate, assumption, residual_cells)
            if cf:
                generated.append(cf)
        if residual_cells and len(generated) < limit:
            generated.append({
                "counterfactual_id": f"counterfactual:{candidate.get('candidate_id')}:residual_guided_mutation",
                "parent_candidate_id": candidate.get("candidate_id"),
                "source_hypothesis_id": candidate.get("hypothesis_id"),
                "changed_assumption_id": "residual_alignment",
                "changed_assumption_ids": ["residual_alignment"],
                "change_type": "residual_guided_mutation",
                "original_value": "unexplained_residual",
                "counterfactual_value": residual_cells,
                "counterfactual_program": {
                    "step_count": 1,
                    "steps": [
                        {
                            "operation": "construct_path",
                            "parameters": {
                                "path_color": 1,
                                "path_cells": residual_cells,
                            },
                        }
                    ],
                },
                "generation_reason": "residual_guided_mutation",
                "expected_information_gain": 0.9,
                "generation_confidence": 0.8,
                "governance_state": "PENDING",
            })
        for alt in arena_alternatives or []:
            if len(generated) >= limit:
                break
            if not isinstance(alt, Mapping) or alt.get("candidate_id") == candidate.get("candidate_id"):
                continue
            generated.append(self._from_alternative(candidate, alt))
        generated.sort(key=lambda item: item["expected_information_gain"], reverse=True)
        return {
            "system": self.system_name,
            "generated_counterfactuals": generated[:limit],
            "generated_counterfactual_count": len(generated[:limit]),
            "generation_success": bool(generated),
        }

    def _from_assumption(self, candidate, assumption, residual_cells):
        program = deepcopy(candidate.get("program", {"step_count": 0, "steps": []}))
        change_type = self._change_type(assumption)
        original = assumption.get("value")
        counter_value = self._counter_value(change_type, original)
        reason = f"challenge_{assumption.get('assumption_type')}"
        if change_type == "residual_guided_mutation" and residual_cells and program.get("steps"):
            step = program["steps"][0]
            params = step.setdefault("parameters", {})
            params["path_cells"] = residual_cells
            params.setdefault("path_color", 1)
            step["operation"] = "construct_path"
            counter_value = residual_cells
            reason = "residual_guided_mutation"
        elif change_type == "color_mapping_variation" and program.get("steps"):
            mapping = self._alternate_mapping(original)
            program["steps"][0].setdefault("parameters", {})["color_mapping"] = mapping
            counter_value = mapping
        elif change_type == "hypothesis_negation":
            program = {"step_count": 0, "steps": []}
            counter_value = "hypothesis_absent"
        return {
            "counterfactual_id": f"counterfactual:{candidate.get('candidate_id')}:{len(str(original))}:{change_type}",
            "parent_candidate_id": candidate.get("candidate_id"),
            "source_hypothesis_id": candidate.get("hypothesis_id"),
            "changed_assumption_id": assumption.get("assumption_id"),
            "changed_assumption_ids": [assumption.get("assumption_id")],
            "change_type": change_type,
            "original_value": original,
            "counterfactual_value": counter_value,
            "counterfactual_program": program,
            "generation_reason": reason,
            "expected_information_gain": 0.85 if change_type == "residual_guided_mutation" else 0.65,
            "generation_confidence": 0.75,
            "governance_state": "PENDING",
        }

    def _from_alternative(self, candidate, alternative):
        return {
            "counterfactual_id": f"counterfactual:{candidate.get('candidate_id')}:alternative:{alternative.get('candidate_id')}",
            "parent_candidate_id": candidate.get("candidate_id"),
            "source_hypothesis_id": alternative.get("hypothesis_id"),
            "changed_assumption_id": "arena_alternative",
            "changed_assumption_ids": ["arena_alternative"],
            "change_type": "operation_substitution",
            "original_value": candidate.get("operation"),
            "counterfactual_value": alternative.get("operation"),
            "counterfactual_program": deepcopy(alternative.get("program", {"step_count": 0, "steps": []})),
            "generation_reason": "validated_arena_alternative",
            "expected_information_gain": 0.80,
            "generation_confidence": _score(alternative.get("source_confidence", 0.7)),
            "governance_state": "PENDING",
        }

    def _change_type(self, assumption):
        kind = assumption.get("assumption_type")
        if kind == "color_mapping_assumption":
            return "color_mapping_variation"
        if kind == "target_region_assumption":
            return "residual_guided_mutation"
        if kind == "operation_assumption":
            return "operation_substitution"
        if kind == "scope_assumption":
            return "scope_variation"
        return "hypothesis_negation"

    def _counter_value(self, change_type, original):
        if change_type == "scope_variation":
            return "global" if original == "local" else "local"
        if change_type == "operation_substitution":
            return {"preserve_grid": "replace_color", "replace_color": "preserve_grid"}.get(str(original), "preserve_grid")
        return f"not_{original}"

    def _alternate_mapping(self, original):
        if isinstance(original, Mapping) and original:
            source = next(iter(original.keys()))
            value = int(next(iter(original.values())))
            return {source: value + 1}
        return {1: 2}


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


counterfactual_generator = CounterfactualGenerator()

__all__ = ["CounterfactualGenerator", "counterfactual_generator"]
