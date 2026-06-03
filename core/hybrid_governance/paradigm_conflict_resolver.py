def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class ParadigmConflictResolver:

    def resolve(self, context):

        selection = context.get("meta_selection_report", {})
        dominant = selection.get("dominant_reasoning", context.get("dominant_reasoning", "unknown"))
        alternatives = selection.get("candidate_modes", context.get("reasoning_modes", []))

        if not isinstance(alternatives, list):

            alternatives = []

        identity_blocks = (
            context.get("ontological_boundary_report", {})
            .get("identity_boundary", {})
            .get("blocked_identity_fusions", 0)
        )
        rejected = context.get("concept_fusion_report", {}).get("rejected_count", 0)
        pressure = _clamp(
            context.get("existential_pressure_report", {})
            .get("managed_pressure", 0.0)
        )

        conflict_score = _clamp(
            len(set(alternatives)) * 0.08
            +
            identity_blocks * 0.12
            +
            rejected * 0.08
            +
            pressure * 0.24
        )

        return {
            "system": "paradigm_conflict_resolver",
            "dominant_paradigm": dominant,
            "candidate_paradigms": alternatives,
            "paradigm_conflict_score": conflict_score,
            "resolution_actions": [
                "isolate_conflicting_paradigm_claims",
                "route_hybrid_reasoning_through_attestation",
            ]
            if conflict_score >= 0.34
            else [],
            "conflict_state": (
                "paradigm_conflict_resolution_active"
                if conflict_score >= 0.34
                else "paradigm_conflict_low"
            ),
        }
