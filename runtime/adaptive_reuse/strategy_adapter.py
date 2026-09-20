"""Lightweight adaptation rules for retrieved strategies."""

from __future__ import annotations

from typing import Any, Mapping


ADAPTATION_RULES = {
    "rotate180": ("rotate90", "rotation_angle_adjusted"),
    "rotate_180": ("rotate_90", "rotation_angle_adjusted"),
    "bridgecreation": ("objectconnection", "bridge_generalized_to_connection"),
    "bridge_creation": ("object_connection", "bridge_generalized_to_connection"),
    "mirrorhorizontal": ("mirrorvertical", "mirror_axis_adjusted"),
    "mirror_horizontal": ("mirror_vertical", "mirror_axis_adjusted"),
    "colorreplacement": ("partialcolorreplacement", "color_scope_narrowed"),
    "color_replacement": ("partial_color_replacement", "color_scope_narrowed"),
}


class StrategyAdapter:
    def adapt(
        self,
        strategy: Mapping[str, Any],
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        adapted = dict(strategy)
        operations = []
        query_text = _text(runtime_context or {})
        strategy_type = str(
            adapted.get("type")
            or adapted.get("strategy_type")
            or adapted.get("name")
            or adapted.get("operation")
            or ""
        )
        normalized_type = _normalize(strategy_type)
        for source, (target, operation) in ADAPTATION_RULES.items():
            if source not in normalized_type:
                continue
            if target.replace("_", "") in _normalize(query_text) or not query_text:
                adapted["adapted_from"] = strategy_type
                adapted["adapted_strategy_type"] = target
                adapted["type"] = target
                operations.append(operation)
                break
        if not operations and strategy_type:
            operations.append("parameter_preserving_strategy_reuse")
        adapted["adaptation_operations"] = operations
        adapted["adaptation_state"] = (
            "ADAPTED_STRATEGY" if operations else "UNCHANGED_REUSE"
        )
        return adapted


def _normalize(value: Any) -> str:
    return str(value).lower().replace("-", "_").replace(" ", "_")


def _text(value: Any) -> str:
    if isinstance(value, Mapping):
        return " ".join(str(item) for item in value.values())
    return str(value)
