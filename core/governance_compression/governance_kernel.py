# ============================================
# NEXRYN UNIFIED GOVERNANCE KERNEL
# ============================================

from datetime import datetime

from core.epistemic_decision_engine import EpistemicDecisionEngine

from core.governance_compression.epistemic_constitution import (
    EpistemicConstitution,
)

from core.governance_compression.identity_core_lock import (
    IdentityCoreLock,
)

from core.governance_compression.runtime_energy_budget import (
    RuntimeEnergyBudget,
)

from core.governance_compression.semantic_compression_engine import (
    SemanticCompressionEngine,
)


class GovernanceKernel:

    def __init__(self):

        self.semantic_compression_engine = SemanticCompressionEngine()
        self.runtime_energy_budget = RuntimeEnergyBudget()
        self.identity_core_lock = IdentityCoreLock()
        self.epistemic_constitution = EpistemicConstitution()
        self.epistemic_decision_engine = EpistemicDecisionEngine()
        self.kernel_history = []

    def build_signals(
        self,
        context,
        semantic_report,
        identity_lock_report,
        epistemic_report,
        cognition_report,
    ):

        immune = context.get(
            "cognitive_immune_system_v2_report",
            {},
        )

        kernel = context.get(
            "cognitive_kernel_report",
            {},
        )

        signals = []

        if immune.get(
            "immune_state",
        ) == "emergency_response":

            signals.append({
                "signal":
                "immune_emergency",

                "priority":
                "critical",
            })

        if kernel.get(
            "active_mode",
        ) == "stabilization_mode":

            signals.append({
                "signal":
                "kernel_stabilization",

                "priority":
                "high",
            })

        if semantic_report.get(
            "encoded_count",
            0,
        ):

            signals.append({
                "signal":
                "semantic_factorization_available",

                "priority":
                "medium",
            })

        if identity_lock_report.get(
            "decision",
        ) == "blocked":

            signals.append({
                "signal":
                "identity_invariant_rewrite_blocked",

                "priority":
                "critical",
            })

        judiciary = epistemic_report.get(
            "epistemic_legitimacy_engine",
            {},
        )

        if judiciary.get(
            "decision",
        ) != "epistemically_legitimate":

            signals.append({
                "signal":
                "epistemic_trial_required",

                "priority":
                "critical",
            })

        if any(
            evaluation.get("truth_commit", {}).get("committed")
            for evaluation in cognition_report.get("evaluations", [])
        ):

            signals.append({
                "signal":
                "constitutional_truth_committed",

                "priority":
                "high",
            })

        drift_regulation = cognition_report.get(
            "epistemic_drift_regulation",
            {},
        )

        if drift_regulation.get(
            "regulation_mode",
        ) == "semantic_containment":

            signals.append({
                "signal":
                "semantic_drift_epistemic_containment",

                "priority":
                "critical",
            })

        promotion = cognition_report.get(
            "epistemic_promotion_engine",
            {},
        )

        if promotion.get(
            "candidate_count",
            0,
        ) > promotion.get(
            "promotion_count",
            0,
        ):

            signals.append({
                "signal":
                "trait_candidates_awaiting_epistemic_promotion",

                "priority":
                "medium",
            })

        ontology = epistemic_report.get(
            "ontological_growth_constitution",
            {},
        )

        if ontology.get(
            "freeze_new_fusions",
            False,
        ):

            signals.append({
                "signal":
                "ontological_growth_freeze",

                "priority":
                "high",
            })

        physician = context.get(
            "cognitive_physician_report",
            {},
        )

        diagnosis = physician.get(
            "diagnosis_report",
            {},
        )

        if diagnosis.get(
            "risk_escalation",
        ) in [
            "elevated",
            "critical",
        ]:

            signals.append({
                "signal":
                "cognitive_physician_review_required",

                "priority":
                (
                    "critical"
                    if diagnosis.get(
                        "risk_escalation",
                    )
                    == "critical"
                    else "high"
                ),
            })

        return signals

    def build_policies(
        self,
        context,
        energy_report,
        identity_lock_report,
        epistemic_report,
        cognition_report,
    ):

        policies = [
            "single_governance_kernel",
            "no_layer_proliferation",
            "legacy_governance_as_modules_only",
        ]

        if energy_report.get(
            "budget_state",
        ) == "governance_over_budget":

            policies.append(
                "collapse_optional_governance_modules",
            )

        if context.get(
            "freeze_new_fusions",
            False,
        ):

            policies.append(
                "freeze_new_fusions",
            )

        if identity_lock_report.get(
            "decision",
        ) == "blocked":

            policies.append(
                "identity_core_lock_enforced",
            )

        policies.append(
            "immutable_core_invariants",
        )

        policies.append(
            "truth_precedes_survival_claims",
        )

        policies.extend([
            "truth_requires_evidence",
            "truth_requires_trials",
            "truth_requires_validation",
            "confidence_is_not_truth",
            "high_reputation_is_not_truth",
            "route_trait_candidates_through_epistemic_promotion",
            "qualified_epistemic_trial_precedes_trait_extinction",
            "trait_survival_is_not_belief",
            "belief_promotion_requires_repeated_validated_trials",
            "truth_commit_requires_truth_candidate_state",
            "evidence_reinforcement_increases_reliability_not_truth",
            "block_truth_commit_during_fragile_semantic_spine",
        ])

        if any(
            evaluation.get("truth_commit", {}).get("committed")
            for evaluation in cognition_report.get("evaluations", [])
        ):

            policies.append(
                "protect_constitutional_truth_commitments",
            )

        drift_regulation = cognition_report.get(
            "epistemic_drift_regulation",
            {},
        )

        if drift_regulation.get(
            "regulation_mode",
        ) == "semantic_containment":

            policies.extend([
                "freeze_weak_belief_birth",
                "archive_weak_probationary_beliefs",
                "block_truth_commit_during_critical_semantic_drift",
                "prioritize_semantic_anchor_recovery",
            ])

        elif drift_regulation.get(
            "regulation_mode",
        ) == "restricted_belief_formation":

            policies.append(
                "cap_new_belief_birth_under_semantic_strain",
            )

        judiciary = epistemic_report.get(
            "epistemic_legitimacy_engine",
            {},
        )

        if judiciary.get(
            "decision",
        ) != "epistemically_legitimate":

            policies.append(
                "require_epistemic_trial_before_truth_commit",
            )

        ontology = epistemic_report.get(
            "ontological_growth_constitution",
            {},
        )

        if ontology.get(
            "freeze_new_fusions",
            False,
        ):

            policies.append(
                "ontological_growth_law_freeze",
            )

        physician = context.get(
            "cognitive_physician_report",
            {},
        )

        if physician.get(
            "diagnosis_report",
            {},
        ).get(
            "risk_escalation",
        ) in [
            "elevated",
            "critical",
        ]:

            policies.append(
                "physician_recommendations_require_governance_review",
            )

        dna = context.get(
            "cognitive_dna_report",
            {},
        )

        if dna:

            policies.append(
                "constitutional_dna_informs_governance_without_authoritarian_control",
            )

            if dna.get(
                "trait_reputation_system",
                {},
            ).get(
                "reputation_state",
            ) == "genome_rehabilitation_required":

                policies.append(
                    "trait_rehabilitation_before_behavioral_inheritance",
                )

        return policies

    def physician_review(self, context):

        physician = context.get(
            "cognitive_physician_report",
            {},
        )

        if not physician:

            return {
                "status":
                "no_physician_submission",
            }

        ethics = physician.get(
            "constitutional_safety_assessment",
            {},
        )

        diagnosis = physician.get(
            "diagnosis_report",
            {},
        )

        approved_for_controlled_execution = (
            ethics.get(
                "ethics_state",
            )
            == "constitutionally_safe"
            and physician.get(
                "governance_submission",
                {},
            ).get(
                "physician_can_bypass_governance",
                True,
            )
            is False
        )

        return {
            "system":
            "governance_physician_review",

            "physician_authority":
            "advisor_only",

            "governance_kernel_final_authority":
            True,

            "diagnosis_state":
            diagnosis.get(
                "state",
                "unknown",
            ),

            "risk_escalation":
            diagnosis.get(
                "risk_escalation",
                "unknown",
            ),

            "approved_for_controlled_execution":
            approved_for_controlled_execution,

            "review_policy":
            (
                "controlled_runtime_execution_allowed"
                if approved_for_controlled_execution
                else "recommendations_restricted"
            ),
        }

    def compatibility_reports(self, kernel_report):

        module_stub = {
            "status":
            "compressed_into_governance_kernel",

            "kernel":
            "governance_kernel",
        }

        return {
            "constitutional_runtime_report":
            dict(
                module_stub,
                module="constitutional_runtime",
            ),

            "semantic_court_report":
            dict(
                module_stub,
                module="semantic_court",
            ),

            "cognitive_immune_engine_report":
            dict(
                module_stub,
                module="cognitive_immune_engine",
            ),

            "adaptive_permissioning_report":
            dict(
                module_stub,
                module="adaptive_permissioning",
            ),

            "meta_constitution_report":
            dict(
                module_stub,
                module="meta_constitution",
            ),

            "civilization_report":
            {
                "status":
                "compressed_into_governance_kernel",

                "civilization_state":
                "governance_kernel_managed",

                "kernel_policies":
                kernel_report.get(
                    "policies",
                    [],
                ),
            },
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        semantic_report = (
            self.semantic_compression_engine
            .run_cycle(context)
        )

        identity_lock_report = (
            self.identity_core_lock
            .evaluate(context)
        )

        epistemic_constitution_report = (
            self.epistemic_constitution
            .run_cycle(context)
        )

        epistemic_cognition_report = context.get(
            "epistemic_cognition_report",
        )

        if not epistemic_cognition_report:

            epistemic_cognition_report = (
                self.epistemic_decision_engine
                .run_cycle(context)
            )

        active_modules = [
            "governance_kernel",
            "epistemic_constitution",
            "epistemic_cognition_layer",
            "cognitive_physician",
            "semantic_compression",
            "cognitive_kernel",
            "semantic_os",
            "concept_lifecycle",
            "cognitive_physics",
            "legacy_governance_aliases",
        ]

        energy_report = (
            self.runtime_energy_budget
            .allocate(
                context,
                active_modules,
            )
        )

        physician_review_report = self.physician_review(
            context,
        )

        signals = self.build_signals(
            context,
            semantic_report,
            identity_lock_report,
            epistemic_constitution_report,
            epistemic_cognition_report,
        )

        report = {
            "system":
            "governance_kernel",

            "modules":
            active_modules,

            "policies":
            self.build_policies(
                context,
                energy_report,
                identity_lock_report,
                epistemic_constitution_report,
                epistemic_cognition_report,
            ),

            "signals":
            signals,

            "semantic_compression":
            semantic_report,

            "runtime_energy_budget":
            energy_report,

            "identity_core_lock":
            identity_lock_report,

            "epistemic_constitution":
            epistemic_constitution_report,

            "epistemic_cognition_layer":
            epistemic_cognition_report,

            "physician_review":
            physician_review_report,

            "cognitive_dna_review":
            {
                "status":
                (
                    "dna_report_received"
                    if context.get(
                        "cognitive_dna_report",
                    )
                    else "no_dna_report"
                ),

                "authority":
                "governance_kernel_final_authority",

                "dna_can_override_constitution":
                False,
            },

            "kernel_state":
            (
                "compressed_governance"
                if energy_report.get(
                    "budget_state",
                )
                == "within_budget"
                else "governance_budget_guarded"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        report[
            "compatibility_reports"
        ] = self.compatibility_reports(
            report,
        )

        self.kernel_history.append(
            report,
        )

        self.kernel_history = (
            self.kernel_history[-64:]
        )

        return report


governance_kernel = (
    GovernanceKernel()
)
