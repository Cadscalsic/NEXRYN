"""Cognitive Search Manager and COGNITIVE_SEARCH_REPORT generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import json
import math
from pathlib import Path
from typing import Any

from runtime.search.cognitive_search_runtime import build_cognitive_search_runtime_report
from runtime.search.adaptive_search_policy import (
    AdaptiveSearchPolicyEngine,
    adaptive_search_policy_engine,
)
from runtime.search.cognitive_route_intelligence import (
    CognitiveRouteIntelligenceEngine,
    cognitive_route_intelligence_engine,
)


class SearchRouteState(str, Enum):
    DISCOVERED = "DISCOVERED"
    CREATED = "CREATED"
    EXPLORING = "EXPLORING"
    SUPPORTED = "SUPPORTED"
    PROMISING = "PROMISING"
    STABLE = "STABLE"
    DOMINANT = "DOMINANT"
    COOLING_READY = "COOLING_READY"
    COOLING = "COOLING"
    SUSPENDED = "SUSPENDED"
    REACTIVATED = "REACTIVATED"
    MERGED = "MERGED"
    SPLIT = "SPLIT"
    PRUNED = "PRUNED"
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


@dataclass
class SearchRoute:
    route_id: str
    parent_route: str | None = None
    creation_trigger: str = "search_space_initialization"
    current_state: str = SearchRouteState.CREATED.value
    current_confidence: float = 0.0
    evidence_score: float = 0.0
    expected_information_gain: float = 0.0
    estimated_computational_cost: float = 0.0
    priority: float = 0.0
    depth: int = 0
    branch_width: int = 0
    visited_concepts: list[str] = field(default_factory=list)
    visited_transformations: list[str] = field(default_factory=list)
    visited_programs: list[str] = field(default_factory=list)
    visited_constraints: list[str] = field(default_factory=list)
    validation_status: str = "unknown"
    decision: str = "Expand"
    decision_explanation: str = "Route created for deterministic search observation."
    scores: dict[str, float] = field(default_factory=dict)
    hypotheses: list[dict[str, Any]] = field(default_factory=list)


class SearchMemory:
    """Small persistent ledger for search decisions.

    The memory stores compact decision summaries only. Report generation remains
    deterministic because the current report is computed from the current run;
    persisted entries are exposed as reuse candidates for future phases.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path("runtime_data") / "search_memory.json"

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"entries": []}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"entries": []}
        if not isinstance(payload, dict):
            return {"entries": []}
        payload.setdefault("entries", [])
        return payload

    def remember(self, report: dict[str, Any]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.load()
        entry = {
            "report_type": "COGNITIVE_SEARCH_REPORT",
            "routes_created": report.get("route_statistics", {}).get("routes_created", 0),
            "winning_route": report.get("winning_route", {}).get("route_id"),
            "pruned_routes": len(report.get("pruning_decisions", [])),
            "suspended_routes": report.get("route_statistics", {}).get("routes_suspended", 0),
            "reactivated_routes": report.get("route_statistics", {}).get("routes_reactivated", 0),
            "optimization_candidates": report.get("optimization_candidates", []),
        }
        entries = list(payload.get("entries", []))
        entries.append(entry)
        payload["entries"] = entries[-100:]
        self.path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return {
            "persistent_search_memory": True,
            "memory_path": str(self.path),
            "entries_stored": len(payload["entries"]),
            "latest_entry": entry,
        }


class SearchScoringEngine:
    def score_route(self, route: SearchRoute) -> dict[str, float]:
        evidence = _clamp(route.evidence_score)
        confidence = _clamp(route.current_confidence)
        novelty = _clamp(1.0 / max(route.depth + 1, 1))
        reuse = _clamp(len(route.visited_programs) / max(route.branch_width, 1))
        transformation = _clamp(len(route.visited_transformations) / max(route.branch_width, 1))
        program = _clamp(len(route.visited_programs) / max(route.branch_width, 1))
        generalization = round((evidence + novelty + reuse) / 3.0, 4)
        success = round((confidence * 0.45) + (evidence * 0.35) + (program * 0.20), 4)
        future_value = round(
            (route.expected_information_gain * 0.35)
            + (novelty * 0.25)
            + (success * 0.40),
            4,
        )
        search_cost = _clamp(route.estimated_computational_cost)
        remaining_cost = _clamp(search_cost * (1.0 - success))
        return {
            "evidence_score": evidence,
            "confidence_score": confidence,
            "information_gain": _clamp(route.expected_information_gain),
            "novelty_score": novelty,
            "reuse_score": reuse,
            "transformation_potential": transformation,
            "program_potential": program,
            "generalization_potential": generalization,
            "estimated_success_probability": success,
            "estimated_future_value": future_value,
            "search_cost": search_cost,
            "expected_remaining_cost": remaining_cost,
        }


class CognitiveSearchManager:
    def __init__(
        self,
        memory: SearchMemory | None = None,
        scoring_engine: SearchScoringEngine | None = None,
        policy_engine: AdaptiveSearchPolicyEngine | None = None,
        route_intelligence_engine: CognitiveRouteIntelligenceEngine | None = None,
        persist_memory: bool = True,
    ) -> None:
        self.memory = memory or SearchMemory()
        self.scoring_engine = scoring_engine or SearchScoringEngine()
        self.policy_engine = policy_engine or AdaptiveSearchPolicyEngine(
            persist_memory=persist_memory
        )
        self.route_intelligence_engine = (
            route_intelligence_engine
            or CognitiveRouteIntelligenceEngine(persist_memory=persist_memory)
        )
        self.persist_memory = persist_memory

    def build_report(
        self,
        all_results: list[dict[str, Any]] | None = None,
        cognitive_pipeline_report: dict[str, Any] | None = None,
        solver_reasoning_report: dict[str, Any] | None = None,
        performance_report: dict[str, Any] | None = None,
        adaptive_reuse_report: dict[str, Any] | None = None,
        dependency_report: dict[str, Any] | None = None,
        process_report: dict[str, Any] | None = None,
        causal_context_report: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        routes = self._routes_from_results(all_results or [])
        if not routes:
            routes = self._routes_from_pipeline(cognitive_pipeline_report or {})
        for route in routes:
            route.scores = self.scoring_engine.score_route(route)
            route.current_state = self._state_for(route)
            route.decision, route.decision_explanation = self._policy_decision(route)
        graph = self._search_space_graph(routes)
        report = {
            "COGNITIVE_SEARCH_REPORT": True,
            "search_space_graph": graph,
            "route_statistics": self._route_statistics(routes),
            "search_timeline": self._timeline(routes),
            "search_cost": self._search_cost(routes),
            "route_ranking": self._route_ranking(routes),
            "route_evolution": self._route_evolution(routes),
            "pruning_decisions": [
                self._decision_payload(route)
                for route in routes
                if route.decision in {"Discard", "Archive"} or route.current_state == SearchRouteState.PRUNED.value
            ],
            "merge_history": self._merge_history(routes),
            "split_history": self._split_history(routes),
            "reactivation_history": [
                self._decision_payload(route)
                for route in routes
                if route.current_state == SearchRouteState.REACTIVATED.value
            ],
            "winning_route": self._winning_route(routes),
            "failed_routes": [
                self._route_summary(route)
                for route in routes
                if route.current_state in {SearchRouteState.FAILED.value, SearchRouteState.PRUNED.value}
            ],
            "knowledge_learned": self._knowledge_learned(routes, adaptive_reuse_report or {}),
            "optimization_candidates": self._optimization_candidates(routes),
            "explainability": self._explainability(routes),
            "runtime_alignment": {
                "does_not_solve_tasks": True,
                "solver_logic_modified": False,
                "planner_replaced": False,
                "deterministic_execution": True,
                "reuses_solver_stages": bool(cognitive_pipeline_report),
                "reuses_reasoning_graph": bool(solver_reasoning_report),
                "reuses_runtime_reports": bool(performance_report),
                "reuses_dependency_runtime": bool(dependency_report),
                "reuses_process_runtime": bool(process_report),
                "reuses_causal_runtime": bool(causal_context_report),
                "instrumentation_overhead_budget": "below_3_percent_target",
            },
            "source_reports": {
                "cognitive_pipeline_report": bool(cognitive_pipeline_report),
                "solver_reasoning_report": bool(solver_reasoning_report),
                "performance_report": bool(performance_report),
                "adaptive_reuse_report": bool(adaptive_reuse_report),
            },
        }
        policy_report = self.policy_engine.plan(
            task_analysis=self._policy_task_analysis(all_results or []),
            routes=routes,
            performance_report=performance_report or {},
            search_report=report,
        )
        report["adaptive_search_policy"] = policy_report
        report["ADAPTIVE_SEARCH_POLICY_REPORT"] = policy_report
        route_intelligence_report = self.route_intelligence_engine.build_report(
            routes=routes,
            search_policy_report=policy_report,
            search_report=report,
            performance_report=performance_report or {},
        )
        report["cognitive_route_intelligence"] = route_intelligence_report
        report["COGNITIVE_ROUTE_INTELLIGENCE_REPORT"] = (
            route_intelligence_report
        )
        report["search_memory"] = (
            self.memory.remember(report)
            if self.persist_memory
            else {"persistent_search_memory": False, "reason": "disabled"}
        )
        search_runtime_report = build_cognitive_search_runtime_report(
            routes=routes,
            search_report=report,
            performance_report=performance_report or {},
        )
        report["COGNITIVE_SEARCH_RUNTIME_REPORT"] = True
        report["search_runtime"] = search_runtime_report
        return report

    def _policy_task_analysis(self, all_results: list[dict[str, Any]]) -> dict[str, Any]:
        reports = []
        for item in all_results:
            result = item.get("result", item) if isinstance(item, dict) else {}
            if not isinstance(result, dict):
                continue
            candidates = [
                result.get("task_complexity_report"),
                result.get("task_profile"),
                (result.get("performance_report") or {}).get("task_complexity_report")
                if isinstance(result.get("performance_report"), dict) else None,
            ]
            report = next((value for value in candidates if isinstance(value, dict)), None)
            if report:
                reports.append(report)
        if not reports:
            return {}
        numeric_keys = {
            "grid_size", "total_cells", "object_count", "object_diversity",
            "color_diversity", "spatial_complexity", "topological_complexity",
            "transformation_count", "transformation_complexity",
            "context_complexity", "uncertainty", "historical_similarity",
            "estimated_cost", "process_complexity",
        }
        combined: dict[str, Any] = {}
        for key in numeric_keys:
            values = [_number(report.get(key), 0.0) for report in reports if key in report]
            if values:
                combined[key] = round(sum(values) / len(values), 4)
        combined["target_concepts"] = sorted({
            str(concept)
            for report in reports
            for concept in (report.get("target_concepts") or report.get("concepts") or [])
        })
        combined["required_capabilities"] = sorted({
            str(capability)
            for report in reports
            for capability in (report.get("required_capabilities") or [])
        })
        return combined

    def _routes_from_results(self, all_results: list[dict[str, Any]]) -> list[SearchRoute]:
        routes: list[SearchRoute] = []
        for task_index, item in enumerate(all_results):
            result = item.get("result", item) if isinstance(item, dict) else {}
            if not isinstance(result, dict):
                continue
            task_id = str(item.get("task") or result.get("task_id") or f"task_{task_index}")
            search_result = _mapping(result.get("search_result"))
            paths = search_result.get("paths") if search_result else None
            if isinstance(paths, list) and paths:
                for route_index, path in enumerate(paths):
                    if not isinstance(path, dict):
                        continue
                    routes.append(self._route_from_path(task_id, route_index, path, result))
                continue
            hypotheses = _list_of_dicts(
                result.get("ranked_hypotheses")
                or result.get("hypotheses")
                or []
            )
            for route_index, hypothesis in enumerate(hypotheses):
                routes.append(self._route_from_path(
                    task_id,
                    route_index,
                    {"path_type": "single", "hypotheses": [hypothesis]},
                    result,
                ))
            if not hypotheses and result:
                routes.append(self._route_from_path(
                    task_id,
                    0,
                    {"path_type": "implicit", "hypotheses": []},
                    result,
                ))
        return routes

    def _route_from_path(
        self,
        task_id: str,
        route_index: int,
        path: dict[str, Any],
        result: dict[str, Any],
    ) -> SearchRoute:
        hypotheses = _list_of_dicts(path.get("hypotheses", []))
        confidence = _average([
            _number(hypothesis.get("confidence"), 0.0)
            for hypothesis in hypotheses
        ])
        evidence = _average([
            max(
                _number(hypothesis.get("explanatory_power"), 0.0),
                _number(hypothesis.get("residual_reduction"), 0.0),
                _number(hypothesis.get("causal_support"), 0.0),
                _number(hypothesis.get("semantic_support"), 0.0),
            )
            for hypothesis in hypotheses
        ])
        score = _number(path.get("score"), confidence)
        validation = _mapping(result.get("evaluation_result"))
        program = _mapping(result.get("synthesized_program"))
        transformations = [
            str(hypothesis.get("primitive") or hypothesis.get("type") or "unknown")
            for hypothesis in hypotheses
        ]
        route = SearchRoute(
            route_id=f"{_stable_id(task_id)}:route:{route_index}",
            parent_route=None,
            creation_trigger=str(path.get("path_type", "hypothesis_path")),
            current_confidence=round(max(confidence, score), 4),
            evidence_score=round(evidence, 4),
            expected_information_gain=round(max(score - evidence, 0.0), 4),
            estimated_computational_cost=round(
                (len(hypotheses) * 0.08)
                + (_number(program.get("step_count"), 0.0) * 0.05)
                + (_number(validation.get("difference_count"), 0.0) * 0.02),
                4,
            ),
            priority=round(score, 4),
            depth=max(1, len(hypotheses)),
            branch_width=max(1, len(hypotheses)),
            visited_concepts=sorted({
                str(hypothesis.get("semantic_class") or hypothesis.get("type") or "hypothesis")
                for hypothesis in hypotheses
            }),
            visited_transformations=transformations,
            visited_programs=(
                [f"program_steps:{program.get('step_count', 0)}"]
                if program else []
            ),
            visited_constraints=_constraints_from_result(result),
            validation_status=_validation_status(validation),
            hypotheses=hypotheses,
        )
        return route

    def _routes_from_pipeline(self, report: dict[str, Any]) -> list[SearchRoute]:
        timeline = report.get("stage_timeline", [])
        routes = []
        for index, event in enumerate(timeline if isinstance(timeline, list) else []):
            if not isinstance(event, dict):
                continue
            stage_id = str(event.get("stage_id", "stage"))
            if stage_id not in {
                "hypothesis_generation",
                "hypothesis_expansion",
                "transformation_discovery",
                "program_synthesis",
                "candidate_validation",
            }:
                continue
            routes.append(SearchRoute(
                route_id=f"pipeline:{stage_id}:{index}",
                creation_trigger=f"pipeline_stage:{stage_id}",
                current_confidence=_number(event.get("confidence"), 0.0),
                evidence_score=1.0 if event.get("execution_status") == "completed" else 0.0,
                expected_information_gain=0.5,
                estimated_computational_cost=_number(event.get("duration"), 0.0),
                priority=_number(event.get("confidence"), 0.0),
                depth=index + 1,
                branch_width=1,
                visited_concepts=list(event.get("generated_concepts", [])),
                visited_programs=(
                    ["pipeline_program"]
                    if stage_id == "program_synthesis" else []
                ),
                validation_status=(
                    "validated"
                    if stage_id == "candidate_validation"
                    and event.get("execution_status") == "completed"
                    else "unknown"
                ),
            ))
        return routes

    def _state_for(self, route: SearchRoute) -> str:
        if route.validation_status == "validated":
            return SearchRouteState.VALIDATED.value
        if route.validation_status == "failed":
            return SearchRouteState.FAILED.value
        if route.scores.get("estimated_success_probability", 0.0) >= 0.85:
            return SearchRouteState.STABLE.value
        if route.scores.get("estimated_future_value", 0.0) >= 0.65:
            return SearchRouteState.PROMISING.value
        if route.evidence_score >= 0.5:
            return SearchRouteState.SUPPORTED.value
        if (
            route.current_confidence < 0.25
            and route.evidence_score < 0.25
            and route.estimated_computational_cost > 0.25
        ):
            return SearchRouteState.PRUNED.value
        if route.current_confidence < 0.35 and route.evidence_score < 0.35:
            return SearchRouteState.SUSPENDED.value
        return SearchRouteState.EXPLORING.value

    def _policy_decision(self, route: SearchRoute) -> tuple[str, str]:
        scores = route.scores
        if route.current_state == SearchRouteState.VALIDATED.value:
            return "Validate", "Route produced a validated candidate solution."
        if route.current_state == SearchRouteState.FAILED.value:
            return "Archive", "Route failed validation and is retained as negative search memory."
        if route.current_state == SearchRouteState.PRUNED.value:
            return "Discard", "Low confidence, weak evidence, and high relative search cost."
        if route.current_state == SearchRouteState.SUSPENDED.value:
            if scores.get("information_gain", 0.0) > 0.4:
                route.current_state = SearchRouteState.REACTIVATED.value
                return "Reuse", "Suspended route recovered because information gain remains useful."
            return "Pause", "Weak evidence route is suspended without deletion."
        if route.current_state in {
            SearchRouteState.PROMISING.value,
            SearchRouteState.STABLE.value,
            SearchRouteState.SUPPORTED.value,
        }:
            return "Expand", "Evidence and expected future value justify continued exploration."
        if route.branch_width > 1:
            return "Split", "Combined route contains multiple hypotheses and can be split for analysis."
        return "Expand", "Route remains active in the deterministic search frontier."

    def _search_space_graph(self, routes: list[SearchRoute]) -> dict[str, Any]:
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        for route in routes:
            nodes.append({
                "id": route.route_id,
                "type": "SearchRoute",
                "state": route.current_state,
                "priority": route.priority,
            })
            if route.parent_route:
                edges.append({"from": route.parent_route, "to": route.route_id, "type": "extends"})
            for index, hypothesis in enumerate(route.hypotheses):
                hyp_id = f"{route.route_id}:hypothesis:{index}"
                nodes.append({
                    "id": hyp_id,
                    "type": "Hypothesis",
                    "label": str(hypothesis.get("type") or hypothesis.get("primitive") or "hypothesis"),
                })
                edges.append({"from": hyp_id, "to": route.route_id, "type": "supports"})
            for transformation in route.visited_transformations:
                trans_id = f"{route.route_id}:transformation:{_stable_id(transformation)}"
                nodes.append({"id": trans_id, "type": "Transformation", "label": transformation})
                edges.append({"from": route.route_id, "to": trans_id, "type": "generated_from"})
            for program in route.visited_programs:
                program_id = f"{route.route_id}:program:{_stable_id(program)}"
                nodes.append({"id": program_id, "type": "Program", "label": program})
                edges.append({"from": route.route_id, "to": program_id, "type": "generated_from"})
                if route.validation_status in {"validated", "failed"}:
                    edges.append({
                        "from": program_id,
                        "to": route.route_id,
                        "type": "validated_by" if route.validation_status == "validated" else "rejected_by",
                    })
            for constraint in route.visited_constraints:
                constraint_id = f"{route.route_id}:constraint:{_stable_id(constraint)}"
                nodes.append({"id": constraint_id, "type": "Constraint", "label": constraint})
                edges.append({"from": route.route_id, "to": constraint_id, "type": "depends_on"})
        return {"nodes": nodes, "edges": edges}

    def _route_statistics(self, routes: list[SearchRoute]) -> dict[str, Any]:
        states = _counts(route.current_state for route in routes)
        return {
            "search_space_size": len(routes),
            "routes_created": len(routes),
            "routes_active": sum(1 for route in routes if route.current_state in {
                SearchRouteState.EXPLORING.value,
                SearchRouteState.SUPPORTED.value,
                SearchRouteState.PROMISING.value,
                SearchRouteState.STABLE.value,
                SearchRouteState.VALIDATED.value,
            }),
            "routes_suspended": states.get(SearchRouteState.SUSPENDED.value, 0),
            "routes_reactivated": states.get(SearchRouteState.REACTIVATED.value, 0),
            "routes_pruned": states.get(SearchRouteState.PRUNED.value, 0),
            "routes_merged": states.get(SearchRouteState.MERGED.value, 0),
            "routes_split": sum(1 for route in routes if route.decision == "Split"),
            "average_route_depth": round(_average([route.depth for route in routes]), 4),
            "average_branch_width": round(_average([route.branch_width for route in routes]), 4),
            "search_entropy": _entropy([route.priority for route in routes]),
            "search_efficiency": self._efficiency(routes),
            "search_cost": round(sum(route.scores.get("search_cost", 0.0) for route in routes), 4),
            "search_coverage": round(
                len({concept for route in routes for concept in route.visited_concepts})
                / max(len(routes), 1),
                4,
            ),
            "search_stability": round(
                states.get(SearchRouteState.STABLE.value, 0)
                / max(len(routes), 1),
                4,
            ),
            "states": states,
        }

    def _timeline(self, routes: list[SearchRoute]) -> list[dict[str, Any]]:
        return [
            {
                "route_id": route.route_id,
                "state": route.current_state,
                "decision": route.decision,
                "confidence": route.current_confidence,
                "evidence_score": route.evidence_score,
                "priority": route.priority,
                "explanation": route.decision_explanation,
            }
            for route in routes
        ]

    def _search_cost(self, routes: list[SearchRoute]) -> dict[str, Any]:
        expensive = max(
            routes,
            key=lambda route: route.scores.get("search_cost", 0.0),
            default=None,
        )
        return {
            "total_search_cost": round(sum(route.scores.get("search_cost", 0.0) for route in routes), 4),
            "expected_remaining_cost": round(sum(route.scores.get("expected_remaining_cost", 0.0) for route in routes), 4),
            "most_expensive_route": self._route_summary(expensive) if expensive else {},
        }

    def _route_ranking(self, routes: list[SearchRoute]) -> list[dict[str, Any]]:
        ranked = sorted(
            routes,
            key=lambda route: (
                route.scores.get("estimated_success_probability", 0.0),
                route.scores.get("estimated_future_value", 0.0),
                route.priority,
            ),
            reverse=True,
        )
        return [self._route_summary(route) for route in ranked]

    def _route_evolution(self, routes: list[SearchRoute]) -> list[dict[str, Any]]:
        return [
            {
                "route_id": route.route_id,
                "creation_trigger": route.creation_trigger,
                "state": route.current_state,
                "depth": route.depth,
                "branch_width": route.branch_width,
                "visited_concepts": list(route.visited_concepts),
                "visited_transformations": list(route.visited_transformations),
                "visited_programs": list(route.visited_programs),
            }
            for route in routes
        ]

    def _merge_history(self, routes: list[SearchRoute]) -> list[dict[str, Any]]:
        return [
            {
                "route_id": route.route_id,
                "merge_type": "combined_hypothesis_path",
                "merged_hypotheses": len(route.hypotheses),
            }
            for route in routes
            if route.creation_trigger == "combined"
        ]

    def _split_history(self, routes: list[SearchRoute]) -> list[dict[str, Any]]:
        return [
            {
                "route_id": route.route_id,
                "split_reason": route.decision_explanation,
                "branch_width": route.branch_width,
            }
            for route in routes
            if route.decision == "Split"
        ]

    def _winning_route(self, routes: list[SearchRoute]) -> dict[str, Any]:
        if not routes:
            return {}
        winners = [route for route in routes if route.validation_status == "validated"]
        route = max(
            winners or routes,
            key=lambda item: (
                item.validation_status == "validated",
                item.scores.get("estimated_success_probability", 0.0),
                item.scores.get("estimated_future_value", 0.0),
            ),
        )
        payload = self._route_summary(route)
        payload["why_it_won"] = (
            "Route won because it validated successfully."
            if route.validation_status == "validated"
            else "Route has the highest estimated success and future value."
        )
        return payload

    def _knowledge_learned(
        self,
        routes: list[SearchRoute],
        adaptive_reuse_report: dict[str, Any],
    ) -> dict[str, Any]:
        successful = [route.route_id for route in routes if route.validation_status == "validated"]
        failed = [route.route_id for route in routes if route.current_state in {
            SearchRouteState.FAILED.value,
            SearchRouteState.PRUNED.value,
        }]
        return {
            "successful_search_routes": successful,
            "failed_search_routes": failed,
            "winning_exploration_patterns": sorted({
                route.creation_trigger for route in routes if route.route_id in successful
            }),
            "pruning_decisions_learned": [
                route.route_id for route in routes if route.decision == "Discard"
            ],
            "merge_decisions_learned": [
                route.route_id for route in routes if route.creation_trigger == "combined"
            ],
            "split_decisions_learned": [
                route.route_id for route in routes if route.decision == "Split"
            ],
            "reactivation_events_learned": [
                route.route_id for route in routes if route.current_state == SearchRouteState.REACTIVATED.value
            ],
            "useful_search_templates": sorted({
                route.creation_trigger for route in routes if route.current_state in {
                    SearchRouteState.VALIDATED.value,
                    SearchRouteState.STABLE.value,
                    SearchRouteState.PROMISING.value,
                }
            }),
            "adaptive_reuse_bridge": {
                "reuse_report_available": bool(adaptive_reuse_report),
                "search_memory_can_feed_adaptive_reuse": True,
            },
        }

    def _optimization_candidates(self, routes: list[SearchRoute]) -> list[dict[str, Any]]:
        candidates = []
        if not routes:
            return candidates
        expensive = max(routes, key=lambda route: route.scores.get("search_cost", 0.0))
        low_gain = min(routes, key=lambda route: route.scores.get("estimated_future_value", 1.0))
        wide = max(routes, key=lambda route: route.branch_width)
        candidates.extend([
            {
                "target": expensive.route_id,
                "reason": "highest_search_cost",
                "recommendation": "profile_route_expansion_and_validation",
                "evidence": expensive.scores.get("search_cost", 0.0),
            },
            {
                "target": low_gain.route_id,
                "reason": "lowest_expected_future_value",
                "recommendation": "consider_suspension_or_pruning",
                "evidence": low_gain.scores.get("estimated_future_value", 0.0),
            },
            {
                "target": wide.route_id,
                "reason": "largest_branch_width",
                "recommendation": "consider_split_or_acsc_cooling",
                "evidence": wide.branch_width,
            },
        ])
        return candidates

    def _explainability(self, routes: list[SearchRoute]) -> dict[str, Any]:
        expensive = max(
            routes,
            key=lambda route: route.scores.get("search_cost", 0.0),
            default=None,
        )
        decisive = max(
            routes,
            key=lambda route: route.evidence_score,
            default=None,
        )
        return {
            "which_search_route_won": self._winning_route(routes),
            "why_it_won": self._winning_route(routes).get("why_it_won"),
            "which_routes_failed": [
                self._route_summary(route)
                for route in routes
                if route.current_state in {SearchRouteState.FAILED.value, SearchRouteState.PRUNED.value}
            ],
            "why_routes_failed": [
                self._decision_payload(route)
                for route in routes
                if route.current_state in {SearchRouteState.FAILED.value, SearchRouteState.PRUNED.value}
            ],
            "route_consuming_most_computation": self._route_summary(expensive) if expensive else {},
            "route_producing_decisive_evidence": self._route_summary(decisive) if decisive else {},
        }

    def _efficiency(self, routes: list[SearchRoute]) -> float:
        success = sum(
            route.scores.get("estimated_success_probability", 0.0)
            for route in routes
        )
        cost = sum(route.scores.get("search_cost", 0.0) for route in routes)
        return round(success / max(cost, 0.0001), 4)

    def _decision_payload(self, route: SearchRoute) -> dict[str, Any]:
        return {
            "route_id": route.route_id,
            "state": route.current_state,
            "decision": route.decision,
            "reason": route.decision_explanation,
            "evidence_score": route.evidence_score,
            "confidence": route.current_confidence,
            "search_cost": route.scores.get("search_cost", 0.0),
            "expected_future_value": route.scores.get("estimated_future_value", 0.0),
        }

    def _route_summary(self, route: SearchRoute | None) -> dict[str, Any]:
        if route is None:
            return {}
        payload = asdict(route)
        payload.pop("hypotheses", None)
        return payload


def build_cognitive_search_report(
    all_results: list[dict[str, Any]] | None = None,
    cognitive_pipeline_report: dict[str, Any] | None = None,
    solver_reasoning_report: dict[str, Any] | None = None,
    performance_report: dict[str, Any] | None = None,
    adaptive_reuse_report: dict[str, Any] | None = None,
    dependency_report: dict[str, Any] | None = None,
    process_report: dict[str, Any] | None = None,
    causal_context_report: dict[str, Any] | None = None,
    persist_memory: bool = True,
) -> dict[str, Any]:
    return CognitiveSearchManager(persist_memory=persist_memory).build_report(
        all_results=all_results,
        cognitive_pipeline_report=cognitive_pipeline_report,
        solver_reasoning_report=solver_reasoning_report,
        performance_report=performance_report,
        adaptive_reuse_report=adaptive_reuse_report,
        dependency_report=dependency_report,
        process_report=process_report,
        causal_context_report=causal_context_report,
    )


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: Any, default: float = 0.0) -> float:
    return round(max(0.0, min(1.0, _number(value, default))), 4)


def _average(values: list[float]) -> float:
    values = [float(value) for value in values]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def _entropy(values: list[float]) -> float:
    total = sum(max(value, 0.0) for value in values)
    if total <= 0:
        return 0.0
    entropy = 0.0
    for value in values:
        probability = max(value, 0.0) / total
        if probability > 0:
            entropy -= probability * math.log2(probability)
    max_entropy = math.log2(max(len(values), 1))
    if max_entropy <= 0:
        return 0.0
    return round(entropy / max_entropy, 4)


def _counts(values) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _stable_id(value: Any) -> str:
    text = str(value).replace("\\", "/")
    return "".join(char.lower() if char.isalnum() else "_" for char in text).strip("_")[:80] or "route"


def _validation_status(validation: dict[str, Any]) -> str:
    if validation.get("success") is True:
        return "validated"
    if validation.get("success") is False:
        return "failed"
    state = str(validation.get("success_state", "")).upper()
    if state == "SUCCESS":
        return "validated"
    if state in {"FAILED", "FAILURE"}:
        return "failed"
    return "unknown"


def _constraints_from_result(result: dict[str, Any]) -> list[str]:
    constraints = []
    gate = _mapping(result.get("world_model_gate"))
    if gate:
        constraints.append(str(gate.get("gate_state", "world_model_gate")))
    readiness = _mapping(result.get("execution_readiness_report"))
    for item in readiness.get("blocking_factors", []) if isinstance(readiness.get("blocking_factors"), list) else []:
        constraints.append(str(item))
    return constraints


__all__ = [
    "CognitiveSearchManager",
    "SearchMemory",
    "SearchRoute",
    "SearchRouteState",
    "SearchScoringEngine",
    "build_cognitive_search_report",
]
