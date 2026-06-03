# ============================================
# NEXRYN GRID ANALYSIS STAGE
# ============================================

from datetime import datetime


# ============================================
# GRID ANALYSIS STAGE
# ============================================

def grid_analysis_stage(context):

    print(
        "\n=================================================="
    )

    print(
        "NEXRYN :: GRID ANALYSIS STAGE"
    )

    print(
        "==================================================\n"
    )

    # ========================================
    # STAGE REPORT
    # ========================================

    stage_report = {

        "stage":
        "grid_analysis",

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
    # VALIDATE CONTEXT
    # ========================================

    if "input_grid" not in context:

        raise ValueError(
            "Missing input_grid"
        )

    if "output_grid" not in context:

        raise ValueError(
            "Missing output_grid"
        )

    # ========================================
    # LOAD GRIDS
    # ========================================

    input_grid = context[
        "input_grid"
    ]

    output_grid = context[
        "output_grid"
    ]

    # ========================================
    # INPUT SUMMARY
    # ========================================

    input_summary = (

        input_grid.grid_summary()
    )

    # ========================================
    # OUTPUT SUMMARY
    # ========================================

    output_summary = (

        output_grid.grid_summary()
    )

    # ========================================
    # GRID DIMENSIONS
    # ========================================

    input_shape = None

    output_shape = None

    if hasattr(
        input_grid,
        "grid"
    ):

        input_shape = (
            input_grid.grid.shape
        )

    if hasattr(
        output_grid,
        "grid"
    ):

        output_shape = (
            output_grid.grid.shape
        )

    # ========================================
    # DIMENSION ANALYSIS
    # ========================================

    dimension_analysis = {

        "input_shape":
        input_shape,

        "output_shape":
        output_shape,

        "shape_changed":
        input_shape != output_shape
    }

    # ========================================
    # GRID COMPLEXITY
    # ========================================

    complexity_report = {

        "input_cells":
        0,

        "output_cells":
        0,

        "complexity_ratio":
        0.0
    }

    if input_shape is not None:

        complexity_report[
            "input_cells"
        ] = (

            input_shape[0]
            *
            input_shape[1]
        )

    if output_shape is not None:

        complexity_report[
            "output_cells"
        ] = (

            output_shape[0]
            *
            output_shape[1]
        )

    input_cells = complexity_report[
        "input_cells"
    ]

    output_cells = complexity_report[
        "output_cells"
    ]

    if input_cells > 0:

        complexity_report[
            "complexity_ratio"
        ] = round(

            output_cells / input_cells,

            4
        )

    # ========================================
    # GRID TRANSFORMATION SIGNALS
    # ========================================

    transformation_signals = {

        "size_transformation":
        input_shape != output_shape,

        "requires_scaling":
        output_cells > input_cells,

        "requires_compression":
        output_cells < input_cells
    }

    # ========================================
    # ANALYSIS METRICS
    # ========================================

    analysis_metrics = {

        "input_dimensions":
        input_shape,

        "output_dimensions":
        output_shape,

        "input_cells":
        input_cells,

        "output_cells":
        output_cells
    }

    # ========================================
    # UPDATE STAGE REPORT
    # ========================================

    stage_report.update({

        "status":
        "completed",

        "analysis_metrics":
        analysis_metrics
    })

    # ========================================
    # DISPLAY RESULTS
    # ========================================

    print(
        "INPUT GRID SUMMARY:\n"
    )

    print(
        input_summary
    )

    print(
        "\nOUTPUT GRID SUMMARY:\n"
    )

    print(
        output_summary
    )

    print(
        "\nGRID DIMENSION ANALYSIS:\n"
    )

    print(
        dimension_analysis
    )

    print(
        "\nGRID COMPLEXITY REPORT:\n"
    )

    print(
        complexity_report
    )

    # ========================================
    # SAVE TO CONTEXT
    # ========================================

    context[
        "input_summary"
    ] = input_summary

    context[
        "output_summary"
    ] = output_summary

    context[
        "dimension_analysis"
    ] = dimension_analysis

    context[
        "complexity_report"
    ] = complexity_report

    context[
        "transformation_signals"
    ] = transformation_signals

    context[
        "analysis_metrics"
    ] = analysis_metrics

    context[
        "grid_analysis_complete"
    ] = True

    context[
        "grid_analysis_stage_report"
    ] = stage_report

    # ========================================
    # RETURN CONTEXT
    # ========================================

    return context