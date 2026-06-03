def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class AmbiguityReasoningSystem:

    def assess(self, context, court):

        ambiguity = _clamp(
            context.get(
                "ambiguity_score",
                1.0 - court.get("court_score", 0.5),
            )
        )
        hybrid_conflict = _clamp(
            context.get("hybrid_governance_report", {})
            .get("paradigm_conflict", {})
            .get("paradigm_conflict_score", 0.0)
        )

        ambiguity_load = _clamp(ambiguity * 0.62 + hybrid_conflict * 0.38)

        return {
            "system": "ambiguity_reasoning_system",
            "ambiguity_load": ambiguity_load,
            "ambiguity_actions": [
                "split_ambiguous_claims",
                "route_ambiguity_to_sandboxed_reasoning",
            ]
            if ambiguity_load >= 0.34
            else [],
            "ambiguity_state": (
                "ambiguity_reasoning_required"
                if ambiguity_load >= 0.34
                else "ambiguity_low"
            ),
        }
