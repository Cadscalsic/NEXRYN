def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class IdentityHomeostasis:

    def balance(self, context):

        continuity = _clamp(
            context.get("identity_continuity", context.get(
                "identity_continuity_guardian_report",
                {},
            ).get("identity_continuity", 0.5))
        )

        identity_cost = _clamp(
            context.get("existential_economics_report", {})
            .get("identity_cost", {})
            .get("identity_maintenance_cost", 0.0)
        )

        identity_balance = _clamp(continuity * 0.64 + (1.0 - identity_cost) * 0.36)

        return {
            "system": "identity_homeostasis",
            "identity_continuity": continuity,
            "identity_maintenance_cost": identity_cost,
            "identity_balance": identity_balance,
            "identity_actions": [
                "reinforce_identity_anchors",
                "limit_identity_fusion",
            ]
            if identity_balance < 0.55
            else [],
            "identity_homeostasis_state": (
                "identity_homeostasis_repairing"
                if identity_balance < 0.55
                else "identity_homeostasis_stable"
            ),
        }
