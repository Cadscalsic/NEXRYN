# ============================================
# NEXRYN CONCEPT LIFECYCLE MANAGER
# ============================================

from datetime import datetime

from core.concept_lifecycle.concept_birth import (
    ConceptBirth,
)

from core.concept_lifecycle.concept_admission_pipeline import (
    ConceptAdmissionPipeline,
)

from core.concept_lifecycle.concept_decay import (
    ConceptDecay,
)

from core.concept_lifecycle.concept_energy_economics import (
    ConceptEnergyEconomics,
)

from core.concept_lifecycle.concept_reputation_engine import (
    ConceptReputationEngine,
)

from core.concept_lifecycle.concept_retirement import (
    ConceptRetirement,
)

from core.concept_lifecycle.concept_revival import (
    ConceptRevival,
)

from core.concept_lifecycle.semantic_gc import (
    SemanticGarbageCollector,
)

from core.concept_lifecycle.concept_validation import (
    ConceptValidation,
)

from core.concept_lifecycle.concept_maturity import (
    ConceptMaturityTracker,
)


class ConceptLifecycleManager:

    def __init__(self):

        self.concept_birth = ConceptBirth()
        self.concept_admission_pipeline = ConceptAdmissionPipeline()
        self.concept_reputation_engine = ConceptReputationEngine()
        self.concept_validation = ConceptValidation()
        self.concept_decay = ConceptDecay()
        self.concept_energy_economics = ConceptEnergyEconomics()
        self.concept_retirement = ConceptRetirement()
        self.concept_revival = ConceptRevival()
        self.semantic_gc = SemanticGarbageCollector()
        self.concept_maturity_tracker = ConceptMaturityTracker()
        self.concept_registry = {}
        self.lifecycle_history = []
        self.knowledge_maturity_report = {}

    def update_knowledge_maturity(self, ledger_report, context=None):

        context = context if isinstance(context, dict) else {}

        self.knowledge_maturity_report = (
            self.concept_maturity_tracker
            .evaluate(
                ledger_report,
                context.get(
                    "truth_candidate_engine_report",
                    context.get(
                        "truth_candidate_report",
                        {},
                    ),
                ),
                context.get(
                    "truth_registry_report",
                    {},
                ),
            )
        )

        return self.knowledge_maturity_report

    def register_validated(self, validation_report):

        for concept in validation_report.get(
            "validated_concepts",
            [],
        ):

            concept_id = concept.get(
                "concept_id",
            )

            if concept_id is None:

                continue

            existing = self.concept_registry.get(
                concept_id,
                {},
            )

            updated = dict(
                existing,
            )

            updated.update(
                concept,
            )

            updated[
                "activation"
            ] = max(
                updated.get(
                    "activation",
                    0.0,
                ),
                concept.get(
                    "viability",
                    0.0,
                ),
            )

            self.concept_registry[
                concept_id
            ] = updated

    def apply_admission_reputation(self, admission_report):

        for evaluation in admission_report.get(
            "evaluations",
            [],
        ):

            concept_id = evaluation.get(
                "concept_id",
            )

            if concept_id not in self.concept_registry:

                continue

            reputation = evaluation.get(
                "historical_reputation",
                {},
            )

            if not reputation:

                continue

            self.concept_registry[
                concept_id
            ][
                "concept_reputation"
            ] = reputation

            self.concept_registry[
                concept_id
            ][
                "reputation"
            ] = reputation.get(
                "reputation",
                0.0,
            )

    def build_reputation_anchor_report(self, reputation_report):

        concept_reputations = reputation_report.get(
            "concept_reputations",
            [],
        )

        if not concept_reputations:

            return {
                "system":
                "reputation_anchor",

                "anchor_source":
                "missing_epistemic_evidence",

                "strength":
                0.0,

                "reputation_state":
                "unknown",

                "survival_is_not_truth":
                True,
            }

        contradiction_load = sum(
            item.get(
                "contradiction_history",
                0.0,
            )
            for item in concept_reputations
        ) / max(
            len(
                concept_reputations,
            ),
            1,
        )

        failure_propagation = sum(
            item.get(
                "failure_propagation_score",
                0.0,
            )
            for item in concept_reputations
        ) / max(
            len(
                concept_reputations,
            ),
            1,
        )

        strength = max(
            0.0,
            min(
                1.0,
                reputation_report.get(
                    "average_concept_reputation",
                    0.0,
                )
                -
                contradiction_load * 0.18
                -
                failure_propagation * 0.22,
            ),
        )

        return {
            "system":
            "reputation_anchor",

            "anchor_source":
            "concept_reputation_engine",

            "strength":
            round(
                strength,
                4,
            ),

            "reputation_state":
            reputation_report.get(
                "reputation_state",
                "epistemically_forming",
            ),

            "concept_count":
            len(
                concept_reputations,
            ),

            "contradiction_load":
            round(
                contradiction_load,
                4,
            ),

            "failure_propagation_score":
            round(
                failure_propagation,
                4,
            ),

            "survival_is_not_truth":
            True,
        }

    def summarize_registry(self):

        states = {}

        for concept in self.concept_registry.values():

            state = concept.get(
                "state",
                "unknown",
            )

            states[
                state
            ] = states.get(
                state,
                0,
            ) + 1

        return {
            "registry_size":
            len(
                self.concept_registry,
            ),

            "states":
            states,

            "concepts":
            list(
                self.concept_registry.values()
            )[:64],
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        birth_report = self.concept_birth.collect_births(
            context,
        )

        concept_reputation_report = (
            self.concept_reputation_engine
            .evaluate(
                birth_report,
                self.concept_registry,
                context,
            )
        )

        context[
            "concept_reputation_report"
        ] = concept_reputation_report

        reputation_anchor_report = (
            self.build_reputation_anchor_report(
                concept_reputation_report,
            )
        )

        context[
            "reputation_anchor_report"
        ] = reputation_anchor_report

        admission_report = (
            self.concept_admission_pipeline
            .evaluate(
                birth_report,
                self.concept_registry,
                context,
            )
        )

        validation_report = self.concept_validation.validate(
            birth_report,
            context,
            admission_report,
        )

        self.register_validated(
            validation_report,
        )

        self.apply_admission_reputation(
            admission_report,
        )

        decay_report = self.concept_decay.decay(
            self.concept_registry,
        )

        retirement_report = self.concept_retirement.retire(
            self.concept_registry,
        )

        concept_energy_report = (
            self.concept_energy_economics
            .evaluate(
                self.concept_registry,
            )
        )

        semantic_gc_report = self.semantic_gc.collect(
            self.concept_registry,
            context,
        )

        revival_report = self.concept_revival.revive(
            self.concept_registry,
            context,
        )

        report = {
            "system":
            "concept_lifecycle_manager",

            "concept_birth":
            birth_report,

            "bridge_hallucination_filter":
            birth_report.get(
                "bridge_hallucination_filter",
                {},
            ),

            "concept_admission_pipeline":
            admission_report,

            "concept_reputation_engine":
            concept_reputation_report,

            "reputation_anchor":
            reputation_anchor_report,

            "concept_validation":
            validation_report,

            "concept_decay":
            decay_report,

            "concept_retirement":
            retirement_report,

            "concept_energy_economics":
            concept_energy_report,

            "semantic_gc":
            semantic_gc_report,

            "concept_revival":
            revival_report,

            "knowledge_maturity":
            self.knowledge_maturity_report,

            "registry":
            self.summarize_registry(),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.lifecycle_history.append(
            report,
        )

        self.lifecycle_history = (
            self.lifecycle_history[-64:]
        )

        return report


concept_lifecycle_manager = (
    ConceptLifecycleManager()
)
