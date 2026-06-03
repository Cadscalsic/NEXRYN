def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class ContinuityEquilibrium:

    def compute(self, identity, semantic, economics):

        continuity_budget = _clamp(
            economics.get("continuity_resource_allocation", {}).get(
                "continuity_allocation",
                0.0,
            )
        )

        equilibrium = _clamp(
            identity.get("identity_balance", 0.0) * 0.42
            +
            semantic.get("semantic_equilibrium", 0.0) * 0.36
            +
            continuity_budget * 0.22
        )

        return {
            "system": "continuity_equilibrium",
            "continuity_budget": continuity_budget,
            "continuity_equilibrium": equilibrium,
            "equilibrium_state": (
                "continuity_equilibrium_repairing"
                if equilibrium < 0.52
                else "continuity_equilibrium_stable"
            ),
        }
