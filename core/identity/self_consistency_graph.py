# ============================================
# NEXRYN SELF CONSISTENCY GRAPH
# ============================================

from datetime import datetime


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


class SelfConsistencyGraph:

    def build(self, anchor_report, causal_memory_report, context):

        laws = anchor_report.get(
            "protected_cognition_laws",
            [],
        )

        invariants = anchor_report.get(
            "architectural_invariants",
            [],
        )

        principles = anchor_report.get(
            "core_principles",
            [],
        )

        recent_events = causal_memory_report.get(
            "recent_events",
            [],
        )

        event_pressure = _clamp(
            len(
                recent_events,
            )
            /
            32
        )

        anchor_strength = _clamp(
            anchor_report.get(
                "anchor_strength",
                0.0,
            ),
        )

        rehearsal = context.get(
            "causal_rehearsal_report",
            {},
        )

        future_state = rehearsal.get(
            "future_state_projection",
            {},
        ).get(
            "future_state",
            "unknown",
        )

        future_bonus = (
            0.10
            if future_state == "safe_evolution_window"
            else 0.03
            if future_state == "rehearsal_required"
            else 0.0
        )

        consistency_score = _clamp(
            anchor_strength * 0.62
            +
            (
                1.0 - event_pressure
            )
            * 0.23
            +
            future_bonus
        )

        return {
            "system":
            "self_consistency_graph",

            "nodes":
            {
                "core_principles":
                principles,

                "causal_history":
                causal_memory_report.get(
                    "recent_events",
                    [],
                ),

                "architectural_invariants":
                invariants,

                "protected_cognition_laws":
                laws,
            },

            "edges":
            [
                {
                    "from": "mutation_candidate",
                    "to": "core_principles",
                    "relation": "must_preserve",
                },
                {
                    "from": "mutation_candidate",
                    "to": "causal_history",
                    "relation": "must_explain",
                },
                {
                    "from": "mutation_candidate",
                    "to": "architectural_invariants",
                    "relation": "must_not_violate",
                },
                {
                    "from": "mutation_candidate",
                    "to": "protected_cognition_laws",
                    "relation": "must_obey",
                },
            ],

            "consistency_score":
            consistency_score,

            "consistency_state":
            (
                "consistent"
                if consistency_score >= 0.72
                else "fragile"
                if consistency_score >= 0.48
                else "fragmenting"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
