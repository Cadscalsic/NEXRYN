"""Semantic intelligence over canonical SearchRoute instances."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Sequence


class RouteIntelligenceMemory:
    """Persistent compact route outcomes and lifecycle histories."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path("runtime/artifacts/runtime_data") / "route_intelligence_memory.json"

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"routes": []}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"routes": []}
        return payload if isinstance(payload, dict) else {"routes": []}

    def history_for(self, trigger: str) -> dict[str, Any]:
        routes = [
            item for item in self.load().get("routes", [])
            if isinstance(item, Mapping) and item.get("creation_trigger") == trigger
        ]
        successes = sum(1 for item in routes if item.get("validated") is True)
        failures = sum(1 for item in routes if item.get("failed") is True)
        return {
            "observations": len(routes),
            "historical_success": successes,
            "historical_failure": failures,
            "historical_success_rate": round(successes / max(len(routes), 1), 4),
            "average_route_score": round(
                sum(_number(item.get("overall_route_score")) for item in routes)
                / max(len(routes), 1),
                4,
            ),
            "average_search_cost": round(
                sum(_number(item.get("search_cost")) for item in routes)
                / max(len(routes), 1),
                4,
            ),
        }

    def remember(self, entities: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.load()
        entries = list(payload.get("routes", []))
        for route in entities:
            quality = route.get("quality", {})
            entries.append({
                "route_id": route.get("route_id"),
                "creation_trigger": route.get("creation_trigger"),
                "state": route.get("current_state"),
                "overall_route_score": route.get("overall_route_score"),
                "expected_future_utility": route.get("expected_future_utility"),
                "search_cost": quality.get("search_cost"),
                "novelty_score": quality.get("novelty_score"),
                "validated": (
                    route.get("current_state") == "VALIDATED"
                    or route.get("proposed_state") == "VALIDATED"
                ),
                "failed": (
                    route.get("current_state") in {"FAILED", "PRUNED", "ARCHIVED"}
                    or route.get("proposed_state") in {"FAILED", "PRUNED", "ARCHIVED"}
                ),
                "reused": bool(route.get("supporting_programs")),
                "cooled": route.get("current_state") in {"COOLING", "SUSPENDED"},
                "reactivated": route.get("current_state") == "REACTIVATED",
                "merged": route.get("current_state") == "MERGED",
                "split": route.get("current_state") == "SPLIT",
            })
        payload["routes"] = entries[-500:]
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return {
            "persistent_route_intelligence_memory": True,
            "memory_path": str(self.path),
            "entries_stored": len(payload["routes"]),
            "best_routes": self._rank(entries, "overall_route_score", reverse=True),
            "worst_routes": self._rank(entries, "overall_route_score"),
            "most_reused_routes": [
                item["route_id"] for item in entries if item.get("reused")
            ][-5:],
            "fastest_successful_routes": [
                item["route_id"]
                for item in sorted(
                    (entry for entry in entries if entry.get("validated")),
                    key=lambda entry: (_number(entry.get("search_cost")), str(entry.get("route_id"))),
                )[:5]
            ],
            "most_innovative_routes": self._rank(entries, "novelty_score", reverse=True),
            "most_expensive_routes": self._rank(entries, "search_cost", reverse=True),
            "cooling_history": [item["route_id"] for item in entries if item.get("cooled")][-20:],
            "reactivation_history": [item["route_id"] for item in entries if item.get("reactivated")][-20:],
            "merge_history": [item["route_id"] for item in entries if item.get("merged")][-20:],
            "split_history": [item["route_id"] for item in entries if item.get("split")][-20:],
        }

    def _rank(self, entries, key, reverse=False):
        ranked = sorted(
            entries,
            key=lambda item: (_number(item.get(key)), str(item.get("route_id"))),
            reverse=reverse,
        )
        return [item.get("route_id") for item in ranked[:5]]


class CognitiveRouteIntelligenceEngine:
    """Understand route quality and evolution without creating or executing routes."""

    system_name = "cognitive_route_intelligence_engine"

    def __init__(
        self,
        memory: RouteIntelligenceMemory | None = None,
        persist_memory: bool = True,
    ) -> None:
        self.memory = memory or RouteIntelligenceMemory()
        self.persist_memory = persist_memory

    def build_report(
        self,
        routes: Sequence[Any] | None = None,
        search_policy_report: Mapping[str, Any] | None = None,
        adaptive_search_intelligence_report: Mapping[str, Any] | None = None,
        concept_formation_report: Mapping[str, Any] | None = None,
        program_synthesis_report: Mapping[str, Any] | None = None,
        truth_report: Mapping[str, Any] | None = None,
        memory_report: Mapping[str, Any] | None = None,
        search_report: Mapping[str, Any] | None = None,
        performance_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        started = perf_counter()
        policy = search_policy_report if isinstance(search_policy_report, Mapping) else {}
        adaptive = (
            adaptive_search_intelligence_report
            if isinstance(adaptive_search_intelligence_report, Mapping) else {}
        )
        concept_report = (
            concept_formation_report if isinstance(concept_formation_report, Mapping) else {}
        )
        program_report = (
            program_synthesis_report if isinstance(program_synthesis_report, Mapping) else {}
        )
        truth = truth_report if isinstance(truth_report, Mapping) else {}
        memory = memory_report if isinstance(memory_report, Mapping) else {}
        route_objects = list(routes or [])
        entities = [
            self._entity(
                route,
                policy,
                adaptive,
                concept_report,
                program_report,
                truth,
                memory,
            )
            for route in route_objects
        ]
        relationships = self._relationships(entities)
        children = self._children(relationships)
        for entity in entities:
            entity["child_routes"] = children.get(entity["route_id"], [])
            entity["relationships"] = [
                edge for edge in relationships
                if edge["from"] == entity["route_id"] or edge["to"] == entity["route_id"]
            ]
        ranked = sorted(
            entities,
            key=lambda route: (route["overall_route_score"], route["route_id"]),
            reverse=True,
        )
        graph = {
            "nodes": [
                {
                    "id": route["route_id"],
                    "type": "CognitiveRoute",
                    "state": route["current_state"],
                    "score": route["overall_route_score"],
                    "future_utility": route["expected_future_utility"],
                }
                for route in entities
            ],
            "edges": relationships,
            "relationship_types": sorted({edge["type"] for edge in relationships}),
            "node_count": len(entities),
            "edge_count": len(relationships),
        }
        elapsed = max(perf_counter() - started, 0.0)
        runtime = max(
            _number((performance_report or {}).get("search_time_seconds")),
            _number((performance_report or {}).get("execution_time")),
            _number((performance_report or {}).get("total_runtime_seconds")),
            0.001,
        )
        report = {
            "system": self.system_name,
            "COGNITIVE_ROUTE_INTELLIGENCE_REPORT": True,
            "route_graph": graph,
            "route_statistics": self._statistics(entities, relationships),
            "route_quality": {
                route["route_id"]: route["quality"] for route in entities
            },
            "route_evolution": {
                route["route_id"]: route["evolution"] for route in entities
            },
            "route_timeline": [
                snapshot
                for route in entities
                for snapshot in route["snapshots"]
            ],
            "route_ranking": [
                self._ranking_summary(route) for route in ranked
            ],
            "route_decisions": [
                {
                    "route_id": route["route_id"],
                    "decision": route["decision"],
                    "justification": route["decision_justification"],
                    "state": route["current_state"],
                    "overall_route_score": route["overall_route_score"],
                    "evidence": route["supporting_evidence"],
                    "expected_gain": route["expected_information_gain"],
                    "risk": route["risk_score"],
                    "utility": route["current_utility"],
                    "confidence": route["current_confidence"],
                }
                for route in entities
            ],
            "cognitive_routes": {
                route["route_id"]: route for route in entities
            },
            "cooling_candidates": self._candidates(
                entities, lambda route: route["decision"] == "Cool"
                or route["decision"] == "Prepare for Cooling"
                or route["quality"]["failure_risk"] >= 0.6
            ),
            "merge_candidates": self._merge_candidates(entities),
            "split_candidates": self._candidates(
                entities, lambda route: route["decision"] == "Split"
            ),
            "reactivation_candidates": self._candidates(
                entities, lambda route: route["reactivation_potential"] >= 0.45
                or route["proposed_state"] == "REACTIVATED"
            ),
            "dominant_route": ranked[0] if ranked else {},
            "dominant_routes": [
                route for route in ranked
                if route["proposed_state"] in {"DOMINANT", "VALIDATED"}
                or route["overall_route_score"] >= 0.65
            ],
            "emerging_routes": [
                route for route in ranked
                if route["current_state"] in {"DISCOVERED", "CREATED", "EXPLORING", "SUPPORTED", "PROMISING"}
            ],
            "weakest_route": ranked[-1] if ranked else {},
            "most_valuable_route": self._extreme(entities, "current_utility"),
            "highest_risk_route": self._extreme_quality(entities, "failure_risk"),
            "highest_potential_route": self._extreme(entities, "expected_future_utility"),
            "optimization_opportunities": self._optimization_opportunities(entities),
            "historical_comparison": {
                route["route_id"]: route["history"] for route in entities
            },
            "instrumentation_overhead_seconds": round(elapsed, 9),
            "instrumentation_overhead_below_2_percent": elapsed / runtime < 0.02,
            "runtime_alignment": {
                "canonical_search_route_objects_reused": True,
                "duplicate_route_objects_created": False,
                "search_behavior_changed": False,
                "solver_behavior_changed": False,
                "arc_algorithms_changed": False,
                "adaptive_search_policy_reused": bool(policy),
                "adaptive_search_intelligence_reused": bool(adaptive),
                "concept_formation_reused": bool(concept_report),
                "program_synthesis_reused": bool(program_report),
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        report["route_intelligence_memory"] = (
            self.memory.remember(entities)
            if self.persist_memory and entities
            else {"persistent_route_intelligence_memory": False, "reason": "no_routes"}
        )
        return report

    def _entity(
        self,
        route: Any,
        policy: Mapping[str, Any],
        adaptive: Mapping[str, Any],
        concept_report: Mapping[str, Any],
        program_report: Mapping[str, Any],
        truth_report: Mapping[str, Any],
        memory_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        route_id = str(_get(route, "route_id", "unknown_route"))
        state = str(_get(route, "current_state", "CREATED"))
        scores = dict(_get(route, "scores", {}) or {})
        confidence = _clamp(_get(route, "current_confidence", scores.get("confidence_score", 0.0)))
        evidence = _clamp(_get(route, "evidence_score", scores.get("evidence_score", 0.0)))
        info = _clamp(_get(route, "expected_information_gain", scores.get("information_gain", 0.0)))
        cost = _clamp(scores.get("search_cost", _get(route, "estimated_computational_cost", 0.0)))
        remaining = _clamp(scores.get("expected_remaining_cost", cost * (1.0 - confidence)))
        novelty = _clamp(scores.get("novelty_score", 1.0 / max(int(_get(route, "depth", 0)) + 1, 1)))
        generalization = _clamp(scores.get("generalization_potential"))
        validation = self._validation_strength(route)
        context = self._support_alignment(_get_list(route, "visited_concepts"))
        dependency = self._keyword_support(route, {"dependency", "causal", "constraint"})
        truth = max(validation, self._keyword_support(route, {"truth", "validated"}))
        memory = max(
            _clamp(scores.get("reuse_score")),
            self._keyword_support(route, {"reuse", "memory", "cache"}),
        )
        transformation_diversity = _clamp(
            len(set(_get_list(route, "visited_transformations"))) / 6
        )
        program_diversity = _clamp(
            len(set(_get_list(route, "visited_programs"))) / 4
        )
        concept_support = _get_list(route, "visited_concepts") or self._top_ids(
            concept_report,
            "top_concepts",
            "concept_id",
            3,
        )
        program_support = _get_list(route, "visited_programs") or self._top_ids(
            program_report,
            "winning_programs",
            "program_id",
            2,
        )
        truth_supporting = self._truth_supporting(truth_report, route_id, validation)
        memory_supporting = self._memory_supporting(memory_report, route_id)
        concept_coverage = _clamp(len(set(concept_support)) / max(_number(concept_report.get("concept_count")), 1.0))
        program_coverage = _clamp(len(set(program_support)) / max(_number(program_report.get("generated_programs")), 1.0))
        compression = round(_clamp((concept_coverage + program_coverage + generalization) / 3), 4)
        history = self.memory.history_for(str(_get(route, "creation_trigger", "")))
        historical = _clamp(history["historical_success_rate"])
        failure_risk = round(_clamp(
            (1.0 - confidence) * 0.30
            + (1.0 - evidence) * 0.25
            + cost * 0.20
            + (1.0 - validation) * 0.15
            + _clamp(history["historical_failure"] / max(history["observations"], 1)) * 0.10
        ), 4)
        utility = round(_clamp(
            confidence * 0.20 + evidence * 0.20 + info * 0.13
            + generalization * 0.12 + validation * 0.12
            + context * 0.08 + truth * 0.07 + memory * 0.04
            + historical * 0.04 - cost * 0.10
        ), 4)
        future = round(_clamp(
            utility * 0.45 + info * 0.20 + novelty * 0.12
            + generalization * 0.13 + memory * 0.05
            + (1.0 - remaining) * 0.05
        ), 4)
        overall = round(_clamp(
            confidence * 0.15 + evidence * 0.15 + utility * 0.17
            + novelty * 0.08 + info * 0.10 + generalization * 0.10
            + historical * 0.05 + context * 0.05 + truth * 0.05
            + memory * 0.04 + (1.0 - cost) * 0.03
            + (1.0 - remaining) * 0.03
        ), 4)
        stability = round(_clamp((confidence + validation + (1.0 - cost) + (1.0 - failure_risk)) / 4), 4)
        temperature = round(_clamp((1.0 - confidence) * 0.5 + info * 0.3 + novelty * 0.2), 4)
        energy = round(_clamp(utility * 0.45 + info * 0.25 + evidence * 0.20 + (1.0 - cost) * 0.10), 4)
        thermal = self._thermal_readiness(
            confidence=confidence,
            utility=utility,
            future=future,
            cost=cost,
            risk=failure_risk,
            stability=stability,
            information_gain=info,
        )
        adaptive_decision = self._adaptive_decision(adaptive, route_id)
        decision, reason, target_state = self._decision(
            state, overall, confidence, evidence, utility, future,
            info, cost, remaining, failure_risk, validation, route,
        )
        lifecycle = ["DISCOVERED", "CREATED"]
        if state != "CREATED":
            lifecycle.append(state)
        if target_state not in lifecycle:
            lifecycle.append(target_state)
        snapshots = self._snapshots(
            route_id, state, target_state, confidence, evidence, route
        )
        quality = {
            "confidence_score": confidence,
            "evidence_score": evidence,
            "novelty_score": novelty,
            "utility_score": utility,
            "search_cost": cost,
            "information_gain": info,
            "generalization_potential": generalization,
            "failure_risk": failure_risk,
            "transformation_diversity": transformation_diversity,
            "program_diversity": program_diversity,
            "validation_strength": validation,
            "context_alignment": context,
            "dependency_support": dependency,
            "truth_support": truth,
            "memory_support": memory,
            "concept_coverage": concept_coverage,
            "program_coverage": program_coverage,
            "compression_score": compression,
            "stability_score": stability,
            "expected_future_value": future,
            "thermal_readiness_score": thermal["thermal_readiness_score"],
        }
        return {
            "route_id": route_id,
            "parent_route": _get(route, "parent_route", None),
            "child_routes": [],
            "root_route": self._root_route(route),
            "route_generation_step": int(_get(route, "depth", 0)),
            "creation_trigger": str(_get(route, "creation_trigger", "search_space_initialization")),
            "creation_evidence": {
                "trigger": str(_get(route, "creation_trigger", "search_space_initialization")),
                "supporting_evidence_count": len(self._supporting_evidence(route)),
                "adaptive_search_decision": adaptive_decision,
            },
            "current_goal": str(_get(route, "current_goal", "interpret_and_reduce_search_uncertainty")),
            "current_strategy": policy.get(
                "selected_strategy",
                (adaptive.get("chosen_strategy") or {}).get("strategy", "Balanced Exploration")
                if isinstance(adaptive.get("chosen_strategy"), Mapping)
                else "Balanced Exploration",
            ),
            "current_state": state,
            "proposed_state": target_state,
            "current_confidence": confidence,
            "current_temperature": temperature,
            "current_energy": energy,
            "current_priority": _clamp(_get(route, "priority", 0.0)),
            "current_utility": utility,
            "expected_utility": future,
            "expected_future_utility": future,
            "future_value": future,
            "expected_information_gain": info,
            "novelty": novelty,
            "complexity": round(_clamp(cost + remaining + len(concept_support) / 20), 4),
            "estimated_remaining_cost": remaining,
            "search_budget_consumed": cost,
            "historical_success": history["historical_success"],
            "historical_failure": history["historical_failure"],
            "generalization_score": generalization,
            "compression_score": compression,
            "risk_score": failure_risk,
            "stability_score": stability,
            "priority_score": round(_clamp(overall * 0.45 + future * 0.35 + (1.0 - failure_risk) * 0.20), 4),
            "thermal_readiness": thermal,
            "thermal_readiness_score": thermal["thermal_readiness_score"],
            "cooling_priority": thermal["cooling_priority"],
            "cooling_risk": thermal["cooling_risk"],
            "cooling_benefit": thermal["cooling_benefit"],
            "expected_recovery_value": thermal["expected_recovery_value"],
            "reactivation_potential": thermal["reactivation_potential"],
            "supporting_evidence": self._supporting_evidence(route),
            "rejected_evidence": self._rejected_evidence(route),
            "supporting_concepts": list(concept_support),
            "supporting_transformations": list(_get_list(route, "visited_transformations")),
            "supporting_programs": list(program_support),
            "supporting_constraints": list(_get_list(route, "visited_constraints")),
            "supporting_truths": truth_supporting,
            "supporting_memory": memory_supporting,
            "current_policy": policy.get("selected_strategy", "Balanced Exploration"),
            "lifecycle": lifecycle,
            "snapshots": snapshots,
            "decision_history": [
                {
                    "decision": decision,
                    "from_state": state,
                    "to_state": target_state,
                    "evidence": self._supporting_evidence(route),
                    "expected_gain": info,
                    "risk": failure_risk,
                    "utility": utility,
                    "confidence": confidence,
                    "reason": reason,
                }
            ],
            "quality": quality,
            "confidence": confidence,
            "utility": utility,
            "evidence": self._supporting_evidence(route),
            "concept_coverage": concept_coverage,
            "program_coverage": program_coverage,
            "truth_support": truth,
            "memory_support": memory,
            "overall_route_score": overall,
            "decision": decision,
            "decision_justification": reason,
            "evolution": self._evolution(route, confidence, evidence, validation),
            "history": history,
            "explainability": self._explainability(route, state, decision, reason, overall, future),
        }

    def _decision(
        self, state, score, confidence, evidence, utility, future, info,
        cost, remaining, risk, validation, route,
    ):
        if validation >= 0.95:
            return "Validate", "Validation succeeded with strong route evidence.", "VALIDATED"
        if state in {"FAILED", "PRUNED"} or risk >= 0.82:
            return "Archive", "Failure risk exceeds future utility; retain as negative memory.", "ARCHIVED"
        if state == "SUSPENDED" and info >= 0.35:
            return "Promote", "Suspended route retains enough information gain for reactivation.", "REACTIVATED"
        if str(_get(route, "creation_trigger", "")) == "combined":
            return "Merge", "Combined hypotheses share evidence and should remain a merged route.", "MERGED"
        if int(_get(route, "branch_width", 0)) > 1 and info >= 0.30:
            return "Split", "Diverse hypotheses have enough information value for separate evaluation.", "SPLIT"
        if score >= 0.78 and confidence >= 0.70:
            return "Promote", "High confidence, utility, and route score justify dominant status.", "DOMINANT"
        if future >= 0.62 and evidence >= 0.45:
            return "Freeze", "Strong future utility justifies preserving this stable route.", "STABLE"
        if cost >= 0.50 and future >= 0.35 and risk < 0.75:
            return (
                "Prepare for Cooling",
                "Route is expensive enough for ACSC consideration while retaining recovery value.",
                "COOLING_READY",
            )
        if cost >= 0.60 and utility < 0.45:
            return "Cool", "Search cost is high relative to current and expected utility.", "COOLING"
        if risk >= 0.60 or (confidence < 0.30 and evidence < 0.30):
            return "Suspend", "Weak support and elevated failure risk do not justify current execution.", "SUSPENDED"
        if info >= 0.40 or future >= 0.45:
            return "Expand", "Expected information gain and future utility exceed remaining cost.", "PROMISING"
        return "Discard", "Low information gain and limited future utility do not justify expansion.", "PRUNED"

    def _relationships(self, entities):
        edges, seen = [], set()

        def add(source, target, relation, reason):
            key = (source, target, relation)
            if source and target and source != target and key not in seen:
                edges.append({"from": source, "to": target, "type": relation, "reason": reason})
                seen.add(key)

        for route in entities:
            parent = route.get("parent_route")
            if parent:
                add(parent, route["route_id"], "extends", "Route declares this parent.")
                add(route["route_id"], parent, "forks_from", "Route was generated from its parent.")
                add(route["route_id"], parent, "inherits", "Route inherits parent evidence and constraints.")
            if route["proposed_state"] == "MERGED":
                for other in entities:
                    if other["route_id"] != route["route_id"]:
                        add(other["route_id"], route["route_id"], "merges_into", "Combined route consolidates peer evidence.")
            if route["proposed_state"] == "REACTIVATED":
                add(route["route_id"], route["route_id"] + ":reactivation", "reactivates", "Information value survived suspension.")
            if route["proposed_state"] == "VALIDATED":
                add(route["route_id"], route["route_id"] + ":validation", "validates", "Validation evidence confirms the route.")
            if route["supporting_programs"]:
                add(route["route_id"], route["route_id"] + ":memory", "reuses", "Route reuses a synthesized program.")
        for index, left in enumerate(entities):
            for right in entities[index + 1:]:
                shared = set(left["supporting_concepts"]) & set(right["supporting_concepts"])
                if shared:
                    add(left["route_id"], right["route_id"], "supports", f"Shared concepts: {sorted(shared)}")
                left_failed = left["current_state"] in {"FAILED", "PRUNED"}
                right_failed = right["current_state"] in {"FAILED", "PRUNED"}
                if left_failed != right_failed and (
                    set(left["supporting_transformations"])
                    & set(right["supporting_transformations"])
                ):
                    add(left["route_id"], right["route_id"], "contradicts", "Shared transformation produced conflicting outcomes.")
        return edges

    def _children(self, relationships):
        children: dict[str, list[str]] = {}
        for edge in relationships:
            if edge["type"] == "extends":
                children.setdefault(edge["from"], []).append(edge["to"])
        return {key: sorted(set(value)) for key, value in children.items()}

    def _snapshots(self, route_id, state, target, confidence, evidence, route):
        snapshots = [
            {
                "route_id": route_id,
                "sequence": 1,
                "snapshot_type": "route_created",
                "confidence": 0.0,
                "evidence": 0.0,
                "state": "CREATED",
                "reason": "Canonical search route was materialized.",
            },
            {
                "route_id": route_id,
                "sequence": 2,
                "snapshot_type": "confidence_and_evidence_changed",
                "confidence": confidence,
                "evidence": evidence,
                "state": state,
                "reason": "Current route telemetry changed confidence or evidence.",
            },
        ]
        events = []
        event = {
            "SPLIT": "route_split",
            "MERGED": "route_merged",
            "COOLING": "cooling_begins",
            "REACTIVATED": "reactivation",
            "VALIDATED": "validation_succeeds",
            "FAILED": "validation_fails",
        }.get(target)
        if event:
            events.append(event)
        if state == "COOLING" and target != "COOLING":
            events.append("cooling_ends")
        if state == "REACTIVATED" and "reactivation" not in events:
            events.append("reactivation")
        validation_status = str(_get(route, "validation_status", "unknown"))
        if validation_status == "failed" and "validation_fails" not in events:
            events.append("validation_fails")
        if validation_status == "validated" and "validation_succeeds" not in events:
            events.append("validation_succeeds")
        for offset, event_name in enumerate(events, start=3):
            snapshots.append({
                "route_id": route_id,
                "sequence": offset,
                "snapshot_type": event_name,
                "confidence": confidence,
                "evidence": evidence,
                "state": target,
                "reason": f"Decision engine proposed {target}.",
            })
        return snapshots

    def _evolution(self, route, confidence, evidence, validation):
        hypotheses = list(_get_list(route, "hypotheses"))
        cost = _clamp((_get(route, "scores", {}) or {}).get("search_cost", _get(route, "estimated_computational_cost", 0.0)))
        risk = _clamp(1.0 - confidence + cost * 0.25)
        return {
            "confidence_growth": round(confidence, 4),
            "confidence_collapse": confidence < 0.25,
            "evidence_growth": round(evidence, 4),
            "knowledge_growth": len(hypotheses),
            "concept_growth": len(set(_get_list(route, "visited_concepts"))),
            "transformation_growth": len(set(_get_list(route, "visited_transformations"))),
            "program_growth": len(set(_get_list(route, "visited_programs"))),
            "utility_growth": round((confidence + evidence + validation) / 3, 4),
            "search_cost_growth": cost,
            "risk_evolution": risk,
            "temperature_readiness": round(_clamp((1.0 - confidence) * 0.6 + risk * 0.4), 4),
            "route_maturity": round(_clamp((confidence + evidence + validation + len(hypotheses) / 5) / 4), 4),
            "validation_progress": validation,
            "knowledge_produced": {
                "hypotheses": len(hypotheses),
                "concepts": len(set(_get_list(route, "visited_concepts"))),
                "transformations": len(set(_get_list(route, "visited_transformations"))),
                "programs": len(set(_get_list(route, "visited_programs"))),
            },
        }

    def _supporting_evidence(self, route):
        evidence = []
        for hypothesis in _get_list(route, "hypotheses"):
            if not isinstance(hypothesis, Mapping):
                continue
            strength = max(
                _number(hypothesis.get("explanatory_power")),
                _number(hypothesis.get("causal_support")),
                _number(hypothesis.get("semantic_support")),
                _number(hypothesis.get("residual_reduction")),
            )
            if strength > 0:
                evidence.append({
                    "source": str(hypothesis.get("type") or hypothesis.get("primitive") or "hypothesis"),
                    "strength": round(strength, 4),
                })
        return evidence

    def _rejected_evidence(self, route):
        if str(_get(route, "validation_status", "unknown")) == "failed":
            return [{"source": "candidate_validation", "reason": "Route failed validation."}]
        return []

    def _validation_strength(self, route):
        status = str(_get(route, "validation_status", "unknown"))
        return {"validated": 1.0, "failed": 0.0}.get(status, 0.35)

    def _support_alignment(self, values):
        return round(_clamp(len(set(values or [])) / 8), 4)

    def _keyword_support(self, route, tokens):
        text = " ".join(
            str(value).lower()
            for values in (
                _get_list(route, "visited_concepts"),
                _get_list(route, "visited_constraints"),
                _get_list(route, "visited_programs"),
            )
            for value in values
        )
        return round(_clamp(sum(token in text for token in tokens) / max(len(tokens), 1)), 4)

    def _explainability(self, route, state, decision, reason, score, future):
        exists = f"Created by {_get(route, 'creation_trigger', 'search initialization')}."
        survived = (
            "It survived because evidence, utility, or information gain remains positive."
            if decision not in {"Archive", "Discard"}
            else "It did not survive active search; it is retained for negative memory."
        )
        return {
            "why_it_exists": exists,
            "why_it_survived": survived,
            "why_it_expanded": reason if decision == "Expand" else "Route was not expanded.",
            "why_it_became_dominant": (
                "Combined route score and confidence crossed the dominant threshold."
                if decision == "Promote" else "Route is not dominant."
            ),
            "why_it_cooled": reason if decision == "Cool" else "Route is not cooling.",
            "why_it_was_reactivated": reason if state == "REACTIVATED" else "Route was not reactivated.",
            "why_it_merged": reason if decision == "Merge" else "Route was not merged.",
            "why_it_split": reason if decision == "Split" else "Route was not split.",
            "why_it_suspended": reason if decision == "Suspend" else "Route was not suspended.",
            "why_it_failed": (
                reason if state in {"FAILED", "PRUNED", "ARCHIVED"}
                else "No terminal route failure is recorded."
            ),
            "score_summary": f"overall={score:.4f}, future_utility={future:.4f}",
        }

    def _thermal_readiness(
        self,
        *,
        confidence,
        utility,
        future,
        cost,
        risk,
        stability,
        information_gain,
    ):
        readiness = round(_clamp(cost * 0.30 + risk * 0.30 + (1.0 - utility) * 0.20 + stability * 0.20), 4)
        benefit = round(_clamp(cost * 0.35 + risk * 0.25 + (1.0 - future) * 0.20 + (1.0 - information_gain) * 0.20), 4)
        reactivation = round(_clamp(information_gain * 0.35 + future * 0.35 + confidence * 0.15 + stability * 0.15), 4)
        return {
            "thermal_readiness_score": readiness,
            "cooling_priority": "HIGH" if readiness >= 0.68 else "MEDIUM" if readiness >= 0.42 else "LOW",
            "cooling_risk": round(_clamp((1.0 - reactivation) * 0.55 + risk * 0.45), 4),
            "cooling_benefit": benefit,
            "expected_recovery_value": reactivation,
            "reactivation_potential": reactivation,
            "explanation": "Computed for ACSC consumption only; this engine does not perform cooling.",
        }

    def _adaptive_decision(self, adaptive, route_id):
        for item in adaptive.get("route_decisions", []) if isinstance(adaptive, Mapping) else []:
            if isinstance(item, Mapping) and str(item.get("route_id")) == route_id:
                return {
                    "decision": item.get("decision"),
                    "explanation": item.get("explanation"),
                    "score": item.get("score"),
                }
        return {}

    def _top_ids(self, report, key, id_key, limit):
        values = report.get(key, []) if isinstance(report, Mapping) else []
        return [
            str(item.get(id_key))
            for item in values[:limit]
            if isinstance(item, Mapping) and item.get(id_key)
        ]

    def _truth_supporting(self, report, route_id, validation):
        if not report:
            return []
        return [{
            "source": "truth_runtime",
            "route_id": route_id,
            "support": round(validation, 4),
            "available": True,
        }]

    def _memory_supporting(self, report, route_id):
        if not report:
            return []
        return [{
            "source": "memory_runtime",
            "route_id": route_id,
            "available": True,
            "summary_keys": sorted(str(key) for key in report.keys())[:6],
        }]

    def _root_route(self, route):
        parent = _get(route, "parent_route", None)
        return str(parent or _get(route, "route_id", "unknown_route"))

    def _ranking_summary(self, route):
        return {
            "route_id": route["route_id"],
            "rank_score": route["overall_route_score"],
            "confidence": route["current_confidence"],
            "utility": route["current_utility"],
            "evidence_quality": route["quality"]["evidence_score"],
            "program_strength": route["quality"]["program_diversity"],
            "concept_coverage": route["concept_coverage"],
            "truth_support": route["truth_support"],
            "memory_reuse": route["memory_support"],
            "expected_generalization": route["generalization_score"],
            "expected_compression": route["compression_score"],
            "future_value": route["future_value"],
            "search_cost": route["search_budget_consumed"],
        }

    def _statistics(self, entities, relationships):
        states: dict[str, int] = {}
        for route in entities:
            states[route["current_state"]] = states.get(route["current_state"], 0) + 1
        scores = [route["overall_route_score"] for route in entities]
        entropy = 0.0
        total = sum(max(score, 0.0001) for score in scores)
        if total:
            for score in scores:
                probability = max(score, 0.0001) / total
                entropy -= probability * _log2(probability)
        return {
            "routes": len(entities),
            "states": states,
            "relationships": len(relationships),
            "route_diversity": len({
                concept
                for route in entities
                for concept in route.get("supporting_concepts", [])
            }),
            "route_entropy": round(entropy, 4),
            "average_route_score": round(
                sum(route["overall_route_score"] for route in entities)
                / max(len(entities), 1),
                4,
            ),
            "average_utility": round(
                sum(route["current_utility"] for route in entities)
                / max(len(entities), 1),
                4,
            ),
            "average_confidence": round(
                sum(route["current_confidence"] for route in entities)
                / max(len(entities), 1),
                4,
            ),
            "average_search_cost": round(
                sum(route["search_budget_consumed"] for route in entities)
                / max(len(entities), 1),
                4,
            ),
            "average_program_coverage": round(
                sum(route["program_coverage"] for route in entities)
                / max(len(entities), 1),
                4,
            ),
            "average_concept_coverage": round(
                sum(route["concept_coverage"] for route in entities)
                / max(len(entities), 1),
                4,
            ),
            "generalization_index": round(
                sum(route["generalization_score"] for route in entities)
                / max(len(entities), 1),
                4,
            ),
            "compression_index": round(
                sum(route["compression_score"] for route in entities)
                / max(len(entities), 1),
                4,
            ),
            "route_stability": round(
                sum(route["stability_score"] for route in entities)
                / max(len(entities), 1),
                4,
            ),
            "route_lifetime": round(
                sum(len(route["snapshots"]) for route in entities)
                / max(len(entities), 1),
                4,
            ),
            "dominant_route_ratio": round(
                len([
                    route for route in entities
                    if route["proposed_state"] in {"DOMINANT", "VALIDATED"}
                    or route["overall_route_score"] >= 0.65
                ])
                / max(len(entities), 1),
                4,
            ),
            "average_future_utility": round(
                sum(route["expected_future_utility"] for route in entities)
                / max(len(entities), 1),
                4,
            ),
            "snapshots": sum(len(route["snapshots"]) for route in entities),
        }

    def _optimization_opportunities(self, entities):
        opportunities = []
        if any(route["thermal_readiness_score"] >= 0.68 for route in entities):
            opportunities.append({
                "opportunity": "send_high_readiness_routes_to_acsc",
                "reason": "Some routes are costly or risky enough to be cooling candidates.",
            })
        if any(route["program_coverage"] < 0.2 for route in entities):
            opportunities.append({
                "opportunity": "increase_program_support",
                "reason": "At least one route has weak synthesized-program coverage.",
            })
        if any(route["concept_coverage"] < 0.2 for route in entities):
            opportunities.append({
                "opportunity": "increase_concept_support",
                "reason": "At least one route has weak concept coverage.",
            })
        if any(route["risk_score"] >= 0.7 for route in entities):
            opportunities.append({
                "opportunity": "prune_or_suspend_high_risk_routes",
                "reason": "High-risk routes should stop consuming active search budget.",
            })
        return opportunities or [{
            "opportunity": "maintain_route_policy",
            "reason": "Route intelligence currently has enough evidence for stable ranking.",
        }]

    def _candidates(self, entities, predicate):
        return [
            {
                "route_id": route["route_id"],
                "score": route["overall_route_score"],
                "decision": route["decision"],
                "reason": route["decision_justification"],
            }
            for route in entities if predicate(route)
        ]

    def _merge_candidates(self, entities):
        candidates = []
        for index, left in enumerate(entities):
            for right in entities[index + 1:]:
                shared = sorted(
                    set(left["supporting_concepts"]) & set(right["supporting_concepts"])
                )
                if shared:
                    candidates.append({
                        "routes": [left["route_id"], right["route_id"]],
                        "shared_concepts": shared,
                        "reason": "Shared conceptual support makes evidence consolidation viable.",
                    })
        return candidates

    def _extreme(self, entities, key):
        return max(entities, key=lambda route: (route[key], route["route_id"]), default={})

    def _extreme_quality(self, entities, key):
        return max(
            entities,
            key=lambda route: (route["quality"][key], route["route_id"]),
            default={},
        )


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: Any) -> float:
    return max(0.0, min(1.0, _number(value)))


def _get(route: Any, key: str, default: Any = None) -> Any:
    if isinstance(route, Mapping):
        return route.get(key, default)
    return getattr(route, key, default)


def _get_list(route: Any, key: str) -> list[Any]:
    value = _get(route, key, [])
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _log2(value: float) -> float:
    if value <= 0:
        return 0.0
    import math
    return math.log2(value)


cognitive_route_intelligence_engine = CognitiveRouteIntelligenceEngine()


__all__ = [
    "CognitiveRouteIntelligenceEngine",
    "RouteIntelligenceMemory",
    "cognitive_route_intelligence_engine",
]
