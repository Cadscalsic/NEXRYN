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
        report_level = str(context.get("report_level", "full") or "full").lower()
        if report_level != "full":
            self.knowledge_maturity_report = self._compact_knowledge_maturity(
                ledger_report,
                context.get(
                    "truth_candidate_engine_report",
                    context.get("truth_candidate_report", {}),
                ),
                report_level=report_level,
            )
            return self.knowledge_maturity_report

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
                report_level=report_level,
            )
        )

        return self.knowledge_maturity_report

    def _compact_knowledge_maturity(
        self,
        ledger_report,
        truth_candidate_report=None,
        report_level="normal",
    ):
        ledger_report = ledger_report if isinstance(ledger_report, dict) else {}
        truth_candidate_report = (
            truth_candidate_report
            if isinstance(truth_candidate_report, dict)
            else {}
        )
        runtime_candidates = {
            str(item.get("concept")): item
            for item in truth_candidate_report.get("evaluations", [])
            if isinstance(item, dict) and item.get("concept")
        }
        concepts = []
        generated_contexts = []
        for item in ledger_report.get("concepts", []):
            if not isinstance(item, dict) or not item.get("concept"):
                continue
            concept = str(item.get("concept"))
            used_task_count = int(item.get("used_task_count", 0) or 0)
            support = float(
                item.get(
                    "cross_task_support",
                    item.get("independent_success_rate", 0.0),
                )
                or 0.0
            )
            contradiction = float(
                item.get("average_contradiction_score", 0.0) or 0.0
            )
            runtime = runtime_candidates.get(concept, {})
            eligible = bool(runtime.get("eligible_for_truth_candidate"))
            blocked = list(runtime.get("blocked_metrics", []))
            score = runtime.get("promotion_score")
            if score is None:
                score = round(
                    min(
                        1.0,
                        support * 0.72
                        + min(used_task_count / 32.0, 1.0) * 0.18
                        + max(0.0, 1.0 - contradiction) * 0.10,
                    ),
                    4,
                )
            if eligible:
                state = "TRUTH_CANDIDATE"
                next_stage = "ESTABLISHED_TRUTH"
                candidate_ready = True
            elif used_task_count >= 5 and support >= 0.80:
                state = "CANDIDATE"
                next_stage = "PROCESS_CONTEXT"
                candidate_ready = True
            elif used_task_count >= 3:
                state = "SUPPORTED"
                next_stage = "CANDIDATE"
                candidate_ready = False
            else:
                state = "DISCOVERING"
                next_stage = "SUPPORTED"
                candidate_ready = False
            eligible_for_context = state in {
                "CANDIDATE",
                "PROCESS_CONTEXT",
                "TRUTH_CANDIDATE",
            }
            eligible_for_truth_candidate = eligible
            thresholds = {
                "minimum_observations": 5,
                "minimum_confidence": 0.80,
                "maximum_contradiction_rate": 0.10,
                "minimum_promotion_score": 0.70,
            }
            epistemic_graduation = {
                "concept": concept,
                "graduation_stage": state,
                "current_stage": state,
                "next_stage": next_stage,
                "candidate_ready": candidate_ready,
                "promotion_score": score,
                "eligible_for_context": eligible_for_context,
                "eligible_for_truth_candidate":
                eligible_for_truth_candidate,
                "blocked_metrics": blocked,
                "thresholds": thresholds,
                "next_required_evidence": [{
                    "metric": "promotion_score",
                    "required": (
                        0.95
                        if state == "TRUTH_CANDIDATE"
                        else thresholds["minimum_promotion_score"]
                    ),
                }],
                "compact_graduation": True,
            }
            if eligible_for_context:
                generated_contexts.append({
                    "context_id": f"{concept}_process_context",
                    "context_name": concept,
                    "concept": concept,
                    "context_type": "PROCESS_CONTEXT",
                    "status": "PROCESS_CONTEXT_SUPPORTED",
                    "confidence": round(
                        min(1.0, max(float(score or 0.0), support)),
                        4,
                    ),
                    "context_strength": round(
                        min(1.0, max(float(score or 0.0), support)),
                        4,
                    ),
                    "transitions": [{
                        "from": state,
                        "to": next_stage,
                        "source": "compact_lifecycle_summary",
                    }],
                    "preconditions": [{
                        "metric": "candidate_ready",
                        "satisfied": candidate_ready,
                    }],
                    "outcomes": [{
                        "stage": next_stage,
                        "eligible_for_context": eligible_for_context,
                    }],
                    "expected_outcomes": [{
                        "stage": next_stage,
                        "eligible_for_context": eligible_for_context,
                    }],
                    "source": "compact_lifecycle_summary",
                    "report_compressed": True,
                })
            concept_report = {
                "concept": concept,
                "state": state,
                "used_task_count": used_task_count,
                "successful_task_count": sum(
                    record.get("success") is True
                    for record in item.get("records", [])
                    if isinstance(record, dict)
                ),
                "counterexample_task_count": sum(
                    record.get("success") is False
                    for record in item.get("records", [])
                    if isinstance(record, dict)
                ),
                "independent_success_rate":
                item.get("independent_success_rate", 0.0),
                "cross_task_support": support,
                "average_contradiction_score": round(contradiction, 4),
                "promotion_score": score,
                "promotion_stage": state,
                "candidate_ready": candidate_ready,
                "preliminary_truth_candidate_ready": candidate_ready,
                "eligible_for_context": eligible_for_context,
                "eligible_for_truth_candidate": eligible_for_truth_candidate,
                "blocked_metrics": blocked,
                "promotion_reason": (
                    "COMPACT_LIFECYCLE_SUMMARY: full lifecycle deferred"
                ),
                "epistemic_graduation": epistemic_graduation,
                "truth_candidate_promotion": {
                    "concept": concept,
                    "candidate_ready": candidate_ready,
                    "promotion_score": score,
                    "promotion_stage": state,
                    "eligible_for_context": eligible_for_context,
                    "eligible_for_truth_candidate":
                    eligible_for_truth_candidate,
                    "blocked_metrics": blocked,
                    "epistemic_graduation": epistemic_graduation,
                    "promotion_dependency_score":
                    runtime.get("promotion_dependency_score", 0.0),
                    "promotion_dependency_bonus":
                    runtime.get("promotion_dependency_bonus", 0.0),
                    "dependency_promotion_blockers": list(
                        runtime.get("dependency_promotion_blockers", [])
                    ),
                    "dependency_confidence":
                    runtime.get("dependency_confidence", 0.0),
                    "dependency_chain_depth":
                    runtime.get("dependency_chain_depth", 0),
                    "dependency_chain_coverage":
                    runtime.get("dependency_chain_coverage", 0.0),
                },
                "report_compressed": True,
            }
            concepts.append(concept_report)

        promotion_report = [
            {
                "concept": concept["concept"],
                "promotion_score": concept["promotion_score"],
                "current_stage": concept["state"],
                "next_stage": (
                    "ESTABLISHED_TRUTH"
                    if concept["state"] == "TRUTH_CANDIDATE"
                    else "PROCESS_CONTEXT"
                    if concept["state"] == "CANDIDATE"
                    else "CANDIDATE"
                    if concept["state"] == "SUPPORTED"
                    else "SUPPORTED"
                ),
                "candidate_ready": concept["candidate_ready"],
                "blocked_reason": (
                    ", ".join(concept["blocked_metrics"])
                    if concept["blocked_metrics"]
                    else None
                ),
            }
            for concept in concepts
        ]
        state_counts = {
            state: sum(concept["state"] == state for concept in concepts)
            for state in self.concept_maturity_tracker.STATES
        }
        return {
            "system": "concept_maturity_tracker",
            "states": list(self.concept_maturity_tracker.STATES),
            "concepts": concepts,
            "promotion_report": promotion_report,
            "context_registry_report": {},
            "generated_contexts": generated_contexts,
            "context_count": len(generated_contexts),
            "context_consumed": 0,
            "context_hits": 0,
            "context_injection_audit": {
                "compact_report": True,
                "concept_count": len(concepts),
                "generated_context_count": len(generated_contexts),
            },
            "recursive_context_audit": {
                "compact_report": True,
                "context_count": len(generated_contexts),
            },
            "knowledge_flow_report": {
                "compact_report": True,
                "knowledge_created": len(generated_contexts),
                "knowledge_consumed": 0,
            },
            "knowledge_reuse_report": {
                "knowledge_reuse_rate": 0.0,
                "strategy_hits": 0,
                "program_hits": 0,
            },
            "truth_reuse_report": {
                "truth_hits": 0,
                "truth_misses": len(concepts),
                "truth_reuse_rate": 0.0,
            },
            "strategy_hits": 0,
            "program_hits": 0,
            "truth_hits": 0,
            "knowledge_reuse_rate": 0.0,
            "truth_candidates": [
                concept
                for concept in concepts
                if concept.get("eligible_for_truth_candidate")
            ],
            "truth_candidate_count": sum(
                bool(concept.get("eligible_for_truth_candidate"))
                for concept in concepts
            ),
            "candidate_ready_lifecycle_invariant_preserved": all(
                concept["candidate_ready"]
                for concept in concepts
                if concept["state"] in {
                    "CANDIDATE",
                    "PROCESS_CONTEXT",
                    "TRUTH_CANDIDATE",
                    "ESTABLISHED_TRUTH",
                }
            ),
            "state_counts": state_counts,
            "closest_truth_candidate_concepts": [
                concept["concept"]
                for concept in concepts
                if concept["state"] in {
                    "CANDIDATE",
                    "PROCESS_CONTEXT",
                    "TRUTH_CANDIDATE",
                    "ESTABLISHED_TRUTH",
                }
            ],
            "count_alone_cannot_promote_truth": True,
            "report_level": "compact",
            "concept_lifecycle_compressed": True,
            "full_lifecycle_deferred": True,
            "deferred_reason": "report_level_not_full",
        }

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
