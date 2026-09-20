"""Deterministic cognitive analytics assembled from existing runtime reports."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable, Mapping


class CognitiveAnalyticsBuilder:
    """Observe cognition by reducing reports already produced by the runtime."""

    system_name = "cognitive_analytics_builder"

    HYPOTHESIS_KEYS = {
        "hypotheses",
        "generated_hypotheses",
        "validated_hypotheses",
        "rejected_hypotheses",
        "alternative_hypotheses",
        "ranked_hypotheses",
        "candidate_hypotheses",
        "epistemic_hypotheses",
    }
    REPORT_KEYS = {
        "hypothesis_generation_report",
        "HYPOTHESIS GENERATION REPORT",
        "cognitive_capability_report",
        "COGNITIVE_CAPABILITY_REPORT",
        "causal_context_report",
        "CAUSAL_CONTEXT_REPORT",
        "counterfactual_reasoning_report",
        "COUNTERFACTUAL REASONING REPORT",
        "adaptive_reuse_report",
        "ADAPTIVE_REUSE_REPORT",
        "context_validation_report",
        "CONTEXT VALIDATION REPORT",
        "performance_report",
        "PERFORMANCE_REPORT",
    }
    CONFIDENCE_KEYS = (
        "confidence",
        "capability_confidence",
        "average_confidence",
        "mapping_confidence",
        "causal_confidence",
        "validation_score",
        "score",
        "final_score",
        "accuracy",
    )

    def build_report(
        self,
        *,
        task_count: int = 0,
        successful_tasks: int = 0,
        failed_tasks: int = 0,
        all_results: Iterable[Mapping[str, Any]] | None = None,
        training_report: Mapping[str, Any] | None = None,
        concept_lifecycle_report: Mapping[str, Any] | None = None,
        performance_report: Mapping[str, Any] | None = None,
        cognitive_capability_report: Mapping[str, Any] | None = None,
        causal_context_report: Mapping[str, Any] | None = None,
        adaptive_reuse_report: Mapping[str, Any] | None = None,
        context_validation_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        sources = self._sources(
            all_results=all_results,
            training_report=training_report,
            concept_lifecycle_report=concept_lifecycle_report,
            performance_report=performance_report,
            cognitive_capability_report=cognitive_capability_report,
            causal_context_report=causal_context_report,
            adaptive_reuse_report=adaptive_reuse_report,
            context_validation_report=context_validation_report,
        )
        hypotheses = self._collect_hypotheses(sources)
        capabilities = self._capabilities(cognitive_capability_report or {}, performance_report or {})
        branches = self._reasoning_branches(hypotheses, causal_context_report or {})
        confidence_values = self._confidence_values(hypotheses, capabilities, sources)
        contribution = self._capability_contribution(capabilities, hypotheses, causal_context_report or {})
        hypothesis_statistics = self._hypothesis_statistics(hypotheses)
        reasoning_width = max(
            hypothesis_statistics["hypotheses_generated"],
            len(branches),
            len(capabilities["capabilities_executed"]),
        )
        reasoning_depth = self._reasoning_depth(causal_context_report or {}, performance_report or {}, branches)
        reasoning_iterations = self._reasoning_iterations(hypotheses, branches, performance_report or {})
        reasoning_efficiency = self._reasoning_efficiency(
            successful_tasks,
            failed_tasks,
            reasoning_iterations,
            hypothesis_statistics,
        )
        convergence_points, divergence_points = self._convergence(
            hypotheses,
            branches,
            contribution,
        )
        missing_capabilities = self._missing_capabilities(capabilities)
        failure_analytics = self._failure_analytics(
            failed_tasks,
            capabilities,
            hypothesis_statistics,
            missing_capabilities,
        )
        learning = self._learning_opportunities(
            adaptive_reuse_report or {},
            cognitive_capability_report or {},
            causal_context_report or {},
            hypothesis_statistics,
            missing_capabilities,
        )
        winning_path = branches[0] if branches else {}
        decisive = contribution[0]["capability"] if contribution else "unknown"

        return {
            "system": self.system_name,
            "COGNITIVE_ANALYTICS_REPORT": True,
            "task": {
                "task_count": int(task_count or 0),
                "successful_tasks": int(successful_tasks or 0),
                "failed_tasks": int(failed_tasks or 0),
            },
            "cognitive_lifecycle": self._lifecycle(hypothesis_statistics, capabilities, causal_context_report or {}),
            "reasoning_summary": self._summary(
                hypothesis_statistics,
                capabilities,
                reasoning_depth,
                reasoning_width,
                decisive,
                winning_path,
            ),
            "reasoning_depth": reasoning_depth,
            "reasoning_width": reasoning_width,
            "branching_factor": round(reasoning_width / max(reasoning_depth, 1), 4),
            "reasoning_iterations": reasoning_iterations,
            "reasoning_convergence": convergence_points[0] if convergence_points else "not_observed",
            "reasoning_efficiency": reasoning_efficiency,
            "average_confidence": self._average(confidence_values),
            "confidence_growth": self._confidence_growth(confidence_values),
            "hypothesis_statistics": hypothesis_statistics,
            "hypotheses": hypotheses[:25],
            "capability_statistics": capabilities,
            "capability_contribution": contribution,
            "reasoning_graph": {
                "nodes": self._graph_nodes(hypotheses, capabilities),
                "edges": self._graph_edges(hypotheses, branches, contribution),
                "branches": branches[:25],
            },
            "convergence_points": convergence_points,
            "divergence_points": divergence_points,
            "failure_analytics": failure_analytics,
            "learning_opportunities": learning["learning_opportunities"],
            "knowledge_candidates": learning["knowledge_candidates"],
            "missing_capabilities": missing_capabilities,
            "recommended_improvements": self._recommended_improvements(
                missing_capabilities,
                failure_analytics,
                learning["learning_opportunities"],
            ),
            "task_intelligence": {
                "why_succeeded": self._why_succeeded(successful_tasks, contribution, winning_path),
                "winning_reasoning_path": winning_path.get("branch_id", "not_observed"),
                "lost_alternatives": [
                    item.get("hypothesis_id")
                    for item in hypotheses
                    if item.get("validation_status") == "rejected"
                ][:10],
                "decisive_capability": decisive,
            },
        }

    def _sources(self, **named_sources):
        sources = []
        all_results = named_sources.pop("all_results", None) or []
        for item in all_results:
            result = item.get("result", {}) if isinstance(item, Mapping) else {}
            if isinstance(result, Mapping):
                sources.append(result)
                for key in self.REPORT_KEYS:
                    report = result.get(key)
                    if isinstance(report, Mapping):
                        sources.append(report)
        for source in named_sources.values():
            if isinstance(source, Mapping) and source:
                sources.append(source)
        return sources

    def _collect_hypotheses(self, sources):
        seen = set()
        hypotheses = []
        for source in sources:
            for key, value in self._walk(source):
                if key not in self.HYPOTHESIS_KEYS:
                    continue
                items = value.values() if isinstance(value, Mapping) else value
                if not isinstance(items, Iterable) or isinstance(items, (str, bytes)):
                    continue
                for item in items:
                    if not isinstance(item, Mapping):
                        continue
                    normalized = self._normalize_hypothesis(item, key)
                    identity = normalized["hypothesis_id"]
                    if identity in seen:
                        continue
                    seen.add(identity)
                    hypotheses.append(normalized)
        return hypotheses

    def _normalize_hypothesis(self, item, source_key):
        item = dict(item)
        hypothesis_id = str(
            item.get("hypothesis_id")
            or item.get("id")
            or item.get("strategy_id")
            or item.get("capability_id")
            or item.get("concept")
            or f"{source_key}:{len(str(item))}"
        )
        confidence = self._score(
            item.get("confidence"),
            item.get("prior_confidence"),
            item.get("calibrated_confidence"),
            item.get("score"),
            item.get("support_score"),
        )
        status = str(
            item.get("validation_status")
            or item.get("status")
            or ("validated" if source_key == "validated_hypotheses" else "rejected" if source_key == "rejected_hypotheses" else "candidate")
        ).lower()
        status = self._canonical_status(status)
        required = item.get("required_capabilities") or item.get("capabilities") or []
        if isinstance(required, str):
            required = [required]
        capability = item.get("capability_id")
        if capability and capability not in required:
            required = [capability, *required]
        return {
            "hypothesis_id": hypothesis_id,
            "claim": item.get("claim") or item.get("hypothesis") or item.get("concept") or hypothesis_id,
            "creation_reason": item.get("creation_reason") or item.get("source") or source_key,
            "supporting_evidence": item.get("supporting_evidence") or item.get("evidence") or [],
            "confidence": confidence,
            "required_capabilities": sorted({str(value) for value in required}),
            "rejection_reason": item.get("rejection_reason") or item.get("failure_reason") or "",
            "validation_status": status,
        }

    def _capabilities(self, report, performance_report):
        report = report if isinstance(report, Mapping) else {}
        inventory = [
            dict(item)
            for item in report.get("capability_inventory", []) or []
            if isinstance(item, Mapping)
        ]
        executed = list(report.get("capabilities_executed", []) or [])
        confidence = report.get("capability_confidence", {}) or {}
        failures = report.get("capability_failures", []) or []
        cooperation = report.get("cooperation_events", []) or []
        runtime = {
            capability: round(float(performance_report.get(f"{capability}_time_seconds", 0.0) or 0.0), 4)
            for capability in executed
        }
        return {
            "capabilities_executed": executed,
            "capability_runtime": runtime,
            "capability_success": [
                item.get("capability_id")
                for item in inventory
                if item.get("executed") and float(item.get("confidence", 0.0) or 0.0) >= 0.6
            ],
            "capability_failure": failures,
            "capability_confidence": confidence,
            "capability_contribution": {},
            "capability_dependencies": {
                item.get("capability_id"): item.get("potential_cooperation", [])
                for item in inventory
                if item.get("capability_id")
            },
            "capability_cooperation": cooperation,
            "capability_inventory": inventory,
        }

    def _capability_contribution(self, capabilities, hypotheses, causal_report):
        weights = Counter()
        for item in capabilities["capability_inventory"]:
            capability = item.get("capability_id")
            if capability:
                weights[capability] += float(item.get("confidence", 0.0) or 0.0) * (1.5 if item.get("executed") else 0.35)
        for hypothesis in hypotheses:
            multiplier = 1.4 if hypothesis["validation_status"] == "validated" else 0.5
            for capability in hypothesis.get("required_capabilities", []):
                weights[capability] += hypothesis["confidence"] * multiplier
        if causal_report.get("CAUSAL_CONTEXT_REPORT"):
            weights["causal_reasoning"] += float(causal_report.get("average_confidence", 0.0) or 0.0)
            weights["dependency_reasoning"] += float(causal_report.get("causal_chain_depth", 0.0) or 0.0) * 0.1
        total = sum(weights.values())
        if total <= 0.0:
            return []
        return [
            {
                "capability": capability,
                "contribution_percent": round((weight / total) * 100.0, 2),
            }
            for capability, weight in sorted(weights.items(), key=lambda pair: (-pair[1], pair[0]))
        ][:12]

    def _hypothesis_statistics(self, hypotheses):
        statuses = Counter(item["validation_status"] for item in hypotheses)
        generated = len(hypotheses)
        validated = statuses.get("validated", 0)
        rejected = statuses.get("rejected", 0) + statuses.get("failed", 0)
        merged = statuses.get("merged", 0)
        reactivated = statuses.get("reactivated", 0)
        return {
            "hypotheses_generated": generated,
            "hypotheses_validated": validated,
            "hypotheses_rejected": rejected,
            "hypotheses_merged": merged,
            "hypotheses_reactivated": reactivated,
            "hypotheses_remaining": max(0, generated - validated - rejected - merged),
        }

    def _reasoning_branches(self, hypotheses, causal_report):
        branches = []
        for index, hypothesis in enumerate(hypotheses[:30]):
            final_result = (
                "dominant"
                if hypothesis["validation_status"] == "validated"
                else "abandoned"
                if hypothesis["validation_status"] == "rejected"
                else "candidate"
            )
            branches.append({
                "branch_id": f"branch:{index}:{hypothesis['hypothesis_id']}",
                "starting_assumption": hypothesis["claim"],
                "supporting_observations": hypothesis["supporting_evidence"],
                "intermediate_decisions": [
                    "hypothesis_generated",
                    f"validation_status:{hypothesis['validation_status']}",
                ],
                "causal_links": [],
                "truth_validation": hypothesis["validation_status"],
                "final_result": final_result,
            })
        links = causal_report.get("cause_effect_pairs", []) or []
        for index, link in enumerate(links[:10]):
            if not isinstance(link, Mapping):
                continue
            branches.append({
                "branch_id": f"causal_branch:{index}",
                "starting_assumption": link.get("cause") or link.get("cause_id") or "causal_relation",
                "supporting_observations": [link],
                "intermediate_decisions": ["causal_relation_observed"],
                "causal_links": [link],
                "truth_validation": "validated" if float(link.get("confidence", 0.0) or 0.0) >= 0.5 else "candidate",
                "final_result": link.get("effect") or link.get("effect_id") or "causal_effect",
            })
        return branches

    def _reasoning_depth(self, causal_report, performance_report, branches):
        return int(max(
            float(causal_report.get("causal_chain_depth", 0) or 0),
            float(causal_report.get("average_chain_depth", 0) or 0),
            float(performance_report.get("dependency_chain_depth", 0) or 0),
            1 if branches else 0,
        ))

    def _reasoning_iterations(self, hypotheses, branches, performance_report):
        explicit = int(float(performance_report.get("reasoning_iterations", 0) or 0))
        return max(explicit, len(hypotheses), len(branches))

    def _reasoning_efficiency(self, successful_tasks, failed_tasks, iterations, stats):
        solved = int(successful_tasks or 0)
        total_tasks = solved + int(failed_tasks or 0)
        success_signal = solved / max(total_tasks, 1)
        validation_signal = stats["hypotheses_validated"] / max(stats["hypotheses_generated"], 1)
        iteration_penalty = 1.0 / max(iterations, 1)
        return round((success_signal * 0.55) + (validation_signal * 0.35) + (iteration_penalty * 0.10), 4)

    def _confidence_values(self, hypotheses, capabilities, sources):
        values = [item["confidence"] for item in hypotheses if item["confidence"] > 0.0]
        values.extend(
            float(value)
            for value in capabilities["capability_confidence"].values()
            if isinstance(value, (int, float))
        )
        for source in sources:
            for key, value in self._walk(source):
                if key in self.CONFIDENCE_KEYS and isinstance(value, (int, float)):
                    values.append(float(value))
        return [max(0.0, min(float(value), 1.0)) for value in values]

    def _convergence(self, hypotheses, branches, contribution):
        dominant = [
            item["hypothesis_id"]
            for item in sorted(hypotheses, key=lambda value: (-value["confidence"], value["hypothesis_id"]))
            if item["validation_status"] in {"validated", "accepted"}
        ][:5]
        convergence = dominant or [
            item["capability"]
            for item in contribution[:3]
        ]
        divergence = [
            branch["branch_id"]
            for branch in branches
            if branch.get("final_result") == "abandoned"
        ][:10]
        return convergence, divergence

    def _missing_capabilities(self, capabilities):
        missing = []
        for item in capabilities["capability_inventory"]:
            if item.get("executed"):
                continue
            patterns = item.get("missing_reasoning_patterns", []) or []
            if patterns:
                missing.append({
                    "capability": item.get("capability_id"),
                    "missing_reasoning_patterns": patterns[:5],
                    "confidence": item.get("confidence", 0.0),
                })
        return missing[:10]

    def _failure_analytics(self, failed_tasks, capabilities, stats, missing_capabilities):
        capability_failures = capabilities.get("capability_failure", [])
        return {
            "reasoning_failed": bool(failed_tasks or capability_failures or stats["hypotheses_rejected"]),
            "failed_capabilities": capability_failures,
            "missing_information": [
                item["capability"]
                for item in missing_capabilities
                if item.get("confidence", 0.0) < 0.45
            ],
            "missing_concepts": [
                pattern
                for item in missing_capabilities
                for pattern in item.get("missing_reasoning_patterns", [])[:2]
            ][:12],
            "missing_transformations": [
                pattern
                for item in missing_capabilities
                if "transformation" in str(item.get("capability", ""))
                for pattern in item.get("missing_reasoning_patterns", [])
            ][:8],
            "possible_improvements": [
                "capture explicit hypothesis rejection reasons",
                "increase validation evidence for low-confidence capabilities",
            ] if stats["hypotheses_rejected"] else [],
        }

    def _learning_opportunities(self, adaptive_reuse_report, capability_report, causal_report, stats, missing):
        reusable = capability_report.get("reusable_assets", {}) if isinstance(capability_report, Mapping) else {}
        opportunities = []
        if adaptive_reuse_report.get("reuse_success_rate", 0.0):
            opportunities.append("promote high-success adaptive reuse strategies")
        if causal_report.get("causal_relation_count", 0):
            opportunities.append("persist validated causal chains as reusable reasoning paths")
        if stats["hypotheses_rejected"]:
            opportunities.append("mine rejected hypotheses for negative training constraints")
        if missing:
            opportunities.append("target weak capability patterns in future ARC curriculum")
        candidates = []
        for key in (
            "successful_strategies",
            "successful_programs",
            "successful_transformations",
            "successful_causal_explanations",
            "successful_validation_patterns",
        ):
            candidates.extend(reusable.get(key, []) or [])
        candidates.extend(adaptive_reuse_report.get("knowledge_growth", {}).get("new_knowledge_candidates", []) or [])
        return {
            "learning_opportunities": opportunities,
            "knowledge_candidates": candidates[:20],
        }

    def _recommended_improvements(self, missing, failure, opportunities):
        recommendations = list(opportunities[:5])
        if missing:
            recommendations.append("add task probes for missing capability patterns")
        if failure.get("failed_capabilities"):
            recommendations.append("attach failure reasons to capability reports")
        if not recommendations:
            recommendations.append("continue collecting cognitive traces across adaptive runs")
        return recommendations

    def _lifecycle(self, stats, capabilities, causal_report):
        return {
            "task": "observed",
            "perception": "observed_via_task_reports",
            "hypothesis_generation": stats["hypotheses_generated"],
            "hypothesis_ranking": "observed" if stats["hypotheses_generated"] else "not_observed",
            "capability_selection": capabilities["capabilities_executed"],
            "capability_cooperation": len(capabilities["capability_cooperation"]),
            "reasoning": "observed",
            "prediction": "observed_via_performance_reports",
            "validation": stats["hypotheses_validated"],
            "final_solution": "observed_via_task_success_metrics",
            "causal_runtime": bool(causal_report.get("CAUSAL_CONTEXT_REPORT")),
        }

    def _summary(self, stats, capabilities, depth, width, decisive, winning_path):
        return (
            f"Observed {stats['hypotheses_generated']} hypotheses across "
            f"{len(capabilities['capabilities_executed'])} executed capabilities; "
            f"reasoning depth {depth}, width {width}. "
            f"Dominant capability: {decisive}. "
            f"Winning path: {winning_path.get('branch_id', 'not_observed')}."
        )

    def _why_succeeded(self, successful_tasks, contribution, winning_path):
        if not successful_tasks:
            return "success_not_observed"
        if contribution:
            return f"{contribution[0]['capability']} carried the strongest evidence contribution."
        if winning_path:
            return f"{winning_path.get('branch_id')} reached validated status."
        return "task success observed, but cognitive attribution was sparse"

    def _graph_nodes(self, hypotheses, capabilities):
        nodes = [
            {"id": item["hypothesis_id"], "type": "hypothesis", "status": item["validation_status"]}
            for item in hypotheses[:40]
        ]
        nodes.extend(
            {"id": capability, "type": "capability"}
            for capability in capabilities["capabilities_executed"]
        )
        return nodes

    def _graph_edges(self, hypotheses, branches, contribution):
        edges = []
        for hypothesis in hypotheses[:40]:
            for capability in hypothesis.get("required_capabilities", []):
                edges.append({
                    "source": capability,
                    "target": hypothesis["hypothesis_id"],
                    "relation": "supports",
                })
        for branch in branches[:20]:
            edges.append({
                "source": branch["starting_assumption"],
                "target": branch["branch_id"],
                "relation": "reasoning_branch",
            })
        for item in contribution[:5]:
            edges.append({
                "source": item["capability"],
                "target": "final_solution",
                "relation": "contributes",
                "weight": item["contribution_percent"],
            })
        return edges

    def _walk(self, value, depth=0):
        if depth > 5 or not isinstance(value, Mapping):
            return
        for key, child in value.items():
            yield key, child
            if isinstance(child, Mapping):
                yield from self._walk(child, depth + 1)

    def _score(self, *values):
        for value in values:
            if isinstance(value, (int, float)):
                return round(max(0.0, min(float(value), 1.0)), 4)
        return 0.0

    def _canonical_status(self, status):
        if status in {
            "accepted",
            "accepted_hypothesis",
            "valid",
            "validated_hypothesis",
            "success",
            "successful",
        }:
            return "validated"
        if status in {
            "rejected_hypothesis",
            "invalid",
            "failure",
            "failed_hypothesis",
            "discarded",
            "abandoned",
        }:
            return "rejected"
        if status in {"merged_hypothesis"}:
            return "merged"
        if status in {"reactivated_hypothesis"}:
            return "reactivated"
        return status

    def _average(self, values):
        return round(sum(values) / max(len(values), 1), 4) if values else 0.0

    def _confidence_growth(self, values):
        if len(values) < 2:
            return 0.0
        midpoint = max(1, len(values) // 2)
        early = self._average(values[:midpoint])
        late = self._average(values[midpoint:])
        return round(late - early, 4)


cognitive_analytics_builder = CognitiveAnalyticsBuilder()


__all__ = [
    "CognitiveAnalyticsBuilder",
    "cognitive_analytics_builder",
]
