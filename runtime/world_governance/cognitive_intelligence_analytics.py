"""Cognitive Intelligence Analytics for NEXRYN operational intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


ANALYTIC_DOMAINS: tuple[str, ...] = (
    "execution",
    "runtime",
    "reasoning",
    "search",
    "concept",
    "program",
    "evidence",
    "knowledge",
    "truth",
    "memory",
    "policy",
    "decision",
    "governance",
    "resource",
    "performance",
    "learning",
    "trend",
    "predictive",
    "optimization",
)


@dataclass
class AnalyticsHistory:
    report_count: int = 0
    average_intelligence_score: float = 0.0
    average_execution_quality: float = 0.0
    average_decision_quality: float = 0.0
    average_policy_quality: float = 0.0
    average_truth_health: float = 0.0
    average_memory_health: float = 0.0

    def update(self, report: Mapping[str, Any]) -> None:
        kpis = report.get("Cognitive KPIs", {})
        self.report_count += 1
        self.average_intelligence_score = self._avg(
            self.average_intelligence_score,
            kpis.get("Overall Cognitive Intelligence", 0.0),
        )
        self.average_execution_quality = self._avg(
            self.average_execution_quality,
            kpis.get("Execution Intelligence", 0.0),
        )
        self.average_decision_quality = self._avg(
            self.average_decision_quality,
            kpis.get("Decision Intelligence", 0.0),
        )
        self.average_policy_quality = self._avg(
            self.average_policy_quality,
            kpis.get("Policy Intelligence", 0.0),
        )
        self.average_truth_health = self._avg(
            self.average_truth_health,
            kpis.get("Truth Intelligence", 0.0),
        )
        self.average_memory_health = self._avg(
            self.average_memory_health,
            kpis.get("Memory Intelligence", 0.0),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "report_count": self.report_count,
            "average_intelligence_score": round(self.average_intelligence_score, 3),
            "average_execution_quality": round(self.average_execution_quality, 3),
            "average_decision_quality": round(self.average_decision_quality, 3),
            "average_policy_quality": round(self.average_policy_quality, 3),
            "average_truth_health": round(self.average_truth_health, 3),
            "average_memory_health": round(self.average_memory_health, 3),
        }

    def _avg(self, current: float, value: Any) -> float:
        value = _score(value)
        return current + (value - current) / max(1, self.report_count)


class CognitiveIntelligenceAnalytics:
    """Interprets cognitive telemetry into insights and optimization signals."""

    def __init__(self) -> None:
        self.analytics_reports: list[dict[str, Any]] = []
        self.history = AnalyticsHistory()

    def analyze(
        self,
        telemetry: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        signals = self._normalize_signals(telemetry or {})
        execution = self._execution_health(signals)
        reasoning = self._reasoning_health(signals)
        search = self._search_health(signals)
        concept = self._concept_health(signals)
        program = self._program_health(signals)
        evidence = self._evidence_health(signals)
        knowledge = self._knowledge_health(signals)
        truth = self._truth_health(signals)
        memory = self._memory_health(signals)
        decision = self._decision_health(signals)
        policy = self._policy_health(signals)
        governance = self._governance_health(signals)
        resources = self._resource_health(signals)
        kpis = self._cognitive_kpis(
            execution,
            reasoning,
            search,
            concept,
            program,
            evidence,
            knowledge,
            truth,
            memory,
            decision,
            policy,
            governance,
            resources,
        )
        anomalies = self._detect_anomalies(
            execution,
            reasoning,
            search,
            evidence,
            truth,
            memory,
            decision,
            policy,
            governance,
            resources,
        )
        root_cause = self._root_cause_analysis(anomalies, signals)
        optimization = self._optimization_opportunities(
            anomalies,
            execution,
            search,
            truth,
            memory,
            decision,
            policy,
            resources,
        )
        predictions = self._predictive_analysis(kpis)
        trends = self._trend_analysis(kpis)
        recommendations = self._recommended_actions(optimization, root_cause)
        report = {
            "COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT": {
                "Executive Summary": self._executive_summary(kpis, anomalies),
                "Cognitive KPIs": kpis,
                "Execution Health": execution,
                "Reasoning Health": reasoning,
                "Search Health": search,
                "Concept Health": concept,
                "Program Health": program,
                "Evidence Health": evidence,
                "Knowledge Health": knowledge,
                "Truth Health": truth,
                "Memory Health": memory,
                "Decision Health": decision,
                "Policy Health": policy,
                "Governance Health": governance,
                "Resource Health": resources,
                "Trend Analysis": trends,
                "Predictive Analysis": predictions,
                "Root Cause Analysis": root_cause,
                "Detected Anomalies": anomalies,
                "Optimization Opportunities": optimization,
                "Recommended Actions": recommendations,
                "World Model Readiness": self._world_model_readiness(kpis, truth, knowledge),
                "DNA Evolution Readiness": self._dna_readiness(kpis, decision, policy),
                "Overall Cognitive Intelligence Score": kpis[
                    "Overall Cognitive Intelligence"
                ],
                "Meta Analytics": self._meta_analytics(kpis, recommendations),
                "Observability Fusion": {
                    "domains_fused": list(ANALYTIC_DOMAINS),
                    "signal_keys": sorted(signals.keys()),
                    "telemetry_interpreted": True,
                },
            }
        }
        self.analytics_reports.append(report)
        self.history.update(report["COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT"])
        return report

    def build_report(self) -> dict[str, Any]:
        latest = self.analytics_reports[-1] if self.analytics_reports else {}
        return {
            "COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT": latest.get(
                "COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT",
                {},
            ),
            "analytics_report_count": len(self.analytics_reports),
            "analytics_history": self.history.as_dict(),
        }

    def reset(self) -> None:
        self.analytics_reports.clear()
        self.history = AnalyticsHistory()

    def _normalize_signals(self, telemetry: Mapping[str, Any]) -> dict[str, Any]:
        signals = dict(telemetry)
        executive = dict(signals.get("WORLD_GOVERNANCE_EXECUTIVE_REPORT") or {})
        policy = dict(signals.get("COGNITIVE_POLICY_REPORT") or {})
        decision = dict(signals.get("COGNITIVE_DECISION_INTELLIGENCE_REPORT") or {})
        signals.setdefault("execution_progress", _nested(executive, "Execution Deviations", "execution_progress", default=0.0))
        signals.setdefault("resource_consumption", _nested(executive, "Execution Deviations", "resource_consumption", default=0.0))
        signals.setdefault("confidence_values", _nested(executive, "Execution Deviations", "confidence_evolution", default=[]))
        signals.setdefault("truth_growth", _nested(executive, "Execution Deviations", "truth_growth", default=0.0))
        signals.setdefault("evidence_growth", _nested(executive, "Execution Deviations", "evidence_growth", default=0.0))
        signals.setdefault("knowledge_density", _nested(executive, "Execution Deviations", "knowledge_density", default=0.0))
        signals.setdefault("activated_runtime_count", len(executive.get("Activated Runtimes", [])))
        signals.setdefault("skipped_runtime_count", len(executive.get("Skipped Runtimes", [])))
        signals.setdefault("policy_confidence", policy.get("Policy Confidence", 0.0))
        signals.setdefault("policy_selection_score", policy.get("Selection Score", 0.0))
        signals.setdefault("decision_utility", _nested(decision, "Selected Decision", "Decision Utility", default=0.0))
        signals.setdefault("decision_confidence", _nested(decision, "Decision Confidence", "Decision Confidence", default=0.0))
        signals.setdefault("decision_prediction_error", signals.get("prediction_error", 0.0))
        return signals

    def _execution_health(self, signals: Mapping[str, Any]) -> dict[str, Any]:
        progress = _score(signals.get("execution_progress"))
        confidence = _average(signals.get("confidence_values", []))
        resource = _score(signals.get("resource_consumption"))
        stability = _clamp(1.0 - abs(confidence - progress) * 0.5)
        efficiency = _clamp(progress * 0.7 + (1.0 - resource) * 0.3)
        quality = _clamp(confidence * 0.4 + progress * 0.35 + efficiency * 0.25)
        return {
            "Execution Quality": round(quality, 3),
            "Execution Stability": round(stability, 3),
            "Execution Consistency": round(_clamp(1.0 - signals.get("skipped_runtime_count", 0) * 0.08), 3),
            "Execution Complexity": round(_clamp(signals.get("activated_runtime_count", 0) / 8.0), 3),
            "Execution Efficiency": round(efficiency, 3),
            "Execution Variability": round(_clamp(abs(confidence - progress)), 3),
            "Execution Predictability": round(_clamp(stability * confidence), 3),
            "Execution Maturity": round(_clamp((quality + stability) / 2.0), 3),
            "Execution Intelligence Score": round(quality, 3),
            "Analytical Conclusion": _banded_text(
                quality,
                "execution is underperforming and needs governance review",
                "execution is functional but optimization opportunities remain",
                "execution is mature and predictable",
            ),
        }

    def _reasoning_health(self, signals: Mapping[str, Any]) -> dict[str, Any]:
        depth = _score(signals.get("reasoning_depth", signals.get("expected_reasoning_depth", 0.5)))
        breadth = _score(signals.get("reasoning_breadth", signals.get("activated_runtime_count", 0) / 8.0))
        cost = _score(signals.get("reasoning_cost", signals.get("resource_consumption", 0.0)))
        confidence = _average(signals.get("confidence_values", []))
        efficiency = _clamp(confidence * 0.65 + (1.0 - cost) * 0.35)
        return {
            "Reasoning Depth": round(depth, 3),
            "Reasoning Breadth": round(breadth, 3),
            "Reasoning Efficiency": round(efficiency, 3),
            "Reasoning Stability": round(_clamp(1.0 - abs(depth - confidence) * 0.4), 3),
            "Reasoning Cost": round(cost, 3),
            "Reasoning Diversity": round(breadth, 3),
            "Reasoning Confidence": round(confidence, 3),
            "Reasoning Convergence": round(_clamp(confidence - cost * 0.2), 3),
            "Reasoning Redundancy": round(_score(signals.get("reasoning_redundancy", 0.0)), 3),
            "Reasoning Quality": round(efficiency, 3),
            "Analytical Conclusion": _banded_text(
                efficiency,
                "reasoning cost is too high for its confidence",
                "reasoning is adequate but may benefit from calibration",
                "reasoning is efficient and stable",
            ),
        }

    def _search_health(self, signals: Mapping[str, Any]) -> dict[str, Any]:
        coverage = _score(signals.get("search_coverage", signals.get("evidence_growth", 0.0) / 5.0))
        diversity = _score(signals.get("search_diversity", signals.get("activated_runtime_count", 0) / 8.0))
        cost = _score(signals.get("search_cost", signals.get("resource_consumption", 0.0)))
        efficiency = _clamp(coverage * 0.65 + (1.0 - cost) * 0.35)
        cooling = _score(signals.get("route_cooling_efficiency", 0.6))
        return {
            "Search Coverage": round(coverage, 3),
            "Search Diversity": round(diversity, 3),
            "Search Cost": round(cost, 3),
            "Search Efficiency": round(efficiency, 3),
            "Search Expansion": round(_score(signals.get("search_expansion", coverage)), 3),
            "Search Compression": round(_score(signals.get("search_compression", 1.0 - cost)), 3),
            "Route Quality": round(_clamp((coverage + efficiency) / 2.0), 3),
            "Route Survival": round(_score(signals.get("route_survival", 0.7)), 3),
            "Route Reuse": round(_score(signals.get("route_reuse", 0.0)), 3),
            "Route Cooling Efficiency": round(cooling, 3),
            "Route Reactivation Success": round(_score(signals.get("route_reactivation_success", 0.0)), 3),
            "Route Merge Quality": round(_score(signals.get("route_merge_quality", 0.5)), 3),
            "Route Split Quality": round(_score(signals.get("route_split_quality", 0.5)), 3),
            "Recommendation": self._search_recommendation(coverage, cost, diversity),
        }

    def _concept_health(self, signals: Mapping[str, Any]) -> dict[str, Any]:
        density = _score(signals.get("concept_density", signals.get("concept_count", 0) / 10.0))
        novelty = _score(signals.get("concept_novelty", 0.4))
        reuse = _score(signals.get("concept_reuse", 0.4))
        redundancy = _score(signals.get("concept_redundancy", max(0.0, density - reuse)))
        quality = _clamp((density + novelty + reuse + (1.0 - redundancy)) / 4.0)
        return {
            "Concept Density": round(density, 3),
            "Concept Novelty": round(novelty, 3),
            "Concept Diversity": round(_score(signals.get("concept_diversity", novelty)), 3),
            "Concept Stability": round(_score(signals.get("concept_stability", 1.0 - redundancy)), 3),
            "Concept Compression": round(_score(signals.get("concept_compression", 1.0 - redundancy)), 3),
            "Concept Reuse": round(reuse, 3),
            "Concept Redundancy": round(redundancy, 3),
            "Concept Generalization": round(_score(signals.get("concept_generalization", reuse)), 3),
            "Concept Lifetime": round(_score(signals.get("concept_lifetime", 0.5)), 3),
            "Concept Evolution": round(quality, 3),
            "Detected Issues": self._concept_issues(density, redundancy, novelty),
        }

    def _program_health(self, signals: Mapping[str, Any]) -> dict[str, Any]:
        correctness = _score(signals.get("program_correctness", _average(signals.get("confidence_values", []))))
        cost = _score(signals.get("program_cost", signals.get("resource_consumption", 0.0)))
        simplicity = _clamp(1.0 - cost)
        return {
            "Program Diversity": round(_score(signals.get("program_diversity", 0.5)), 3),
            "Program Simplicity": round(simplicity, 3),
            "Program Reusability": round(_score(signals.get("program_reusability", 0.5)), 3),
            "Program Correctness": round(correctness, 3),
            "Program Compression": round(simplicity, 3),
            "Program Evolution": round(_clamp((correctness + simplicity) / 2.0), 3),
            "Program Cost": round(cost, 3),
            "Program Efficiency": round(_clamp(correctness * 0.7 + simplicity * 0.3), 3),
        }

    def _evidence_health(self, signals: Mapping[str, Any]) -> dict[str, Any]:
        growth = _score(signals.get("evidence_growth", 0.0) / 5.0)
        coverage = _score(signals.get("evidence_coverage", growth))
        consistency = _score(signals.get("evidence_consistency", 0.75))
        redundancy = _score(signals.get("evidence_redundancy", 0.0))
        completeness = _clamp((coverage + consistency + growth + (1.0 - redundancy)) / 4.0)
        return {
            "Evidence Density": round(growth, 3),
            "Evidence Coverage": round(coverage, 3),
            "Evidence Consistency": round(consistency, 3),
            "Evidence Novelty": round(_score(signals.get("evidence_novelty", growth)), 3),
            "Evidence Reliability": round(_clamp((coverage + consistency) / 2.0), 3),
            "Evidence Utility": round(completeness, 3),
            "Evidence Redundancy": round(redundancy, 3),
            "Evidence Completeness": round(completeness, 3),
            "Recommendation": (
                "increase evidence collection before truth promotion"
                if completeness < 0.55
                else "evidence is sufficient for current governance stage"
            ),
        }

    def _knowledge_health(self, signals: Mapping[str, Any]) -> dict[str, Any]:
        density = _score(signals.get("knowledge_density", 0.0))
        growth = _score(signals.get("knowledge_growth", density))
        consistency = _score(signals.get("knowledge_consistency", 0.75))
        reuse = _score(signals.get("knowledge_reuse", 0.5))
        fragmentation = _score(signals.get("knowledge_fragmentation", 1.0 - consistency))
        return {
            "Knowledge Growth": round(growth, 3),
            "Knowledge Compression": round(_clamp(1.0 - fragmentation), 3),
            "Knowledge Connectivity": round(_score(signals.get("knowledge_connectivity", density)), 3),
            "Knowledge Reuse": round(reuse, 3),
            "Knowledge Consistency": round(consistency, 3),
            "Knowledge Stability": round(_clamp((consistency + reuse) / 2.0), 3),
            "Knowledge Fragmentation": round(fragmentation, 3),
            "Knowledge Coverage": round(density, 3),
            "Knowledge Evolution": round(_clamp((growth + consistency + reuse) / 3.0), 3),
        }

    def _truth_health(self, signals: Mapping[str, Any]) -> dict[str, Any]:
        candidates = float(signals.get("truth_candidates", signals.get("truth_growth", 0.0)))
        validation = _score(signals.get("truth_validation_rate", signals.get("truth_growth", 0.0) / max(1.0, candidates)))
        promotion = _score(signals.get("truth_promotion_rate", validation * 0.8))
        commit = _score(signals.get("truth_commit_rate", promotion * 0.75))
        confidence = _average(signals.get("confidence_values", []))
        reliability = _clamp((validation + promotion + confidence) / 3.0)
        bottleneck = candidates >= 5 and promotion < 0.4
        return {
            "Truth Candidates": int(candidates),
            "Validation Rate": round(validation, 3),
            "Promotion Rate": round(promotion, 3),
            "Commit Rate": round(commit, 3),
            "Truth Stability": round(_score(signals.get("truth_stability", reliability)), 3),
            "Truth Lifetime": round(_score(signals.get("truth_lifetime", 0.5)), 3),
            "Truth Reliability": round(reliability, 3),
            "Truth Confidence": round(confidence, 3),
            "Truth Evolution": round(_clamp((promotion + commit + reliability) / 3.0), 3),
            "Insight": (
                f"{int(candidates)} Truth Candidates generated. Promotion Rate is below expectation. Validation bottleneck detected."
                if bottleneck
                else "truth generation is aligned with current evidence quality"
            ),
            "Recommendation": (
                "increase evidence quality before promotion"
                if promotion < 0.45
                else "continue governed truth promotion"
            ),
        }

    def _memory_health(self, signals: Mapping[str, Any]) -> dict[str, Any]:
        growth = _score(signals.get("memory_growth", 0.0))
        utilization = _score(signals.get("memory_utilization", signals.get("memory_reuse_rate", 0.0)))
        compression = _score(signals.get("memory_compression", 0.5))
        recall = _score(signals.get("memory_recall_accuracy", utilization))
        promotion = _score(signals.get("memory_promotion", 0.0))
        fragmentation = _score(signals.get("memory_fragmentation", 1.0 - compression))
        quality = _clamp((utilization + compression + recall + promotion + (1.0 - fragmentation)) / 5.0)
        return {
            "Memory Growth": round(growth, 3),
            "Memory Utilization": round(utilization, 3),
            "Memory Compression": round(compression, 3),
            "Memory Recall Accuracy": round(recall, 3),
            "Memory Reuse Rate": round(utilization, 3),
            "Memory Promotion": round(promotion, 3),
            "Memory Persistence": round(_score(signals.get("memory_persistence", quality)), 3),
            "Memory Fragmentation": round(fragmentation, 3),
            "Memory Quality": round(quality, 3),
            "Inactivity Explanation": (
                "memory inactivity is caused by low reuse and low promotion signals"
                if utilization < 0.25 and promotion < 0.25
                else "memory is participating in the cognitive cycle"
            ),
        }

    def _decision_health(self, signals: Mapping[str, Any]) -> dict[str, Any]:
        confidence = _score(signals.get("decision_confidence", 0.0))
        utility = _score(signals.get("decision_utility", 0.0))
        error = _score(signals.get("decision_prediction_error", 0.0))
        stability = _score(signals.get("decision_stability", confidence))
        quality = _clamp(confidence * 0.35 + utility * 0.35 + stability * 0.2 + (1.0 - error) * 0.1)
        return {
            "Decision Accuracy": round(_clamp(1.0 - error), 3),
            "Decision Confidence": round(confidence, 3),
            "Decision Stability": round(stability, 3),
            "Decision Cost": round(_score(signals.get("decision_cost", 0.0)), 3),
            "Decision Utility": round(utility, 3),
            "Decision Consistency": round(_score(signals.get("decision_consistency", stability)), 3),
            "Decision Prediction Error": round(error, 3),
            "Decision Learning Rate": round(_score(signals.get("decision_learning_rate", quality)), 3),
            "Decision Evolution": round(quality, 3),
            "Decision Quality": round(quality, 3),
        }

    def _policy_health(self, signals: Mapping[str, Any]) -> dict[str, Any]:
        confidence = _score(signals.get("policy_confidence", 0.0))
        selection = _score(signals.get("policy_selection_score", 0.0))
        success = _score(signals.get("policy_success_rate", confidence))
        failure = _score(signals.get("policy_failure_rate", 1.0 - success))
        cost = _score(signals.get("policy_cost", signals.get("resource_consumption", 0.0)))
        quality = _clamp(success * 0.3 + confidence * 0.25 + selection * 0.25 + (1.0 - cost) * 0.2)
        return {
            "Policy Activation Frequency": round(_score(signals.get("policy_activation_frequency", 0.5)), 3),
            "Policy Success Rate": round(success, 3),
            "Policy Failure Rate": round(failure, 3),
            "Policy Cost": round(cost, 3),
            "Policy Utility": round(selection, 3),
            "Policy Stability": round(confidence, 3),
            "Policy Generalization": round(_score(signals.get("policy_generalization", 0.5)), 3),
            "Policy Adaptability": round(_score(signals.get("policy_adaptability", quality)), 3),
            "Policy Evolution": round(quality, 3),
            "Recommendation": (
                "recommend policy ranking review"
                if quality < 0.55
                else "current policy ranking is analytically supported"
            ),
        }

    def _governance_health(self, signals: Mapping[str, Any]) -> dict[str, Any]:
        planning = _score(signals.get("planning_quality", signals.get("policy_selection_score", 0.0)))
        scheduling = _score(signals.get("scheduling_quality", 1.0 - signals.get("skipped_runtime_count", 0) * 0.1))
        budget = _score(signals.get("budget_efficiency", 1.0 - signals.get("resource_consumption", 0.0)))
        consistency = _score(signals.get("governance_consistency", 0.8))
        intelligence = _clamp((planning + scheduling + budget + consistency) / 4.0)
        return {
            "Planning Quality": round(planning, 3),
            "Scheduling Quality": round(scheduling, 3),
            "Budget Efficiency": round(budget, 3),
            "Resource Allocation": round(budget, 3),
            "Execution Planning Accuracy": round(_score(signals.get("execution_planning_accuracy", planning)), 3),
            "Governance Consistency": round(consistency, 3),
            "Governance Adaptability": round(_score(signals.get("governance_adaptability", intelligence)), 3),
            "Governance Efficiency": round(_clamp((scheduling + budget) / 2.0), 3),
            "Governance Intelligence": round(intelligence, 3),
        }

    def _resource_health(self, signals: Mapping[str, Any]) -> dict[str, Any]:
        consumption = _score(signals.get("resource_consumption", 0.0))
        waste = _score(signals.get("budget_waste", max(0.0, consumption - signals.get("execution_progress", 0.0))))
        efficiency = _clamp(1.0 - waste - consumption * 0.25)
        return {
            "CPU Efficiency": round(_score(signals.get("cpu_efficiency", efficiency)), 3),
            "Memory Efficiency": round(_score(signals.get("memory_efficiency", efficiency)), 3),
            "Reasoning Budget Usage": round(_score(signals.get("reasoning_budget_usage", consumption)), 3),
            "Search Budget Usage": round(_score(signals.get("search_budget_usage", consumption)), 3),
            "Truth Budget Usage": round(_score(signals.get("truth_budget_usage", consumption)), 3),
            "Energy Consumption": round(_score(signals.get("energy_consumption", consumption)), 3),
            "Execution Cost": round(consumption, 3),
            "Budget Waste": round(waste, 3),
            "Optimization Opportunities": (
                "reduce budget waste and rebalance runtime allocation"
                if waste > 0.25
                else "resource allocation is within expected bounds"
            ),
        }

    def _cognitive_kpis(self, *health_sections: Mapping[str, Any]) -> dict[str, float]:
        execution, reasoning, search, concept, program, evidence, knowledge, truth, memory, decision, policy, governance, resources = health_sections
        kpis = {
            "Execution Intelligence": execution["Execution Intelligence Score"],
            "Reasoning Efficiency": reasoning["Reasoning Efficiency"],
            "Search Intelligence": search["Search Efficiency"],
            "Concept Intelligence": concept["Concept Evolution"],
            "Program Intelligence": program["Program Efficiency"],
            "Evidence Intelligence": evidence["Evidence Utility"],
            "Knowledge Intelligence": knowledge["Knowledge Evolution"],
            "Truth Intelligence": truth["Truth Reliability"],
            "Memory Intelligence": memory["Memory Quality"],
            "Decision Intelligence": decision["Decision Quality"],
            "Policy Intelligence": policy["Policy Evolution"],
            "Governance Intelligence": governance["Governance Intelligence"],
            "Learning Intelligence": _clamp((knowledge["Knowledge Evolution"] + memory["Memory Quality"] + decision["Decision Learning Rate"]) / 3.0),
            "World Model Readiness": _clamp((truth["Truth Reliability"] + knowledge["Knowledge Stability"] + governance["Governance Intelligence"]) / 3.0),
            "DNA Evolution Readiness": _clamp((decision["Decision Quality"] + policy["Policy Evolution"] + governance["Governance Intelligence"]) / 3.0),
            "Resource Intelligence": _clamp((resources["CPU Efficiency"] + resources["Memory Efficiency"]) / 2.0),
        }
        kpis["Overall Cognitive Intelligence"] = round(
            sum(kpis.values()) / max(1, len(kpis)),
            3,
        )
        return {key: round(value, 3) for key, value in kpis.items()}

    def _detect_anomalies(self, *sections: Mapping[str, Any]) -> list[dict[str, Any]]:
        anomalies = []
        checks = {
            "execution_anomaly": sections[0].get("Execution Quality", 1.0),
            "reasoning_anomaly": sections[1].get("Reasoning Quality", 1.0),
            "search_anomaly": sections[2].get("Search Efficiency", 1.0),
            "evidence_anomaly": sections[3].get("Evidence Utility", 1.0),
            "truth_anomaly": sections[4].get("Promotion Rate", 1.0),
            "memory_anomaly": sections[5].get("Memory Quality", 1.0),
            "decision_anomaly": sections[6].get("Decision Quality", 1.0),
            "policy_anomaly": sections[7].get("Policy Evolution", 1.0),
            "governance_anomaly": sections[8].get("Governance Intelligence", 1.0),
        }
        resource_waste = sections[9].get("Budget Waste", 0.0)
        for kind, value in checks.items():
            if value < 0.45:
                anomalies.append({
                    "anomaly_type": kind,
                    "severity": "high" if value < 0.3 else "medium",
                    "observed_value": round(value, 3),
                    "explanation": f"{kind} detected because interpreted health score is below expectation",
                    "corrective_action": self._corrective_action(kind),
                })
        if resource_waste > 0.25:
            anomalies.append({
                "anomaly_type": "resource_waste",
                "severity": "medium",
                "observed_value": round(resource_waste, 3),
                "explanation": "resource consumption exceeds observed execution progress",
                "corrective_action": "rebalance budgets and suspend low-value routes",
            })
        return anomalies

    def _root_cause_analysis(
        self,
        anomalies: list[Mapping[str, Any]],
        signals: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        analyses = []
        for anomaly in anomalies:
            kind = anomaly["anomaly_type"]
            affected = self._affected_systems(kind)
            analyses.append({
                "anomaly_type": kind,
                "Immediate Cause": anomaly["explanation"],
                "Contributing Factors": self._contributing_factors(kind, signals),
                "Historical Patterns": self.history.as_dict(),
                "System Dependencies": affected,
                "Affected Runtimes": affected.get("runtimes", []),
                "Affected Policies": affected.get("policies", []),
                "Affected Decisions": affected.get("decisions", []),
                "Recovery Recommendations": [anomaly["corrective_action"]],
            })
        return analyses

    def _optimization_opportunities(self, anomalies, execution, search, truth, memory, decision, policy, resources):
        opportunities = []
        if search["Search Efficiency"] < 0.55:
            opportunities.append({"domain": "Search", "recommendation": search["Recommendation"], "justification": "search efficiency below target"})
        if truth["Promotion Rate"] < 0.45:
            opportunities.append({"domain": "Truth Promotion", "recommendation": truth["Recommendation"], "justification": truth["Insight"]})
        if memory["Memory Quality"] < 0.45:
            opportunities.append({"domain": "Memory Promotion", "recommendation": "increase governed memory reuse and promotion", "justification": memory["Inactivity Explanation"]})
        if policy["Policy Evolution"] < 0.55:
            opportunities.append({"domain": "Policy Ranking", "recommendation": policy["Recommendation"], "justification": "policy intelligence below target"})
        if decision["Decision Quality"] < 0.55:
            opportunities.append({"domain": "Decision Strategy", "recommendation": "increase decision simulation calibration", "justification": "decision quality below target"})
        if resources["Budget Waste"] > 0.25:
            opportunities.append({"domain": "Resource Allocation", "recommendation": resources["Optimization Opportunities"], "justification": "budget waste detected"})
        if not opportunities and not anomalies:
            opportunities.append({"domain": "Continuous Optimization", "recommendation": "maintain current governance strategy and keep monitoring trends", "justification": "no critical anomalies detected"})
        return opportunities

    def _recommended_actions(self, opportunities, root_causes):
        actions = [
            {
                "action": item["recommendation"],
                "domain": item["domain"],
                "evidence": item["justification"],
            }
            for item in opportunities
        ]
        for cause in root_causes:
            for recommendation in cause["Recovery Recommendations"]:
                actions.append({
                    "action": recommendation,
                    "domain": cause["anomaly_type"],
                    "evidence": cause["Immediate Cause"],
                })
        return actions

    def _trend_analysis(self, kpis: Mapping[str, float]) -> dict[str, Any]:
        history = self.history.as_dict()
        current = kpis["Overall Cognitive Intelligence"]
        previous = history["average_intelligence_score"]
        trend = current - previous if history["report_count"] else 0.0
        return {
            "Concept Growth": "stable",
            "Truth Stability": self._trend_label(kpis["Truth Intelligence"], history["average_truth_health"]),
            "Memory Growth": self._trend_label(kpis["Memory Intelligence"], history["average_memory_health"]),
            "Knowledge Expansion": "improving" if kpis["Knowledge Intelligence"] >= 0.6 else "needs_attention",
            "Execution Cost": "controlled" if kpis["Resource Intelligence"] >= 0.55 else "rising",
            "Search Efficiency": "healthy" if kpis["Search Intelligence"] >= 0.55 else "regressing",
            "Reasoning Quality": "healthy" if kpis["Reasoning Efficiency"] >= 0.55 else "regressing",
            "Decision Quality": self._trend_label(kpis["Decision Intelligence"], history["average_decision_quality"]),
            "Policy Performance": self._trend_label(kpis["Policy Intelligence"], history["average_policy_quality"]),
            "Governance Quality": "healthy" if kpis["Governance Intelligence"] >= 0.55 else "needs_attention",
            "Overall Trend Delta": round(trend, 3),
        }

    def _predictive_analysis(self, kpis: Mapping[str, float]) -> dict[str, Any]:
        return {
            "Expected Truth Stability": round(_clamp(kpis["Truth Intelligence"] * 0.9 + kpis["Evidence Intelligence"] * 0.1), 3),
            "Expected Memory Growth": round(_clamp(kpis["Memory Intelligence"] * 0.8 + kpis["Learning Intelligence"] * 0.2), 3),
            "Expected Knowledge Expansion": round(_clamp(kpis["Knowledge Intelligence"] * 0.75 + kpis["Learning Intelligence"] * 0.25), 3),
            "Expected Execution Cost": round(_clamp(1.0 - kpis["Resource Intelligence"]), 3),
            "Expected Search Efficiency": round(kpis["Search Intelligence"], 3),
            "Expected Learning Progress": round(kpis["Learning Intelligence"], 3),
            "Expected DNA Evolution": round(kpis["DNA Evolution Readiness"], 3),
            "Expected World Model Readiness": round(kpis["World Model Readiness"], 3),
            "Prediction Measurable": True,
        }

    def _executive_summary(self, kpis, anomalies):
        score = kpis["Overall Cognitive Intelligence"]
        return {
            "summary": _banded_text(
                score,
                "cognitive operations are generating weak intelligence and require optimization",
                "cognitive operations are interpretable with targeted optimization opportunities",
                "cognitive operations show strong intelligence and stable governance feedback",
            ),
            "anomaly_count": len(anomalies),
            "overall_score": score,
        }

    def _world_model_readiness(self, kpis, truth, knowledge):
        score = kpis["World Model Readiness"]
        return {
            "readiness_score": score,
            "committed_knowledge_sufficient": score >= 0.65,
            "truth_reliability": truth["Truth Reliability"],
            "knowledge_stability": knowledge["Knowledge Stability"],
            "recommendation": "allow governed World Model updates" if score >= 0.7 else "continue accumulating committed knowledge",
        }

    def _dna_readiness(self, kpis, decision, policy):
        score = kpis["DNA Evolution Readiness"]
        return {
            "readiness_score": score,
            "decision_quality": decision["Decision Quality"],
            "policy_quality": policy["Policy Evolution"],
            "performance_evidence_sufficient": score >= 0.7,
            "recommendation": "permit analytical DNA influence" if score >= 0.7 else "hold DNA evolution under observation",
        }

    def _meta_analytics(self, kpis, recommendations):
        return {
            "kpis_meaningful": bool(kpis),
            "predictions_measurable": True,
            "recommendations_actionable": bool(recommendations),
            "insights_improving_execution": self.history.report_count > 0,
            "analytical_model_evolution": "continue_calibration",
        }

    def _search_recommendation(self, coverage, cost, diversity):
        if cost > 0.75 and coverage < 0.55:
            return "reduce branching and improve route quality"
        if coverage < 0.45:
            return "expand search depth and increase exploration"
        if diversity < 0.35:
            return "increase exploration diversity"
        return "reuse memory and preserve efficient search routes"

    def _concept_issues(self, density, redundancy, novelty):
        issues = []
        if density > 0.8 and redundancy > 0.4:
            issues.append("conceptual_inflation_detected")
        if novelty < 0.25 and density < 0.3:
            issues.append("missing_abstractions_detected")
        if redundancy > 0.5:
            issues.append("redundant_concepts_detected")
        return issues

    def _corrective_action(self, kind: str) -> str:
        actions = {
            "execution_anomaly": "replan execution with stricter stopping criteria",
            "reasoning_anomaly": "reduce redundant reasoning and recalibrate confidence",
            "search_anomaly": "adjust exploration and route cooling policy",
            "evidence_anomaly": "collect higher quality evidence before promotion",
            "truth_anomaly": "increase evidence quality before truth promotion",
            "memory_anomaly": "increase memory reuse and promotion review",
            "decision_anomaly": "recalibrate decision simulation and ranking",
            "policy_anomaly": "review policy ranking and historical outcomes",
            "governance_anomaly": "rebalance governance budgets and planning criteria",
        }
        return actions.get(kind, "perform governance review")

    def _affected_systems(self, kind: str) -> dict[str, list[str]]:
        mapping = {
            "search_anomaly": {"runtimes": ["adaptive_search"], "policies": ["novel_task_policy", "deep_investigation_policy"], "decisions": ["search_depth_selection"]},
            "truth_anomaly": {"runtimes": ["truth_runtime", "evidence_builder"], "policies": ["high_confidence_policy", "conflict_resolution_policy"], "decisions": ["truth_promotion_decision"]},
            "memory_anomaly": {"runtimes": ["memory_runtime"], "policies": ["known_task_policy"], "decisions": ["memory_reuse_decision"]},
            "decision_anomaly": {"runtimes": [], "policies": ["all_policy_candidates"], "decisions": ["policy_selection_decision"]},
            "policy_anomaly": {"runtimes": [], "policies": ["policy_registry"], "decisions": ["policy_ranking"]},
            "governance_anomaly": {"runtimes": ["world_governance"], "policies": ["governance_policies"], "decisions": ["execution_intent"]},
        }
        return mapping.get(kind, {"runtimes": ["execution_runtime"], "policies": [], "decisions": []})

    def _contributing_factors(self, kind: str, signals: Mapping[str, Any]) -> list[str]:
        factors = []
        if _score(signals.get("resource_consumption", 0.0)) > 0.7:
            factors.append("high_resource_consumption")
        if _average(signals.get("confidence_values", [])) < 0.5:
            factors.append("low_confidence")
        if _score(signals.get("evidence_growth", 0.0) / 5.0) < 0.3:
            factors.append("low_evidence_growth")
        if kind in {"truth_anomaly", "memory_anomaly"}:
            factors.append("promotion_signal_weak")
        return factors or ["insufficient_supporting_signal"]

    def _trend_label(self, current: float, previous: float) -> str:
        if previous == 0:
            return "baseline"
        delta = current - previous
        if delta > 0.05:
            return "improving"
        if delta < -0.05:
            return "regressing"
        return "stable"


def _score(value: Any) -> float:
    return _clamp(value)


def _clamp(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


def _average(values: Any) -> float:
    if isinstance(values, (int, float)):
        return _score(values)
    if not values:
        return 0.0
    numbers = [_score(value) for value in values]
    return sum(numbers) / max(1, len(numbers))


def _nested(mapping: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = mapping
    for key in keys:
        if not isinstance(current, Mapping):
            return default
        current = current.get(key)
    return default if current is None else current


def _banded_text(score: float, low: str, medium: str, high: str) -> str:
    if score < 0.45:
        return low
    if score < 0.75:
        return medium
    return high


cognitive_intelligence_analytics = CognitiveIntelligenceAnalytics()


__all__ = [
    "ANALYTIC_DOMAINS",
    "AnalyticsHistory",
    "CognitiveIntelligenceAnalytics",
    "cognitive_intelligence_analytics",
]
