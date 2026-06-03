# ============================================
# NEXRYN SPATIAL TRANSLATION ENGINE
# ============================================

from datetime import datetime

import math

import numpy as np


# ============================================
# SPATIAL TRANSLATION ENGINE
# ============================================

class SpatialTranslationEngine:

    """
    Detects spatial object movement,
    centroid displacement,
    directional translation,
    and transformation priority scoring.
    """

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # TRANSLATION HISTORY
        # ====================================

        self.translation_history = []

        self.detected_movements = []

        self.failed_detections = []

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "spatial_translation":
            True,

            "centroid_tracking":
            True,

            "movement_reasoning":
            True,

            "directional_analysis":
            True,

            "translation_priority":
            True
        }

    # ========================================
    # SAFE OBJECT EXTRACTION
    # ========================================

    def safe_objects(

        self,

        object_list
    ):

        if object_list is None:

            return []

        if not isinstance(
            object_list,
            list
        ):

            return []

        return object_list

    # ========================================
    # COMPUTE DISTANCE
    # ========================================

    def compute_distance(

        self,

        point_a,

        point_b
    ):

        row_distance = (

            point_b.get("row", 0)

            -

            point_a.get("row", 0)
        )

        col_distance = (

            point_b.get("col", 0)

            -

            point_a.get("col", 0)
        )

        return math.sqrt(

            row_distance ** 2

            +

            col_distance ** 2
        )

    # ========================================
    # DETECT DIRECTION
    # ========================================

    def detect_direction(

        self,

        row_shift,

        col_shift
    ):

        # ====================================
        # PURE DIRECTIONS
        # ====================================

        if row_shift == 0 and col_shift > 0:

            return "right"

        if row_shift == 0 and col_shift < 0:

            return "left"

        if col_shift == 0 and row_shift > 0:

            return "down"

        if col_shift == 0 and row_shift < 0:

            return "up"

        # ====================================
        # DIAGONALS
        # ====================================

        if row_shift > 0 and col_shift > 0:

            return "down_right"

        if row_shift > 0 and col_shift < 0:

            return "down_left"

        if row_shift < 0 and col_shift > 0:

            return "up_right"

        if row_shift < 0 and col_shift < 0:

            return "up_left"

        return "stationary"

    # ========================================
    # DETECT TRANSLATION
    # ========================================

    def detect_translation(

        self,

        input_objects,

        output_objects
    ):

        input_objects = self.safe_objects(
            input_objects
        )

        output_objects = self.safe_objects(
            output_objects
        )

        # ====================================
        # EMPTY OBJECTS
        # ====================================

        if len(input_objects) == 0:

            return {

                "translation_detected":
                False,

                "reason":
                "no_input_objects"
            }

        if len(output_objects) == 0:

            return {

                "translation_detected":
                False,

                "reason":
                "no_output_objects"
            }

        # ====================================
        # OBJECT COUNT MISMATCH
        # ====================================

        if len(input_objects) != (
            len(output_objects)
        ):

            return {

                "translation_detected":
                False,

                "reason":
                "object_count_changed"
            }

        translation_results = []

        # ====================================
        # OBJECT MATCHING
        # ====================================

        for index in range(

            min(

                len(input_objects),

                len(output_objects)
            )
        ):

            input_object = (
                input_objects[index]
            )

            output_object = (
                output_objects[index]
            )

            input_centroid = (

                input_object.get(
                    "centroid",
                    {}
                )
            )

            output_centroid = (

                output_object.get(
                    "centroid",
                    {}
                )
            )

            input_size = input_object.get(
                "size",
                0
            )

            output_size = output_object.get(
                "size",
                0
            )

            # ================================
            # OBJECT PRESERVATION
            # ================================

            if input_size != output_size:

                continue

            row_shift = round(

                output_centroid.get(
                    "row",
                    0
                )

                -

                input_centroid.get(
                    "row",
                    0
                ),

                4
            )

            col_shift = round(

                output_centroid.get(
                    "col",
                    0
                )

                -

                input_centroid.get(
                    "col",
                    0
                ),

                4
            )

            movement_distance = (

                self.compute_distance(

                    input_centroid,

                    output_centroid
                )
            )

            translation_detected = (

                row_shift != 0

                or

                col_shift != 0
            )

            direction = (

                self.detect_direction(

                    row_shift,

                    col_shift
                )
            )

            translation_result = {

                "object_index":
                index,

                "translation_detected":
                translation_detected,

                "row_shift":
                row_shift,

                "col_shift":
                col_shift,

                "direction":
                direction,

                "movement_distance":
                round(
                    movement_distance,
                    4
                ),

                "input_centroid":
                input_centroid,

                "output_centroid":
                output_centroid,

                "size_preserved":
                True
            }

            translation_results.append(
                translation_result
            )

        # ====================================
        # GLOBAL ANALYSIS
        # ====================================

        detected_movements = [

            result

            for result in translation_results

            if result[
                "translation_detected"
            ]
        ]

        global_translation = (

            len(detected_movements)
            > 0
        )

        translation_report = {

            "translation_detected":
            global_translation,

            "movement_count":

            len(
                detected_movements
            ),

            "translation_results":
            translation_results,

            "timestamp":
            str(datetime.utcnow())
        }

        self.translation_history.append(
            translation_report
        )

        if global_translation:

            self.detected_movements.extend(
                detected_movements
            )

        return translation_report

    # ========================================
    # BUILD SPATIAL HYPOTHESIS
    # ========================================

    def build_spatial_hypothesis(

        self,

        translation_report
    ):

        if not translation_report.get(

            "translation_detected",

            False
        ):

            return None

        translation_results = (

            translation_report.get(

                "translation_results",

                []
            )
        )

        if len(translation_results) == 0:

            return None

        dominant_translation = (
            translation_results[0]
        )

        hypothesis = {

            "type":
            "spatial_translation",

            "category":
            "spatial",

            "description":
            "Detected object translation movement",

            "confidence":
            0.98,

            "metadata": {

                "direction":

                dominant_translation.get(
                    "direction"
                ),

                "row_shift":

                dominant_translation.get(
                    "row_shift"
                ),

                "col_shift":

                dominant_translation.get(
                    "col_shift"
                ),

                "movement_distance":

                dominant_translation.get(
                    "movement_distance"
                )
            },

            "translation_priority":
            1.0,

            "spatial_weight":
            1.0,

            "mutation_applied":
            False
        }

        return hypothesis

    # ========================================
    # PRIORITIZE SPATIAL REASONING
    # ========================================

    def prioritize_spatial_reasoning(

        self,

        hypotheses
    ):

        if not isinstance(
            hypotheses,
            list
        ):

            return []

        prioritized = []

        for hypothesis in hypotheses:

            if not isinstance(
                hypothesis,
                dict
            ):

                continue

            hypothesis_type = hypothesis.get(
                "type",
                ""
            )

            confidence = hypothesis.get(
                "confidence",
                0.0
            )

            # ================================
            # SPATIAL BOOST
            # ================================

            if hypothesis_type == (
                "spatial_translation"
            ):

                confidence += 0.20

            hypothesis["confidence"] = min(

                confidence,

                1.0
            )

            prioritized.append(
                hypothesis
            )

        prioritized = sorted(

            prioritized,

            key=lambda item:

            item.get(
                "confidence",
                0.0
            ),

            reverse=True
        )

        return prioritized

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_translation = {}

        if self.translation_history:

            latest_translation = (

                self.translation_history[-1]
            )

        return {

            "translation_cycles":

            len(
                self.translation_history
            ),

            "detected_movements":

            len(
                self.detected_movements
            ),

            "failed_detections":

            len(
                self.failed_detections
            ),

            "engine_state":
            self.engine_state,

            "latest_translation":
            latest_translation
        }


# ============================================
# GLOBAL SPATIAL TRANSLATION ENGINE
# ============================================

spatial_translation_engine = (
    SpatialTranslationEngine()
)