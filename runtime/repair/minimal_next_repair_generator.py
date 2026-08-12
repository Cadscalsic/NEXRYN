from __future__ import annotations

from typing import Any, Mapping


class MinimalNextRepairGenerator:
    """Generate minimal local repair candidates from current residual evidence."""

    def generate(
        self,
        residual_evidence: Mapping[str, Any] | None,
        *,
        parent_repair_iteration_id: str,
        parent_candidate_id: str,
        max_candidates: int = 3,
    ) -> dict[str, Any]:
        evidence = residual_evidence if isinstance(residual_evidence, Mapping) else {}
        locations = list(evidence.get("residual_locations") or [])
        actionable = (
            evidence.get("residual_type") == "localized_color_residual"
            and int(evidence.get("residual_difference_count", 0) or 0) > 0
            and bool(locations)
        )
        candidates = []
        if actionable:
            for index, location in enumerate(locations[:max_candidates], start=1):
                candidates.append({
                    "repair_candidate_id": f"{parent_candidate_id}:minimal:{index}",
                    "parent_candidate_id": parent_candidate_id,
                    "repair_operation": "recolor_residual_cells",
                    "target_locations": [location],
                    "expected_residual_reduction": 1,
                    "expected_information_gain": 1.0,
                    "expected_accuracy_gain": 0.01,
                })
        return {
            "next_repair_required": actionable,
            "parent_repair_iteration_id": parent_repair_iteration_id,
            "target_residual_fingerprint": evidence.get("residual_fingerprint"),
            "target_locations": locations,
            "repair_scope": "MINIMAL_LOCAL",
            "candidate_count": len(candidates),
            "repair_candidates": candidates,
        }


minimal_next_repair_generator = MinimalNextRepairGenerator()


__all__ = ["MinimalNextRepairGenerator", "minimal_next_repair_generator"]
