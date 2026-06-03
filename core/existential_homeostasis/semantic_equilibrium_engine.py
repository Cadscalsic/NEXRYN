def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class SemanticEquilibriumEngine:

    def compute(self, context):

        spine = context.get("semantic_spine_report", {})
        stability = context.get("stability_field_report", {})

        spine_integrity = _clamp(spine.get("spine_integrity", 0.0))
        drift = _clamp(
            stability.get("semantic_drift", {}).get(
                "semantic_drift",
                context.get("semantic_drift", 0.0),
            )
        )

        equilibrium = _clamp(spine_integrity * 0.58 + (1.0 - drift) * 0.42)

        return {
            "system": "semantic_equilibrium_engine",
            "spine_integrity": spine_integrity,
            "semantic_drift": drift,
            "semantic_equilibrium": equilibrium,
            "equilibrium_actions": [
                "increase_semantic_gravity",
                "reanchor_semantic_spine",
            ]
            if equilibrium < 0.52
            else [],
            "equilibrium_state": (
                "semantic_equilibrium_repairing"
                if equilibrium < 0.52
                else "semantic_equilibrium_stable"
            ),
        }
