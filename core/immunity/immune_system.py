# ============================================
# NEXRYN COGNITIVE IMMUNE SYSTEM V2
# ============================================

from datetime import datetime

from core.immunity.collapse_predictor import (
    CollapsePredictor,
)

from core.immunity.identity_firewall import (
    IdentityFirewall,
)

from core.immunity.semantic_antibodies import (
    SemanticAntibodySystem,
)


class CognitiveImmuneSystemV2:

    def __init__(self):

        self.semantic_antibodies = SemanticAntibodySystem()
        self.collapse_predictor = CollapsePredictor()
        self.identity_firewall = IdentityFirewall()
        self.immune_history = []

    def build_immune_response(
        self,
        antibody_report,
        collapse_report,
        firewall_report,
    ):

        actions = []

        actions.extend(
            collapse_report.get(
                "preventive_actions",
                [],
            )
        )

        if antibody_report.get(
            "infection",
            {},
        ).get(
            "infection_state",
        ) == "infected":

            actions.append(
                "quarantine_semantic_infection",
            )

        if firewall_report.get(
            "firewall_state",
        ) == "sealed":

            actions.append(
                "block_identity_mutation",
            )

        return sorted(
            set(
                actions,
            )
        )

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        antibody_report = self.semantic_antibodies.generate_antibodies(
            context,
        )

        collapse_report = self.collapse_predictor.predict(
            context,
        )

        firewall_report = self.identity_firewall.inspect(
            context,
        )

        response_actions = self.build_immune_response(
            antibody_report,
            collapse_report,
            firewall_report,
        )

        report = {
            "system":
            "cognitive_immune_system_v2",

            "semantic_antibodies":
            antibody_report,

            "collapse_predictor":
            collapse_report,

            "identity_firewall":
            firewall_report,

            "immune_response_actions":
            response_actions,

            "prevents":
            [
                "runaway_recursion",
                "ontology_collapse",
                "semantic_infection",
                "unstable_concept_fusion",
            ],

            "immune_state":
            (
                "emergency_response"
                if collapse_report.get(
                    "collapse_state",
                )
                in [
                    "critical",
                    "imminent",
                ]
                or firewall_report.get(
                    "firewall_state",
                )
                == "sealed"
                else "active_monitoring"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.immune_history.append(
            report,
        )

        self.immune_history = (
            self.immune_history[-64:]
        )

        return report


cognitive_immune_system_v2 = (
    CognitiveImmuneSystemV2()
)
