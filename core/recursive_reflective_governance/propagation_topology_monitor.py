def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class PropagationTopologyMonitor:

    def monitor(self, context):

        propagation = _clamp(
            context.get("adaptive_equilibrium_report", {})
            .get("propagation_stability_manager", {})
            .get(
                "failure_propagation_score",
                context.get("failure_propagation_score", 0.0),
            )
        )

        topology_flex = _clamp(
            context.get("adaptive_equilibrium_report", {})
            .get("contextual_topology_regulator", {})
            .get("contextual_topology_flexibility", 0.5)
        )

        topology_risk = _clamp(
            propagation * 0.58
            +
            (1.0 - topology_flex) * 0.42
        )

        return {
            "system": "propagation_topology_monitor",
            "failure_propagation_score": propagation,
            "topology_flexibility": topology_flex,
            "topology_risk": topology_risk,
            "monitor_actions": [
                "localize_recursive_propagation",
                "hold_topology_growth",
            ]
            if topology_risk >= 0.40
            else [],
            "monitor_state": (
                "propagation_topology_monitor_active"
                if topology_risk >= 0.40
                else "propagation_topology_clear"
            ),
        }
