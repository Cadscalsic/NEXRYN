# ============================================
# NEXRYN RECURSIVE SELF MODEL
# ============================================

from datetime import datetime

from core.self_model.capability_map import (
    CapabilityMap,
)

from core.self_model.confidence_model import (
    ConfidenceModel,
)

from core.self_model.limitation_model import (
    LimitationModel,
)


class RecursiveSelfModel:

    def __init__(self):

        self.capability_map = CapabilityMap()
        self.limitation_model = LimitationModel()
        self.confidence_model = ConfidenceModel()
        self.self_history = []

    def infer_failure_patterns(self, context):

        patterns = []

        thermodynamics = context.get(
            "cognitive_thermodynamics_report",
            {},
        )

        if thermodynamics.get(
            "thermodynamic_state",
        ) in [
            "critical",
            "hot_but_regulated",
        ]:

            patterns.append(
                "semantic_heat_accumulation",
            )

        routing = context.get(
            "predictive_attention_routing_v2_report",
            {},
        )

        if routing.get(
            "routing_state",
        ) == "rerouted":

            patterns.append(
                "direct_reasoning_route_instability",
            )

        recursive = context.get(
            "recursive_pressure_governor_report",
            {},
        )

        if recursive.get(
            "pressure_state",
        ) == "capped":

            patterns.append(
                "recursive_depth_overrun",
            )

        return patterns

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        capability_report = self.capability_map.map_capabilities(
            context,
        )

        limitation_report = self.limitation_model.detect_limitations(
            context,
        )

        confidence_report = self.confidence_model.estimate(
            context,
            capability_report,
            limitation_report,
        )

        failure_patterns = self.infer_failure_patterns(
            context,
        )

        report = {
            "system":
            "recursive_self_model",

            "self_representation":
            {
                "capable_of":
                [
                    item.get(
                        "capability",
                    )
                    for item in capability_report.get(
                        "capabilities",
                        [],
                    )
                    if item.get(
                        "available",
                    )
                ],

                "uncertain_about":
                [
                    item.get(
                        "limitation",
                    )
                    for item in limitation_report.get(
                        "limitations",
                        [],
                    )
                ],

                "known_failure_patterns":
                failure_patterns,
            },

            "capability_map":
            capability_report,

            "limitation_model":
            limitation_report,

            "confidence_model":
            confidence_report,

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.self_history.append(
            report,
        )

        self.self_history = (
            self.self_history[-64:]
        )

        return report


recursive_self_model = (
    RecursiveSelfModel()
)
