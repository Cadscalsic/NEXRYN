"""Build sandbox-only alternative worlds."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


class AlternativeWorldBuilder:
    system_name = "alternative_world_builder"

    def build(self, counterfactual: Mapping[str, Any], current_world: Mapping[str, Any] | None = None) -> dict[str, Any]:
        current_world = current_world if isinstance(current_world, Mapping) else {}
        protected_violation = counterfactual.get("change_type") == "invariance_challenge" and counterfactual.get("protected_invariant")
        issues = ["protected_invariant_cannot_be_negated"] if protected_violation else []
        return {
            "system": self.system_name,
            "world_id": f"world:{counterfactual.get('counterfactual_id')}",
            "parent_world_id": current_world.get("world_id", "current_world"),
            "counterfactual_id": counterfactual.get("counterfactual_id"),
            "modified_assumptions": list(counterfactual.get("changed_assumption_ids", [counterfactual.get("changed_assumption_id")])),
            "preserved_invariants": list(current_world.get("preserved_invariants", [])),
            "relaxed_invariants": [] if protected_violation else [counterfactual.get("changed_assumption_id")],
            "sandbox_state": deepcopy(dict(current_world)),
            "world_consistency": 0.0 if protected_violation else 1.0,
            "world_valid": not protected_violation,
            "validation_issues": issues,
            "persistent_effects_forbidden": True,
        }


alternative_world_builder = AlternativeWorldBuilder()

__all__ = ["AlternativeWorldBuilder", "alternative_world_builder"]
