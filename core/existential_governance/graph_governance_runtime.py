def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class GraphGovernanceRuntime:

    def govern(self, context):

        propagation = _clamp(
            context.get("adaptive_equilibrium_report", {})
            .get("propagation_stability_manager", {})
            .get("failure_propagation_score", 0.0)
        )
        recursive = _clamp(
            1.0
            -
            context.get("recursive_reflective_report", {}).get(
                "recursive_reflective_score",
                0.5,
            )
        )

        graph_risk = _clamp(propagation * 0.52 + recursive * 0.48)

        return {
            "system": "graph_governance_runtime",
            "graph_risk": graph_risk,
            "graph_actions": [
                "localize_graph_governance_updates",
                "block_unattested_recursive_graph_propagation",
            ]
            if graph_risk >= 0.34
            else [],
            "graph_governance_state": (
                "graph_governance_runtime_active"
                if graph_risk >= 0.34
                else "graph_governance_runtime_clear"
            ),
        }
