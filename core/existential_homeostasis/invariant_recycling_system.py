class InvariantRecyclingSystem:

    def recycle(self, context):

        rehabilitated = (
            context.get("ontological_boundary_report", {})
            .get("invariant_survival", {})
            .get("rehabilitated_invariants", [])
        )

        recycled = [
            {
                "invariant_id": item.get("invariant_id"),
                "recycling_mode": "dormant_to_stabilizing_pool",
            }
            for item in rehabilitated
        ]

        return {
            "system": "invariant_recycling_system",
            "recycled_invariants": recycled,
            "recycling_state": (
                "critical_invariants_recycled"
                if recycled
                else "no_invariants_require_recycling"
            ),
        }
