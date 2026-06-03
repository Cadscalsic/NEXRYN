def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class ResilientIdentityCore:

    def reinforce(self, context):

        identity_homeostasis = context.get(
            "existential_homeostasis_report",
            {},
        ).get("identity_homeostasis", {})

        strain = context.get("existential_pressure_report", {}).get(
            "identity_strain_regulator",
            {},
        )

        identity_balance = _clamp(identity_homeostasis.get("identity_balance", 0.5))
        identity_strain = _clamp(strain.get("identity_strain", 0.0))

        resilience = _clamp(identity_balance * 0.66 + (1.0 - identity_strain) * 0.34)

        return {
            "system": "resilient_identity_core",
            "identity_balance": identity_balance,
            "identity_strain": identity_strain,
            "identity_resilience": resilience,
            "identity_core_actions": [
                "reinforce_resilient_identity_core",
                "keep_identity_fusion_probationary",
            ]
            if resilience < 0.58
            else [],
            "identity_core_state": (
                "resilient_identity_core_reinforcing"
                if resilience < 0.58
                else "resilient_identity_core_stable"
            ),
        }
