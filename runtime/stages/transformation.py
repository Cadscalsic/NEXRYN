# ============================================
# NEXRYN TRANSFORMATION STAGE
# EXECUTABLE TRANSFORMATION RUNTIME
# ============================================

from datetime import datetime

import numpy as np

# ============================================
# TRANSFORMATION ENGINE
# ============================================

from runtime.engines.transformation_engine import (
    TransformationEngine
)

# ============================================
# WORLD MODEL
# ============================================

from runtime.world.world_model import (
    world_model_engine
)

# ============================================
# PRIMITIVE EXECUTION
# ============================================

from runtime.transforms import (
    primitive_executor
)
from runtime.execution.execution_integrity_guard import (
    execution_integrity_guard,
)
from runtime.execution.world_model_gate import (
    world_model_gate,
)

# ============================================
# GLOBAL TRANSFORMATION ENGINE
# ============================================

transformation_engine = (
    TransformationEngine()
)

# ============================================
# SAFE GRID EXTRACTION
# ============================================

def extract_grid_array(grid_object):

    if grid_object is None:

        return None

    if hasattr(
        grid_object,
        "grid"
    ):

        return np.array(
            grid_object.grid
        )

    return np.array(grid_object)

# ============================================
# SAFE LIST
# ============================================

def safe_list(value):

    if value is None:

        return []

    if not isinstance(
        value,
        list
    ):

        return []

    return value

# ============================================
# BUILD EXECUTION METRICS
# ============================================

def build_execution_metrics(

    executed_steps,

    strategy_count,

    execution_trace
):

    return {

        "executed_steps":
        executed_steps,

        "strategy_count":
        strategy_count,

        "trace_depth":
        len(execution_trace)
    }

# ============================================
# BUILD EXECUTION HEALTH
# ============================================

def build_execution_health(

    predicted_output,

    execution_trace,

    executed_steps
):

    return {

        "valid_output":
        predicted_output is not None,

        "trace_available":
        len(execution_trace) > 0,

        "execution_success":
        executed_steps > 0
    }

# ============================================
# BUILD WORLD CONSISTENCY
# ============================================

def build_world_consistency(

    predicted_simulation,

    prediction_report
):

    return {

        "simulation_available":

        predicted_simulation is not None,

        "prediction_valid":

        prediction_report.get(
            "success",
            False
        ),

        "prediction_accuracy":

        prediction_report.get(
            "prediction_accuracy",
            prediction_report.get(
                "accuracy",
                0.0
            )
        )
    }

# ============================================
# TRANSFORMATION STAGE
# ============================================

def transformation_stage(context):

    print(
        "\n=================================================="
    )

    print(
        "NEXRYN :: TRANSFORMATION STAGE"
    )

    print(
        "==================================================\n"
    )

    # ========================================
    # SAFE CONTEXT
    # ========================================

    if not isinstance(
        context,
        dict
    ):

        context = {}

    # ========================================
    # STAGE REPORT
    # ========================================

    stage_report = {

        "stage":
        "transformation",

        "status":
        "running",

        "runtime_health":
        "stable",

        "timestamp":
        str(
            datetime.utcnow()
        )
    }

    # ========================================
    # LOAD CONTEXT
    # ========================================

    input_grid = context.get(
        "input_grid"
    )

    output_grid = context.get(
        "output_grid"
    )

    synthesized_program = context.get(
        "synthesized_program",
        {}
    )

    ranked_primitives = safe_list(

        context.get(
            "ranked_primitives",
            []
        )
    )

    execution_result = context.get(
        "execution_result",
        {}
    )

    execution_plan = context.get(
        "execution_plan",
        {}
    )

    world_model_anticipation = context.get(
        "world_model_anticipation",
        {}
    )

    # ========================================
    # VALIDATION
    # ========================================

    if input_grid is None:

        raise ValueError(
            "Missing input_grid"
        )

    if output_grid is None:

        raise ValueError(
            "Missing output_grid"
        )

    # ========================================
    # EXTRACT ARRAYS
    # ========================================

    input_array = extract_grid_array(
        input_grid
    )

    output_array = extract_grid_array(
        output_grid
    )

    # ========================================
    # WORLD MODEL SIMULATION
    # ========================================

    simulation_result = {}

    prediction_report = {

        "accuracy": 0.0,

        "success": False
    }

    predicted_simulation = None

    try:

        simulation_result = (

            world_model_engine
            .simulate_transformation(

                input_array,

                synthesized_program
            )
        )

        predicted_simulation = (

            simulation_result.get(
                "predicted_grid"
            )
        )

        prediction_report = (

            world_model_engine
            .evaluate_prediction(

                predicted_simulation,

                output_array
            )
        )

    except Exception as error:

        prediction_report = {

            "accuracy": 0.0,

            "success": False,

            "error": repr(error)
        }

    # ========================================
    # WORLD CONSISTENCY
    # ========================================

    world_consistency = (

        build_world_consistency(

            predicted_simulation,

            prediction_report
        )
    )

    # ========================================
    # DISPLAY WORLD MODEL
    # ========================================

    print(
        "\nWORLD MODEL REPORT:\n"
    )

    print(
        prediction_report
    )

    # ========================================
    # AUTHORIZED EXECUTION
    # ========================================

    planned_primitives = (
        execution_integrity_guard
        .primitives_from_plan(
            execution_plan
        )
    )

    world_model_gate_report = (
        world_model_gate.evaluate(
            world_model_anticipation
        )
    )

    sandbox_execution_result = None

    if world_model_gate_report[
        "sandbox_execution_authorized"
    ]:

        sandbox_execution_result = {

            "execution_mode":
            "isolated_world_model_sandbox",

            "output_grid":
            simulation_result.get(
                "predicted_grid"
            ),

            "execution_trace":
            simulation_result.get(
                "simulation_trace",
                []
            ),

            "persistent_effects_forbidden":
            True
        }

    if world_model_gate_report[
        "execution_authorized"
    ]:

        execution_result = (

            primitive_executor
            .run_execution(

                input_grid=
                input_array,

                primitives=
                planned_primitives
            )
        )

    else:

        execution_result = {

            "output_grid":
            np.array(
                input_array,
                copy=True
            ),

            "execution_trace":
            [],

            "execution_aborted":
            True,

            "abort_reason":
            world_model_gate_report[
                "gate_state"
            ]
        }

    execution_integrity_report = (
        execution_integrity_guard.evaluate(
            execution_plan,
            execution_result.get(
                "execution_trace",
                []
            ),
            execution_authorized=
            world_model_gate_report[
                "execution_authorized"
            ],
        )
    )

    if (
        world_model_gate_report[
            "execution_authorized"
        ]
        and not execution_integrity_report[
            "integrity_preserved"
        ]
    ):

        execution_result = {

            **execution_result,

            "output_grid":
            np.array(
                input_array,
                copy=True
            ),

            "execution_aborted":
            True,

            "abort_reason":
            "EXECUTION_INTEGRITY_VIOLATION"
        }

    predicted_output = (

        execution_result.get(
            "output_grid"
        )
    )

    if sandbox_execution_result is not None:

        predicted_output = sandbox_execution_result.get(
            "output_grid",
            predicted_output
        )

    if predicted_output is None:

        predicted_output = np.array(
            input_array,
            copy=True
        )

        execution_result = {

            **execution_result,

            "output_grid":
            predicted_output,

            "execution_aborted":
            True,

            "abort_reason":
            "MISSING_AUTHORIZED_EXECUTION_OUTPUT"
        }

    # ========================================
    # SAFE EXECUTION TRACE
    # ========================================

    execution_trace = safe_list(

        execution_result.get(
            "execution_trace",
            []
        )
    )

    executed_steps = len(
        execution_trace
    )

    strategy_count = len(
        planned_primitives
    )

    # ========================================
    # EXECUTION METRICS
    # ========================================

    execution_metrics = (

        build_execution_metrics(

            executed_steps,

            strategy_count,

            execution_trace
        )
    )

    # ========================================
    # TRANSFORMATION COMPLEXITY
    # ========================================

    transformation_complexity = "low"

    if executed_steps > 15:

        transformation_complexity = "high"

    elif executed_steps > 5:

        transformation_complexity = "medium"

    # ========================================
    # EXECUTION HEALTH
    # ========================================

    execution_health = (

        build_execution_health(

            predicted_output,

            execution_trace,

            executed_steps
        )
    )

    # ========================================
    # TRANSFORMATION CONFIDENCE
    # ========================================

    transformation_confidence = round(

        prediction_report.get(
            "prediction_accuracy",
            prediction_report.get(
                "accuracy",
                0.0
            )
        ),

        4
    )

    # ========================================
    # TRANSFORMATION REPORT
    # ========================================

    transformation_report = {

        "executed_steps":
        executed_steps,

        "strategy_count":
        strategy_count,

        "execution_trace":
        execution_trace,

        "transformation_complexity":
        transformation_complexity,

        "transformation_confidence":
        transformation_confidence,

        "execution_aborted":
        execution_result.get(
            "execution_aborted",
            False
        ),

        "world_model_gate":
        world_model_gate_report,

        "execution_integrity":
        execution_integrity_report,

        "sandbox_execution":
        sandbox_execution_result
    }

    # ========================================
    # DISPLAY RESULTS
    # ========================================

    print(
        "\nTRANSFORMATION REPORT:\n"
    )

    print(
        transformation_report
    )

    print(
        "\nPREDICTED OUTPUT:\n"
    )

    print(
        predicted_output
    )

    # ========================================
    # UPDATE STAGE REPORT
    # ========================================

    stage_report.update({

        "status":
        "completed",

        "executed_steps":
        executed_steps,

        "strategy_count":
        strategy_count,

        "transformation_confidence":
        transformation_confidence,

        "transformation_complexity":
        transformation_complexity
    })

    # ========================================
    # SAVE CONTEXT
    # ========================================

    context[
        "simulation_result"
    ] = simulation_result

    context[
        "prediction_report"
    ] = prediction_report

    context[
        "predicted_output"
    ] = predicted_output

    context[
        "transformation_report"
    ] = transformation_report

    context[
        "transformation_execution_trace"
    ] = execution_trace

    context[
        "execution_metrics"
    ] = execution_metrics

    context[
        "execution_health"
    ] = execution_health

    context[
        "world_consistency"
    ] = world_consistency

    context[
        "transformation_confidence"
    ] = transformation_confidence

    context[
        "transformation_complexity"
    ] = transformation_complexity

    context[
        "transformation_execution_result"
    ] = execution_result

    context[
        "sandbox_execution_result"
    ] = sandbox_execution_result

    context[
        "world_model_gate_report"
    ] = world_model_gate_report

    context[
        "execution_integrity_report"
    ] = execution_integrity_report

    context[
        "transformation_stage_report"
    ] = stage_report

    context[
        "transformation_complete"
    ] = True

    # ========================================
    # RETURN CONTEXT
    # ========================================

    return context
