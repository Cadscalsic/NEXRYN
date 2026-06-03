def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class TopologyPredictionEngine:

    def predict(self, context, topology):

        topology_delta = _clamp(
            abs(
                context.get("topology_result", {})
                .get("topology_delta", 0.0)
            )
        )
        topology_risk = _clamp(topology.get("topology_risk", 0.0))

        predicted_growth_risk = _clamp(
            topology_delta * 0.44
            +
            topology_risk * 0.56
        )

        return {
            "system": "topology_prediction_engine",
            "topology_delta": topology_delta,
            "predicted_growth_risk": predicted_growth_risk,
            "prediction_actions": [
                "simulate_topology_growth_before_commit",
                "prefer_topology_preserving_routes",
            ]
            if predicted_growth_risk >= 0.34
            else [],
            "prediction_state": (
                "topology_growth_risk_predicted"
                if predicted_growth_risk >= 0.34
                else "topology_growth_risk_low"
            ),
        }
