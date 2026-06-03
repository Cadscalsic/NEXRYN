class ContextualLimiters:

    def run_cycle(self, negotiation_report, fatigue_report):

        overload = fatigue_report.get(
            "ontological_fatigue",
            0.0,
        ) >= 0.5

        return {
            "system":
            "contextual_limiters",

            "contextual_overload":
            overload,

            "limiter_actions":
            [
                "reduce_contextual_reinterpretation",
                "require_absolute_invariant_check",
            ]
            if overload
            else [],

            "limiter_state":
            (
                "contextual_limiters_active"
                if overload
                else "contextual_load_within_bounds"
            ),
        }
