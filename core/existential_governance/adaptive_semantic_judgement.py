def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class AdaptiveSemanticJudgement:

    def judge(self, epistemic, legitimacy, trust_reasoning, ethics):

        judgement_score = _clamp(
            epistemic.get("epistemic_confidence", 0.0) * 0.28
            +
            (1.0 - legitimacy.get("legitimacy_pressure", 1.0)) * 0.22
            +
            trust_reasoning.get("reasoning_weight", 0.0) * 0.24
            +
            ethics.get("continuity_ethics_score", 0.0) * 0.26
        )

        return {
            "system": "adaptive_semantic_judgement",
            "judgement_score": judgement_score,
            "judgement_actions": [
                "defer_semantic_commit_until_judgement_improves",
                "keep_claims_probationary",
            ]
            if judgement_score < 0.58
            else [
                "allow_guarded_semantic_commit",
            ],
            "judgement_state": (
                "adaptive_semantic_judgement_guarded"
                if judgement_score < 0.58
                else "adaptive_semantic_judgement_clear"
            ),
        }
