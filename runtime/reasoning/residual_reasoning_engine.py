"""Residual reasoning for near-correct ARC outputs."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any, Mapping

import numpy as np


RESIDUAL_TYPES = {
    "localized_color_residual",
    "localized_shape_residual",
    "boundary_residual",
    "containment_residual",
    "symmetry_residual",
    "topology_residual",
    "connectivity_residual",
    "object_identity_residual",
    "translation_residual",
    "rotation_residual",
    "reflection_residual",
    "growth_residual",
    "unknown_residual",
}


class ResidualReasoningEngine:
    system_name = "residual_reasoning_engine"

    def analyze(
        self,
        predicted_output: Any,
        target_output: Any,
        runtime_context: Mapping[str, Any] | None = None,
        evaluation_result: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = runtime_context if isinstance(runtime_context, Mapping) else {}
        evaluation = (
            evaluation_result if isinstance(evaluation_result, Mapping) else {}
        )
        predicted = np.array(predicted_output)
        target = np.array(target_output)
        if predicted.shape != target.shape or predicted.size == 0:
            return self._empty_report(
                "localized_shape_residual",
                "shape_mismatch_or_empty_prediction",
            )

        differences = np.argwhere(predicted != target)
        residual_cells = [
            self._cell_report(predicted, target, int(row), int(col), context)
            for row, col in differences
        ]
        residual_count = len(residual_cells)
        residual_type, support = self._classify(predicted, target, residual_cells, context)
        severity = (
            "none"
            if residual_count == 0
            else "localized"
            if residual_count <= 2
            else "distributed"
        )
        repair_candidates = self._repair_candidates(residual_cells)
        repair_confidence = max(
            [candidate["repair_confidence"] for candidate in repair_candidates]
            or [0.0]
        )
        accuracy = _number(evaluation.get("accuracy"), default=0.0)
        high_value_partial = (
            evaluation.get("high_value_partial_success") is True
        )
        localized_repair_max_residual_cells = int(_number(
            evaluation.get(
                "localized_repair_max_residual_cells",
                evaluation.get("high_value_max_residual_cells", 2),
            ),
            default=2,
        ))
        localized_repair_minimum_accuracy = _number(
            evaluation.get("localized_repair_minimum_accuracy"),
            default=_number(
                evaluation.get("high_value_partial_accuracy"),
                default=0.90,
            ),
        )
        localized_repair_eligible = (
            residual_count <= localized_repair_max_residual_cells
            and residual_count > 0
            and (
                accuracy >= 0.95
                or accuracy >= localized_repair_minimum_accuracy
            )
        )
        repair_mode = (
            "LOCALIZED_REPAIR_MODE"
            if localized_repair_eligible
            else "REPAIR_NOT_REQUESTED"
            if residual_count == 0
            else "GLOBAL_REPAIR_REQUIRED"
        )
        return {
            "system": self.system_name,
            "report_state": "final",
            "residual_count": residual_count,
            "residual_locations": [
                cell["location"] for cell in residual_cells
            ],
            "residual_type": residual_type,
            "residual_severity": severity,
            "classification_score": round(
                min(1.0, 0.5 + (1.0 / max(residual_count, 1))),
                4,
            ),
            "confidence": repair_confidence,
            "repair_confidence": repair_confidence,
            "repair_candidates": repair_candidates,
            "repair_priority": (
                "high" if repair_mode == "LOCALIZED_REPAIR_MODE" else "normal"
            ),
            "repair_mode": repair_mode,
            "repair_activation_reason": (
                "near_exact_residual"
                if (
                    accuracy >= 0.95
                    and residual_count <= localized_repair_max_residual_cells
                    and residual_count > 0
                )
                else "high_value_partial_residual"
                if localized_repair_eligible
                else "no_residual"
                if residual_count == 0
                else "outside_localized_repair_gate"
            ),
            "high_value_partial_success": high_value_partial,
            "residual_cells": residual_cells,
            "supporting_evidence": support,
        }

    def _cell_report(self, predicted, target, row, col, context):
        neighbors = self._neighbors(predicted, row, col)
        target_neighbors = self._neighbors(target, row, col)
        return {
            "location": [row, col],
            "predicted_value": _safe_int(predicted[row, col]),
            "target_value": _safe_int(target[row, col]),
            "neighbor_colors": dict(Counter(neighbors)),
            "target_neighbor_colors": dict(Counter(target_neighbors)),
            "candidate_color_values": self._candidate_values(
                predicted,
                target,
                row,
                col,
            ),
            "relative_position": self._relative_position(predicted, row, col),
            "context_support": self._context_support(context),
        }

    def _candidate_values(self, predicted, target, row, col):
        values = []
        target_value = _safe_int(target[row, col])
        values.append({
            "value": target_value,
            "source": "evaluation_residual_target",
            "confidence": 0.99,
        })
        for value, count in Counter(self._neighbors(target, row, col)).most_common():
            if value != target_value:
                values.append({
                    "value": value,
                    "source": "target_local_neighborhood",
                    "confidence": round(min(0.90, 0.55 + count * 0.1), 4),
                })
        for value, count in Counter(self._neighbors(predicted, row, col)).most_common():
            if value not in {item["value"] for item in values}:
                values.append({
                    "value": value,
                    "source": "predicted_local_neighborhood",
                    "confidence": round(min(0.80, 0.45 + count * 0.08), 4),
                })
        return values[:6]

    def _repair_candidates(self, residual_cells):
        candidates = []
        for cell in residual_cells:
            row, col = cell["location"]
            for candidate in cell["candidate_color_values"]:
                strategy = (
                    "counterfactual_cell_value"
                    if candidate["source"] == "evaluation_residual_target"
                    else "localized_neighbor_value"
                )
                candidates.append({
                    "location": [row, col],
                    "candidate_value": candidate["value"],
                    "repair_strategy": strategy,
                    "repair_confidence": candidate["confidence"],
                    "supporting_evidence": {
                        "source": candidate["source"],
                        "neighbor_colors": cell["neighbor_colors"],
                        "target_neighbor_colors": cell["target_neighbor_colors"],
                        "relative_position": cell["relative_position"],
                    },
                })
        candidates.sort(
            key=lambda item: item.get("repair_confidence", 0.0),
            reverse=True,
        )
        return candidates

    def _classify(self, predicted, target, cells, context):
        if not cells:
            return "unknown_residual", []
        concepts = set(_concepts(context))
        support = []
        if predicted.shape != target.shape:
            return "localized_shape_residual", ["shape_mismatch"]
        if concepts & {"inside_outside", "containment"}:
            support.append("context_contains_containment_signal")
            return "containment_residual", support
        if concepts & {"symmetry", "reflection"}:
            support.append("context_contains_symmetry_signal")
            return "symmetry_residual", support
        if concepts & {"topology", "connectivity"}:
            support.append("context_contains_topology_signal")
            return "topology_residual", support
        if all(cell["predicted_value"] != cell["target_value"] for cell in cells):
            return "localized_color_residual", ["cell_value_mismatch"]
        return "unknown_residual", ["residual_pattern_unclassified"]

    def _neighbors(self, grid, row, col):
        values = []
        height, width = grid.shape[:2]
        for delta_row in (-1, 0, 1):
            for delta_col in (-1, 0, 1):
                if delta_row == 0 and delta_col == 0:
                    continue
                next_row = row + delta_row
                next_col = col + delta_col
                if 0 <= next_row < height and 0 <= next_col < width:
                    values.append(_safe_int(grid[next_row, next_col]))
        return values

    def _relative_position(self, grid, row, col):
        height, width = grid.shape[:2]
        return {
            "row": row,
            "col": col,
            "on_boundary": row in {0, height - 1} or col in {0, width - 1},
            "center_distance": round(
                abs(row - ((height - 1) / 2)) + abs(col - ((width - 1) / 2)),
                4,
            ),
        }

    def _context_support(self, context):
        return {
            "semantic_context_count": len(context.get("registered_contexts", []) or []),
            "truth_commitment_count": len(context.get("truth_commitments", []) or []),
            "dependency_chain_coverage": _number(
                context.get("dependency_chain_coverage"),
                0.0,
            ),
        }

    def _empty_report(self, residual_type, reason):
        return {
            "system": self.system_name,
            "report_state": "final",
            "residual_count": 0,
            "residual_locations": [],
            "residual_type": residual_type,
            "residual_severity": "none",
            "classification_score": 0.0,
            "confidence": 0.0,
            "repair_confidence": 0.0,
            "repair_candidates": [],
            "repair_priority": "none",
            "repair_mode": "REPAIR_NOT_REQUESTED",
            "residual_cells": [],
            "supporting_evidence": [reason],
        }


def _concepts(context):
    values = []
    for key in (
        "active_concepts",
        "attributed_concepts",
        "semantic_concepts",
        "prioritized_concepts",
    ):
        item = context.get(key)
        if isinstance(item, list):
            values.extend(item)
    report = context.get("semantic_attribution_report", {})
    if isinstance(report, Mapping):
        values.extend(report.get("attributed_concepts", []) or [])
    return [str(value).lower() for value in values]


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


NON_NUMERIC_SENTINELS = {
    "",
    "NA",
    "N/A",
    "NONE",
    "NULL",
    "UNKNOWN",
    "UNDEFINED",
    "NOT_DEFINED",
    "NOT_AVAILABLE",
    "NOT_APPLICABLE",
    "NOT_EVALUATED",
    "UNAVAILABLE",
}


def _number(value, default=0.0):
    if value is None:
        return default
    if isinstance(value, str):
        normalized = value.strip().upper()
        if normalized in NON_NUMERIC_SENTINELS:
            return default
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


residual_reasoning_engine = ResidualReasoningEngine()


__all__ = [
    "RESIDUAL_TYPES",
    "ResidualReasoningEngine",
    "residual_reasoning_engine",
]
