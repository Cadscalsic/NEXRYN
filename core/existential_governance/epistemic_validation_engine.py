def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class EpistemicValidationEngine:

    def validate(self, context):

        legitimacy = _clamp(
            context.get("semantic_legitimacy_report", {}).get(
                "semantic_legitimacy_score",
                0.5,
            )
        )
        truth_lock = context.get("ontological_boundary_report", {}).get(
            "invariant_boundary",
            {},
        ).get("protected_invariants", [])
        trust = _clamp(
            context.get("adaptive_permissioning_report", {})
            .get("trust_score", {})
            .get("trust_score", context.get("trust_score", 0.5))
        )

        epistemic_confidence = _clamp(
            legitimacy * 0.46
            +
            trust * 0.34
            +
            min(len(truth_lock), 8) * 0.025
        )

        return {
            "system": "epistemic_validation_engine",
            "semantic_legitimacy_score": legitimacy,
            "trust_score": trust,
            "protected_truth_count": len(truth_lock),
            "epistemic_confidence": epistemic_confidence,
            "validation_actions": [
                "require_epistemic_attestation",
                "defer_untrusted_semantic_commit",
            ]
            if epistemic_confidence < 0.58
            else [],
            "validation_state": (
                "epistemic_validation_required"
                if epistemic_confidence < 0.58
                else "epistemic_validation_stable"
            ),
        }
