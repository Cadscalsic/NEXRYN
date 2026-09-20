"""Adaptive search intelligence built from existing search evidence.

This engine does not execute search.  It reasons about search: strategy,
budget, route decisions, hypotheses, and learning signals are derived from the
current search runtime, concept formation, program synthesis, and telemetry.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


STRATEGIES = (
    "Exploration First",
    "Exploitation First",
    "Balanced",
    "Concept Driven",
    "Program Driven",
    "Transformation Driven",
    "Spatial Driven",
    "Object Driven",
    "Constraint Driven",
    "Evidence Driven",
    "Hybrid Strategy",
)

ROUTE_ACTIONS = (
    "Expand",
    "Merge",
    "Split",
    "Suspend",
    "Reactivate",
    "Terminate",
    "Promote",
    "Archive",
)


@dataclass
class SearchBudget:
    maximum_routes: int
    maximum_programs: int
    maximum_branch_depth: int
    maximum_branch_width: int
    maximum_concept_expansion: int
    maximum_validation_attempts: int
    maximum_runtime_budget: float
    explanation: str


@dataclass
class RouteDecision:
    route_id: str
    decision: str
    evidence: dict[str, Any]
    score: dict[str, float]
    explanation: str


@dataclass
class SearchHypothesis:
    hypothesis_id: str
    supporting_concepts: list[str]
    supporting_programs: list[str]
    supporting_evidence: list[dict[str, Any]]
    confidence: float
    utility: float
    expected_gain: float
    status: str
    explanation: str


class AdaptiveSearchIntelligenceMemory:
    """Small deterministic memory for search strategy outcomes."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(
            path or "runtime/artifacts/runtime_data/search/adaptive_search_intelligence_memory.json"
        )

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"history": []}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"history": []}
        return payload if isinstance(payload, dict) else {"history": []}

    def summary(self) -> dict[str, Any]:
        history = [
            item for item in self.load().get("history", [])
            if isinstance(item, Mapping)
        ]
        successful = [item for item in history if item.get("successful") is True]
        failed = [item for item in history if item.get("successful") is False]
        strategies: dict[str, list[Mapping[str, Any]]] = {}
        for item in history:
            strategies.setdefault(str(item.get("strategy", "Balanced")), []).append(item)
        ranked = sorted(
            strategies,
            key=lambda name: (
                -sum(1 for item in strategies[name] if item.get("successful") is True)
                / max(len(strategies[name]), 1),
                name,
            ),
        )
        route_counts = [_number(item.get("routes")) for item in history]
        program_counts = [_number(item.get("programs")) for item in history]
        costs = [_number(item.get("search_cost")) for item in history]
        return {
            "successful_search_strategies": len(successful),
            "failed_strategies": len(failed),
            "typical_route_counts": round(sum(route_counts) / max(len(route_counts), 1), 4),
            "typical_program_counts": round(sum(program_counts) / max(len(program_counts), 1), 4),
            "winning_search_policies": ranked[:5],
            "average_search_cost": round(sum(costs) / max(len(costs), 1), 4),
            "generalization_statistics": {
                "observations": len(history),
                "strategy_diversity": len(strategies),
                "confidence": round(min(0.95, 0.4 + len(history) * 0.03), 4),
            },
            "search_templates": [
                item.get("template") for item in successful[-5:]
                if item.get("template")
            ],
        }

    def remember(self, report: Mapping[str, Any]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.load()
        history = list(payload.get("history", []))
        stats = report.get("route_statistics", {})
        complexity = report.get("task_complexity", {})
        history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "strategy": (report.get("chosen_strategy") or {}).get("strategy"),
            "difficulty": complexity.get("difficulty"),
            "routes": stats.get("routes_observed", 0),
            "programs": (report.get("program_statistics") or {}).get("programs_available", 0),
            "search_cost": (report.get("search_cost") or {}).get("total_search_cost", 0.0),
            "successful": stats.get("promoted_routes", 0) > 0,
            "template": (report.get("chosen_strategy") or {}).get("strategy"),
        })
        payload["history"] = history[-200:]
        self.path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return {
            "persistent_search_memory": True,
            "memory_path": str(self.path),
            "entries_stored": len(payload["history"]),
        }


class AdaptiveSearchIntelligenceEngine:
    """Strategic cognition for how search should behave."""

    system_name = "adaptive_search_intelligence_engine"

    def __init__(
        self,
        memory: AdaptiveSearchIntelligenceMemory | None = None,
    ) -> None:
        self.memory = memory or AdaptiveSearchIntelligenceMemory()

    def build_report(
        self,
        *,
        cognitive_search_report: Mapping[str, Any] | None = None,
        adaptive_search_policy_report: Mapping[str, Any] | None = None,
        cognitive_route_intelligence_report: Mapping[str, Any] | None = None,
        concept_formation_report: Mapping[str, Any] | None = None,
        program_synthesis_report: Mapping[str, Any] | None = None,
        truth_report: Mapping[str, Any] | None = None,
        memory_report: Mapping[str, Any] | None = None,
        dependency_report: Mapping[str, Any] | None = None,
        causal_report: Mapping[str, Any] | None = None,
        all_results: list[dict[str, Any]] | None = None,
        report_level: str = "normal",
        persist: bool = True,
    ) -> dict[str, Any]:
        search_report = dict(cognitive_search_report or {})
        policy_report = dict(adaptive_search_policy_report or {})
        route_report = dict(cognitive_route_intelligence_report or {})
        concept_report = dict(concept_formation_report or {})
        program_report = dict(program_synthesis_report or {})
        results = all_results or []

        task_complexity = self._task_complexity(
            results=results,
            search_report=search_report,
            concept_report=concept_report,
            program_report=program_report,
            dependency_report=dict(dependency_report or {}),
            causal_report=dict(causal_report or {}),
        )
        memory_summary = self.memory.summary()
        strategy = self._choose_strategy(
            task_complexity,
            policy_report,
            concept_report,
            program_report,
            memory_summary,
        )
        budget = self._budget(task_complexity, program_report, concept_report)
        routes = self._routes(search_report, route_report, results)
        route_decisions = self._route_decisions(routes, budget, strategy)
        hypotheses = self._hypotheses(
            route_decisions=route_decisions,
            concept_report=concept_report,
            program_report=program_report,
            truth_report=dict(truth_report or {}),
        )
        graph = self._graph(route_decisions, hypotheses, concept_report, program_report)
        timeline = self._timeline(strategy, budget, route_decisions, hypotheses)
        route_stats = self._route_statistics(route_decisions, routes)
        program_stats = self._program_statistics(program_report)
        concept_stats = self._concept_statistics(concept_report)
        search_cost = {
            "total_search_cost": round(
                task_complexity["expected_search_cost"]
                + route_stats["routes_observed"] * 0.05
                + program_stats["programs_available"] * 0.02,
                4,
            ),
            "cost_reason": "Derived from complexity, observed route count, and available program count.",
        }
        policy_decisions = self._policy_decisions(
            task_complexity,
            strategy,
            budget,
            route_decisions,
            hypotheses,
        )
        learning = self._learning_outcomes(
            strategy,
            route_stats,
            program_stats,
            concept_stats,
            memory_summary,
        )
        report = {
            "system": self.system_name,
            "ADAPTIVE_SEARCH_INTELLIGENCE_REPORT": True,
            "status": "OPERATIONAL",
            "report_level": report_level,
            "task_complexity": task_complexity,
            "chosen_strategy": strategy,
            "search_budget": asdict(budget),
            "search_timeline": timeline,
            "search_graph": graph,
            "route_decisions": [asdict(item) for item in route_decisions],
            "route_statistics": route_stats,
            "program_statistics": program_stats,
            "concept_statistics": concept_stats,
            "strategy_evolution": self._strategy_evolution(strategy, route_decisions),
            "policy_decisions": policy_decisions,
            "multi_hypothesis_management": [asdict(item) for item in hypotheses],
            "learning_outcomes": learning,
            "optimization_candidates": self._optimization_candidates(
                route_stats,
                program_stats,
                concept_stats,
                task_complexity,
            ),
            "search_memory": memory_summary,
            "search_cost": search_cost,
            "runtime_alignment": {
                "executes_search": False,
                "reuses_search_runtime": True,
                "reuses_concept_formation_engine": True,
                "reuses_program_synthesis_engine": True,
                "runtime_registry_redesigned": False,
                "deterministic_execution": True,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        report["search_memory_update"] = (
            self.memory.remember(report)
            if persist
            else {"persistent_search_memory": False, "reason": "persistence_disabled"}
        )
        return report

    def _task_complexity(
        self,
        *,
        results: list[dict[str, Any]],
        search_report: Mapping[str, Any],
        concept_report: Mapping[str, Any],
        program_report: Mapping[str, Any],
        dependency_report: Mapping[str, Any],
        causal_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        grids = []
        successes = 0
        for result in results:
            if isinstance(result, Mapping):
                successes += int(bool(result.get("success") or result.get("exact_match")))
                for key in ("input", "output", "predicted_output", "prediction"):
                    grid = result.get(key)
                    if _is_grid(grid):
                        grids.append(grid)
        cells = sum(len(grid) * max((len(row) for row in grid), default=0) for grid in grids)
        colors = {
            value
            for grid in grids
            for row in grid
            for value in row
            if isinstance(value, int)
        }
        route_count = len(self._list(search_report.get("route_ranking")))
        if route_count == 0:
            route_count = _count_graph_nodes(search_report.get("search_graph"))
        concept_count = int(_number(concept_report.get("concept_count")))
        program_count = int(_number(program_report.get("generated_programs")))
        dependency_count = len(dependency_report) if dependency_report else 0
        causal_count = len(causal_report) if causal_report else 0
        result_count = max(len(results), 1)
        visual = _clamp(len(colors) / 10 + min(cells / 900, 0.4), 0.05, 1.0)
        structural = _clamp(route_count / 16 + concept_count / 80, 0.05, 1.0)
        transformation = _clamp(program_count / 40 + dependency_count / 80, 0.05, 1.0)
        object_complexity = _clamp(concept_count / 50 + len(colors) / 25, 0.05, 1.0)
        color = _clamp(len(colors) / 8, 0.05, 1.0)
        spatial = _clamp(route_count / 20 + cells / max(result_count * 1200, 1), 0.05, 1.0)
        topological = _clamp((dependency_count + causal_count) / 60 + concept_count / 120, 0.05, 1.0)
        reasoning = _clamp((route_count + program_count + concept_count) / 120, 0.05, 1.0)
        concept_density = _clamp(concept_count / max(route_count + result_count, 1) / 6, 0.0, 1.0)
        expected_program_diversity = _clamp(program_count / 30, 0.0, 1.0)
        aggregate = round(
            (
                visual
                + structural
                + transformation
                + object_complexity
                + color
                + spatial
                + topological
                + reasoning
            ) / 8,
            4,
        )
        difficulty = (
            "EASY" if aggregate < 0.32
            else "MEDIUM" if aggregate < 0.62
            else "DIFFICULT"
        )
        return {
            "visual_complexity": round(visual, 4),
            "structural_complexity": round(structural, 4),
            "transformation_complexity": round(transformation, 4),
            "object_complexity": round(object_complexity, 4),
            "color_complexity": round(color, 4),
            "spatial_complexity": round(spatial, 4),
            "topological_complexity": round(topological, 4),
            "reasoning_complexity": round(reasoning, 4),
            "concept_density": round(concept_density, 4),
            "expected_search_cost": round(aggregate * max(route_count, 1), 4),
            "expected_program_diversity": round(expected_program_diversity, 4),
            "difficulty": difficulty,
            "observed_routes": route_count,
            "observed_concepts": concept_count,
            "observed_programs": program_count,
            "observed_successes": successes,
            "complexity_score": aggregate,
        }

    def _choose_strategy(
        self,
        task_complexity: Mapping[str, Any],
        policy_report: Mapping[str, Any],
        concept_report: Mapping[str, Any],
        program_report: Mapping[str, Any],
        memory_summary: Mapping[str, Any],
    ) -> dict[str, Any]:
        complexity = _number(task_complexity.get("complexity_score"))
        concept_count = _number(concept_report.get("concept_count"))
        program_count = _number(program_report.get("generated_programs"))
        policy_strategy = policy_report.get("selected_strategy")
        if program_count >= 6 and complexity >= 0.35:
            strategy = "Program Driven"
            reason = "Available synthesized programs can focus route evolution before broad exploration."
        elif concept_count >= 6:
            strategy = "Concept Driven"
            reason = "Concept density is high enough to let concepts guide expansion and pruning."
        elif _number(task_complexity.get("spatial_complexity")) > 0.55:
            strategy = "Spatial Driven"
            reason = "Spatial complexity is the dominant task-analysis signal."
        elif policy_strategy in STRATEGIES and complexity < 0.35:
            strategy = str(policy_strategy)
            reason = "Existing adaptive search policy is sufficient for low-complexity evidence."
        elif complexity < 0.3:
            strategy = "Exploitation First"
            reason = "Task complexity is low, so exploiting the strongest current route is preferred."
        elif complexity > 0.68:
            strategy = "Hybrid Strategy"
            reason = "High complexity requires mixed concept, program, and evidence-driven control."
        else:
            strategy = "Balanced"
            reason = "Evidence does not justify a narrow search style; maintain exploration and exploitation."
        if memory_summary.get("winning_search_policies") and strategy == "Balanced":
            strategy = str(memory_summary["winning_search_policies"][0])
            reason = "Historical search memory provides a stronger prior than the neutral baseline."
        return {
            "strategy": strategy,
            "why_chosen": reason,
            "evidence": {
                "complexity_score": task_complexity.get("complexity_score"),
                "concept_count": concept_count,
                "program_count": program_count,
                "policy_strategy": policy_strategy,
            },
        }

    def _budget(
        self,
        task_complexity: Mapping[str, Any],
        program_report: Mapping[str, Any],
        concept_report: Mapping[str, Any],
    ) -> SearchBudget:
        complexity = _number(task_complexity.get("complexity_score"))
        programs = int(_number(program_report.get("generated_programs")))
        concepts = int(_number(concept_report.get("concept_count")))
        maximum_routes = max(2, min(24, int(3 + complexity * 18)))
        maximum_programs = max(1, min(max(programs, 1), int(2 + complexity * 12)))
        maximum_branch_depth = max(1, min(8, int(2 + complexity * 6)))
        maximum_branch_width = max(2, min(10, int(2 + complexity * 8)))
        maximum_concept_expansion = max(1, min(max(concepts, 1), int(2 + complexity * 16)))
        maximum_validation_attempts = max(2, min(18, int(3 + complexity * 14)))
        maximum_runtime_budget = round(0.05 + complexity * 0.45, 4)
        return SearchBudget(
            maximum_routes=maximum_routes,
            maximum_programs=maximum_programs,
            maximum_branch_depth=maximum_branch_depth,
            maximum_branch_width=maximum_branch_width,
            maximum_concept_expansion=maximum_concept_expansion,
            maximum_validation_attempts=maximum_validation_attempts,
            maximum_runtime_budget=maximum_runtime_budget,
            explanation=(
                f"{task_complexity.get('difficulty')} complexity "
                f"({complexity:.4f}) allocates {maximum_routes} routes, "
                f"{maximum_programs} programs, depth {maximum_branch_depth}, "
                "and validation proportional to observed concept/program density."
            ),
        )

    def _routes(
        self,
        search_report: Mapping[str, Any],
        route_report: Mapping[str, Any],
        results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        routes = [
            item for item in self._list(search_report.get("route_ranking"))
            if isinstance(item, Mapping)
        ]
        routes.extend(
            item for item in self._list(route_report.get("route_decisions"))
            if isinstance(item, Mapping)
        )
        if not routes:
            for index, result in enumerate(results[:8]):
                if isinstance(result, Mapping):
                    routes.append({
                        "route_id": result.get("task_id") or f"result_route_{index}",
                        "confidence": result.get("confidence", result.get("score", 0.4)),
                        "success": bool(result.get("success") or result.get("exact_match")),
                        "evidence": _small_mapping(result),
                    })
        if not routes:
            routes.append({
                "route_id": "bootstrap_route",
                "confidence": 0.35,
                "success": False,
                "evidence": {"source": "search_runtime_bootstrap"},
            })
        return [dict(route) for route in routes[:24]]

    def _route_decisions(
        self,
        routes: list[dict[str, Any]],
        budget: SearchBudget,
        strategy: Mapping[str, Any],
    ) -> list[RouteDecision]:
        decisions = []
        for index, route in enumerate(routes):
            confidence = _clamp(
                max(
                    _number(route.get("confidence")),
                    _number(route.get("current_confidence")),
                    _number(route.get("route_confidence")),
                    _number(route.get("score")),
                    0.25 + (0.5 if route.get("success") else 0.0),
                ),
                0.0,
                1.0,
            )
            evidence_score = _clamp(confidence + (0.15 if route.get("success") else 0.0), 0.0, 1.0)
            novelty = _clamp(1.0 - index / max(len(routes), 1), 0.05, 1.0)
            expected_gain = _clamp((evidence_score + novelty) / 2, 0.0, 1.0)
            search_cost = _clamp((index + 1) / max(budget.maximum_routes, 1), 0.0, 1.0)
            failure_risk = _clamp(1.0 - confidence + search_cost * 0.25, 0.0, 1.0)
            score = {
                "evidence_score": round(evidence_score, 4),
                "concept_coverage": round(_number(route.get("concept_coverage"), 0.35), 4),
                "program_coverage": round(_number(route.get("program_coverage"), 0.35), 4),
                "transformation_coverage": round(_number(route.get("transformation_coverage"), 0.3), 4),
                "novelty": round(novelty, 4),
                "confidence": round(confidence, 4),
                "utility": round(_clamp((confidence + expected_gain) / 2, 0.0, 1.0), 4),
                "expected_information_gain": round(expected_gain, 4),
                "expected_generalization": round(_clamp((novelty + confidence) / 2, 0.0, 1.0), 4),
                "search_cost": round(search_cost, 4),
                "future_potential": round(_clamp(expected_gain - search_cost * 0.2, 0.0, 1.0), 4),
                "historical_success": round(_number(route.get("historical_success"), 0.0), 4),
                "failure_risk": round(failure_risk, 4),
            }
            if route.get("success") or confidence >= 0.78:
                action = "Promote"
                explanation = "High confidence or observed success justifies promotion."
            elif index >= budget.maximum_routes:
                action = "Archive"
                explanation = "Route exceeds the current adaptive route budget."
            elif failure_risk > 0.78 and expected_gain < 0.45:
                action = "Terminate"
                explanation = "Low information gain and high failure risk stop this route."
            elif failure_risk > 0.68:
                action = "Suspend"
                explanation = "Evidence is weak now, but the route is retained for possible reactivation."
            elif strategy.get("strategy") in {"Exploration First", "Hybrid Strategy"} and novelty > 0.55:
                action = "Split"
                explanation = "Novel evidence under an exploratory strategy supports route splitting."
            elif confidence > 0.52:
                action = "Expand"
                explanation = "Route has enough evidence and manageable cost to expand."
            else:
                action = "Reactivate" if index == 0 else "Merge"
                explanation = "Route has partial support; combine or reactivate before discarding."
            decisions.append(
                RouteDecision(
                    route_id=str(route.get("route_id") or route.get("id") or f"route_{index}"),
                    decision=action,
                    evidence=_small_mapping(route),
                    score=score,
                    explanation=explanation,
                )
            )
        if decisions and not any(item.decision == "Expand" for item in decisions):
            weakest_promotable = min(
                decisions,
                key=lambda item: item.score.get("search_cost", 1.0),
            )
            if weakest_promotable.decision not in {"Promote", "Terminate"}:
                weakest_promotable.decision = "Expand"
                weakest_promotable.explanation = (
                    "At least one active route is kept expanding to avoid premature search collapse."
                )
        if decisions and not any(item.decision in {"Terminate", "Archive", "Suspend"} for item in decisions):
            last = decisions[-1]
            if len(decisions) > 1 and last.decision != "Promote":
                last.decision = "Terminate"
                last.explanation = "Lowest-ranked route is stopped to keep the adaptive budget bounded."
        return decisions

    def _hypotheses(
        self,
        *,
        route_decisions: list[RouteDecision],
        concept_report: Mapping[str, Any],
        program_report: Mapping[str, Any],
        truth_report: Mapping[str, Any],
    ) -> list[SearchHypothesis]:
        concepts = [
            str(item.get("concept_id"))
            for item in self._list(concept_report.get("top_concepts"))
            if isinstance(item, Mapping) and item.get("concept_id")
        ][:6]
        programs = [
            str(item.get("program_id"))
            for item in self._list(program_report.get("winning_programs"))
            if isinstance(item, Mapping) and item.get("program_id")
        ][:6]
        hypotheses = []
        for index, decision in enumerate(route_decisions[:6]):
            confidence = decision.score.get("confidence", 0.0)
            utility = decision.score.get("utility", 0.0)
            expected_gain = decision.score.get("expected_information_gain", 0.0)
            status = (
                "survived" if decision.decision in {"Expand", "Split", "Promote", "Reactivate"}
                else "disappeared"
            )
            reason = (
                "Hypothesis survived because route evidence remains useful for future search."
                if status == "survived"
                else "Hypothesis disappeared because its route was stopped or archived by evidence."
            )
            hypotheses.append(
                SearchHypothesis(
                    hypothesis_id=_id("hypothesis", decision.route_id, index),
                    supporting_concepts=concepts[:3],
                    supporting_programs=programs[:3],
                    supporting_evidence=[
                        {
                            "route_id": decision.route_id,
                            "decision": decision.decision,
                            "truth_support": _small_mapping(truth_report),
                        }
                    ],
                    confidence=round(confidence, 4),
                    utility=round(utility, 4),
                    expected_gain=round(expected_gain, 4),
                    status=status,
                    explanation=reason,
                )
            )
        return hypotheses

    def _graph(
        self,
        route_decisions: list[RouteDecision],
        hypotheses: list[SearchHypothesis],
        concept_report: Mapping[str, Any],
        program_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        nodes = []
        edges = []
        for decision in route_decisions:
            nodes.append({
                "id": decision.route_id,
                "type": "route",
                "decision": decision.decision,
            })
        for hypothesis in hypotheses:
            nodes.append({
                "id": hypothesis.hypothesis_id,
                "type": "hypothesis",
                "status": hypothesis.status,
            })
            if hypothesis.supporting_evidence:
                route_id = hypothesis.supporting_evidence[0].get("route_id")
                edges.append({
                    "source": route_id,
                    "target": hypothesis.hypothesis_id,
                    "relation": "supports" if hypothesis.status == "survived" else "contradicts",
                })
        for concept in self._list(concept_report.get("top_concepts"))[:8]:
            if isinstance(concept, Mapping) and concept.get("concept_id"):
                nodes.append({"id": concept["concept_id"], "type": "concept"})
                for hypothesis in hypotheses[:2]:
                    edges.append({
                        "source": concept["concept_id"],
                        "target": hypothesis.hypothesis_id,
                        "relation": "supports",
                    })
        for program in self._list(program_report.get("winning_programs"))[:8]:
            if isinstance(program, Mapping) and program.get("program_id"):
                nodes.append({"id": program["program_id"], "type": "program"})
                for decision in route_decisions[:2]:
                    edges.append({
                        "source": program["program_id"],
                        "target": decision.route_id,
                        "relation": "validated_by",
                    })
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "edge_types": sorted({edge["relation"] for edge in edges}),
        }

    def _timeline(
        self,
        strategy: Mapping[str, Any],
        budget: SearchBudget,
        decisions: list[RouteDecision],
        hypotheses: list[SearchHypothesis],
    ) -> list[dict[str, Any]]:
        return [
            {
                "step": "task_analysis",
                "decision": "estimate_complexity",
                "reason": "Search intelligence first estimates the shape of the task.",
            },
            {
                "step": "strategy_selection",
                "decision": strategy.get("strategy"),
                "reason": strategy.get("why_chosen"),
            },
            {
                "step": "budget_allocation",
                "decision": "allocate_dynamic_budget",
                "reason": budget.explanation,
            },
            {
                "step": "route_management",
                "decision": "evaluate_routes",
                "reason": f"{len(decisions)} routes received adaptive decisions.",
            },
            {
                "step": "hypothesis_management",
                "decision": "maintain_multi_hypothesis_set",
                "reason": f"{len([h for h in hypotheses if h.status == 'survived'])} hypotheses survived.",
            },
        ]

    def _policy_decisions(
        self,
        task_complexity: Mapping[str, Any],
        strategy: Mapping[str, Any],
        budget: SearchBudget,
        route_decisions: list[RouteDecision],
        hypotheses: list[SearchHypothesis],
    ) -> list[dict[str, Any]]:
        survived = len([item for item in hypotheses if item.status == "survived"])
        stopped = len([item for item in route_decisions if item.decision in {"Terminate", "Archive", "Suspend"}])
        decisions = [
            {
                "question": "Why this strategy?",
                "answer": strategy.get("why_chosen"),
                "evidence": strategy.get("evidence"),
            },
            {
                "question": "Why this budget?",
                "answer": budget.explanation,
                "evidence": asdict(budget),
            },
            {
                "question": "Why exploration changed?",
                "answer": (
                    "Exploration increases when novelty or complexity is high; otherwise exploitation is favored."
                ),
                "evidence": {
                    "complexity_score": task_complexity.get("complexity_score"),
                    "strategy": strategy.get("strategy"),
                },
            },
            {
                "question": "Why routes stopped?",
                "answer": f"{stopped} routes stopped because risk, low gain, or budget pressure exceeded support.",
                "evidence": [asdict(item) for item in route_decisions if item.decision in {"Terminate", "Archive", "Suspend"}],
            },
            {
                "question": "Why hypotheses survived?",
                "answer": f"{survived} hypotheses retained enough route, concept, or program support.",
                "evidence": [asdict(item) for item in hypotheses if item.status == "survived"],
            },
        ]
        return decisions

    def _route_statistics(
        self,
        decisions: list[RouteDecision],
        routes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        counts = {action: 0 for action in ROUTE_ACTIONS}
        for decision in decisions:
            counts[decision.decision] = counts.get(decision.decision, 0) + 1
        return {
            "routes_observed": len(routes),
            "routes_created": len(routes),
            "expanded_routes": counts.get("Expand", 0),
            "stopped_routes": counts.get("Terminate", 0) + counts.get("Archive", 0) + counts.get("Suspend", 0),
            "promoted_routes": counts.get("Promote", 0),
            "reactivated_routes": counts.get("Reactivate", 0),
            "split_routes": counts.get("Split", 0),
            "merged_routes": counts.get("Merge", 0),
            "action_counts": counts,
        }

    def _program_statistics(self, program_report: Mapping[str, Any]) -> dict[str, Any]:
        programs = int(_number(program_report.get("generated_programs")))
        validated = int(_number(program_report.get("programs_validated")))
        return {
            "programs_available": programs,
            "programs_validated": validated,
            "program_coverage": round(validated / max(programs, 1), 4),
            "program_influence": "HIGH" if programs >= 6 else "LOW",
        }

    def _concept_statistics(self, concept_report: Mapping[str, Any]) -> dict[str, Any]:
        concepts = int(_number(concept_report.get("concept_count")))
        confidence = _number(concept_report.get("confidence"))
        return {
            "concepts_available": concepts,
            "average_confidence": round(confidence, 4),
            "concept_influence": "HIGH" if concepts >= 6 else "LOW",
            "concept_graph_available": bool(concept_report.get("concept_graph")),
        }

    def _strategy_evolution(
        self,
        strategy: Mapping[str, Any],
        decisions: list[RouteDecision],
    ) -> list[dict[str, Any]]:
        high_risk = len([item for item in decisions if item.score.get("failure_risk", 0.0) > 0.7])
        expansion = len([item for item in decisions if item.decision in {"Expand", "Split"}])
        return [
            {
                "phase": "initial",
                "strategy": strategy.get("strategy"),
                "reason": strategy.get("why_chosen"),
            },
            {
                "phase": "route_feedback",
                "strategy_adjustment": "increase_exploitation" if expansion == 0 else "maintain_adaptation",
                "reason": "Route expansion pressure is derived from current decision balance.",
            },
            {
                "phase": "risk_feedback",
                "strategy_adjustment": "reduce_branching" if high_risk > 1 else "allow_branching",
                "reason": "High failure risk reduces branch width; stable evidence permits branching.",
            },
        ]

    def _learning_outcomes(
        self,
        strategy: Mapping[str, Any],
        route_stats: Mapping[str, Any],
        program_stats: Mapping[str, Any],
        concept_stats: Mapping[str, Any],
        memory_summary: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "strategy_learning": (
                f"{strategy.get('strategy')} retained as current template"
                if route_stats.get("promoted_routes", 0) > 0
                else f"{strategy.get('strategy')} requires more validation"
            ),
            "budget_learning": "Route stopping indicates budget pressure is being applied.",
            "concept_search_learning": (
                "Concepts strongly influence route choice."
                if concept_stats.get("concept_influence") == "HIGH"
                else "Concept support remains emerging."
            ),
            "program_search_learning": (
                "Programs provide convergence pressure."
                if program_stats.get("program_influence") == "HIGH"
                else "Program coverage is not yet sufficient to dominate search."
            ),
            "memory_prior": memory_summary,
        }

    def _optimization_candidates(
        self,
        route_stats: Mapping[str, Any],
        program_stats: Mapping[str, Any],
        concept_stats: Mapping[str, Any],
        task_complexity: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        candidates = []
        if route_stats.get("stopped_routes", 0) == 0:
            candidates.append({
                "candidate": "increase_route_pruning",
                "reason": "No stopped routes were observed; future search can prune earlier.",
            })
        if program_stats.get("program_coverage", 0.0) < 0.5:
            candidates.append({
                "candidate": "improve_program_validation",
                "reason": "Validated program coverage is below the adaptive threshold.",
            })
        if concept_stats.get("concept_influence") == "LOW":
            candidates.append({
                "candidate": "increase_concept_expansion",
                "reason": "Concept density is too low to drive search strongly.",
            })
        if task_complexity.get("difficulty") == "DIFFICULT":
            candidates.append({
                "candidate": "hybridize_strategy",
                "reason": "Difficult tasks benefit from joint concept/program/hypothesis control.",
            })
        return candidates or [{
            "candidate": "maintain_current_policy",
            "reason": "Current adaptive controls cover route, program, and concept evidence.",
        }]

    def _list(self, value: Any) -> list[Any]:
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        return []


def _id(prefix: str, *parts: Any) -> str:
    digest = hashlib.sha1(
        "|".join(str(part) for part in parts).encode("utf-8")
    ).hexdigest()[:12]
    return f"{prefix}_{digest}"


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or isinstance(value, bool):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _is_grid(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(row, list) for row in value)
    )


def _small_mapping(value: Any, limit: int = 8) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    payload = {}
    for index, (key, item) in enumerate(value.items()):
        if index >= limit:
            break
        if isinstance(item, (str, int, float, bool)) or item is None:
            payload[str(key)] = item
        elif isinstance(item, Mapping):
            payload[str(key)] = {"keys": sorted(str(k) for k in item.keys())[:8]}
        elif isinstance(item, list):
            payload[str(key)] = {"count": len(item)}
        else:
            payload[str(key)] = type(item).__name__
    return payload


def _count_graph_nodes(value: Any) -> int:
    if not isinstance(value, Mapping):
        return 0
    nodes = value.get("nodes")
    return len(nodes) if isinstance(nodes, list) else 0


adaptive_search_intelligence_engine = AdaptiveSearchIntelligenceEngine()
