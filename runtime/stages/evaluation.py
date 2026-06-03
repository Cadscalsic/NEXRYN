# ============================================
# NEXRYN EVALUATION STAGE
# ============================================

from datetime import datetime

from runtime.evaluation.evaluation_engine import (
    UnifiedEvaluationEngine
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

from runtime.memory import (
    latent_reasoning_reservoir
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


# ============================================
# EVALUATION STAGE
# ============================================

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

        raise ValueError(
            "Missing predicted_output"
        )

    if output_grid is None:

        raise ValueError(
            "Missing output_grid"
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

    introspection_report = (

        introspection_engine.analyze_cycle(

            cognitive_cycle,

            evaluation_result
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

            evaluation_result
        )
    )

    recovery_plan = (

        failure_analyzer.build_recovery_plan(

            failure_analysis
        )
    )

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

    # ========================================
    # SAVE CONTEXT
    # ========================================

    context[
        "evaluation_result"
    ] = evaluation_result

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
        "evaluation_metrics"
    ] = evaluation_metrics

    context[
        "evaluation_stage_report"
    ] = stage_report

    # ========================================
    # RETURN CONTEXT
    # ========================================

    return context
