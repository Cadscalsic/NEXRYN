def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class CausalPermissionController:

    def control(self, context, legality):

        causal_integrity = _clamp(
            context.get("causal_integrity", context.get("semantic_physics_report", {}).get("causal_integrity", 0.5))
        )
        permission = _clamp(causal_integrity * 0.54 + legality.get("semantic_legality", 0.5) * 0.46)

        return {
            "system": "causal_permission_controller",
            "causal_permission_score": permission,
            "causal_actions": [
                "require_causal_permission_review",
                "block_causally_unlicensed_execution",
            ]
            if permission < 0.56
            else [],
            "causal_permission_state": (
                "causal_permission_guarded"
                if permission < 0.56
                else "causal_permission_granted"
            ),
        }
