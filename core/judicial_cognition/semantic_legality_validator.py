def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class SemanticLegalityValidator:

    def validate(self, context, court):

        legitimacy_pressure = _clamp(
            context.get("existential_governance_report", {})
            .get("semantic_legitimacy", {})
            .get("legitimacy_pressure", 0.0)
        )
        legality = _clamp(court.get("court_score", 0.5) * 0.56 + (1.0 - legitimacy_pressure) * 0.44)

        return {
            "system": "semantic_legality_validator",
            "semantic_legality": legality,
            "legality_actions": [
                "reject_semantically_illegal_commit",
                "require_legitimacy_repair",
            ]
            if legality < 0.58
            else [],
            "legality_state": (
                "semantic_legality_review_required"
                if legality < 0.58
                else "semantic_legality_clear"
            ),
        }
