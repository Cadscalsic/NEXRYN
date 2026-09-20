"""Meta-cognitive optimization reports derived from reasoning analytics."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Iterable, Mapping


class MetaCognitiveOptimizer:
    """Learn future reasoning policy preferences from completed episodes."""

    system_name = "meta_cognitive_optimizer"

    DEFAULT_POLICY_MEMORY_PATH = os.path.join(
        "runtime/artifacts/runtime_data",
        "reasoning_policy_memory.json",
    )

    def build_report(
        self,
        *,
        reasoning_graph_report: Mapping[str, Any] | None = None,
        reasoning_analytics_report: Mapping[str, Any] | None = None,
        reasoning_intelligence_report: Mapping[str, Any] | None = None,
        cognitive_analytics_report: Mapping[str, Any] | None = None,
        performance_report: Mapping[str, Any] | None = None,
        cognitive_capability_report: Mapping[str, Any] | None = None,
        causal_context_report: Mapping[str, Any] | None = None,
        dependency_audit_report: Mapping[str, Any] | None = None,
        adaptive_reuse_report: Mapping[str, Any] | None = None,
        all_results: Iterable[Mapping[str, Any]] | None = None,
        policy_memory_path: str | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        graph = self._mapping(reasoning_graph_report)
        analytics = self._mapping(reasoning_analytics_report)
        reasoning = self._mapping(reasoning_intelligence_report)
        cognitive = self._mapping(cognitive_analytics_report)
        performance = self._mapping(performance_report)
        capability = self._mapping(cognitive_capability_report)
        causal = self._mapping(causal_context_report)
        dependency = self._mapping(dependency_audit_report)
        adaptive = self._mapping(adaptive_reuse_report)
        path = policy_memory_path or self.DEFAULT_POLICY_MEMORY_PATH
        memory_before = self._load_policy_memory(path)

        review = self._reasoning_review(graph, analytics, reasoning)
        patterns = self._discover_patterns(
            graph,
            analytics,
            reasoning,
            capability,
            causal,
        )
        optimization_opportunities = self._optimization_opportunities(
            analytics,
            review,
            patterns,
            adaptive,
        )
        policy_updates = self._policy_updates(
            analytics,
            review,
            patterns,
            optimization_opportunities,
        )
        capability_ordering = self._capability_ordering(
            analytics,
            capability,
            memory_before,
        )
        failure_lessons = self._failure_lessons(
            analytics,
            graph,
            all_results or [],
        )
        success_lessons = self._success_lessons(
            graph,
            analytics,
            reasoning,
            causal,
        )
        improvement_plan = self._improvement_plan(
            policy_updates,
            optimization_opportunities,
            failure_lessons,
            success_lessons,
        )
        memory_after, memory_delta = self._update_policy_memory(
            memory_before,
            policy_updates,
            patterns,
            capability_ordering,
            failure_lessons,
            success_lessons,
            analytics,
        )
        persistence_report = (
            self._save_policy_memory(path, memory_after) if persist else {
                "persisted": False,
                "policy_memory_path": path,
                "reason": "persistence_disabled",
            }
        )
        scores = self._scores(
            analytics,
            policy_updates,
            memory_delta,
            optimization_opportunities,
            success_lessons,
            failure_lessons,
        )

        return {
            "system": self.system_name,
            "META_COGNITIVE_REPORT": True,
            "reasoning_review": review,
            "optimization_opportunities": optimization_opportunities,
            "improvement_plan": improvement_plan,
            "policy_updates": policy_updates,
            "capability_ordering": capability_ordering,
            "learning_summary": self._learning_summary(
                patterns,
                policy_updates,
                failure_lessons,
                success_lessons,
                memory_delta,
            ),
            "failure_lessons": failure_lessons,
            "success_lessons": success_lessons,
            "reasoning_improvements": self._reasoning_improvements(
                policy_updates,
                optimization_opportunities,
            ),
            "new_policies": memory_delta["new_policies"],
            "policy_confidence": self._policy_confidence(memory_after),
            "reusable_strategies": patterns["successful_reasoning_templates"],
            "knowledge_growth": memory_delta,
            "generalization_progress": self._generalization_progress(
                memory_after,
                patterns,
                analytics,
            ),
            "self_improvement_score": scores,
            "reasoning_policy_memory": self._memory_summary(memory_after),
            "policy_memory_persistence": persistence_report,
            "pre_reasoning_strategy": self._pre_reasoning_strategy(
                analytics,
                capability_ordering,
                policy_updates,
            ),
            "source_reports": {
                "reasoning_graph": bool(graph),
                "reasoning_analytics": bool(analytics),
                "reasoning_intelligence": bool(reasoning),
                "cognitive_analytics": bool(cognitive),
                "performance": bool(performance),
                "capability": bool(capability),
                "causal": bool(causal),
                "dependency": bool(dependency),
                "adaptive_reuse": bool(adaptive),
            },
            "optimization_safety": {
                "runtime_behavior_modified": False,
                "planner_modified": False,
                "dispatcher_modified": False,
                "capability_architecture_modified": False,
                "policy_updates_are_recommendations": True,
                "drift_control": "bounded_confidence_updates_with_evidence",
            },
        }

    def _reasoning_review(self, graph, analytics, reasoning):
        dashboard = self._mapping(analytics.get("quality_dashboard"))
        capability_stats = self._mapping(analytics.get("capability_statistics"))
        rejected = analytics.get("rejected_hypothesis_analysis", []) or []
        warnings = analytics.get("quality_warnings", []) or []
        convergence = self._mapping(analytics.get("reasoning_convergence"))
        branches = self._branches(graph)
        weak_capabilities = [
            name
            for name, item in capability_stats.items()
            if isinstance(item, Mapping)
            and item.get("capability_influence_score", 0.0) < 0.25
        ]
        return {
            "what_reasoning_worked": [
                f"{dashboard.get('most_useful_capability')} produced the strongest capability influence"
                if dashboard.get("most_useful_capability")
                else "winning branch retained enough evidence",
                f"convergence point: {convergence.get('convergence_point', 'not_observed')}",
            ],
            "what_reasoning_failed": [
                item.get("warning")
                for item in warnings[:10]
                if isinstance(item, Mapping)
            ],
            "unnecessary_branches": [
                branch
                for branch in branches
                if branch.get("state") == "DISCARDED"
                and branch.get("confidence", 0.0) < 0.45
            ][:10],
            "hypotheses_wasted_computation": [
                item
                for item in rejected
                if item.get("should_remain_dormant")
            ][:10],
            "capabilities_dominated": [
                dashboard.get("most_useful_capability")
            ] if dashboard.get("most_useful_capability") else [],
            "capabilities_ignored": weak_capabilities[:10],
            "evidence_arrived_too_late": convergence.get(
                "evidence_triggered_convergence",
                [],
            ) if convergence.get("late_convergence") else [],
            "validations_that_could_have_happened_earlier": [
                "final candidate validation"
            ] if convergence.get("late_convergence") else [],
            "decision_review": self._mapping(
                analytics.get("decision_quality"),
            ).get("decisions", [])[:10],
            "prior_review_reference": reasoning.get("reasoning_summary", ""),
        }

    def _discover_patterns(self, graph, analytics, reasoning, capability, causal):
        dashboard = self._mapping(analytics.get("quality_dashboard"))
        convergence = self._mapping(analytics.get("reasoning_convergence"))
        capability_stats = self._mapping(analytics.get("capability_statistics"))
        learning = analytics.get("learning_opportunities", []) or []
        branches = self._branches(graph)
        hypotheses = [
            item for item in graph.get("hypotheses", []) or []
            if isinstance(item, Mapping)
        ]
        successful_hypotheses = [
            item.get("hypothesis_id")
            for item in hypotheses
            if item.get("status") in {"VALIDATED", "EXECUTED", "SUPPORTED"}
        ]
        failed_hypotheses = [
            item.get("hypothesis_id")
            for item in hypotheses
            if item.get("status") == "REJECTED"
        ]
        cooperation = [
            item for item in capability.get("cooperation_events", []) or []
            if isinstance(item, Mapping)
        ]
        return {
            "successful_reasoning_templates": [
                {
                    "template_id": f"template:{item}",
                    "dominant_hypothesis": item,
                    "evidence": "validated or supported reasoning branch",
                }
                for item in successful_hypotheses[:10]
            ],
            "repeated_reasoning_failures": failed_hypotheses[:10],
            "repeated_dead_ends": convergence.get("dead_ends", [])[:10],
            "repeated_loops": convergence.get("circular_reasoning", [])[:10],
            "repeated_branch_explosions": [
                item for item in analytics.get("quality_warnings", []) or []
                if isinstance(item, Mapping)
                and item.get("warning") == "excessive_branching"
            ],
            "repeated_convergence_patterns": [
                convergence.get("convergence_point"),
                dashboard.get("most_reused_reasoning_pattern"),
            ],
            "repeated_capability_cooperation": cooperation[:10],
            "repeated_transformation_sequences": [
                item
                for item in learning
                if isinstance(item, Mapping)
                and "transformation" in str(item.get("type", ""))
            ][:10],
            "repeated_validation_strategies": [
                item
                for item in learning
                if isinstance(item, Mapping)
                and "validation" in str(item.get("type", ""))
            ][:10],
            "repeated_causal_structures": (
                causal.get("cause_effect_pairs", []) or []
            )[:10],
            "branch_outcome_patterns": [
                {
                    "branch_id": branch.get("branch_id"),
                    "state": branch.get("state"),
                    "confidence": branch.get("confidence", 0.0),
                }
                for branch in branches[:20]
            ],
            "capability_influence_patterns": [
                {
                    "capability": name,
                    "influence": item.get("capability_influence_score", 0.0),
                    "success_rate": item.get("success_rate", 0.0),
                }
                for name, item in capability_stats.items()
                if isinstance(item, Mapping)
            ][:20],
        }

    def _optimization_opportunities(self, analytics, review, patterns, adaptive):
        warnings = [
            item.get("warning")
            for item in analytics.get("quality_warnings", []) or []
            if isinstance(item, Mapping)
        ]
        opportunities = []

        def add(target, action, evidence, expected_effect):
            opportunities.append({
                "target": target,
                "recommended_action": action,
                "evidence": self._as_list(evidence)[:8],
                "expected_effect": expected_effect,
            })

        if "excessive_branching" in warnings or review["unnecessary_branches"]:
            add(
                "reasoning_width",
                "reduce unnecessary branching",
                review["unnecessary_branches"] or "excessive_branching",
                "lower reasoning entropy and cost",
            )
        if patterns["repeated_reasoning_failures"]:
            add(
                "duplicate_reasoning",
                "reduce repeated failed hypothesis generation",
                patterns["repeated_reasoning_failures"],
                "increase hypothesis survival",
            )
        if "late_convergence" in warnings:
            add(
                "convergence_speed",
                "validate earlier",
                "late_convergence",
                "increase convergence speed",
            )
        if "capability_overuse" in warnings:
            add(
                "capability_utilization",
                "delay low-contribution expensive capabilities",
                "capability_overuse",
                "reduce capability cost",
            )
        if adaptive.get("reuse_success_rate", 0.0) or adaptive.get("strategy_hits", 0):
            add(
                "reuse",
                "promote reusable reasoning paths",
                adaptive,
                "increase reuse and generalization",
            )
        if not opportunities:
            add(
                "reasoning_policy",
                "preserve current strategy and collect more evidence",
                analytics.get("reasoning_health"),
                "avoid premature policy drift",
            )
        return opportunities[:20]

    def _policy_updates(self, analytics, review, patterns, opportunities):
        warnings = [
            item.get("warning")
            for item in analytics.get("quality_warnings", []) or []
            if isinstance(item, Mapping)
        ]
        dashboard = self._mapping(analytics.get("quality_dashboard"))
        efficiency = self._mapping(analytics.get("reasoning_efficiency"))
        updates = []

        def add(policy_id, policy_type, recommendation, evidence, confidence):
            updates.append({
                "policy_id": policy_id,
                "policy_type": policy_type,
                "recommendation": recommendation,
                "evidence": self._as_list(evidence)[:10],
                "confidence": self._score(confidence, 0.5),
                "justification": (
                    "policy emerged from reasoning analytics evidence"
                ),
                "drift_guard": "requires repeated evidence before high confidence",
            })

        if "too_many_hypotheses" in warnings or "excessive_branching" in warnings:
            add(
                "branching:generate_fewer_hypotheses",
                "branching_preference",
                "generate fewer hypotheses for similar contexts",
                warnings,
                0.68,
            )
        if "too_few_hypotheses" in warnings:
            add(
                "branching:expand_hypotheses",
                "branching_preference",
                "generate more initial alternatives before converging",
                warnings,
                0.64,
            )
        if "late_convergence" in warnings:
            add(
                "validation:validate_early",
                "validation_preference",
                "run validation earlier for promising branches",
                analytics.get("reasoning_convergence", {}),
                0.72,
            )
        if "premature_convergence" in warnings:
            add(
                "branching:keep_promising_branches_alive",
                "branching_preference",
                "keep promising branches alive longer before final convergence",
                analytics.get("reasoning_convergence", {}),
                0.7,
            )
        if efficiency.get("branch_collapse_rate", 0.0) > 0.5:
            add(
                "rejection:reject_weak_branches_sooner",
                "optimization_rule",
                "reject weak branches sooner after low-confidence evidence",
                efficiency,
                0.66,
            )
        useful = dashboard.get("most_useful_capability")
        if useful:
            add(
                f"capability_order:prefer_{useful}",
                "capability_preference",
                f"prefer {useful} earlier when matching evidence appears",
                dashboard,
                0.74,
            )
        least = dashboard.get("least_useful_capability")
        if least and least != useful:
            add(
                f"capability_order:delay_{least}",
                "capability_preference",
                f"delay {least} unless task evidence demands it",
                dashboard,
                0.58,
            )
        if patterns["successful_reasoning_templates"]:
            add(
                "reuse:promote_reusable_reasoning_paths",
                "reuse_preference",
                "promote reusable reasoning paths before novel expansion",
                patterns["successful_reasoning_templates"],
                0.76,
            )
        if not updates:
            add(
                "stability:preserve_current_policy",
                "stability_rule",
                "preserve current reasoning policy until more evidence accumulates",
                opportunities,
                0.55,
            )
        return updates[:20]

    def _capability_ordering(self, analytics, capability, memory):
        stats = self._mapping(analytics.get("capability_statistics"))
        preferences = self._mapping(memory.get("capability_preferences"))
        rows = []
        for name, item in stats.items():
            if not isinstance(item, Mapping):
                continue
            historical = self._mapping(preferences.get(name))
            score = (
                item.get("capability_influence_score", 0.0) * 0.45
                + item.get("success_rate", 0.0) * 0.25
                + item.get("average_confidence", 0.0) * 0.20
                + historical.get("preference_score", 0.5) * 0.10
            )
            rows.append({
                "capability": name,
                "ordering_score": round(score, 4),
                "evidence": {
                    "influence": item.get("capability_influence_score", 0.0),
                    "success_rate": item.get("success_rate", 0.0),
                    "confidence": item.get("average_confidence", 0.0),
                    "historical_preference": historical.get(
                        "preference_score",
                        0.5,
                    ),
                },
            })
        if not rows:
            rows = [
                {
                    "capability": item,
                    "ordering_score": 0.5,
                    "evidence": {"source": "capabilities_executed"},
                }
                for item in capability.get("capabilities_executed", []) or []
            ]
        ordered = sorted(
            rows,
            key=lambda item: (-item["ordering_score"], item["capability"]),
        )
        return {
            "preferred_order": [item["capability"] for item in ordered],
            "ordering_rationale": ordered[:12],
            "dynamic_ordering_enabled": True,
            "applies_to_future_tasks": True,
        }

    def _failure_lessons(self, analytics, graph, all_results):
        rejected = analytics.get("rejected_hypothesis_analysis", []) or []
        failed_tasks = [
            item for item in all_results
            if isinstance(item, Mapping)
            and not self._mapping(item.get("result")).get("success", True)
        ]
        lessons = []
        for item in rejected[:10]:
            if not isinstance(item, Mapping):
                continue
            lessons.append({
                "root_cognitive_failure": item.get("why_rejected"),
                "missing_reasoning_step": "earlier evidence check"
                if item.get("should_remain_dormant")
                else "additional validation",
                "missing_capability": item.get("capability_rejected_it"),
                "incorrect_ordering": False,
                "insufficient_validation": item.get("rejection_correctness") == "uncertain",
                "weak_evidence": item.get("confidence_after_rejection", 0.0) < 0.5,
                "incorrect_confidence_update": False,
                "knowledge_gap": item.get("evidence_rejected_it", []),
                "improvement_recommendation": (
                    "keep dormant until stronger evidence appears"
                    if item.get("should_remain_dormant")
                    else "learn rejection boundary as negative evidence"
                ),
            })
        for item in failed_tasks[:5]:
            result = self._mapping(item.get("result"))
            residual = self._mapping(result.get("residual_analysis"))
            lessons.append({
                "root_cognitive_failure": residual.get(
                    "probable_root_cause",
                    "task_failed",
                ),
                "missing_reasoning_step": residual.get(
                    "future_learning_priority",
                    "unknown",
                ),
                "missing_capability": "unknown",
                "incorrect_ordering": False,
                "insufficient_validation": True,
                "weak_evidence": True,
                "incorrect_confidence_update": False,
                "knowledge_gap": residual,
                "improvement_recommendation": "store failure for future reasoning review",
            })
        return lessons[:20]

    def _success_lessons(self, graph, analytics, reasoning, causal):
        dashboard = self._mapping(analytics.get("quality_dashboard"))
        final = self._mapping(
            self._mapping(graph.get("decision_trace")).get("final_candidate"),
        )
        confidence = graph.get("confidence_evolution", []) or []
        capability_order = self._mapping(
            analytics.get("quality_dashboard"),
        ).get("most_useful_capability")
        return {
            "winning_reasoning_sequence": [
                item.get("stage")
                for item in graph.get("reasoning_timeline", []) or []
                if isinstance(item, Mapping)
            ][:20],
            "winning_capability_order": [
                capability_order
            ] if capability_order else [],
            "winning_validation_order": [
                item.get("stage")
                for item in graph.get("reasoning_timeline", []) or []
                if isinstance(item, Mapping)
                and item.get("stage") in {"Validation", "Solution"}
            ],
            "winning_causal_chain": (
                causal.get("cause_effect_pairs", []) or []
            )[:10],
            "winning_transformation_chain": [
                item
                for item in analytics.get("learning_opportunities", []) or []
                if isinstance(item, Mapping)
                and "transformation" in str(item.get("type", ""))
            ][:10],
            "winning_confidence_evolution": confidence[:20],
            "reusable_strategy_id": final.get("hypothesis_id")
            or dashboard.get("most_reused_reasoning_pattern")
            or "not_observed",
            "success_reference": reasoning.get("success_intelligence", {}),
        }

    def _improvement_plan(
        self,
        policy_updates,
        opportunities,
        failure_lessons,
        success_lessons,
    ):
        plan = []
        for index, policy in enumerate(policy_updates[:8]):
            plan.append({
                "step": index + 1,
                "policy_id": policy["policy_id"],
                "action": policy["recommendation"],
                "evidence": policy["evidence"],
                "expected_future_effect": self._matching_effect(
                    policy,
                    opportunities,
                ),
            })
        if failure_lessons:
            plan.append({
                "step": len(plan) + 1,
                "policy_id": "failure:learn_negative_constraints",
                "action": "store failed reasoning as negative constraints",
                "evidence": failure_lessons[:5],
                "expected_future_effect": "reduce repeated failures",
            })
        if success_lessons.get("reusable_strategy_id") != "not_observed":
            plan.append({
                "step": len(plan) + 1,
                "policy_id": "success:reuse_winning_sequence",
                "action": "reuse winning reasoning sequence in similar tasks",
                "evidence": success_lessons.get("reusable_strategy_id"),
                "expected_future_effect": "increase convergence speed",
            })
        return plan[:12]

    def _update_policy_memory(
        self,
        memory,
        policy_updates,
        patterns,
        capability_ordering,
        failure_lessons,
        success_lessons,
        analytics,
    ):
        memory = self._ensure_memory(memory)
        now = self._timestamp()
        new_policies = []
        updated_policies = []
        for policy in policy_updates:
            policy_id = policy["policy_id"]
            existing = self._mapping(
                memory["reasoning_policies"].get(policy_id),
            )
            old_confidence = self._score(existing.get("confidence"), 0.0)
            new_confidence = round(
                min(1.0, (old_confidence * 0.8) + (policy["confidence"] * 0.2))
                if existing else policy["confidence"],
                4,
            )
            record = {
                "policy_id": policy_id,
                "policy_type": policy["policy_type"],
                "recommendation": policy["recommendation"],
                "confidence": new_confidence,
                "evidence_count": int(existing.get("evidence_count", 0) or 0) + 1,
                "last_evidence": policy["evidence"],
                "last_updated": now,
                "status": "ACTIVE",
                "justification": policy["justification"],
            }
            memory["reasoning_policies"][policy_id] = record
            if existing:
                updated_policies.append(policy_id)
            else:
                new_policies.append(policy_id)
        for policy in policy_updates:
            bucket = self._policy_bucket(policy["policy_type"])
            if bucket:
                self._append_unique(memory[bucket], policy["policy_id"])
        for item in patterns["successful_reasoning_templates"]:
            self._append_unique(memory["successful_sequences"], item)
        for item in failure_lessons:
            self._append_unique(memory["failed_sequences"], item)
        for item in capability_ordering.get("ordering_rationale", []):
            capability = item.get("capability")
            if not capability:
                continue
            prior = self._mapping(
                memory["capability_preferences"].get(capability),
            )
            prior_score = self._score(prior.get("preference_score"), 0.5)
            score = round(
                (prior_score * 0.7)
                + (item.get("ordering_score", 0.5) * 0.3),
                4,
            )
            memory["capability_preferences"][capability] = {
                "capability": capability,
                "preference_score": score,
                "evidence": item.get("evidence", {}),
                "last_updated": now,
            }
        if success_lessons.get("winning_validation_order"):
            self._append_unique(
                memory["validation_preferences"],
                success_lessons["winning_validation_order"],
            )
        if analytics.get("reasoning_efficiency"):
            self._append_unique(
                memory["branching_preferences"],
                analytics["reasoning_efficiency"],
            )
        memory["episodes_reviewed"] = int(memory.get("episodes_reviewed", 0) or 0) + 1
        memory["last_updated"] = now
        memory = self._bound_memory(memory)
        delta = {
            "new_policies": new_policies,
            "updated_policies": updated_policies,
            "policy_count": len(memory["reasoning_policies"]),
            "successful_sequences_added": len(patterns["successful_reasoning_templates"]),
            "failed_sequences_added": len(failure_lessons),
            "episodes_reviewed": memory["episodes_reviewed"],
        }
        return memory, delta

    def _scores(
        self,
        analytics,
        policy_updates,
        memory_delta,
        opportunities,
        success_lessons,
        failure_lessons,
    ):
        quality = self._score(analytics.get("reasoning_quality_score"), 0.5)
        updates = len(policy_updates)
        new_count = len(memory_delta["new_policies"])
        updated_count = len(memory_delta["updated_policies"])
        lessons = len(failure_lessons) + (
            1 if success_lessons.get("reusable_strategy_id") != "not_observed" else 0
        )
        adaptation_rate = round(
            (new_count + updated_count)
            / max(memory_delta.get("policy_count", 1), 1),
            4,
        )
        optimization_efficiency = round(
            min(1.0, len(opportunities) / max(updates, 1)),
            4,
        )
        learning_velocity = round(
            min(1.0, lessons / max(memory_delta.get("episodes_reviewed", 1), 1)),
            4,
        )
        readiness = round(
            min(1.0, (quality * 0.45) + (learning_velocity * 0.35) + (adaptation_rate * 0.20)),
            4,
        )
        improvement = round(
            min(1.0, (updates / 8.0 * 0.4) + (optimization_efficiency * 0.35) + (quality * 0.25)),
            4,
        )
        stability = round(max(0.0, 1.0 - adaptation_rate * 0.6), 4)
        meta = round(
            min(1.0, (improvement * 0.35) + (stability * 0.25) + (learning_velocity * 0.20) + (readiness * 0.20)),
            4,
        )
        return {
            "meta_cognitive_score": meta,
            "reasoning_improvement_score": improvement,
            "policy_stability": stability,
            "policy_adaptation_rate": adaptation_rate,
            "optimization_efficiency": optimization_efficiency,
            "learning_velocity": learning_velocity,
            "generalization_readiness": readiness,
        }

    def _pre_reasoning_strategy(self, analytics, capability_ordering, policies):
        efficiency = self._mapping(analytics.get("reasoning_efficiency"))
        cost = self._mapping(analytics.get("reasoning_cost"))
        return {
            "expected_reasoning_complexity": (
                "high"
                if efficiency.get("reasoning_width", 0) > 8
                or efficiency.get("maximum_branch_depth", 0) > 4
                else "moderate"
                if efficiency.get("reasoning_width", 0) > 2
                else "low"
            ),
            "expected_branching": efficiency.get("branch_expansion_rate", 0.0),
            "expected_capability_cost": cost.get("cost_per_capability", 0.0),
            "expected_confidence_growth": efficiency.get("average_confidence_gain", 0.0),
            "expected_reuse_opportunity": analytics.get(
                "reasoning_generalization_potential",
                0.0,
            ),
            "expected_causal_importance": analytics.get(
                "reasoning_convergence",
                {},
            ).get("convergence_point", "not_observed"),
            "expected_validation_cost": cost.get("cost_per_validation", 0.0),
            "adaptive_reasoning_strategy": [
                item["recommendation"] for item in policies[:8]
            ],
            "preferred_capability_order": capability_ordering.get(
                "preferred_order",
                [],
            ),
        }

    def _learning_summary(self, patterns, policies, failure_lessons, success_lessons, delta):
        return {
            "successful_patterns_discovered": len(patterns["successful_reasoning_templates"]),
            "failure_patterns_discovered": len(patterns["repeated_reasoning_failures"]),
            "policy_updates_generated": len(policies),
            "failure_lessons_generated": len(failure_lessons),
            "success_strategy": success_lessons.get("reusable_strategy_id"),
            "memory_delta": delta,
        }

    def _reasoning_improvements(self, policies, opportunities):
        return [
            {
                "improvement": policy["recommendation"],
                "policy_id": policy["policy_id"],
                "evidence": policy["evidence"],
                "optimization_target": self._matching_target(policy, opportunities),
            }
            for policy in policies[:12]
        ]

    def _generalization_progress(self, memory, patterns, analytics):
        reusable = len(memory.get("successful_sequences", []))
        policies = len(memory.get("reasoning_policies", {}))
        readiness = self._score(
            analytics.get("reasoning_generalization_potential"),
            0.0,
        )
        return {
            "reusable_strategy_count": reusable,
            "policy_count": policies,
            "generalization_signal": readiness,
            "progress_state": (
                "READY"
                if readiness >= 0.75 and reusable >= 3
                else "GROWING"
                if reusable or policies
                else "OBSERVING"
            ),
            "new_templates": patterns["successful_reasoning_templates"][:10],
        }

    def _policy_confidence(self, memory):
        policies = self._mapping(memory.get("reasoning_policies"))
        return {
            key: item.get("confidence", 0.0)
            for key, item in sorted(policies.items())
            if isinstance(item, Mapping)
        }

    def _memory_summary(self, memory):
        return {
            "episodes_reviewed": memory.get("episodes_reviewed", 0),
            "reasoning_policy_count": len(memory.get("reasoning_policies", {})),
            "optimization_rule_count": len(memory.get("optimization_rules", [])),
            "successful_sequence_count": len(memory.get("successful_sequences", [])),
            "failed_sequence_count": len(memory.get("failed_sequences", [])),
            "capability_preference_count": len(memory.get("capability_preferences", {})),
            "validation_preference_count": len(memory.get("validation_preferences", [])),
            "branching_preference_count": len(memory.get("branching_preferences", [])),
            "last_updated": memory.get("last_updated"),
        }

    def _load_policy_memory(self, path):
        if not os.path.exists(path):
            return self._empty_memory()
        try:
            with open(path, "r", encoding="utf-8") as file:
                payload = json.load(file)
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return self._empty_memory()
        return self._ensure_memory(payload)

    def _save_policy_memory(self, path, memory):
        try:
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(path, "w", encoding="utf-8") as file:
                json.dump(memory, file, indent=2, sort_keys=True)
        except OSError as exc:
            return {
                "persisted": False,
                "policy_memory_path": path,
                "error": str(exc),
            }
        return {
            "persisted": True,
            "policy_memory_path": path,
            "policy_count": len(memory.get("reasoning_policies", {})),
        }

    def _empty_memory(self):
        return {
            "version": 1,
            "episodes_reviewed": 0,
            "last_updated": None,
            "reasoning_policies": {},
            "optimization_rules": [],
            "successful_sequences": [],
            "failed_sequences": [],
            "capability_preferences": {},
            "validation_preferences": [],
            "branching_preferences": [],
        }

    def _ensure_memory(self, memory):
        base = self._empty_memory()
        if isinstance(memory, Mapping):
            for key, value in memory.items():
                if key in base:
                    base[key] = value
        if not isinstance(base["reasoning_policies"], dict):
            base["reasoning_policies"] = {}
        if not isinstance(base["capability_preferences"], dict):
            base["capability_preferences"] = {}
        for key in (
            "optimization_rules",
            "successful_sequences",
            "failed_sequences",
            "validation_preferences",
            "branching_preferences",
        ):
            if not isinstance(base[key], list):
                base[key] = []
        return base

    def _bound_memory(self, memory):
        for key in (
            "optimization_rules",
            "successful_sequences",
            "failed_sequences",
            "validation_preferences",
            "branching_preferences",
        ):
            memory[key] = memory[key][-50:]
        if len(memory["reasoning_policies"]) > 80:
            ordered = sorted(
                memory["reasoning_policies"].values(),
                key=lambda item: (
                    item.get("confidence", 0.0),
                    item.get("last_updated", ""),
                ),
                reverse=True,
            )[:80]
            memory["reasoning_policies"] = {
                item["policy_id"]: item for item in ordered
            }
        return memory

    def _append_unique(self, target, item):
        marker = json.dumps(item, sort_keys=True, default=str)
        existing = {
            json.dumps(value, sort_keys=True, default=str)
            for value in target
        }
        if marker not in existing:
            target.append(item)

    def _policy_bucket(self, policy_type):
        return {
            "optimization_rule": "optimization_rules",
            "validation_preference": "validation_preferences",
            "branching_preference": "branching_preferences",
        }.get(policy_type)

    def _branches(self, graph):
        branches = []
        for key in (
            "active_branches",
            "merged_branches",
            "discarded_branches",
            "validated_branches",
        ):
            branches.extend([
                item for item in graph.get(key, []) or []
                if isinstance(item, Mapping)
            ])
        return branches

    def _matching_effect(self, policy, opportunities):
        target = self._matching_target(policy, opportunities)
        for item in opportunities:
            if item.get("target") == target:
                return item.get("expected_effect")
        return "improve future reasoning quality"

    def _matching_target(self, policy, opportunities):
        recommendation = policy.get("recommendation", "")
        for item in opportunities:
            action = item.get("recommended_action", "")
            if action and action in recommendation or recommendation in action:
                return item.get("target")
        return policy.get("policy_type", "reasoning_policy")

    def _timestamp(self):
        return datetime.utcnow().isoformat(timespec="microseconds") + "Z"

    def _mapping(self, value):
        return value if isinstance(value, Mapping) else {}

    def _as_list(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, set):
            return list(value)
        if isinstance(value, Mapping):
            return [value]
        return [value]

    def _score(self, value, default=0.0):
        if isinstance(value, (int, float)):
            return round(max(0.0, min(float(value), 1.0)), 4)
        return round(float(default or 0.0), 4)


meta_cognitive_optimizer = MetaCognitiveOptimizer()


__all__ = [
    "MetaCognitiveOptimizer",
    "meta_cognitive_optimizer",
]
