# ============================================
# NEXRYN COGNITIVE HOMEOSTASIS
# ============================================

from datetime import datetime

from core.identity_anchors import (
    identity_anchors,
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


TRAIT_STATES = [
    "emerging",
    "candidate",
    "adaptive",
    "dominant",
    "decaying",
    "suppressed",
    "extinct",
]


class CognitiveHomeostasis:

    def __init__(self):

        self.identity_anchors = identity_anchors
        self.homeostasis_history = []

    def regulate_entropy(self, context):

        entropy = _clamp(
            context.get(
                "runtime_entropy",
                context.get(
                    "cognitive_entropy_report",
                    {},
                ).get(
                    "runtime_entropy",
                    0.0,
                ),
            ),
        )

        entropy_control = _clamp(
            1.0
            -
            max(
                entropy - 0.42,
                0.0,
            )
            * 1.35
        )

        return {
            "runtime_entropy":
            entropy,

            "entropy_control":
            entropy_control,

            "entropy_state":
            (
                "explosive"
                if entropy >= 0.82
                else "elevated"
                if entropy >= 0.62
                else "regulated"
            ),
        }

    def stabilize_identity(self, context, anchor_report=None):

        if anchor_report is None:

            anchor_report = self.identity_anchors.run_cycle(
                context,
            )

        identity = context.get(
            "identity_stability_report",
            {},
        )

        continuity = _clamp(
            identity.get(
                "continuity_verifier",
                {},
            ).get(
                "continuity_score",
                context.get(
                    "identity_continuity",
                    0.0,
                ),
            ),
        )

        anchor_strength = _clamp(
            anchor_report.get(
                "anchor_strength",
                0.0,
            ),
        )

        identity_stability = _clamp(
            continuity * 0.62
            +
            anchor_strength * 0.38
        )

        return {
            "identity_continuity":
            continuity,

            "anchor_strength":
            anchor_strength,

            "identity_stability":
            identity_stability,

            "identity_state":
            (
                "stable"
                if identity_stability >= 0.72
                else "fragile"
                if identity_stability >= 0.50
                else "repair_required"
            ),
        }

    def adaptive_pressure_control(self, context):

        ecology = context.get(
            "cognitive_ecology_report",
            {},
        )

        environmental_pressure = _clamp(
            ecology.get(
                "ecological_pressure_score",
                ecology.get(
                    "resource_pressure",
                    {},
                ).get(
                    "resource_pressure",
                    0.0,
                ),
            ),
        )

        trust = context.get(
            "adaptive_permissioning_report",
            {},
        ).get(
            "trust_score",
            {},
        )

        trust_band = trust.get(
            "trust_band",
            context.get(
                "trust_band",
                "sandboxed",
            ),
        )

        trust_modifier = {
            "trusted": 1.0,
            "probationary": 0.72,
            "sandboxed": 0.42,
            "untrusted": 0.18,
        }.get(
            trust_band,
            0.42,
        )

        return {
            "environmental_pressure":
            environmental_pressure,

            "trust_band":
            trust_band,

            "trust_modifier":
            trust_modifier,
        }

    def semantic_drift_detection(self, context):

        firewall = context.get(
            "semantic_firewall_report",
            {},
        )

        ontology = firewall.get(
            "ontology_intrusion_detection",
            {},
        )

        merge_risk = _clamp(
            ontology.get(
                "average_merge_risk",
                context.get(
                    "average_merge_risk",
                    0.0,
                ),
            ),
        )

        legitimacy_report = context.get(
            "semantic_legitimacy_report",
            {},
        )

        rehearsal_evidence = context.get(
            "causal_rehearsal_report",
            {},
        ).get(
            "evidence_exports",
            {},
        )

        legitimacy_available = (
            "semantic_legitimacy_score"
            in legitimacy_report
        )

        legitimacy = _clamp(
            legitimacy_report.get(
                "semantic_legitimacy_score",
                rehearsal_evidence.get(
                    "causal_attestation_score",
                    0.5,
                ),
            ),
        )

        semantic_drift = _clamp(
            merge_risk * 0.68
            +
            (
                1.0 - legitimacy
            )
            * 0.32
        )

        return {
            "average_merge_risk":
            merge_risk,

            "semantic_legitimacy_score":
            legitimacy,

            "semantic_legitimacy_available":
            legitimacy_available,

            "measurement_source":
            (
                "semantic_legitimacy_report"
                if legitimacy_available
                else "causal_rehearsal_fallback"
            ),

            "semantic_drift":
            semantic_drift,

            "semantic_drift_state":
            (
                "critical"
                if semantic_drift >= 0.78
                else "watched"
                if semantic_drift >= 0.48
                else "stable"
            ),
        }

    def evolutionary_balance(self, context):

        evolutionary = context.get(
            "evolutionary_memory_report",
            {},
        )

        traits = evolutionary.get(
            "adaptive_trait_memory",
            {},
        ).get(
            "traits",
            [],
        )

        state_counts = {}

        for trait in traits:

            state = trait.get(
                "trait_state",
                "emerging",
            )

            state_counts[
                state
            ] = state_counts.get(
                state,
                0,
            ) + 1

        surviving = sum(
            state_counts.get(
                state,
                0,
            )
            for state in [
                "emerging",
                "candidate",
                "adaptive",
                "dominant",
            ]
        )

        suppressed = sum(
            state_counts.get(
                state,
                0,
            )
            for state in [
                "decaying",
                "suppressed",
                "extinct",
            ]
        )

        balance_score = _clamp(
            1.0
            -
            abs(
                surviving - max(
                    suppressed,
                    1,
                )
            )
            /
            max(
                surviving + suppressed,
                1,
            )
        )

        return {
            "trait_states":
            TRAIT_STATES,

            "state_counts":
            state_counts,

            "surviving_traits":
            surviving,

            "suppressed_traits":
            suppressed,

            "evolutionary_balance_score":
            balance_score,

            "balance_state":
            (
                "balanced"
                if balance_score >= 0.55
                else "accumulation_bias"
            ),
        }

    def suppress_runaway_mutations(
        self,
        context,
        entropy_report,
        identity_report,
        pressure_report,
    ):

        evolutionary = context.get(
            "evolutionary_memory_report",
            {},
        )

        traits = evolutionary.get(
            "adaptive_trait_memory",
            {},
        ).get(
            "traits",
            [],
        )

        regulated = []

        entropy_control = entropy_report.get(
            "entropy_control",
            1.0,
        )

        identity_stability = identity_report.get(
            "identity_stability",
            0.0,
        )

        environmental_pressure = pressure_report.get(
            "environmental_pressure",
            0.0,
        )

        trust_modifier = pressure_report.get(
            "trust_modifier",
            0.42,
        )

        for trait in traits:

            base_rate = _clamp(
                trait.get(
                    "mutation_rate",
                    0.10,
                ),
            )

            effective_rate = _clamp(
                base_rate
                *
                max(
                    environmental_pressure,
                    0.10,
                )
                *
                trust_modifier
                *
                entropy_control
                *
                identity_stability
            )

            state = trait.get(
                "trait_state",
                "candidate",
            )

            if entropy_report.get(
                "entropy_state",
            ) == "explosive" and effective_rate < base_rate * 0.35:

                state = (
                    "suppressed"
                    if state
                    in [
                        "emerging",
                        "candidate",
                        "decaying",
                    ]
                    else state
                )

            regulated.append({
                "id":
                trait.get(
                    "id",
                    trait.get(
                        "trait",
                        "unknown",
                    ),
                ),

                "base_mutation_rate":
                base_rate,

                "effective_mutation_rate":
                effective_rate,

                "trait_state":
                state,

                "mutation_governor":
                (
                    "suppressed"
                    if effective_rate <= 0.03
                    else "constrained"
                    if effective_rate <= base_rate * 0.55
                    else "open"
                ),
            })

        return {
            "regulated_traits":
            regulated,

            "suppressed_count":
            len([
                item
                for item in regulated
                if item.get(
                    "mutation_governor",
                )
                == "suppressed"
                or item.get(
                    "trait_state",
                )
                == "suppressed"
            ]),

            "mutation_governor_state":
            (
                "runaway_mutation_suppressed"
                if any(
                    item.get(
                        "mutation_governor",
                    )
                    in [
                        "suppressed",
                        "constrained",
                    ]
                    for item in regulated
                )
                else "mutation_open"
            ),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        anchor_report = self.identity_anchors.run_cycle(
            context,
        )

        entropy_report = self.regulate_entropy(
            context,
        )

        identity_report = self.stabilize_identity(
            context,
            anchor_report,
        )

        pressure_report = self.adaptive_pressure_control(
            context,
        )

        drift_report = self.semantic_drift_detection(
            context,
        )

        balance_report = self.evolutionary_balance(
            context,
        )

        mutation_report = self.suppress_runaway_mutations(
            context,
            entropy_report,
            identity_report,
            pressure_report,
        )

        homeostasis_score = _clamp(
            entropy_report.get(
                "entropy_control",
                0.0,
            )
            * 0.28
            +
            identity_report.get(
                "identity_stability",
                0.0,
            )
            * 0.28
            +
            (
                1.0 - drift_report.get(
                    "semantic_drift",
                    1.0,
                )
            )
            * 0.22
            +
            balance_report.get(
                "evolutionary_balance_score",
                0.0,
            )
            * 0.22
        )

        report = {
            "system":
            "cognitive_homeostasis",

            "identity_anchors":
            anchor_report,

            "entropy_regulation":
            entropy_report,

            "identity_stabilization":
            identity_report,

            "adaptive_pressure_control":
            pressure_report,

            "semantic_drift_detection":
            drift_report,

            "evolutionary_balance":
            balance_report,

            "mutation_governor":
            mutation_report,

            "homeostasis_score":
            homeostasis_score,

            "homeostasis_state":
            (
                "regulated"
                if homeostasis_score >= 0.60
                else "strained"
                if homeostasis_score >= 0.36
                else "critical"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.homeostasis_history.append(
            report,
        )

        self.homeostasis_history = (
            self.homeostasis_history[-128:]
        )

        return report


cognitive_homeostasis = (
    CognitiveHomeostasis()
)
