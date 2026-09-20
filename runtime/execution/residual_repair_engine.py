from __future__ import annotations

from typing import Any


class ResidualRepairEngine:
    """Generate localized repair proposals from residual localization evidence."""

    def repair(
        self,
        residual_report: dict[str, Any] | None,
        *,
        program: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        residual = residual_report if isinstance(residual_report, dict) else {}
        missing = residual.get("missing_primitives") if isinstance(residual.get("missing_primitives"), list) else []
        regions = residual.get("residual_regions") if isinstance(residual.get("residual_regions"), list) else []
        proposals = []
        for index, primitive in enumerate(missing, start=1):
            proposals.append({
                "repair_id": f"repair_{index}",
                "repair_type": "localized_repair",
                "primitive": primitive,
                "operation": self._operation_for(primitive),
                "target_region": regions[0] if regions else {},
                "residual_cells": residual.get("residual_cells", []),
                "expected_effect": "reduce_residual",
            })
        return {
            "repair_proposals": proposals,
            "localized_repairs": [proposal for proposal in proposals if proposal["repair_type"] == "localized_repair"],
            "primitive_repairs": [proposal["primitive"] for proposal in proposals],
            "object_repairs": residual.get("residual_objects", []),
            "region_repairs": regions,
            "generated_repairs": len(proposals),
            "residual_repair_success": 1 if proposals else 0,
            "residual_repair_operational": True,
        }

    def _operation_for(self, primitive: str) -> str:
        return {
            "recolor": "add_missing_recolor_step",
            "propagate": "add_missing_growth_step",
            "split": "add_missing_removal_step",
            "compose": "add_missing_composition_step",
        }.get(primitive, f"add_missing_{primitive}_step")


residual_repair_engine = ResidualRepairEngine()


__all__ = ["ResidualRepairEngine", "residual_repair_engine"]
