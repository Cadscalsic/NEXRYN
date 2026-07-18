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

        final_repair_report = {
            "report_state": "minimal",
            "repair_accepted": repair_result[
                "final_repair_report"
            ].get("repair_accepted", False),
            "repair_attempts": repair_result[
                "final_repair_report"
            ].get("repair_attempts", 0),
            "repair_successes": repair_result[
                "final_repair_report"
            ].get("repair_successes", 0),
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

    context[
        "FINAL_REPAIR_REPORT"
    ] = repair_result["final_repair_report"]

    context[
        "residual_repair_applied"
    ] = repair_result["final_repair_report"].get(
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
