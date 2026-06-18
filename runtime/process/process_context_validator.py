"""Validation for process contexts under governance constraints."""

from __future__ import annotations

from typing import Any, Mapping

from core.epistemic_models import clamp


class ProcessContextValidator:
    """Validate process contexts without weakening identity or contradiction rules."""

    system_name = "process_context_validator"

    def validate(
        self,
        context: Mapping[str, Any],
        identity_continuity: float,
        causal_alignment: float,
        contradiction_score: float = 0.0,
    ) -> dict[str, Any]:
        blockers = []
        if identity_continuity < 0.85:
            blockers.append("identity_continuity_below_process_floor")
        if causal_alignment < 0.85:
            blockers.append("causal_alignment_below_process_floor")
        if contradiction_score > 0.10:
            blockers.append("contradiction_threshold_exceeded")
        if not (
            context.get("transition_signature")
            or context.get("transitions")
        ):
            blockers.append("process_transition_missing")

        return {
            "system": self.system_name,
            "process_context_valid": not blockers,
            "process_context_ready": not blockers,
            "semantic_validation": not blockers,
            "identity_compatible": identity_continuity >= 0.85,
            "governance_visible": not blockers,
            "identity_continuity": clamp(identity_continuity),
            "causal_alignment": clamp(causal_alignment),
            "contradiction_score": clamp(contradiction_score),
            "validation_blockers": blockers,
        }


__all__ = ["ProcessContextValidator"]
