"""Spatially constrained residual repair proposals."""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np


class SpatialResidualRepair:
    system_name = "spatial_residual_repair"

    def propose(
        self,
        predicted_output: Any,
        residual_report: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        predicted = np.array(predicted_output)
        report = residual_report if isinstance(residual_report, Mapping) else {}
        context = runtime_context if isinstance(runtime_context, Mapping) else {}
        candidates = []
        for cell in report.get("residual_cells", []) or []:
            location = cell.get("location", [])
            if len(location) != 2:
                continue
            row, col = int(location[0]), int(location[1])
            for candidate in cell.get("candidate_color_values", []) or []:
                confidence = float(candidate.get("confidence", 0.0) or 0.0)
                if cell.get("relative_position", {}).get("on_boundary"):
                    confidence = min(1.0, confidence + 0.03)
                if self._has_spatial_context(context):
                    confidence = min(1.0, confidence + 0.04)
                candidates.append({
                    "location": [row, col],
                    "candidate_value": candidate.get("value"),
                    "repair_strategy": "spatial_local_residual_repair",
                    "repair_confidence": round(confidence, 4),
                    "spatial_constraints": {
                        "relative_position": cell.get("relative_position", {}),
                        "neighbor_colors": cell.get("neighbor_colors", {}),
                        "inside_outside_signal": self._has_spatial_context(context),
                    },
                })
        candidates.sort(
            key=lambda item: item.get("repair_confidence", 0.0),
            reverse=True,
        )
        return {
            "system": self.system_name,
            "report_state": "final",
            "candidate_count": len(candidates),
            "repair_candidates": candidates,
            "spatial_repair_available": bool(candidates and predicted.size),
        }

    def _has_spatial_context(self, context):
        text = " ".join(
            str(value).lower()
            for key in (
                "active_concepts",
                "attributed_concepts",
                "prioritized_concepts",
            )
            for value in (context.get(key, []) or [])
            if isinstance(context.get(key, []), list)
        )
        return any(
            signal in text
            for signal in (
                "inside_outside",
                "containment",
                "relative_position",
                "spatial_relation",
                "boundary",
            )
        )


spatial_residual_repair = SpatialResidualRepair()


__all__ = ["SpatialResidualRepair", "spatial_residual_repair"]
