# ============================================
# NEXRYN EPISTEMIC CERTAINTY ENGINE
# ============================================


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(
                value,
                maximum,
            ),
        ),
        4,
    )


class EpistemicCertaintyEngine:

    def assess(self, context):

        truth_confidence = _clamp(
            context.get(
                "truth_confidence",
                context.get(
                    "truth_evidence",
                    0.0,
                ),
            )
        )

        abstraction_validity = _clamp(
            context.get(
                "abstraction_validity",
                context.get(
                    "abstraction_consistency",
                    0.0,
                ),
            )
        )

        causal_coherence = _clamp(
            context.get(
                "causal_coherence",
                context.get(
                    "causal_consistency",
                    0.0,
                ),
            )
        )

        contradiction_likelihood = _clamp(
            context.get(
                "contradiction_likelihood",
                context.get(
                    "contradiction_risk",
                    0.0,
                ),
            )
        )

        certainty_score = _clamp(
            truth_confidence * 0.34
            + abstraction_validity * 0.26
            + causal_coherence * 0.22
            + (1.0 - contradiction_likelihood) * 0.18
        )

        epistemic_state = (
            "epistemic_assured"
            if certainty_score >= 0.70
            else "epistemic_caution"
            if certainty_score >= 0.48
            else "epistemic_understanding_gap"
        )

        recommended_actions = []
        if certainty_score < 0.62:
            recommended_actions.append(
                "require_epistemic_review",
            )
        if contradiction_likelihood > 0.60:
            recommended_actions.append(
                "increase_contradiction_mitigation",
            )
        if abstraction_validity < 0.40:
            recommended_actions.append(
                "revalidate_abstraction_models",
            )

        return {
            "system":
            "epistemic_certainty_engine",

            "truth_confidence":
            truth_confidence,

            "abstraction_validity":
            abstraction_validity,

            "causal_coherence":
            causal_coherence,

            "contradiction_likelihood":
            contradiction_likelihood,

            "certainty_score":
            certainty_score,

            "epistemic_state":
            epistemic_state,

            "recommended_actions":
            recommended_actions,
        }
