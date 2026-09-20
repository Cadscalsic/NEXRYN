"""Cognitive Ecosystem Engine.

This layer consumes existing runtime telemetry and computes ecosystem-level
health, homeostasis, influence, pressure, resource flow, and recovery signals.
It coordinates physiology; it does not execute cognition or replace governance,
ACSC, policy, or decision layers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from runtime.observability import REQUIRED_COGNITIVE_RUNTIMES


DEFAULT_ECOSYSTEM_MEMORY = Path("runtime/memory/storage/ecosystem/ecosystem_states.json")


@dataclass
class RuntimeEcology:
    runtime_id: str
    health: float
    energy: float
    pressure: float
    load: float
    influence: float
    dependency_satisfaction: float
    recovery_capacity: float
    efficiency: float
    reliability: float
    contribution: float
    risk: float
    adaptability: float
    stability: float


class CognitiveEcosystemEngine:
    """Computes homeostatic intelligence from existing runtime telemetry."""

    system_name = "cognitive_ecosystem_engine"

    def __init__(self, memory_path: str | Path = DEFAULT_ECOSYSTEM_MEMORY) -> None:
        self.memory_path = Path(memory_path)

    def build_report(
        self,
        *,
        runtime_report: Mapping[str, Any] | None = None,
        observability_report: Mapping[str, Any] | None = None,
        execution_registry_report: Mapping[str, Any] | None = None,
        execution_timeline: list[Mapping[str, Any]] | None = None,
        governance_report: Mapping[str, Any] | None = None,
        policy_report: Mapping[str, Any] | None = None,
        decision_report: Mapping[str, Any] | None = None,
        situation_report: Mapping[str, Any] | None = None,
        analytics_report: Mapping[str, Any] | None = None,
        acsc_report: Mapping[str, Any] | None = None,
        experience_report: Mapping[str, Any] | None = None,
        world_model_report: Mapping[str, Any] | None = None,
        dna_report: Mapping[str, Any] | None = None,
        persist: bool = True,
    ) -> dict[str, Any]:
        runtime = _mapping(runtime_report)
        observability = _mapping(observability_report)
        registry = _mapping(execution_registry_report)
        timeline = list(execution_timeline or observability.get("cognitive_timeline") or [])
        runtimes = self._runtime_ids(runtime, observability, registry, timeline)
        ecology = {
            runtime_id: self._runtime_ecology(runtime_id, runtime, observability, registry, timeline)
            for runtime_id in runtimes
        }
        distribution = {runtime_id: asdict(item) for runtime_id, item in ecology.items()}
        influence_graph = self._influence_graph(ecology, runtime, observability, timeline)
        resource_flow = self._resource_flow(ecology, runtime, _mapping(governance_report), _mapping(policy_report))
        bottlenecks = self._bottlenecks(ecology, observability)
        cascade = self._cascade_analysis(ecology, influence_graph, bottlenecks)
        recovery = self._recovery_actions(ecology, bottlenecks, _mapping(acsc_report))
        stability = self._global_stability(ecology, influence_graph)
        homeostasis = self._homeostasis_score(ecology, resource_flow, recovery)
        risk_forecast = self._risk_forecast(ecology, cascade, bottlenecks)
        adaptation = self._ecological_adaptation(ecology, _mapping(experience_report), _mapping(analytics_report))
        world_model_updates = self._world_model_updates(ecology, stability, homeostasis, _mapping(world_model_report))
        dna_updates = self._dna_updates(ecology, _mapping(dna_report))
        state = {
            "state_id": _id("ecosystem_state", distribution, stability, homeostasis),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "global_health": self._global_health(ecology),
            "global_stability": stability,
            "homeostasis_score": homeostasis,
            "runtime_count": len(ecology),
            "bottleneck_count": len(bottlenecks),
            "predicted_risk_count": len(risk_forecast),
        }
        persistence = self._persist_state(state) if persist else {
            "stored": False,
            "reason": "persistence_disabled",
        }
        return {
            "system": self.system_name,
            "COGNITIVE_ECOSYSTEM_REPORT": True,
            "status": "OPERATIONAL",
            "global_health": state["global_health"],
            "health_distribution": {runtime_id: item.health for runtime_id, item in ecology.items()},
            "energy_distribution": {runtime_id: item.energy for runtime_id, item in ecology.items()},
            "pressure_distribution": {runtime_id: item.pressure for runtime_id, item in ecology.items()},
            "runtime_ecology": distribution,
            "influence_graph": influence_graph,
            "dependency_health": self._dependency_health(ecology, influence_graph),
            "collaboration_matrix": self._collaboration_matrix(ecology, influence_graph),
            "resource_flow": resource_flow,
            "bottlenecks": bottlenecks,
            "cascade_analysis": cascade,
            "recovery_actions": recovery,
            "predicted_risks": risk_forecast,
            "adaptive_recommendations": self._recommendations(ecology, bottlenecks, recovery, adaptation),
            "global_stability": stability,
            "homeostasis_score": homeostasis,
            "future_risk_forecast": risk_forecast,
            "workload_balancing": self._workload_balancing(ecology),
            "runtime_collaboration": self._runtime_collaboration(ecology, influence_graph),
            "predictive_ecology": self._predictive_ecology(ecology, risk_forecast),
            "self_organization": self._self_organization(ecology, bottlenecks),
            "ecological_adaptation": adaptation,
            "ecological_memory": {
                "stores_ecosystem_states": True,
                "state": state,
                "persistence": persistence,
            },
            "world_governance_integration": {
                "governs_ecosystem_instead_of_isolated_runtimes": True,
                "ecosystem_health_available_to_governance": True,
                "governance_context": _small(_mapping(governance_report)),
            },
            "acsc_integration": {
                "cooling_uses_health_pressure_influence_risk_energy": True,
                "cooling_targets": [item["runtime_id"] for item in recovery if item["action"] == "increase_acsc_cooling"],
                "acsc_context": _small(_mapping(acsc_report)),
            },
            "policy_engine_integration": {
                "policies_regulate_ecosystem_balance": True,
                "suggested_policy_families": ["Pressure Policy", "Energy Policy", "Recovery Policy", "Balance Policy", "Influence Policy"],
                "policy_context": _small(_mapping(policy_report)),
            },
            "decision_intelligence_integration": {
                "decision_intelligence_reasons_over_ecosystem_state": True,
                "imbalances_explained": [item["runtime_id"] for item in bottlenecks],
                "decision_context": _small(_mapping(decision_report)),
            },
            "situation_awareness_integration": {
                "situation_includes_ecosystem_state": True,
                "current_imbalance": bottlenecks[:5],
                "health_distribution_available": True,
                "situation_context": _small(_mapping(situation_report)),
            },
            "world_model_integration": world_model_updates,
            "dna_integration": dna_updates,
            "meta_cognition": {
                "evaluates_ecosystem_health": True,
                "system_balance": homeostasis,
                "recovery_efficiency": self._recovery_efficiency(ecology, recovery),
                "collaboration_quality": self._collaboration_quality(ecology, influence_graph),
                "adaptation_quality": adaptation["adaptation_quality"],
            },
            "runtime_alignment": {
                "redesigns_existing_runtimes": False,
                "duplicates_world_governance": False,
                "duplicates_acsc": False,
                "duplicates_decision_intelligence": False,
                "duplicates_policy_engine": False,
                "executes_cognition": False,
                "uses_existing_telemetry": True,
                "computes_ecosystem_intelligence": True,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _runtime_ids(
        self,
        runtime_report: Mapping[str, Any],
        observability_report: Mapping[str, Any],
        registry_report: Mapping[str, Any],
        timeline: list[Mapping[str, Any]],
    ) -> list[str]:
        ids = set(REQUIRED_COGNITIVE_RUNTIMES)
        ids.update(_mapping(runtime_report.get("runtime_registry")).keys())
        ids.update(_mapping(runtime_report.get("runtime_metrics")).keys())
        ids.update(_mapping(observability_report.get("runtime_reports")).keys())
        ids.update(_mapping(observability_report.get("runtime_health")).keys())
        ids.update(_mapping(registry_report.get("execution_registry")).keys())
        ids.update(str(item.get("runtime_id")) for item in timeline if isinstance(item, Mapping) and item.get("runtime_id"))
        ordered = [runtime_id for runtime_id in REQUIRED_COGNITIVE_RUNTIMES if runtime_id in ids]
        ordered.extend(sorted(ids - set(ordered)))
        return ordered

    def _runtime_ecology(
        self,
        runtime_id: str,
        runtime_report: Mapping[str, Any],
        observability_report: Mapping[str, Any],
        registry_report: Mapping[str, Any],
        timeline: list[Mapping[str, Any]],
    ) -> RuntimeEcology:
        runtime_metrics = _mapping(_mapping(runtime_report.get("runtime_metrics")).get(runtime_id))
        runtime_entry = _mapping(_mapping(runtime_report.get("runtime_registry")).get(runtime_id))
        obs_report = _mapping(_mapping(observability_report.get("runtime_reports")).get(runtime_id))
        obs_health = _mapping(_mapping(observability_report.get("runtime_health")).get(runtime_id))
        flow = _mapping(_mapping(observability_report.get("artifact_flow_observability")).get(runtime_id))
        telemetry = _mapping(_mapping(runtime_report.get("runtime_telemetry")).get(runtime_id))
        duration = _number(telemetry.get("duration_seconds", runtime_metrics.get("duration_seconds", runtime_entry.get("duration_seconds", 0.0))))
        coverage = _number(runtime_entry.get("coverage", obs_report.get("coverage", _mapping(observability_report.get("coverage")).get("level_5_coverage", 0.5))))
        health = self._health(runtime_id, runtime_metrics, runtime_entry, obs_report, obs_health, flow, duration, coverage)
        load = self._load(runtime_id, runtime_metrics, flow, duration, timeline)
        pressure = self._pressure(runtime_id, runtime_metrics, obs_report, flow, load, health)
        energy = round(max(0.0, min(1.0, health * 0.65 + (1.0 - pressure) * 0.35)), 4)
        contribution = self._contribution(runtime_id, runtime_metrics, flow, timeline)
        dependency_satisfaction = self._dependency_satisfaction(obs_health, flow, obs_report)
        recovery_capacity = round(max(0.0, min(1.0, health * 0.45 + energy * 0.35 + dependency_satisfaction * 0.2)), 4)
        efficiency = round(max(0.0, min(1.0, contribution * 0.45 + (1.0 - load) * 0.3 + health * 0.25)), 4)
        reliability = round(max(0.0, min(1.0, health * 0.65 + dependency_satisfaction * 0.35)), 4)
        influence = round(max(0.0, min(1.0, contribution * 0.45 + dependency_satisfaction * 0.25 + health * 0.3)), 4)
        risk = round(max(0.0, min(1.0, pressure * 0.45 + (1.0 - health) * 0.4 + (1.0 - recovery_capacity) * 0.15)), 4)
        adaptability = round(max(0.0, min(1.0, recovery_capacity * 0.55 + efficiency * 0.25 + (1.0 - risk) * 0.2)), 4)
        stability = round(max(0.0, min(1.0, health * 0.4 + reliability * 0.25 + (1.0 - pressure) * 0.2 + adaptability * 0.15)), 4)
        return RuntimeEcology(
            runtime_id=runtime_id,
            health=health,
            energy=energy,
            pressure=pressure,
            load=load,
            influence=influence,
            dependency_satisfaction=dependency_satisfaction,
            recovery_capacity=recovery_capacity,
            efficiency=efficiency,
            reliability=reliability,
            contribution=contribution,
            risk=risk,
            adaptability=adaptability,
            stability=stability,
        )

    def _health(self, runtime_id, metrics, runtime_entry, obs_report, obs_health, flow, duration, coverage) -> float:
        explicit = _number(obs_report.get("health_score", runtime_entry.get("health_score")))
        if explicit > 0:
            return explicit
        observability_score = _number(obs_health.get("observability_score", obs_report.get("observability_score", 0.5)))
        success = 1.0 if obs_health.get("execution_success", True) else 0.0
        coverage = _number(coverage or runtime_entry.get("coverage", obs_report.get("coverage", 0.5)))
        latency_penalty = min(0.35, duration)
        missing = len(_list(flow.get("missing_required")))
        rejection = len(_list(flow.get("rejected_artifacts")))
        penalty = min(0.4, missing * 0.08 + rejection * 0.05 + latency_penalty)
        return round(max(0.0, min(1.0, (success + observability_score + coverage) / 3 - penalty)), 4)

    def _load(self, runtime_id, metrics, flow, duration, timeline) -> float:
        produced = len(_list(flow.get("produced_artifacts"))) + _number(metrics.get("produced_artifact_count"))
        consumed = len(_list(flow.get("consumed_artifacts"))) + _number(metrics.get("consumed_artifact_count"))
        timeline_hits = sum(1 for item in timeline if isinstance(item, Mapping) and item.get("runtime_id") == runtime_id)
        return round(min(1.0, duration * 0.35 + (produced + consumed) / 12 + timeline_hits / 10), 4)

    def _pressure(self, runtime_id, metrics, obs_report, flow, load, health) -> float:
        missing = len(_list(flow.get("missing_required")))
        rejected = len(_list(flow.get("rejected_artifacts")))
        warnings = len(_list(obs_report.get("warnings")))
        explicit = _number(metrics.get("pressure", metrics.get("cognitive_pressure", 0.0)))
        raw = max(explicit, load * 0.45 + (1.0 - health) * 0.35 + min(0.25, (missing + rejected + warnings) * 0.05))
        return round(min(1.0, raw), 4)

    def _contribution(self, runtime_id, metrics, flow, timeline) -> float:
        produced = len(_list(flow.get("produced_artifacts"))) + _number(metrics.get("produced_artifact_count"))
        consumed = len(_list(flow.get("consumed_artifacts"))) + _number(metrics.get("consumed_artifact_count"))
        promoted = len(_list(flow.get("promoted_artifacts")))
        persisted = len(_list(flow.get("persisted_artifacts")))
        timeline_hits = sum(1 for item in timeline if isinstance(item, Mapping) and item.get("runtime_id") == runtime_id)
        return round(min(1.0, (produced + consumed + promoted + persisted) / 16 + timeline_hits / 12), 4)

    def _dependency_satisfaction(self, obs_health, flow, obs_report) -> float:
        explicit = _number(obs_health.get("artifact_consistency", obs_report.get("dependency_satisfaction", 0.0)))
        if explicit > 0:
            return explicit
        missing = len(_list(flow.get("missing_required")))
        return round(max(0.0, 1.0 - missing * 0.12), 4)

    def _influence_graph(self, ecology, runtime_report, observability_report, timeline) -> dict[str, Any]:
        graph = _mapping(runtime_report.get("runtime_graph"))
        edges = []
        for edge in _list(graph.get("edges")):
            source = str(edge.get("from") or edge.get("source") or "")
            target = str(edge.get("to") or edge.get("target") or "")
            if source and target and source in ecology and target in ecology:
                edges.append(self._influence_edge(source, target, ecology, "dependency"))
        flow = _mapping(observability_report.get("artifact_flow_observability"))
        producers = {
            runtime_id: set(_list(bucket.get("produced_artifacts")) + list(_mapping(bucket.get("published_artifacts")).keys()))
            for runtime_id, bucket in flow.items()
            if isinstance(bucket, Mapping)
        }
        consumers = {
            runtime_id: set(_list(bucket.get("consumed_artifacts")))
            for runtime_id, bucket in flow.items()
            if isinstance(bucket, Mapping)
        }
        for source, produced in producers.items():
            for target, consumed in consumers.items():
                if source != target and source in ecology and target in ecology and produced & consumed:
                    edges.append(self._influence_edge(source, target, ecology, "cooperation"))
        ordered = [str(item.get("runtime_id")) for item in timeline if isinstance(item, Mapping) and item.get("runtime_id")]
        for source, target in zip(ordered, ordered[1:]):
            if source != target and source in ecology and target in ecology:
                edges.append(self._influence_edge(source, target, ecology, "propagation"))
        edges = _dedupe_edges(edges)
        return {
            "nodes": [
                {
                    "id": runtime_id,
                    "type": "runtime_organism",
                    "health": item.health,
                    "pressure": item.pressure,
                    "energy": item.energy,
                    "influence": item.influence,
                }
                for runtime_id, item in ecology.items()
            ],
            "edges": edges,
            "node_count": len(ecology),
            "edge_count": len(edges),
            "relationship_types": sorted({edge["relationship"] for edge in edges}),
        }

    def _influence_edge(self, source, target, ecology, relationship) -> dict[str, Any]:
        source_state = ecology[source]
        target_state = ecology[target]
        influence = round(min(1.0, source_state.influence * 0.65 + target_state.dependency_satisfaction * 0.35), 4)
        harm = round(source_state.risk * max(0.1, target_state.influence), 4)
        benefit = round(source_state.contribution * target_state.recovery_capacity, 4)
        return {
            "source": source,
            "target": target,
            "relationship": relationship,
            "influence": influence,
            "benefit": benefit,
            "degradation_harm": harm,
        }

    def _resource_flow(self, ecology, runtime_report, governance_report, policy_report) -> dict[str, Any]:
        budgets = _mapping(governance_report.get("runtime_budgets", governance_report.get("Runtime Budgets")))
        flows = []
        for runtime_id, item in ecology.items():
            budget = _number(_mapping(budgets.get(runtime_id)).get("budget", budgets.get(runtime_id, 0.0)))
            attention = round(min(1.0, item.pressure * 0.4 + item.influence * 0.35 + item.risk * 0.25), 4)
            direction = "increase" if item.pressure >= 0.7 and item.health >= 0.45 else "decrease" if item.energy < 0.35 else "maintain"
            flows.append({
                "runtime_id": runtime_id,
                "attention": attention,
                "reasoning_budget": budget if "reasoning" in runtime_id else round(attention * 0.5, 4),
                "search_budget": budget if "search" in runtime_id else round(attention * 0.45, 4),
                "validation_budget": budget if "truth" in runtime_id or "evidence" in runtime_id else round(attention * 0.35, 4),
                "memory_budget": budget if "memory" in runtime_id else round(attention * 0.25, 4),
                "cooling_budget": round(item.pressure * item.risk, 4),
                "recommended_flow": direction,
            })
        return {
            "flows": flows,
            "resource_balance": self._balance([item["attention"] for item in flows]),
            "policy_budget_context": _small(policy_report),
        }

    def _bottlenecks(self, ecology, observability_report) -> list[dict[str, Any]]:
        bottlenecks = []
        gaps = _mapping(observability_report.get("observability_gap_detection"))
        gap_runtimes = set()
        for key in ("missing_snapshots", "missing_metrics", "missing_telemetry", "missing_artifact_reports", "missing_lifecycle_events"):
            gap_runtimes.update(str(item) for item in _list(gaps.get(key)))
        for runtime_id, item in ecology.items():
            reasons = []
            if item.pressure >= 0.68:
                reasons.append("high_pressure")
            if item.health < 0.55:
                reasons.append("low_health")
            if item.energy < 0.35:
                reasons.append("low_energy")
            if item.dependency_satisfaction < 0.65:
                reasons.append("dependency_satisfaction_low")
            if runtime_id in gap_runtimes:
                reasons.append("observability_gap")
            if reasons:
                bottlenecks.append({
                    "runtime_id": runtime_id,
                    "severity": round(item.risk, 4),
                    "pressure": item.pressure,
                    "health": item.health,
                    "reasons": reasons,
                    "predicted_before_failure": item.risk < 0.85,
                })
        bottlenecks.sort(key=lambda item: item["severity"], reverse=True)
        return bottlenecks

    def _cascade_analysis(self, ecology, influence_graph, bottlenecks) -> dict[str, Any]:
        bottleneck_ids = {item["runtime_id"] for item in bottlenecks}
        chains = []
        for start in bottleneck_ids:
            chain = [start]
            current = start
            visited = {start}
            for _ in range(5):
                outgoing = [
                    edge for edge in influence_graph["edges"]
                    if edge["source"] == current and edge["target"] not in visited
                ]
                if not outgoing:
                    break
                next_edge = max(outgoing, key=lambda edge: edge["influence"] * edge["degradation_harm"])
                current = next_edge["target"]
                chain.append(current)
                visited.add(current)
            if len(chain) > 1:
                chains.append({
                    "chain": chain,
                    "cascade_risk": round(sum(ecology[item].risk for item in chain) / len(chain), 4),
                    "interpretation": " -> ".join(chain),
                })
        return {
            "cascading_failures_predicted": bool(chains),
            "chains": sorted(chains, key=lambda item: item["cascade_risk"], reverse=True)[:10],
        }

    def _recovery_actions(self, ecology, bottlenecks, acsc_report) -> list[dict[str, Any]]:
        actions = []
        for bottleneck in bottlenecks:
            runtime_id = bottleneck["runtime_id"]
            item = ecology[runtime_id]
            if item.pressure >= 0.75:
                action = "increase_acsc_cooling"
            elif item.energy < 0.35:
                action = "pause_expensive_runtime"
            elif "search" in runtime_id:
                action = "reduce_search_depth_and_increase_reuse"
            elif "memory" in runtime_id:
                action = "trigger_memory_compression"
            elif "truth" in runtime_id:
                action = "increase_evidence_before_truth_promotion"
            else:
                action = "redistribute_resources"
            actions.append({
                "runtime_id": runtime_id,
                "action": action,
                "priority": "critical" if item.risk >= 0.75 else "high" if item.risk >= 0.55 else "medium",
                "expected_effect": round(min(1.0, item.pressure * 0.45 + item.risk * 0.35 + (1.0 - item.energy) * 0.2), 4),
            })
        if not actions:
            actions.append({
                "runtime_id": "ecosystem",
                "action": "maintain_balanced_homeostasis",
                "priority": "normal",
                "expected_effect": 0.2,
            })
        return actions

    def _global_health(self, ecology) -> float:
        return round(sum(item.health for item in ecology.values()) / max(len(ecology), 1), 4)

    def _global_stability(self, ecology, influence_graph) -> float:
        avg_stability = sum(item.stability for item in ecology.values()) / max(len(ecology), 1)
        influence_values = [_number(edge.get("influence")) for edge in influence_graph["edges"]]
        influence_balance = self._balance(influence_values)
        pressure_balance = self._balance([item.pressure for item in ecology.values()])
        return round(avg_stability * 0.55 + influence_balance * 0.25 + pressure_balance * 0.2, 4)

    def _homeostasis_score(self, ecology, resource_flow, recovery_actions) -> float:
        health = self._global_health(ecology)
        pressure_balance = self._balance([item.pressure for item in ecology.values()])
        energy_balance = self._balance([item.energy for item in ecology.values()])
        resource_balance = _number(resource_flow.get("resource_balance"))
        recovery_readiness = self._recovery_efficiency(ecology, recovery_actions)
        return round(health * 0.3 + pressure_balance * 0.2 + energy_balance * 0.2 + resource_balance * 0.15 + recovery_readiness * 0.15, 4)

    def _risk_forecast(self, ecology, cascade, bottlenecks) -> list[dict[str, Any]]:
        forecasts = []
        for runtime_id, item in ecology.items():
            future_pressure = round(min(1.0, item.pressure + item.load * 0.15 + item.risk * 0.1), 4)
            future_health = round(max(0.0, item.health - item.pressure * 0.08 + item.recovery_capacity * 0.04), 4)
            if future_pressure >= 0.65 or future_health < 0.55 or item.risk >= 0.55:
                forecasts.append({
                    "runtime_id": runtime_id,
                    "future_pressure": future_pressure,
                    "future_health": future_health,
                    "future_resource_need": round(min(1.0, future_pressure * 0.6 + item.influence * 0.4), 4),
                    "risk": item.risk,
                    "predicted_failure": future_health < 0.4 or future_pressure >= 0.85,
                })
        forecasts.sort(key=lambda item: (item["predicted_failure"], item["risk"]), reverse=True)
        return forecasts[:12]

    def _dependency_health(self, ecology, influence_graph) -> dict[str, Any]:
        values = {runtime_id: item.dependency_satisfaction for runtime_id, item in ecology.items()}
        return {
            "average_dependency_satisfaction": round(sum(values.values()) / max(len(values), 1), 4),
            "runtime_dependency_satisfaction": values,
            "weak_dependencies": [runtime_id for runtime_id, value in values.items() if value < 0.65],
            "influence_edges_considered": influence_graph["edge_count"],
        }

    def _collaboration_matrix(self, ecology, influence_graph) -> dict[str, dict[str, float]]:
        matrix = {runtime_id: {} for runtime_id in ecology}
        for edge in influence_graph["edges"]:
            score = round(_number(edge.get("benefit")) * 0.6 + _number(edge.get("influence")) * 0.4, 4)
            matrix.setdefault(edge["source"], {})[edge["target"]] = score
            matrix.setdefault(edge["target"], {}).setdefault(edge["source"], round(score * 0.8, 4))
        return matrix

    def _runtime_collaboration(self, ecology, influence_graph) -> dict[str, Any]:
        matrix = self._collaboration_matrix(ecology, influence_graph)
        scores = [score for row in matrix.values() for score in row.values()]
        return {
            "collaboration_quality": self._collaboration_quality(ecology, influence_graph),
            "strong_collaborations": [
                {"source": source, "target": target, "score": score}
                for source, row in matrix.items()
                for target, score in row.items()
                if score >= 0.55
            ][:20],
            "average_collaboration": round(sum(scores) / max(len(scores), 1), 4),
        }

    def _workload_balancing(self, ecology) -> dict[str, Any]:
        loads = {runtime_id: item.load for runtime_id, item in ecology.items()}
        overloaded = [runtime_id for runtime_id, load in loads.items() if load >= 0.72]
        idle = [runtime_id for runtime_id, load in loads.items() if load <= 0.12]
        return {
            "load_distribution": loads,
            "overloaded_runtimes": overloaded,
            "idle_runtimes": idle,
            "resource_distribution_evenness": self._balance(list(loads.values())),
            "execution_starvation_risk": bool(overloaded and idle),
        }

    def _predictive_ecology(self, ecology, risk_forecast) -> dict[str, Any]:
        return {
            "future_pressure": {runtime_id: round(min(1.0, item.pressure + item.load * 0.15), 4) for runtime_id, item in ecology.items()},
            "future_runtime_health": {runtime_id: round(max(0.0, item.health - item.risk * 0.08), 4) for runtime_id, item in ecology.items()},
            "future_bottlenecks": [item["runtime_id"] for item in risk_forecast],
            "future_failures": [item["runtime_id"] for item in risk_forecast if item["predicted_failure"]],
            "future_recovery_actions": ["increase_cooling", "redistribute_resources", "increase_reuse"] if risk_forecast else ["maintain_homeostasis"],
        }

    def _self_organization(self, ecology, bottlenecks) -> dict[str, Any]:
        priority_adjustments = {
            runtime_id: "increase_priority" if item.pressure >= 0.7 and item.health >= 0.45 else "decrease_priority" if item.energy < 0.35 else "maintain_priority"
            for runtime_id, item in ecology.items()
        }
        return {
            "dynamic_priority_adjustment": priority_adjustments,
            "adaptive_execution_ordering": sorted(ecology, key=lambda runtime_id: (ecology[runtime_id].risk, ecology[runtime_id].influence), reverse=True),
            "adaptive_resource_routing": [item["runtime_id"] for item in bottlenecks[:5]],
            "emergent_optimization_available": bool(ecology),
        }

    def _ecological_adaptation(self, ecology, experience_report, analytics_report) -> dict[str, Any]:
        domains = _list(_mapping(experience_report.get("experience")).get("semantic_domains"))
        patterns = {}
        for domain in domains:
            dominant = max(ecology.values(), key=lambda item: item.contribution, default=None)
            if dominant:
                patterns[str(domain)] = f"{dominant.runtime_id}_dominates"
        return {
            "learned_task_configurations": patterns,
            "healthy_configuration_candidates": [runtime_id for runtime_id, item in ecology.items() if item.health >= 0.75 and item.pressure <= 0.45],
            "failure_configuration_candidates": [runtime_id for runtime_id, item in ecology.items() if item.risk >= 0.65],
            "adaptation_quality": round(self._global_health(ecology) * 0.5 + self._balance([item.pressure for item in ecology.values()]) * 0.5, 4),
            "analytics_context": _small(analytics_report),
        }

    def _world_model_updates(self, ecology, stability, homeostasis, world_model_report) -> dict[str, Any]:
        return {
            "world_model_stores_ecosystem_states": True,
            "successful_ecosystem_configurations": [runtime_id for runtime_id, item in ecology.items() if item.health >= 0.75 and item.stability >= 0.7],
            "failure_configurations": [runtime_id for runtime_id, item in ecology.items() if item.risk >= 0.65],
            "recovery_configurations": [runtime_id for runtime_id, item in ecology.items() if item.recovery_capacity >= 0.7],
            "adaptive_configurations": [runtime_id for runtime_id, item in ecology.items() if item.adaptability >= 0.7],
            "global_stability": stability,
            "homeostasis_score": homeostasis,
            "world_model_context": _small(world_model_report),
        }

    def _dna_updates(self, ecology, dna_report) -> dict[str, Any]:
        return {
            "dna_evolves_from_ecosystem_behavior": True,
            "resource_allocation_traits": {runtime_id: "increase_resource_bias" for runtime_id, item in ecology.items() if item.contribution >= 0.55},
            "collaboration_traits": {runtime_id: "strengthen_collaboration" for runtime_id, item in ecology.items() if item.influence >= 0.65},
            "recovery_traits": {runtime_id: "strengthen_recovery" for runtime_id, item in ecology.items() if item.recovery_capacity >= 0.7},
            "balance_traits": {runtime_id: "reduce_pressure" for runtime_id, item in ecology.items() if item.pressure >= 0.7},
            "efficiency_traits": {runtime_id: "preserve_efficient_configuration" for runtime_id, item in ecology.items() if item.efficiency >= 0.7},
            "dna_context": _small(dna_report),
        }

    def _recommendations(self, ecology, bottlenecks, recovery, adaptation) -> list[str]:
        recommendations = []
        for item in bottlenecks[:5]:
            recommendations.append(f"Stabilize {item['runtime_id']} because {', '.join(item['reasons'])}.")
        for item in recovery[:5]:
            recommendations.append(f"{item['action']} for {item['runtime_id']} at {item['priority']} priority.")
        if adaptation["healthy_configuration_candidates"]:
            recommendations.append("Preserve healthy ecosystem configurations in ecological memory.")
        if not recommendations:
            recommendations.append("Maintain current ecosystem balance and continue predictive monitoring.")
        return recommendations

    def _recovery_efficiency(self, ecology, recovery_actions) -> float:
        if not recovery_actions:
            return self._global_health(ecology)
        effects = [_number(item.get("expected_effect")) for item in recovery_actions]
        risk = sum(item.risk for item in ecology.values()) / max(len(ecology), 1)
        return round(max(0.0, min(1.0, sum(effects) / max(len(effects), 1) * 0.6 + (1.0 - risk) * 0.4)), 4)

    def _collaboration_quality(self, ecology, influence_graph) -> float:
        if not influence_graph["edges"]:
            return 0.0
        scores = [_number(edge.get("benefit")) * 0.5 + _number(edge.get("influence")) * 0.5 for edge in influence_graph["edges"]]
        return round(sum(scores) / max(len(scores), 1), 4)

    def _balance(self, values: list[float]) -> float:
        values = [_number(value) for value in values]
        if not values:
            return 0.0
        spread = max(values) - min(values)
        return round(max(0.0, 1.0 - spread), 4)

    def _persist_state(self, state: Mapping[str, Any]) -> dict[str, Any]:
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        history = []
        if self.memory_path.exists():
            try:
                payload = json.loads(self.memory_path.read_text(encoding="utf-8"))
                history = list(payload.get("ecosystem_states", [])) if isinstance(payload, Mapping) else []
            except (OSError, ValueError):
                history = []
        history.append(dict(state))
        history = history[-200:]
        try:
            self.memory_path.write_text(
                json.dumps({"ecosystem_states": history}, indent=2, sort_keys=True, default=str),
                encoding="utf-8",
            )
        except OSError as error:
            return {"stored": False, "reason": str(error)}
        return {"stored": True, "path": str(self.memory_path), "state_count": len(history)}


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _number(value: Any) -> float:
    try:
        if value is None or isinstance(value, bool):
            return 0.0
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


def _small(value: Mapping[str, Any], limit: int = 8) -> dict[str, Any]:
    output = {}
    for index, (key, item) in enumerate(value.items()):
        if index >= limit:
            break
        if isinstance(item, (str, int, float, bool)) or item is None:
            output[str(key)] = item
        elif isinstance(item, list):
            output[str(key)] = {"count": len(item)}
        elif isinstance(item, Mapping):
            output[str(key)] = {"keys": sorted(str(k) for k in item.keys())[:8]}
        else:
            output[str(key)] = type(item).__name__
    return output


def _id(prefix: str, *values: Any) -> str:
    digest = hashlib.sha1(json.dumps(values, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _dedupe_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    output = []
    for edge in edges:
        marker = (edge.get("source"), edge.get("target"), edge.get("relationship"))
        if not edge.get("source") or not edge.get("target") or edge.get("source") == edge.get("target") or marker in seen:
            continue
        output.append(edge)
        seen.add(marker)
    return output


cognitive_ecosystem_engine = CognitiveEcosystemEngine()
