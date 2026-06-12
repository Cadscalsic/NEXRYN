from core.epistemic_models import clamp
from core.knowledge.adaptive_contradiction_governance import (
    AdaptiveContradictionGovernance,
)
from core.knowledge.contradiction_review_policy import (
    SOFT_REVIEW_ZONE,
)


class TruthCandidatePromotionEngine:
    MINIMUM_OBSERVED_TASKS = 8
    MINIMUM_CROSS_TASK_SUPPORT = 0.80
    MINIMUM_CAUSAL_STABILITY = 0.80
    MINIMUM_CONTEXT_STRENGTH = 0.69
    MINIMUM_IDENTITY_STRENGTH = 0.62
    MAXIMUM_CONTRADICTION = 0.10
    CONTRADICTION_REVIEW_ZONE = SOFT_REVIEW_ZONE

    WEIGHTS = {
        "observation_strength": 0.18,
        "cross_task_support": 0.20,
        "contradiction_governance": 0.18,
        "causal_stability": 0.18,
        "context_strength": 0.14,
        "identity_strength": 0.12,
    }
    PROCESS_CONCEPTS = {
        "growth",
        "propagation",
        "replication",
        "topological_growth",
        "directional_motion",
        "object_identity_preservation",
    }

    def __init__(self):
        self.adaptive_contradiction_governance = (
            AdaptiveContradictionGovernance()
        )

    def _records(self, ledger_item):
        return [
            record
            for record in ledger_item.get("records", [])
            if isinstance(record, dict)
        ]

    def _average(self, records, key, default):
        values = [
            clamp(record.get(key))
            for record in records
            if record.get(key) is not None
        ]
        if not values:
            return clamp(default)
        return clamp(sum(values) / len(values))

    def _success_counts(self, records):
        successes = sum(record.get("success") is True for record in records)
        counterexamples = sum(
            record.get("success") is False
            for record in records
        )
        return successes, counterexamples

    def _runtime_evaluation (self, concept, truth_candidate_report):
        for item in truth_candidate_report.get("evaluations", []):
            if (
                isinstance(item, dict)
                and str(item.get("concept")) == concept
            ):
                return item
        return {}

    def _nested_score(self, report, *paths, default=0.0):
        for path in paths:
            data = report
            for key in path:
                if not isinstance(data, dict):
                    data = None
                    break
                data = data.get(key)
            if data is not None:
                return clamp(data)
        return clamp(default)

    def _context_strength(self, runtime):
        return max(
            self._nested_score(
                runtime,
                ("contextual_truth_authority", "effective_contextual_truth"),
                ("contextual_truth", "effective_contextual_truth"),
                ("contextual_truth", "contextual_truth_score"),
                default=0.0,
            ),
            self._nested_score(
                runtime,
                ("context_hierarchy", "context_hierarchy_score"),
                ("context_hierarchy", "score"),
                default=0.0,
            ),
            self._nested_score(
                runtime,
                ("semantic_context", "semantic_context_score"),
                ("semantic_context", "confidence"),
                default=0.0,
            ),
        )

    def _identity_strength(self, runtime, ledger_item):
        return max(
            self._nested_score(
                runtime,
                ("identity_safe_truth_integration", "identity_continuity"),
                ("identity_safe_truth_integration", "identity_strength"),
                default=0.0,
            ),
            clamp(ledger_item.get("identity_strength", 0.0)),
        )

    def _causal_stability(self, records, ledger_item, runtime):
        return max(
            self._average(
                records,
                "causal_alignment",
                ledger_item.get("cross_task_support", 0.0),
            ),
            self._nested_score(
                runtime,
                ("causal_validation", "validation_score"),
                ("causal_graph_alignment", "alignment_score"),
                default=0.0,
            ),
        )

    def _dependency_promotion(self, concept, runtime):
        runtime = runtime if isinstance(runtime, dict) else {}
        causal_validation = runtime.get("causal_validation", {})
        causal_validation = (
            causal_validation
            if isinstance(causal_validation, dict)
            else {}
        )
        evidence = causal_validation.get("dependency_promotion_evidence", {})
        if not isinstance(evidence, dict):
            evidence = {}
        confidence = clamp(
            causal_validation.get(
                "dependency_confidence",
                evidence.get("dependency_confidence", 0.0),
            )
        )
        coverage = clamp(
            causal_validation.get(
                "dependency_chain_coverage",
                evidence.get("dependency_chain_coverage", 0.0),
            )
        )
        try:
            depth = int(
                causal_validation.get(
                    "dependency_chain_depth",
                    evidence.get("dependency_chain_depth", 0),
                )
                or 0
            )
        except Exception:
            depth = 0
        missing_dependencies = list(
            causal_validation.get(
                "missing_dependencies",
                evidence.get("missing_dependencies", []),
            )
            or []
        )
        blockers = []
        if confidence <= 0.85:
            blockers.append("dependency_confidence_below_promotion_floor")
        if missing_dependencies:
            blockers.append("dependency_chain_missing_dependencies")
        if depth < 4:
            blockers.append("dependency_chain_depth_below_promotion_floor")
        complete = (
            confidence > 0.85
            and not missing_dependencies
            and depth >= 4
        )
        depth_score = clamp(depth / 5.0)
        score = max(
            clamp(
                confidence * 0.46
                + coverage * 0.34
                + depth_score * 0.20
            ),
            clamp(causal_validation.get("promotion_dependency_score", 0.0)),
        )
        bonus = max(
            clamp(causal_validation.get("promotion_dependency_bonus", 0.0)),
            (
                round(min((score - 0.80) * 0.25, 0.08), 4)
                if complete and score > 0.80
                else 0.0
            ),
        )
        return {
            "promotion_dependency_score": round(score, 4),
            "promotion_dependency_bonus": bonus,
            "dependency_promotion_blockers": blockers,
            "dependency_confidence": confidence,
            "dependency_chain_depth": depth,
            "dependency_chain_coverage": coverage,
            "missing_dependencies": missing_dependencies,
            "dependency_chain_complete_for_promotion": complete,
            "dependency_aware_promotion_applicable":
            concept in self.PROCESS_CONCEPTS,
        }

    def _contradiction_governance(
        self,
        contradiction_score,
        cross_task_support,
        causal_stability,
        context_strength,
        context,
    ):
        governance = self.adaptive_contradiction_governance.evaluate(
            contradiction_score,
            context,
        )
        adaptive_soft_review_zone = (
            contradiction_score > self.MAXIMUM_CONTRADICTION
            and governance["contradiction_below_dynamic_threshold"]
        )
        soft_review_acceptable = (
            (
                governance["within_soft_review_zone"]
                or adaptive_soft_review_zone
            )
            and cross_task_support >= self.MINIMUM_CROSS_TASK_SUPPORT
            and causal_stability >= self.MINIMUM_CAUSAL_STABILITY
            and context_strength >= self.MINIMUM_CONTEXT_STRENGTH
        )
        passed = (
            governance["contradiction_below_dynamic_threshold"]
            or soft_review_acceptable
        )
        return {
            **governance,
            "contradiction_score": contradiction_score,
            "contradiction_threshold": governance["dynamic_threshold"],
            "base_contradiction_threshold": self.MAXIMUM_CONTRADICTION,
            "adaptive_soft_review_zone": adaptive_soft_review_zone,
            "soft_review_acceptable_for_candidate_promotion":
            soft_review_acceptable,
            "passed": passed,
        }

    def _normalized_task_score(self, observed_task_count):
        return clamp(observed_task_count / self.MINIMUM_OBSERVED_TASKS)

    def evaluate(
        self,
        ledger_item,
        truth_candidate_report=None,
    ):
        truth_candidate_report = truth_candidate_report or {}
        concept = str(ledger_item.get("concept", ""))
        records = self._records(ledger_item)
        runtime = self._runtime_evaluation(concept, truth_candidate_report)
        successful_tasks, counterexample_tasks = self._success_counts(
            records,
        )
        observed_task_count = int(ledger_item.get("used_task_count", 0))
        cross_task_support = clamp(
            ledger_item.get(
                "cross_task_support",
                ledger_item.get("independent_success_rate", 0.0),
            )
        )
        contradiction_score = self._average(
            records,
            "contradiction_score",
            runtime.get(
                "effective_contradiction_score",
                ledger_item.get("average_contradiction_score", 1.0),
            ),
        )
        context_strength = max(
            self._context_strength(runtime),
            clamp(ledger_item.get("context_strength", 0.0)),
        )
        identity_strength = self._identity_strength(runtime, ledger_item)
        identity_observed = identity_strength > 0.0
        if not identity_observed:
            identity_strength = 0.75
        causal_stability = self._causal_stability(
            records,
            ledger_item,
            runtime,
        )
        dependency_promotion = self._dependency_promotion(concept, runtime)
        print(
            "LIFECYCLE DEP DEBUG:",
            concept,
            {
                "runtime_keys": list(runtime.keys())
                if isinstance(runtime, dict)
                else [],
                "process_dependency_memory":
                runtime.get("process_dependency_memory", {})
                if isinstance(runtime, dict)
                else {},
                "dependency_promotion": dependency_promotion,
            },
        )
        dependency_bonus = (
            dependency_promotion["promotion_dependency_bonus"]
            if dependency_promotion["dependency_aware_promotion_applicable"]
            else 0.0
        )
        raw_causal_stability = causal_stability
        causal_stability = max(
            causal_stability,
            clamp(causal_stability + dependency_bonus),
            (
                dependency_promotion["promotion_dependency_score"]
                if (
                    dependency_promotion[
                        "dependency_chain_complete_for_promotion"
                    ]
                    and dependency_promotion[
                        "dependency_aware_promotion_applicable"
                    ]
                )
                else 0.0
            ),
        )
        contradiction_governance = self._contradiction_governance(
            contradiction_score,
            cross_task_support,
            causal_stability,
            context_strength,
            {
                "knowledge_generalization": ledger_item,
                "truth_candidate": runtime,
                **runtime,
            },
        )
        readiness_gates = {
            "observed_task_count":
            observed_task_count >= self.MINIMUM_OBSERVED_TASKS,
            "cross_task_support":
            cross_task_support >= self.MINIMUM_CROSS_TASK_SUPPORT,
            "contradiction_governance":
            contradiction_governance["passed"],
            "causal_stability":
            causal_stability >= self.MINIMUM_CAUSAL_STABILITY,
            "context_strength":
            context_strength >= self.MINIMUM_CONTEXT_STRENGTH,
            "identity_strength":
            identity_strength >= self.MINIMUM_IDENTITY_STRENGTH,
        }
        dependency_promotion_blockers = list(
            dependency_promotion["dependency_promotion_blockers"]
        )
        component_scores = {
            "observation_strength":
            self._normalized_task_score(observed_task_count),
            "cross_task_support": cross_task_support,
            "contradiction_governance": (
                1.0
                if contradiction_governance["passed"]
                else clamp(
                    1.0
                    - contradiction_governance["contradiction_gap"]
                    / max(self.CONTRADICTION_REVIEW_ZONE, 0.0001)
                )
            ),
            "causal_stability": causal_stability,
            "context_strength": context_strength,
            "identity_strength": identity_strength,
        }
        promotion_score = clamp(
            sum(
                component_scores[name] * weight
                for name, weight in self.WEIGHTS.items()
            )
        )
        candidate_ready = all(readiness_gates.values())
        remaining_blockers_after_dependency = [
            gate
            for gate, passed in readiness_gates.items()
            if not passed
        ]
        if (
            dependency_promotion["dependency_chain_complete_for_promotion"]
            and dependency_promotion[
                "dependency_aware_promotion_applicable"
            ]
            and not candidate_ready
        ):
            dependency_promotion_blockers.extend(
                f"promotion_gate_blocked:{gate}"
                for gate in remaining_blockers_after_dependency
            )
        mixed_outcomes = bool(successful_tasks and counterexample_tasks)
        decision = (
            "PROMOTE_TO_TRUTH_CANDIDATE"
            if candidate_ready
            else "CONTINUE_BOUNDARY_REFINEMENT"
            if mixed_outcomes
            else "CONTINUE_GENERALIZATION"
            if observed_task_count >= self.MINIMUM_OBSERVED_TASKS
            else "CONTINUE_DISCOVERY"
        )

        return {
            "system": "truth_candidate_promotion_engine",
            "phase": "5.6",
            "concept": concept,
            "decision": decision,
            "candidate_ready": candidate_ready,
            "promotion_score": promotion_score,
            "promotion_dependency_score":
            dependency_promotion["promotion_dependency_score"],
            "promotion_dependency_bonus": dependency_bonus,
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
            "readiness_gates": readiness_gates,
            "failed_gates": [
                gate
                for gate, passed in readiness_gates.items()
                if not passed
            ],
            "component_scores": component_scores,
            "observed_task_count": observed_task_count,
            "successful_task_count": successful_tasks,
            "counterexample_task_count": counterexample_tasks,
            "mixed_outcomes_detected": mixed_outcomes,
            "cross_task_support": cross_task_support,
            "average_contradiction_score": contradiction_score,
            "causal_stability": causal_stability,
            "raw_causal_stability": raw_causal_stability,
            "context_strength": context_strength,
            "identity_strength": identity_strength,
            "identity_strength_observed": identity_observed,
            "contradiction_governance": contradiction_governance,
            "formal_lifecycle_path": [
                "DISCOVERING",
                "BOUNDARY_REFINEMENT",
                "TRUTH_CANDIDATE",
                "STABLE_TRUTH",
            ],
            "truth_commit_still_requires_identity_and_trials": True,
        }


__all__ = [
    "TruthCandidatePromotionEngine",
]
