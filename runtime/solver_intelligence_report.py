"""Solver execution graph and intelligence report synthesis."""

from __future__ import annotations

from collections import Counter
from sys import getsizeof
from typing import Any, Mapping


SOLVER_STAGE_MODEL = [
    ("perception", "Perception"),
    ("object_extraction", "ObjectDetection"),
    ("feature_analysis", "FeatureAnalysis"),
    ("pattern_analysis", "PatternAnalysis"),
    ("spatial_analysis", "SpatialAnalysis"),
    ("color_analysis", "ColorAnalysis"),
    ("topology_analysis", "TopologyAnalysis"),
    ("dependency_analysis", "DependencyAnalysis"),
    ("causal_analysis", "CausalAnalysis"),
    ("hypothesis_generation", "HypothesisGeneration"),
    ("transformation_discovery", "TransformationSearch"),
    ("candidate_program_generation", "ProgramSynthesis"),
    ("candidate_ranking", "ProgramRanking"),
    ("program_validation", "ProgramValidation"),
    ("solution_selection", "SolutionSelection"),
    ("final_output", "SolutionSelection"),
]


def build_report(
    *,
    all_results: list[Mapping[str, Any]] | None = None,
    performance_report: Mapping[str, Any] | None = None,
    cognitive_capability_report: Mapping[str, Any] | None = None,
    runtime_lifecycle_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a non-invasive solver observability report from existing context."""

    all_results = list(all_results or [])
    performance_report = dict(performance_report or {})
    cognitive_capability_report = dict(cognitive_capability_report or {})
    runtime_lifecycle_report = dict(runtime_lifecycle_report or {})
    task_reports = [
        _build_task_report(index, item)
        for index, item in enumerate(all_results, start=1)
        if isinstance(item, Mapping)
    ]
    aggregate_nodes = [
        node
        for task_report in task_reports
        for node in task_report["execution_graph"]["nodes"]
    ]
    aggregate_edges = [
        edge
        for task_report in task_reports
        for edge in task_report["execution_graph"]["edges"]
    ]
    transformations = [
        attempt
        for task_report in task_reports
        for attempt in task_report["transformation_statistics"][
            "transformation_attempts"
        ]
    ]
    program_statistics = _aggregate_program_statistics(task_reports)
    capability_activations = _capability_activations(
        cognitive_capability_report,
        task_reports,
    )
    bottlenecks = _bottleneck_analysis(
        aggregate_nodes,
        transformations,
        capability_activations,
        performance_report,
    )
    stage_durations = _stage_durations(aggregate_nodes)
    stage_statistics = _stage_statistics(aggregate_nodes)

    return {
        "system": "solver_intelligence",
        "SOLVER_INTELLIGENCE_REPORT": True,
        "task_count": len(task_reports),
        "execution_graph": {
            "nodes": aggregate_nodes,
            "edges": aggregate_edges,
            "node_count": len(aggregate_nodes),
            "edge_count": len(aggregate_edges),
        },
        "execution_timeline": _execution_timeline(aggregate_nodes),
        "stage_durations": stage_durations,
        "stage_statistics": stage_statistics,
        "transformation_statistics": _transformation_statistics(
            transformations,
        ),
        "program_statistics": program_statistics,
        "capability_activations": capability_activations,
        "execution_tree": _execution_tree(task_reports),
        "bottleneck_analysis": bottlenecks,
        "optimization_candidates": _optimization_candidates(bottlenecks),
        "task_reports": task_reports,
        "runtime_lifecycle_bridge": {
            "execution_ids_reused": bool(runtime_lifecycle_report),
            "lifecycle_execution_count": runtime_lifecycle_report.get(
                "executions_created",
                0,
            ),
        },
        "instrumentation_overhead": {
            "mode": "post_hoc_context_synthesis",
            "estimated_overhead_percent": 0.0,
            "duplicate_profiling": False,
        },
    }


def _build_task_report(index: int, item: Mapping[str, Any]) -> dict[str, Any]:
    context = item.get("result", item)
    if not isinstance(context, Mapping):
        context = {}
    task_id = str(
        item.get("task")
        or item.get("task_file")
        or context.get("task_id")
        or f"task_{index}",
    )
    nodes = []
    edges = []
    previous_node_id = None
    for order, (stage_key, node_type) in enumerate(SOLVER_STAGE_MODEL, start=1):
        node = _stage_node(task_id, order, stage_key, node_type, context)
        nodes.append(node)
        if previous_node_id:
            edges.append({
                "from": previous_node_id,
                "to": node["node_id"],
                "previous_stage": nodes[-2]["stage_name"],
                "next_stage": node["stage_name"],
                "execution_order": order,
                "parallel_execution": False,
            })
        previous_node_id = node["node_id"]

    flow = {
        "previous_stage": {
            node["stage_name"]: nodes[pos - 1]["stage_name"] if pos else None
            for pos, node in enumerate(nodes)
        },
        "next_stage": {
            node["stage_name"]: (
                nodes[pos + 1]["stage_name"]
                if pos + 1 < len(nodes)
                else None
            )
            for pos, node in enumerate(nodes)
        },
        "execution_order": [
            {"stage": node["stage_name"], "order": node["execution_order"]}
            for node in nodes
        ],
        "parallel_execution": [],
        "blocked_stages": [
            node["stage_name"] for node in nodes if node["status"] == "blocked"
        ],
        "skipped_stages": [
            node["stage_name"] for node in nodes if node["status"] == "skipped"
        ],
        "failed_stages": [
            node["stage_name"] for node in nodes if node["status"] == "failed"
        ],
        "repeated_stages": _repeated_stages(nodes),
    }
    transformations = _transformation_attempts(context)
    return {
        "task_id": task_id,
        "execution_graph": {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
        "pipeline_flow": flow,
        "transformation_statistics": _transformation_statistics(
            transformations,
        ),
        "program_statistics": _program_statistics(context),
        "execution_tree": _task_execution_tree(task_id, nodes),
    }


def _stage_node(
    task_id: str,
    order: int,
    stage_key: str,
    node_type: str,
    context: Mapping[str, Any],
) -> dict[str, Any]:
    stage_report = _stage_report(stage_key, context)
    stage_name = _stage_name(stage_key)
    status = _stage_status(stage_key, stage_report, context)
    start = stage_report.get("timestamp") or context.get("timestamp")
    end = stage_report.get("completed_at") or start
    elapsed = _stage_elapsed(stage_key, stage_report, context)
    input_objects = _input_objects(stage_key, context)
    output_objects = _output_objects(stage_key, context)
    statistics = _stage_profile(stage_key, context)
    confidence = _stage_confidence(stage_key, context)

    return {
        "node_id": f"{task_id}:solver:{order:02d}:{stage_key}",
        "node_type": node_type,
        "stage_name": stage_name,
        "execution_start": start,
        "execution_end": end,
        "elapsed_time": elapsed,
        "execution_time": elapsed,
        "cpu_time": elapsed,
        "cpu_cost": elapsed,
        "memory_cost": _memory_cost(stage_report, statistics),
        "input_objects": input_objects,
        "output_objects": output_objects,
        "status": status,
        "confidence": confidence,
        "execution_order": order,
        "parallel_execution": False,
        **statistics,
    }


def _stage_report(stage_key: str, context: Mapping[str, Any]) -> dict[str, Any]:
    mapping = {
        "perception": "grid_analysis_stage_report",
        "object_extraction": "object_detection_stage_report",
        "feature_analysis": "grid_analysis_stage_report",
        "pattern_analysis": "pattern_rule_stage_report",
        "spatial_analysis": "inference_stage_report",
        "color_analysis": "pattern_rule_stage_report",
        "topology_analysis": "inference_stage_report",
        "dependency_analysis": "dependency_context_report",
        "causal_analysis": "CAUSAL_CONTEXT_REPORT",
        "hypothesis_generation": "inference_stage_report",
        "transformation_discovery": "transformation_stage_report",
        "candidate_program_generation": "inference_stage_report",
        "candidate_ranking": "inference_stage_report",
        "program_validation": "evaluation_stage_report",
        "solution_selection": "evaluation_stage_report",
        "final_output": "evaluation_stage_report",
    }
    value = context.get(mapping.get(stage_key, ""))
    return dict(value) if isinstance(value, Mapping) else {}


def _stage_name(stage_key: str) -> str:
    return stage_key.replace("_", " ").title()


def _stage_status(
    stage_key: str,
    stage_report: Mapping[str, Any],
    context: Mapping[str, Any],
) -> str:
    if stage_report.get("status"):
        return str(stage_report["status"]).lower()
    required = {
        "perception": "input_grid",
        "object_extraction": "input_object_summaries",
        "feature_analysis": "grid_analysis",
        "pattern_analysis": "patterns",
        "hypothesis_generation": "hypotheses",
        "transformation_discovery": "transformation_report",
        "candidate_program_generation": "synthesized_program",
        "candidate_ranking": "ranked_hypotheses",
        "program_validation": "evaluation_result",
        "solution_selection": "evaluation_result",
        "final_output": "predicted_output",
    }
    key = required.get(stage_key)
    if key and context.get(key) is not None:
        return "completed"
    if stage_key in {"dependency_analysis", "causal_analysis"}:
        return "completed" if _stage_profile(stage_key, context)[
            "objects_processed"
        ] else "skipped"
    return "skipped"


def _stage_elapsed(
    stage_key: str,
    stage_report: Mapping[str, Any],
    context: Mapping[str, Any],
) -> float:
    for key in ("elapsed_time", "execution_time", "duration_seconds"):
        if key in stage_report:
            return round(_number(stage_report.get(key)), 6)
    timings = context.get("performance_report", {}).get("module_timings", {})
    if isinstance(timings, list):
        matches = {
            "perception": ("grid_analysis", "task_loading"),
            "object_extraction": ("object_detection",),
            "feature_analysis": ("grid_analysis",),
            "pattern_analysis": ("pattern_rule",),
            "hypothesis_generation": ("inference",),
            "transformation_discovery": ("transformation",),
            "candidate_program_generation": ("inference",),
            "candidate_ranking": ("inference",),
            "program_validation": ("evaluation",),
            "solution_selection": ("evaluation",),
            "final_output": ("evaluation",),
        }.get(stage_key, ())
        total = sum(
            _number(item.get("seconds"))
            for item in timings
            if isinstance(item, Mapping)
            and any(name in str(item.get("module", "")) for name in matches)
        )
        if total:
            return round(total, 6)
    return 0.0


def _input_objects(stage_key: str, context: Mapping[str, Any]) -> list[Any]:
    if stage_key == "object_extraction":
        return _object_ids(context.get("input_objects", []))
    return _object_ids(context.get("input_object_summaries", []))


def _output_objects(stage_key: str, context: Mapping[str, Any]) -> list[Any]:
    if stage_key in {"final_output", "solution_selection"}:
        return ["predicted_output"] if context.get("predicted_output") is not None else []
    return _object_ids(context.get("output_object_summaries", []))


def _object_ids(objects: Any) -> list[Any]:
    if not isinstance(objects, list):
        return []
    ids = []
    for index, obj in enumerate(objects, start=1):
        if isinstance(obj, Mapping):
            ids.append(obj.get("id") or obj.get("object_id") or f"object_{index}")
        else:
            ids.append(f"object_{index}")
    return ids


def _stage_profile(stage_key: str, context: Mapping[str, Any]) -> dict[str, Any]:
    hypotheses = _list(context.get("hypotheses"))
    ranked = _list(context.get("ranked_hypotheses"))
    program = context.get("synthesized_program", {})
    evaluation = context.get("evaluation_result", {})
    transformation_attempts = _transformation_attempts(context)
    validation_count = 1 if isinstance(evaluation, Mapping) and evaluation else 0
    successful = sum(1 for item in transformation_attempts if item["success"])
    failed = sum(1 for item in transformation_attempts if not item["success"])
    profile = {
        "objects_processed": len(_input_objects(stage_key, context))
        + len(_output_objects(stage_key, context)),
        "concepts_generated": len(_list(context.get("semantic_abstractions")))
        + len(_list(context.get("patterns")))
        + len(_list(context.get("rules"))),
        "hypotheses_generated": len(hypotheses) if "hypothesis" in stage_key else 0,
        "candidate_programs": _number(program.get("step_count"), 0)
        if isinstance(program, Mapping)
        else len(ranked),
        "validation_count": validation_count
        if stage_key in {"program_validation", "solution_selection"}
        else 0,
        "successful_transformations": successful
        if stage_key == "transformation_discovery"
        else 0,
        "failed_transformations": failed
        if stage_key == "transformation_discovery"
        else 0,
        "retry_count": _retry_count(context)
        if stage_key in {"program_validation", "solution_selection"}
        else 0,
    }
    if stage_key == "object_extraction":
        profile["objects_processed"] = len(_list(context.get("input_objects"))) + len(
            _list(context.get("output_objects"))
        )
    if stage_key == "candidate_ranking":
        profile["candidate_programs"] = len(ranked)
    return profile


def _stage_confidence(stage_key: str, context: Mapping[str, Any]) -> float:
    inference = context.get("inference_report", {})
    evaluation = context.get("evaluation_result", {})
    inference = inference if isinstance(inference, Mapping) else {}
    evaluation = evaluation if isinstance(evaluation, Mapping) else {}
    if stage_key in {"hypothesis_generation", "candidate_ranking"}:
        return round(_number(inference.get("global_confidence")), 4)
    if stage_key == "transformation_discovery":
        return round(_number(context.get("transformation_confidence")), 4)
    if stage_key in {"program_validation", "solution_selection"}:
        return round(_number(evaluation.get("accuracy")), 4)
    return 1.0 if _stage_status(stage_key, _stage_report(stage_key, context), context) == "completed" else 0.0


def _memory_cost(*values: Any) -> int:
    return sum(getsizeof(value) for value in values)


def _transformation_attempts(context: Mapping[str, Any]) -> list[dict[str, Any]]:
    attempts = []
    report = context.get("transformation_report", {})
    trace = []
    if isinstance(report, Mapping):
        trace = _list(report.get("execution_trace"))
    trace.extend(_list(context.get("transformation_execution_trace")))
    if not trace and isinstance(report, Mapping):
        for item in _list(report.get("sandbox_execution", {}).get("simulation_trace")):
            trace.append(item)
    for index, item in enumerate(trace, start=1):
        item = item if isinstance(item, Mapping) else {"operation": str(item)}
        status = str(item.get("status", "")).lower()
        success = status in {"success", "completed", "executed", "simulated"}
        attempts.append({
            "attempt_id": f"transformation_{index}",
            "transformation_type": item.get("operation")
            or item.get("primitive")
            or item.get("type")
            or "unknown",
            "input": item.get("input") or item.get("parameters", {}),
            "output": item.get("output") or item.get("result", {}),
            "success": success,
            "failure_reason": item.get("failure_reason")
            or (None if success else item.get("status", "not_successful")),
            "confidence": round(_number(item.get("confidence"), 0.0), 4),
            "execution_cost": round(_number(item.get("execution_cost"), 0.0), 6),
            "validation_result": item.get("validation_result", item.get("status")),
        })
    return attempts


def _program_statistics(context: Mapping[str, Any]) -> dict[str, Any]:
    ranked = _list(context.get("ranked_hypotheses"))
    selected = _list(context.get("hypotheses"))
    program = context.get("synthesized_program", {})
    winning = context.get("winner_hypothesis", {})
    generated = max(
        len(ranked),
        len(selected),
        int(_number(program.get("step_count"), 0)) if isinstance(program, Mapping) else 0,
    )
    rejected = []
    winner_type = winning.get("type") if isinstance(winning, Mapping) else None
    for candidate in ranked:
        if not isinstance(candidate, Mapping):
            continue
        if candidate is winning or candidate.get("type") == winner_type:
            continue
        rejected.append({
            "program": candidate.get("type") or candidate.get("primitive", "candidate"),
            "why_rejected": candidate.get("rejection_reason")
            or "ranked_below_winning_program",
            "why_another_program_won": "higher_confidence_or_execution_score",
        })
    return {
        "programs_generated": generated,
        "programs_rejected": len(rejected),
        "programs_validated": 1 if context.get("evaluation_result") else 0,
        "programs_ranked": len(ranked),
        "programs_executed": 1 if context.get("predicted_output") is not None else 0,
        "winning_program": winning,
        "rejected_programs": rejected,
    }


def _aggregate_program_statistics(task_reports: list[Mapping[str, Any]]) -> dict[str, Any]:
    stats = Counter()
    rejected = []
    winning = []
    for report in task_reports:
        program = report.get("program_statistics", {})
        for key in (
            "programs_generated",
            "programs_rejected",
            "programs_validated",
            "programs_ranked",
            "programs_executed",
        ):
            stats[key] += int(_number(program.get(key), 0))
        rejected.extend(_list(program.get("rejected_programs")))
        if program.get("winning_program"):
            winning.append(program.get("winning_program"))
    return {
        **dict(stats),
        "winning_program": winning[0] if winning else {},
        "winning_programs": winning,
        "rejected_programs": rejected,
    }


def _transformation_statistics(attempts: list[Mapping[str, Any]]) -> dict[str, Any]:
    failures = [item for item in attempts if not item.get("success")]
    successes = [item for item in attempts if item.get("success")]
    by_type = Counter(str(item.get("transformation_type", "unknown")) for item in attempts)
    return {
        "transformation_attempts": list(attempts),
        "attempt_count": len(attempts),
        "successful_transformations": len(successes),
        "failed_transformations": len(failures),
        "success_rate": round(len(successes) / max(len(attempts), 1), 4),
        "by_type": dict(by_type),
        "most_failed_transformation": (
            Counter(
                str(item.get("transformation_type", "unknown"))
                for item in failures
            ).most_common(1)[0][0]
            if failures else None
        ),
    }


def _capability_activations(
    report: Mapping[str, Any],
    task_reports: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    raw = report.get("capabilities_executed") or report.get("capability_events") or []
    activations = []
    for index, item in enumerate(_list(raw), start=1):
        item = item if isinstance(item, Mapping) else {"capability": str(item)}
        activations.append({
            "capability": item.get("capability")
            or item.get("name")
            or item.get("capability_name")
            or f"capability_{index}",
            "activation_time": item.get("activation_time"),
            "execution_time": round(_number(item.get("execution_time")), 6),
            "contribution": item.get("contribution", item.get("result", "")),
            "confidence": round(_number(item.get("confidence"), 0.0), 4),
            "input_concepts": _list(item.get("input_concepts")),
            "output_concepts": _list(item.get("output_concepts")),
            "interaction_with_other_capabilities": _list(
                item.get("interaction_with_other_capabilities")
                or item.get("interactions")
            ),
        })
    if not activations and task_reports:
        activations.append({
            "capability": "solver_pipeline",
            "activation_time": None,
            "execution_time": sum(
                node.get("elapsed_time", 0.0)
                for task in task_reports
                for node in task["execution_graph"]["nodes"]
            ),
            "contribution": "constructed_solver_solution_path",
            "confidence": 1.0,
            "input_concepts": [],
            "output_concepts": [],
            "interaction_with_other_capabilities": [],
        })
    return activations


def _bottleneck_analysis(
    nodes: list[Mapping[str, Any]],
    transformations: list[Mapping[str, Any]],
    capabilities: list[Mapping[str, Any]],
    performance_report: Mapping[str, Any],
) -> dict[str, Any]:
    slowest = max(nodes, key=lambda node: node.get("elapsed_time", 0.0), default={})
    expensive = max(nodes, key=lambda node: node.get("cpu_cost", 0.0), default={})
    branch = max(nodes, key=lambda node: node.get("candidate_programs", 0), default={})
    validation = max(
        [node for node in nodes if node.get("validation_count", 0)],
        key=lambda node: node.get("elapsed_time", 0.0),
        default={},
    )
    retries = max(nodes, key=lambda node: node.get("retry_count", 0), default={})
    failed_by_type = Counter(
        str(item.get("transformation_type", "unknown"))
        for item in transformations
        if not item.get("success")
    )
    capability_counts = Counter(str(item.get("capability")) for item in capabilities)
    least_effective = min(
        capabilities,
        key=lambda item: item.get("confidence", 0.0),
        default={},
    )
    return {
        "slowest_stage": slowest.get("stage_name"),
        "slowest_stage_time": slowest.get("elapsed_time", 0.0),
        "most_expensive_stage": expensive.get("stage_name"),
        "most_expensive_stage_cost": expensive.get("cpu_cost", 0.0),
        "largest_branch_explosion": branch.get("stage_name"),
        "largest_branch_count": branch.get("candidate_programs", 0),
        "most_failed_transformations": failed_by_type.most_common(1)[0][0]
        if failed_by_type else None,
        "longest_validation": validation.get("stage_name"),
        "longest_validation_time": validation.get("elapsed_time", 0.0),
        "highest_retry_count": retries.get("retry_count", 0),
        "highest_retry_stage": retries.get("stage_name"),
        "most_reused_capability": capability_counts.most_common(1)[0][0]
        if capability_counts else None,
        "least_effective_capability": least_effective.get("capability"),
        "reasoning_time_seconds": performance_report.get(
            "reasoning_time_seconds",
            0.0,
        ),
    }


def _optimization_candidates(bottlenecks: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    if bottlenecks.get("slowest_stage"):
        candidates.append({
            "target": bottlenecks["slowest_stage"],
            "reason": "slowest_solver_stage",
            "evidence": bottlenecks.get("slowest_stage_time", 0.0),
        })
    if bottlenecks.get("largest_branch_explosion"):
        candidates.append({
            "target": bottlenecks["largest_branch_explosion"],
            "reason": "largest_candidate_branching",
            "evidence": bottlenecks.get("largest_branch_count", 0),
        })
    if bottlenecks.get("most_failed_transformations"):
        candidates.append({
            "target": bottlenecks["most_failed_transformations"],
            "reason": "transformation_failures",
            "evidence": "highest_failure_count",
        })
    return candidates


def _execution_timeline(nodes: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "node_id": node["node_id"],
            "stage_name": node["stage_name"],
            "execution_start": node.get("execution_start"),
            "execution_end": node.get("execution_end"),
            "elapsed_time": node.get("elapsed_time", 0.0),
            "status": node.get("status"),
        }
        for node in nodes
    ]


def _stage_durations(nodes: list[Mapping[str, Any]]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for node in nodes:
        totals[node["stage_name"]] = round(
            totals.get(node["stage_name"], 0.0)
            + _number(node.get("elapsed_time")),
            6,
        )
    return totals


def _stage_statistics(nodes: list[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for node in nodes:
        stage = node["stage_name"]
        current = stats.setdefault(stage, {
            "execution_count": 0,
            "objects_processed": 0,
            "concepts_generated": 0,
            "hypotheses_generated": 0,
            "candidate_programs": 0,
            "validation_count": 0,
            "successful_transformations": 0,
            "failed_transformations": 0,
            "retry_count": 0,
        })
        current["execution_count"] += 1
        for key in list(current.keys()):
            if key != "execution_count":
                current[key] += int(_number(node.get(key), 0))
    return stats


def _execution_tree(task_reports: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "name": "Task",
        "children": [
            task_report["execution_tree"]
            for task_report in task_reports
        ],
    }


def _task_execution_tree(task_id: str, nodes: list[Mapping[str, Any]]) -> dict[str, Any]:
    focus = {
        "Perception",
        "Pattern Analysis",
        "Transformation Discovery",
        "Candidate Program Generation",
        "Program Validation",
        "Solution Selection",
    }
    children = [
        {
            "name": node["stage_name"],
            "node_id": node["node_id"],
            "elapsed_time": node.get("elapsed_time", 0.0),
            "cpu_cost": node.get("cpu_cost", 0.0),
            "objects_processed": node.get("objects_processed", 0),
            "status": node.get("status"),
        }
        for node in nodes
        if node["stage_name"] in focus or node["stage_name"] == "Final Output"
    ]
    return {
        "name": task_id,
        "children": [
            {
                "name": "Solver",
                "children": children,
            }
        ],
    }


def _repeated_stages(nodes: list[Mapping[str, Any]]) -> list[str]:
    counts = Counter(node["stage_name"] for node in nodes)
    return [stage for stage, count in counts.items() if count > 1]


def _retry_count(context: Mapping[str, Any]) -> int:
    final_repair = context.get("FINAL_REPAIR_REPORT", {})
    evaluation = context.get("evaluation_metrics", {})
    return int(
        _number(final_repair.get("repair_attempts"), 0)
        or _number(evaluation.get("repair_attempts"), 0)
    )


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default
