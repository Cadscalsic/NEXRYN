from __future__ import annotations

from typing import Any, Mapping


class RepairRouteSelector:
    """Select a repair family from validated residual evidence."""

    ROUTES = {
        "localized_color_residual": "localized_color_repair",
        "localized_spatial_residual": "spatial_repair",
        "object_mismatch": "object_grounding_repair",
        "topology_residual": "topology_repair",
        "program_step_residual": "program_revision_repair",
    }

    def select(
        self,
        residual_evidence: Mapping[str, Any] | None,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        evidence = residual_evidence if isinstance(residual_evidence, Mapping) else {}
        runtime_context = context if isinstance(context, Mapping) else {}
        residual_type = str(evidence.get("residual_type") or "")
        route = self.ROUTES.get(residual_type)
        evidence_notes = [residual_type] if residual_type else []

        if runtime_context.get("truth_supported_correction") is True:
            route = "truth_guided_repair"
            evidence_notes.append("truth_supported_correction")
        elif runtime_context.get("dependency_supported_correction") is True:
            route = "dependency_guided_repair"
            evidence_notes.append("dependency_supported_correction")
        elif runtime_context.get("counterfactual_supported_alternative") is True:
            route = "counterfactual_repair"
            evidence_notes.append("counterfactual_supported_alternative")

        fallback = "program_revision_repair"
        return {
            "repair_route": route or fallback,
            "repair_route_confidence": 0.92 if route else 0.35,
            "repair_route_evidence": evidence_notes,
            "fallback_route": fallback,
            "route_selected": bool(route),
        }


repair_route_selector = RepairRouteSelector()


__all__ = ["RepairRouteSelector", "repair_route_selector"]
