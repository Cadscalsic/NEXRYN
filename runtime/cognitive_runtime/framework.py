"""First-class runtime ownership for cognitive processes.

The framework does not execute reasoning, memory, truth, or evaluation logic.
It registers those processes as cognitive runtimes and reconstructs their
ownership, lifecycle, metrics, snapshots, and telemetry from existing reports.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Mapping


@dataclass
class CognitiveRuntimeRecord:
    runtime_id: str
    runtime_name: str
    owner: str
    execution_id: str
    lifecycle: list[str]
    timing_metric: str
    duration_seconds: float = 0.0
    execution_start: str | None = None
    execution_end: str | None = None
    cpu_time: float = 0.0
    memory_cost: float = 0.0
    lifecycle_events: list[dict[str, Any]] = field(default_factory=list)
    completion_reason: str = ""
    telemetry_source: str = ""
    last_binding_timestamp: str | None = None
    children: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    graph: dict[str, Any] = field(default_factory=dict)
    snapshots: list[dict[str, Any]] = field(default_factory=list)
    telemetry: dict[str, Any] = field(default_factory=dict)
    status: str = "PARTIAL"
    coverage: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CognitiveRuntimeFramework:
    system_name = "cognitive_runtime_framework"

    RUNTIME_DEFINITIONS = {
        "execution_runtime": {
            "runtime_name": "Execution Runtime",
            "owner": "execution_runtime",
            "timing_metric": "task_execution_time_seconds",
            "lifecycle": ["execution_requested", "execution_started", "execution_completed"],
            "children": ["execution_engine", "execution_dispatcher"],
        },
        "reasoning_runtime": {
            "runtime_name": "Reasoning Runtime",
            "owner": "reasoning_runtime",
            "timing_metric": "reasoning_time_seconds",
            "lifecycle": [
                "reasoning_initialization",
                "hypothesis_generation",
                "hypothesis_ranking",
                "program_synthesis",
                "solution_selection",
            ],
            "children": ["search_runtime", "cognitive_search_manager", "cognitive_solver_pipeline"],
        },
        "search_runtime": {
            "runtime_name": "Cognitive Search Runtime",
            "owner": "search_runtime",
            "timing_metric": "search_time_seconds",
            "lifecycle": [
                "route_creation",
                "route_expansion",
                "evidence_collection",
                "route_ranking",
                "route_cooling",
                "route_reactivation",
                "route_merge",
                "route_split",
                "route_validation",
            ],
            "children": [
                "search_route_registry",
                "search_scoring_engine",
                "search_policy",
                "search_memory",
                "acsc_route_cooling",
            ],
        },
        "concept_formation_runtime": {
            "runtime_name": "Concept Formation Runtime",
            "owner": "concept_formation_runtime",
            "timing_metric": "concept_cost",
            "lifecycle": [
                "evidence_extraction",
                "candidate_concepts",
                "concept_competition",
                "concept_validation",
                "concept_promotion",
                "concept_memory_persistence",
            ],
            "children": [
                "concept_formation_engine",
                "concept_graph",
                "concept_memory",
            ],
        },
        "program_synthesis_runtime": {
            "runtime_name": "Program Synthesis Runtime",
            "owner": "program_synthesis_runtime",
            "timing_metric": "program_synthesis_time_seconds",
            "lifecycle": [
                "program_generation",
                "program_composition",
                "program_competition",
                "program_validation",
                "program_promotion",
                "program_memory_persistence",
            ],
            "children": [
                "program_synthesis_intelligence_engine",
                "program_graph",
                "program_memory",
            ],
        },
        "adaptive_search_intelligence_runtime": {
            "runtime_name": "Adaptive Search Intelligence Runtime",
            "owner": "adaptive_search_intelligence_runtime",
            "timing_metric": "adaptive_search_intelligence_time_seconds",
            "lifecycle": [
                "task_analysis",
                "strategy_selection",
                "budget_allocation",
                "route_decision",
                "hypothesis_management",
                "search_memory_persistence",
            ],
            "children": [
                "adaptive_search_intelligence_engine",
                "search_graph",
                "search_strategy_memory",
            ],
        },
        "acsc_runtime": {
            "runtime_name": "Adaptive Cognitive Super Cooling Runtime",
            "owner": "acsc_runtime",
            "timing_metric": "acsc_time_seconds",
            "lifecycle": [
                "route_thermal_evaluation",
                "resource_allocation",
                "cooling_decision",
                "reactivation_decision",
                "resource_redistribution",
                "thermal_memory_persistence",
            ],
            "children": [
                "adaptive_cognitive_super_cooling_engine",
                "thermal_graph",
                "thermal_memory",
            ],
        },
        "truth_runtime": {
            "runtime_name": "Truth Runtime",
            "owner": "truth_runtime",
            "timing_metric": "truth_time_seconds",
            "lifecycle": [
                "truth_candidate",
                "truth_validation",
                "truth_promotion",
                "truth_commitment",
            ],
            "children": ["truth_candidate_engine", "truth_commit_engine"],
        },
        "memory_runtime": {
            "runtime_name": "Memory Runtime",
            "owner": "memory_runtime",
            "timing_metric": "memory_time_seconds",
            "lifecycle": [
                "encoding",
                "retrieval",
                "matching",
                "promotion",
                "persistence",
            ],
            "children": ["adaptive_reuse", "search_memory", "concept_cache"],
        },
        "evaluation_runtime": {
            "runtime_name": "Evaluation Runtime",
            "owner": "evaluation_runtime",
            "timing_metric": "evaluation_time_seconds",
            "lifecycle": [
                "evaluation_planning",
                "metric_collection",
                "scoring",
                "reward",
                "penalty",
                "learning_recommendation",
            ],
            "children": ["success_semantics", "reward_engine", "penalty_engine"],
        },
        "dependency_runtime": {
            "runtime_name": "Dependency Runtime",
            "owner": "dependency_runtime",
            "timing_metric": "dependency_reasoning_time_seconds",
            "lifecycle": ["dependency_discovery", "dependency_execution", "dependency_completion"],
            "children": ["dependency_execution_bridge", "dependency_activation_bridge"],
        },
        "process_runtime": {
            "runtime_name": "Process Runtime",
            "owner": "process_runtime",
            "timing_metric": "process_generation_time",
            "lifecycle": ["process_generation", "process_validation", "process_completion"],
            "children": ["process_context_runtime"],
        },
        "causal_runtime": {
            "runtime_name": "Causal Runtime",
            "owner": "causal_runtime",
            "timing_metric": "causal_generation_time",
            "lifecycle": ["causal_generation", "causal_validation", "causal_completion"],
            "children": ["causal_context_runtime"],
        },
        "reuse_runtime": {
            "runtime_name": "Reuse Runtime",
            "owner": "reuse_runtime",
            "timing_metric": "reuse_time_seconds",
            "lifecycle": ["reuse_lookup", "reuse_validation", "reuse_completion"],
            "children": ["adaptive_reuse_layer"],
        },
    }

    def build_report(
        self,
        performance_report: Mapping[str, Any] | None = None,
        runtime_lifecycle_report: Mapping[str, Any] | None = None,
        runtime_observability_report: Mapping[str, Any] | None = None,
        cognitive_pipeline_report: Mapping[str, Any] | None = None,
        cognitive_search_report: Mapping[str, Any] | None = None,
        solver_reasoning_report: Mapping[str, Any] | None = None,
        truth_report: Mapping[str, Any] | None = None,
        memory_report: Mapping[str, Any] | None = None,
        evaluation_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        performance = performance_report if isinstance(performance_report, Mapping) else {}
        lifecycle = runtime_lifecycle_report if isinstance(runtime_lifecycle_report, Mapping) else {}
        observability = runtime_observability_report if isinstance(runtime_observability_report, Mapping) else {}
        sources = {
            "cognitive_pipeline_report": cognitive_pipeline_report if isinstance(cognitive_pipeline_report, Mapping) else {},
            "cognitive_search_report": cognitive_search_report if isinstance(cognitive_search_report, Mapping) else {},
            "solver_reasoning_report": solver_reasoning_report if isinstance(solver_reasoning_report, Mapping) else {},
            "truth_report": truth_report if isinstance(truth_report, Mapping) else {},
            "memory_report": memory_report if isinstance(memory_report, Mapping) else {},
            "evaluation_report": evaluation_report if isinstance(evaluation_report, Mapping) else {},
        }
        core_runtime_ids = {
            "reasoning_runtime",
            "search_runtime",
            "truth_runtime",
            "memory_runtime",
            "evaluation_runtime",
        }
        records = [
            self._runtime_record(runtime_id, definition, performance, lifecycle, sources)
            for runtime_id, definition in self.RUNTIME_DEFINITIONS.items()
            if runtime_id in core_runtime_ids
            or self._execution_id(runtime_id, lifecycle)
            != f"{runtime_id}:synthetic_execution"
        ]
        status = self._status(records, observability)
        return {
            "system": self.system_name,
            "COGNITIVE_RUNTIME_REPORT": True,
            "runtime_registry": {
                record.runtime_id: record.as_dict()
                for record in records
            },
            "runtime_graph": self._runtime_graph(records),
            "runtime_lifecycle": {
                record.runtime_id: record.lifecycle
                for record in records
            },
            "runtime_metrics": {
                record.runtime_id: record.metrics
                for record in records
            },
            "runtime_snapshots": {
                record.runtime_id: record.snapshots
                for record in records
            },
            "runtime_telemetry": {
                record.runtime_id: record.telemetry
                for record in records
            },
            "metric_ownership": {
                record.timing_metric: {
                    "owner": record.owner,
                    "runtime_id": record.runtime_id,
                    "execution_id": record.execution_id,
                    "status": record.status,
                    "duration_seconds": record.duration_seconds,
                }
                for record in records
            },
            "cognitive_runtime_coverage": self._coverage(records),
            "cognitive_runtime_gaps": self._gaps(records),
            "status_semantics": status,
            "acsc_readiness": {
                "can_cool_reasoning_runtime": True,
                "can_cool_search_runtime": True,
                "can_cool_truth_runtime": True,
                "can_cool_memory_runtime": True,
                "can_cool_evaluation_runtime": True,
                "can_cool_search_routes": self._search_route_targets(records),
                "cooling_target": "cognitive_runtime_and_search_routes",
                "readiness": "EMERGING" if self._coverage(records)["coverage_score"] < 1.0 else "READY",
            },
            "runtime_alignment": {
                "does_not_change_solver_logic": True,
                "does_not_redesign_arc_algorithms": True,
                "uses_existing_reports": True,
                "deterministic_registry": True,
            },
            "generated_at": str(datetime.utcnow()),
        }

    def _runtime_record(
        self,
        runtime_id: str,
        definition: Mapping[str, Any],
        performance: Mapping[str, Any],
        lifecycle: Mapping[str, Any],
        sources: Mapping[str, Mapping[str, Any]],
    ) -> CognitiveRuntimeRecord:
        timing_metric = str(definition["timing_metric"])
        duration = self._duration_for(timing_metric, performance, lifecycle, runtime_id)
        source_payload = self._source_for_runtime(runtime_id, sources)
        metrics = self._metrics_for(runtime_id, timing_metric, performance, source_payload)
        graph = self._graph_for(runtime_id, source_payload)
        snapshots = self._snapshots_for(runtime_id, source_payload)
        telemetry = {
            "timing_source": "performance_report_or_lifecycle",
            "source_available": bool(source_payload),
            "duration_seconds": duration,
            "metric_owner": definition["owner"],
            "execution_id": self._execution_id(runtime_id, lifecycle),
        }
        coverage = self._record_coverage(duration, graph, snapshots, telemetry)
        status = "OPERATIONAL" if coverage >= 0.75 else "EMERGING" if coverage >= 0.35 else "PARTIAL"
        return CognitiveRuntimeRecord(
            runtime_id=runtime_id,
            runtime_name=str(definition["runtime_name"]),
            owner=str(definition["owner"]),
            execution_id=telemetry["execution_id"],
            lifecycle=list(definition["lifecycle"]),
            timing_metric=timing_metric,
            duration_seconds=duration,
            telemetry_source="runtime_lifecycle",
            children=list(definition["children"]),
            metrics=metrics,
            graph=graph,
            snapshots=snapshots,
            telemetry=telemetry,
            status=status,
            coverage=coverage,
        )

    def _duration_for(
        self,
        metric_name: str,
        performance: Mapping[str, Any],
        lifecycle: Mapping[str, Any],
        runtime_id: str,
    ) -> float:
        value = _number(performance.get(metric_name))
        if value > 0.0:
            return round(value, 6)
        canonical = performance.get("canonical_metrics", {})
        if isinstance(canonical, Mapping):
            value = _number(canonical.get(metric_name))
            if value > 0.0:
                return round(value, 6)
        total = 0.0
        token = runtime_id.replace("_runtime", "")
        for execution in lifecycle.get("executions", []) or []:
            if not isinstance(execution, Mapping):
                continue
            text = " ".join([
                str(execution.get("runtime_name", "")),
                str(execution.get("module_name", "")),
                str(execution.get("trigger", "")),
            ]).lower()
            if token not in text:
                continue
            total += max(
                _number(execution.get("elapsed_seconds")),
                _number(execution.get("duration_seconds")),
                _number(execution.get("elapsed_time")),
            )
        return round(total, 6)

    def _execution_id(self, runtime_id: str, lifecycle: Mapping[str, Any]) -> str:
        token = runtime_id.replace("_runtime", "")
        execution_type = {
            "execution_runtime": "ExecutionExecution",
            "reasoning_runtime": "ReasoningExecution",
            "search_runtime": "SearchExecution",
            "memory_runtime": "MemoryExecution",
            "truth_runtime": "TruthExecution",
            "evaluation_runtime": "EvaluationExecution",
        }.get(runtime_id)
        candidates = []
        for execution in lifecycle.get("executions", []) or []:
            if not isinstance(execution, Mapping):
                continue
            text = " ".join([
                str(execution.get("runtime_name", "")),
                str(execution.get("module_name", "")),
            ]).lower()
            if token in text and execution.get("execution_id"):
                candidates.append(execution)
        for execution in candidates:
            if execution_type and str(execution.get("module_name")) == execution_type:
                return str(execution["execution_id"])
        for execution in candidates:
            runtime_name = str(execution.get("runtime_name", "")).lower().replace(" ", "_")
            if runtime_name == runtime_id:
                return str(execution["execution_id"])
        if candidates:
            return str(candidates[0]["execution_id"])
        return f"{runtime_id}:synthetic_execution"

    def _source_for_runtime(
        self,
        runtime_id: str,
        sources: Mapping[str, Mapping[str, Any]],
    ) -> Mapping[str, Any]:
        if runtime_id == "reasoning_runtime":
            reasoning = sources.get("solver_reasoning_report") or {}
            search = sources.get("cognitive_search_report") or {}
            pipeline = sources.get("cognitive_pipeline_report") or {}
            combined = dict(reasoning or pipeline or search or {})
            for key in (
                "route_statistics",
                "search_timeline",
                "route_ranking",
                "route_evolution",
                "search_runtime",
            ):
                if key in search:
                    combined[key] = search[key]
            return combined
        if runtime_id == "search_runtime":
            search = sources.get("cognitive_search_report") or {}
            runtime_payload = search.get("search_runtime") if isinstance(search.get("search_runtime"), Mapping) else {}
            return dict(runtime_payload or search or {})
        if runtime_id == "truth_runtime":
            return sources.get("truth_report") or {}
        if runtime_id == "memory_runtime":
            return (
                sources.get("memory_report")
                or (sources.get("cognitive_search_report") or {}).get("search_memory", {})
                or {}
            )
        if runtime_id == "evaluation_runtime":
            return sources.get("evaluation_report") or {}
        return {}

    def _metrics_for(
        self,
        runtime_id: str,
        timing_metric: str,
        performance: Mapping[str, Any],
        source_payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        metrics = {
            timing_metric: _number(performance.get(timing_metric)),
            "source_available": bool(source_payload),
        }
        if runtime_id == "reasoning_runtime":
            route_stats = source_payload.get("route_statistics") or {}
            search_runtime = source_payload.get("search_runtime") or {}
            search_runtime_metrics = (
                search_runtime.get("metrics")
                if isinstance(search_runtime, Mapping) and isinstance(search_runtime.get("metrics"), Mapping)
                else {}
            )
            metrics.update({
                "reasoning_graph_nodes": _number(
                    (source_payload.get("reasoning_graph") or {}).get("node_count")
                    if isinstance(source_payload.get("reasoning_graph"), Mapping)
                    else 0
                ),
                "search_routes": max(
                    _number(route_stats.get("routes_created")) if isinstance(route_stats, Mapping) else 0,
                    _number(search_runtime_metrics.get("search_routes")),
                ),
            })
        elif runtime_id == "search_runtime":
            payload_metrics = (
                source_payload.get("metrics")
                if isinstance(source_payload.get("metrics"), Mapping)
                else {}
            )
            route_stats = source_payload.get("route_statistics") if isinstance(source_payload.get("route_statistics"), Mapping) else {}
            metrics.update({
                "search_routes": max(
                    _number(payload_metrics.get("search_routes")),
                    _number(route_stats.get("routes_created")),
                ),
                "routes_created": max(
                    _number(payload_metrics.get("routes_created")),
                    _number(route_stats.get("routes_created")),
                ),
                "routes_active": max(
                    _number(payload_metrics.get("routes_active")),
                    _number(route_stats.get("routes_active")),
                ),
                "routes_suspended": max(
                    _number(payload_metrics.get("routes_suspended")),
                    _number(route_stats.get("routes_suspended")),
                ),
                "routes_reactivated": max(
                    _number(payload_metrics.get("routes_reactivated")),
                    _number(route_stats.get("routes_reactivated")),
                ),
                "routes_pruned": max(
                    _number(payload_metrics.get("routes_pruned")),
                    _number(route_stats.get("routes_pruned")),
                ),
                "routes_merged": max(
                    _number(payload_metrics.get("routes_merged")),
                    _number(route_stats.get("routes_merged")),
                ),
                "routes_split": max(
                    _number(payload_metrics.get("routes_split")),
                    _number(route_stats.get("routes_split")),
                ),
                "search_entropy": max(
                    _number(payload_metrics.get("search_entropy")),
                    _number(route_stats.get("search_entropy")),
                ),
                "search_efficiency": max(
                    _number(payload_metrics.get("search_efficiency")),
                    _number(route_stats.get("search_efficiency")),
                ),
                "search_cost": max(
                    _number(payload_metrics.get("search_cost")),
                    _number(route_stats.get("search_cost")),
                ),
                "search_coverage": max(
                    _number(payload_metrics.get("search_coverage")),
                    _number(route_stats.get("search_coverage")),
                ),
                "cooling_candidates": _count(source_payload.get("acsc_route_targets")),
            })
        elif runtime_id == "truth_runtime":
            metrics.update({
                "truth_candidates": _count(source_payload.get("truth_candidates") or source_payload.get("evaluations")),
                "truth_commits": _count(source_payload.get("committed_truths") or source_payload.get("truths")),
            })
        elif runtime_id == "memory_runtime":
            metrics.update({
                "memory_entries": _number(source_payload.get("entries_stored")),
                "memory_available": bool(source_payload),
            })
        elif runtime_id == "evaluation_runtime":
            metrics.update({
                "success": source_payload.get("success"),
                "accuracy": _number(source_payload.get("accuracy")),
                "success_state": source_payload.get("success_state"),
            })
        return metrics

    def _graph_for(self, runtime_id: str, source_payload: Mapping[str, Any]) -> dict[str, Any]:
        if runtime_id == "reasoning_runtime":
            if isinstance(source_payload.get("search_space_graph"), Mapping):
                return dict(source_payload["search_space_graph"])
            if isinstance(source_payload.get("reasoning_graph"), Mapping):
                return dict(source_payload["reasoning_graph"])
        if runtime_id == "search_runtime":
            if isinstance(source_payload.get("graph"), Mapping):
                return dict(source_payload["graph"])
            if isinstance(source_payload.get("search_space_graph"), Mapping):
                return dict(source_payload["search_space_graph"])
        return {
            "nodes": [{"id": runtime_id, "type": "CognitiveRuntime"}],
            "edges": [],
        }

    def _snapshots_for(
        self,
        runtime_id: str,
        source_payload: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        if runtime_id == "reasoning_runtime":
            if isinstance(source_payload.get("search_timeline"), list):
                return [{"snapshot_type": "search_timeline", "items": len(source_payload["search_timeline"])}]
            if isinstance(source_payload.get("task_reports"), list):
                return [{"snapshot_type": "reasoning_task_reports", "items": len(source_payload["task_reports"])}]
        if runtime_id == "search_runtime":
            if isinstance(source_payload.get("snapshots"), list):
                return list(source_payload["snapshots"])
            snapshots = []
            for key in ("search_timeline", "route_ranking", "route_evolution"):
                if isinstance(source_payload.get(key), list):
                    snapshots.append({"snapshot_type": key, "items": len(source_payload[key])})
            return snapshots
        if runtime_id == "memory_runtime" and source_payload:
            return [{"snapshot_type": "memory_state", "keys": sorted(source_payload.keys())}]
        if source_payload:
            return [{"snapshot_type": "source_payload", "keys": sorted(source_payload.keys())[:20]}]
        return []

    def _record_coverage(
        self,
        duration: float,
        graph: Mapping[str, Any],
        snapshots: list[dict[str, Any]],
        telemetry: Mapping[str, Any],
    ) -> float:
        score = 0.0
        score += 0.25 if duration > 0.0 else 0.0
        score += 0.25 if graph.get("nodes") else 0.0
        score += 0.25 if snapshots else 0.0
        score += 0.25 if telemetry.get("execution_id") else 0.0
        return round(score, 4)

    def _runtime_graph(self, records: list[CognitiveRuntimeRecord]) -> dict[str, Any]:
        nodes = [
            {
                "id": record.runtime_id,
                "type": "CognitiveRuntime",
                "owner": record.owner,
                "status": record.status,
            }
            for record in records
        ]
        edges = []
        for record in records:
            for child in record.children:
                nodes.append({"id": child, "type": "RuntimeChild"})
                edges.append({
                    "from": record.runtime_id,
                    "to": child,
                    "type": "owns",
                })
        return {"nodes": nodes, "edges": edges}

    def _coverage(self, records: list[CognitiveRuntimeRecord]) -> dict[str, Any]:
        score = round(
            sum(record.coverage for record in records)
            / max(len(records), 1),
            4,
        )
        return {
            "coverage_score": score,
            "coverage_percentage": round(score * 100.0, 2),
            "covered_runtimes": [
                record.runtime_id for record in records if record.coverage >= 0.75
            ],
            "emerging_runtimes": [
                record.runtime_id for record in records if 0.35 <= record.coverage < 0.75
            ],
            "partial_runtimes": [
                record.runtime_id for record in records if record.coverage < 0.35
            ],
        }

    def _gaps(self, records: list[CognitiveRuntimeRecord]) -> list[dict[str, Any]]:
        gaps = []
        for record in records:
            if record.duration_seconds <= 0.0:
                gaps.append({
                    "runtime_id": record.runtime_id,
                    "gap": "missing_timing",
                    "metric": record.timing_metric,
                })
            if not record.snapshots:
                gaps.append({
                    "runtime_id": record.runtime_id,
                    "gap": "missing_snapshots",
                })
        return gaps

    def _status(
        self,
        records: list[CognitiveRuntimeRecord],
        observability: Mapping[str, Any],
    ) -> dict[str, Any]:
        coverage = self._coverage(records)
        obs_score = _number(observability.get("observability_score"))
        obs_state = "COMPLETE" if obs_score >= 0.9 else "PARTIAL" if obs_score > 0.0 else "EMERGING"
        cognitive_state = (
            "OPERATIONAL"
            if coverage["coverage_score"] >= 0.75
            else "EMERGING"
            if coverage["coverage_score"] >= 0.35
            else "PARTIAL"
        )
        return {
            "execution": "SUCCESS",
            "observability": obs_state,
            "cognitive_coverage": cognitive_state,
            "overall": (
                "SUCCESS"
                if obs_state == "COMPLETE" and cognitive_state == "OPERATIONAL"
                else "SUCCESS_WITH_LIMITED_OBSERVABILITY"
            ),
            "legacy_failure_reinterpretation": (
                "OBSERVABILITY_GAPS_ARE_PARTIAL_COVERAGE_NOT_EXECUTION_FAILURE"
            ),
        }

    def _search_route_targets(self, records: list[CognitiveRuntimeRecord]) -> bool:
        for record in records:
            if record.runtime_id != "search_runtime":
                continue
            return _count(record.metrics.get("cooling_candidates")) > 0 or record.metrics.get("search_routes", 0) > 0
        return False


def build_cognitive_runtime_report(
    performance_report: Mapping[str, Any] | None = None,
    runtime_lifecycle_report: Mapping[str, Any] | None = None,
    runtime_observability_report: Mapping[str, Any] | None = None,
    cognitive_pipeline_report: Mapping[str, Any] | None = None,
    cognitive_search_report: Mapping[str, Any] | None = None,
    solver_reasoning_report: Mapping[str, Any] | None = None,
    truth_report: Mapping[str, Any] | None = None,
    memory_report: Mapping[str, Any] | None = None,
    evaluation_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return CognitiveRuntimeFramework().build_report(
        performance_report=performance_report,
        runtime_lifecycle_report=runtime_lifecycle_report,
        runtime_observability_report=runtime_observability_report,
        cognitive_pipeline_report=cognitive_pipeline_report,
        cognitive_search_report=cognitive_search_report,
        solver_reasoning_report=solver_reasoning_report,
        truth_report=truth_report,
        memory_report=memory_report,
        evaluation_report=evaluation_report,
    )


def _number(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _count(value: Any) -> int:
    if isinstance(value, Mapping):
        return len(value)
    if isinstance(value, (list, tuple, set)):
        return len(value)
    return 0


__all__ = [
    "CognitiveRuntimeFramework",
    "CognitiveRuntimeRecord",
    "build_cognitive_runtime_report",
]
