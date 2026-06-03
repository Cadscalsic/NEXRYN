# ============================================
# NEXRYN OBJECT DETECTION STAGE
# ============================================

from datetime import datetime

from core.objects import (
    ObjectDetector
)


# ============================================
# SAFE OBJECT SUMMARY
# ============================================

def build_object_summary(

    detected_object
):

    try:

        return detected_object.summary()

    except Exception:

        return {

            "object_type":
            "unknown",

            "summary_error":
            True
        }


# ============================================
# OBJECT METRICS
# ============================================

def build_object_metrics(

    objects
):

    return {

        "object_count":
        len(objects)
    }


# ============================================
# OBJECT DETECTION STAGE
# ============================================

def object_detection_stage(context):

    print(
        "\n=================================================="
    )

    print(
        "NEXRYN :: OBJECT DETECTION STAGE"
    )

    print(
        "==================================================\n"
    )

    # ========================================
    # STAGE REPORT
    # ========================================

    stage_report = {

        "stage":
        "object_detection",

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
    # INPUT OBJECT DETECTION
    # ========================================

    input_detector = ObjectDetector(
        input_grid.grid
    )

    input_objects = (

        input_detector.detect_objects()
    )

    # ========================================
    # OUTPUT OBJECT DETECTION
    # ========================================

    output_detector = ObjectDetector(
        output_grid.grid
    )

    output_objects = (

        output_detector.detect_objects()
    )

    # ========================================
    # OBJECT SUMMARIES
    # ========================================

    input_object_summaries = []

    output_object_summaries = []

    # ========================================
    # INPUT OBJECTS
    # ========================================

    print(
        "INPUT OBJECTS:\n"
    )

    for index, obj in enumerate(
        input_objects
    ):

        summary = (
            build_object_summary(obj)
        )

        input_object_summaries.append(
            summary
        )

        print(
            f"OBJECT {index + 1}"
        )

        print(summary)

        print()

    # ========================================
    # OUTPUT OBJECTS
    # ========================================

    print(
        "\nOUTPUT OBJECTS:\n"
    )

    for index, obj in enumerate(
        output_objects
    ):

        summary = (
            build_object_summary(obj)
        )

        output_object_summaries.append(
            summary
        )

        print(
            f"OBJECT {index + 1}"
        )

        print(summary)

        print()

    # ========================================
    # OBJECT METRICS
    # ========================================

    input_metrics = (
        build_object_metrics(
            input_objects
        )
    )

    output_metrics = (
        build_object_metrics(
            output_objects
        )
    )

    # ========================================
    # OBJECT COMPARISON
    # ========================================

    object_comparison = {

        "input_object_count":
        len(input_objects),

        "output_object_count":
        len(output_objects),

        "object_delta":

        len(output_objects)

        -

        len(input_objects),

        "preservation_detected":

        len(input_objects)

        ==

        len(output_objects)
    }

    # ========================================
    # DETECTION COMPLEXITY
    # ========================================

    detection_complexity = {

        "input_complexity":
        "low",

        "output_complexity":
        "low"
    }

    if len(input_objects) > 10:

        detection_complexity[
            "input_complexity"
        ] = "high"

    elif len(input_objects) > 5:

        detection_complexity[
            "input_complexity"
        ] = "medium"

    if len(output_objects) > 10:

        detection_complexity[
            "output_complexity"
        ] = "high"

    elif len(output_objects) > 5:

        detection_complexity[
            "output_complexity"
        ] = "medium"

    # ========================================
    # OBJECT TRANSFORMATION SIGNALS
    # ========================================

    transformation_signals = {

        "object_creation":

        len(output_objects)

        >

        len(input_objects),

        "object_removal":

        len(output_objects)

        <

        len(input_objects),

        "object_preservation":

        len(output_objects)

        ==

        len(input_objects)
    }

    # ========================================
    # DETECTION METRICS
    # ========================================

    detection_metrics = {

        "input_objects":
        len(input_objects),

        "output_objects":
        len(output_objects),

        "total_objects":

        len(input_objects)

        +

        len(output_objects)
    }

    # ========================================
    # UPDATE STAGE REPORT
    # ========================================

    stage_report.update({

        "status":
        "completed",

        "detection_metrics":
        detection_metrics
    })

    # ========================================
    # SAVE TO CONTEXT
    # ========================================

    context[
        "input_objects"
    ] = input_objects

    context[
        "output_objects"
    ] = output_objects

    context[
        "input_object_summaries"
    ] = input_object_summaries

    context[
        "output_object_summaries"
    ] = output_object_summaries

    context[
        "input_object_metrics"
    ] = input_metrics

    context[
        "output_object_metrics"
    ] = output_metrics

    context[
        "object_comparison"
    ] = object_comparison

    context[
        "detection_complexity"
    ] = detection_complexity

    context[
        "object_transformation_signals"
    ] = transformation_signals

    context[
        "detection_metrics"
    ] = detection_metrics

    context[
        "object_detection_stage_report"
    ] = stage_report

    context[
        "object_detection_complete"
    ] = True

    # ========================================
    # RETURN CONTEXT
    # ========================================

    return context