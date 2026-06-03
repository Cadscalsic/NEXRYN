def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(minimum, min(value, maximum)),
        4,
    )


class TopologyMaintenanceCosts:

    def compute(self, context):

        topology = context.get(
            "ontological_boundary_report",
            {},
        ).get(
            "topology_integrity_guard",
            {},
        )

        spine_topology = context.get(
            "semantic_spine_report",
            {},
        ).get(
            "semantic_elastic_topology",
            {},
        )

        elasticity = _clamp(
            spine_topology.get(
                "elasticity",
                1.0,
            )
        )

        active_guard = (
            topology.get(
                "topology_state",
            )
            == "topology_integrity_guard_active"
        )

        cost = _clamp(
            (1.0 - elasticity) * 0.46
            +
            (
                0.20
                if active_guard
                else 0.0
            )
        )

        return {
            "system":
            "topology_maintenance_costs",

            "topology_elasticity":
            elasticity,

            "topology_guard_active":
            active_guard,

            "topology_maintenance_cost":
            cost,

            "cost_state":
            (
                "topology_cost_high"
                if cost >= 0.58
                else "topology_cost_elevated"
                if cost >= 0.32
                else "topology_cost_contained"
            ),
        }
