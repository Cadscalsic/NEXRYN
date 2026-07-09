"""Deterministic strategic control for the existing cognitive search runtime."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping


LEVELS = (
    ("VERY_EASY", 0.20, (1, 2)),
    ("EASY", 0.40, (3, 4)),
    ("MEDIUM", 0.65, (5, 8)),
    ("HARD", 0.85, (10, 16)),
    ("VERY_HARD", 1.01, (16, 24)),
)


class AdaptiveSearchPolicyMemory:
    """Compact persistent outcomes used only as deterministic policy evidence."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path("runtime_data") / "adaptive_search_policy_memory.json"

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"policies": []}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"policies": []}
        return payload if isinstance(payload, dict) else {"policies": []}

    def summary(self, task_type: str) -> dict[str, Any]:
        entries = [
            item for item in self.load().get("policies", [])
            if isinstance(item, Mapping) and item.get("task_type") == task_type
        ]
        successful = [item for item in entries if item.get("success") is True]
        strategies: dict[str, list[Mapping[str, Any]]] = {}
        for item in entries:
            strategies.setdefault(str(item.get("strategy")), []).append(item)
        ranked = sorted(
            strategies,
            key=lambda name: (
                -sum(1 for item in strategies[name] if item.get("success") is True)
                / max(len(strategies[name]), 1),
                name,
            ),
        )
        return {
            "observations": len(entries),
            "successful_policies": len(successful),
            "failed_policies": len(entries) - len(successful),
            "average_success_rate": round(len(successful) / max(len(entries), 1), 4),
            "average_search_cost": round(
                sum(_number(item.get("search_cost")) for item in entries)
                / max(len(entries), 1),
                4,
            ),
            "best_strategy": ranked[0] if ranked else None,
            "best_search_budgets": [
                item.get("search_budget") for item in successful[-5:]
            ],
            "policy_confidence": round(min(0.95, 0.45 + len(entries) * 0.05), 4),
        }

    def remember(self, report: Mapping[str, Any]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.load()
        entries = list(payload.get("policies", []))
        effectiveness = report.get("policy_effectiveness", {})
        entries.append({
            "task_type": report.get("task_complexity", {}).get("task_type"),
            "difficulty_level": report.get("task_complexity", {}).get("difficulty_level"),
            "strategy": report.get("selected_strategy"),
            "search_budget": report.get("search_budget"),
            "success": effectiveness.get("validation_success") is True,
            "success_rate": effectiveness.get("success_rate", 0.0),
            "search_cost": effectiveness.get("search_cost", 0.0),
            "policy_confidence": report.get("policy_confidence", 0.0),
        })
        payload["policies"] = entries[-200:]
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return {
            "persistent_policy_memory": True,
            "memory_path": str(self.path),
            "entries_stored": len(payload["policies"]),
        }


class AdaptiveSearchPolicyEngine:
    """Choose search shape; never generate solutions or execute transformations."""

    system_name = "adaptive_search_policy_engine"

    def __init__(
        self,
        memory: AdaptiveSearchPolicyMemory | None = None,
        persist_memory: bool = True,
    ) -> None:
        self.memory = memory or AdaptiveSearchPolicyMemory()
        self.persist_memory = persist_memory

    def plan(
        self,
        task_analysis: Any = None,
        routes: list[Any] | None = None,
        performance_report: Mapping[str, Any] | None = None,
        search_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        started = perf_counter()
        features = self._features(task_analysis)
        score = self._complexity_score(features)
        level, route_range = self._level(score)
        task_type = self._task_type(features)
        memory = self.memory.summary(task_type)
        strategy, strategy_reason = self._strategy(features, score, memory)
        budget = self._budget(score, route_range, features)
        decisions, timeline = self._adapt(routes or [], budget)
        route_count = len(routes or [])
        effectiveness = self._effectiveness(
            routes or [], performance_report or {}, search_report or {}
        )
        changes = [
            item for item in decisions
            if item["decision"] in {
                "Increase Budget", "Reduce Budget", "Increase Exploration",
                "Increase Validation", "Switch Strategy",
            }
        ]
        elapsed = max(perf_counter() - started, 0.0)
        expected_runtime = max(
            _number((performance_report or {}).get("search_time_seconds")),
            _number((performance_report or {}).get("reasoning_time_seconds")),
            _number((performance_report or {}).get("execution_time")),
            _number((performance_report or {}).get("total_runtime_seconds")),
            features["expected_runtime"],
        )
        report = {
            "system": self.system_name,
            "ADAPTIVE_SEARCH_POLICY_REPORT": True,
            "task_complexity": {
                **features,
                "complexity_score": score,
                "difficulty_level": level,
                "task_type": task_type,
                "expected_runtime": round(expected_runtime, 4),
                "expected_search_cost": round(score * budget["maximum_search_routes"], 4),
            },
            "selected_strategy": strategy,
            "strategy_selection_reason": strategy_reason,
            "search_budget": budget,
            "search_budget_reason": (
                f"{level} complexity ({score:.4f}) maps to "
                f"{route_range[0]}-{route_range[1]} routes; allocation is capped "
                "to avoid unsupported expansion."
            ),
            "policy_decisions": decisions,
            "strategy_changes": [
                item for item in changes if item["decision"] == "Switch Strategy"
            ],
            "budget_changes": [
                item for item in changes if "Budget" in item["decision"]
            ],
            "route_allocation": {
                "recommended_routes": budget["maximum_search_routes"],
                "observed_routes": route_count,
                "allocation_status": (
                    "WITHIN_BUDGET" if route_count <= budget["maximum_search_routes"]
                    else "OVER_BUDGET"
                ),
                "reason": (
                    "Observed routes fit the complexity-derived allocation."
                    if route_count <= budget["maximum_search_routes"]
                    else "Observed routes exceed policy allocation; reduce branching."
                ),
            },
            "search_adaptation_timeline": timeline,
            "policy_confidence": self._policy_confidence(features, memory),
            "policy_effectiveness": effectiveness,
            "recommended_future_policy": self._future_policy(
                strategy, effectiveness, memory
            ),
            "policy_memory": memory,
            "policy_overhead_seconds": round(elapsed, 9),
            "policy_overhead_below_2_percent": (
                elapsed / max(expected_runtime, 0.001) < 0.02
            ),
            "runtime_alignment": {
                "does_not_solve_tasks": True,
                "search_runtime_redesigned": False,
                "solver_redesigned": False,
                "runtime_registry_redesigned": False,
                "deterministic_policy": True,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        report["policy_memory_update"] = (
            self.memory.remember(report)
            if self.persist_memory and routes
            else {"persistent_policy_memory": False, "reason": "no_completed_routes"}
        )
        return report

    def apply_budget(self, reasoning_budget: Any, report: Mapping[str, Any]) -> Any:
        """Apply compatible limits to the existing reasoning budget in-place."""
        budget = report.get("search_budget", {})
        if reasoning_budget is None or not isinstance(budget, Mapping):
            return reasoning_budget
        if int(getattr(reasoning_budget, "max_active_routes", 1) or 0) <= 0:
            notes = getattr(reasoning_budget, "notes", None)
            if isinstance(notes, list):
                notes.append("adaptive_search_policy_blocked_by_execution_authority")
            return reasoning_budget
        reasoning_budget.max_active_routes = int(budget["maximum_search_routes"])
        reasoning_budget.max_reasoning_depth = min(
            int(budget["maximum_branch_depth"]),
            max(1, int(getattr(reasoning_budget, "max_reasoning_depth", 1))),
        )
        reasoning_budget.max_hypotheses = min(
            int(budget["maximum_candidate_programs"]),
            max(1, int(getattr(reasoning_budget, "max_hypotheses", 1))),
        )
        notes = getattr(reasoning_budget, "notes", None)
        if isinstance(notes, list):
            notes.append("adaptive_search_policy_applied")
        return reasoning_budget

    def _features(self, analysis):
        if is_dataclass(analysis):
            data = asdict(analysis)
        elif isinstance(analysis, Mapping):
            data = dict(analysis)
        else:
            data = {}
        grid_size = _number(data.get("grid_size") or data.get("total_cells"))
        object_count = _number(data.get("object_count"))
        transformations = _number(
            data.get("transformation_count") or data.get("transformation_complexity")
        )
        concepts = data.get("target_concepts") or data.get("concepts") or []
        required = data.get("required_capabilities") or []
        historical = _clamp(data.get("historical_similarity"))
        uncertainty = _clamp(data.get("uncertainty", 1.0 - historical))
        return {
            "grid_size": round(grid_size, 4),
            "object_count": int(object_count),
            "object_diversity": round(_clamp(data.get("object_diversity", object_count / 8)), 4),
            "color_diversity": round(_clamp(data.get("color_diversity")), 4),
            "spatial_complexity": round(_clamp(data.get("spatial_complexity")), 4),
            "topological_complexity": round(_clamp(
                data.get("topological_complexity", data.get("process_complexity"))
            ), 4),
            "transformation_complexity": round(_clamp(transformations / 6), 4),
            "context_complexity": round(_clamp(
                data.get("context_complexity", len(required) / 10)
            ), 4),
            "novelty": round(1.0 - historical, 4),
            "expected_search_difficulty": round(_clamp(
                data.get("estimated_cost", uncertainty)
            ), 4),
            "concepts": sorted(str(item).lower() for item in concepts),
            "expected_runtime": round(max(0.001, _number(data.get("estimated_cost")) * 0.1), 4),
        }

    def _complexity_score(self, f):
        grid = _clamp(f["grid_size"] / 400)
        objects = _clamp(f["object_count"] / 12)
        weighted = (
            grid * 0.08 + objects * 0.10 + f["object_diversity"] * 0.08
            + f["color_diversity"] * 0.07 + f["spatial_complexity"] * 0.12
            + f["topological_complexity"] * 0.12
            + f["transformation_complexity"] * 0.16
            + f["context_complexity"] * 0.09 + f["novelty"] * 0.09
            + f["expected_search_difficulty"] * 0.09
        )
        return round(_clamp(weighted), 4)

    def _level(self, score):
        for level, ceiling, route_range in LEVELS:
            if score < ceiling:
                return level, route_range
        return LEVELS[-1][0], LEVELS[-1][2]

    def _task_type(self, f):
        concepts = " ".join(f["concepts"])
        for token in ("topology", "spatial", "color", "object", "pattern", "program"):
            if token in concepts:
                return token
        return "transformation" if f["transformation_complexity"] >= 0.35 else "general"

    def _strategy(self, f, score, memory):
        if memory.get("observations", 0) >= 3 and memory.get("policy_confidence", 0) >= 0.6:
            return memory["best_strategy"], "Historical policy memory has sufficient confidence for this task type."
        task_type = self._task_type(f)
        mapping = {
            "topology": "Topology-First",
            "spatial": "Spatial-First",
            "color": "Color-First",
            "object": "Object-First",
            "pattern": "Pattern-First",
            "program": "Program-First",
            "transformation": "Transformation-First",
        }
        if f["novelty"] > 0.75 and score >= 0.55:
            return "Aggressive Exploration", "High novelty and complexity require broader evidence collection."
        if task_type in mapping:
            return mapping[task_type], f"{task_type.title()} signals dominate the task analysis."
        if score < 0.25:
            return "Conservative Search", "Low complexity favors minimal branching and early validation."
        if score > 0.70:
            return "Hybrid Strategy", "Multiple high-complexity signals require mixed search operators."
        return "Balanced Exploration", "No single feature dominates; exploitation and exploration remain balanced."

    def _budget(self, score, route_range, f):
        low, high = route_range
        routes = low + int(round((high - low) * score))
        if score >= 0.85:
            routes = low  # begin bounded; online evidence may authorize expansion
        return {
            "maximum_search_routes": max(1, routes),
            "maximum_branch_depth": max(1, 1 + int(round(score * 7))),
            "maximum_branch_width": max(1, 1 + int(round(score * 5))),
            "maximum_candidate_programs": max(1, 2 + int(round(score * 18))),
            "maximum_transformations": max(1, 2 + int(round(score * 14))),
            "maximum_validation_attempts": max(1, 1 + int(round(score * 7))),
            "maximum_runtime_budget": round(0.05 + score * 1.95, 4),
            "adaptive_expansion_enabled": score >= 0.85,
        }

    def _adapt(self, routes, budget):
        decisions, timeline = [], []
        previous_evidence = None
        failures = 0
        for index, route in enumerate(routes):
            scores = getattr(route, "scores", {}) or {}
            confidence = _clamp(getattr(route, "current_confidence", 0.0))
            evidence = _clamp(getattr(route, "evidence_score", 0.0))
            cost = _clamp(getattr(route, "estimated_computational_cost", 0.0))
            info = _clamp(scores.get("information_gain", getattr(route, "expected_information_gain", 0.0)))
            validation = str(getattr(route, "validation_status", "unknown"))
            failures += int(validation == "failed")
            gain = evidence - previous_evidence if previous_evidence is not None else evidence
            if validation == "validated":
                decision, reason = "Terminate Search", "A candidate passed validation."
            elif cost > 0.75 and evidence < 0.4:
                decision, reason = "Reduce Budget", "Search cost is rising without proportional evidence."
            elif failures >= 2:
                decision, reason = "Switch Strategy", "Repeated validation failures require a different search bias."
            elif confidence < 0.25 and info > 0.35:
                decision, reason = "Reactivate Routes", "Confidence collapsed while suspended routes retain information value."
            elif gain > 0.20:
                decision, reason = "Freeze Route", "Evidence is growing rapidly; preserve this route for exploitation."
            elif previous_evidence is not None and gain <= 0.02:
                decision, reason = "Increase Exploration", "Evidence gain stagnated across consecutive route observations."
            elif info > 0.45:
                decision, reason = "Split Route", "High information gain justifies testing distinct branches."
            elif confidence > 0.70:
                decision, reason = "Increase Validation", "High-confidence evidence should be validated before expansion."
            else:
                decision, reason = "Expand Route", "Expected information gain remains proportionate to search cost."
            item = {
                "sequence": index + 1,
                "route_id": getattr(route, "route_id", f"route:{index}"),
                "decision": decision,
                "reason": reason,
                "features": {
                    "confidence": confidence,
                    "evidence_strength": evidence,
                    "novelty": _clamp(scores.get("novelty_score")),
                    "historical_success": 0.0,
                    "transformation_diversity": len(getattr(route, "visited_transformations", [])),
                    "program_diversity": len(getattr(route, "visited_programs", [])),
                    "search_cost": cost,
                    "expected_information_gain": info,
                    "generalization_potential": _clamp(scores.get("generalization_potential")),
                },
            }
            decisions.append(item)
            timeline.append({
                "sequence": index + 1,
                "event": decision,
                "route_id": item["route_id"],
                "reason": reason,
            })
            previous_evidence = evidence
        if not decisions:
            decisions.append({
                "sequence": 0,
                "route_id": None,
                "decision": "Limit Routes",
                "reason": "Pre-search allocation limits routes to the complexity-derived budget.",
                "features": {},
            })
        return decisions, timeline

    def _effectiveness(self, routes, performance, search_report):
        validated = sum(
            1 for route in routes
            if str(getattr(route, "validation_status", "")) == "validated"
        )
        search_cost = search_report.get("search_cost", {})
        canonical_cost = (
            _number(search_cost.get("total_search_cost"))
            if isinstance(search_cost, Mapping)
            else _number(search_cost)
        )
        cost = max(
            canonical_cost,
            sum(_number(getattr(route, "estimated_computational_cost", 0.0)) for route in routes),
        )
        return {
            "validation_success": validated > 0,
            "success_rate": round(validated / max(len(routes), 1), 4),
            "search_cost": round(cost, 4),
            "routes_evaluated": len(routes),
            "evidence_per_cost": round(
                sum(_number(getattr(route, "evidence_score", 0.0)) for route in routes)
                / max(cost, 0.000001),
                4,
            ) if routes else 0.0,
        }

    def _policy_confidence(self, f, memory):
        feature_coverage = sum(
            1 for key in (
                "object_count", "spatial_complexity", "topological_complexity",
                "transformation_complexity", "context_complexity", "novelty",
            )
            if _number(f.get(key)) > 0.0
        ) / 6
        return round(_clamp(0.45 + feature_coverage * 0.35 + memory.get("policy_confidence", 0) * 0.2), 4)

    def _future_policy(self, strategy, effectiveness, memory):
        if effectiveness["validation_success"]:
            return f"Retain {strategy} and reuse its budget for this task type."
        if effectiveness["search_cost"] > 0.75:
            return "Use Conservative Search with reduced branch width and earlier validation."
        if memory.get("best_strategy"):
            return f"Compare {strategy} against historical {memory['best_strategy']}."
        return "Increase exploration modestly, then validate the first evidence-bearing routes."


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: Any) -> float:
    return max(0.0, min(1.0, _number(value)))


adaptive_search_policy_engine = AdaptiveSearchPolicyEngine()


__all__ = [
    "AdaptiveSearchPolicyEngine",
    "AdaptiveSearchPolicyMemory",
    "adaptive_search_policy_engine",
]
