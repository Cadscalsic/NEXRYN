def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class IdentityStrainRegulator:

    def regulate(self, context, stress):

        identity_cost = _clamp(
            context.get("existential_economics_report", {})
            .get("identity_cost", {})
            .get("identity_maintenance_cost", 0.0)
        )
        continuity = _clamp(
            context.get("identity_continuity_guardian_report", {}).get(
                "identity_continuity",
                context.get("identity_continuity", 0.5),
            )
        )

        strain = _clamp(
            identity_cost * 0.48
            +
            (1.0 - continuity) * 0.34
            +
            stress.get("ontological_stress", 0.0) * 0.18
        )

        return {
            "system": "identity_strain_regulator",
            "identity_cost": identity_cost,
            "identity_continuity": continuity,
            "identity_strain": strain,
            "strain_actions": [
                "reinforce_identity_boundaries",
                "suspend_identity_fusion_pressure",
            ]
            if strain >= 0.36
            else [],
            "strain_state": (
                "identity_strain_regulation_active"
                if strain >= 0.36
                else "identity_strain_contained"
            ),
        }
