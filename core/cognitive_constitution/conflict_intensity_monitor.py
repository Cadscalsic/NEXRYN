def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class ConflictIntensityMonitor:

    def assess(self, context):

        paradigm_conflict = (
            context.get("hybrid_governance_report", {})
            .get("paradigm_conflict", {})
            .get("paradigm_conflict_score", 0.0)
        )

        identity_strain = (
            context.get("existential_pressure_report", {})
            .get("identity_strain_regulator", {})
            .get("identity_strain", 0.0)
        )

        ambiguity_load = (
            context.get("judicial_cognition_report", {})
            .get("ambiguity_reasoning", {})
            .get("ambiguity_load", context.get("ambiguity_score", 0.0))
        )

        tension = (
            context.get("existential_pressure_report", {})
            .get("ontological_tension_homeostasis", {})
            .get("ontological_tension", 0.0)
        )

        conflict_intensity = _clamp(
            paradigm_conflict * 0.30
            +
            identity_strain * 0.30
            +
            ambiguity_load * 0.22
            +
            tension * 0.18
        )

        actions = []
        if conflict_intensity > 0.58:
            actions.extend([
                "reduce_conflict_intensity",
                "require_layered_conflict_resolution",
            ])
        if conflict_intensity > 0.72:
            actions.append("freeze_high_conflict_constitutional_cases")

        return {
            "system": "conflict_intensity_monitor",
            "conflict_intensity": conflict_intensity,
            "conflict_actions": actions,
            "conflict_state": (
                "constitutional_conflict_active"
                if actions
                else "constitutional_conflict_tolerable"
            ),
        }
