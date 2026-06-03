def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class SemanticAdmissibilityEngine:

    def assess(self, context):

        judicial = context.get("judicial_cognition_report", {})
        admissibility = judicial.get("admissibility_filter", {})
        legality = judicial.get("semantic_legality", {})
        court = judicial.get("epistemic_court", {})

        governance = context.get("existential_governance_report", {})
        judgement = governance.get("adaptive_semantic_judgement", {})
        legitimacy = governance.get("semantic_legitimacy", {})

        admissible_bonus = (
            0.14
            if admissibility.get("admissible", False)
            else -0.12
        )

        admissibility_score = _clamp(
            legality.get("semantic_legality", 0.5) * 0.28
            +
            court.get("court_score", 0.5) * 0.22
            +
            judgement.get("judgement_score", 0.5) * 0.24
            +
            (1.0 - legitimacy.get("legitimacy_pressure", 0.5)) * 0.26
            +
            admissible_bonus
        )

        actions = []
        if admissibility_score < 0.54:
            actions.extend([
                "filter_semantically_inadmissible_claim",
                "require_constitutional_semantic_review",
            ])
        if not admissibility.get("admissible", True):
            actions.append("route_inadmissible_meaning_to_sandbox")

        return {
            "system": "semantic_admissibility_engine",
            "semantic_admissibility": admissibility_score,
            "judicial_admissible": admissibility.get("admissible", True),
            "admissibility_actions": actions,
            "admissibility_state": (
                "semantic_admissibility_restricted"
                if actions
                else "semantic_admissibility_clear"
            ),
        }
