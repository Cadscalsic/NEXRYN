from __future__ import annotations

from typing import Any


class PrimitiveSelector:
    """Select primitive families capable of implementing an executable intent."""

    OPERATION_PRIMITIVES = {
        "duplicate_object": ["duplicate", "preserve"],
        "mirror_duplicate_object": ["mirror", "duplicate", "preserve"],
        "replace_color": ["recolor", "preserve"],
        "global_recolor": ["recolor"],
        "remap_symbols": ["remap", "preserve"],
        "symbolic_remapping": ["remap", "preserve"],
        "translate_object": ["translate", "preserve"],
        "directional_motion": ["translate", "preserve"],
        "rotate_object": ["rotate", "preserve"],
        "mirror_object": ["mirror", "preserve"],
        "resize_object": ["resize", "preserve"],
        "merge_objects": ["merge", "compose"],
        "split_object": ["split", "compose"],
        "growth": ["grow", "propagate", "preserve"],
        "topological_growth": ["grow", "propagate", "preserve"],
        "construct_path": ["propagate", "compose"],
        "preserve_topology": ["preserve"],
        "preserve_grid": ["preserve"],
    }

    def select(
        self,
        operation: str | None,
        execution_plan: dict[str, Any] | None = None,
        *,
        semantic_intent: str | None = None,
    ) -> dict[str, Any]:
        operation_name = str(operation or semantic_intent or "preserve").lower()
        primitives = list(self.OPERATION_PRIMITIVES.get(operation_name, []))
        if not primitives:
            if "color" in operation_name:
                primitives = ["recolor", "preserve"]
            elif "duplicate" in operation_name or "replic" in operation_name:
                primitives = ["duplicate", "preserve"]
            elif "grow" in operation_name:
                primitives = ["grow", "propagate", "preserve"]
            else:
                primitives = ["compose"]
        plan = execution_plan if isinstance(execution_plan, dict) else {}
        scope = plan.get("execution_scope", "local")
        return {
            "operation": operation_name,
            "selected_primitives": primitives,
            "primitive_family": self._family_for(primitives),
            "execution_scope": scope,
            "selection_confidence": 0.95 if operation_name in self.OPERATION_PRIMITIVES else 0.72,
            "missing_primitives": [],
            "primitive_selection_operational": True,
        }

    def _family_for(self, primitives: list[str]) -> str:
        if not primitives:
            return "unsupported_primitives"
        primary = primitives[0]
        families = {
            "duplicate": "duplication_primitives",
            "recolor": "color_primitives",
            "remap": "symbol_primitives",
            "translate": "motion_primitives",
            "rotate": "geometry_primitives",
            "mirror": "geometry_primitives",
            "resize": "geometry_primitives",
            "merge": "composition_primitives",
            "split": "composition_primitives",
            "grow": "growth_primitives",
            "propagate": "propagation_primitives",
            "preserve": "preservation_primitives",
            "compose": "composition_primitives",
        }
        return families.get(primary, "composition_primitives")


primitive_selector = PrimitiveSelector()


__all__ = ["PrimitiveSelector", "primitive_selector"]
