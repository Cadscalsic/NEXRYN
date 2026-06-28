"""Object-first grounding and localization recovery for ARC transformations."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.grounding.grounding_memory import grounding_memory


class ObjectGroundingEngine:
    system_name = "object_grounding_engine"

    def ground(
        self,
        hypothesis: Mapping[str, Any] | None = None,
        localization: Mapping[str, Any] | None = None,
        synthesized_program: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        hypothesis = hypothesis if isinstance(hypothesis, Mapping) else {}
        localization = localization if isinstance(localization, Mapping) else {}
        synthesized_program = (
            synthesized_program if isinstance(synthesized_program, Mapping) else {}
        )
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        operation = self._operation(synthesized_program, hypothesis)
        residual_locations = self._residual_locations(runtime_context, localization)
        candidate_regions = self._candidate_regions(residual_locations)
        existing_targets = list(localization.get("target_objects", []) or [])
        target_objects = existing_targets or self._targets_from_regions(
            candidate_regions,
            role="residual_target",
        )
        affected_objects = self._affected_objects(target_objects, residual_locations)
        anchor_objects = self._anchor_objects(localization, target_objects)
        supporting_objects = self._supporting_objects(localization, anchor_objects)
        transformation_targets = self._transformation_targets(
            operation,
            target_objects,
            synthesized_program,
        )
        hints = self._localization_hints(
            residual_locations,
            candidate_regions,
            operation,
        )
        reused_hints = grounding_memory.reuse_hints(operation)
        if reused_hints:
            hints.extend(reused_hints)
        confidence = self._confidence(
            target_objects,
            transformation_targets,
            residual_locations,
            hypothesis,
        )
        report = {
            "system": self.system_name,
            "OBJECT GROUNDING REPORT": True,
            "operation": operation,
            "target_objects": target_objects,
            "affected_objects": affected_objects,
            "supporting_objects": supporting_objects,
            "anchor_objects": anchor_objects,
            "transformation_targets": transformation_targets,
            "candidate_object_regions": candidate_regions,
            "candidate_transform_regions": candidate_regions,
            "localization_hints": hints,
            "residual_locations": residual_locations,
            "object_detection": round(0.85 if target_objects else 0.0, 4),
            "transformation_detection": round(
                0.80 if transformation_targets else 0.0,
                4,
            ),
            "causal_support": round(
                max(self._number(hypothesis.get("causal_support")), 0.65 if hints else 0.0),
                4,
            ),
            "localization_confidence": round(confidence, 4),
            "transformation_scope": "object_level" if target_objects else "unlocalized",
            "localization_recovery_mode": bool(not existing_targets and target_objects),
            "recovery_methods": [
                "object_backtracking",
                "transformation_backtracking",
                "region_discovery",
                "residual_guided_localization",
                "difference_driven_localization",
            ],
            "LOCALIZATION EXPLAINER REPORT": self._explainer(
                target_objects,
                candidate_regions,
                hints,
                confidence,
            ),
        }
        grounding_memory.record(report, success=bool(target_objects))
        return report

    def recover_localization(
        self,
        localization: Mapping[str, Any] | None,
        grounding_report: Mapping[str, Any],
        synthesized_program: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = dict(localization or {})
        if grounding_report.get("target_objects"):
            result["target_objects"] = list(grounding_report["target_objects"])
        result["affected_objects"] = list(grounding_report.get("affected_objects", []))
        result["anchor_objects"] = list(grounding_report.get("anchor_objects", []))
        result["transformation_targets"] = list(
            grounding_report.get("transformation_targets", [])
        )
        result["candidate_object_regions"] = list(
            grounding_report.get("candidate_object_regions", [])
        )
        result["candidate_transform_regions"] = list(
            grounding_report.get("candidate_transform_regions", [])
        )
        result["localization_hints"] = list(
            grounding_report.get("localization_hints", [])
        )
        result["object_grounding_report"] = dict(grounding_report)
        result["OBJECT GROUNDING REPORT"] = dict(grounding_report)
        if grounding_report.get("localization_recovery_mode"):
            result["localization_recovery_mode"] = True
            result["fallback_used"] = result.get("fallback_used") or "object_grounding_recovery"
        result["localization_confidence"] = max(
            self._number(result.get("localization_confidence")),
            self._number(grounding_report.get("localization_confidence")),
        )
        if synthesized_program and "localized_program" not in result:
            result["localized_program"] = dict(synthesized_program)
        if grounding_report.get("target_objects"):
            result["localized_step_count"] = max(
                int(result.get("localized_step_count", 0) or 0),
                len((synthesized_program or {}).get("steps", []) or []),
                1,
            )
            result["localization_ready"] = (
                result.get("localization_confidence", 0.0) >= 0.60
            )
        return result

    def _residual_locations(
        self,
        runtime_context: Mapping[str, Any],
        localization: Mapping[str, Any],
    ) -> list[dict[str, int]]:
        raw = (
            runtime_context.get("residual_locations")
            or localization.get("residual_locations")
            or self._diff_locations(
                runtime_context.get("predicted_output"),
                runtime_context.get("output_grid"),
            )
        )
        locations = []
        for item in raw or []:
            if isinstance(item, Mapping):
                row = item.get("row", item.get("r"))
                col = item.get("col", item.get("c"))
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                row, col = item[0], item[1]
            else:
                continue
            try:
                locations.append({"row": int(row), "col": int(col)})
            except (TypeError, ValueError):
                continue
        return locations

    def _diff_locations(self, predicted: Any, target: Any) -> list[dict[str, int]]:
        if predicted is None or target is None:
            return []
        try:
            pred_rows = predicted.tolist() if hasattr(predicted, "tolist") else predicted
            tgt_rows = target.tolist() if hasattr(target, "tolist") else target
            locations = []
            for row_index, (pred_row, tgt_row) in enumerate(zip(pred_rows, tgt_rows)):
                for col_index, (pred_value, tgt_value) in enumerate(zip(pred_row, tgt_row)):
                    if pred_value != tgt_value:
                        locations.append({"row": row_index, "col": col_index})
            return locations
        except Exception:
            return []

    def _candidate_regions(self, locations: list[dict[str, int]]) -> list[dict[str, Any]]:
        if not locations:
            return []
        rows = [item["row"] for item in locations]
        cols = [item["col"] for item in locations]
        return [{
            "region_id": "residual_region_0",
            "min_row": min(rows),
            "max_row": max(rows),
            "min_col": min(cols),
            "max_col": max(cols),
            "cells": locations,
            "cell_count": len(locations),
            "source": "residual_difference",
        }]

    def _targets_from_regions(
        self,
        regions: list[dict[str, Any]],
        role: str,
    ) -> list[dict[str, Any]]:
        return [
            {
                "object_id": region["region_id"],
                "role": role,
                "region": region,
                "identity_preserved": True,
                "identity_confidence": 0.65,
            }
            for region in regions
        ]

    def _affected_objects(
        self,
        targets: list[dict[str, Any]],
        residual_locations: list[dict[str, int]],
    ) -> list[dict[str, Any]]:
        return [
            {
                **target,
                "residual_cell_count": len(residual_locations),
            }
            for target in targets
        ]

    def _anchor_objects(
        self,
        localization: Mapping[str, Any],
        targets: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        anchors = []
        for report in localization.get("localization_reports", []) or []:
            if isinstance(report, Mapping) and report.get("anchor_object"):
                anchors.append({
                    "object_id": report["anchor_object"],
                    "role": "anchor_object",
                    "relative_offset": report.get("relative_offset", [0, 0]),
                })
        return anchors or targets[:1]

    def _supporting_objects(
        self,
        localization: Mapping[str, Any],
        anchors: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        supporting = list(anchors)
        for report in localization.get("localization_reports", []) or []:
            for match in (report.get("object_matches", []) if isinstance(report, Mapping) else []):
                if isinstance(match, Mapping):
                    supporting.append(dict(match))
        return supporting

    def _transformation_targets(
        self,
        operation: str,
        targets: list[dict[str, Any]],
        synthesized_program: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        steps = synthesized_program.get("steps", []) or []
        if not targets and not steps:
            return []
        return [
            {
                "object_id": target.get("object_id"),
                "operation": operation,
                "step_count": len(steps) or 1,
                "grounded_by": target.get("role", "object_grounding"),
            }
            for target in (targets or [{"object_id": "global_candidate"}])
        ]

    def _localization_hints(
        self,
        locations: list[dict[str, int]],
        regions: list[dict[str, Any]],
        operation: str,
    ) -> list[dict[str, Any]]:
        hints = []
        if locations:
            hints.append({
                "hint_type": "residual_locations",
                "operation": operation,
                "locations": locations,
            })
        for region in regions:
            hints.append({
                "hint_type": "candidate_region",
                "operation": operation,
                "region": region,
            })
        return hints

    def _confidence(
        self,
        targets: list[dict[str, Any]],
        transformations: list[dict[str, Any]],
        residuals: list[dict[str, int]],
        hypothesis: Mapping[str, Any],
    ) -> float:
        return min(
            1.0,
            max(
                self._number(hypothesis.get("confidence")) * 0.74,
                (0.35 if targets else 0.0)
                + (0.20 if transformations else 0.0)
                + (0.20 if residuals else 0.0)
                + (0.15 if hypothesis else 0.0),
            ),
        )

    def _explainer(
        self,
        targets: list[dict[str, Any]],
        regions: list[dict[str, Any]],
        hints: list[dict[str, Any]],
        confidence: float,
    ) -> dict[str, Any]:
        missing = []
        if not targets:
            missing.append("target_objects")
        if not regions:
            missing.append("candidate_regions")
        contributors = []
        if targets:
            contributors.append("target_objects_identified")
        if regions:
            contributors.append("residual_regions_discovered")
        if hints:
            contributors.append("localization_hints_generated")
        suppressors = []
        if confidence < 0.70:
            suppressors.append("confidence_below_execution_threshold")
        return {
            "why_localization_succeeded": contributors,
            "why_localization_failed": missing,
            "missing_evidence": missing,
            "candidate_objects": targets,
            "candidate_regions": regions,
            "confidence_contributors": contributors,
            "confidence_suppressors": suppressors,
        }

    def _operation(
        self,
        synthesized_program: Mapping[str, Any],
        hypothesis: Mapping[str, Any],
    ) -> str:
        primitive = hypothesis.get("primitive") or hypothesis.get("type")
        if primitive:
            return str(primitive).lower()
        for step in synthesized_program.get("steps", []) or []:
            if isinstance(step, Mapping):
                operation = step.get("operation") or step.get("primitive")
                if operation:
                    return str(operation).lower()
        return "unknown"

    def _number(self, value: Any, default: float = 0.0) -> float:
        try:
            return max(0.0, min(float(value), 1.0))
        except (TypeError, ValueError):
            return default


object_grounding_engine = ObjectGroundingEngine()


__all__ = ["ObjectGroundingEngine", "object_grounding_engine"]
