def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(minimum, min(value, maximum)),
        4,
    )


class ContinuityResourceAllocator:

    def compute(self, identity_cost, invariant_cost, semantic_budget):

        continuity_need = _clamp(
            identity_cost.get(
                "identity_maintenance_cost",
                0.0,
            )
            * 0.42
            +
            invariant_cost.get(
                "invariant_preservation_cost",
                0.0,
            )
            * 0.34
            +
            semantic_budget.get(
                "spine_repair_cost",
                0.0,
            )
            * 0.24
        )

        exploration_allowance = _clamp(
            0.45
            -
            continuity_need * 0.34,
            0.04,
            0.45,
        )

        return {
            "system":
            "continuity_resource_allocator",

            "continuity_allocation":
            continuity_need,

            "exploration_allowance":
            exploration_allowance,

            "allocator_state":
            (
                "continuity_prioritized"
                if continuity_need >= 0.48
                else "continuity_and_evolution_balanced"
            ),
        }
