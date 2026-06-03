# ============================================
# NEXRYN SEMANTIC LEGITIMACY ENGINE
# ============================================

from datetime import datetime

from core.semantic_legitimacy.causal_benefit_estimator import (
    CausalBenefitEstimator,
)

from core.semantic_legitimacy.constructive_mutation_detection import (
    ConstructiveMutationDetection,
)

from core.semantic_legitimacy.novelty_scoring import (
    NoveltyScoring,
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


class SemanticLegitimacyEngine:

    def __init__(self):

        self.novelty_scoring = NoveltyScoring()
        self.constructive_mutation_detection = (
            ConstructiveMutationDetection()
        )
        self.causal_benefit_estimator = CausalBenefitEstimator()
        self.legitimacy_history = []

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        novelty_report = self.novelty_scoring.score(
            context,
        )

        mutation_report = (
            self.constructive_mutation_detection
            .detect(context)
        )

        benefit_report = self.causal_benefit_estimator.estimate(
            context,
        )

        evolutionary = context.get(
            "evolutionary_memory_report",
            {},
        )

        selection_pressure = evolutionary.get(
            "evolutionary_pressure",
            {},
        ).get(
            "pressure_score",
            0.0,
        )

        ecology = context.get(
            "cognitive_ecology_report",
            {},
        )

        landscape_score = ecology.get(
            "adaptive_fitness_landscape",
            {},
        ).get(
            "average_fitness_peak",
            0.0,
        )

        homeostasis = context.get(
            "cognitive_homeostasis_report",
            {},
        )

        homeostasis_score = homeostasis.get(
            "homeostasis_score",
            0.0,
        )

        natural_selection = context.get(
            "cognitive_natural_selection_report",
            {},
        )

        selected_count = natural_selection.get(
            "selected_count",
            0,
        )

        suppressed_count = (
            natural_selection.get(
                "suppressed_count",
                0,
            )
            +
            natural_selection.get(
                "extinct_count",
                0,
            )
        )

        natural_selection_score = _clamp(
            selected_count
            /
            max(
                selected_count + suppressed_count,
                1,
            )
        )

        extinction = context.get(
            "extinction_engine_report",
            {},
        )

        extinction_hygiene_score = _clamp(
            1.0
            -
            extinction.get(
                "graveyard_pressure",
                0.0,
            )
        )

        entropy_regulation = context.get(
            "entropy_regulator_report",
            {},
        )

        cooling_score = _clamp(
            1.0
            -
            entropy_regulation.get(
                "cognitive_cooling",
                {},
            ).get(
                "cooling_intensity",
                0.0,
            )
            * 0.35
        )

        recovery = context.get(
            "trait_recovery_report",
            {},
        )

        recovery_review_score = _clamp(
            (
                recovery.get(
                    "recovered_count",
                    0,
                )
                +
                recovery.get(
                    "wrongful_extinction_risk_count",
                    0,
                )
                * 0.5
            )
            /
            max(
                recovery.get(
                    "monitored_count",
                    0,
                ),
                1,
            )
        )

        guardian = context.get(
            "identity_continuity_guardian_report",
            {},
        )

        guardian_blocks_rewrite = (
            guardian.get(
                "catastrophic_rewrite_guard",
                {},
            ).get(
                "block_rewrite",
                False,
            )
        )

        semantic_anchor = guardian.get(
            "semantic_anchor_graph",
            {},
        )

        semantic_anchor_score = _clamp(
            semantic_anchor.get(
                "identity_stability",
                {},
            ).get(
                "identity_stability",
                0.0,
            )
        )

        identity_guardian_score = (
            0.0
            if guardian_blocks_rewrite
            else semantic_anchor_score
            if semantic_anchor_score
            else 1.0
        )

        memory_compression = context.get(
            "memory_compression_report",
            {},
        )

        memory_pressure_score = _clamp(
            1.0
            -
            memory_compression.get(
                "compression_ratio",
                1.0,
            )
            * 0.20
        )

        sandbox = context.get(
            "evolution_sandbox_report",
            {},
        )

        sandbox_score = _clamp(
            sandbox.get(
                "best_future",
                {},
            ).get(
                "commit_probability",
                0.0,
            )
        )

        concept_fusion = context.get(
            "concept_fusion_report",
            {},
        )

        fusion_count = len(
            concept_fusion.get(
                "fused_concepts",
                [],
            )
        )

        rejected_fusion_count = len(
            concept_fusion.get(
                "rejected_fusions",
                [],
            )
        )

        fusion_score = _clamp(
            fusion_count
            /
            max(
                fusion_count + rejected_fusion_count,
                1,
            )
        )

        stability_field = context.get(
            "stability_field_report",
            {},
        )

        stability_rejected = stability_field.get(
            "destructive_mutation_filter",
            {},
        ).get(
            "reject_destructive_mutation",
            False,
        )

        stability_field_score = (
            0.0
            if stability_rejected
            else _clamp(
                stability_field.get(
                    "identity_resilience",
                    {},
                ).get(
                    "identity_resilience_score",
                    0.0,
                )
            )
        )

        identity_reasoner = context.get(
            "identity_reasoner_report",
            {},
        )

        repair_required = identity_reasoner.get(
            "repair_required_count",
            0,
        )

        identity_reasoning_score = _clamp(
            1.0
            -
            repair_required
            /
            max(
                len(
                    identity_reasoner.get(
                        "identity_analyses",
                        [],
                    )
                ),
                1,
            )
        )

        concept_lineage = context.get(
            "concept_lineage_report",
            {},
        )

        lineage_score = (
            1.0
            if concept_lineage.get(
                "lineage_count",
                0,
            )
            else 0.5
        )

        recursive_guardian = context.get(
            "recursive_guardian_report",
            {},
        )

        recursive_safety_score = (
            0.0
            if recursive_guardian.get(
                "recursive_guardian_state",
            )
            == "recursive_safety_intervention"
            else 1.0
        )

        cognitive_immune = context.get(
            "cognitive_immune_report",
            {},
        )

        immune_state = cognitive_immune.get(
            "cognitive_immune_state",
            "immune_monitoring",
        )

        cognitive_immune_score = (
            0.0
            if immune_state == "immune_lockdown"
            else 0.35
            if immune_state == "family_merge_freeze"
            else 1.0
        )

        legitimacy_score = _clamp(
            novelty_report.get(
                "productive_novelty",
                0.0,
            )
            * 0.26
            +
            mutation_report.get(
                "constructive_signal",
                0.0,
            )
            * 0.24
            +
            mutation_report.get(
                "average_constructive_utility",
                0.0,
            )
            * 0.18
            +
            benefit_report.get(
                "causal_benefit_score",
                0.0,
            )
            * 0.28
            +
            selection_pressure
            * 0.04
            +
            landscape_score
            * 0.04
            +
            homeostasis_score
            * 0.03
            +
            natural_selection_score
            * 0.025
            +
            extinction_hygiene_score
            * 0.005
            +
            cooling_score
            * 0.005
            +
            recovery_review_score
            * 0.005
            +
            identity_guardian_score
            * 0.005
            +
            memory_pressure_score
            * 0.005
            +
            sandbox_score
            * 0.005
            +
            fusion_score
            * 0.005
            +
            stability_field_score
            * 0.005
            +
            identity_reasoning_score
            * 0.005
            +
            lineage_score
            * 0.005
            +
            recursive_safety_score
            * 0.005
            +
            cognitive_immune_score
            * 0.005
        )

        legitimacy_state = (
            "legitimate"
            if legitimacy_score >= 0.62
            else "conditionally_legitimate"
            if legitimacy_score >= 0.38
            else "unproven"
        )

        report = {
            "system":
            "semantic_legitimacy_engine",

            "novelty_scoring":
            novelty_report,

            "constructive_mutation_detection":
            mutation_report,

            "causal_benefit_estimator":
            benefit_report,

            "evolutionary_memory":
            evolutionary,

            "cognitive_ecology":
            ecology,

            "cognitive_homeostasis":
            homeostasis,

            "cognitive_natural_selection":
            natural_selection,

            "extinction_engine":
            extinction,

            "entropy_regulation":
            entropy_regulation,

            "trait_recovery":
            recovery,

            "identity_continuity_guardian":
            guardian,

            "memory_compression":
            memory_compression,

            "evolution_sandbox":
            sandbox,

            "concept_fusion":
            concept_fusion,

            "stability_field":
            stability_field,

            "identity_reasoner":
            identity_reasoner,

            "concept_lineage":
            concept_lineage,

            "recursive_guardian":
            recursive_guardian,

            "cognitive_immune":
            cognitive_immune,

            "semantic_legitimacy_score":
            legitimacy_score,

            "legitimacy_state":
            legitimacy_state,

            "legitimacy_policy":
            (
                "graduate_under_monitoring"
                if legitimacy_state == "legitimate"
                else "rehearse_then_probation"
                if legitimacy_state == "conditionally_legitimate"
                else "keep_in_shadow_rehearsal"
            ),

            "evidence_exports":
            {
                "semantic_attestation_score":
                legitimacy_score,

                "causal_attestation_score":
                benefit_report.get(
                    "causal_benefit_score",
                    0.0,
                ),

            "constructive_mutation_score":
            mutation_report.get(
                "constructive_signal",
                0.0,
            ),

            "constructive_value_score":
            mutation_report.get(
                "average_constructive_utility",
                0.0,
            ),

            "evolutionary_pressure_score":
            selection_pressure,

            "ecological_fitness_score":
            landscape_score,

            "homeostasis_score":
            homeostasis_score,

            "natural_selection_score":
            natural_selection_score,

            "extinction_hygiene_score":
            extinction_hygiene_score,

            "entropy_cooling_score":
            cooling_score,

            "recovery_review_score":
            recovery_review_score,

            "identity_guardian_score":
            identity_guardian_score,

            "semantic_anchor_score":
            semantic_anchor_score,

            "memory_pressure_score":
            memory_pressure_score,

            "evolution_sandbox_score":
            sandbox_score,

            "concept_fusion_score":
            fusion_score,

            "stability_field_score":
            stability_field_score,

            "identity_reasoning_score":
            identity_reasoning_score,

            "concept_lineage_score":
            lineage_score,

            "recursive_safety_score":
            recursive_safety_score,

            "cognitive_immune_score":
            cognitive_immune_score,
        },

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.legitimacy_history.append(
            report,
        )

        self.legitimacy_history = (
            self.legitimacy_history[-128:]
        )

        return report


semantic_legitimacy_engine = (
    SemanticLegitimacyEngine()
)
