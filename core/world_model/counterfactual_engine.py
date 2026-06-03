# ============================================
# NEXRYN CAUSAL COUNTERFACTUAL ENGINE
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


class CausalCounterfactualEngine:

    def build_counterfactuals(self, context):

        entropy = context.get(
            "runtime_entropy",
            context.get(
                "cognitive_entropy_report",
                {},
            ).get(
                "runtime_entropy",
                0.0,
            ),
        )

        return [
            {
                "scenario":
                "increase_cooling",

                "entropy_delta":
                -0.18,

                "identity_delta":
                0.02,

                "execution_delta":
                -0.04,
            },
            {
                "scenario":
                "allow_more_exploration",

                "entropy_delta":
                0.14,

                "identity_delta":
                0.05,

                "execution_delta":
                0.08,
            },
            {
                "scenario":
                "prefer_compiled_macros",

                "entropy_delta":
                -0.12,

                "identity_delta":
                -0.01,

                "execution_delta":
                0.06,
            },
            {
                "scenario":
                "compress_recursion",

                "entropy_delta":
                -0.10,

                "identity_delta":
                0.00,

                "execution_delta":
                -0.02,
            },
        ]

    def compare_outcomes(self, context):

        entropy = context.get(
            "runtime_entropy",
            context.get(
                "cognitive_entropy_report",
                {},
            ).get(
                "runtime_entropy",
                0.0,
            ),
        )

        identity = context.get(
            "identity_anchor_core_report",
            {},
        ).get(
            "identity_drift_before",
            context.get(
                "identity_drift",
                0.0,
            ),
        )

        outcomes = []

        for scenario in self.build_counterfactuals(
            context,
        ):

            projected_entropy = _clamp(
                entropy
                +
                scenario.get(
                    "entropy_delta",
                    0.0,
                )
            )

            projected_identity = _clamp(
                identity
                +
                scenario.get(
                    "identity_delta",
                    0.0,
                )
            )

            utility = _clamp(
                (1.0 - projected_entropy) * 0.45
                +
                (1.0 - projected_identity) * 0.30
                +
                (0.50 + scenario.get("execution_delta", 0.0)) * 0.25
            )

            outcomes.append({
                "scenario":
                scenario.get(
                    "scenario",
                ),

                "projected_entropy":
                projected_entropy,

                "projected_identity_risk":
                projected_identity,

                "execution_usefulness":
                _clamp(
                    0.50
                    +
                    scenario.get(
                        "execution_delta",
                        0.0,
                    )
                ),

                "outcome_utility":
                utility,

                "timestamp":
                str(
                    datetime.utcnow()
                ),
            })

        return {
            "system":
            "causal_counterfactual_engine",

            "outcomes":
            sorted(
                outcomes,
                key=lambda item: item.get(
                    "outcome_utility",
                    0.0,
                ),
                reverse=True,
            ),

            "best_outcome":
            (
                sorted(
                    outcomes,
                    key=lambda item: item.get(
                        "outcome_utility",
                        0.0,
                    ),
                    reverse=True,
                )[0]
                if outcomes
                else {}
            ),
        }
