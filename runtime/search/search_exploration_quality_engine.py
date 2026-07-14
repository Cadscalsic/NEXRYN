"""Objective exploration quality analysis for completed cognitive search."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
from typing import Any, Iterable, Mapping


SUCCESS_STATES = {"VALIDATED", "STABLE", "DOMINANT", "SUPPORTED", "PROMISING"}
DEAD_END_STATES = {"FAILED", "PRUNED", "ARCHIVED", "SUSPENDED"}
RECOVERY_STATES = {"REACTIVATED"}


@dataclass(frozen=True)
class ExplorationRouteQuality:
    route_id: str
    route_depth: int
    route_cost: float
    route_quality: float
    route_productivity: float
    route_novelty: float
    route_reuse: float
    route_confidence: float
    route_success_probability: float
    route_signature: str
    dead_end: bool
    redundant: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SearchExplorationQualityEngine:
    """Evaluate completed search exploration without performing search."""

    system_name = "search_exploration_quality_engine"

    def build_report(
        self,
        *,
        search_report: Mapping[str, Any] | None = None,
        routes: Iterable[Any] | None = None,
    ) -> dict[str, Any]:
        route_payloads = self._routes(routes, search_report or {})
        graph = self._graph(search_report or {}, route_payloads)
        path_quality = self._path_quality(route_payloads)
        redundancy = self._redundancy(route_payloads, path_quality)
        metrics = self._metrics(route_payloads, path_quality, graph, redundancy)
        strategy = self._strategy(metrics, redundancy, path_quality)
        learning = self._learning(route_payloads, path_quality)
        return {
            "system": self.system_name,
            "SEARCH_EXPLORATION_QUALITY_REPORT": True,
            "exploration_quality_authority": True,
            "does_not_perform_search": True,
            "routes_analyzed": len(route_payloads),
            "search_graph": graph,
            "path_quality": path_quality,
            "route_quality": path_quality,
            "redundancy_analysis": redundancy,
            "strategy_analysis": strategy,
            "learning_output": learning,
            "overall_exploration_quality": metrics["overall_exploration_quality"],
            "exploration_entropy": metrics["exploration_entropy"],
            "exploration_diversity": metrics["exploration_diversity"],
            "exploration_redundancy": metrics["exploration_redundancy"],
            "exploration_depth": metrics["exploration_depth"],
            "exploration_breadth": metrics["exploration_breadth"],
            "exploration_efficiency": metrics["exploration_efficiency"],
            "exploration_novelty": metrics["exploration_novelty"],
            "exploration_coverage": metrics["exploration_coverage"],
            "exploration_stability": metrics["exploration_stability"],
            "exploration_cost": metrics["exploration_cost"],
            "exploration_recovery": metrics["exploration_recovery"],
            "exploration_consistency": metrics["exploration_consistency"],
            "exploration_adaptability": metrics["exploration_adaptability"],
            "productive_routes": metrics["productive_routes"],
            "dead_end_routes": metrics["dead_end_routes"],
            "reused_routes": metrics["reused_routes"],
            "unique_routes": metrics["unique_routes"],
            "novel_routes": metrics["novel_routes"],
            "preferred_search_strategy": strategy["preferred_search_strategy"],
            "quality_components": metrics["quality_components"],
            "reproducibility_signature": self._reproducibility_signature(
                route_payloads,
                metrics,
                redundancy,
                strategy,
            ),
        }

    def _routes(
        self,
        routes: Iterable[Any] | None,
        search_report: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        payloads = [self._route_payload(route) for route in routes or []]
        payloads = [payload for payload in payloads if payload.get("route_id")]
        if payloads:
            return sorted(payloads, key=lambda item: item["route_id"])

        by_id: dict[str, dict[str, Any]] = {}
        for key in ("route_ranking", "route_evolution", "search_timeline", "failed_routes"):
            value = search_report.get(key)
            if not isinstance(value, list):
                continue
            for item in value:
                if not isinstance(item, Mapping):
                    continue
                payload = self._route_payload(item)
                route_id = payload.get("route_id")
                if not route_id:
                    continue
                existing = by_id.get(route_id, {})
                existing.update({key: value for key, value in payload.items() if value not in (None, "", [], {})})
                by_id[route_id] = existing
        if by_id:
            return [self._route_payload(by_id[key]) for key in sorted(by_id)]

        graph = search_report.get("search_space_graph")
        if isinstance(graph, Mapping):
            for node in graph.get("nodes", []):
                if isinstance(node, Mapping) and node.get("id"):
                    payload = self._route_payload({
                        "route_id": node.get("id"),
                        "current_state": node.get("state", "CREATED"),
                        "priority": node.get("priority", 0.0),
                    })
                    by_id[payload["route_id"]] = payload
        return [self._route_payload(by_id[key]) for key in sorted(by_id)]

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
                "visited_concepts": getattr(route, "visited_concepts", []),
                "visited_transformations": getattr(route, "visited_transformations", []),
                "visited_programs": getattr(route, "visited_programs", []),
                "visited_constraints": getattr(route, "visited_constraints", []),
                "validation_status": getattr(route, "validation_status", "unknown"),
                "decision": getattr(route, "decision", ""),
                "scores": getattr(route, "scores", {}),
            }
        scores = payload.get("scores") if isinstance(payload.get("scores"), Mapping) else {}
        payload["route_id"] = str(payload.get("route_id") or payload.get("id") or "")
        payload["current_state"] = str(payload.get("current_state") or payload.get("state") or "CREATED").upper()
        payload["depth"] = int(_number(payload.get("depth")))
        payload["branch_width"] = int(_number(payload.get("branch_width")))
        payload["current_confidence"] = _clamp(max(
            _number(payload.get("current_confidence")),
            _number(payload.get("confidence")),
            _number(scores.get("confidence_score")),
        ))
        payload["evidence_score"] = _clamp(max(
            _number(payload.get("evidence_score")),
            _number(scores.get("evidence_score")),
        ))
        payload["expected_information_gain"] = _clamp(max(
            _number(payload.get("expected_information_gain")),
            _number(scores.get("information_gain")),
            _number(scores.get("estimated_future_value")),
        ))
        payload["estimated_computational_cost"] = _clamp(max(
            _number(payload.get("estimated_computational_cost")),
            _number(payload.get("search_cost")),
            _number(scores.get("search_cost")),
        ))
        payload["priority"] = _clamp(payload.get("priority"))
        payload["visited_concepts"] = _strings(payload.get("visited_concepts"))
        payload["visited_transformations"] = _strings(payload.get("visited_transformations"))
        payload["visited_programs"] = _strings(payload.get("visited_programs"))
        payload["visited_constraints"] = _strings(payload.get("visited_constraints"))
        payload["decision"] = str(payload.get("decision") or "")
        payload["validation_status"] = str(payload.get("validation_status") or "unknown")
        payload["scores"] = dict(scores)
        return payload

    def _graph(
        self,
        search_report: Mapping[str, Any],
        routes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        existing = search_report.get("search_space_graph")
        if isinstance(existing, Mapping) and existing.get("nodes"):
            nodes = list(existing.get("nodes", []))
            edges = list(existing.get("edges", []))
            return {
                "nodes": nodes,
                "edges": edges,
                "node_count": len(nodes),
                "edge_count": len(edges),
                "node_types": sorted({
                    str(node.get("type", "search_state"))
                    for node in nodes
                    if isinstance(node, Mapping)
                }),
                "edge_types": sorted({
                    str(edge.get("type") or edge.get("relation") or "transition")
                    for edge in edges
                    if isinstance(edge, Mapping)
                }),
            }
        nodes = []
        edges = []
        for route in routes:
            route_id = route["route_id"]
            nodes.append({"id": route_id, "type": "SearchRoute", "state": route["current_state"]})
            parent = route.get("parent_route")
            if parent:
                edges.append({"from": str(parent), "to": route_id, "type": "expansion"})
            for concept in route["visited_concepts"]:
                node_id = f"concept:{concept}"
                nodes.append({"id": node_id, "type": "IntermediateConcept"})
                edges.append({"from": route_id, "to": node_id, "type": "visits"})
            for transformation in route["visited_transformations"]:
                node_id = f"transformation:{transformation}"
                nodes.append({"id": node_id, "type": "TransformationHypothesis"})
                edges.append({"from": route_id, "to": node_id, "type": "expands"})
            for program in route["visited_programs"]:
                node_id = f"program:{program}"
                nodes.append({"id": node_id, "type": "ProgramCandidate"})
                edges.append({"from": route_id, "to": node_id, "type": "reuse"})
        nodes = _dedupe_nodes(nodes)
        edges = _dedupe_edges(edges)
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_types": sorted({node["type"] for node in nodes}),
            "edge_types": sorted({edge["type"] for edge in edges}),
        }

    def _path_quality(self, routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        signatures = [self._route_signature(route) for route in routes]
        duplicate_signatures = {
            signature for signature in signatures if signatures.count(signature) > 1
        }
        novelty_by_signature = self._novelty_by_signature(signatures)
        qualities = []
        for route in routes:
            state = route["current_state"]
            signature = self._route_signature(route)
            success_probability = _clamp(max(
                route["current_confidence"],
                _number(route.get("scores", {}).get("estimated_success_probability")),
                1.0 if route["validation_status"] == "validated" else 0.0,
            ))
            productivity = _clamp(
                route["evidence_score"] * 0.35
                + route["expected_information_gain"] * 0.30
                + success_probability * 0.25
                + (1.0 if state in SUCCESS_STATES else 0.0) * 0.10
            )
            reuse = _clamp(len(route["visited_programs"]) / max(route["depth"], 1))
            novelty = novelty_by_signature.get(signature, 0.0)
            cost = route["estimated_computational_cost"]
            quality = _clamp(
                productivity * 0.40
                + novelty * 0.18
                + success_probability * 0.18
                + (1.0 - cost) * 0.14
                + (1.0 - reuse) * 0.05
                + (0.05 if state in RECOVERY_STATES else 0.0)
            )
            qualities.append(ExplorationRouteQuality(
                route_id=route["route_id"],
                route_depth=max(route["depth"], 1),
                route_cost=cost,
                route_quality=quality,
                route_productivity=productivity,
                route_novelty=novelty,
                route_reuse=reuse,
                route_confidence=route["current_confidence"],
                route_success_probability=success_probability,
                route_signature=signature,
                dead_end=state in DEAD_END_STATES or route["decision"].lower() in {"discard", "archive"},
                redundant=signature in duplicate_signatures,
            ).to_dict())
        return sorted(qualities, key=lambda item: item["route_id"])

    def _redundancy(
        self,
        routes: list[dict[str, Any]],
        path_quality: list[dict[str, Any]],
    ) -> dict[str, Any]:
        route_count = len(routes)
        route_signatures = [item["route_signature"] for item in path_quality]
        decision_signatures = [route["decision"].lower() for route in routes if route.get("decision")]
        hypothesis_signatures = [
            value for route in routes for value in route["visited_concepts"] + route["visited_transformations"]
        ]
        transformation_signatures = [
            value for route in routes for value in route["visited_transformations"]
        ]
        repeated_routes = _duplicates(route_signatures)
        repeated_decisions = _duplicates(decision_signatures)
        repeated_hypotheses = _duplicates(hypothesis_signatures)
        repeated_transformations = _duplicates(transformation_signatures)
        reused = [
            route["route_id"] for route in routes
            if route["visited_programs"] or route["creation_trigger"] in {"memory_reuse", "reuse"}
        ]
        unique_count = len(set(route_signatures))
        redundancy_ratio = _ratio(len(route_signatures) - unique_count, route_count)
        return {
            "repeated_routes": repeated_routes,
            "repeated_decisions": repeated_decisions,
            "repeated_hypotheses": repeated_hypotheses,
            "repeated_transformations": repeated_transformations,
            "repeated_reasoning_paths": repeated_routes,
            "redundancy_ratio": round(redundancy_ratio, 4),
            "reuse_ratio": round(_ratio(len(reused), route_count), 4),
            "unique_route_ratio": round(_ratio(unique_count, route_count), 4),
            "reused_route_ids": reused,
            "unique_route_ids": [
                item["route_id"] for item in path_quality if not item["redundant"]
            ],
        }

    def _metrics(
        self,
        routes: list[dict[str, Any]],
        path_quality: list[dict[str, Any]],
        graph: Mapping[str, Any],
        redundancy: Mapping[str, Any],
    ) -> dict[str, Any]:
        route_count = len(routes)
        depths = [item["route_depth"] for item in path_quality]
        breadths = [max(route["branch_width"], 1) for route in routes]
        all_tokens = [
            token
            for route in routes
            for token in (
                route["visited_concepts"]
                + route["visited_transformations"]
                + route["visited_programs"]
                + route["visited_constraints"]
            )
        ]
        unique_tokens = set(all_tokens)
        productive = [
            item["route_id"] for item in path_quality
            if item["route_productivity"] >= 0.55 or item["route_success_probability"] >= 0.70
        ]
        dead_ends = [item["route_id"] for item in path_quality if item["dead_end"]]
        novel = [item["route_id"] for item in path_quality if item["route_novelty"] >= 0.67]
        stable = sum(1 for route in routes if route["current_state"] in SUCCESS_STATES)
        recovered = sum(1 for route in routes if route["current_state"] in RECOVERY_STATES)
        decisions = [route["decision"] or route["current_state"] for route in routes]
        probabilities = [
            max(
                route["priority"],
                route["expected_information_gain"],
                item["route_success_probability"],
                0.0001,
            )
            for route, item in zip(routes, path_quality)
        ]
        coverage = _clamp(len(unique_tokens) / max(len(all_tokens), route_count, 1))
        diversity = _clamp((
            _ratio(len(set(decisions)), route_count)
            + _ratio(len(set(route["creation_trigger"] for route in routes)), route_count)
            + _ratio(len(unique_tokens), max(len(all_tokens), 1))
        ) / 3)
        entropy = _entropy(probabilities)
        redundancy_ratio = float(redundancy.get("redundancy_ratio", 0.0) or 0.0)
        cost = _average(item["route_cost"] for item in path_quality)
        productivity = _average(item["route_productivity"] for item in path_quality)
        efficiency = _clamp(productivity / max(cost, 0.05) / 4)
        novelty = _average(item["route_novelty"] for item in path_quality)
        stability = _ratio(stable, route_count)
        recovery = _ratio(recovered, max(len(dead_ends) + recovered, 1))
        consistency = _clamp(1.0 - _stddev(item["route_quality"] for item in path_quality))
        adaptability = _clamp((
            _ratio(len(set(route["decision"] for route in routes)), route_count)
            + recovery
            + _ratio(len(graph.get("edge_types", [])), max(len(graph.get("node_types", [])), 1))
        ) / 3)
        depth_score = _clamp(_average(depths) / max(max(depths, default=1), 1))
        breadth_score = _clamp(_average(breadths) / max(max(breadths, default=1), 1))
        components = {
            "coverage": coverage,
            "diversity": diversity,
            "efficiency": efficiency,
            "non_redundancy": _clamp(1.0 - redundancy_ratio),
            "stability": round(stability, 4),
            "novelty": novelty,
            "depth": depth_score,
            "breadth": breadth_score,
            "low_cost": _clamp(1.0 - cost),
            "recovery": round(recovery, 4),
            "consistency": consistency,
            "adaptability": adaptability,
            "entropy": entropy,
        }
        overall = _clamp(
            components["coverage"] * 0.11
            + components["diversity"] * 0.10
            + components["efficiency"] * 0.12
            + components["non_redundancy"] * 0.10
            + components["stability"] * 0.08
            + components["novelty"] * 0.08
            + components["depth"] * 0.07
            + components["breadth"] * 0.07
            + components["low_cost"] * 0.08
            + components["recovery"] * 0.05
            + components["consistency"] * 0.07
            + components["adaptability"] * 0.04
            + components["entropy"] * 0.03
        )
        return {
            "overall_exploration_quality": overall,
            "exploration_entropy": entropy,
            "exploration_diversity": diversity,
            "exploration_redundancy": round(redundancy_ratio, 4),
            "exploration_depth": round(_average(depths), 4),
            "exploration_breadth": round(_average(breadths), 4),
            "exploration_efficiency": efficiency,
            "exploration_novelty": novelty,
            "exploration_coverage": coverage,
            "exploration_stability": round(stability, 4),
            "exploration_cost": round(cost, 4),
            "exploration_recovery": round(recovery, 4),
            "exploration_consistency": consistency,
            "exploration_adaptability": adaptability,
            "productive_routes": productive,
            "dead_end_routes": dead_ends,
            "reused_routes": list(redundancy.get("reused_route_ids", [])),
            "unique_routes": list(redundancy.get("unique_route_ids", [])),
            "novel_routes": novel,
            "quality_components": components,
        }

    def _strategy(
        self,
        metrics: Mapping[str, Any],
        redundancy: Mapping[str, Any],
        path_quality: list[dict[str, Any]],
    ) -> dict[str, Any]:
        breadth = float(metrics.get("exploration_breadth", 0.0) or 0.0)
        depth = float(metrics.get("exploration_depth", 0.0) or 0.0)
        entropy = float(metrics.get("exploration_entropy", 0.0) or 0.0)
        redundancy_ratio = float(redundancy.get("redundancy_ratio", 0.0) or 0.0)
        dead_end_ratio = _ratio(len(metrics.get("dead_end_routes", [])), len(path_quality))
        productive_ratio = _ratio(len(metrics.get("productive_routes", [])), len(path_quality))
        if breadth >= 4 and entropy >= 0.70:
            strategy = "aggressive_exploration"
        elif breadth <= 2 and depth >= 3 and entropy < 0.55:
            strategy = "conservative_exploration"
        else:
            strategy = "balanced_exploration"
        flags = []
        if dead_end_ratio >= 0.5 and breadth <= 2:
            flags.append("over_pruning")
        if len(path_quality) < 2 or (entropy < 0.35 and productive_ratio < 0.5):
            flags.append("under_exploration")
        if breadth >= 6:
            flags.append("excessive_branching")
        if entropy < 0.35 and redundancy_ratio >= 0.25:
            flags.append("premature_convergence")
        return {
            "preferred_search_strategy": strategy,
            "detected_patterns": flags or [strategy],
            "aggressive_exploration": strategy == "aggressive_exploration",
            "conservative_exploration": strategy == "conservative_exploration",
            "balanced_exploration": strategy == "balanced_exploration",
            "over_pruning": "over_pruning" in flags,
            "under_exploration": "under_exploration" in flags,
            "excessive_branching": "excessive_branching" in flags,
            "premature_convergence": "premature_convergence" in flags,
        }

    def _learning(
        self,
        routes: list[dict[str, Any]],
        path_quality: list[dict[str, Any]],
    ) -> dict[str, Any]:
        quality_by_id = {item["route_id"]: item for item in path_quality}
        productive = [
            route for route in routes
            if quality_by_id[route["route_id"]]["route_productivity"] >= 0.55
        ]
        failed = [
            route for route in routes
            if quality_by_id[route["route_id"]]["dead_end"]
        ]
        high_value = sorted(
            path_quality,
            key=lambda item: (item["route_quality"], item["route_productivity"]),
            reverse=True,
        )[:5]
        return {
            "productive_search_patterns": sorted({
                route["creation_trigger"] or route["decision"] or "unknown"
                for route in productive
            }),
            "failed_search_patterns": sorted({
                route["creation_trigger"] or route["decision"] or "unknown"
                for route in failed
            }),
            "high_value_branches": [item["route_id"] for item in high_value],
            "dead_end_patterns": sorted({
                token
                for route in failed
                for token in route["visited_transformations"] + route["visited_constraints"]
            }),
            "preferred_expansion_strategies": sorted({
                route["decision"] for route in productive if route["decision"]
            }),
            "preferred_pruning_strategies": sorted({
                route["decision"] for route in failed if route["decision"]
            }),
        }

    def _route_signature(self, route: Mapping[str, Any]) -> str:
        return _digest({
            "concepts": sorted(route.get("visited_concepts", [])),
            "transformations": sorted(route.get("visited_transformations", [])),
            "programs": sorted(route.get("visited_programs", [])),
            "constraints": sorted(route.get("visited_constraints", [])),
            "trigger": route.get("creation_trigger"),
        })

    def _novelty_by_signature(self, signatures: list[str]) -> dict[str, float]:
        counts = {signature: signatures.count(signature) for signature in set(signatures)}
        return {
            signature: round(1.0 / max(count, 1), 4)
            for signature, count in counts.items()
        }

    def _reproducibility_signature(
        self,
        routes: list[dict[str, Any]],
        metrics: Mapping[str, Any],
        redundancy: Mapping[str, Any],
        strategy: Mapping[str, Any],
    ) -> str:
        return _digest({
            "routes": [
                {
                    "route_id": route["route_id"],
                    "state": route["current_state"],
                    "signature": self._route_signature(route),
                }
                for route in routes
            ],
            "metrics": {
                key: metrics[key]
                for key in sorted(metrics)
                if key.startswith("exploration_") or key == "overall_exploration_quality"
            },
            "redundancy": {
                "redundancy_ratio": redundancy.get("redundancy_ratio"),
                "unique_route_ratio": redundancy.get("unique_route_ratio"),
            },
            "strategy": strategy.get("preferred_search_strategy"),
        })[:16]


def _strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [str(value[key]) for key in ("id", "route_id", "name") if value.get(key)]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if item is not None and item != ""]
    return [str(value)]


def _duplicates(values: list[str]) -> list[str]:
    counts = {}
    for value in values:
        if value:
            counts[value] = counts.get(value, 0) + 1
    return sorted(value for value, count in counts.items() if count > 1)


def _dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {}
    for node in nodes:
        by_id[node["id"]] = node
    return [by_id[key] for key in sorted(by_id)]


def _dedupe_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    output = []
    for edge in edges:
        marker = (edge.get("from"), edge.get("to"), edge.get("type"))
        if marker in seen or edge.get("from") == edge.get("to"):
            continue
        seen.add(marker)
        output.append(edge)
    return output


def _ratio(numerator: float, denominator: float) -> float:
    return round(float(numerator) / max(float(denominator), 1.0), 4)


def _average(values: Iterable[float]) -> float:
    items = [float(value or 0.0) for value in values]
    return round(sum(items) / len(items), 4) if items else 0.0


def _stddev(values: Iterable[float]) -> float:
    items = [float(value or 0.0) for value in values]
    if not items:
        return 0.0
    avg = sum(items) / len(items)
    variance = sum((value - avg) ** 2 for value in items) / len(items)
    return round(math.sqrt(variance), 4)


def _entropy(values: list[float]) -> float:
    total = sum(max(float(value or 0.0), 0.0) for value in values)
    if total <= 0.0:
        return 0.0
    entropy = 0.0
    for value in values:
        probability = max(float(value or 0.0), 0.0) / total
        if probability > 0.0:
            entropy -= probability * math.log2(probability)
    max_entropy = math.log2(max(len(values), 1))
    if max_entropy <= 0.0:
        return 0.0
    return round(entropy / max_entropy, 4)


def _number(value: Any) -> float:
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: Any) -> float:
    return round(max(0.0, min(1.0, _number(value))), 4)


def _digest(value: Any) -> str:
    return hashlib.sha1(
        json.dumps(value, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


search_exploration_quality_engine = SearchExplorationQualityEngine()


__all__ = [
    "ExplorationRouteQuality",
    "SearchExplorationQualityEngine",
    "search_exploration_quality_engine",
]
