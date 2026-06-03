def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class RecursiveTopologyJudge:

    def judge(self, context):

        reflective = context.get("recursive_reflective_report", {})
        topology = reflective.get("propagation_topology_monitor", {})
        prediction = reflective.get("topology_prediction", {})

        topology_risk = _clamp(topology.get("topology_risk", 0.0))
        growth_risk = _clamp(prediction.get("predicted_growth_risk", 0.0))

        judgement_risk = _clamp(topology_risk * 0.52 + growth_risk * 0.48)

        return {
            "system": "recursive_topology_judge",
            "recursive_topology_risk": judgement_risk,
            "topology_judgement_actions": [
                "require_topology_rehearsal",
                "block_unbounded_recursive_topology_growth",
            ]
            if judgement_risk >= 0.34
            else [],
            "topology_judgement_state": (
                "recursive_topology_judgement_active"
                if judgement_risk >= 0.34
                else "recursive_topology_judgement_clear"
            ),
        }
