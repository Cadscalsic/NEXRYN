def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class EpistemicCourtEngine:

    def review(self, context):

        governance = context.get("existential_governance_report", {})
        epistemic = governance.get("epistemic_validation", {})
        judgement = governance.get("adaptive_semantic_judgement", {})

        confidence = _clamp(epistemic.get("epistemic_confidence", 0.5))
        judgement_score = _clamp(judgement.get("judgement_score", 0.5))
        trust = _clamp(
            governance.get("trust_weighted_reasoning", {}).get(
                "reasoning_weight",
                0.5,
            )
        )

        court_score = _clamp(
            confidence * 0.42
            +
            judgement_score * 0.34
            +
            trust * 0.24
        )

        return {
            "system": "epistemic_court_engine",
            "court_score": court_score,
            "court_actions": [
                "require_evidence_hearing",
                "keep_claim_probationary",
            ]
            if court_score < 0.58
            else [],
            "court_state": (
                "epistemic_court_hearing_required"
                if court_score < 0.58
                else "epistemic_court_clear"
            ),
        }
