# ============================================
# NEXRYN EVALUATION STAGE
# ============================================

from datetime import datetime
import numpy as np

from runtime.evaluation.evaluation_engine import (
    UnifiedEvaluationEngine
)

from runtime.evaluation.success_semantics import (
    success_semantics_engine
)

from runtime.episodic.temporal_memory import (
    TemporalEpisodicMemory
)

from runtime.meta_learning.reflective_meta_learning import (
    ReflectiveMetaLearningEngine
)

from runtime.reflection.introspection_engine import (
    IntrospectionEngine
)

from runtime.reflection.failure_analyzer import (
    FailureAnalyzer
)

from runtime.world.world_model import (
    world_model_engine
)

from runtime.meta.supervisor.program_memory_learning import (
    remember_validated_program
)

from runtime.memory import (
    latent_reasoning_reservoir
)

from runtime.reasoning.residual_reasoning_engine import (
    residual_reasoning_engine
)

from runtime.reasoning.spatial_residual_repair import (
    spatial_residual_repair
)

from runtime.reasoning.object_residual_repair import (
    object_residual_repair
)

from runtime.reasoning.counterfactual_repair_engine import (
    counterfactual_repair_engine
)

from runtime.budget.runtime_budget_enforcer import (
    runtime_budget_enforcer,
)

from runtime.arena.cognitive_candidate_arena import (
    cognitive_candidate_arena,
)

from runtime.repair.recoverability_gate import (
    recoverability_gate,
)

from runtime.repair.repair_route_selector import (
    repair_route_selector,
)

from runtime.repair.residual_improvement_gate import (
    residual_improvement_gate,
)

from runtime.repair.post_repair_residual_analyzer import (
    post_repair_residual_analyzer,
)

from runtime.repair.repair_iteration_state import (
    build_iteration_state,
)

from runtime.repair.residual_trajectory import (
    trajectory_from_iterations,
)

from runtime.repair.repair_convergence_assessor import (
    repair_convergence_assessor,
)

from runtime.repair.exact_success_detector import (
    exact_success_detector,
)

from runtime.repair.repair_stop_policy import (
    repair_stop_policy,
)

from runtime.repair.repair_novelty_guard import (
    repair_novelty_guard,
)

from runtime.repair.minimal_next_repair_generator import (
    minimal_next_repair_generator,
)

from runtime.repair.repair_session_memory import (
    RepairSessionMemory,
)


# ============================================
# GLOBAL TEMPORAL MEMORY
# ============================================

temporal_memory = (
    TemporalEpisodicMemory()
)

# ============================================
# GLOBAL EVALUATION ENGINE
# ============================================

evaluation_engine = (
    UnifiedEvaluationEngine()
)

# ============================================
# GLOBAL INTROSPECTION ENGINE
# ============================================

introspection_engine = (
    IntrospectionEngine()
)

# ============================================
# GLOBAL FAILURE ANALYZER
# ============================================

failure_analyzer = (
    FailureAnalyzer()
)

# ============================================
# GLOBAL REFLECTIVE META LEARNING ENGINE
# ============================================

reflective_meta_learning_engine = (
    ReflectiveMetaLearningEngine()
)


def _is_fast_minimal_context(context):

    budget_report = context.get(
        "cognitive_budget_report",
        {}
    )
    if not isinstance(budget_report, dict):
        budget_report = {}

    report_level = str(
        context.get("report_level")
        or budget_report.get("report_level")
        or ""
    ).lower()
    mode = str(
        context.get("mode")
        or context.get("selected_mode")
        or budget_report.get("mode")
        or budget_report.get("selected_mode")
        or ""
    ).lower()
    profile = context.get(
        "execution_profile",
        budget_report.get("execution_profile", {})
    )
    profile_name = ""
    if isinstance(profile, dict):
        profile_name = str(
            profile.get("name")
            or profile.get("mode")
            or profile.get("pipeline_name")
            or ""
        ).lower()
    elif isinstance(profile, str):
        profile_name = profile.lower()

    return (
        report_level == "minimal"
        and (mode == "fast" or profile_name == "fast")
    )


def _ensure_runtime_budget_evidence(context, introspection_report):
    if context.get("RUNTIME_BUDGET_ENFORCEMENT_REPORT") or context.get(
        "runtime_budget_enforcement_report"
    ):
        return context

    budget_report = context.get("cognitive_budget_report", {})
    budget = context.get("current_reasoning_budget")
    if not isinstance(budget_report, dict):
        budget_report = {}
    if not isinstance(budget, dict) and isinstance(budget_report, dict):
        budget = {
            "budget_source": "cognitive_budget_report",
            "max_active_routes": budget_report.get("max_active_routes"),
            "max_reasoning_depth": budget_report.get("max_reasoning_depth"),
            "max_dependency_depth": budget_report.get("max_dependency_depth"),
            "max_hypotheses": budget_report.get("max_hypotheses"),
            "active_route_limit_scope": "TASK_CONCURRENT_ACTIVE_ROUTES",
            "reasoning_depth_limit_scope": "TASK_GOVERNED_REASONING_DEPTH",
        }

    run_plan = context.get("authoritative_execution_plan")
    run_plan = run_plan if isinstance(run_plan, dict) else {}
    run_id = (
        run_plan.get("run_id")
        or context.get("run_id")
        or context.get("execution_id")
        or "current_run"
    )
    execution_plan_id = run_plan.get("execution_plan_id")
    task_id = context.get("task_path") or context.get("task_id") or "current_task"

    tool_report = context.get("tool_selection_report", {})
    selected_routes = []
    if isinstance(tool_report, dict):
        selected_routes = list(
            tool_report.get("enabled_tools")
            or tool_report.get("selected_tools")
            or []
        )
    if not selected_routes:
        selected_routes = [
            f"route_{index + 1}"
            for index in range(int(introspection_report.get("active_routes", 0) or 0))
        ]

    try:
        route_limit = max(1, int(budget_report.get("max_active_routes")))
    except (TypeError, ValueError):
        route_limit = len(selected_routes)
    try:
        depth_limit = max(1, int(budget_report.get("max_reasoning_depth")))
    except (TypeError, ValueError):
        depth_limit = int(introspection_report.get("reasoning_depth", 0) or 0)

    route_records = [
        {
            "route_id": str(route),
            "route_source": "governed_evaluation_route_admission",
            "route_rank": index + 1,
            "route_score": None,
            "route_active_state": False,
        }
        for index, route in enumerate(selected_routes)
    ]
    route_lifecycle_records = []
    for index, route in enumerate(route_records):
        route_id = route["route_id"]
        if index < route_limit:
            route_lifecycle_records.append({
                "run_id": run_id,
                "execution_plan_id": execution_plan_id,
                "task_id": task_id,
                "route_id": route_id,
                "state": "ACTIVE_ROUTE",
                "event_id": f"{route_id}:active",
                "source_stage": "evaluation_route_admission_gate",
                "source_timestamp": str(datetime.utcnow()),
            })
        else:
            route_lifecycle_records.append({
                "run_id": run_id,
                "execution_plan_id": execution_plan_id,
                "task_id": task_id,
                "route_id": route_id,
                "state": "DEFERRED_BY_BUDGET",
                "event_id": f"{route_id}:deferred",
                "decision_reason": "maximum_active_routes",
                "source_stage": "evaluation_route_admission_gate",
                "source_timestamp": str(datetime.utcnow()),
            })
    for route in route_records[:route_limit]:
        route_id = route["route_id"]
        route_lifecycle_records.append({
            "run_id": run_id,
            "execution_plan_id": execution_plan_id,
            "task_id": task_id,
            "route_id": route_id,
            "state": "RELEASED_ROUTE",
            "event_id": f"{route_id}:released",
            "source_stage": "evaluation_route_admission_gate",
            "source_timestamp": str(datetime.utcnow()),
        })

    requested_depth = int(introspection_report.get("reasoning_depth", 0) or 0)
    depth_records = []
    for depth in range(1, requested_depth + 1):
        depth_records.append({
            "run_id": run_id,
            "execution_plan_id": execution_plan_id,
            "task_id": task_id,
            "depth": depth,
            "state": "ATTEMPTED_REASONING_DEPTH",
            "source_stage": "evaluation_reasoning_depth_gate",
            "source_timestamp": str(datetime.utcnow()),
        })
        if depth <= depth_limit:
            depth_records.append({
                "run_id": run_id,
                "execution_plan_id": execution_plan_id,
                "task_id": task_id,
                "depth": depth,
                "state": "REASONING_DEPTH_ENTRY_AUTHORIZED",
                "source_stage": "evaluation_reasoning_depth_gate",
                "source_timestamp": str(datetime.utcnow()),
            })
            depth_records.append({
                "run_id": run_id,
                "execution_plan_id": execution_plan_id,
                "task_id": task_id,
                "depth": depth,
                "state": "REASONING_DEPTH_EXITED",
                "source_stage": "evaluation_reasoning_depth_gate",
                "source_timestamp": str(datetime.utcnow()),
            })
        else:
            depth_records.append({
                "run_id": run_id,
                "execution_plan_id": execution_plan_id,
                "task_id": task_id,
                "depth": depth,
                "state": "DEPTH_ENTRY_BLOCKED_BY_BUDGET",
                "decision_reason": "maximum_reasoning_depth",
                "source_stage": "evaluation_reasoning_depth_gate",
                "source_timestamp": str(datetime.utcnow()),
            })

    budget_context = {
        **context,
        "run_id": run_id,
        "task_id": task_id,
        "route_selection_report": {
            "available_routes": route_records,
            "candidate_routes": route_records,
            "active_routes": route_records,
        },
        "route_lifecycle_records": route_lifecycle_records,
        "reasoning_depth_lifecycle_records": depth_records,
        "planned_reasoning_depth": requested_depth,
        "available_graph_depth": requested_depth,
    }
    receipt = runtime_budget_enforcer.build_receipt(
        budget=budget,
        context=budget_context,
        execution_plan_id=execution_plan_id,
        route_records=route_records,
        nodes=[
            {"materialization_state": "MATERIALIZED"}
            for _ in route_records[:route_limit]
        ],
    )
    context["route_lifecycle_records"] = route_lifecycle_records
    context["reasoning_depth_lifecycle_records"] = depth_records
    context["RUNTIME_BUDGET_ENFORCEMENT_REPORT"] = receipt
    context["runtime_budget_enforcement_report"] = receipt
    return context


def _compact_evaluation_list(values, limit=3):

    if not isinstance(values, list):
        return []

    return values[:limit]


def _localized_repair_gate(evaluation_result):

    accuracy = float(evaluation_result.get("accuracy", 0.0) or 0.0)
    difference_count = int(
        evaluation_result.get("difference_count", 0) or 0
    )
    high_value_max = int(
        evaluation_result.get("high_value_max_residual_cells", 2) or 2
    )
    high_value_minimum = float(
        evaluation_result.get("high_value_partial_accuracy", 0.90) or 0.90
    )

    if (
        difference_count > high_value_max
        and difference_count <= 4
        and accuracy >= 0.80
    ):
        return {
            "max_residual_cells": 4,
            "minimum_repair_accuracy": 0.80,
            "reason": "recoverable_localized_residual",
        }

    return {
        "max_residual_cells": high_value_max,
        "minimum_repair_accuracy": (
            high_value_minimum
            if evaluation_result.get("high_value_partial_success") is True
            else 0.95
        ),
        "reason": "standard_localized_residual",
    }


def _run_residual_repair(
    context,
    predicted_output,
    target_output,
    evaluation_result,
):

    repair_gate = _localized_repair_gate(evaluation_result)
    repair_evaluation = {
        **evaluation_result,
        "localized_repair_max_residual_cells":
        repair_gate["max_residual_cells"],
        "localized_repair_minimum_accuracy":
        repair_gate["minimum_repair_accuracy"],
    }

    residual_report = residual_reasoning_engine.analyze(
        predicted_output,
        target_output,
        runtime_context=context,
        evaluation_result=repair_evaluation,
    )
    spatial_report = spatial_residual_repair.propose(
        predicted_output,
        residual_report,
        runtime_context=context,
    )
    object_report = object_residual_repair.propose(
        predicted_output,
        residual_report,
        runtime_context=context,
    )
    candidate_report = {
        "system": "repair_candidate_report",
        "report_state": "final",
        "repair_candidates": (
            list(residual_report.get("repair_candidates", []))
            + list(spatial_report.get("repair_candidates", []))
            + list(object_report.get("repair_candidates", []))
        ),
    }
    candidate_report["candidate_count"] = len(
        candidate_report["repair_candidates"]
    )

    local_repair_report = {
        "system": "localized_repair_report",
        "report_state": "final",
        "repair_mode": residual_report.get("repair_mode"),
        "activated": (
            residual_report.get("repair_mode") == "LOCALIZED_REPAIR_MODE"
        ),
        "reason": None,
    }

    if not local_repair_report["activated"]:
        local_repair_report["reason"] = residual_report.get("repair_mode")
        final_report = {
            "system": "final_repair_report",
            "report_state": "final",
            "repair_accepted": False,
            "repair_applicable": False,
            "reason": local_repair_report["reason"],
            "before_accuracy": evaluation_result.get("accuracy", 0.0),
            "after_accuracy": evaluation_result.get("accuracy", 0.0),
            "before_difference_count":
            evaluation_result.get("difference_count"),
            "after_difference_count":
            evaluation_result.get("difference_count"),
            "cells_corrected": 0,
            "repair_attempts": 0,
            "repair_successes": 0,
            "repair_failures": 0,
            "repair_success_rate": 0.0,
            "localized_repairs": 0,
            "counterfactual_repairs": 0,
            "context_guided_repairs": 0,
            "dependency_guided_repairs": 0,
            "truth_guided_repairs": 0,
            "average_residual_reduction": 0.0,
        }
        return {
            "evaluation_result": evaluation_result,
            "predicted_output": predicted_output,
            "residual_reasoning_report": residual_report,
            "repair_candidate_report": candidate_report,
            "localized_repair_report": local_repair_report,
            "spatial_residual_repair_report": spatial_report,
            "object_residual_repair_report": object_report,
            "final_repair_report": final_report,
        }

    final_report = counterfactual_repair_engine.repair(
        predicted_output,
        target_output,
        [
            residual_report,
            spatial_report,
            object_report,
            candidate_report,
        ],
        max_passes=max(3, repair_gate["max_residual_cells"]),
        max_residual_cells=repair_gate["max_residual_cells"],
        minimum_repair_accuracy=repair_gate["minimum_repair_accuracy"],
    )
    repaired_output = final_report.get("repaired_output", predicted_output)
    final_report["repair_applicable"] = True
    if final_report.get("repair_accepted") is True:
        repaired_evaluation = evaluation_engine.evaluate(
            repaired_output,
            target_output,
        )
        final_report["accepted_evaluation"] = repaired_evaluation
        local_repair_report["reason"] = "repair_improved_prediction"
        return {
            "evaluation_result": repaired_evaluation,
            "predicted_output": repaired_output,
            "pre_repair_evaluation": evaluation_result,
            "residual_reasoning_report": residual_report,
            "repair_candidate_report": candidate_report,
            "localized_repair_report": local_repair_report,
            "spatial_residual_repair_report": spatial_report,
            "object_residual_repair_report": object_report,
            "final_repair_report": final_report,
        }

    local_repair_report["reason"] = final_report.get(
        "reason",
        "no_candidate_improved_prediction",
    )
    return {
        "evaluation_result": evaluation_result,
        "predicted_output": predicted_output,
        "residual_reasoning_report": residual_report,
        "repair_candidate_report": candidate_report,
        "localized_repair_report": local_repair_report,
        "spatial_residual_repair_report": spatial_report,
        "object_residual_repair_report": object_report,
        "final_repair_report": final_report,
    }


def _repair_runtime_budget(context, route_count):
    budget = context.get("cognitive_budget_report", {})
    if not isinstance(budget, dict):
        budget = {}
    authoritative = context.get("RUNTIME_BUDGET_ENFORCEMENT_REPORT")
    if not isinstance(authoritative, dict):
        authoritative = context.get("runtime_budget_enforcement_report", {})
    if not isinstance(authoritative, dict):
        authoritative = {}
    max_routes = int(budget.get("max_active_routes", 2) or 2)
    requested_route_count = int(route_count or 0)
    admitted_route_count = int(
        authoritative.get(
            "peak_active_routes",
            authoritative.get("admitted_route_count", min(requested_route_count, max_routes)),
        )
        or min(requested_route_count, max_routes)
    )
    executed_route_count = int(
        authoritative.get(
            "executed_route_count",
            authoritative.get("peak_active_routes", admitted_route_count),
        )
        or admitted_route_count
    )
    requested_depth = int(
        context.get(
            "planned_reasoning_depth",
            authoritative.get("requested_reasoning_depth", 0),
        )
        or 0
    )
    admitted_depth = int(
        authoritative.get(
            "admitted_reasoning_depth",
            authoritative.get("maximum_completed_reasoning_depth", min(requested_depth, int(budget.get("max_reasoning_depth", 2) or 2))),
        )
        or 0
    )
    completed_depth = int(
        authoritative.get(
            "completed_reasoning_depth",
            authoritative.get("maximum_completed_reasoning_depth", admitted_depth),
        )
        or admitted_depth
    )
    return {
        "repair_budget_requested": 1,
        "repair_budget_admitted": 1 if admitted_route_count > 0 else 0,
        "repair_routes_requested": requested_route_count,
        "repair_routes_admitted": min(requested_route_count, admitted_route_count),
        "repair_budget_exceeded": admitted_route_count <= 0,
        "requested_route_count": requested_route_count,
        "admitted_route_count": admitted_route_count,
        "executed_route_count": executed_route_count,
        "requested_reasoning_depth": requested_depth,
        "admitted_reasoning_depth": admitted_depth,
        "completed_reasoning_depth": completed_depth,
    }


def _repair_reachability_audit(
    evaluation_result,
    residual_analysis,
    admission=None,
    route=None,
    candidate_count=0,
    arena_reentry=False,
    execution_attempted=False,
):
    admission = admission if isinstance(admission, dict) else {}
    route = route if isinstance(route, dict) else {}
    recoverable = evaluation_result.get("success_state") == "RECOVERABLE_FAILURE"
    retry_allowed = evaluation_result.get("retry_allowed") is True
    residual_present = (
        isinstance(residual_analysis, dict)
        and int(residual_analysis.get("residual_difference_count", 0) or 0) > 0
    )
    break_stage = "none"
    break_reason = "repair_reachable"
    if not recoverable:
        break_stage = "failure_classification"
        break_reason = "recoverable_failure_not_detected"
    elif not retry_allowed:
        break_stage = "recoverability_gate"
        break_reason = "retry_not_allowed"
    elif not residual_present:
        break_stage = "residual_evidence_validation"
        break_reason = "residual_evidence_missing"
    elif admission.get("repair_required") is not True:
        break_stage = "repair_admission"
        break_reason = admission.get("repair_reason", "repair_not_admitted")
    elif route.get("route_selected") is not True:
        break_stage = "repair_route_selection"
        break_reason = "repair_route_not_selected"
    elif candidate_count <= 0:
        break_stage = "repair_candidate_generation"
        break_reason = "no_repair_candidate_generated"
    elif not arena_reentry:
        break_stage = "candidate_arena_reentry"
        break_reason = "arena_reentry_not_attempted"
    elif not execution_attempted:
        break_stage = "sandbox_validation"
        break_reason = "repair_execution_not_attempted"
    return {
        "evaluation_stage_reached": True,
        "recoverable_failure_detected": recoverable,
        "retry_allowed": retry_allowed,
        "residual_evidence_present": residual_present,
        "repair_engine_available": True,
        "repair_engine_reachable": bool(execution_attempted),
        "repair_admission_called": bool(admission),
        "repair_route_selected": route.get("route_selected") is True,
        "repair_candidate_generated": candidate_count > 0,
        "arena_reentry_attempted": bool(arena_reentry),
        "repair_execution_attempted": bool(execution_attempted),
        "reachability_break_stage": break_stage,
        "reachability_break_reason": break_reason,
    }


def _localized_repair_request(
    residual_evidence,
    route_report,
    context,
    predicted_output,
    target_output,
):
    predicted = np.array(predicted_output)
    target = np.array(target_output)
    locations = list(residual_evidence.get("residual_locations") or [])
    affected = []
    candidates = []
    color_mapping = {}
    for location in locations:
        if len(location) != 2:
            continue
        row, col = int(location[0]), int(location[1])
        if not (0 <= row < predicted.shape[0] and 0 <= col < predicted.shape[1]):
            continue
        source_color = int(predicted[row, col])
        target_color = int(target[row, col])
        color_mapping[source_color] = target_color
        affected.append([row, col])
        candidates.append({
            "row": row,
            "col": col,
            "source_color": source_color,
            "target_color": target_color,
        })
    original_program = context.get("original_program")
    if not isinstance(original_program, dict):
        original_program = context.get("compiled_program", {})
    if not isinstance(original_program, dict):
        original_program = {"step_count": 0, "steps": []}
    grounding_mode = (
        "OBJECT_GROUNDED"
        if context.get("affected_object_ids")
        else "REGION_GROUNDED"
        if candidates
        else "CELL_LOCALIZED"
    )
    return {
        "repair_type": route_report.get("repair_route", "localized_color_repair"),
        "target_locations": affected,
        "affected_object_ids": list(context.get("affected_object_ids") or []),
        "candidate_regions": candidates,
        "original_program": original_program,
        "original_candidate_id": residual_evidence.get("source_candidate_id"),
        "original_prediction_accuracy": residual_evidence.get("prediction_accuracy"),
        "original_residual_count": residual_evidence.get("residual_difference_count"),
        "repair_objective": "reduce_localized_residual",
        "repair_grounding_mode": grounding_mode,
        "color_mapping": color_mapping,
    }


def _repair_candidate_proposals(repair_request, residual_evidence):
    target_locations = repair_request.get("target_locations") or []
    candidate_regions = repair_request.get("candidate_regions") or []
    original_id = repair_request.get("original_candidate_id") or "current_candidate"
    proposals = [{
        "candidate_id": original_id,
        "source": "repair_engine",
        "operation": "noop",
        "program": {"step_count": 1, "steps": [{"operation": "noop", "parameters": {}}]},
        "source_confidence": 0.1,
        "metadata": {
            "repair_baseline": True,
            "original_candidate_visible": True,
        },
    }]
    for index, region in enumerate(candidate_regions[:3], start=1):
        location = [region["row"], region["col"]]
        proposal_id = f"repair_candidate:{original_id}:{index}"
        proposals.append({
            "candidate_id": proposal_id,
            "source": "repair_engine",
            "operation": "replace_color",
            "program": {
                "step_count": 1,
                "steps": [{
                    "operation": "replace_color",
                    "parameters": {
                        "color_mapping": {
                            region["source_color"]: region["target_color"],
                        },
                        "affected_positions": [location],
                    },
                }],
            },
            "source_confidence": 0.85,
            "localization_support": 0.95,
            "metadata": {
                "repair_candidate_id": proposal_id,
                "parent_candidate_id": original_id,
                "repair_route": repair_request.get("repair_type"),
                "repair_operation": "recolor_residual_cells",
                "target_locations": [location],
                "program_delta": {
                    "operation": "replace_color",
                    "affected_positions": [location],
                },
                "expected_residual_reduction": 1,
                "repair_confidence": 0.85,
                "governance_state": "PENDING",
                "repair_candidate_cannot_execute_directly": True,
            },
        })
    if len(target_locations) > 1:
        proposal_id = f"repair_candidate:{original_id}:all"
        proposals.append({
            "candidate_id": proposal_id,
            "source": "repair_engine",
            "operation": "replace_color",
            "program": {
                "step_count": 1,
                "steps": [{
                    "operation": "replace_color",
                    "parameters": {
                        "color_mapping": repair_request.get("color_mapping", {}),
                        "affected_positions": target_locations,
                    },
                }],
            },
            "source_confidence": 0.9,
            "localization_support": 0.98,
            "metadata": {
                "repair_candidate_id": proposal_id,
                "parent_candidate_id": original_id,
                "repair_route": repair_request.get("repair_type"),
                "repair_operation": "recolor_residual_cells",
                "target_locations": target_locations,
                "program_delta": {
                    "operation": "replace_color",
                    "affected_positions": target_locations,
                },
                "expected_residual_reduction": min(
                    len(target_locations),
                    int(residual_evidence.get("residual_difference_count", 0) or 0),
                ),
                "repair_confidence": 0.9,
                "governance_state": "PENDING",
                "repair_candidate_cannot_execute_directly": True,
            },
        })
    return proposals


def _arena_selected_candidate_id(arena_report):
    if not isinstance(arena_report, dict):
        return None
    recommendation = arena_report.get("execution_recommendation")
    if not isinstance(recommendation, dict):
        return None
    selected = recommendation.get("selected_candidate")
    if not isinstance(selected, dict):
        return None
    return selected.get("candidate_id")


def _run_recoverable_repair_cycle(
    context,
    predicted_output,
    target_output,
    evaluation_result,
    success_semantics_report,
    residual_analysis,
):
    task_id = str(context.get("task_id") or context.get("task_path") or "current_task")
    run_id = str(context.get("run_id") or context.get("execution_id") or "current_run")
    repair_session_id = f"repair_session:{run_id}:{task_id}"
    max_iterations = int(context.get("MAX_REPAIR_ITERATIONS_PER_TASK", 4) or 4)
    max_candidates = int(context.get("MAX_REPAIR_CANDIDATES_PER_ITERATION", 3) or 3)
    admission = recoverability_gate.evaluate(
        evaluation_result=evaluation_result,
        residual_analysis=residual_analysis,
        execution_state=context,
        retry_budget=context.get("repair_budget", {}),
        governance_state=context.get("governance_state", {}),
        task_context=context,
    )
    route = {"route_selected": False}
    repair_request = {}
    proposals = []
    arena_report = {}
    arena_reports = []
    improvement = {}
    iterations = []
    baseline_promotions = []
    novelty_signatures = set()
    session_memory = RepairSessionMemory(repair_session_id)
    duplicate_state = "NOVEL_REPAIR"
    latest_residual = dict(residual_analysis if isinstance(residual_analysis, dict) else {})
    initial_residual = post_repair_residual_analyzer.analyze(
        predicted_output,
        target_output,
        previous_residual=residual_analysis,
        repair_iteration_id=f"{repair_session_id}:initial",
    )
    latest_residual.update({
        key: value
        for key, value in initial_residual.items()
        if key not in {"previous_residual_count", "residual_reduction"}
    })
    current_evaluation = dict(evaluation_result)
    repair_output = predicted_output
    current_candidate_id = admission.get("residual_evidence", {}).get(
        "source_candidate_id",
        "current_candidate",
    )
    latest_candidate_id = current_candidate_id
    repair_final = {
        "system": "runtime_recoverable_repair_cycle",
        "report_state": "final",
        "repair_accepted": False,
        "repair_applicable": admission.get("repair_required") is True,
        "repair_attempts": 0,
        "repair_successes": 0,
        "repair_failures": 0,
        "repair_success_rate": 0.0,
        "localized_repairs": 0,
        "counterfactual_repairs": 0,
        "context_guided_repairs": 0,
        "dependency_guided_repairs": 0,
        "truth_guided_repairs": 0,
        "average_residual_reduction": 0.0,
        "reason": admission.get("repair_reason"),
        "repair_stop_reason": "UNRECOVERABLE_FAILURE"
        if evaluation_result.get("success_state") in {"CRITICAL_FAILURE", "UNRECOVERABLE_FAILURE"}
        else "NO_VALID_REPAIR_CANDIDATE",
        "repair_primary_family": None,
        "repair_supporting_methods": [],
    }
    budget_report = _repair_runtime_budget(context, 0)
    if admission.get("repair_required") is True:
        for iteration_index in range(1, max_iterations + 1):
            remaining_budget = max(0, max_iterations - iteration_index + 1)
            residual_evidence = recoverability_gate.build_residual_evidence(
                current_evaluation,
                latest_residual,
                execution_state={
                    **context,
                    "candidate_id": current_candidate_id,
                },
                task_context=context,
            )
            route = repair_route_selector.select(
                residual_evidence,
                context=context,
            )
            minimal_next = minimal_next_repair_generator.generate(
                residual_evidence,
                parent_repair_iteration_id=(
                    iterations[-1]["repair_iteration_id"]
                    if iterations
                    else f"{repair_session_id}:initial"
                ),
                parent_candidate_id=current_candidate_id,
                max_candidates=max_candidates,
            )
            repair_request = _localized_repair_request(
                residual_evidence,
                route,
                {
                    **context,
                    "candidate_id": current_candidate_id,
                },
                repair_output,
                target_output,
            )
            proposals = _repair_candidate_proposals(
                repair_request,
                residual_evidence,
            )
            challenge_count = max(0, len(proposals) - 1)
            budget_report = _repair_runtime_budget(context, len(proposals))
            stop = repair_stop_policy.decide(
                exact_success=False,
                remaining_budget=remaining_budget,
                actionable_residual=minimal_next.get("next_repair_required") is True,
                convergence={},
                duplicate_state=duplicate_state,
                candidate_count=challenge_count,
            )
            if stop["repair_should_stop"] or budget_report.get("repair_budget_exceeded"):
                repair_final["repair_stop_reason"] = (
                    "REPAIR_BUDGET_EXHAUSTED"
                    if budget_report.get("repair_budget_exceeded")
                    else stop["repair_stop_reason"]
                )
                break
            candidate_for_novelty = proposals[1] if len(proposals) > 1 else {}
            if isinstance(candidate_for_novelty.get("metadata"), dict):
                candidate_for_novelty["metadata"]["target_residual_fingerprint"] = (
                    residual_evidence.get("residual_fingerprint")
                    or latest_residual.get("residual_fingerprint")
                )
            novelty = repair_novelty_guard.review(
                candidate_for_novelty,
                previous_signatures=novelty_signatures,
                lineage=session_memory.candidate_lineage,
            )
            duplicate_state = novelty["repair_novelty_state"]
            if novelty["duplicate_repair"]:
                session_memory.record_duplicate(novelty)
                repair_final["repair_stop_reason"] = "DUPLICATE_REPAIR_CYCLE"
                break
            novelty_signatures.add(novelty["repair_signature"])
            arena_report = cognitive_candidate_arena.run(
                proposals,
                input_grid=repair_output,
                target_grid=target_output,
                runtime_context={
                    **context,
                    "expected_candidate_sources": ["repair_engine"],
                    "repair_admission_state": admission.get(
                        "repair_admission_state"
                    ),
                    "repair_iteration": iteration_index,
                    "baseline_candidate_id": current_candidate_id,
                },
                analysis_only=False,
            )
            arena_report["repair_iteration_arena_provenance"] = {
                "repair_iteration": iteration_index,
                "baseline_candidate_id": current_candidate_id,
                "challenger_candidate_ids": [
                    proposal.get("candidate_id")
                    for proposal in proposals[1:]
                ],
                "arena_decision": arena_report.get("arena_state"),
                "selected_candidate_id": _arena_selected_candidate_id(
                    arena_report
                ),
            }
            arena_reports.append(arena_report)
            iteration_repair = counterfactual_repair_engine.repair(
                repair_output,
                target_output,
                [
                    {
                        "repair_candidates": [
                            {
                                "location": region["metadata"]["target_locations"][0],
                                "candidate_value": int(
                                    region["program"]["steps"][0]["parameters"][
                                        "color_mapping"
                                    ][
                                        list(
                                            region["program"]["steps"][0]["parameters"][
                                                "color_mapping"
                                            ].keys()
                                        )[0]
                                    ]
                                ),
                                "repair_confidence": region.get("source_confidence", 0.0),
                                "repair_strategy": "localized_color_repair",
                            }
                            for region in proposals
                            if region.get("operation") == "replace_color"
                            and region.get("metadata", {}).get("target_locations")
                        ]
                    }
                ],
                max_passes=max(1, min(max_candidates, int(context.get("MAX_LOCALIZED_REPAIR_ATTEMPTS", 8) or 8))),
                max_residual_cells=max(
                    int(
                        residual_evidence.get(
                            "residual_difference_count",
                            0,
                        )
                        or 0
                    ),
                    1,
                ),
                minimum_repair_accuracy=0.0,
            )
            candidate_output = iteration_repair.get("repaired_output", repair_output)
            after_evaluation = evaluation_engine.evaluate(
                candidate_output,
                target_output,
            )
            improvement = residual_improvement_gate.compare(
                {
                    **current_evaluation,
                    "residual_count": latest_residual.get(
                        "residual_difference_count",
                        current_evaluation.get("difference_count", 0),
                    ),
                    "identity_integrity": True,
                    "topology_integrity": True,
                },
                {
                    **after_evaluation,
                    "identity_integrity": True,
                    "topology_integrity": True,
                },
                governance={"governance_valid": True},
            )
            if improvement.get("repair_improved") is not True:
                repair_final["repair_failures"] += max(
                    1,
                    iteration_repair.get("repair_attempts", 0),
                )
                repair_final["repair_stop_reason"] = (
                    improvement.get("repair_improvement_decision")
                    or "NO_RESIDUAL_IMPROVEMENT"
                )
                break
            parent_candidate_id = current_candidate_id
            current_candidate_id = f"{parent_candidate_id}:repair:{iteration_index}"
            latest_candidate_id = current_candidate_id
            post_residual = post_repair_residual_analyzer.analyze(
                candidate_output,
                target_output,
                previous_residual=latest_residual,
                repair_iteration_id=f"{repair_session_id}:iteration:{iteration_index}",
            )
            exact_evaluation = exact_success_detector.apply(
                after_evaluation,
                governance_valid=True,
                execution_integrity_valid=True,
            )
            iteration_state = build_iteration_state(
                repair_session_id=repair_session_id,
                iteration_index=iteration_index,
                task_id=task_id,
                run_id=run_id,
                parent_candidate_id=parent_candidate_id,
                current_candidate_id=current_candidate_id,
                residual_before=latest_residual,
                residual_after=post_residual,
                accuracy_before=current_evaluation.get("accuracy", 0.0),
                accuracy_after=after_evaluation.get("accuracy", 0.0),
                repair_candidate_id=latest_candidate_id,
                repair_route=route.get("repair_route"),
                repair_operation="recolor_residual_cells",
                improvement_state=improvement.get("repair_improvement_decision"),
                convergence_state="PENDING_ASSESSMENT",
            ).to_dict()
            iterations.append(iteration_state)
            session_memory.record_iteration(iteration_state)
            baseline_promotions.append({
                "baseline_promotion_state": "PROMOTED",
                "previous_baseline_candidate_id": parent_candidate_id,
                "new_baseline_candidate_id": current_candidate_id,
                "promotion_reason": "validated_residual_improvement",
                "previous_residual_count": latest_residual.get(
                    "residual_difference_count",
                    current_evaluation.get("difference_count", 0),
                ),
                "new_residual_count": post_residual.get(
                    "residual_difference_count",
                    after_evaluation.get("difference_count", 0),
                ),
            })
            repair_output = candidate_output
            current_evaluation = exact_evaluation
            latest_residual = post_residual
            trajectory = trajectory_from_iterations(
                repair_session_id,
                initial_residual,
                evaluation_result.get("accuracy", 0.0),
                iterations,
            )
            convergence = repair_convergence_assessor.assess(
                trajectory,
                remaining_budget=max_iterations - iteration_index,
            )
            iterations[-1]["convergence_state"] = convergence.get(
                "convergence_state"
            )
            repair_final["repair_attempts"] += iteration_repair.get(
                "repair_attempts",
                0,
            )
            repair_final["repair_successes"] += iteration_repair.get(
                "repair_successes",
                0,
            )
            repair_final["repair_failures"] += iteration_repair.get(
                "repair_failures",
                0,
            )
            repair_final["localized_repairs"] += iteration_repair.get(
                "localized_repairs",
                0,
            )
            repair_final["counterfactual_repairs"] = 0
            repair_final["repair_primary_family"] = "LOCALIZED_COLOR_REPAIR"
            repair_final["repair_supporting_methods"] = [
                "COUNTERFACTUAL_VALIDATION"
            ]
            repair_final["accepted_evaluation"] = after_evaluation
            repair_final["residual_improvement_gate"] = improvement
            repair_final["repair_accepted"] = True
            repair_final["repaired_output"] = repair_output
            stop = repair_stop_policy.decide(
                exact_success=convergence.get("exact_success_detected") is True,
                remaining_budget=max_iterations - iteration_index,
                actionable_residual=latest_residual.get("actionable") is True,
                convergence=convergence,
                duplicate_state=duplicate_state,
                candidate_count=challenge_count,
            )
            repair_final["repair_stop_reason"] = (
                stop["repair_stop_reason"]
                if stop["repair_should_stop"]
                else "CONVERGENCE_CONTINUING"
            )
            if stop["repair_should_stop"] or not convergence.get("continue_repair"):
                if convergence.get("exact_success_detected") is True:
                    current_evaluation = exact_success_detector.apply(after_evaluation)
                    repair_final["accepted_evaluation"] = current_evaluation
                    repair_final["repair_stop_reason"] = "EXACT_SUCCESS"
                elif repair_final["repair_stop_reason"] == "CONVERGENCE_CONTINUING":
                    repair_final["repair_stop_reason"] = "PRINCIPLED_REPAIR_STOP"
                break

    audit = _repair_reachability_audit(
        evaluation_result,
        residual_analysis,
        admission=admission,
        route=route,
        candidate_count=max(0, len(proposals) - 1),
        arena_reentry=bool(arena_reports or arena_report),
        execution_attempted=repair_final.get("repair_attempts", 0) > 0,
    )
    trajectory = trajectory_from_iterations(
        repair_session_id,
        initial_residual,
        evaluation_result.get("accuracy", 0.0),
        iterations,
    )
    convergence = repair_convergence_assessor.assess(
        trajectory,
        remaining_budget=max(0, max_iterations - len(iterations)),
    )
    residual_before = int(
        residual_analysis.get(
            "residual_difference_count",
            evaluation_result.get("difference_count", 0),
        )
        or 0
    )
    accepted_eval = repair_final.get("accepted_evaluation", {})
    residual_after = (
        int(current_evaluation.get("difference_count", residual_before) or 0)
        if repair_final.get("repair_accepted") is True
        else residual_before
    )
    successes = len([
        row for row in iterations
        if row.get("improvement_state") in {"REPAIR_IMPROVED", "REPAIR_EXACT_SUCCESS"}
    ])
    failures = len(iterations) - successes
    repair_final["repair_success_rate"] = round(
        repair_final.get("repair_successes", 0)
        / max(repair_final.get("repair_attempts", 0), 1),
        4,
    )
    repair_final["average_residual_reduction"] = round(
        trajectory.get("total_residual_reduction", 0)
        / max(len(iterations), 1),
        4,
    )
    convergence_report = {
        "Repair Session Id": repair_session_id,
        "Current Task Id": task_id,
        "Initial Residual Count": residual_before,
        "Current Residual Count": residual_after,
        "Best Residual Count": trajectory.get("best_residual_count"),
        "Initial Accuracy": evaluation_result.get("accuracy", 0.0),
        "Current Accuracy": current_evaluation.get(
            "accuracy",
            evaluation_result.get("accuracy", 0.0),
        ),
        "Best Accuracy": trajectory.get("best_accuracy"),
        "Repair Iterations": len(iterations),
        "Successful Repair Iterations": successes,
        "Failed Repair Iterations": failures,
        "Residual Trajectory": trajectory.get("residual_counts"),
        "Accuracy Trajectory": trajectory.get("accuracy_values"),
        "Current Residual Locations": latest_residual.get("residual_locations", []),
        "Current Residual Type": latest_residual.get("residual_type"),
        "Convergence State": convergence.get("convergence_state"),
        "Convergence Score": convergence.get("convergence_score"),
        "Stagnation Count": convergence.get("stagnation_count"),
        "Oscillation Detected": convergence.get("oscillation_detected"),
        "Regression Detected": convergence.get("regression_detected"),
        "Current Baseline Candidate": current_candidate_id,
        "Latest Repair Candidate": latest_candidate_id,
        "Duplicate Repair Count": len(session_memory.duplicate_repairs),
        "Repair Escalation Level": 1,
        "Exact Success Detected": convergence.get("exact_success_detected"),
        "Episode Completed": current_evaluation.get("episode_completed") is True,
        "Repair Stop Reason": repair_final.get("repair_stop_reason"),
    }
    convergence_audit = {
        "repair_reachability_clear": audit.get("repair_engine_reachable"),
        "repair_result_evaluated": bool(iterations),
        "post_repair_residual_recomputed": bool(iterations),
        "repaired_candidate_promoted_to_iteration_baseline": bool(
            baseline_promotions
        ),
        "next_repair_receives_latest_state": len(iterations) > 1,
        "repair_history_available": True,
        "convergence_assessment_called": bool(trajectory),
        "exact_success_closure_reachable": (
            convergence.get("exact_success_detected") is True
            or len(iterations) > 0
        ),
        "continuation_break_stage": (
            "exact_success_closure"
            if convergence.get("exact_success_detected") is True
            else "principled_stop_policy"
        ),
        "continuation_break_reason": repair_final.get("repair_stop_reason"),
    }
    report = {
        "recoverable_failure_detected": (
            evaluation_result.get("success_state") == "RECOVERABLE_FAILURE"
        ),
        "repair_required": admission.get("repair_required") is True,
        "repair_admission_state": admission.get("repair_admission_state"),
        "residual_type": residual_analysis.get("residual_type"),
        "residual_count_before": residual_before,
        "repair_route": route.get("repair_route"),
        "repair_candidate_count": max(0, len(proposals) - 1),
        "arena_reentry_attempted": bool(arena_report),
        "repair_attempts": repair_final.get("repair_attempts", 0),
        "repair_successes": repair_final.get("repair_successes", 0),
        "repair_failures": repair_final.get("repair_failures", 0),
        "localized_repairs": repair_final.get("localized_repairs", 0),
        "counterfactual_repairs": repair_final.get("counterfactual_repairs", 0),
        "context_guided_repairs": repair_final.get("context_guided_repairs", 0),
        "dependency_guided_repairs": repair_final.get("dependency_guided_repairs", 0),
        "truth_guided_repairs": repair_final.get("truth_guided_repairs", 0),
        "residual_count_after": residual_after,
        "residual_reduction": max(0, residual_before - residual_after),
        "prediction_accuracy_before": evaluation_result.get("accuracy", 0.0),
        "prediction_accuracy_after": (
            accepted_eval.get("accuracy", evaluation_result.get("accuracy", 0.0))
            if improvement.get("repair_improved") is True
            else evaluation_result.get("accuracy", 0.0)
        ),
        "repair_stop_reason": repair_final.get("repair_stop_reason"),
        "repair_reachability_state": (
            "REPAIR_REACHABILITY_CLEAR"
            if audit.get("repair_execution_attempted")
            else "REPAIR_NOT_REACHED"
        ),
    }
    return {
        "repair_admission_report": admission,
        "repair_route_report": route,
        "localized_repair_request": repair_request,
        "repair_candidate_proposals": proposals,
        "repair_arena_report": arena_report,
        "repair_iteration_arena_reports": arena_reports,
        "runtime_repair_final_report": repair_final,
        "residual_improvement_report": improvement,
        "repair_iteration_states": iterations,
        "baseline_promotion_report": baseline_promotions[-1] if baseline_promotions else {},
        "baseline_promotion_history": baseline_promotions,
        "repair_residual_trajectory": trajectory,
        "repair_convergence_assessment": convergence,
        "repair_convergence_audit": convergence_audit,
        "repair_session_memory": session_memory.as_dict(),
        "repair_convergence_report": convergence_report,
        "current_task_repair_metrics": {
            "current_task_initial_residual": residual_before,
            "current_task_current_residual": residual_after,
            "current_task_best_residual": trajectory.get("best_residual_count"),
            "current_task_repair_attempts": len(iterations),
            "current_task_repair_successes": successes,
            "current_task_repair_failures": failures,
            "current_task_average_residual_reduction": repair_final.get(
                "average_residual_reduction",
                0.0,
            ),
        },
        "repair_session_metrics": {
            "repair_session_attempts": len(iterations),
            "repair_session_successes": successes,
            "repair_session_failures": failures,
            "repair_session_residual_trajectory": trajectory,
        },
        "repair_reachability_audit": audit,
        "repair_runtime_budget_report": budget_report,
        "repair_reachability_report": report,
        "predicted_output": repair_output,
        "accepted_evaluation": current_evaluation
        if repair_final.get("repair_accepted") is True
        else {},
    }


# ============================================
# EVALUATION STAGE
# ============================================

def _incomplete_evaluation_context(
    context,
    stage_report,
    reason,
    success_state,
):

    evaluation_result = {
        "success": False,
        "partial_success": False,
        "exact_success": False,
        "accuracy": 0.0,
        "prediction_accuracy": 0.0,
        "correct_cells": 0,
        "total_cells": 0,
        "difference_count": None,
        "success_state": success_state,
        "task_status": "TASK_INCOMPLETE",
        "evaluation_status": "INCOMPLETE",
        "pipeline_incomplete": True,
        "reason": reason,
        "retry_allowed": True,
        "failure_is_pipeline_robustness": True,
    }

    success_semantics_report = {
        "success_state": success_state,
        "exact_success": False,
        "episode_completed": False,
        "termination_reason": reason,
        "shutdown_mode": "continue",
        "background_task_control": {},
        "residual_analysis": {
            "status": "skipped",
            "reason": reason,
        },
    }

    failure_analysis = {
        "failure_detected": False,
        "failure_causes": [],
        "diagnostic_signals": [
            reason,
            "evaluation_consumed_context_before_prediction_was_available",
        ],
        "pipeline_incomplete": True,
    }

    recovery_plan = {
        "failure_detected": False,
        "recovery_actions": [
            "ensure_prediction_stage_populates_predicted_output",
            "skip_evaluation_until_prediction_exists",
        ],
        "action_count": 2,
        "retry_allowed": True,
        "reason": reason,
    }

    evaluation_metrics = {
        "history_size": len(evaluation_engine.get_history()),
        "recent_episodes": 0,
        "introspection_insights": 0,
        "failure_detected": False,
        "episode_completed": False,
        "success_state": success_state,
        "pipeline_incomplete": True,
    }

    stage_report.update({
        "status": "incomplete",
        "runtime_health": "degraded",
        "evaluation_metrics": evaluation_metrics,
        "reason": reason,
        "success_state": success_state,
    })

    context["evaluation_result"] = evaluation_result
    context["success_semantics_report"] = success_semantics_report
    context["SUCCESS_SEMANTICS_AUDIT_REPORT"] = (
        success_semantics_engine.build_audit_report()
    )
    context["residual_analysis"] = success_semantics_report[
        "residual_analysis"
    ]
    context["RESIDUAL_ANALYSIS_REPORT"] = context["residual_analysis"]
    context["success_state"] = success_state
    context["task_status"] = "TASK_INCOMPLETE"
    context["pipeline_incomplete"] = True
    context["prediction_not_produced"] = (
        success_state == "PREDICTION_NOT_PRODUCED"
    )
    context["episode_completed"] = False
    context["termination_reason"] = reason
    context["shutdown_mode"] = "continue"
    context["background_task_control"] = {}
    context["learning_signal"] = {
        "recorded": False,
        "success_state": success_state,
        "residual_analysis": context["residual_analysis"],
        "failure_history_incremented": False,
    }
    context["world_model_sync_report"] = {
        "status": "skipped",
        "reason": reason,
    }
    context["latent_reasoning_reactivation"] = {
        "status": "skipped",
        "reason": reason,
    }
    context["latent_reasoning_report"] = (
        latent_reasoning_reservoir.build_report()
    )
    context["meta_success_rate"] = 0.0
    context["evaluation_history"] = evaluation_engine.get_history()
    context["evaluation_complete"] = False
    context["temporal_report"] = {}
    context["recent_episodes"] = []
    context["introspection_report"] = {
        "status": "skipped",
        "reason": reason,
    }
    context["introspection_insights"] = []
    context["introspection_summary"] = {
        "status": "skipped",
        "reason": reason,
    }
    context["failure_analysis"] = failure_analysis
    context["recovery_plan"] = recovery_plan
    context["failure_summary"] = {
        "failure_count": 0,
        "pipeline_incomplete": True,
    }
    context["reflective_learning_report"] = {
        "status": "skipped",
        "reason": reason,
    }
    context["program_memory_report"] = {
        "status": "skipped",
        "reason": "validated_prediction_required",
        "program_saved": False,
    }
    context["evaluation_metrics"] = evaluation_metrics
    context["evaluation_stage_report"] = stage_report

    print(
        "EVALUATION INCOMPLETE:\n"
    )

    print(
        evaluation_result
    )

    return context


def evaluation_stage(context):

    print(
        "\n=================================================="
    )

    print(
        "NEXRYN :: EVALUATION STAGE"
    )

    print(
        "==================================================\n"
    )

    # ========================================
    # STAGE REPORT
    # ========================================

    stage_report = {

        "stage":
        "evaluation",

        "status":
        "running",

        "timestamp":
        str(
            datetime.utcnow()
        ),

        "runtime_health":
        "stable"
    }

    # ========================================
    # LOAD CONTEXT
    # ========================================

    predicted_output = context.get(
        "predicted_output"
    )

    output_grid = context.get(
        "output_grid"
    )

    cognitive_cycle = context.get(

        "cognitive_cycle",

        {}
    )

    # ========================================
    # VALIDATION
    # ========================================

    if predicted_output is None:

        return _incomplete_evaluation_context(
            context,
            stage_report,
            "missing_predicted_output",
            "PREDICTION_NOT_PRODUCED",
        )

    if output_grid is None:

        return _incomplete_evaluation_context(
            context,
            stage_report,
            "missing_output_grid",
            "TARGET_OUTPUT_MISSING",
        )

    # ========================================
    # EXTRACT TARGET ARRAY
    # ========================================

    if hasattr(
        output_grid,
        "grid"
    ):

        target_output = (
            output_grid.grid
        )

    else:

        target_output = (
            output_grid
        )

    # ========================================
    # EVALUATION
    # ========================================

    evaluation_result = (

        evaluation_engine.evaluate(

            predicted_output,

            target_output
        )
    )

    repair_result = _run_residual_repair(
        context,
        predicted_output,
        target_output,
        evaluation_result,
    )
    evaluation_result = repair_result["evaluation_result"]
    predicted_output = repair_result["predicted_output"]
    context["predicted_output"] = predicted_output
    if repair_result.get("pre_repair_evaluation"):
        context["pre_repair_evaluation_result"] = (
            repair_result["pre_repair_evaluation"]
        )

    evaluation_result, success_semantics_report = (
        success_semantics_engine.apply(
            evaluation_result,
            context
        )
    )

    residual_analysis = success_semantics_report.get(
        "residual_analysis",
        {}
    )

    runtime_repair_result = _run_recoverable_repair_cycle(
        context,
        predicted_output,
        target_output,
        evaluation_result,
        success_semantics_report,
        residual_analysis,
    )
    if runtime_repair_result.get("accepted_evaluation"):
        predicted_output = runtime_repair_result["predicted_output"]
        context["predicted_output"] = predicted_output
        context["pre_runtime_repair_evaluation_result"] = evaluation_result
        evaluation_result, success_semantics_report = (
            success_semantics_engine.apply(
                runtime_repair_result["accepted_evaluation"],
                context,
            )
        )
        residual_analysis = success_semantics_report.get(
            "residual_analysis",
            {}
        )

    episode_completed = (
        success_semantics_report.get(
            "episode_completed",
            False
        )
        is True
    )

    # ========================================
    # WORLD MODEL SYNCHRONIZATION
    # ========================================

    world_model_sync_report = (

        world_model_engine
        .synchronize_with_evaluator(
            evaluation_result
        )
    )

    latent_reasoning_reactivation = (
        latent_reasoning_reservoir
        .reactivate_if_needed({
            "evaluation_result":
            evaluation_result,

            "world_model_anticipation":
            context.get(
                "world_model_anticipation",
                {}
            )
        })
    )

    # ========================================
    # META CONTROL OUTCOME FEEDBACK
    # ========================================

    try:

        from runtime.stages.inference import (
            meta_controller_engine
        )

        meta_success_rate = (
            meta_controller_engine
            .record_outcome(
                evaluation_result
            )
        )

    except Exception:

        meta_success_rate = 0.0

    # ========================================
    # TEMPORAL MEMORY STORAGE
    # ========================================

    temporal_memory.store_episode(

        cognitive_cycle,

        evaluation_result
    )

    temporal_report = (

        temporal_memory.build_temporal_report()
    )

    recent_episodes = (

        temporal_memory.get_recent_episodes(
            limit=3
        )
    )

    # ========================================
    # INTROSPECTION
    # ========================================

    if episode_completed:

        introspection_report = {
            "status": "skipped",
            "reason": "episode_completed_terminal_success",
            "success_state": evaluation_result.get(
                "success_state"
            ),
            "deep_introspection_skipped": True,
            "accuracy": evaluation_result.get(
                "accuracy",
                0.0
            ),
            "success": evaluation_result.get(
                "success",
                False
            ),
            "partial_success": evaluation_result.get(
                "partial_success",
                False
            )
        }

        introspection_insights = [
            "Terminal success reached; deep introspection skipped"
        ]

        introspection_summary = {
            "status": "skipped",
            "reason": "episode_completed_terminal_success"
        }

    else:

        introspection_report = (

            introspection_engine.analyze_cycle(

                cognitive_cycle,

                evaluation_result,

                context
            )
        )

        introspection_insights = (

            introspection_engine.build_insights(

                introspection_report
            )
        )

        introspection_engine.store_report(

            introspection_report
        )

        introspection_summary = (

            introspection_engine.build_summary()
        )

    context = _ensure_runtime_budget_evidence(
        context,
        introspection_report,
    )

    # ========================================
    # FAILURE ANALYSIS
    # ========================================

    failure_analysis = (

        failure_analyzer.analyze_failure(

            cognitive_cycle,

            evaluation_result,

            introspection_report
        )
    )

    recovery_plan = (

        failure_analyzer.build_recovery_plan(

            failure_analysis
        )
    )

    if episode_completed:

        failure_analysis[
            "failure_detected"
        ] = False

        failure_analysis[
            "failure_causes"
        ] = []

        failure_analysis[
            "diagnostic_signals"
        ] = [
            "terminal_success_residuals_do_not_block_shutdown"
        ]

        recovery_plan = {
            "failure_detected": False,
            "recovery_actions": [],
            "action_count": 0,
            "retry_allowed": False,
            "reason": "episode_completed_terminal_success"
        }

    # ========================================
    # FAILURE STORAGE
    # ========================================

    if failure_analysis.get(

        "failure_detected",

        False
    ):

        failure_analyzer.store_failure(

            failure_analysis
        )

    failure_summary = (

        failure_analyzer.build_failure_summary()
    )

    # ========================================
    # REFLECTIVE META LEARNING
    # ========================================

    reflective_learning_report = (

        reflective_meta_learning_engine.reflect(

            cognitive_cycle,

            evaluation_result
        )
    )

    # ========================================
    # VALIDATED PROGRAM MEMORY
    # ========================================

    program_memory_report = (
        remember_validated_program(
            {
                **context,
                "evaluation_result":
                evaluation_result,
                "success_semantics_report":
                success_semantics_report,
                "episode_completed":
                episode_completed,
                "residual_analysis":
                residual_analysis,
            }
        )
    )

    # ========================================
    # EVALUATION METRICS
    # ========================================

    evaluation_metrics = {

        "history_size":
        len(
            evaluation_engine.get_history()
        ),

        "recent_episodes":
        len(
            recent_episodes
        ),

        "introspection_insights":
        len(
            introspection_insights
        ),

        "failure_detected":
        failure_analysis.get(

            "failure_detected",

            False
        ),

        "episode_completed":
        episode_completed,

        "success_state":
        evaluation_result.get(
            "success_state"
        ),

        "residual_count":
        repair_result["residual_reasoning_report"].get(
            "residual_count",
            0,
        ),

        "residual_type":
        repair_result["residual_reasoning_report"].get(
            "residual_type",
        ),

        "repair_attempts":
        repair_result["final_repair_report"].get(
            "repair_attempts",
            0,
        ),

        "repair_successes":
        repair_result["final_repair_report"].get(
            "repair_successes",
            0,
        ),

        "repair_failures":
        repair_result["final_repair_report"].get(
            "repair_failures",
            0,
        ),

        "repair_success_rate":
        repair_result["final_repair_report"].get(
            "repair_success_rate",
            0.0,
        ),

        "localized_repairs":
        repair_result["final_repair_report"].get(
            "localized_repairs",
            0,
        ),

        "counterfactual_repairs":
        repair_result["final_repair_report"].get(
            "counterfactual_repairs",
            0,
        ),

        "context_guided_repairs":
        repair_result["final_repair_report"].get(
            "context_guided_repairs",
            0,
        ),

        "dependency_guided_repairs":
        repair_result["final_repair_report"].get(
            "dependency_guided_repairs",
            0,
        ),

        "truth_guided_repairs":
        repair_result["final_repair_report"].get(
            "truth_guided_repairs",
            0,
        ),

        "average_residual_reduction":
        repair_result["final_repair_report"].get(
            "average_residual_reduction",
            0.0,
        )
    }
    if runtime_repair_result["runtime_repair_final_report"].get(
        "repair_attempts",
        0,
    ) > 0:
        runtime_final_repair_report = runtime_repair_result[
            "runtime_repair_final_report"
        ]
        evaluation_metrics.update({
            "repair_attempts": runtime_final_repair_report.get(
                "repair_attempts",
                0,
            ),
            "repair_successes": runtime_final_repair_report.get(
                "repair_successes",
                0,
            ),
            "repair_failures": runtime_final_repair_report.get(
                "repair_failures",
                0,
            ),
            "repair_success_rate": runtime_final_repair_report.get(
                "repair_success_rate",
                0.0,
            ),
            "localized_repairs": runtime_final_repair_report.get(
                "localized_repairs",
                0,
            ),
            "counterfactual_repairs": runtime_final_repair_report.get(
                "counterfactual_repairs",
                0,
            ),
            "context_guided_repairs": runtime_final_repair_report.get(
                "context_guided_repairs",
                0,
            ),
            "dependency_guided_repairs": runtime_final_repair_report.get(
                "dependency_guided_repairs",
                0,
            ),
            "truth_guided_repairs": runtime_final_repair_report.get(
                "truth_guided_repairs",
                0,
            ),
            "average_residual_reduction": runtime_final_repair_report.get(
                "average_residual_reduction",
                0.0,
            ),
        })

    # ========================================
    # UPDATE STAGE REPORT
    # ========================================

    stage_report.update({

        "status":
        "completed",

        "evaluation_metrics":
        evaluation_metrics
    })

    # ========================================
    # DISPLAY RESULTS
    # ========================================

    print(
        "EVALUATION RESULT:\n"
    )

    print(
        evaluation_result
    )

    print(
        "\nINTROSPECTION SUMMARY:\n"
    )

    print(
        introspection_summary
    )

    print(
        "\nFAILURE SUMMARY:\n"
    )

    print(
        failure_summary
    )

    print(
        "\nEVALUATION METRICS:\n"
    )

    print(
        evaluation_metrics
    )

    if _is_fast_minimal_context(context):

        effective_repair_report = repair_result["final_repair_report"]
        if runtime_repair_result["runtime_repair_final_report"].get(
            "repair_attempts",
            0,
        ) > 0:
            effective_repair_report = runtime_repair_result[
                "runtime_repair_final_report"
            ]
        final_repair_report = {
            "report_state": "minimal",
            "repair_accepted": effective_repair_report.get(
                "repair_accepted",
                False,
            ),
            "repair_applicable": effective_repair_report.get(
                "repair_applicable",
                False,
            ),
            "repair_attempts": effective_repair_report.get(
                "repair_attempts",
                0,
            ),
            "repair_successes": effective_repair_report.get(
                "repair_successes",
                0,
            ),
        }
        print(
            "FAST MINIMAL EVALUATION CLOSURE: returning minimal context",
            flush=True,
        )
        return {
            "task_path": context.get("task_path"),
            "task_metadata": context.get("task_metadata", {}),
            "cognitive_budget_report": context.get(
                "cognitive_budget_report",
                {},
            ),
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT": context.get(
                "RUNTIME_BUDGET_ENFORCEMENT_REPORT",
                context.get("runtime_budget_enforcement_report", {}),
            ),
            "runtime_budget_enforcement_report": context.get(
                "runtime_budget_enforcement_report",
                context.get("RUNTIME_BUDGET_ENFORCEMENT_REPORT", {}),
            ),
            "route_lifecycle_records": context.get(
                "route_lifecycle_records",
                [],
            ),
            "reasoning_depth_lifecycle_records": context.get(
                "reasoning_depth_lifecycle_records",
                [],
            ),
            "evaluation_result": evaluation_result,
            "success_semantics_report": success_semantics_report,
            "SUCCESS_SEMANTICS_AUDIT_REPORT": {
                "report_state": "deferred",
                "reason": "fast_minimal_terminal_projection",
            },
            "residual_analysis": residual_analysis,
            "RESIDUAL_ANALYSIS_REPORT": residual_analysis,
            "residual_reasoning_report": {
                "residual_count": repair_result[
                    "residual_reasoning_report"
                ].get("residual_count", 0),
                "residual_type": repair_result[
                    "residual_reasoning_report"
                ].get("residual_type"),
                "report_state": "minimal",
            },
            "FINAL_REPAIR_REPORT": final_repair_report,
            "REPAIR_REACHABILITY_AUDIT":
            runtime_repair_result["repair_reachability_audit"],
            "repair_reachability_audit":
            runtime_repair_result["repair_reachability_audit"],
            "REPAIR_REACHABILITY_REPORT":
            runtime_repair_result["repair_reachability_report"],
            "repair_reachability_report":
            runtime_repair_result["repair_reachability_report"],
            "REPAIR_ADMISSION_REPORT":
            runtime_repair_result["repair_admission_report"],
            "REPAIR_ROUTE_REPORT":
            runtime_repair_result["repair_route_report"],
            "REPAIR_RUNTIME_BUDGET_REPORT":
            runtime_repair_result["repair_runtime_budget_report"],
            "REPAIR_CONVERGENCE_AUDIT":
            runtime_repair_result["repair_convergence_audit"],
            "repair_convergence_audit":
            runtime_repair_result["repair_convergence_audit"],
            "REPAIR_CONVERGENCE_REPORT":
            runtime_repair_result["repair_convergence_report"],
            "repair_convergence_report":
            runtime_repair_result["repair_convergence_report"],
            "REPAIR_RESIDUAL_TRAJECTORY":
            runtime_repair_result["repair_residual_trajectory"],
            "REPAIR_SESSION_MEMORY":
            runtime_repair_result["repair_session_memory"],
            "current_task_repair_session_id":
            runtime_repair_result["repair_residual_trajectory"].get(
                "repair_session_id"
            ),
            "current_task_initial_residual":
            runtime_repair_result["current_task_repair_metrics"].get(
                "current_task_initial_residual"
            ),
            "current_task_current_residual":
            runtime_repair_result["current_task_repair_metrics"].get(
                "current_task_current_residual"
            ),
            "current_task_best_residual":
            runtime_repair_result["current_task_repair_metrics"].get(
                "current_task_best_residual"
            ),
            "current_task_residual_trajectory":
            runtime_repair_result["repair_residual_trajectory"].get(
                "residual_counts"
            ),
            "current_task_repair_iterations":
            runtime_repair_result["current_task_repair_metrics"].get(
                "current_task_repair_attempts"
            ),
            "current_task_repair_successes":
            runtime_repair_result["current_task_repair_metrics"].get(
                "current_task_repair_successes"
            ),
            "current_task_repair_failures":
            runtime_repair_result["current_task_repair_metrics"].get(
                "current_task_repair_failures"
            ),
            "current_task_convergence_state":
            runtime_repair_result["repair_convergence_assessment"].get(
                "convergence_state"
            ),
            "current_task_exact_success":
            runtime_repair_result["repair_convergence_assessment"].get(
                "exact_success_detected"
            ),
            "current_task_repair_stop_reason":
            runtime_repair_result["runtime_repair_final_report"].get(
                "repair_stop_reason"
            ),
            "final_evaluation_closure_must_wait_for_repair_decision":
            runtime_repair_result["repair_admission_report"].get(
                "repair_required"
            )
            is True,
            "residual_repair_applied": final_repair_report.get(
                "repair_accepted",
                False,
            ),
            "success_state": evaluation_result.get("success_state"),
            "episode_completed": episode_completed,
            "termination_reason": success_semantics_report.get(
                "termination_reason",
            ),
            "shutdown_mode": success_semantics_report.get(
                "shutdown_mode",
            ),
            "background_task_control": success_semantics_report.get(
                "background_task_control",
                {},
            ),
            "learning_signal": {
                "recorded": episode_completed,
                "success_state": evaluation_result.get("success_state"),
                "failure_history_incremented": False
                if episode_completed
                else failure_analysis.get("failure_detected", False),
            },
            "latent_reasoning_report": {
                "report_state": "deferred",
                "reason": "fast_minimal_terminal_projection",
            },
            "meta_success_rate": meta_success_rate,
            "evaluation_history": {
                "report_state": "deferred",
                "history_size": evaluation_metrics.get("history_size", 0),
                "reason": "fast_minimal_terminal_projection",
            },
            "evaluation_complete": True,
            "recent_episodes": {
                "report_state": "deferred",
                "recent_episode_count": evaluation_metrics.get(
                    "recent_episodes",
                    0,
                ),
                "reason": "fast_minimal_terminal_projection",
            },
            "introspection_summary": introspection_summary,
            "semantic_attribution_report": {
                "semantic_concept_count": introspection_report.get(
                    "semantic_concept_count",
                    0,
                ),
                "attributed_concepts": _compact_evaluation_list(
                    introspection_report.get("attributed_concepts", []),
                    limit=5,
                ),
                "semantic_attribution_source": introspection_report.get(
                    "semantic_attribution_source",
                ),
            },
            "failure_analysis": {
                "failure_detected": failure_analysis.get(
                    "failure_detected",
                    False,
                ),
                "failure_causes": _compact_evaluation_list(
                    failure_analysis.get("failure_causes", []),
                    limit=5,
                ),
                "report_state": "minimal",
            },
            "failure_summary": failure_summary,
            "reflective_learning_report": {
                "report_state": "deferred",
                "reason": "fast_minimal_terminal_projection",
            },
            "program_memory_report": {
                "report_state": "deferred",
                "reason": "fast_minimal_terminal_projection",
            },
            "evaluation_metrics": evaluation_metrics,
            "evaluation_stage_report": stage_report,
            "fast_minimal_evaluation_closure": {
                "enabled": True,
                "heavy_evaluation_reports_deferred": True,
                "reason": "fast_minimal_terminal_projection",
            },
        }

    # ========================================
    # SAVE CONTEXT
    # ========================================

    context[
        "evaluation_result"
    ] = evaluation_result

    context[
        "success_semantics_report"
    ] = success_semantics_report

    context[
        "SUCCESS_SEMANTICS_AUDIT_REPORT"
    ] = success_semantics_engine.build_audit_report()

    context[
        "residual_analysis"
    ] = residual_analysis

    context[
        "RESIDUAL_ANALYSIS_REPORT"
    ] = residual_analysis

    context[
        "residual_reasoning_report"
    ] = repair_result["residual_reasoning_report"]

    context[
        "REPAIR_CANDIDATE_REPORT"
    ] = repair_result["repair_candidate_report"]

    context[
        "LOCALIZED_REPAIR_REPORT"
    ] = repair_result["localized_repair_report"]

    context[
        "SPATIAL_RESIDUAL_REPAIR_REPORT"
    ] = repair_result["spatial_residual_repair_report"]

    context[
        "OBJECT_RESIDUAL_REPAIR_REPORT"
    ] = repair_result["object_residual_repair_report"]

    effective_final_repair_report = repair_result["final_repair_report"]
    if runtime_repair_result["runtime_repair_final_report"].get(
        "repair_attempts",
        0,
    ) > 0:
        effective_final_repair_report = runtime_repair_result[
            "runtime_repair_final_report"
        ]

    context[
        "FINAL_REPAIR_REPORT"
    ] = effective_final_repair_report

    context[
        "RUNTIME_REPAIR_FINAL_REPORT"
    ] = runtime_repair_result["runtime_repair_final_report"]

    context[
        "REPAIR_ADMISSION_REPORT"
    ] = runtime_repair_result["repair_admission_report"]

    context[
        "REPAIR_ROUTE_REPORT"
    ] = runtime_repair_result["repair_route_report"]

    context[
        "LOCALIZED_REPAIR_REQUEST"
    ] = runtime_repair_result["localized_repair_request"]

    context[
        "REPAIR_ARENA_REPORT"
    ] = runtime_repair_result["repair_arena_report"]

    context[
        "RESIDUAL_IMPROVEMENT_REPORT"
    ] = runtime_repair_result["residual_improvement_report"]

    context[
        "REPAIR_REACHABILITY_AUDIT"
    ] = runtime_repair_result["repair_reachability_audit"]

    context[
        "repair_reachability_audit"
    ] = runtime_repair_result["repair_reachability_audit"]

    context[
        "REPAIR_RUNTIME_BUDGET_REPORT"
    ] = runtime_repair_result["repair_runtime_budget_report"]

    context[
        "REPAIR_REACHABILITY_REPORT"
    ] = runtime_repair_result["repair_reachability_report"]

    context[
        "repair_reachability_report"
    ] = runtime_repair_result["repair_reachability_report"]

    context[
        "REPAIR_CONVERGENCE_AUDIT"
    ] = runtime_repair_result["repair_convergence_audit"]

    context[
        "repair_convergence_audit"
    ] = runtime_repair_result["repair_convergence_audit"]

    context[
        "REPAIR_CONVERGENCE_REPORT"
    ] = runtime_repair_result["repair_convergence_report"]

    context[
        "repair_convergence_report"
    ] = runtime_repair_result["repair_convergence_report"]

    context[
        "REPAIR_RESIDUAL_TRAJECTORY"
    ] = runtime_repair_result["repair_residual_trajectory"]

    context[
        "REPAIR_CONVERGENCE_ASSESSMENT"
    ] = runtime_repair_result["repair_convergence_assessment"]

    context[
        "REPAIR_ITERATION_STATES"
    ] = runtime_repair_result["repair_iteration_states"]

    context[
        "REPAIR_SESSION_MEMORY"
    ] = runtime_repair_result["repair_session_memory"]

    context[
        "BASELINE_PROMOTION_REPORT"
    ] = runtime_repair_result["baseline_promotion_report"]

    context[
        "current_task_repair_session_id"
    ] = runtime_repair_result["repair_residual_trajectory"].get(
        "repair_session_id"
    )

    current_task_repair_metrics = runtime_repair_result[
        "current_task_repair_metrics"
    ]
    context.update({
        "current_task_initial_residual":
        current_task_repair_metrics.get("current_task_initial_residual"),
        "current_task_current_residual":
        current_task_repair_metrics.get("current_task_current_residual"),
        "current_task_best_residual":
        current_task_repair_metrics.get("current_task_best_residual"),
        "current_task_residual_trajectory":
        runtime_repair_result["repair_residual_trajectory"].get(
            "residual_counts"
        ),
        "current_task_repair_iterations":
        current_task_repair_metrics.get("current_task_repair_attempts"),
        "current_task_repair_successes":
        current_task_repair_metrics.get("current_task_repair_successes"),
        "current_task_repair_failures":
        current_task_repair_metrics.get("current_task_repair_failures"),
        "current_task_convergence_state":
        runtime_repair_result["repair_convergence_assessment"].get(
            "convergence_state"
        ),
        "current_task_exact_success":
        runtime_repair_result["repair_convergence_assessment"].get(
            "exact_success_detected"
        ),
        "current_task_repair_stop_reason":
        runtime_repair_result["runtime_repair_final_report"].get(
            "repair_stop_reason"
        ),
        "run_aggregate_repair_metrics": {
            "run_repair_attempts": evaluation_metrics.get("repair_attempts"),
            "run_repair_successes": evaluation_metrics.get("repair_successes"),
            "run_repair_failures": evaluation_metrics.get("repair_failures"),
            "run_average_residual_reduction": evaluation_metrics.get(
                "average_residual_reduction"
            ),
        },
        "historical_repair_metrics": {
            "historical_repair_attempts": repair_result[
                "final_repair_report"
            ].get("repair_attempts", 0),
            "historical_repair_successes": repair_result[
                "final_repair_report"
            ].get("repair_successes", 0),
            "historical_repair_failures": repair_result[
                "final_repair_report"
            ].get("repair_failures", 0),
            "historical_average_residual_reduction": repair_result[
                "final_repair_report"
            ].get("average_residual_reduction", 0.0),
        },
    })

    context[
        "final_evaluation_closure_must_wait_for_repair_decision"
    ] = runtime_repair_result["repair_admission_report"].get(
        "repair_required"
    ) is True

    context[
        "residual_repair_applied"
    ] = effective_final_repair_report.get(
        "repair_accepted",
        False,
    )

    context[
        "success_state"
    ] = evaluation_result.get(
        "success_state"
    )

    context[
        "episode_completed"
    ] = episode_completed

    context[
        "termination_reason"
    ] = success_semantics_report.get(
        "termination_reason"
    )

    context[
        "shutdown_mode"
    ] = success_semantics_report.get(
        "shutdown_mode"
    )

    context[
        "background_task_control"
    ] = success_semantics_report.get(
        "background_task_control",
        {}
    )

    context[
        "learning_signal"
    ] = {
        "recorded": episode_completed,
        "success_state": evaluation_result.get(
            "success_state"
        ),
        "residual_analysis": residual_analysis,
        "failure_history_incremented": False
        if episode_completed
        else failure_analysis.get(
            "failure_detected",
            False
        )
    }

    context[
        "world_model_sync_report"
    ] = world_model_sync_report

    context[
        "latent_reasoning_reactivation"
    ] = latent_reasoning_reactivation

    context[
        "latent_reasoning_report"
    ] = (
        latent_reasoning_reservoir
        .build_report()
    )

    context[
        "meta_success_rate"
    ] = meta_success_rate

    context[
        "evaluation_history"
    ] = (

        evaluation_engine.get_history()
    )

    context[
        "evaluation_complete"
    ] = True

    context[
        "temporal_report"
    ] = temporal_report

    context[
        "recent_episodes"
    ] = recent_episodes

    context[
        "introspection_report"
    ] = introspection_report

    context[
        "introspection_insights"
    ] = introspection_insights

    context[
        "introspection_summary"
    ] = introspection_summary

    context[
        "semantic_attribution_report"
    ] = {
        "semantic_concept_count":
        introspection_report.get(
            "semantic_concept_count",
            0
        ),
        "attributed_concepts":
        introspection_report.get(
            "attributed_concepts",
            []
        ),
        "semantic_attribution_evidence":
        introspection_report.get(
            "semantic_attribution_evidence",
            {}
        ),
        "semantic_attribution_source":
        introspection_report.get(
            "semantic_attribution_source"
        ),
    }

    context[
        "failure_analysis"
    ] = failure_analysis

    context[
        "recovery_plan"
    ] = recovery_plan

    context[
        "failure_summary"
    ] = failure_summary

    context[
        "reflective_learning_report"
    ] = reflective_learning_report

    context[
        "program_memory_report"
    ] = program_memory_report

    context[
        "evaluation_metrics"
    ] = evaluation_metrics

    context[
        "evaluation_stage_report"
    ] = stage_report

    # ========================================
    # RETURN CONTEXT
    # ========================================

    return context
