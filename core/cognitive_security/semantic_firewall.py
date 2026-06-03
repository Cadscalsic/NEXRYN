# ============================================
# NEXRYN SEMANTIC FIREWALL
# ============================================

from datetime import datetime

from core.cognitive_security.concept_sandboxing import (
    ConceptSandboxing,
)

from core.cognitive_security.identity_attack_detection import (
    IdentityAttackDetection,
)

from core.cognitive_security.ontology_intrusion_detection import (
    OntologyIntrusionDetection,
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


class SemanticFirewall:

    def __init__(self):

        self.ontology_ids = OntologyIntrusionDetection()
        self.concept_sandboxing = ConceptSandboxing()
        self.identity_attack_detection = IdentityAttackDetection()
        self.firewall_history = []

    def decide(
        self,
        ontology_report,
        sandbox_report,
        identity_report,
    ):

        ontology_score = ontology_report.get(
            "intrusion_score",
            0.0,
        )

        identity_score = identity_report.get(
            "attack_score",
            0.0,
        )

        average_merge_risk = ontology_report.get(
            "average_merge_risk",
            0.0,
        )

        sandbox_locked = (
            sandbox_report.get(
                "sandbox_state",
            )
            == "locked"
        )

        firewall_pressure = _clamp(
            ontology_score * 0.45
            +
            identity_score * 0.30
            +
            average_merge_risk * 0.20
            +
            (
                0.05
                if sandbox_locked
                else 0.0
            )
        )

        firewall_state = (
            "sealed"
            if firewall_pressure >= 0.78
            or average_merge_risk >= 0.82
            else "quarantine"
            if firewall_pressure >= 0.62
            or sandbox_locked
            else "filtered"
            if firewall_pressure >= 0.38
            else "open"
        )

        if firewall_state == "sealed":

            decision = "deny"

        elif firewall_state == "quarantine":

            decision = "quarantine"

        elif firewall_state == "filtered":

            decision = "allow_after_attestation"

        else:

            decision = "allow"

        commit_probability_hint = _clamp(
            1.0
            -
            firewall_pressure * 0.72
            -
            average_merge_risk * 0.18
            +
            (
                0.04
                if firewall_state == "filtered"
                else 0.0
            )
        )

        blocked_operations = []

        if firewall_state in [
            "sealed",
            "quarantine",
        ]:

            blocked_operations.extend([
                "semantic_merge",
                "ontology_mutation",
                "identity_topology_write",
                "bridge_concept_promotion",
                "abstraction_core_commit",
            ])

        elif firewall_state == "filtered":

            blocked_operations.extend([
                "unattested_semantic_merge",
                "unattested_bridge_concept_promotion",
            ])

        return {
            "firewall_pressure":
            firewall_pressure,

            "firewall_state":
            firewall_state,

            "decision":
            decision,

            "commit_probability_hint":
            commit_probability_hint,

            "blocked_operations":
            blocked_operations,

            "required_attestations":
            [
                "semantic_consistency",
                "identity_continuity",
                "causal_non_regression",
                "entropy_delta_bound",
            ],
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        ontology_report = self.ontology_ids.inspect(
            context,
        )

        sandbox_report = self.concept_sandboxing.run_cycle(
            context,
        )

        identity_report = self.identity_attack_detection.inspect(
            context,
        )

        decision = self.decide(
            ontology_report,
            sandbox_report,
            identity_report,
        )

        report = {
            "system":
            "semantic_firewall",

            "zero_trust_policy":
            "treat_merge_mutation_abstraction_bridge_as_hostile_until_attested",

            "ontology_intrusion_detection":
            ontology_report,

            "concept_sandboxing":
            sandbox_report,

            "identity_attack_detection":
            identity_report,

            "firewall_pressure":
            decision.get(
                "firewall_pressure",
                0.0,
            ),

            "firewall_state":
            decision.get(
                "firewall_state",
                "open",
            ),

            "decision":
            decision.get(
                "decision",
                "allow",
            ),

            "commit_probability_hint":
            decision.get(
                "commit_probability_hint",
                0.0,
            ),

            "blocked_operations":
            decision.get(
                "blocked_operations",
                [],
            ),

            "required_attestations":
            decision.get(
                "required_attestations",
                [],
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.firewall_history.append(
            report,
        )

        self.firewall_history = (
            self.firewall_history[-128:]
        )

        return report


semantic_firewall = (
    SemanticFirewall()
)
