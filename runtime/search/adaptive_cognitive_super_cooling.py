"""Adaptive Cognitive Super Cooling (ACSC).

ACSC allocates cognitive resources from route-intelligence evidence.  It does
not execute reasoning, search, planning, or cooling; it produces deterministic
resource allocations, thermal states, and explainable cooling decisions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping


THERMAL_STATES = (
    "HOT",
    "WARM",
    "STABLE",
    "COOLING",
    "DORMANT",
    "REACTIVATING",
    "TERMINATED",
)


@dataclass
class AllocatedResources:
    cpu_budget: float
    reasoning_budget: float
    search_budget: float
    validation_budget: float
    memory_budget: float
    concept_budget: float
    program_budget: float
    attention_budget: float
    energy_budget: float


class ACSCMemory:
    """Persistent compact thermal resource history."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or "runtime_data/search/acsc_memory.json")

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
        cooled = [item for item in history if item.get("action") == "Cool Route"]
        reactivated = [item for item in history if item.get("action") == "Reactivate Route"]
        dominant = [
            item.get("route_id") for item in history
            if item.get("thermal_state") in {"HOT", "WARM"}
        ][-10:]
        return {
            "cooling_history": [item.get("route_id") for item in cooled][-20:],
            "reactivation_history": [item.get("route_id") for item in reactivated][-20:],
            "budget_history_count": len(history),
            "dominant_routes": dominant,
            "resource_allocation_history": history[-20:],
            "thermal_evolution": [
                {
                    "route_id": item.get("route_id"),
                    "thermal_state": item.get("thermal_state"),
                    "thermal_score": item.get("thermal_score"),
                }
                for item in history[-20:]
            ],
            "recovered_routes": [item.get("route_id") for item in reactivated if item.get("recovered")][-20:],
            "failed_cooling_decisions": [
                item.get("route_id") for item in cooled
                if item.get("expected_recovery_value", 0) < 0.2
            ][-20:],
        }

    def remember(self, route_allocations: list[Mapping[str, Any]]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.load()
        history = list(payload.get("history", []))
        timestamp = datetime.now(timezone.utc).isoformat()
        for route in route_allocations:
            history.append({
                "timestamp": timestamp,
                "route_id": route.get("route_id"),
                "thermal_state": route.get("thermal_state"),
                "thermal_score": route.get("thermal_score"),
                "action": route.get("cooling_decision", {}).get("action"),
                "resource_total": route.get("allocated_resource_total"),
                "released_resources": route.get("released_resources"),
                "expected_recovery_value": route.get("predictive_cooling", {}).get("expected_recovery_value"),
                "recovered": route.get("thermal_state") == "REACTIVATING",
            })
        payload["history"] = history[-500:]
        self.path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return {
            "persistent_thermal_memory": True,
            "memory_path": str(self.path),
            "entries_stored": len(payload["history"]),
        }


class AdaptiveCognitiveSuperCoolingEngine:
    """Cognitive resource allocation from route-intelligence evidence."""

    system_name = "adaptive_cognitive_super_cooling"

    def __init__(self, memory: ACSCMemory | None = None) -> None:
        self.memory = memory or ACSCMemory()

    def build_report(
        self,
        *,
        cognitive_route_intelligence_report: Mapping[str, Any] | None = None,
        adaptive_search_intelligence_report: Mapping[str, Any] | None = None,
        concept_formation_report: Mapping[str, Any] | None = None,
        program_synthesis_report: Mapping[str, Any] | None = None,
        performance_report: Mapping[str, Any] | None = None,
        report_level: str = "normal",
        persist: bool = True,
    ) -> dict[str, Any]:
        started = perf_counter()
        route_report = (
            cognitive_route_intelligence_report
            if isinstance(cognitive_route_intelligence_report, Mapping) else {}
        )
        routes = self._routes(route_report)
        memory_summary = self.memory.summary()
        route_allocations = [
            self._route_allocation(route, index, memory_summary)
            for index, route in enumerate(routes)
        ]
        redistribution = self._redistribution(route_allocations)
        graph = self._thermal_graph(
            route_allocations,
            concept_formation_report if isinstance(concept_formation_report, Mapping) else {},
            program_synthesis_report if isinstance(program_synthesis_report, Mapping) else {},
        )
        analytics = self._analytics(route_allocations, redistribution)
        runtime = max(
            _number((performance_report or {}).get("total_runtime_seconds")),
            _number((performance_report or {}).get("execution_time")),
            0.001,
        )
        elapsed = max(perf_counter() - started, 0.0)
        report = {
            "system": self.system_name,
            "ACSC_REPORT": True,
            "status": "OPERATIONAL",
            "report_level": report_level,
            "thermal_graph": graph,
            "route_thermal_states": {
                route["route_id"]: route for route in route_allocations
            },
            "resource_allocation_timeline": self._timeline(route_allocations, redistribution),
            "thermal_evolution": [
                route["thermal_evolution"] for route in route_allocations
            ],
            "cooling_decisions": [
                route["cooling_decision"] for route in route_allocations
                if route["cooling_decision"]["action"] in {
                    "Decrease Budget", "Suspend Route", "Freeze Route",
                    "Cool Route", "Terminate Route",
                }
            ],
            "reactivation_decisions": [
                route["cooling_decision"] for route in route_allocations
                if route["cooling_decision"]["action"] in {
                    "Warm Route", "Reactivate Route", "Increase Budget",
                }
            ],
            "budget_evolution": [
                route["resource_history"] for route in route_allocations
            ],
            "resource_redistribution": redistribution,
            "resource_savings": analytics["resource_savings"],
            "dominant_routes": [
                route for route in route_allocations
                if route["thermal_state"] in {"HOT", "WARM"}
            ],
            "recovered_routes": [
                route for route in route_allocations
                if route["thermal_state"] == "REACTIVATING"
            ],
            "optimization_opportunities": self._optimization_opportunities(
                route_allocations,
                analytics,
                adaptive_search_intelligence_report
                if isinstance(adaptive_search_intelligence_report, Mapping) else {},
            ),
            "acsc_analytics": analytics,
            "thermal_memory": memory_summary,
            "runtime_alignment": {
                "executes_reasoning": False,
                "executes_search": False,
                "executes_planning": False,
                "reuses_route_intelligence": True,
                "reuses_adaptive_search_intelligence": bool(adaptive_search_intelligence_report),
                "reuses_concept_formation": bool(concept_formation_report),
                "reuses_program_synthesis": bool(program_synthesis_report),
                "deterministic_execution": True,
                "solver_redesigned": False,
            },
            "instrumentation_overhead_seconds": round(elapsed, 9),
            "instrumentation_overhead_below_2_percent": elapsed / runtime < 0.02,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        report["thermal_memory_update"] = (
            self.memory.remember(route_allocations)
            if persist and route_allocations
            else {"persistent_thermal_memory": False, "reason": "no_routes"}
        )
        return report

    def _route_allocation(
        self,
        route: Mapping[str, Any],
        index: int,
        memory_summary: Mapping[str, Any],
    ) -> dict[str, Any]:
        quality = route.get("quality", {}) if isinstance(route.get("quality"), Mapping) else {}
        confidence = _value(route, "current_confidence", quality.get("confidence_score"))
        utility = _value(route, "current_utility", quality.get("utility_score"))
        evidence = _value(quality, "evidence_score", _value(route, "truth_support"))
        concept = _value(route, "concept_coverage", quality.get("concept_coverage"))
        program = _value(route, "program_coverage", quality.get("program_coverage"))
        cost = _value(route, "search_budget_consumed", quality.get("search_cost"))
        future = _value(route, "future_value", route.get("expected_future_utility"))
        generalization = _value(route, "generalization_score", quality.get("generalization_potential"))
        novelty = _value(route, "novelty", quality.get("novelty_score"))
        compression = _value(route, "compression_score", quality.get("compression_score"))
        risk = _value(route, "risk_score", quality.get("failure_risk"))
        recovery = _value(route, "expected_recovery_value", route.get("reactivation_potential"))
        historical = _clamp(
            _number(route.get("historical_success"))
            / max(_number(route.get("historical_success")) + _number(route.get("historical_failure")), 1)
        )
        remaining_gain = _clamp(future + _value(route, "expected_information_gain") - cost * 0.3)
        resource_consumption = _clamp(cost + _number(route.get("search_budget_consumed", 0)))
        thermal_score = round(_clamp(
            confidence * 0.14
            + utility * 0.14
            + evidence * 0.12
            + concept * 0.08
            + program * 0.08
            + future * 0.13
            + generalization * 0.08
            + novelty * 0.05
            + compression * 0.05
            + historical * 0.05
            + remaining_gain * 0.08
            - risk * 0.08
            - resource_consumption * 0.04
        ), 4)
        state = self._thermal_state(thermal_score, risk, cost, recovery, route)
        resources = self._resources(thermal_score, state, route)
        decision = self._decision(
            route=route,
            state=state,
            thermal_score=thermal_score,
            risk=risk,
            cost=cost,
            utility=utility,
            future=future,
            recovery=recovery,
        )
        released = round(
            max(0.0, 1.0 - sum(asdict(resources).values()) / 9.0)
            if decision["action"] in {"Cool Route", "Suspend Route", "Terminate Route", "Decrease Budget"}
            else 0.0,
            4,
        )
        return {
            "route_id": str(route.get("route_id", f"route_{index}")),
            "thermal_state": state,
            "thermal_score": thermal_score,
            "allocated_resources": asdict(resources),
            "allocated_resource_total": round(sum(asdict(resources).values()), 4),
            "resource_history": {
                "route_id": str(route.get("route_id", f"route_{index}")),
                "previous_total": round(1.0 + cost, 4),
                "allocated_total": round(sum(asdict(resources).values()), 4),
                "decision": decision["action"],
                "reason": decision["explanation"],
            },
            "cooling_decision": decision,
            "reactivation_decision": decision if decision["action"] == "Reactivate Route" else {},
            "released_resources": released,
            "predictive_cooling": {
                "expected_future_utility": future,
                "expected_future_evidence": round(_clamp(evidence + remaining_gain * 0.25), 4),
                "expected_future_search_gain": remaining_gain,
                "expected_future_generalization": generalization,
                "expected_recovery_value": recovery,
                "premature_cooling_guard": future >= 0.35 or recovery >= 0.35,
            },
            "cooperative_cooling": {
                "shares_resources_with": list(route.get("child_routes", []))[:5],
                "competes_with": [],
                "reinforcement_basis": list(route.get("supporting_concepts", []))[:5],
            },
            "thermal_evolution": {
                "route_id": str(route.get("route_id", f"route_{index}")),
                "from_state": route.get("current_state"),
                "to_thermal_state": state,
                "thermal_score": thermal_score,
                "risk": risk,
                "future_value": future,
                "resource_consumption": resource_consumption,
            },
            "explainability": {
                "why_cooled": decision["explanation"] if "Cool" in decision["action"] else "Route was not cooled.",
                "why_reactivated": decision["explanation"] if decision["action"] == "Reactivate Route" else "Route was not reactivated.",
                "why_budget_increased": decision["explanation"] if decision["action"] == "Increase Budget" else "Budget was not increased.",
                "why_budget_reduced": decision["explanation"] if decision["action"] == "Decrease Budget" else "Budget was not reduced.",
                "why_route_terminated": decision["explanation"] if decision["action"] == "Terminate Route" else "Route was not terminated.",
                "why_resources_moved": "Released resources are redistributed to routes with higher utility, confidence, information gain, or emerging promise.",
            },
            "source_route": {
                "confidence": confidence,
                "utility": utility,
                "evidence_quality": evidence,
                "concept_quality": concept,
                "program_quality": program,
                "search_cost": cost,
                "future_value": future,
                "failure_risk": risk,
            },
        }

    def _thermal_state(self, score, risk, cost, recovery, route):
        if route.get("proposed_state") in {"ARCHIVED", "PRUNED"} or risk >= 0.88:
            return "TERMINATED"
        if route.get("current_state") == "SUSPENDED" and recovery >= 0.45:
            return "REACTIVATING"
        if score >= 0.72:
            return "HOT"
        if score >= 0.55:
            return "WARM"
        if risk >= 0.68 or (cost >= 0.55 and score < 0.46):
            return "COOLING"
        if score < 0.28:
            return "DORMANT"
        return "STABLE"

    def _resources(self, score, state, route):
        modifier = {
            "HOT": 1.0,
            "WARM": 0.82,
            "STABLE": 0.62,
            "COOLING": 0.36,
            "DORMANT": 0.18,
            "REACTIVATING": 0.70,
            "TERMINATED": 0.05,
        }[state]
        base = _clamp(0.25 + score * 0.75) * modifier
        info = _value(route, "expected_information_gain")
        concept = _value(route, "concept_coverage")
        program = _value(route, "program_coverage")
        return AllocatedResources(
            cpu_budget=round(base, 4),
            reasoning_budget=round(_clamp(base + info * 0.18), 4),
            search_budget=round(_clamp(base + info * 0.24), 4),
            validation_budget=round(_clamp(base + _value(route, "truth_support") * 0.2), 4),
            memory_budget=round(_clamp(base + _value(route, "memory_support") * 0.15), 4),
            concept_budget=round(_clamp(base + concept * 0.2), 4),
            program_budget=round(_clamp(base + program * 0.2), 4),
            attention_budget=round(_clamp(base + _value(route, "priority_score") * 0.18), 4),
            energy_budget=round(_clamp(base + _value(route, "future_value") * 0.2), 4),
        )

    def _decision(self, *, route, state, thermal_score, risk, cost, utility, future, recovery):
        if state == "TERMINATED":
            action = "Terminate Route"
            reason = "Failure risk or terminal route state exceeds ACSC recovery threshold."
        elif state == "REACTIVATING":
            action = "Reactivate Route"
            reason = "Dormant route retains enough evidence and recovery value to receive resources."
        elif state == "HOT":
            action = "Increase Budget"
            reason = "High thermal score indicates strong confidence, utility, and future value."
        elif state == "WARM":
            action = "Warm Route"
            reason = "Route is promising but should not consume maximum resources."
        elif state == "STABLE":
            action = "Freeze Route"
            reason = "Route has stable value; preserve moderate resources without expansion."
        elif state == "COOLING":
            action = "Cool Route"
            reason = "High cost or risk relative to utility triggers cooling."
        elif state == "DORMANT" and recovery >= 0.4:
            action = "Reactivate Route"
            reason = "Dormant route has sufficient expected recovery value."
        elif state == "DORMANT":
            action = "Suspend Route"
            reason = "Weak evidence and low future value justify dormant allocation."
        elif cost > utility and future < 0.4:
            action = "Decrease Budget"
            reason = "Resource consumption exceeds expected value."
        else:
            action = "Redistribute Resources"
            reason = "Allocation should be balanced against stronger peer routes."
        return {
            "route_id": str(route.get("route_id", "unknown_route")),
            "action": action,
            "thermal_state": state,
            "thermal_score": thermal_score,
            "evidence": route.get("evidence", route.get("supporting_evidence", [])),
            "risk": risk,
            "utility": utility,
            "future_value": future,
            "explanation": reason,
        }

    def _redistribution(self, routes):
        released = round(sum(route["released_resources"] for route in routes), 4)
        receivers = sorted(
            [
                route for route in routes
                if route["thermal_state"] in {"HOT", "WARM", "REACTIVATING", "STABLE"}
            ],
            key=lambda route: (
                route["source_route"]["utility"],
                route["source_route"]["confidence"],
                route["source_route"].get("future_value", 0),
                route["route_id"],
            ),
            reverse=True,
        )
        shares = []
        for route in receivers[:5]:
            share = round(released / max(min(len(receivers), 5), 1), 4) if released else 0.0
            shares.append({
                "route_id": route["route_id"],
                "received_resources": share,
                "priority_basis": "utility_confidence_information_gain_or_emerging_promise",
            })
        return {
            "released_resources": released,
            "redistributed_resources": round(sum(item["received_resources"] for item in shares), 4),
            "receivers": shares,
            "measurable": True,
        }

    def _thermal_graph(self, routes, concept_report, program_report):
        nodes = [
            {
                "id": route["route_id"],
                "type": "route",
                "thermal_state": route["thermal_state"],
                "thermal_score": route["thermal_score"],
            }
            for route in routes
        ]
        edges = []
        for route in routes:
            for concept in route["cooperative_cooling"]["reinforcement_basis"]:
                nodes.append({"id": concept, "type": "concept"})
                edges.append({"source": concept, "target": route["route_id"], "relation": "supports"})
            for program in route.get("source_route", {}).get("programs", []):
                nodes.append({"id": program, "type": "program"})
                edges.append({"source": program, "target": route["route_id"], "relation": "supports"})
            if route["cooling_decision"]["action"] == "Cool Route":
                edges.append({"source": route["route_id"], "target": route["route_id"] + ":cooling", "relation": "cools"})
            if route["cooling_decision"]["action"] == "Reactivate Route":
                edges.append({"source": route["route_id"], "target": route["route_id"] + ":reactivation", "relation": "reactivates"})
        hot = [route for route in routes if route["thermal_state"] in {"HOT", "WARM"}]
        cool = [route for route in routes if route["thermal_state"] in {"COOLING", "DORMANT", "TERMINATED"}]
        for receiver in hot[:3]:
            for donor in cool[:3]:
                edges.append({"source": donor["route_id"], "target": receiver["route_id"], "relation": "shares_resources"})
        for index, left in enumerate(routes):
            for right in routes[index + 1:]:
                edges.append({"source": left["route_id"], "target": right["route_id"], "relation": "competes_with"})
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "relationship_types": sorted({edge["relation"] for edge in edges}),
        }

    def _analytics(self, routes, redistribution):
        total_alloc = sum(route["allocated_resource_total"] for route in routes)
        cooled = [route for route in routes if route["thermal_state"] in {"COOLING", "DORMANT", "TERMINATED"}]
        recovered = [route for route in routes if route["thermal_state"] == "REACTIVATING"]
        return {
            "average_resource_allocation": round(total_alloc / max(len(routes), 1), 4),
            "cooling_efficiency": round(len(cooled) / max(len(routes), 1), 4),
            "resource_savings": redistribution["released_resources"],
            "recovered_routes": len(recovered),
            "premature_cooling_rate": round(
                len([
                    route for route in cooled
                    if route["predictive_cooling"]["premature_cooling_guard"]
                ])
                / max(len(cooled), 1),
                4,
            ),
            "successful_reactivations": len(recovered),
            "budget_utilization": round(total_alloc / max(len(routes) * 9, 1), 4),
            "energy_distribution": {
                route["route_id"]: route["allocated_resources"]["energy_budget"]
                for route in routes
            },
            "route_survival": round(
                len([route for route in routes if route["thermal_state"] != "TERMINATED"])
                / max(len(routes), 1),
                4,
            ),
        }

    def _timeline(self, routes, redistribution):
        timeline = []
        for index, route in enumerate(routes):
            timeline.append({
                "step": index,
                "route_id": route["route_id"],
                "thermal_state": route["thermal_state"],
                "action": route["cooling_decision"]["action"],
                "allocated_total": route["allocated_resource_total"],
                "released_resources": route["released_resources"],
            })
        timeline.append({
            "step": "redistribution",
            "released_resources": redistribution["released_resources"],
            "redistributed_resources": redistribution["redistributed_resources"],
            "receivers": redistribution["receivers"],
        })
        return timeline

    def _optimization_opportunities(self, routes, analytics, adaptive):
        opportunities = []
        if analytics["resource_savings"] == 0:
            opportunities.append({
                "opportunity": "increase_selective_cooling",
                "reason": "No resources were released; ACSC can cool low-value routes more aggressively.",
            })
        if analytics["premature_cooling_rate"] > 0.25:
            opportunities.append({
                "opportunity": "raise_predictive_cooling_guard",
                "reason": "Some cooled routes still have future or recovery value.",
            })
        if not any(route["thermal_state"] == "REACTIVATING" for route in routes):
            opportunities.append({
                "opportunity": "monitor_dormant_reactivation",
                "reason": "No dormant route qualified for reactivation in this cycle.",
            })
        if adaptive.get("chosen_strategy"):
            opportunities.append({
                "opportunity": "align_thermal_policy_with_adaptive_search",
                "reason": "Adaptive search strategy can inform future ACSC allocation priors.",
            })
        return opportunities or [{
            "opportunity": "maintain_current_thermal_policy",
            "reason": "Current allocation has measurable savings and survivable route distribution.",
        }]

    def _routes(self, route_report):
        routes = route_report.get("cognitive_routes", {})
        if isinstance(routes, Mapping):
            return [
                route for route in routes.values()
                if isinstance(route, Mapping)
            ]
        if isinstance(routes, list):
            return [route for route in routes if isinstance(route, Mapping)]
        return []


def _number(value: Any) -> float:
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: Any) -> float:
    return max(0.0, min(1.0, _number(value)))


def _value(mapping: Mapping[str, Any], key: str, fallback: Any = 0.0) -> float:
    if isinstance(mapping, Mapping):
        return _clamp(mapping.get(key, fallback))
    return _clamp(fallback)


adaptive_cognitive_super_cooling_engine = AdaptiveCognitiveSuperCoolingEngine()

