# ============================================
# TASK LOADING STAGE
# ============================================

# ============================================
# IMPORTS
# ============================================

from datetime import datetime

from core.loader import (
    ARCJSONLoader
)

from core.arc_task_boundary import (
    SolverTaskView
)

# ============================================
# BUILD TASK METADATA
# ============================================

def build_task_metadata(

    train_example
):

    input_grid = train_example.get(
        "input"
    )

    output_grid = train_example.get(
        "output"
    )

    input_shape = None
    output_shape = None

    # ========================================
    # INPUT SHAPE
    # ========================================

    if hasattr(
        input_grid,
        "grid"
    ):

        input_shape = (
            input_grid.grid.shape
        )

    # ========================================
    # OUTPUT SHAPE
    # ========================================

    if hasattr(
        output_grid,
        "grid"
    ):

        output_shape = (
            output_grid.grid.shape
        )

    return {

        "input_shape":
        input_shape,

        "output_shape":
        output_shape,

        "shape_changed":
        input_shape != output_shape
    }

def task_loading_stage(context):

    print(
        "\n=================================================="
    )

    print(
        "NEXRYN :: TASK LOADING STAGE"
    )

    print(
        "==================================================\n"
    )

    # ========================================
    # STAGE REPORT
    # ========================================

    stage_report = {

        "stage":
        "task_loading",

        "status":
        "running",

        "runtime_health":
        "stable",

        "timestamp":
        str(datetime.utcnow())
    }

    # ========================================
    # VALIDATE CONTEXT
    # ========================================

    if not isinstance(
        context,
        dict
    ):

        context = {}

    if "task_path" not in context:

        context[
            "task_loading_error"
        ] = "missing_task_path"

        return context

    # ========================================
    # LOAD TASK PATH
    # ========================================

    task_path = context.get(
        "task_path"
    )

    # ========================================
    # TASK PATH NORMALIZATION
    # ========================================

    if isinstance(
        task_path,
        dict
    ):

        task_path = task_path.get(
            "value"
        )

    # ========================================
    # INVALID PATH PROTECTION
    # ========================================

    if task_path is None:

        context[
            "task_loading_error"
        ] = "task_path_none"

        return context

    if not isinstance(
        task_path,
        str
    ):

        context[
            "task_loading_error"
        ] = "task_path_invalid"

        return context

    # ========================================
    # SAFE TASK PATH
    # ========================================

    task_path = str(task_path)

    # ========================================
    # INITIALIZE LOADER
    # ========================================

    try:

        loader = ARCJSONLoader(
            task_path
        )

    except Exception as loader_error:

        context[
            "task_loading_error"
        ] = repr(loader_error)

        return context

    # ========================================
    # LOAD TASK
    # ========================================

    try:

        task_loaded = (
            loader.load()
        )

    except Exception as loading_error:

        print(
            "\n==================================="
        )

        print(
            "NEXRYN LOADER ERROR"
        )

        print(
            "===================================\n"
        )

        print(
            "TASK PATH:"
        )

        print(task_path)

        print(
            "\nERROR:"
        )

        print(
            repr(loading_error)
        )

        context[
            "task_loading_error"
        ] = repr(
            loading_error
        )

        return context

    # ========================================
    # VALIDATION FAILURE
    # ========================================

    if not task_loaded:

        context[
            "task_loading_error"
        ] = "failed_to_load_task"

        return context

    # ========================================
    # PRINT TASK SUMMARY
    # ========================================

    try:

        loader.print_summary()

    except Exception:

        pass

    # ========================================
    # LOAD TRAIN EXAMPLE
    # ========================================

    solver_task_id = context.get(
        "task_id",
        task_path
    )

    solver_task_view = (
        SolverTaskView.from_raw_task(
            loader.task_data,
            solver_task_id
        )
    )

    train_example = (
        solver_task_view.first_train_example()
    )

    # ========================================
    # VALIDATE TRAIN EXAMPLE
    # ========================================

    if train_example is None:

        context[
            "task_loading_error"
        ] = "missing_train_example"

        return context

    # ========================================
    # EXTRACT GRIDS
    # ========================================

    input_grid = train_example.get(
        "input"
    )

    output_grid = train_example.get(
        "output"
    )

    test_example = (
        solver_task_view.first_test_example()
    )

    test_input_grid = None

    if test_example is not None:

        test_input_grid = test_example.get(
            "input"
        )

    if input_grid is None:

        context[
            "task_loading_error"
        ] = "missing_input_grid"

        return context

    if output_grid is None:

        context[
            "task_loading_error"
        ] = "missing_output_grid"

        return context

    # ========================================
    # TASK METADATA
    # ========================================

    task_metadata = (

        build_task_metadata(
            train_example
        )
    )

    # ========================================
    # TASK ANALYSIS
    # ========================================

    task_analysis = {

        "task_loaded":
        True,

        "has_input_grid":
        input_grid is not None,

        "has_output_grid":
        output_grid is not None,

        "shape_changed":
        task_metadata.get(
            "shape_changed",
            False
        )
    }

    # ========================================
    # LOADING METRICS
    # ========================================

    loading_metrics = {

        "input_shape":
        task_metadata.get(
            "input_shape"
        ),

        "output_shape":
        task_metadata.get(
            "output_shape"
        )
    }

    # ========================================
    # UPDATE STAGE REPORT
    # ========================================

    stage_report.update({

        "status":
        "completed",

        "task_path":
        task_path,

        "loading_metrics":
        loading_metrics
    })

    # ========================================
    # DISPLAY RESULTS
    # ========================================

    print(
        "TASK METADATA:\n"
    )

    print(
        task_metadata
    )

    print(
        "\nTASK ANALYSIS:\n"
    )

    print(
        task_analysis
    )

    # ========================================
    # SAVE TO CONTEXT
    # ========================================

    context[
        "train_example"
    ] = train_example

    context[
        "solver_task_view"
    ] = solver_task_view

    context[
        "input_grid"
    ] = input_grid

    context[
        "output_grid"
    ] = output_grid

    context[
        "test_input_grid"
    ] = test_input_grid

    context[
        "raw_loader_excluded_from_solver_context"
    ] = True

    context[
        "raw_task_data_excluded_from_solver_context"
    ] = True

    context[
        "hidden_test_output_solver_visible"
    ] = False

    context[
        "train_output_grid_provenance"
    ] = {

        "source":
        "solver_task_view.train[0].output",

        "visibility":
        "TRAIN_VISIBLE",

        "arc_hidden_test_target":
        False
    }

    context[
        "test_output_visibility"
    ] = {

        "state":
        "EVALUATOR_ONLY_AFTER_ATTEMPT_FREEZE",

        "solver_visible":
        False
    }

    if context.get(
        "arc_benchmark_mode"
    ) is True:

        context[
            "arc_benchmark_memory_policy"
        ] = {

            "hidden_label_memory_writes":
            "DISABLED_FOR_BASELINE",

            "reuse_visibility":
            "NO_HIDDEN_LABEL_REUSE_DURING_BENCHMARK",

            "authority":
            "BENCHMARK_ISOLATION_ONLY"
        }

    context[
        "task_metadata"
    ] = task_metadata

    context[
        "task_analysis"
    ] = task_analysis

    context[
        "loading_metrics"
    ] = loading_metrics

    context[
        "task_loading_stage_report"
    ] = stage_report

    context[
        "task_loaded"
    ] = True

    # ========================================
    # RETURN CONTEXT
    # ========================================

    return context
