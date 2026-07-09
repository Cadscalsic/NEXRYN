"""First-class runtime ownership for cognitive search routes."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence


SEARCH_RUNTIME_LIFECYCLE = [
    "route_creation",
    "route_expansion",
    "evidence_collection",
    "route_ranking",
    "route_cooling",
    "route_reactivation",
    "route_merge",
    "route_split",
    "route_validation",
]


@dataclass
class CognitiveSearchRuntimeRecord:
    runtime_id: str = "search_runtime"
    runtime_name: str = "Cognitive Search Runtime"
    owner: str = "search_runtime"
    execution_id: str = "search_runtime:synthetic_execution"
    lifecycle: list[str] = field(default_factory=lambda: list(SEARCH_RUNTIME_LIFECYCLE))
    status: str = "EMERGING"
    metrics: dict[str, Any] = field(default_factory=dict)
    graph: dict[str, Any] = field(default_factory=dict)
    snapshots: list[dict[str, Any]] = field(default_factory=list)
    telemetry: dict[str, Any] = field(default_factory=dict)
    coverage: dict[str, Any] = field(default_factory=dict)
    acsc_route_targets: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["COGNITIVE_SEARCH_RUNTIME_REPORT"] = True
        return payload


class CognitiveSearchRuntime:
    """Runtime view over search routes without changing solver behavior."""

    def build_report(
        self,
        routes: Sequence[Any] | None = None,
        search_report: Mapping[str, Any] | None = None,
        performance_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        route_payloads = self._route_payloads(routes or [], search_report or {})
        graph = self._graph(route_payloads, search_report or {})
        metrics = self._metrics(route_payloads, search_report or {}, performance_report or {})
        snapshots = self._snapshots(route_payloads, search_report or {})
        acsc_targets = self._acsc_targets(route_payloads)
        telemetry = self._telemetry(route_payloads, metrics, performance_report or {})
        coverage = self._coverage(metrics, graph, snapshots, acsc_targets)
        status = "OPERATIONAL" if coverage["coverage_score"] >= 0.75 else "EMERGING"
        return CognitiveSearchRuntimeRecord(
            execution_id=telemetry["execution_id"],
            status=status,
            metrics=metrics,
            graph=graph,
            snapshots=snapshots,
            telemetry=telemetry,
            coverage=coverage,
            acsc_route_targets=acsc_targets,
        ).as_dict()

    def _route_payloads(
        self,
        routes: Sequence[Any],
        search_report: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        payloads = [self._route_payload(route) for route in routes]
        payloads = [payload for payload in payloads if payload.get("route_id")]
        if payloads:
            return payloads
        ranking = search_report.get("route_ranking")
        if isinstance(ranking, list) and ranking:
            return [dict(item) for item in ranking if isinstance(item, Mapping)]
        evolution = search_report.get("route_evolution")
        if isinstance(evolution, list) and evolution:
            return [dict(item) for item in evolution if isinstance(item, Mapping)]
        graph = search_report.get("search_space_graph")
        if isinstance(graph, Mapping):
            return [
                {"route_id": str(node.get("id")), "current_state": str(node.get("state", "CREATED"))}
                for node in graph.get("nodes", [])
                if isinstance(node, Mapping) and node.get("type") == "SearchRoute"
            ]
        return []

    def _route_payload(self, route: Any) -> dict[str, Any]:
        if isinstance(route, Mapping):
            return dict(route)
        scores = getattr(route, "scores", {}) or {}
        return {
            "route_id": getattr(route, "route_id", None),
            "parent_route": getattr(route, "parent_route", None),
            "creation_trigger": getattr(route, "creation_trigger", "search_space_initialization"),
            "current_state": getattr(route, "current_state", "CREATED"),
            "current_confidence": getattr(route, "current_confidence", 0.0),
            "evidence_score": getattr(route, "evidence_score", 0.0),
            "expected_information_gain": getattr(route, "expected_information_gain", 0.0),
            "estimated_computational_cost": getattr(route, "estimated_computational_cost", 0.0),
            "priority": getattr(route, "priority", 0.0),
            "depth": getattr(route, "depth", 0),
            "branch_width": getattr(route, "branch_width", 0),
            "visited_concepts": list(getattr(route, "visited_concepts", []) or []),
            "visited_transformations": list(getattr(route, "visited_transformations", []) or []),
            "visited_programs": list(getattr(route, "visited_programs", []) or []),
            "visited_constraints": list(getattr(route, "visited_constraints", []) or []),
            "validation_status": getattr(route, "validation_status", "unknown"),
            "decision": getattr(route, "decision", "Expand"),
            "decision_explanation": getattr(route, "decision_explanation", ""),
            "scores": dict(scores) if isinstance(scores, Mapping) else {},
        }

    def _metrics(
        self,
        routes: list[dict[str, Any]],
        search_report: Mapping[str, Any],
        performance_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        stats = search_report.get("route_statistics")
        stats = stats if isinstance(stats, Mapping) else {}
        route_count = max(len(routes), _number(stats.get("routes_created")))
        states = stats.get("states") if isinstance(stats.get("states"), Mapping) else {}
        return {
            "search_time_seconds": round(_number(performance_report.get("search_time_seconds")), 6),
            "search_routes": route_count,
            "routes_created": route_count,
            "routes_active": max(_number(stats.get("routes_active")), self._count_states(routes, {
                "EXPLORING", "SUPPORTED", "PROMISING", "STABLE", "VALIDATED"
            })),
            "routes_suspended": max(_number(stats.get("routes_suspended")), _number(states.get("SUSPENDED"))),
            "routes_reactivated": max(_number(stats.get("routes_reactivated")), _number(states.get("REACTIVATED"))),
            "routes_pruned": max(_number(stats.get("routes_pruned")), _number(states.get("PRUNED"))),
            "routes_merged": max(_number(stats.get("routes_merged")), _number(states.get("MERGED"))),
            "routes_split": max(_number(stats.get("routes_split")), self._decision_count(routes, "Split")),
            "average_route_depth": _number(stats.get("average_route_depth")) or self._average(routes, "depth"),
            "average_branch_width": _number(stats.get("average_branch_width")) or self._average(routes, "branch_width"),
            "search_entropy": _number(stats.get("search_entropy")),
            "search_efficiency": _number(stats.get("search_efficiency")),
            "search_cost": _number(stats.get("search_cost")),
            "search_coverage": _number(stats.get("search_coverage")),
            "search_stability": _number(stats.get("search_stability")),
            "cooling_candidates": len(self._acsc_targets(routes)),
        }

    def _graph(
        self,
        routes: list[dict[str, Any]],
        search_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        graph = search_report.get("search_space_graph")
        if isinstance(graph, Mapping) and graph.get("nodes"):
            return dict(graph)
        nodes = [{"id": route["route_id"], "type": "SearchRoute", "state": route.get("current_state")} for route in routes]
        edges = [
            {"from": route["parent_route"], "to": route["route_id"], "type": "extends"}
            for route in routes
            if route.get("parent_route")
        ]
        return {"nodes": nodes, "edges": edges}

    def _snapshots(
        self,
        routes: list[dict[str, Any]],
        search_report: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        snapshots = [
            {"snapshot_type": "route_registry", "items": len(routes)},
            {"snapshot_type": "search_lifecycle", "items": len(SEARCH_RUNTIME_LIFECYCLE)},
        ]
        for key in ("search_timeline", "route_ranking", "route_evolution"):
            value = search_report.get(key)
            if isinstance(value, list):
                snapshots.append({"snapshot_type": key, "items": len(value)})
        snapshots.append({"snapshot_type": "route_cooling_plan", "items": len(self._acsc_targets(routes))})
        return snapshots

    def _telemetry(
        self,
        routes: list[dict[str, Any]],
        metrics: Mapping[str, Any],
        performance_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        execution_id = str(
            performance_report.get("search_execution_id")
            or performance_report.get("execution_id")
            or "search_runtime:unbound_execution"
        )
        return {
            "execution_id": execution_id,
            "runtime_name": "Cognitive Search Runtime",
            "owner": "search_runtime",
            "route_count": len(routes),
            "search_routes_materialized": metrics.get("search_routes", 0) > 0,
            "instrumentation_overhead_budget": "below_3_percent_target",
            "deterministic_execution": True,
        }

    def _coverage(
        self,
        metrics: Mapping[str, Any],
        graph: Mapping[str, Any],
        snapshots: list[dict[str, Any]],
        acsc_targets: list[dict[str, Any]],
    ) -> dict[str, Any]:
        score = 0.0
        score += 0.25 if metrics.get("search_routes", 0) > 0 else 0.0
        score += 0.25 if graph.get("nodes") else 0.0
        score += 0.25 if snapshots else 0.0
        score += 0.25 if acsc_targets else 0.0
        return {
            "coverage_score": round(score, 4),
            "coverage_percentage": round(score * 100.0, 2),
            "routes_observable": metrics.get("search_routes", 0) > 0,
            "route_cooling_ready": bool(acsc_targets),
        }

    def _acsc_targets(self, routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        targets = []
        for route in routes:
            route_id = route.get("route_id")
            if not route_id:
                continue
            scores = route.get("scores") if isinstance(route.get("scores"), Mapping) else {}
            targets.append({
                "route_id": route_id,
                "state": route.get("current_state") or route.get("state", "CREATED"),
                "cooling_priority": self._cooling_priority(route, scores),
                "reason": self._cooling_reason(route, scores),
            })
        return sorted(targets, key=lambda item: item["cooling_priority"], reverse=True)

    def _cooling_priority(self, route: Mapping[str, Any], scores: Mapping[str, Any]) -> float:
        cost = _number(scores.get("search_cost") or route.get("estimated_computational_cost"))
        future = _number(scores.get("estimated_future_value") or route.get("expected_information_gain"))
        confidence = _number(route.get("current_confidence") or route.get("confidence"))
        return round(max(cost, 0.0) * (1.0 - min(future + confidence, 1.0) / 2.0), 4)

    def _cooling_reason(self, route: Mapping[str, Any], scores: Mapping[str, Any]) -> str:
        state = str(route.get("current_state") or route.get("state", "CREATED"))
        if state in {"SUSPENDED", "PRUNED", "FAILED"}:
            return "route_is_low_value_or_failed_but_retained_for_reactivation"
        if _number(scores.get("search_cost") or route.get("estimated_computational_cost")) > 0.25:
            return "route_has_high_search_cost"
        return "route_available_for_future_acsc_policy"

    def _count_states(self, routes: list[dict[str, Any]], states: set[str]) -> int:
        return sum(1 for route in routes if str(route.get("current_state") or route.get("state")) in states)

    def _decision_count(self, routes: list[dict[str, Any]], decision: str) -> int:
        return sum(1 for route in routes if route.get("decision") == decision)

    def _average(self, routes: list[dict[str, Any]], field_name: str) -> float:
        values = [_number(route.get(field_name)) for route in routes]
        values = [value for value in values if value > 0.0]
        return round(sum(values) / max(len(values), 1), 4)


def build_cognitive_search_runtime_report(
    routes: Sequence[Any] | None = None,
    search_report: Mapping[str, Any] | None = None,
    performance_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return CognitiveSearchRuntime().build_report(
        routes=routes,
        search_report=search_report,
        performance_report=performance_report,
    )


def _number(value: Any) -> float:
    if isinstance(value, bool):
        return float(value)
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


__all__ = [
    "CognitiveSearchRuntime",
    "CognitiveSearchRuntimeRecord",
    "SEARCH_RUNTIME_LIFECYCLE",
    "build_cognitive_search_runtime_report",
]
