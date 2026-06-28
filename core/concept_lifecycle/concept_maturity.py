from core.knowledge.truth_state_authority import TruthStateAuthority
from core.truth.truth_candidate_engine import (
    TruthCandidatePromotionEngine,
)
from runtime.context.context_registry import ContextRegistry
from runtime.knowledge.epistemic_graduation_engine import (
    EpistemicGraduationEngine,
)


class ConceptMaturityTracker:
    DISCOVERY_ONLY_MODE = True
    TRUTH_CANDIDATE_MINIMUM_TASKS = 8
    TRUTH_CANDIDATE_MINIMUM_SUPPORT = 0.80
    TRUTH_CANDIDATE_MINIMUM_CAUSAL_ALIGNMENT = 0.80
    TRUTH_CANDIDATE_MAXIMUM_CONTRADICTION = 0.10

    STATES = [
        "DISCOVERING",
        "SUPPORTED",
        "CANDIDATE",
        "PROCESS_CONTEXT",
        "TRUTH_CANDIDATE",
        "ESTABLISHED_TRUTH",
    ]

    def __init__(
        self,
        supported_task_count=3,
        generalizing_task_count=5,
    ):
        self.supported_task_count = max(int(supported_task_count), 1)
        self.generalizing_task_count = max(
            int(generalizing_task_count),
            self.supported_task_count,
        )
        self._concepts = {}
        self.truth_state_authority = TruthStateAuthority()
        self.truth_candidate_promotion_engine = (
            TruthCandidatePromotionEngine()
        )
        self.epistemic_graduation_engine = EpistemicGraduationEngine()
        self.context_registry = ContextRegistry()

    def _concept_names(self, report, key, accepted_key=None):
        concepts = set()
        for item in report.get(key, []):
            if not isinstance(item, dict):
                continue
            if accepted_key and item.get(accepted_key) is not True:
                continue
            concept = item.get("concept")
            if concept:
                concepts.add(str(concept))
        return concepts

    def _stable_truths(self, truth_registry):
        return self.truth_state_authority.stable_truth_concepts(
            truth_registry,
        )

    def _lock_candidate_ready(self, promotion, reason):
        readiness_gates = {
            gate: True
            for gate in promotion.get("readiness_gates", {})
        }
        return {
            **promotion,
            "decision": reason,
            "candidate_ready": True,
            "readiness_gates": readiness_gates,
            "failed_gates": [],
            "candidate_ready_lock_reason": reason,
            "raw_readiness_gates_before_lifecycle_lock":
            promotion.get("readiness_gates", {}),
            "raw_failed_gates_before_lifecycle_lock":
            promotion.get("failed_gates", []),
        }

    def _hold_in_discovery(self, promotion):
        readiness_gates = {
            gate: False
            for gate in promotion.get("readiness_gates", {})
        }
        return {
            **promotion,
            "decision": "REMAIN_DISCOVERING",
            "candidate_ready": False,
            "readiness_gates": readiness_gates,
            "failed_gates": list(readiness_gates),
            "candidate_ready_lock_reason": None,
            "discovery_only_mode": True,
        }

    def _context_candidate_ready(
        self,
        ledger_item,
        promotion,
        mixed_outcomes,
    ):
        if mixed_outcomes:
            return False
        observed_task_count = int(ledger_item.get("used_task_count", 0) or 0)
        cross_task_support = float(
            ledger_item.get(
                "cross_task_support",
                ledger_item.get("independent_success_rate", 0.0),
            )
            or 0.0
        )
        dependency_ready = (
            promotion.get("dependency_chain_complete_for_promotion") is True
            and float(promotion.get("promotion_dependency_score", 0.0) or 0.0)
            >= 0.86
            and float(promotion.get("dependency_confidence", 0.0) or 0.0)
            >= 0.85
            and float(promotion.get("dependency_chain_coverage", 0.0) or 0.0)
            >= 0.85
        )
        return bool(
            observed_task_count >= 32
            and cross_task_support >= self.TRUTH_CANDIDATE_MINIMUM_SUPPORT
            and dependency_ready
        )

    def _mark_context_candidate(self, promotion):
        readiness_gates = dict(promotion.get("readiness_gates", {}))
        failed_gates = [
            gate
            for gate, passed in readiness_gates.items()
            if not passed
        ]
        return {
            **promotion,
            "decision": "PROMOTE_TO_CONTEXT_CANDIDATE",
            "candidate_ready": False,
            "context_candidate_ready": True,
            "context_candidate_reason":
            "mature_dependency_backed_concept_needs_context_generation",
            "failed_gates": failed_gates,
            "truth_candidate_blocked_until_context_registered": (
                "context_strength" in failed_gates
                or "process_context_ready" in failed_gates
            ),
            "discovery_only_mode": self.DISCOVERY_ONLY_MODE,
        }

    def _graduation_inputs(
        self,
        item,
        promotion,
        used_task_count,
        average_contradiction_score,
    ):
        confidence = max(
            float(item.get("independent_success_rate", 0.0) or 0.0),
            float(item.get("cross_task_support", 0.0) or 0.0),
        )
        dependency_confidence = max(
            float(promotion.get("dependency_confidence", 0.0) or 0.0),
            float(promotion.get("promotion_dependency_score", 0.0) or 0.0),
        )
        causal_support = max(
            float(promotion.get("causal_stability", 0.0) or 0.0),
            dependency_confidence,
        )
        return {
            "observations": used_task_count,
            "confidence": confidence,
            "dependency_confidence": dependency_confidence,
            "contradiction_rate": average_contradiction_score,
            "cross_task_stability": float(
                item.get("cross_task_support", confidence) or 0.0
            ),
            "causal_support": causal_support,
            "context_support": max(
                float(promotion.get("context_strength", 0.0) or 0.0),
                float(promotion.get("context_surface_score", 0.0) or 0.0),
            ),
            "cross_task_validation_passed": bool(
                used_task_count >= self.TRUTH_CANDIDATE_MINIMUM_TASKS
                and confidence >= self.TRUTH_CANDIDATE_MINIMUM_SUPPORT
                and average_contradiction_score
                <= self.TRUTH_CANDIDATE_MAXIMUM_CONTRADICTION
            ),
        }

    def _average_contradiction_score(self, item, records):
        for key in (
            "average_contradiction_score",
            "ledger_average_contradiction_score",
            "contradiction_score",
        ):
            if item.get(key) is not None:
                return float(item.get(key) or 0.0)
        if not records:
            return 0.0
        return (
            sum(
                record.get(
                    "contradiction_score",
                    1.0 if record.get("success") is False else 0.0,
                )
                for record in records
            )
            / len(records)
        )

    def _context_artifacts(self, concept, graduation, promotion):
        if not graduation["eligible_for_context"]:
            return {
                "generated": False,
                "contexts": [],
                "registration_report": self.context_registry.report(),
            }

        score = graduation["promotion_score"]
        dependency_graph = promotion.get("reasoned_dependency_chain", {})
        process_context = {
            "context_id": f"process_context:{concept}",
            "context_name": f"{concept}_process_context",
            "context_type": "PROCESS_CONTEXT",
            "concept": concept,
            "confidence": score,
            "context_confidence": score,
            "source": "epistemic_graduation_engine",
            "promotion_stage": graduation["promotion_stage"],
            "process_context_generated": True,
            "preconditions": ["concept_observed_across_tasks"],
            "transitions": ["dependency_supported_behavior"],
            "expected_outcomes": ["reusable_process_explanation"],
        }
        semantic_context = {
            "context_id": f"semantic_context:{concept}",
            "context_name": f"{concept}_semantic_context",
            "context_type": "SEMANTIC_CONTEXT",
            "concept": concept,
            "confidence": score,
            "source": "epistemic_graduation_engine",
            "semantic_definition":
            f"{concept} supported by promoted cross-task evidence",
            "properties": [
                "evidence_backed",
                "dependency_explainable",
                "context_eligible",
            ],
        }
        dependency_surface = {
            "context_id": f"dependency_surface:{concept}",
            "context_name": f"{concept}_dependency_surface",
            "context_type": "DEPENDENCY_SURFACE",
            "concept": concept,
            "confidence": max(
                score,
                float(promotion.get("promotion_dependency_score", 0.0) or 0.0),
            ),
            "source": "epistemic_graduation_engine",
            "dependency_confidence": promotion.get("dependency_confidence", 0.0),
            "dependency_chain_depth": promotion.get("dependency_chain_depth", 0),
            "dependency_chain_coverage":
            promotion.get("dependency_chain_coverage", 0.0),
            "dependency_graph": dependency_graph,
        }
        contexts = [process_context, semantic_context, dependency_surface]
        registration = self.context_registry.register_batch(
            contexts,
            source="epistemic_graduation_engine",
        )
        return {
            "generated": True,
            "contexts": contexts,
            "process_context": process_context,
            "semantic_context": semantic_context,
            "dependency_surface": dependency_surface,
            "registration_report": registration,
        }

    def _truth_artifacts(self, concept, graduation, promotion, contexts):
        if not graduation["eligible_for_truth_candidate"]:
            return {
                "generated": False,
                "truth_candidate": None,
                "truth_evidence_summary": {},
                "truth_dependency_graph": {},
                "truth_validation_request": {},
            }

        evidence_summary = {
            "concept": concept,
            "promotion_score": graduation["promotion_score"],
            "promotion_stage": graduation["promotion_stage"],
            "component_scores": graduation["component_scores"],
            "blocked_metrics": graduation["blocked_metrics"],
            "dependency_confidence": promotion.get("dependency_confidence", 0.0),
            "promotion_dependency_bonus":
            promotion.get("promotion_dependency_bonus", 0.0),
            "context_count": len(contexts.get("contexts", [])),
        }
        dependency_graph = {
            "concept": concept,
            "dependency_chain_depth": promotion.get("dependency_chain_depth", 0),
            "dependency_chain_coverage":
            promotion.get("dependency_chain_coverage", 0.0),
            "dependency_confidence": promotion.get("dependency_confidence", 0.0),
            "reasoned_dependency_chain":
            promotion.get("reasoned_dependency_chain", {}),
            "missing_dependencies": promotion.get("missing_dependencies", []),
        }
        truth_candidate = {
            "type": "TRUTH_CANDIDATE_OBJECT",
            "concept": concept,
            "promotion_score": graduation["promotion_score"],
            "promotion_stage": graduation["promotion_stage"],
            "candidate_ready": True,
            "evidence_summary": evidence_summary,
            "dependency_graph": dependency_graph,
            "automatic_truth_commit_forbidden": True,
        }
        validation_request = {
            "type": "TRUTH_VALIDATION_REQUEST",
            "concept": concept,
            "requested_review": "identity_safe_truth_validation",
            "required_checks": [
                "identity_continuity",
                "contradiction_review",
                "cross_task_revalidation",
                "dependency_graph_review",
            ],
            "promotion_score": graduation["promotion_score"],
        }
        return {
            "generated": True,
            "truth_candidate": truth_candidate,
            "truth_evidence_summary": evidence_summary,
            "truth_dependency_graph": dependency_graph,
            "truth_validation_request": validation_request,
        }

    def _promotion_report_item(self, concept, graduation):
        return {
            "concept": concept,
            "promotion_score": graduation["promotion_score"],
            "current_stage": graduation["promotion_stage"],
            "next_stage": graduation["next_stage"],
            "candidate_ready": graduation["candidate_ready"],
            "blocked_reason": (
                ", ".join(graduation["blocked_metrics"])
                if graduation["blocked_metrics"]
                else None
            ),
        }

    def evaluate(
        self,
        ledger_report=None,
        truth_candidate_report=None,
        truth_registry=None,
    ):
        ledger_report = ledger_report or {}
        truth_candidate_report = truth_candidate_report or {}
        truth_registry = truth_registry or {}
        candidate_concepts = self._concept_names(
            truth_candidate_report,
            "evaluations",
            "eligible_for_truth_candidate",
        )
        stable_truths = self._stable_truths(truth_registry)

        concepts = []
        for item in ledger_report.get("concepts", []):
            concept = str(item.get("concept", ""))
            if not concept:
                continue
            records = list(item.get("records", []))
            successful_tasks = sum(
                record.get("success") is True
                for record in records
            )
            counterexample_tasks = sum(
                record.get("success") is False
                for record in records
            )
            used_task_count = int(item.get("used_task_count", 0))
            mixed_outcomes = bool(successful_tasks and counterexample_tasks)
            average_causal_alignment = (
                sum(
                    record.get("causal_alignment", 0.0)
                    for record in records
                )
                / len(records)
                if records
                else 0.0
            )
            average_contradiction_score = self._average_contradiction_score(
                item,
                records,
            )
            cross_task_support = item.get("cross_task_support", 0.0)
            runtime_candidate_report = {
                **truth_candidate_report,
                "evaluations": [
                    evaluation
                    for evaluation in truth_candidate_report.get(
                        "evaluations",
                        [],
                    )
                    if (
                        isinstance(evaluation, dict)
                        and str(evaluation.get("concept")) == concept
                    )
                ],
            }

            promotion = self.truth_candidate_promotion_engine.evaluate(
                item,
                runtime_candidate_report,
            )
            graduation = self.epistemic_graduation_engine.evaluate(
                **self._graduation_inputs(
                    item,
                    promotion,
                    used_task_count,
                    average_contradiction_score,
                )
            )
            if concept in stable_truths:
                graduation = {
                    **graduation,
                    "graduation_stage": "ESTABLISHED_TRUTH",
                    "promotion_stage": "ESTABLISHED_TRUTH",
                    "current_stage": "ESTABLISHED_TRUTH",
                    "next_stage": None,
                    "candidate_ready": True,
                    "eligible_for_context": True,
                    "eligible_for_truth_candidate": True,
                    "eligible_for_established_truth": True,
                    "promotion_reason": "ESTABLISHED_TRUTH: truth registry authority confirmed",
                    "graduation_reason": "ESTABLISHED_TRUTH: truth registry authority confirmed",
                }
                promotion = self._lock_candidate_ready(
                    promotion,
                    "ESTABLISHED_TRUTH_CANDIDATE_LOCKED",
                )
            elif concept in candidate_concepts:
                graduation = {
                    **graduation,
                    "graduation_stage": max(
                        graduation["graduation_stage"],
                        "TRUTH_CANDIDATE",
                        key=self.STATES.index,
                    ),
                    "promotion_stage": "TRUTH_CANDIDATE",
                    "current_stage": "TRUTH_CANDIDATE",
                    "next_stage": "ESTABLISHED_TRUTH",
                    "candidate_ready": True,
                    "eligible_for_context": True,
                    "eligible_for_truth_candidate": True,
                    "promotion_reason": "TRUTH_CANDIDATE: runtime truth candidate authority confirmed",
                    "graduation_reason": "TRUTH_CANDIDATE: runtime truth candidate authority confirmed",
                }
                promotion = self._lock_candidate_ready(
                    promotion,
                    "RUNTIME_TRUTH_CANDIDATE_READY",
                )
            elif (
                promotion.get("candidate_ready") is True
                and promotion.get("dependency_chain_complete_for_promotion") is True
                and promotion.get("readiness_gates", {}).get(
                    "process_context_ready",
                    True,
                ) is True
                and used_task_count >= self.TRUTH_CANDIDATE_MINIMUM_TASKS
            ):
                graduation = {
                    **graduation,
                    "graduation_stage": "TRUTH_CANDIDATE",
                    "promotion_stage": "TRUTH_CANDIDATE",
                    "current_stage": "TRUTH_CANDIDATE",
                    "next_stage": "ESTABLISHED_TRUTH",
                    "candidate_ready": True,
                    "eligible_for_context": True,
                    "eligible_for_truth_candidate": True,
                    "promotion_reason":
                    "TRUTH_CANDIDATE: dependency-synchronized gates satisfied",
                    "graduation_reason":
                    "TRUTH_CANDIDATE: dependency-synchronized gates satisfied",
                }
                promotion = self._lock_candidate_ready(
                    promotion,
                    "DEPENDENCY_SYNCHRONIZED_TRUTH_CANDIDATE_READY",
                )
            state = graduation["promotion_stage"]
            context_artifacts = self._context_artifacts(
                concept,
                graduation,
                promotion,
            )
            truth_artifacts = self._truth_artifacts(
                concept,
                graduation,
                promotion,
                context_artifacts,
            )
            promotion = {
                **promotion,
                "promotion_score": graduation["promotion_score"],
                "promotion_stage": graduation["promotion_stage"],
                "candidate_ready": graduation["candidate_ready"],
                "eligible_for_context": graduation["eligible_for_context"],
                "eligible_for_truth_candidate":
                graduation["eligible_for_truth_candidate"],
                "blocked_metrics": graduation["blocked_metrics"],
                "promotion_reason": graduation["promotion_reason"],
                "promotion_dependency_bonus":
                promotion.get("promotion_dependency_bonus", 0.0),
                "epistemic_graduation": graduation,
                "process_context_generated": context_artifacts["generated"],
                "truth_candidate_generated": truth_artifacts["generated"],
            }
            readiness_gates = {
                "independent_task_coverage": promotion[
                    "readiness_gates"
                ]["observed_task_count"],
                "cross_task_support": promotion["readiness_gates"][
                    "cross_task_support"
                ],
                "causal_alignment": promotion["readiness_gates"][
                    "causal_stability"
                ],
                "contradiction_score": promotion["readiness_gates"][
                    "contradiction_governance"
                ],
                "context_strength": promotion["readiness_gates"][
                    "context_strength"
                ],
                "identity_strength": promotion["readiness_gates"][
                    "identity_strength"
                ],
            }

            maturity = {
                "concept": concept,
                "state": state,
                "used_task_count": used_task_count,
                "task_ids": list(item.get("used_task_ids", [])),
                "successful_task_count": successful_tasks,
                "counterexample_task_count": counterexample_tasks,
                "mixed_outcomes_detected": mixed_outcomes,
                "independent_success_rate":
                item.get("independent_success_rate", 0.0),
                "cross_task_support": item.get("cross_task_support", 0.0),
                "average_causal_alignment":
                round(average_causal_alignment, 4),
                "average_contradiction_score":
                round(average_contradiction_score, 4),
                "truth_candidate_readiness_gates": readiness_gates,
                "preliminary_truth_candidate_ready":
                promotion["candidate_ready"],
                "promotion_score": graduation["promotion_score"],
                "promotion_stage": graduation["promotion_stage"],
                "candidate_ready": graduation["candidate_ready"],
                "eligible_for_context": graduation["eligible_for_context"],
                "eligible_for_truth_candidate":
                graduation["eligible_for_truth_candidate"],
                "blocked_metrics": graduation["blocked_metrics"],
                "promotion_reason": graduation["promotion_reason"],
                "promotion_dependency_bonus":
                promotion.get("promotion_dependency_bonus", 0.0),
                "epistemic_graduation": graduation,
                "process_context": context_artifacts.get("process_context", {}),
                "semantic_context": context_artifacts.get("semantic_context", {}),
                "dependency_surface":
                context_artifacts.get("dependency_surface", {}),
                "context_artifacts": context_artifacts,
                "truth_candidate_object":
                truth_artifacts.get("truth_candidate"),
                "truth_evidence_summary":
                truth_artifacts.get("truth_evidence_summary", {}),
                "truth_dependency_graph":
                truth_artifacts.get("truth_dependency_graph", {}),
                "truth_validation_request":
                truth_artifacts.get("truth_validation_request", {}),
                "truth_candidate_promotion": promotion,
                "truth_candidate_requires_epistemic_gates": True,
                "stable_truth_requires_truth_registry_commitment": True,
            }
            self._concepts[concept] = maturity
            concepts.append(maturity)

        promotion_report = [
            self._promotion_report_item(
                concept["concept"],
                concept["epistemic_graduation"],
            )
            for concept in concepts
        ]
        generated_contexts = [
            context
            for concept in concepts
            for context in concept.get("context_artifacts", {}).get(
                "contexts",
                [],
            )
        ]
        generated_truth_candidates = [
            concept["truth_candidate_object"]
            for concept in concepts
            if concept.get("truth_candidate_object")
        ]

        return {
            "system": "concept_maturity_tracker",
            "states": list(self.STATES),
            "concepts": concepts,
            "promotion_report": promotion_report,
            "promotion_report_text": _format_promotion_report(
                promotion_report,
            ),
            "context_registry_report": self.context_registry.report(),
            "generated_contexts": generated_contexts,
            "context_count": len(generated_contexts),
            "truth_candidates": generated_truth_candidates,
            "truth_candidate_count": len(generated_truth_candidates),
            "candidate_ready_definition":
            "CANDIDATE_OR_HIGHER_IMPLIES_CANDIDATE_READY",
            "candidate_ready_lifecycle_invariant_preserved": all(
                concept["preliminary_truth_candidate_ready"]
                for concept in concepts
                if concept["state"] in {
                    "CANDIDATE",
                    "PROCESS_CONTEXT",
                    "TRUTH_CANDIDATE",
                    "ESTABLISHED_TRUTH",
                }
            ),
            "state_counts": {
                state: sum(
                    concept["state"] == state
                    for concept in concepts
                )
                for state in self.STATES
            },
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
        }


__all__ = [
    "ConceptMaturityTracker",
]


def _format_promotion_report(items):
    lines = ["PROMOTION REPORT"]
    for item in items:
        lines.append(
            "concept={concept} promotion_score={promotion_score} "
            "current_stage={current_stage} next_stage={next_stage} "
            "candidate_ready={candidate_ready} blocked_reason={blocked_reason}"
            .format(**item)
        )
    return "\n".join(lines)
