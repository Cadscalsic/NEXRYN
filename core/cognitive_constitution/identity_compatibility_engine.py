def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class IdentityCompatibilityEngine:

    def assess(self, context):

        identity_report = context.get("identity_reasoner_report", {})
        analyses = identity_report.get("identity_analyses", [])
        if not isinstance(analyses, list):
            analyses = []

        conflict_count = 0
        for analysis in analyses:
            if not isinstance(analysis, dict):
                continue
            if (
                analysis.get("identity_status")
                == "identity_conflict_above_limit"
            ):
                conflict_count += 1

        boundary = context.get("ontological_boundary_report", {})
        blocked_fusions = (
            boundary.get("identity_boundary", {})
            .get("blocked_identity_fusions", 0)
        )

        resilient_identity = (
            context.get("adaptive_equilibrium_report", {})
            .get("resilient_identity_core", {})
            .get("identity_resilience", 0.64)
        )

        judicial_identity = (
            context.get("judicial_cognition_report", {})
            .get("judicial_identity_supervisor", {})
            .get("judicial_identity_score", 0.58)
        )

        conflict_pressure = _clamp(
            conflict_count * 0.14
            +
            blocked_fusions * 0.08
        )

        compatibility = _clamp(
            resilient_identity * 0.44
            +
            judicial_identity * 0.32
            +
            (1.0 - conflict_pressure) * 0.24
        )

        actions = []
        if compatibility < 0.58:
            actions.extend([
                "require_identity_compatibility_review",
                "hold_identity_sensitive_merge",
            ])
        if blocked_fusions:
            actions.append("preserve_identity_boundary_blocks")

        return {
            "system": "identity_compatibility_engine",
            "identity_compatibility": compatibility,
            "identity_conflict_count": conflict_count,
            "blocked_identity_fusions": blocked_fusions,
            "compatibility_actions": actions,
            "compatibility_state": (
                "identity_constitution_review_required"
                if actions
                else "identity_compatible"
            ),
        }
