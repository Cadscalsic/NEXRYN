def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class ContradictionPredictionEngine:

    def predict(self, context, identity, merge, conflict):

        failure_memory = context.get("cognitive_failure_memory", {})
        latest_failure = failure_memory.get("latest_failure", {})

        lineage = context.get("concept_lineage_report", {})
        failure_records = lineage.get("failure_records", [])
        if not isinstance(failure_records, list):
            failure_records = []

        judicial_permission = (
            context.get("judicial_cognition_report", {})
            .get("execution_gatekeeper", {})
            .get("execution_permission", "granted")
        )

        unsafe_failure = 0.18 if latest_failure else 0.0
        sandbox_penalty = (
            0.16
            if judicial_permission in ["blocked", "sandbox_only"]
            else 0.0
        )

        contradiction_risk = _clamp(
            (1.0 - identity.get("identity_compatibility", 0.5)) * 0.28
            +
            (1.0 - merge.get("merge_legality", 0.5)) * 0.26
            +
            conflict.get("conflict_intensity", 0.0) * 0.24
            +
            min(len(failure_records), 5) * 0.04
            +
            unsafe_failure
            +
            sandbox_penalty
        )

        actions = []
        if contradiction_risk > 0.50:
            actions.extend([
                "predict_contradictions_before_commit",
                "require_counterexample_search",
            ])
        if contradiction_risk > 0.70:
            actions.append("block_predicted_contradiction")

        return {
            "system": "contradiction_prediction_engine",
            "contradiction_risk": contradiction_risk,
            "judicial_execution_permission": judicial_permission,
            "lineage_failure_records": len(failure_records),
            "contradiction_actions": actions,
            "contradiction_state": (
                "contradiction_prediction_required"
                if actions
                else "contradiction_risk_clear"
            ),
        }
