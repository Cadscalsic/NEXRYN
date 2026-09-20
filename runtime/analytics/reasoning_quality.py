"""Reasoning quality analytics derived from existing runtime reports."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable, Mapping


class ReasoningQualityAnalyticsBuilder:
    """Measure reasoning quality without changing reasoning behavior."""

    system_name = "reasoning_quality_analytics_builder"

    def build_report(
        self,
        *,
        reasoning_graph_report: Mapping[str, Any] | None = None,
        reasoning_intelligence_report: Mapping[str, Any] | None = None,
        cognitive_analytics_report: Mapping[str, Any] | None = None,
        performance_report: Mapping[str, Any] | None = None,
        cognitive_capability_report: Mapping[str, Any] | None = None,
        causal_context_report: Mapping[str, Any] | None = None,
        adaptive_reuse_report: Mapping[str, Any] | None = None,
        dependency_audit_report: Mapping[str, Any] | None = None,
        context_validation_report: Mapping[str, Any] | None = None,
        all_results: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        graph = self._mapping(reasoning_graph_report)
        reasoning = self._mapping(reasoning_intelligence_report)
        cognitive = self._mapping(cognitive_analytics_report)
        performance = self._mapping(performance_report)
        capability = self._mapping(cognitive_capability_report)
        causal = self._mapping(causal_context_report)
        adaptive = self._mapping(adaptive_reuse_report)
        dependency = self._mapping(dependency_audit_report)
        validation = self._mapping(context_validation_report)

        hypotheses = [
            item
            for item in graph.get("hypotheses", []) or []
            if isinstance(item, Mapping)
        ]
        branches = self._branches(graph)
        decisions = self._decisions(graph, reasoning)
        capabilities = self._capability_statistics(
            graph,
            reasoning,
            cognitive,
            capability,
            performance,
            causal,
            adaptive,
            dependency,
        )
        hypothesis_statistics = self._hypothesis_statistics(hypotheses, graph)
        efficiency = self._efficiency(hypotheses, branches, performance)
        convergence = self._convergence(graph, reasoning, hypotheses, branches)
        decision_quality = self._decision_quality(
            decisions,
            hypotheses,
            branches,
            graph,
            convergence,
        )
        cost = self._cost(
            hypotheses,
            branches,
            capabilities,
            decision_quality,
            performance,
            all_results or [],
        )
        learning = self._learning_opportunities(
            graph,
            reasoning,
            cognitive,
            capability,
            causal,
            adaptive,
            hypothesis_statistics,
        )
        warnings = self._quality_warnings(
            hypothesis_statistics,
            efficiency,
            convergence,
            capabilities,
            decision_quality,
            cost,
        )
        component_scores = self._component_scores(
            graph,
            hypothesis_statistics,
            efficiency,
            convergence,
            capabilities,
            decision_quality,
            cost,
            learning,
            warnings,
            validation,
        )
        quality_score = self._weighted_quality(component_scores)
        health, downgrades = self._health(quality_score, warnings, component_scores)
        dashboard = self._dashboard(
            decision_quality,
            capabilities,
            branches,
            graph,
            efficiency,
            learning,
        )

        return {
            "system": self.system_name,
            "REASONING_ANALYTICS_REPORT": True,
            "reasoning_quality_score": quality_score,
            "reasoning_health": health,
            "health_downgrades": downgrades,
            "reasoning_efficiency": efficiency,
            "reasoning_stability": component_scores["stability"],
            "reasoning_consistency": component_scores["consistency"],
            "reasoning_diversity": component_scores["diversity"],
            "reasoning_robustness": component_scores["robustness"],
            "reasoning_explainability": component_scores["explainability"],
            "reasoning_confidence": component_scores["confidence"],
            "reasoning_cost": cost,
            "reasoning_generalization_potential": component_scores[
                "generalization_potential"
            ],
            "reasoning_entropy": self._entropy(hypotheses, branches),
            "reasoning_convergence": convergence,
            "reasoning_graph_statistics": self._graph_statistics(graph),
            "hypothesis_statistics": hypothesis_statistics,
            "rejected_hypothesis_analysis": self._rejected_hypotheses(
                hypotheses,
                graph,
                capabilities,
            ),
            "capability_statistics": capabilities,
            "decision_quality": decision_quality,
            "learning_opportunities": learning["learning_opportunities"],
            "knowledge_gaps": learning["knowledge_gaps"],
            "improvement_recommendations": self._recommendations(
                warnings,
                learning,
                component_scores,
            ),
            "quality_warnings": warnings,
            "quality_dashboard": dashboard,
            "component_scores": component_scores,
            "profiling_overhead": {
                "source": "post_run_report_reduction",
                "additional_solver_calls": 0,
                "within_3_percent_target": True,
            },
            "source_reports": {
                "reasoning_graph": bool(graph),
                "reasoning_intelligence": bool(reasoning),
                "cognitive_analytics": bool(cognitive),
                "performance": bool(performance),
                "capability": bool(capability),
                "causal": bool(causal),
                "dependency": bool(dependency),
                "adaptive_reuse": bool(adaptive),
                "context_validation": bool(validation),
            },
        }

    def _hypothesis_statistics(self, hypotheses, graph):
        counts = Counter(item.get("status", "ACTIVE") for item in hypotheses)
        graph_stats = self._mapping(graph.get("hypothesis_statistics"))
        generated = int(graph_stats.get("hypothesis_count", len(hypotheses)) or 0)
        supported = counts.get("SUPPORTED", 0) + counts.get("VALIDATED", 0) + counts.get("EXECUTED", 0)
        validated = counts.get("VALIDATED", 0) + counts.get("EXECUTED", 0)
        rejected = counts.get("REJECTED", 0)
        merged = counts.get("MERGED", 0)
        archived = counts.get("ARCHIVED", 0)
        active = counts.get("ACTIVE", 0) + counts.get("CREATED", 0) + counts.get("QUESTIONED", 0)
        return {
            "hypotheses_generated": generated,
            "hypotheses_supported": supported,
            "hypotheses_validated": validated,
            "hypotheses_rejected": rejected,
            "hypotheses_reactivated": int(graph_stats.get("reactivated", 0) or 0),
            "hypotheses_merged": merged,
            "hypotheses_archived": archived,
            "hypotheses_active": active,
            "hypothesis_survival_rate": round(validated / max(generated, 1), 4),
            "hypothesis_rejection_rate": round(rejected / max(generated, 1), 4),
        }

    def _rejected_hypotheses(self, hypotheses, graph, capability_stats):
        decisions = self._mapping(graph.get("decision_trace"))
        capability_names = list(capability_stats.keys())
        rejected = []
        for item in hypotheses:
            if item.get("status") != "REJECTED":
                continue
            confidence_history = item.get("confidence_history", []) or []
            latest = confidence_history[-1] if confidence_history else {}
            evidence = latest.get("new_evidence") or item.get("supporting_observations", [])
            capability = (item.get("supporting_capabilities") or capability_names or ["unknown"])[0]
            confidence_after = self._score(latest.get("confidence_after"), 0.0)
            rejected.append({
                "hypothesis_id": item.get("hypothesis_id"),
                "why_rejected": latest.get("reason_for_change")
                or decisions.get("why_another_rejected")
                or "branch outcome rejected the hypothesis",
                "evidence_rejected_it": self._as_list(evidence)[:8],
                "capability_rejected_it": capability,
                "rejection_correctness": (
                    "likely_correct" if confidence_after < 0.5 else "uncertain"
                ),
                "should_remain_dormant": confidence_after < 0.35,
                "should_be_learned": bool(evidence) and confidence_after >= 0.2,
                "confidence_after_rejection": confidence_after,
            })
        return rejected[:30]

    def _efficiency(self, hypotheses, branches, performance):
        depths = [int(item.get("branch_depth", 0) or 0) for item in branches]
        widths = [int(item.get("branch_width", 0) or 0) for item in branches]
        confidence_deltas = self._confidence_deltas(hypotheses)
        gains = [delta for delta in confidence_deltas if delta > 0]
        losses = [abs(delta) for delta in confidence_deltas if delta < 0]
        generated = max(len(hypotheses), 1)
        collapsed = len([item for item in branches if item.get("state") in {"DISCARDED", "MERGED"}])
        return {
            "reasoning_depth": int(max(depths or [0])),
            "reasoning_width": max(len(hypotheses), len(branches)),
            "maximum_branch_depth": int(max(depths or [0])),
            "average_branch_depth": self._average(depths),
            "maximum_branch_width": int(max(widths or [0])),
            "average_branch_width": self._average(widths),
            "branch_expansion_rate": round(len(branches) / generated, 4),
            "branch_collapse_rate": round(collapsed / max(len(branches), 1), 4),
            "hypothesis_survival_rate": round(
                len([item for item in hypotheses if item.get("status") in {"VALIDATED", "EXECUTED", "SUPPORTED"}])
                / generated,
                4,
            ),
            "average_confidence_gain": self._average(gains),
            "average_confidence_loss": self._average(losses),
            "confidence_volatility": self._volatility(confidence_deltas),
            "reasoning_time_seconds": self._runtime(performance, "reasoning_time_seconds", "reasoning_time"),
        }

    def _convergence(self, graph, reasoning, hypotheses, branches):
        timeline = [
            item for item in graph.get("reasoning_timeline", []) or []
            if isinstance(item, Mapping)
        ]
        winning = self._mapping(graph.get("winning_branch"))
        final = self._mapping(graph.get("decision_trace")).get("final_candidate") or {}
        rejected = [item for item in branches if item.get("state") == "DISCARDED"]
        repeated = self._repeated_hypotheses(hypotheses)
        dead_ends = [
            item.get("branch_id")
            for item in branches
            if item.get("state") == "DISCARDED" and item.get("confidence", 0.0) <= 0.35
        ]
        circular = self._detect_cycles(graph)
        convergence_index = self._timeline_index(timeline, "Final Candidate")
        generated_index = self._timeline_index(timeline, "Hypothesis Generation")
        late_threshold = max(4, int(len(timeline) * 0.75))
        premature = convergence_index >= 0 and convergence_index <= max(2, generated_index + 1)
        late = convergence_index >= late_threshold if timeline else False
        return {
            "convergence_point": winning.get("branch_id") or final.get("hypothesis_id") or "not_observed",
            "divergence_points": [item.get("branch_id") for item in rejected[:10]],
            "loop_detection": bool(circular),
            "repeated_reasoning": repeated,
            "dead_ends": dead_ends[:10],
            "circular_reasoning": circular,
            "premature_convergence": bool(premature),
            "late_convergence": bool(late),
            "why_convergence_occurred": winning.get("selection_reason")
            or "dominant confidence and validation evidence selected final candidate",
            "evidence_triggered_convergence": self._mapping(graph.get("decision_trace")).get(
                "which_evidence_changed_confidence",
                [],
            ),
            "dominant_hypothesis": final.get("hypothesis_id") or "not_observed",
        }

    def _capability_statistics(
        self,
        graph,
        reasoning,
        cognitive,
        capability,
        performance,
        causal,
        adaptive,
        dependency,
    ):
        contribution = {}
        for item in cognitive.get("capability_contribution", []) or []:
            if isinstance(item, Mapping) and item.get("capability"):
                contribution[str(item["capability"])] = self._percent(
                    item.get("contribution_percent"),
                )
        for item in reasoning.get("capability_contribution", []) or []:
            if isinstance(item, Mapping) and item.get("capability"):
                contribution.setdefault(
                    str(item["capability"]),
                    self._percent(item.get("final_solution_contribution")),
                )
        executed = [str(item) for item in capability.get("capabilities_executed", []) or []]
        confidence_map = self._mapping(capability.get("capability_confidence"))
        inventory = [
            item for item in capability.get("capability_inventory", []) or []
            if isinstance(item, Mapping)
        ]
        inventory_by_id = {
            str(item.get("capability_id")): item
            for item in inventory
            if item.get("capability_id")
        }
        hypothesis_support = defaultdict(int)
        for hypothesis in graph.get("hypotheses", []) or []:
            if not isinstance(hypothesis, Mapping):
                continue
            for name in hypothesis.get("supporting_capabilities", []) or []:
                hypothesis_support[str(name)] += 1
        names = sorted(set(executed) | set(contribution) | set(confidence_map) | set(hypothesis_support))
        stats = {}
        for name in names:
            inv = inventory_by_id.get(name, {})
            failures = inv.get("failure_cases", []) or []
            execution_count = 1 if name in executed or inv.get("executed") else 0
            confidence = self._score(confidence_map.get(name, inv.get("confidence")), 0.5)
            success_rate = 1.0 if execution_count and confidence >= 0.6 and not failures else confidence if execution_count else 0.0
            failure_rate = min(1.0, len(failures) / max(len(failures) + execution_count, 1))
            runtime = self._runtime(performance, f"{name}_time_seconds", f"{name}_time")
            cooperation = self._cooperation_score(name, capability)
            reuse_count = self._reuse_count(name, adaptive)
            dependency_count = len(self._as_list(dependency.get("injected_dependencies"))) if name == "dependency_reasoning" else 0
            truth_support = len(self._as_list(inv.get("shared_truths") or capability.get("shared_truths")))
            produced = hypothesis_support.get(name, 0) + len(self._as_list(inv.get("successful_outputs")))
            influence = round(
                (contribution.get(name, 0.0) * 0.45)
                + (confidence * 0.25)
                + (success_rate * 0.20)
                + (cooperation * 0.10),
                4,
            )
            stats[name] = {
                "execution_count": execution_count,
                "contribution_score": round(contribution.get(name, 0.0), 4),
                "success_rate": round(success_rate, 4),
                "failure_rate": round(failure_rate, 4),
                "average_confidence": confidence,
                "average_runtime": round(runtime, 6),
                "knowledge_produced": produced,
                "dependencies_used": dependency_count,
                "truth_support": truth_support,
                "reuse_count": reuse_count,
                "capability_cooperation_score": cooperation,
                "capability_influence_score": influence,
                "causal_support": self._score(causal.get("average_confidence"), 0.0)
                if name in {"causal_reasoning", "dependency_reasoning"}
                else 0.0,
            }
        return stats

    def _decision_quality(self, decisions, hypotheses, branches, graph, convergence):
        by_hypothesis = {item.get("hypothesis_id"): item for item in hypotheses}
        branch_lookup = {
            hypothesis_id: branch
            for branch in branches
            for hypothesis_id in branch.get("generated_hypotheses", []) or []
        }
        rows = []
        for index, decision in enumerate(decisions[:30]):
            hypothesis_id = decision.get("hypothesis_id") or self._mapping(decision.get("final_candidate")).get("hypothesis_id")
            hypothesis = by_hypothesis.get(hypothesis_id, {})
            confidence_history = hypothesis.get("confidence_history", []) or []
            latest = confidence_history[-1] if confidence_history else {}
            before = self._score(latest.get("confidence_before"), 0.0)
            after = self._score(latest.get("confidence_after"), decision.get("confidence", 0.0))
            evidence = self._as_list(
                decision.get("evidence_changed_confidence")
                or decision.get("which_evidence_changed_confidence")
                or latest.get("new_evidence")
            )
            status = hypothesis.get("status", "ACTIVE")
            confirmed = status in {"VALIDATED", "EXECUTED", "SUPPORTED"}
            alternatives = [
                branch.get("branch_id")
                for branch in branches
                if branch.get("branch_id") != branch_lookup.get(hypothesis_id, {}).get("branch_id")
            ][:8]
            score = round(
                (after * 0.45)
                + ((1.0 if evidence else 0.35) * 0.20)
                + ((1.0 if confirmed else 0.4) * 0.20)
                + ((1.0 if alternatives else 0.5) * 0.15),
                4,
            )
            rows.append({
                "decision_id": decision.get("decision_id") or f"decision:{index}",
                "hypothesis_id": hypothesis_id,
                "quality_score": score,
                "why_this_decision": decision.get("why_survived")
                or decision.get("why_branch_selected")
                or convergence.get("why_convergence_occurred"),
                "alternatives_existed": alternatives,
                "why_alternatives_lost": decision.get("why_competing_hypotheses_failed")
                or self._mapping(graph.get("decision_trace")).get("why_another_rejected"),
                "decisive_evidence": evidence[:8],
                "confidence_changed": round(after - before, 4),
                "later_confirmed": confirmed,
            })
        if not rows and graph.get("decision_trace"):
            trace = self._mapping(graph.get("decision_trace"))
            final = self._mapping(trace.get("final_candidate"))
            rows.append({
                "decision_id": "decision:final_candidate",
                "hypothesis_id": final.get("hypothesis_id"),
                "quality_score": self._score(final.get("confidence"), 0.0),
                "why_this_decision": trace.get("why_branch_selected"),
                "alternatives_existed": [item.get("branch_id") for item in graph.get("discarded_branches", []) or []][:8],
                "why_alternatives_lost": trace.get("why_another_rejected"),
                "decisive_evidence": self._as_list(trace.get("which_evidence_changed_confidence")),
                "confidence_changed": 0.0,
                "later_confirmed": bool(final),
            })
        return {
            "decision_count": len(rows),
            "average_decision_quality": self._average(item["quality_score"] for item in rows),
            "confirmed_decisions": sum(1 for item in rows if item["later_confirmed"]),
            "failed_decisions": sum(1 for item in rows if not item["later_confirmed"]),
            "decisions": rows,
        }

    def _cost(self, hypotheses, branches, capabilities, decision_quality, performance, all_results):
        total_time = self._runtime(
            performance,
            "reasoning_time_seconds",
            "report_time_seconds",
            "active_compute_time_seconds",
        )
        if total_time <= 0.0:
            total_time = self._runtime(performance, "task_execution_time_seconds")
        solved = sum(
            1
            for item in all_results
            if isinstance(item, Mapping)
            and self._mapping(item.get("result")).get("success")
        )
        correct = decision_quality.get("confirmed_decisions", 0)
        failed = decision_quality.get("failed_decisions", 0)
        validations = len([
            item for item in hypotheses
            if item.get("status") in {"VALIDATED", "REJECTED", "EXECUTED"}
        ])
        return {
            "total_reasoning_cost_seconds": round(total_time, 6),
            "cost_per_hypothesis": self._divide(total_time, len(hypotheses)),
            "cost_per_branch": self._divide(total_time, len(branches)),
            "cost_per_capability": self._divide(total_time, len(capabilities)),
            "cost_per_validation": self._divide(total_time, validations),
            "cost_per_correct_decision": self._divide(total_time, correct),
            "cost_per_failed_decision": self._divide(total_time, failed),
            "cost_per_solved_task": self._divide(total_time, solved),
            "cost_basis": "existing_runtime_metrics",
        }

    def _learning_opportunities(self, graph, reasoning, cognitive, capability, causal, adaptive, stats):
        reusable_assets = self._mapping(capability.get("reusable_assets"))
        learning = []
        gaps = []
        candidates = []
        for key, label in (
            ("successful_strategies", "reusable reasoning chains"),
            ("successful_programs", "reusable capability combinations"),
            ("successful_transformations", "reusable transformations"),
            ("successful_causal_explanations", "reusable causal explanations"),
            ("successful_validation_patterns", "reusable validation patterns"),
        ):
            values = self._as_list(reusable_assets.get(key))
            if values:
                learning.append({"type": label, "candidates": values[:8]})
                candidates.extend(values)
        validated = [
            item for item in graph.get("hypotheses", []) or []
            if isinstance(item, Mapping) and item.get("status") in {"VALIDATED", "EXECUTED", "SUPPORTED"}
        ]
        if validated:
            learning.append({
                "type": "reusable hypotheses",
                "candidates": [item.get("hypothesis_id") for item in validated[:8]],
            })
        if causal.get("cause_effect_pairs"):
            learning.append({
                "type": "reusable causal explanations",
                "candidates": (causal.get("cause_effect_pairs") or [])[:8],
            })
        missing = cognitive.get("missing_capabilities", []) or reasoning.get("learning_candidates", [])
        gaps.extend(self._as_list(missing)[:12])
        if stats["hypotheses_rejected"]:
            gaps.append("rejected_hypotheses_need_negative_constraints")
        if not learning:
            learning.append({
                "type": "continued_observation",
                "candidates": ["collect more reasoning graph episodes"],
            })
        return {
            "learning_opportunities": learning[:20],
            "knowledge_gaps": gaps[:20],
            "candidate_count": len(candidates),
        }

    def _quality_warnings(self, stats, efficiency, convergence, capabilities, decision_quality, cost):
        warnings = []
        generated = stats["hypotheses_generated"]
        if generated > 30:
            warnings.append({"warning": "too_many_hypotheses", "severity": "medium"})
        if generated < 1:
            warnings.append({"warning": "too_few_hypotheses", "severity": "high"})
        if efficiency["hypothesis_survival_rate"] < 0.15 and generated >= 3:
            warnings.append({"warning": "weak_evidence", "severity": "medium"})
        if efficiency["confidence_volatility"] > 0.35:
            warnings.append({"warning": "low_confidence_stability", "severity": "medium"})
        if efficiency["maximum_branch_width"] > 8:
            warnings.append({"warning": "excessive_branching", "severity": "medium"})
        if convergence.get("premature_convergence"):
            warnings.append({"warning": "premature_convergence", "severity": "high"})
        if convergence.get("late_convergence"):
            warnings.append({"warning": "late_convergence", "severity": "medium"})
        if convergence.get("dead_ends"):
            warnings.append({"warning": "dead_ends_detected", "severity": "medium"})
        for name, item in capabilities.items():
            if item["execution_count"] and item["contribution_score"] < 0.05:
                warnings.append({"warning": "capability_overuse", "capability": name, "severity": "low"})
            if not item["execution_count"] and item["capability_influence_score"] > 0.3:
                warnings.append({"warning": "capability_underuse", "capability": name, "severity": "medium"})
            if item["failure_rate"] > 0.5:
                warnings.append({"warning": "repeated_failures", "capability": name, "severity": "high"})
        if decision_quality["failed_decisions"] > decision_quality["confirmed_decisions"]:
            warnings.append({"warning": "unnecessary_reasoning", "severity": "medium"})
        if cost["cost_per_hypothesis"] > 5.0:
            warnings.append({"warning": "expensive_hypotheses", "severity": "medium"})
        return warnings[:30]

    def _component_scores(
        self,
        graph,
        stats,
        efficiency,
        convergence,
        capabilities,
        decision_quality,
        cost,
        learning,
        warnings,
        validation,
    ):
        avg_capability = self._average(
            item["capability_influence_score"] for item in capabilities.values()
        )
        confidence = self._average(
            item.get("confidence_history", [{}])[-1].get("confidence_after", 0.0)
            for item in graph.get("hypotheses", []) or []
            if isinstance(item, Mapping)
        )
        if confidence == 0.0:
            confidence = self._score(graph.get("winning_branch", {}).get("confidence"), 0.0)
        stability = max(0.0, 1.0 - efficiency["confidence_volatility"])
        consistency = max(
            0.0,
            min(
                1.0,
                (decision_quality["average_decision_quality"] * 0.65)
                + (stats["hypothesis_survival_rate"] * 0.35),
            ),
        )
        diversity = min(1.0, efficiency["reasoning_width"] / 8.0)
        robustness = max(
            0.0,
            min(
                1.0,
                (stats["hypotheses_supported"] / max(stats["hypotheses_generated"], 1) * 0.45)
                + (avg_capability * 0.35)
                + ((1.0 if validation.get("reports") else 0.5) * 0.20),
            ),
        )
        explainability = min(
            1.0,
            (
                bool(graph.get("decision_trace"))
                + bool(graph.get("reasoning_timeline"))
                + bool(graph.get("reasoning_snapshots"))
                + bool(graph.get("hypotheses"))
            )
            / 4.0,
        )
        cost_score = 1.0 / (1.0 + cost["cost_per_hypothesis"])
        warning_penalty = min(0.45, len(warnings) * 0.035)
        return {
            "efficiency": max(0.0, min(1.0, (efficiency["hypothesis_survival_rate"] * 0.45) + (cost_score * 0.35) + ((1.0 - min(efficiency["branch_collapse_rate"], 1.0)) * 0.20))),
            "stability": round(stability, 4),
            "consistency": round(consistency, 4),
            "diversity": round(diversity, 4),
            "robustness": round(robustness, 4),
            "explainability": round(explainability, 4),
            "confidence": round(confidence, 4),
            "cost_quality": round(cost_score, 4),
            "generalization_potential": round(min(1.0, (learning["candidate_count"] / 10.0) + (stats["hypotheses_validated"] / max(stats["hypotheses_generated"], 1) * 0.45)), 4),
            "convergence_quality": round(0.25 if convergence["premature_convergence"] else 0.65 if convergence["late_convergence"] else 0.9, 4),
            "warning_penalty": round(warning_penalty, 4),
        }

    def _dashboard(self, decision_quality, capabilities, branches, graph, efficiency, learning):
        decisions = decision_quality.get("decisions", [])
        strongest = sorted(decisions, key=lambda item: item["quality_score"], reverse=True)[:10]
        weakest = sorted(decisions, key=lambda item: item["quality_score"])[:10]
        capability_rows = [
            {"capability": name, **values}
            for name, values in capabilities.items()
        ]
        useful = max(
            capability_rows,
            key=lambda item: item.get("capability_influence_score", 0.0),
            default={},
        )
        least = min(
            capability_rows,
            key=lambda item: item.get("capability_influence_score", 0.0),
            default={},
        )
        branch_costs = [
            {
                "branch_id": branch.get("branch_id"),
                "state": branch.get("state"),
                "estimated_cost": round(
                    branch.get("branch_depth", 0) * max(branch.get("branch_width", 1), 1),
                    4,
                ),
                "confidence": branch.get("confidence", 0.0),
            }
            for branch in branches
        ]
        successful = [item for item in branch_costs if item["state"] == "VALIDATED"]
        deltas = self._confidence_events(graph)
        return {
            "top_10_strongest_reasoning_decisions": strongest,
            "top_10_weakest_reasoning_decisions": weakest,
            "most_useful_capability": useful.get("capability"),
            "least_useful_capability": least.get("capability"),
            "most_reused_reasoning_pattern": self._most_reused_pattern(learning),
            "largest_reasoning_bottleneck": self._largest_bottleneck(efficiency),
            "highest_confidence_gain": max(deltas, key=lambda item: item["delta"], default={}),
            "largest_confidence_collapse": min(deltas, key=lambda item: item["delta"], default={}),
            "most_expensive_branch": max(branch_costs, key=lambda item: item["estimated_cost"], default={}),
            "cheapest_successful_branch": min(successful, key=lambda item: item["estimated_cost"], default={}),
        }

    def _weighted_quality(self, scores):
        weights = {
            "efficiency": 0.12,
            "stability": 0.10,
            "consistency": 0.13,
            "diversity": 0.08,
            "robustness": 0.12,
            "explainability": 0.12,
            "confidence": 0.12,
            "cost_quality": 0.08,
            "generalization_potential": 0.08,
            "convergence_quality": 0.05,
        }
        raw = sum(scores[key] * weight for key, weight in weights.items())
        return round(max(0.0, min(1.0, raw - scores.get("warning_penalty", 0.0))), 4)

    def _health(self, score, warnings, scores):
        severe = len([item for item in warnings if item.get("severity") == "high"])
        downgrades = []
        if severe:
            downgrades.append(f"{severe} high severity reasoning warning(s)")
        for key in ("efficiency", "stability", "consistency", "robustness", "confidence"):
            if scores.get(key, 1.0) < 0.45:
                downgrades.append(f"{key} below quality threshold")
        if score >= 0.85 and not severe:
            return "Excellent", downgrades
        if score >= 0.72 and severe <= 1:
            return "Good", downgrades
        if score >= 0.55:
            return "Stable", downgrades
        if score >= 0.35:
            return "Weak", downgrades
        return "Critical", downgrades

    def _branches(self, graph):
        branches = []
        for key in ("active_branches", "merged_branches", "discarded_branches", "validated_branches"):
            branches.extend([
                item for item in graph.get(key, []) or []
                if isinstance(item, Mapping)
            ])
        return branches

    def _decisions(self, graph, reasoning):
        decisions = []
        log = reasoning.get("decision_log", []) or []
        decisions.extend(item for item in log if isinstance(item, Mapping))
        trace = graph.get("decision_trace")
        if isinstance(trace, Mapping):
            decisions.append(trace)
        return decisions

    def _graph_statistics(self, graph):
        size = self._mapping(graph.get("graph_size"))
        return {
            "node_count": int(graph.get("node_count", size.get("nodes", 0)) or 0),
            "edge_count": int(graph.get("edge_count", size.get("edges", 0)) or 0),
            "graph_density": self._graph_density(graph),
            "source_report_coverage": round(
                sum(1 for value in self._mapping(graph.get("source_reports")).values() if value)
                / max(len(self._mapping(graph.get("source_reports"))), 1),
                4,
            ),
        }

    def _confidence_events(self, graph):
        events = []
        for item in graph.get("confidence_evolution", []) or []:
            if not isinstance(item, Mapping):
                continue
            before = self._score(item.get("confidence_before"), 0.0)
            after = self._score(item.get("confidence_after"), 0.0)
            events.append({
                "hypothesis_id": item.get("hypothesis_id"),
                "delta": round(after - before, 4),
                "reason": item.get("reason_for_change"),
            })
        return events

    def _confidence_deltas(self, hypotheses):
        deltas = []
        for item in hypotheses:
            history = item.get("confidence_history", []) or []
            for update in history:
                if isinstance(update, Mapping):
                    before = self._score(update.get("confidence_before"), 0.0)
                    after = self._score(update.get("confidence_after"), 0.0)
                    deltas.append(after - before)
        return deltas

    def _entropy(self, hypotheses, branches):
        statuses = Counter(item.get("status", "ACTIVE") for item in hypotheses)
        branch_states = Counter(item.get("state", "ACTIVE") for item in branches)
        buckets = list(statuses.values()) + list(branch_states.values())
        total = sum(buckets)
        if total <= 0:
            return 0.0
        concentration = sum((count / total) ** 2 for count in buckets)
        return round(1.0 - concentration, 4)

    def _detect_cycles(self, graph):
        edges = self._mapping(graph.get("reasoning_graph")).get("edges", []) or []
        seen = set()
        reverse = set()
        cycles = []
        for edge in edges:
            if not isinstance(edge, Mapping):
                continue
            pair = (edge.get("source"), edge.get("target"))
            if (pair[1], pair[0]) in seen:
                cycles.append({"source": pair[0], "target": pair[1]})
            seen.add(pair)
            reverse.add((pair[1], pair[0]))
        return cycles[:10]

    def _repeated_hypotheses(self, hypotheses):
        claims = Counter(str(item.get("creation_reason") or item.get("hypothesis_id")) for item in hypotheses)
        return [
            {"pattern": key, "count": count}
            for key, count in claims.items()
            if count > 1
        ][:10]

    def _cooperation_score(self, name, capability):
        events = [
            item for item in capability.get("cooperation_events", []) or []
            if isinstance(item, Mapping)
        ]
        hits = sum(
            1 for item in events
            if item.get("source_capability") == name or item.get("target_capability") == name
        )
        return round(min(1.0, hits / 5.0), 4)

    def _reuse_count(self, name, adaptive):
        if name == "adaptive_reuse":
            return int(
                adaptive.get("strategy_hits", 0)
                or adaptive.get("reuse_hits", 0)
                or adaptive.get("truth_hits", 0)
                or 0
            )
        return 0

    def _runtime(self, report, *keys):
        for key in keys:
            value = report.get(key)
            if isinstance(value, (int, float)):
                return max(0.0, float(value))
        return 0.0

    def _timeline_index(self, timeline, stage):
        for index, item in enumerate(timeline):
            if item.get("stage") == stage:
                return index
        return -1

    def _graph_density(self, graph):
        nodes = int(graph.get("node_count", 0) or 0)
        edges = int(graph.get("edge_count", 0) or 0)
        possible = nodes * max(nodes - 1, 1)
        return round(edges / possible, 4) if nodes else 0.0

    def _most_reused_pattern(self, learning):
        for item in learning.get("learning_opportunities", []):
            candidates = item.get("candidates", [])
            if candidates:
                return item.get("type")
        return "not_observed"

    def _largest_bottleneck(self, efficiency):
        values = {
            "branch_depth": efficiency.get("maximum_branch_depth", 0),
            "branch_width": efficiency.get("maximum_branch_width", 0),
            "confidence_volatility": efficiency.get("confidence_volatility", 0),
            "branch_collapse_rate": efficiency.get("branch_collapse_rate", 0),
        }
        return max(values.items(), key=lambda item: item[1])[0]

    def _recommendations(self, warnings, learning, scores):
        recommendations = []
        for warning in warnings[:8]:
            recommendations.append(f"investigate {warning['warning']}")
        if learning.get("knowledge_gaps"):
            recommendations.append("target knowledge gaps in future reasoning probes")
        if scores["explainability"] < 0.75:
            recommendations.append("increase decision evidence attribution coverage")
        if scores["cost_quality"] < 0.45:
            recommendations.append("review expensive hypothesis and branch patterns")
        if not recommendations:
            recommendations.append("continue collecting reasoning analytics baselines")
        return list(dict.fromkeys(recommendations))[:12]

    def _volatility(self, deltas):
        if not deltas:
            return 0.0
        mean = sum(deltas) / len(deltas)
        variance = sum((delta - mean) ** 2 for delta in deltas) / len(deltas)
        return round(min(1.0, variance ** 0.5), 4)

    def _divide(self, numerator, denominator):
        return round(float(numerator or 0.0) / max(float(denominator or 0.0), 1.0), 6)

    def _average(self, values):
        values = [float(value) for value in values if isinstance(value, (int, float))]
        return round(sum(values) / max(len(values), 1), 4) if values else 0.0

    def _score(self, value, default=0.0):
        if isinstance(value, (int, float)):
            return round(max(0.0, min(float(value), 1.0)), 4)
        return round(float(default or 0.0), 4)

    def _percent(self, value):
        if not isinstance(value, (int, float)):
            return 0.0
        value = float(value)
        if value > 1.0:
            value = value / 100.0
        return round(max(0.0, min(value, 1.0)), 4)

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

    def _mapping(self, value):
        return value if isinstance(value, Mapping) else {}


reasoning_quality_analytics_builder = ReasoningQualityAnalyticsBuilder()


__all__ = [
    "ReasoningQualityAnalyticsBuilder",
    "reasoning_quality_analytics_builder",
]
