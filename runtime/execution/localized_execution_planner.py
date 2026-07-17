from __future__ import annotations

from typing import Any


class LocalizedExecutionPlanner:
    """Plan where and in what order executable operations should apply."""

    def plan(
        self,
        operation: str | None,
        grounding_report: dict[str, Any] | None,
        *,
        semantic_intent: str | None = None,
    ) -> dict[str, Any]:
        grounding = grounding_report if isinstance(grounding_report, dict) else {}
        operation_name = self._normalize_operation(operation or semantic_intent)
        target_objects = grounding.get("target_objects")
        target_objects = target_objects if isinstance(target_objects, list) else []
        affected_regions = grounding.get("affected_regions")
        affected_regions = affected_regions if isinstance(affected_regions, list) else []
        scope = grounding.get("transformation_scope") or self._scope_for(operation_name)
        localized_operations = []
        for index, target in enumerate(target_objects or [{}], start=1):
            region = affected_regions[index - 1] if index - 1 < len(affected_regions) else {}
            localized_operations.append({
                "operation": operation_name,
                "target_object": target.get("object_id") if isinstance(target, dict) else None,
                "target_region": region,
                "execution_scope": scope,
                "execution_order": index,
            })
        return {
            "operation": operation_name,
            "localized_operations": localized_operations,
            "target_objects": [
                target.get("object_id")
                for target in target_objects
                if isinstance(target, dict) and target.get("object_id")
            ],
            "affected_regions": affected_regions,
            "execution_scope": scope,
            "transformation_ordering": [
                item["operation"] for item in sorted(localized_operations, key=lambda row: row["execution_order"])
            ],
            "local_execution_supported": scope in {"local", "mixed"},
            "global_execution_supported": scope in {"global", "mixed"},
            "planning_confidence": 0.9 if localized_operations else 0.0,
            "localized_execution_planning_operational": True,
        }

    def _normalize_operation(self, operation: str | None) -> str:
        value = str(operation or "preserve").strip().lower()
        aliases = {
            "duplicate": "duplicate_object",
            "recolor": "replace_color",
            "preserve_color": "replace_color",
            "translate": "translate_object",
            "grow": "growth",
        }
        return aliases.get(value, value)

    def _scope_for(self, operation: str) -> str:
        if operation.startswith("global_") or operation in {"preserve_grid", "remap_palette"}:
            return "global"
        return "local"


localized_execution_planner = LocalizedExecutionPlanner()


__all__ = ["LocalizedExecutionPlanner", "localized_execution_planner"]
