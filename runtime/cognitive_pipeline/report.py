"""COGNITIVE_PIPELINE_REPORT generation."""

from __future__ import annotations

from typing import Any

from .context import CognitiveContext
from .orchestrator import CognitivePipelineOrchestrator
from .stages import build_default_stages


def build_cognitive_pipeline_report(
    all_results: list[dict[str, Any]] | None = None,
    performance_report: dict[str, Any] | None = None,
    contexts: list[CognitiveContext] | None = None,
) -> dict[str, Any]:
    contexts = list(contexts or [])
    if not contexts:
        contexts = [_context_from_result(item) for item in (all_results or [])]
        orchestrator = CognitivePipelineOrchestrator()
        contexts = [orchestrator.execute(context) for context in contexts]
    stage_events = [event for context in contexts for event in context.stage_events]
    snapshots = [snapshot for context in contexts for snapshot in context.stage_snapshots]
    stage_stats = _stage_statistics(stage_events)
    bottlenecks = _bottlenecks(stage_events, snapshots)
    graph = _pipeline_graph()
    return {
        "COGNITIVE_PIPELINE_REPORT": True,
        "pipeline_graph": graph,
        "stage_timeline": stage_events,
        "pipeline_statistics": {
            "task_count": len(contexts),
            "stage_count": len(graph["nodes"]),
            "event_count": len(stage_events),
            "pipeline_depth": len(graph["nodes"]),
            "pipeline_width": 1,
            "stage_statistics": stage_stats,
            "total_duration": round(sum(event.get("duration", 0.0) for event in stage_events), 6),
            "total_cpu_cost": round(sum(event.get("cpu_cost", 0.0) for event in stage_events), 6),
            "total_memory_cost": sum(event.get("memory_cost", 0) for event in stage_events),
        },
        "context_evolution": [snapshot["context_snapshot"] for snapshot in snapshots],
        "concept_evolution": _evolution(snapshots, "concepts"),
        "hypothesis_evolution": _evolution(snapshots, "hypotheses"),
        "transformation_evolution": _evolution(snapshots, "transformations"),
        "program_evolution": _evolution(snapshots, "candidate_programs"),
        "validation_statistics": _validation_statistics(contexts),
        "pipeline_bottlenecks": bottlenecks,
        "optimization_candidates": bottlenecks,
        "execution_trace": [context.trace for context in contexts],
        "runtime_alignment": {
            "reuses_runtime": True,
            "reuses_lifecycle": True,
            "reuses_dependency_runtime": True,
            "reuses_process_runtime": True,
            "reuses_causal_runtime": True,
            "reuses_adaptive_reuse": True,
            "deterministic_orchestration": True,
            "instrumentation_overhead_budget": "below_3_percent_target",
        },
        "performance_report_bridge": dict(performance_report or {}),
    }


def _context_from_result(item: dict[str, Any]) -> CognitiveContext:
    result = item.get("result", item) if isinstance(item, dict) else {}
    if not isinstance(result, dict):
        result = {}
    return CognitiveContext(
        task=item.get("task") if isinstance(item, dict) else None,
        input_grid=result.get("input_grid", [[0]]),
        output_grid=result.get("output_grid"),
        rules=list(result.get("rules", [])),
        perceived_objects=list(result.get("input_object_summaries", [])),
        relationships=list(result.get("relationships", [])),
        hypotheses=list(result.get("ranked_hypotheses") or result.get("hypotheses", [])),
        transformations=list(result.get("transformations", [])),
        candidate_programs=([result["synthesized_program"]] if result.get("synthesized_program") else []),
        validation_results=([result["evaluation_result"]] if result.get("evaluation_result") else []),
        evidence=list(result.get("patterns", [])),
        metadata={"source": "execution_result"},
    )


def _pipeline_graph() -> dict[str, Any]:
    stages = build_default_stages()
    nodes = [
        {
            "stage_id": stage.spec.stage_id,
            "stage_name": stage.spec.stage_name,
            "required_inputs": list(stage.spec.required_inputs),
            "optional_inputs": list(stage.spec.optional_inputs),
            "generated_outputs": list(stage.spec.generated_outputs),
            "consumed_outputs": list(stage.spec.consumed_outputs),
            "dependent_stages": list(stage.spec.dependent_stages),
            "blocking_conditions": list(stage.spec.blocking_conditions),
        }
        for stage in stages
    ]
    edges = [
        {"from": stages[index].spec.stage_id, "to": stages[index + 1].spec.stage_id}
        for index in range(len(stages) - 1)
    ]
    return {"nodes": nodes, "edges": edges}


def _stage_statistics(events: list[dict[str, Any]]) -> dict[str, Any]:
    stats: dict[str, Any] = {}
    for event in events:
        stage_id = event["stage_id"]
        bucket = stats.setdefault(stage_id, {
            "runs": 0,
            "successes": 0,
            "failures": 0,
            "skips": 0,
            "total_duration": 0.0,
            "total_memory_cost": 0,
        })
        bucket["runs"] += 1
        bucket["successes"] += int(event.get("execution_status") == "completed")
        bucket["failures"] += int(event.get("execution_status") == "failed")
        bucket["skips"] += int(event.get("execution_status") == "skipped")
        bucket["total_duration"] += event.get("duration", 0.0)
        bucket["total_memory_cost"] += event.get("memory_cost", 0)
    for bucket in stats.values():
        runs = max(bucket["runs"], 1)
        bucket["stage_throughput"] = round(runs / max(bucket["total_duration"], 0.000001), 4)
        bucket["stage_success_rate"] = round(bucket["successes"] / runs, 4)
        bucket["stage_failure_rate"] = round(bucket["failures"] / runs, 4)
        bucket["stage_reuse_rate"] = 0.0
        bucket["total_duration"] = round(bucket["total_duration"], 6)
    return stats


def _bottlenecks(events: list[dict[str, Any]], snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    slowest = max(events, key=lambda event: event.get("duration", 0.0), default={})
    highest_memory = max(events, key=lambda event: event.get("memory_cost", 0), default={})
    largest_concept = max(snapshots, key=lambda snap: snap.get("context_growth", {}).get("concepts", 0), default={})
    largest_hypothesis = max(snapshots, key=lambda snap: snap.get("context_growth", {}).get("hypotheses", 0), default={})
    validation_events = [event for event in events if event.get("stage_id") == "candidate_validation"]
    expensive_validation = max(validation_events, key=lambda event: event.get("duration", 0.0), default={})
    skipped = [event for event in events if event.get("execution_status") == "skipped"]
    repeated = _most_frequent(events)
    return {
        "slowest_stage": _stage_ref(slowest),
        "highest_memory_stage": _stage_ref(highest_memory),
        "largest_concept_growth": _snapshot_ref(largest_concept),
        "largest_hypothesis_explosion": _snapshot_ref(largest_hypothesis),
        "most_expensive_validation": _stage_ref(expensive_validation),
        "highest_reuse_opportunity": _stage_ref(slowest),
        "most_frequently_skipped_stage": _stage_ref(_most_frequent(skipped)),
        "most_frequently_repeated_stage": _stage_ref(repeated),
    }


def _stage_ref(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage_id": event.get("stage_id"),
        "stage_name": event.get("stage_name"),
        "duration": round(event.get("duration", 0.0), 6),
        "memory_cost": event.get("memory_cost", 0),
    }


def _snapshot_ref(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage_id": snapshot.get("stage_id"),
        "stage_name": snapshot.get("stage_name"),
        "growth": dict(snapshot.get("context_growth", {})),
    }


def _most_frequent(events: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    by_id: dict[str, dict[str, Any]] = {}
    for event in events:
        stage_id = event.get("stage_id")
        counts[stage_id] = counts.get(stage_id, 0) + 1
        by_id[stage_id] = event
    if not counts:
        return {}
    return by_id[max(counts, key=counts.get)]


def _evolution(snapshots: list[dict[str, Any]], key: str) -> list[int]:
    return [snapshot.get("context_snapshot", {}).get(key, 0) for snapshot in snapshots]


def _validation_statistics(contexts: list[CognitiveContext]) -> dict[str, Any]:
    validations = [item for context in contexts for item in context.validation_results]
    successes = sum(1 for item in validations if isinstance(item, dict) and item.get("success") is True)
    failures = sum(1 for item in validations if isinstance(item, dict) and item.get("success") is False)
    return {
        "validation_count": len(validations),
        "validation_successes": successes,
        "validation_failures": failures,
        "validation_success_rate": round(successes / max(successes + failures, 1), 4),
    }


__all__ = ["build_cognitive_pipeline_report"]
