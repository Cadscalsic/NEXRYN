def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class SemanticLegitimacyController:

    def control(self, context, epistemic):

        legitimacy = _clamp(epistemic.get("semantic_legitimacy_score", 0.5))
        hybrid_risk = _clamp(
            1.0
            -
            context.get("hybrid_governance_report", {}).get(
                "hybrid_governance_score",
                0.5,
            )
        )
        recursive_risk = _clamp(
            1.0
            -
            context.get("recursive_reflective_report", {}).get(
                "recursive_reflective_score",
                0.5,
            )
        )

        legitimacy_pressure = _clamp(
            (1.0 - legitimacy) * 0.46
            +
            hybrid_risk * 0.26
            +
            recursive_risk * 0.28
        )

        return {
            "system": "semantic_legitimacy_controller",
            "legitimacy_pressure": legitimacy_pressure,
            "legitimacy_actions": [
                "route_semantic_claims_to_legitimacy_review",
                "preserve_unverified_claims_as_hypotheses",
            ]
            if legitimacy_pressure >= 0.34
            else [],
            "legitimacy_state": (
                "semantic_legitimacy_review_active"
                if legitimacy_pressure >= 0.34
                else "semantic_legitimacy_clear"
            ),
        }
