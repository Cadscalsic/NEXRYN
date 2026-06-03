def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class TrustWeightedReasoning:

    def weight(self, context, epistemic):

        trust = _clamp(epistemic.get("trust_score", 0.5))
        pressure = _clamp(
            context.get("existential_pressure_report", {}).get("managed_pressure", 0.0)
        )
        hybrid_score = _clamp(
            context.get("hybrid_governance_report", {}).get(
                "hybrid_governance_score",
                0.5,
            )
        )

        reasoning_weight = _clamp(
            trust * 0.48
            +
            hybrid_score * 0.28
            +
            (1.0 - pressure) * 0.24
        )

        return {
            "system": "trust_weighted_reasoning",
            "reasoning_weight": reasoning_weight,
            "reasoning_actions": [
                "sandbox_low_trust_reasoning_paths",
                "prefer_attested_reasoning_routes",
            ]
            if reasoning_weight < 0.56
            else [],
            "reasoning_state": (
                "trust_weighted_reasoning_guarded"
                if reasoning_weight < 0.56
                else "trust_weighted_reasoning_open"
            ),
        }
