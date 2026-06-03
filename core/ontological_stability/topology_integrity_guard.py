class TopologyIntegrityGuard:

    def run_cycle(self, context):

        spine_topology = context.get(
            "semantic_spine_report",
            {},
        ).get(
            "semantic_elastic_topology",
            {},
        )

        stable = (
            spine_topology.get(
                "adaptation_without_collapse",
                False,
            )
            or spine_topology.get(
                "elasticity",
                0.0,
            )
            >= 0.42
        )

        return {
            "system":
            "topology_integrity_guard",

            "topology_structure_negotiability":
            "limited",

            "topology_stable":
            stable,

            "topology_controls":
            []
            if stable
            else [
                "block_topology_rewrite",
                "require_spatial_invariant_validation",
            ],

            "topology_state":
            (
                "topology_integrity_preserved"
                if stable
                else "topology_integrity_guard_active"
            ),
        }
