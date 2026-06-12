from core.context import ContextualTruthAuthorityEngine
from core.epistemic_models import BeliefState, clamp
from core.knowledge.adaptive_contradiction_governance import (
    AdaptiveContradictionGovernance,
)
from core.knowledge.contradiction_review_policy import (
    SOFT_REVIEW_ZONE,
    classify_contradiction_review,
)
from core.knowledge.contextual_truth_support_policy import (
    ContextualTruthSupportPolicy,
)
from core.knowledge.truth_state_authority import TruthStateAuthority
from runtime.causal import RuntimeCausalAlignmentEngine


class TruthCandidateEngine:
    MINIMUM_INDEPENDENT_TASKS = 8
    CONTRADICTION_REVIEW_ZONE = SOFT_REVIEW_ZONE
    CONTEXTUAL_TRUTH_SUPPORT_THRESHOLD = (
        ContextualTruthSupportPolicy.SUPPORT_THRESHOLD
    )
    CONTEXTUAL_TRUTH_SUPPORT_GRACE = (
        ContextualTruthSupportPolicy.SUPPORT_GRACE
    )

    METRICS = [
        {
            "name": "evidence_strength",
            "comparator": ">=",
            "threshold": 0.80,
            "action": "collect_execution_validation_evidence",
        },
        {
            "name": "confidence",
            "comparator": ">=",
            "threshold": 0.85,
            "action": "reinforce_reliable_independent_evidence",
        },
        {
            "name": "contradiction_score",
            "comparator": "<",
            "threshold": 0.10,
            "action": "resolve_or_explain_contradictory_evidence",
        },
        {
            "name": "causal_alignment",
            "comparator": ">=",
            "threshold": 0.80,
            "action": "collect_causal_attestation_evidence",
        },
        {
            "name": "causal_graph_alignment",
            "comparator": ">=",
            "threshold": 0.80,
            "action": "construct_explicit_causal_explanation_graph",
        },
        {
            "name": "causal_validation_score",
            "comparator": ">=",
            "threshold": 0.75,
            "action": "validate_causal_hypothesis_before_truth_promotion",
        },
        {
            "name": "contextual_truth_score",
            "comparator": ">=",
            "threshold": CONTEXTUAL_TRUTH_SUPPORT_THRESHOLD,
            "action": "specialize_truth_context_before_promotion",
        },
        {
            "name": "context_hierarchy_score",
            "comparator": ">=",
            "threshold": 0.75,
            "action": "differentiate_context_hierarchy_before_promotion",
        },
    ]
    PROCESS_CONCEPTS = {
        "growth",
        "propagation",
        "replication",
        "topological_growth",
        "directional_motion",
        "object_identity_preservation",
    }

    def __init__(self):
        self.truth_state_authority = TruthStateAuthority()
        self.runtime_causal_alignment_engine = (
            RuntimeCausalAlignmentEngine()
        )
        self.contextual_truth_authority_engine = (
            ContextualTruthAuthorityEngine()
        )
        self.adaptive_contradiction_governance = (
            AdaptiveContradictionGovernance()
        )
        self.contextual_truth_support_policy = (
            ContextualTruthSupportPolicy()
        )

    def _nested_score(self, report, keys, default=0.0):
        report = report if isinstance(report, dict) else {}
        for key in keys:
            value = report.get(key)
            if value is not None:
                return clamp(value)
        return clamp(default)

    def _context_hierarchy_report(self, context):
        report = context.get("context_hierarchy", {})
        report = dict(report) if isinstance(report, dict) else {}
        score = self._nested_score(
            report,
            ["context_hierarchy_score", "score", "confidence"],
            0.0,
        )
        if score == 0.0 and report.get("contexts"):
            contexts = [
                item
                for item in report.get("contexts", [])
                if isinstance(item, dict)
            ]
            if contexts:
                score = clamp(
                    sum(
                        item.get(
                            "stability",
                            item.get("confidence", 0.0),
                        )
                        for item in contexts
                    )
                    / len(contexts)
                )
        if "context_hierarchy_score" not in report:
            report["context_hierarchy_score"] = score
        if "hierarchy_ready" not in report and score:
            report["hierarchy_ready"] = score >= 0.75
        return report

    def _semantic_context_report(self, context):
        report = context.get("semantic_context", {})
        report = dict(report) if isinstance(report, dict) else {}
        score = self._nested_score(
            report,
            ["semantic_context_score", "confidence", "score"],
            0.0,
        )
        if "semantic_context_score" not in report:
            report["semantic_context_score"] = score
        return report

    def _contextual_truth_report(self, context):
        report = context.get("contextual_truth", {})
        return dict(report) if isinstance(report, dict) else {}

    def _causal_validation_report(self, context):
        report = context.get("causal_validation", {})
        return dict(report) if isinstance(report, dict) else {}

    def _context_consistency_report(self, context):
        explicit = context.get("context_consistency", {})
        if isinstance(explicit, dict):
            return dict(explicit)
        causal_validation = self._causal_validation_report(context)
        contextual_truth = self._contextual_truth_report(context)
        return {
            "context_consistency": causal_validation.get(
                "context_consistency",
                contextual_truth.get("context_binding_score", 0.0),
            ),
            "context_signature": contextual_truth.get(
                "context_signature",
                context.get("context_discovery", {}).get(
                    "transformation_family",
                    "unknown",
                )
                if isinstance(context.get("context_discovery"), dict)
                else "unknown",
            ),
        }

    def _causal_graph_alignment_score(self, context, aggregate):
        report = context.get("causal_graph_alignment", {})
        if not isinstance(report, dict):
            return aggregate.causal_alignment
        return clamp(
            report.get(
                "alignment_score",
                report.get(
                    "causal_graph_alignment",
                    aggregate.causal_alignment,
                ),
            )
        )

    def _causal_validation_score(self, context, aggregate):
        report = self._causal_validation_report(context)
        return clamp(
            report.get(
                "validation_score",
                report.get(
                    "causal_validation_score",
                    aggregate.causal_alignment,
                ),
            )
        )

    def _dependency_promotion(self, concept, context):
        causal_validation = self._causal_validation_report(context)

        evidence = causal_validation.get(
            "dependency_promotion_evidence",
            {},
        )
        evidence = evidence if isinstance(evidence, dict) else {}

        process_memory = context.get("process_dependency_memory", {})
        process_memory = (
            process_memory
            if isinstance(process_memory, dict)
            else {}
        )

        alignment = context.get("dependency_chain_alignment", {})
        alignment = alignment if isinstance(alignment, dict) else {}

        alignment_ready = alignment.get("alignment_ready", False)
        alignment_confidence = clamp(
            alignment.get("alignment_confidence", 0.0)
        )

        confidence = clamp(
            process_memory.get(
                "dependency_confidence",
                evidence.get(
                    "dependency_confidence",
                    causal_validation.get("dependency_confidence", 0.0),
                ),
            )
        )

        coverage = clamp(
            process_memory.get(
                "dependency_chain_coverage",
                evidence.get(
                    "dependency_chain_coverage",
                    causal_validation.get("dependency_chain_coverage", 0.0),
                ),
            )
        )

        try:
            depth = int(
                process_memory.get(
                    "dependency_chain_depth",
                    evidence.get(
                        "dependency_chain_depth",
                        causal_validation.get("dependency_chain_depth", 0),
                    ),
                )
                or 0
            )
        except Exception:
            depth = 0

        missing_dependencies = list(
            process_memory.get(
                "missing_dependencies",
                evidence.get(
                    "missing_dependencies",
                    causal_validation.get("missing_dependencies", []),
                ),
            )
            or []
        )

        blockers = []

        if confidence < 0.85:
            blockers.append("dependency_confidence_below_promotion_floor")

        if missing_dependencies:
            blockers.append("dependency_chain_missing_dependencies")

        if depth < 4:
            blockers.append("dependency_chain_depth_below_promotion_floor")

        if not alignment_ready:
            blockers.append("dependency_chain_alignment_not_ready")

        complete = (
            confidence >= 0.85
            and not missing_dependencies
            and depth >= 4
            and alignment_ready
        )

        calculated_score = clamp(
            confidence * 0.42
            + coverage * 0.30
            + clamp(depth / 5.0) * 0.18
            + alignment_confidence * 0.10
        )

        score = max(
            clamp(causal_validation.get("promotion_dependency_score", 0.0)),
            calculated_score,
        )

        bonus = max(
            clamp(causal_validation.get("promotion_dependency_bonus", 0.0)),
            (
                round(min((score - 0.80) * 0.25, 0.08), 4)
                if complete and score > 0.80
                else 0.0
            ),
        )

        applicable = concept in self.PROCESS_CONCEPTS

        return {
            "promotion_dependency_score": round(score, 4),
            "promotion_dependency_bonus": bonus if applicable else 0.0,
            "dependency_promotion_blockers": blockers,
            "dependency_confidence": confidence,
            "dependency_chain_depth": depth,
            "dependency_chain_coverage": coverage,
            "missing_dependencies": missing_dependencies,
            "dependency_alignment_ready": alignment_ready,
            "dependency_alignment_confidence": alignment_confidence,
            "dependency_chain_complete_for_promotion": complete,
            "dependency_aware_promotion_applicable": applicable,
        }
    def _contextual_truth_authority_report(
        self,
        concept,
        aggregate,
        context,
        contradiction_review,
        contextual_truth,
        context_consistency,
        semantic_context,
        context_hierarchy,
        causal_validation,
    ):
        raw_contextual_truth_score = clamp(
            contextual_truth.get(
                "contextual_truth_score",
                aggregate.causal_alignment,
            )
        )
        authority = self.contextual_truth_authority_engine.analyze(
            concept,
            truth_candidate_report={
                **contextual_truth,
                "contextual_truth_score": raw_contextual_truth_score,
                **contradiction_review,
            },
            context_consistency_report=context_consistency,
            contextual_truth_report=contextual_truth,
            semantic_context_report=semantic_context,
            context_hierarchy_report=context_hierarchy,
            causal_validation_report={
                **causal_validation,
                "causal_graph_alignment":
                self._causal_graph_alignment_score(context, aggregate),
            },
            identity_report=context.get(
                "identity_safe_truth_integration",
                {},
            ),
        )
        effective_score = max(
            raw_contextual_truth_score,
            clamp(authority.get("contextual_truth_authority", 0.0)),
        )
        support = self.contextual_truth_support_policy.evaluate(
            contextual_truth=contextual_truth,
            contextual_truth_authority=authority,
            context_hierarchy=context_hierarchy,
            semantic_context=semantic_context,
            effective_score=effective_score,
        )
        return {
            **authority,
            "raw_contextual_truth_score": raw_contextual_truth_score,
            "effective_contextual_truth": effective_score,
            "contextual_truth_supported":
            support["contextual_truth_supported"],
            "support_threshold": support["support_threshold"],
            "support_grace_margin": support["support_grace_margin"],
            "contextual_truth_support_policy": support,
        }

    def _metric(self, concept, specification, current_value):
        threshold = specification["threshold"]
        comparator = specification["comparator"]
        effective_threshold = specification.get(
            "effective_threshold",
            self.contextual_truth_support_policy.STRONG_CONTEXT_SUPPORT_FLOOR
            if specification["name"] == "contextual_truth_score"
            else threshold
        )
        passed = (
            current_value >= effective_threshold
            if comparator == ">="
            else current_value < effective_threshold
        )
        gap = (
            max(effective_threshold - current_value, 0.0)
            if comparator == ">="
            else max(current_value - effective_threshold, 0.0)
        )
        return {
            "concept": concept,
            "metric": specification["name"],
            "current_value": current_value,
            "threshold": {
                "comparator": comparator,
                "required": threshold,
            },
            "gap": round(gap, 4),
            "passed": passed,
            "status": "PASSED" if passed else "FAILED",
            "required_action": None if passed else specification["action"],
        }

    def _semantic_spine_recovery(self, context):
        semantic_spine = context.get(
            "semantic_spine_report",
            {},
        )
        semantic_anchor = context.get(
            "semantic_anchor_graph_report",
            context.get(
                "identity_continuity_guardian_report",
                {},
            ).get(
                "semantic_anchor_graph",
                {},
            ),
        ).get(
            "identity_stability",
            {},
        )
        report = semantic_spine or semantic_anchor
        state = report.get(
            "semantic_spine_state",
            report.get(
                "stability_state",
                "unknown",
            ),
        )
        recovery_streak = report.get("recovery_streak", 0)
        required_cycles = report.get("required_recovery_cycles", 3)
        recovery_pending = state == "semantic_spine_recovering"

        return {
            "stability_state": state,
            "recovery_streak": recovery_streak,
            "required_recovery_cycles": required_cycles,
            "remaining_recovery_cycles": (
                max(required_cycles - recovery_streak, 0)
                if recovery_pending
                else 0
            ),
            "recovery_confirmation_pending": recovery_pending,
        }

    def _contradiction_review(
        self,
        contradiction_score,
        context=None,
        stable_truth_authority_locked=False,
    ):
        threshold = next(
            item["threshold"]
            for item in self.METRICS
            if item["name"] == "contradiction_score"
        )
        governance = self.adaptive_contradiction_governance.evaluate(
            contradiction_score,
            context,
            stable_truth_authority_locked=stable_truth_authority_locked,
        )
        dynamic_threshold = governance["dynamic_threshold"]
        review = classify_contradiction_review(
            contradiction_score,
            threshold=dynamic_threshold,
            soft_review_zone=self.CONTRADICTION_REVIEW_ZONE,
        )
        return {
            "effective_contradiction_score": contradiction_score,
            "contradiction_threshold": dynamic_threshold,
            "base_contradiction_threshold": threshold,
            "dynamic_contradiction_threshold": dynamic_threshold,
            "adaptive_contradiction_governance": governance,
            "contradiction_review_zone":
            self.CONTRADICTION_REVIEW_ZONE,
            **review,
        }

    def evaluate(self, belief, aggregate, context=None):
        context = context if isinstance(context, dict) else {}
        causal_boundary_alignment = context.get(
            "causal_boundary_alignment",
        )
        if not isinstance(causal_boundary_alignment, dict):
            causal_boundary_alignment = (
                self.runtime_causal_alignment_engine.evaluate(
                    belief.concept,
                    aggregate,
                    context,
                )
            )
        raw_contradiction_score = aggregate.contradiction_score
        effective_contradiction_score = causal_boundary_alignment[
            "adjusted_contradiction_score"
        ]
        contradiction_review = self._contradiction_review(
            effective_contradiction_score,
            context,
            belief.state == BeliefState.TRUTH_COMMITTED,
        )
        context_hierarchy = self._context_hierarchy_report(context)
        semantic_context = self._semantic_context_report(context)
        contextual_truth = self._contextual_truth_report(context)
        causal_validation = self._causal_validation_report(context)
        dependency_promotion = self._dependency_promotion(
            belief.concept,
            context,
        )
        context_consistency = self._context_consistency_report(context)
        contextual_truth_authority = (
            self._contextual_truth_authority_report(
                belief.concept,
                aggregate,
                context,
                contradiction_review,
                contextual_truth,
                context_consistency,
                semantic_context,
                context_hierarchy,
                causal_validation,
            )
        )
        contextual_truth_score = contextual_truth_authority[
            "effective_contextual_truth"
        ]
        contextual_truth = {
            **contextual_truth,
            "contextual_truth_score": contextual_truth_score,
            "raw_contextual_truth_score":
            contextual_truth_authority["raw_contextual_truth_score"],
            "effective_contextual_truth": contextual_truth_score,
            "contextual_truth_authority":
            contextual_truth_authority["contextual_truth_authority"],
            "contextual_truth_supported":
            contextual_truth_authority["contextual_truth_supported"],
            "authority_status":
            contextual_truth_authority["authority_status"],
            "truth_governance_action":
            contextual_truth_authority["truth_governance_action"],
            "support_threshold":
            self.CONTEXTUAL_TRUTH_SUPPORT_THRESHOLD,
            "support_grace_margin":
            self.CONTEXTUAL_TRUTH_SUPPORT_GRACE,
        }
        if belief.state == BeliefState.TRUTH_COMMITTED:
            return {
                "system": "truth_candidate_engine",
                "concept": belief.concept,
                "current_state": belief.state.value,
                "candidate_state": "TRUTH_STATE_LOCKED",
                "validated_knowledge": True,
                "qualified_metrics": True,
                "stage_eligible_for_truth_candidate": True,
                "metrics_eligible_for_truth_candidate": True,
                "eligible_for_truth_candidate": True,
                "eligibility_reason": "stable_truth_authority_locked",
                "metric_progress": {
                    "passed_count": 0,
                    "required_count": 0,
                    "progress_ratio": 1.0,
                },
                "metrics": [],
                "blocked_metrics": [],
                "ranked_bottlenecks": [],
                "dominant_bottleneck": None,
                "required_actions": [],
                **contradiction_review,
                "raw_contradiction_score": raw_contradiction_score,
                "causal_boundary_alignment":
                causal_boundary_alignment,
                "causal_graph_alignment":
                context.get("causal_graph_alignment", {}),
                "causal_explanation":
                context.get("causal_explanation", {}),
                "causal_validation":
                causal_validation,
                "contextual_truth": contextual_truth,
                "contextual_truth_authority":
                contextual_truth_authority,
                "context_discovery":
                context.get("context_discovery", {}),
                "context_hierarchy": context_hierarchy,
                "semantic_context": semantic_context,
                "semantic_spine_recovery":
                self._semantic_spine_recovery(context),
                "minimum_independent_tasks":
                self.MINIMUM_INDEPENDENT_TASKS,
                "automatic_truth_commit_forbidden": True,
                "truth_candidate_evaluation_skipped": True,
                "truth_state_authority": {
                    "state": "TRUTH_COMMITTED",
                    "truth_state_locked": True,
                },
            }
        generalization = context.get("knowledge_generalization", {})
        values = {
            "evidence_strength": aggregate.evidence_strength,
            "confidence": belief.confidence,
            "contradiction_score": effective_contradiction_score,
            "causal_alignment": aggregate.causal_alignment,
            "causal_graph_alignment":
            max(
                self._causal_graph_alignment_score(context, aggregate),
                clamp(
                    self._causal_graph_alignment_score(context, aggregate)
                    + dependency_promotion["promotion_dependency_bonus"]
                ),
                (
                    dependency_promotion["promotion_dependency_score"]
                    if dependency_promotion[
                        "dependency_chain_complete_for_promotion"
                    ]
                    and dependency_promotion[
                        "dependency_aware_promotion_applicable"
                    ]
                    else 0.0
                ),
            ),
            "causal_validation_score":
            max(
                self._causal_validation_score(context, aggregate),
                clamp(
                    self._causal_validation_score(context, aggregate)
                    + dependency_promotion["promotion_dependency_bonus"]
                ),
                (
                    dependency_promotion["promotion_dependency_score"]
                    if dependency_promotion[
                        "dependency_chain_complete_for_promotion"
                    ]
                    and dependency_promotion[
                        "dependency_aware_promotion_applicable"
                    ]
                    else 0.0
                ),
            ),
            "contextual_truth_score": contextual_truth_score,
            "context_hierarchy_score":
            context_hierarchy.get(
                "context_hierarchy_score",
                aggregate.causal_alignment,
            ),
        }
        dynamic_contradiction_threshold = contradiction_review[
            "dynamic_contradiction_threshold"
        ]
        metric_specifications = [
            {
                **specification,
                "threshold": specification["threshold"],
                "base_threshold": specification["threshold"],
                "effective_threshold": dynamic_contradiction_threshold,
                "dynamic_threshold": dynamic_contradiction_threshold,
            }
            if specification["name"] == "contradiction_score"
            else specification
            for specification in self.METRICS
            if (
                specification["name"]
                not in [
                    "causal_graph_alignment",
                    "causal_validation_score",
                    "contextual_truth_score",
                    "context_hierarchy_score",
                ]
                or isinstance(
                    context.get(
                        "causal_graph_alignment"
                        if specification["name"]
                        == "causal_graph_alignment"
                        else "context_hierarchy"
                        if specification["name"]
                        == "context_hierarchy_score"
                        else "contextual_truth"
                        if specification["name"]
                        == "contextual_truth_score"
                        else "causal_validation"
                    ),
                    dict,
                )
                and context.get(
                    "context_hierarchy"
                    if specification["name"]
                    == "context_hierarchy_score"
                    else "contextual_truth"
                    if specification["name"]
                    == "contextual_truth_score"
                    else "causal_validation"
                    if specification["name"]
                    == "causal_validation_score"
                    else "causal_graph_alignment",
                    {},
                ).get("hierarchy_required", True)
            )
        ]
        metrics = [
            self._metric(
                belief.concept,
                specification,
                values[specification["name"]],
            )
            for specification in metric_specifications
        ]
        used_task_count = generalization.get("used_task_count", 0)
        if used_task_count:
            metrics.append({
                "concept": belief.concept,
                "metric": "independent_task_coverage",
                "current_value": used_task_count,
                "threshold": {
                    "comparator": ">=",
                    "required": self.MINIMUM_INDEPENDENT_TASKS,
                },
                "gap": max(
                    self.MINIMUM_INDEPENDENT_TASKS - used_task_count,
                    0,
                ),
                "passed":
                used_task_count >= self.MINIMUM_INDEPENDENT_TASKS,
                "status": (
                    "PASSED"
                    if used_task_count >= self.MINIMUM_INDEPENDENT_TASKS
                    else "FAILED"
                ),
                "required_action": (
                    None
                    if used_task_count >= self.MINIMUM_INDEPENDENT_TASKS
                    else "collect_independent_cross_task_replications"
                ),
            })
        blocked_metrics = [
            item["metric"]
            for item in metrics
            if not item["passed"]
        ]
        required_actions = [
            item["required_action"]
            for item in metrics
            if item["required_action"]
        ]
        ranked_bottlenecks = sorted(
            (
                item
                for item in metrics
                if not item["passed"]
            ),
            key=lambda item: item["gap"],
        )
        dominant_bottleneck = (
            ranked_bottlenecks[-1]
            if ranked_bottlenecks
            else None
        )

        soft_contradiction_review_only = (
            blocked_metrics == ["contradiction_score"]
            and contradiction_review["within_soft_review_zone"]
        )

        qualified = not blocked_metrics

        dependency_promotion_override_candidate = (
            dependency_promotion[
                "dependency_chain_complete_for_promotion"
            ]
            and dependency_promotion[
                "dependency_aware_promotion_applicable"
            ]
            and dependency_promotion[
                "promotion_dependency_score"
            ] >= 0.90
            and blocked_metrics == ["causal_alignment"]
        )

        promotion_qualified = (
            qualified
            or soft_contradiction_review_only
        )

        promotion_override_review_candidate = (
            not promotion_qualified
            and dependency_promotion_override_candidate
        )

        dependency_promotion_audit = {
            "qualified": qualified,
            "promotion_qualified": promotion_qualified,
            "promotion_override_review_candidate":
                promotion_override_review_candidate,
            "dependency_promotion_override_candidate":
                dependency_promotion_override_candidate,
            "promotion_dependency_score":
                dependency_promotion["promotion_dependency_score"],
            "promotion_dependency_bonus":
                dependency_promotion["promotion_dependency_bonus"],
            "dependency_chain_complete_for_promotion":
                dependency_promotion[
                    "dependency_chain_complete_for_promotion"
                ],
            "dependency_aware_promotion_applicable":
                dependency_promotion[
                    "dependency_aware_promotion_applicable"
                ],
            "blocked_metrics": blocked_metrics,
            "blocked_metric_details": [
                {
                    "metric": item["metric"],
                    "current_value": item["current_value"],
                    "threshold": item["threshold"],
                    "gap": item["gap"],
                    "required_action": item["required_action"],
                }
                for item in metrics
                if not item["passed"]
            ],
        }

        current_state = belief.state.value
        stage_eligible = belief.state in [
            BeliefState.VALIDATED,
            BeliefState.TRUTH_CANDIDATE,
            BeliefState.TRUTH_COMMITTED,
        ]

        eligible = (
            promotion_qualified
            and stage_eligible
        )

        override_review_ready = (
            promotion_override_review_candidate
            and stage_eligible
        )

        if override_review_ready:
            eligible = True

        dependency_promotion_audit[
            "stage_eligible"
        ] = stage_eligible
        dependency_promotion_audit[
            "eligible_for_truth_candidate"
        ] = eligible
        dependency_promotion_audit[
            "override_review_ready"
        ] = override_review_ready

        dependency_promotion_blockers = list(
            dependency_promotion["dependency_promotion_blockers"]
        )
        if (
            dependency_promotion["dependency_chain_complete_for_promotion"]
            and dependency_promotion[
                "dependency_aware_promotion_applicable"
            ]
            and not eligible
        ):
            dependency_promotion_blockers.extend(
                f"promotion_metric_blocked:{metric}"
                for metric in blocked_metrics
            )
            if not stage_eligible:
                dependency_promotion_blockers.append(
                    "promotion_stage_blocked:validated_stage_required"
                )
            if override_review_ready:
                dependency_promotion_blockers.append(
                    "promotion_override_review_ready"
                )
        metrics_passed = len(metrics) - len(blocked_metrics)
        progress_ratio = round(
            metrics_passed / max(len(metrics), 1),
            4,
        )
        eligibility_reason = (
            "dependency_promotion_override"
            if override_review_ready
            else "truth_candidate_ready"
            if eligible
            and not soft_contradiction_review_only
            else "truth_candidate_contradiction_review_required"
            if eligible
            and soft_contradiction_review_only
            else "truth_candidate_contextual_boundary_required"
            if (
                "contradiction_score" not in blocked_metrics
                and causal_boundary_alignment[
                    "contradiction_adjustment"
                ] > 0
            )
            else "truth_candidate_metric_gaps"
            if blocked_metrics
            else "validated_stage_required"
        )
        candidate_state = (
            "REJECTED"
            if belief.state == BeliefState.REJECTED
            else "READY_FOR_LOW_RISK_CONTRADICTION_REVIEW"
            if (
                soft_contradiction_review_only
                and belief.state == BeliefState.TRUTH_CANDIDATE
            )
            else "ADVANCING_TO_TRUTH_CANDIDATE_REVIEW"
            if (
                soft_contradiction_review_only
                and belief.state == BeliefState.VALIDATED
            )
            else "READY_FOR_TRUTH_COMMIT_REVIEW"
            if belief.state in [
                BeliefState.TRUTH_CANDIDATE,
                BeliefState.TRUTH_COMMITTED,
            ]
            else "ADVANCING_TO_TRUTH_CANDIDATE"
            if belief.state == BeliefState.VALIDATED
            else "PRE_VALIDATION"
        )

        return {
            "system": "truth_candidate_engine",
            "concept": belief.concept,
            "current_state": current_state,
            "candidate_state": candidate_state,
            "validated_knowledge":
            belief.state
            in [
                BeliefState.VALIDATED,
                BeliefState.TRUTH_CANDIDATE,
                BeliefState.TRUTH_COMMITTED,
            ],
            "qualified_metrics": promotion_qualified,
            "strict_qualified_metrics": qualified,
            "stage_eligible_for_truth_candidate": stage_eligible,
            "metrics_eligible_for_truth_candidate": promotion_qualified,
            "eligible_for_truth_candidate": eligible,
            "eligibility_reason": eligibility_reason,
            "promotion_review_required": soft_contradiction_review_only,
            "soft_contradiction_review_only":
            soft_contradiction_review_only,
            "truth_commit_review_still_required":
            contradiction_review["contradiction_review_required"],
            "metric_progress": {
                "passed_count": metrics_passed,
                "required_count": len(metrics),
                "progress_ratio": progress_ratio,
            },
            "promotion_dependency_score":
            dependency_promotion["promotion_dependency_score"],
            "promotion_dependency_bonus":
            dependency_promotion["promotion_dependency_bonus"],
            "dependency_promotion_audit":
            dependency_promotion_audit,
            "dependency_promotion_override_candidate":
            dependency_promotion_override_candidate,
            "promotion_override_review_candidate":
            promotion_override_review_candidate,
            "override_review_ready":
            override_review_ready,
            "dependency_promotion_blockers":
            dependency_promotion_blockers,
            "dependency_confidence":
            dependency_promotion["dependency_confidence"],
            "dependency_chain_depth":
            dependency_promotion["dependency_chain_depth"],
            "dependency_chain_coverage":
            dependency_promotion["dependency_chain_coverage"],
            "missing_dependencies":
            dependency_promotion["missing_dependencies"],
            "dependency_chain_complete_for_promotion":
            dependency_promotion["dependency_chain_complete_for_promotion"],
            "metrics": metrics,
            "blocked_metrics": blocked_metrics,
            "ranked_bottlenecks": ranked_bottlenecks,
            "dominant_bottleneck": dominant_bottleneck,
            "required_actions": required_actions,
            **contradiction_review,
            "raw_contradiction_score": raw_contradiction_score,
            "causal_boundary_alignment": causal_boundary_alignment,
            "causal_graph_alignment":
            context.get("causal_graph_alignment", {}),
            "causal_explanation":
            context.get("causal_explanation", {}),
            "causal_validation":
            causal_validation,
            "contextual_truth": contextual_truth,
            "contextual_truth_authority":
            contextual_truth_authority,
            "context_discovery":
            context.get("context_discovery", {}),
            "context_hierarchy": context_hierarchy,
            "semantic_context": semantic_context,
            "semantic_spine_recovery":
            self._semantic_spine_recovery(context),
            "minimum_independent_tasks":
            self.MINIMUM_INDEPENDENT_TASKS,
            "automatic_truth_commit_forbidden": True,
        }


__all__ = [
    "TruthCandidateEngine",
]
