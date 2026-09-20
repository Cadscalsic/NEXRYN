"""Post-execution analytics for completed cognitive search routes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Iterable, Mapping


TERMINAL_SUCCESS_STATES = {"VALIDATED", "STABLE", "DOMINANT", "SUPPORTED", "PROMISING"}
TERMINAL_FAILURE_STATES = {"FAILED", "PRUNED", "ARCHIVED"}
RECOVERY_STATES = {"REACTIVATED"}

QUALITY_COMPONENT_WEIGHTS = {
    "coverage": 0.16,
    "efficiency": 0.16,
    "diversity": 0.12,
    "entropy": 0.10,
    "stability": 0.10,
    "consistency": 0.10,
    "completion": 0.10,
    "success": 0.10,
    "recovery": 0.06,
}


@dataclass(frozen=True)
class RouteAnalysis:
    route_id: str
    route_length: int
    route_cost: float
    route_quality: float
    route_success: bool
    route_confidence: float
    route_reason: str
    route_dependencies: list[str]
    route_reuse: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class SearchAnalyticsEngine:
    """Authoritative search quality metrics for completed search executions."""

    system_name = "search_analytics_engine"

    def build_report(
        self,
        *,
        routes: Iterable[Any] | None = None,
        search_report: Mapping[str, Any] | None = None,
        performance_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        route_payloads = self._routes(routes, search_report or {})
        performance = performance_report if isinstance(performance_report, Mapping) else {}
        route_analysis = [self._route_analysis(route) for route in route_payloads]
        metrics = self._metrics(route_payloads, route_analysis, performance)
        quality_components = {
            "coverage": metrics["search_coverage"],
            "efficiency": metrics["search_efficiency"],
            "diversity": metrics["search_diversity"],
            "entropy": metrics["search_entropy"],
            "stability": metrics["search_stability"],
            "consistency": metrics["search_consistency"],
            "completion": metrics["search_completion_ratio"],
            "success": metrics["search_success_ratio"],
            "recovery": metrics["search_recovery_ratio"],
        }
        overall = round(
            sum(
                quality_components[component] * weight
                for component, weight in QUALITY_COMPONENT_WEIGHTS.items()
            ),
            4,
        )
        best = max(route_analysis, key=lambda item: item["route_quality"], default={})
        worst = min(route_analysis, key=lambda item: item["route_quality"], default={})
        diagnostics = self._diagnostics(route_payloads, route_analysis, metrics)
        return {
            "system": self.system_name,
            "SEARCH_ANALYTICS_REPORT": True,
            "search_analytics_authority": True,
            "routes_analyzed": len(route_payloads),
            "route_analysis": route_analysis,
            "overall_search_quality": overall,
            "search_quality_components": quality_components,
            "search_quality_reason": self._quality_reason(quality_components, overall),
            **metrics,
            "average_route_quality": round(
                sum(item["route_quality"] for item in route_analysis)
                / max(len(route_analysis), 1),
                4,
            ),
            "best_route": best,
            "worst_route": worst,
            "route_distribution": self._route_distribution(route_payloads, route_analysis),
            "search_diagnostics": diagnostics,
            "analytics_generation_success": bool(route_payloads),
            "analytics_generation_failures": [] if route_payloads else ["no_search_routes"],
        }

    def _routes(
        self,
        routes: Iterable[Any] | None,
        search_report: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        payloads = [self._route_payload(route) for route in routes or []]
        payloads = [payload for payload in payloads if payload.get("route_id")]
        if payloads:
            return payloads
        for key in ("route_ranking", "route_evolution", "search_timeline"):
            value = search_report.get(key)
            if isinstance(value, list) and value:
                payloads = [
                    self._route_payload(item)
                    for item in value
                    if isinstance(item, Mapping)
                ]
                payloads = [payload for payload in payloads if payload.get("route_id")]
                if payloads:
                    return payloads
        graph = search_report.get("search_space_graph")
        if isinstance(graph, Mapping):
            return [
                self._route_payload({
                    "route_id": node.get("id"),
                    "current_state": node.get("state", "CREATED"),
                    "priority": node.get("priority", 0.0),
                })
                for node in graph.get("nodes", [])
                if isinstance(node, Mapping) and node.get("type") == "SearchRoute"
            ]
        return []

    def _route_payload(self, route: Any) -> dict[str, Any]:
        if isinstance(route, Mapping):
            payload = dict(route)
        else:
            payload = {
                "route_id": getattr(route, "route_id", None),
                "parent_route": getattr(route, "parent_route", None),
                "creation_trigger": getattr(route, "creation_trigger", ""),
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
                "decision": getattr(route, "decision", ""),
                "decision_explanation": getattr(route, "decision_explanation", ""),
                "scores": dict(getattr(route, "scores", {}) or {}),
            }
        scores = payload.get("scores") if isinstance(payload.get("scores"), Mapping) else {}
        payload["route_id"] = str(payload.get("route_id") or payload.get("id") or "")
        payload["current_state"] = str(
            payload.get("current_state") or payload.get("state") or "CREATED"
        )
        payload["depth"] = int(_number(payload.get("depth"), default=0))
        payload["branch_width"] = int(_number(payload.get("branch_width"), default=0))
        payload["current_confidence"] = max(
            _number(payload.get("current_confidence")),
            _number(payload.get("confidence")),
            _number(scores.get("confidence_score")),
        )
        payload["estimated_computational_cost"] = max(
            _number(payload.get("estimated_computational_cost")),
            _number(payload.get("search_cost")),
            _number(scores.get("search_cost")),
        )
        payload["expected_information_gain"] = max(
            _number(payload.get("expected_information_gain")),
            _number(scores.get("information_gain")),
            _number(scores.get("estimated_future_value")),
        )
        payload["visited_concepts"] = _as_list(payload.get("visited_concepts"))
        payload["visited_transformations"] = _as_list(payload.get("visited_transformations"))
        payload["visited_programs"] = _as_list(payload.get("visited_programs"))
        payload["visited_constraints"] = _as_list(payload.get("visited_constraints"))
        payload["scores"] = dict(scores)
        return payload

    def _route_analysis(self, route: Mapping[str, Any]) -> dict[str, Any]:
        route_id = str(route.get("route_id"))
        state = str(route.get("current_state") or "CREATED").upper()
        dependencies = sorted(
            str(item)
            for item in (
                _as_list(route.get("visited_concepts"))
                + _as_list(route.get("visited_transformations"))
                + _as_list(route.get("visited_constraints"))
            )
            if item
        )
        route_length = max(
            int(_number(route.get("depth"))),
            len(dependencies),
            len(_as_list(route.get("visited_programs"))),
            1,
        )
        route_cost = _number(route.get("estimated_computational_cost"))
        route_confidence = _number(route.get("current_confidence"))
        evidence = _number(route.get("evidence_score"))
        reuse = min(1.0, len(_as_list(route.get("visited_programs"))) / max(route_length, 1))
        success = state in TERMINAL_SUCCESS_STATES or str(route.get("validation_status")) == "validated"
        quality = round(
            (route_confidence * 0.30)
            + (evidence * 0.20)
            + (_number(route.get("expected_information_gain")) * 0.15)
            + ((1.0 - route_cost) * 0.15)
            + (reuse * 0.10)
            + ((1.0 if success else 0.0) * 0.10),
            4,
        )
        return RouteAnalysis(
            route_id=route_id,
            route_length=route_length,
            route_cost=round(route_cost, 4),
            route_quality=max(0.0, min(1.0, quality)),
            route_success=success,
            route_confidence=round(route_confidence, 4),
            route_reason=self._route_reason(route, quality, success),
            route_dependencies=dependencies,
            route_reuse=round(reuse, 4),
        ).as_dict()

    def _metrics(
        self,
        routes: list[dict[str, Any]],
        route_analysis: list[dict[str, Any]],
        performance: Mapping[str, Any],
    ) -> dict[str, Any]:
        route_count = len(routes)
        states = [str(route.get("current_state") or "CREATED").upper() for route in routes]
        successful = sum(1 for item in route_analysis if item["route_success"])
        failed = sum(1 for state in states if state in TERMINAL_FAILURE_STATES)
        recovered = sum(1 for state in states if state in RECOVERY_STATES)
        pruned = sum(1 for state in states if state == "PRUNED")
        costs = [item["route_cost"] for item in route_analysis]
        qualities = [item["route_quality"] for item in route_analysis]
        unique_states = {
            str(value)
            for route in routes
            for value in (
                _as_list(route.get("visited_concepts"))
                + _as_list(route.get("visited_transformations"))
                + _as_list(route.get("visited_programs"))
                + [route.get("route_id")]
            )
            if value
        }
        total_visits = sum(
            len(_as_list(route.get("visited_concepts")))
            + len(_as_list(route.get("visited_transformations")))
            + len(_as_list(route.get("visited_programs")))
            + 1
            for route in routes
        )
        repeated = max(total_visits - len(unique_states), 0)
        total_cost = round(
            sum(costs) + _number(performance.get("search_time_seconds")),
            4,
        )
        coverage = round(len(unique_states) / max(total_visits, 1), 4)
        success_ratio = round(successful / max(route_count, 1), 4)
        failure_ratio = round(failed / max(route_count, 1), 4)
        recovery_ratio = round(recovered / max(max(failed + recovered, 1), 1), 4)
        completion_ratio = round((successful + failed) / max(route_count, 1), 4)
        expansion_ratio = round(
            sum(max(int(_number(route.get("branch_width"))), 1) for route in routes)
            / max(route_count, 1),
            4,
        )
        compression_ratio = round(len(unique_states) / max(total_visits, 1), 4)
        efficiency = round(
            (sum(qualities) / max(route_count, 1))
            / max(1.0 + total_cost, 1.0),
            4,
        )
        return {
            "search_coverage": coverage,
            "search_efficiency": efficiency,
            "search_cost": total_cost,
            "search_diversity": round(
                len({route.get("creation_trigger") for route in routes}) / max(route_count, 1),
                4,
            ),
            "search_entropy": _entropy([_number(route.get("priority")) for route in routes] or qualities),
            "search_stability": round(
                sum(1 for state in states if state in {"STABLE", "VALIDATED", "DOMINANT"})
                / max(route_count, 1),
                4,
            ),
            "search_consistency": round(1.0 - min(1.0, repeated / max(total_visits, 1)), 4),
            "search_completion_ratio": completion_ratio,
            "search_expansion_ratio": expansion_ratio,
            "search_success_ratio": success_ratio,
            "search_failure_ratio": failure_ratio,
            "search_recovery_ratio": recovery_ratio,
            "search_compression_ratio": compression_ratio,
            "adaptive_strategy_utilization": round(
                sum(1 for route in routes if route.get("decision")) / max(route_count, 1),
                4,
            ),
            "average_branching_factor": round(
                sum(max(int(_number(route.get("branch_width"))), 1) for route in routes)
                / max(route_count, 1),
                4,
            ),
            "average_search_depth": round(
                sum(item["route_length"] for item in route_analysis) / max(route_count, 1),
                4,
            ),
            "maximum_search_depth": max([item["route_length"] for item in route_analysis] or [0]),
            "unique_search_states": len(unique_states),
            "repeated_search_states": repeated,
            "pruned_route_count": pruned,
        }

    def _diagnostics(
        self,
        routes: list[dict[str, Any]],
        route_analysis: list[dict[str, Any]],
        metrics: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not routes:
            return {
                "search_bottlenecks": [],
                "dead_end_routes": [],
                "redundant_exploration": [],
                "repeated_exploration": [],
                "unused_search_branches": [],
                "expensive_search_regions": [],
                "highly_productive_search_regions": [],
                "high_reuse_opportunities": [],
            }
        average_cost = sum(item["route_cost"] for item in route_analysis) / max(len(route_analysis), 1)
        average_quality = sum(item["route_quality"] for item in route_analysis) / max(len(route_analysis), 1)
        return {
            "search_bottlenecks": [
                item["route_id"] for item in route_analysis
                if item["route_cost"] > average_cost and item["route_quality"] < average_quality
            ][:20],
            "dead_end_routes": [
                item["route_id"] for item in route_analysis
                if not item["route_success"] and item["route_quality"] < 0.35
            ][:20],
            "redundant_exploration": [
                route.get("route_id") for route in routes
                if len(set(_as_list(route.get("visited_concepts")))) < len(_as_list(route.get("visited_concepts")))
            ][:20],
            "repeated_exploration": [
                route.get("route_id") for route in routes
                if route.get("current_state") in {"SUSPENDED", "REACTIVATED"}
            ][:20],
            "unused_search_branches": [
                route.get("route_id") for route in routes
                if int(_number(route.get("branch_width"))) > 1 and not route.get("decision")
            ][:20],
            "expensive_search_regions": [
                item["route_id"] for item in route_analysis
                if item["route_cost"] >= average_cost
            ][:20],
            "highly_productive_search_regions": [
                item["route_id"] for item in route_analysis
                if item["route_success"] or item["route_quality"] >= 0.7
            ][:20],
            "high_reuse_opportunities": [
                item["route_id"] for item in route_analysis
                if item["route_reuse"] >= 0.25
            ][:20],
        }

    def _route_distribution(
        self,
        routes: list[dict[str, Any]],
        route_analysis: list[dict[str, Any]],
    ) -> dict[str, Any]:
        quality = {"low": 0, "medium": 0, "high": 0}
        for item in route_analysis:
            if item["route_quality"] < 0.4:
                quality["low"] += 1
            elif item["route_quality"] < 0.7:
                quality["medium"] += 1
            else:
                quality["high"] += 1
        return {
            "by_state": _counts(str(route.get("current_state") or "CREATED") for route in routes),
            "by_decision": _counts(str(route.get("decision") or "UNKNOWN") for route in routes),
            "by_quality": quality,
        }

    def _route_reason(
        self,
        route: Mapping[str, Any],
        quality: float,
        success: bool,
    ) -> str:
        if success:
            return "route succeeded or remains highly supported"
        if _number(route.get("estimated_computational_cost")) > 0.5:
            return "route quality limited by high search cost"
        if quality < 0.35:
            return "route has weak evidence and confidence"
        return str(route.get("decision_explanation") or "route remains analytically viable")

    def _quality_reason(
        self,
        components: Mapping[str, float],
        overall: float,
    ) -> str:
        if not components:
            return "no completed search routes available for analytics"
        strongest = max(components, key=lambda key: components[key])
        weakest = min(components, key=lambda key: components[key])
        return (
            f"overall_search_quality={overall} from weighted measurable components; "
            f"strongest={strongest}, weakest={weakest}"
        )


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value)
    return []


def _counts(values: Iterable[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


def _entropy(values: Iterable[float]) -> float:
    items = [max(float(value or 0.0), 0.0) for value in values]
    total = sum(items)
    if total <= 0.0:
        return 0.0
    entropy = 0.0
    for value in items:
        probability = value / total
        if probability > 0.0:
            entropy -= probability * math.log2(probability)
    maximum = math.log2(max(len(items), 1))
    return round(entropy / maximum, 4) if maximum > 0.0 else 0.0


def _number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(number) or math.isinf(number):
        return default
    return max(0.0, number)


search_analytics_engine = SearchAnalyticsEngine()


__all__ = [
    "RouteAnalysis",
    "SearchAnalyticsEngine",
    "search_analytics_engine",
]
