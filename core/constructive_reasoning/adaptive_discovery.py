# ============================================
# NEXRYN ADAPTIVE DISCOVERY
# ============================================

from datetime import datetime

from core.constructive_reasoning.beneficial_mutation_learning import (
    BeneficialMutationLearning,
)

from core.constructive_reasoning.causal_gain_estimator import (
    CausalGainEstimator,
)

from core.constructive_reasoning.constructive_signal import (
    ConstructiveSignal,
)

from core.constructive_reasoning.novel_pattern_value import (
    NovelPatternValue,
)


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


class AdaptiveDiscovery:

    def __init__(self):

        self.novel_pattern_value = NovelPatternValue()
        self.causal_gain_estimator = CausalGainEstimator()
        self.constructive_signal = ConstructiveSignal()
        self.beneficial_mutation_learning = (
            BeneficialMutationLearning()
        )
        self.discovery_history = []

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        rehearsal = context.get(
            "causal_rehearsal_report",
            {},
        )

        simulations = rehearsal.get(
            "mutation_simulator",
            {},
        ).get(
            "simulations",
            [],
        )

        assessments = []

        for simulation in simulations:

            pattern_report = self.novel_pattern_value.evaluate(
                simulation,
            )

            gain_report = self.causal_gain_estimator.estimate(
                simulation,
                pattern_report,
            )

            signal_report = self.constructive_signal.combine(
                simulation,
                pattern_report,
                gain_report,
            )

            item = {
                "simulation":
                simulation,

                "novel_pattern_value":
                pattern_report,

                "causal_gain_estimate":
                gain_report,

                "constructive_signal":
                signal_report,

                "constructive_score":
                signal_report.get(
                    "constructive_score",
                    0.0,
                ),
            }

            assessments.append(
                item,
            )

        constructive_assessments = [
            item
            for item in assessments
            if item.get(
                "constructive_signal",
                {},
            ).get(
                "constructive_state",
            )
            in [
                "constructive",
                "promising",
            ]
        ]

        learning_report = self.beneficial_mutation_learning.learn(
            constructive_assessments,
        )

        constructive_signal = _clamp(
            sum(
                item.get(
                    "constructive_score",
                    0.0,
                )
                for item in constructive_assessments
            )
            /
            max(
                len(
                    assessments,
                ),
                1,
            )
        )

        report = {
            "system":
            "adaptive_discovery",

            "constructive_reasoning_mode":
            "detect_cognitive_value_not_only_risk",

            "assessment_count":
            len(
                assessments,
            ),

            "constructive_signal":
            constructive_signal,

            "constructive_assessments":
            constructive_assessments[:32],

            "all_assessments":
            assessments[:64],

            "beneficial_mutation_learning":
            learning_report,

            "discovery_state":
            (
                "constructive_cognition_found"
                if constructive_signal >= 0.34
                else "promising_cognition_detected"
                if constructive_assessments
                else "no_constructive_signal"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.discovery_history.append(
            report,
        )

        self.discovery_history = (
            self.discovery_history[-128:]
        )

        return report


adaptive_discovery = (
    AdaptiveDiscovery()
)
