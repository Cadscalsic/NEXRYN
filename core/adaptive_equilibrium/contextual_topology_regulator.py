def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class ContextualTopologyRegulator:

    def regulate(self, context):

        topology = context.get("ontological_boundary_report", {}).get(
            "topology_integrity_guard",
            {},
        )
        spine_topology = context.get("semantic_spine_report", {}).get(
            "semantic_elastic_topology",
            {},
        )

        elasticity = _clamp(spine_topology.get("elasticity", 0.5))
        stable = topology.get("topology_stable", elasticity >= 0.42)

        flexibility = _clamp(elasticity * 0.62 + (0.24 if stable else 0.0))

        return {
            "system": "contextual_topology_regulator",
            "topology_elasticity": elasticity,
            "topology_stable": stable,
            "contextual_topology_flexibility": flexibility,
            "topology_actions": [
                "allow_limited_contextual_topology_adaptation",
            ]
            if flexibility >= 0.46
            else [
                "hold_topology_shape_until_stabilized",
            ],
            "topology_regulation_state": (
                "contextual_topology_adaptation_allowed"
                if flexibility >= 0.46
                else "contextual_topology_regulation_strict"
            ),
        }
