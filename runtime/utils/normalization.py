# ============================================
# NEXRYN COGNITIVE CONTEXT SERIALIZER
# ============================================

import numpy as np

from datetime import datetime


# ============================================
# NORMALIZATION METRICS
# ============================================

class NormalizationMetrics:

    def __init__(self):

        self.metrics = {

            "normalized_objects":
            0,

            "normalized_arrays":
            0,

            "normalized_dicts":
            0,

            "normalized_lists":
            0,

            "normalized_sets":
            0,

            "normalized_tuples":
            0,

            "serialized_objects":
            0,

            "unsupported_objects":
            0,

            "circular_references":
            0,

            "max_depth_events":
            0
        }

    # ========================================
    # INCREMENT
    # ========================================

    def increment(

        self,

        key
    ):

        if key not in self.metrics:

            self.metrics[key] = 0

        self.metrics[key] += 1

    # ========================================
    # EXPORT
    # ========================================

    def export(self):

        return self.metrics.copy()


# ============================================
# GLOBAL METRICS
# ============================================

normalization_metrics = (
    NormalizationMetrics()
)


# ============================================
# NORMALIZE VALUE
# ============================================

def normalize_value(

    value,

    visited=None,

    depth=0,

    max_depth=32
):

    # ========================================
    # INITIALIZE VISITED
    # ========================================

    if visited is None:

        visited = set()

    # ========================================
    # DEPTH PROTECTION
    # ========================================

    if depth > max_depth:

        normalization_metrics.increment(
            "max_depth_events"
        )

        return {

            "__error__":
            "max_depth_exceeded"
        }

    # ========================================
    # PRIMITIVE TYPES
    # ========================================

    if isinstance(

        value,

        (
            str,
            int,
            float,
            bool,
            type(None)
        )
    ):

        return value

    # ========================================
    # OBJECT ID
    # ========================================

    object_id = id(value)

    # ========================================
    # CIRCULAR REFERENCE PROTECTION
    # ========================================

    if object_id in visited:

        normalization_metrics.increment(
            "circular_references"
        )

        return {

            "__error__":
            "circular_reference",

            "__object_id__":
            object_id
        }

    # ========================================
    # LOCAL VISITED
    # ========================================

    local_visited = visited.copy()

    local_visited.add(
        object_id
    )

    normalization_metrics.increment(
        "normalized_objects"
    )

    # ========================================
    # NUMPY INTEGER
    # ========================================

    if isinstance(value, np.integer):

        return int(value)

    # ========================================
    # NUMPY FLOAT
    # ========================================

    if isinstance(value, np.floating):

        return float(value)

    # ========================================
    # NUMPY ARRAY
    # ========================================

    if isinstance(value, np.ndarray):

        normalization_metrics.increment(
            "normalized_arrays"
        )

        return {

            "__type__":
            "ndarray",

            "shape":
            value.shape,

            "dtype":
            str(value.dtype),

            "data":
            value.tolist()
        }

    # ========================================
    # LIST
    # ========================================

    if isinstance(value, list):

        normalization_metrics.increment(
            "normalized_lists"
        )

        return [

            normalize_value(

                item,

                local_visited,

                depth + 1,

                max_depth
            )

            for item in value
        ]

    # ========================================
    # TUPLE
    # ========================================

    if isinstance(value, tuple):

        normalization_metrics.increment(
            "normalized_tuples"
        )

        return tuple(

            normalize_value(

                item,

                local_visited,

                depth + 1,

                max_depth
            )

            for item in value
        )

    # ========================================
    # SET
    # ========================================

    if isinstance(value, set):

        normalization_metrics.increment(
            "normalized_sets"
        )

        return [

            normalize_value(

                item,

                local_visited,

                depth + 1,

                max_depth
            )

            for item in value
        ]

    # ========================================
    # DICTIONARY
    # ========================================

    if isinstance(value, dict):

        normalization_metrics.increment(
            "normalized_dicts"
        )

        normalized_dict = {}

        for key, val in value.items():

            normalized_dict[

                str(key)

            ] = normalize_value(

                val,

                local_visited,

                depth + 1,

                max_depth
            )

        return normalized_dict

    # ========================================
    # OBJECT SERIALIZATION
    # ========================================

    if hasattr(value, "__dict__"):

        normalization_metrics.increment(
            "serialized_objects"
        )

        safe_attributes = {}

        for key, val in value.__dict__.items():

            # ====================================
            # SKIP CALLABLES
            # ====================================

            if callable(val):

                continue

            # ====================================
            # SKIP PRIVATE ATTRIBUTES
            # ====================================

            if key.startswith("__"):

                continue

            safe_attributes[key] = val

        return {

            "__class__":
            value.__class__.__name__,

            "__object_id__":
            object_id,

            "__attributes__":

            normalize_value(

                safe_attributes,

                local_visited,

                depth + 1,

                max_depth
            )
        }

    # ========================================
    # FALLBACK STRING SERIALIZATION
    # ========================================

    normalization_metrics.increment(
        "unsupported_objects"
    )

    return {

        "__unsupported_type__":
        str(type(value)),

        "__string__":
        str(value)
    }


# ============================================
# NORMALIZE CONTEXT
# ============================================

def normalize_context(

    context
):

    normalized = {}

    for key, value in context.items():

        normalized[
            str(key)
        ] = normalize_value(
            value
        )

    return normalized


# ============================================
# BUILD NORMALIZATION REPORT
# ============================================

def build_normalization_report():

    return {

        "metrics":

        normalization_metrics.export(),

        "normalizer_state":
        "stable",

        "serializer_mode":
        "recursive_cognitive_serialization",

        "timestamp":
        str(
            datetime.utcnow()
        )
    }


# ============================================
# PRINT NORMALIZATION REPORT
# ============================================

def print_normalization_report():

    report = (
        build_normalization_report()
    )

    print("\n==================================================")
    print("NEXRYN :: CONTEXT SERIALIZER")
    print("==================================================\n")

    print(report)