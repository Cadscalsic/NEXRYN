# ============================================
# NEXRYN SPATIAL REASONING ENGINE
# ============================================

import numpy as np

from copy import deepcopy

from datetime import datetime


# ============================================
# SPATIAL REASONING ENGINE
# ============================================

class SpatialReasoningEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.spatial_history = []

        self.detected_operations = []

        self.engine_state = {

            "translation_detection":
            True,

            "rotation_detection":
            True,

            "reflection_detection":
            True,

            "topology_tracking":
            True,

            "coordinate_reasoning":
            True
        }

    # ========================================
    # EXTRACT OBJECT COORDINATES
    # ========================================

    def extract_coordinates(

        self,

        grid,

        target_color
    ):

        coordinates = []

        for row in range(

            len(grid)
        ):

            for col in range(

                len(grid[0])
            ):

                if grid[row][col] == target_color:

                    coordinates.append(

                        (row, col)
                    )

        return coordinates

    # ========================================
    # COMPUTE CENTROID
    # ========================================

    def compute_centroid(

        self,

        coordinates
    ):

        if not coordinates:

            return (0, 0)

        rows = [

            point[0]

            for point in coordinates
        ]

        cols = [

            point[1]

            for point in coordinates
        ]

        return (

            sum(rows) / len(rows),

            sum(cols) / len(cols)
        )

    # ========================================
    # DETECT TRANSLATION
    # ========================================

    def detect_translation(

        self,

        input_grid,

        output_grid
    ):

        input_colors = np.unique(
            input_grid
        )

        output_colors = np.unique(
            output_grid
        )

        shared_colors = [

            color

            for color in input_colors

            if color in output_colors
            and color != 0
        ]

        translations = []

        for color in shared_colors:

            input_coords = (

                self.extract_coordinates(

                    input_grid,

                    color
                )
            )

            output_coords = (

                self.extract_coordinates(

                    output_grid,

                    color
                )
            )

            if not input_coords or not output_coords:

                continue

            input_centroid = (

                self.compute_centroid(
                    input_coords
                )
            )

            output_centroid = (

                self.compute_centroid(
                    output_coords
                )
            )

            delta_row = round(

                output_centroid[0]
                -
                input_centroid[0],

                3
            )

            delta_col = round(

                output_centroid[1]
                -
                input_centroid[1],

                3
            )

            translation_detected = (

                delta_row != 0
                or
                delta_col != 0
            )

            translations.append({

                "color":
                int(color),

                "translation_detected":
                translation_detected,

                "delta_row":
                delta_row,

                "delta_col":
                delta_col,

                "input_centroid":
                input_centroid,

                "output_centroid":
                output_centroid
            })

        return translations

    # ========================================
    # DETECT HORIZONTAL REFLECTION
    # ========================================

    def detect_horizontal_reflection(

        self,

        input_grid,

        output_grid
    ):

        try:

            input_grid = np.array(
                input_grid
            )

            output_grid = np.array(
                output_grid
            )

            # ====================================
            # VALIDATE DIMENSIONS
            # ====================================

            if input_grid.ndim < 2:

                return False

            if output_grid.ndim < 2:

                return False

            # ====================================
            # APPLY REFLECTION
            # ====================================

            reflected = np.fliplr(
                input_grid
            )

            return np.array_equal(

                reflected,

                output_grid
            )

        except Exception:

            return False

    # ========================================
    # DETECT VERTICAL REFLECTION
    # ========================================

    def detect_vertical_reflection(

        self,

        input_grid,

        output_grid
    ):

        try:

            input_grid = np.array(
                input_grid
            )

            output_grid = np.array(
                output_grid
            )

            # ====================================
            # VALIDATE DIMENSIONS
            # ====================================

            if input_grid.ndim < 2:

                return False

            if output_grid.ndim < 2:

                return False

            # ====================================
            # APPLY REFLECTION
            # ====================================

            reflected = np.flipud(
                input_grid
            )

            return np.array_equal(

                reflected,

                output_grid
            )

        except Exception:

            return False

    # ========================================
    # DETECT ROTATION
    # ========================================

    def detect_rotation(

        self,

        input_grid,

        output_grid
    ):

        rotations = []

        try:

            input_grid = np.array(
                input_grid
            )

            output_grid = np.array(
                output_grid
            )

            # ====================================
            # VALIDATE DIMENSIONS
            # ====================================

            if input_grid.ndim < 2:

                return rotations

            if output_grid.ndim < 2:

                return rotations

            # ====================================
            # ROTATION ANALYSIS
            # ====================================

            for rotation_degree in [

                90,

                180,

                270
            ]:

                rotated = np.rot90(

                    input_grid,

                    k=rotation_degree // 90
                )

                rotation_match = np.array_equal(

                    rotated,

                    output_grid
                )

                rotations.append({

                    "rotation":
                    rotation_degree,

                    "matched":
                    rotation_match
                })

        except Exception:

            return rotations

        return rotations

    # ========================================
    # BUILD SPATIAL HYPOTHESES
    # ========================================

    def build_spatial_hypotheses(

        self,

        input_grid,

        output_grid
    ):

        hypotheses = []

        # ====================================
        # TRANSLATION ANALYSIS
        # ====================================

        translations = (

            self.detect_translation(

                input_grid,

                output_grid
            )
        )

        for translation in translations:

            if translation[
                "translation_detected"
            ]:

                hypotheses.append({

                    "type":
                    "object_translation",

                    "category":
                    "spatial",

                    "confidence":
                    0.93,

                    "description":
                    "Detected object translation",

                    "metadata":
                    translation
                })

        # ====================================
        # HORIZONTAL REFLECTION
        # ====================================

        horizontal_reflection = (

            self.detect_horizontal_reflection(

                input_grid,

                output_grid
            )
        )

        if horizontal_reflection:

            hypotheses.append({

                "type":
                "horizontal_reflection",

                "category":
                "spatial",

                "confidence":
                0.95,

                "description":
                "Detected horizontal reflection",

                "metadata":
                {}
            })

        # ====================================
        # VERTICAL REFLECTION
        # ====================================

        vertical_reflection = (

            self.detect_vertical_reflection(

                input_grid,

                output_grid
            )
        )

        if vertical_reflection:

            hypotheses.append({

                "type":
                "vertical_reflection",

                "category":
                "spatial",

                "confidence":
                0.95,

                "description":
                "Detected vertical reflection",

                "metadata":
                {}
            })

        # ====================================
        # ROTATION ANALYSIS
        # ====================================

        rotation_results = (

            self.detect_rotation(

                input_grid,

                output_grid
            )
        )

        for rotation in rotation_results:

            if rotation["matched"]:

                hypotheses.append({

                    "type":
                    "rotation",

                    "category":
                    "spatial",

                    "confidence":
                    0.94,

                    "description":
                    "Detected grid rotation",

                    "metadata":
                    rotation
                })

        # ====================================
        # STORE HISTORY
        # ====================================

        self.spatial_history.append({

            "timestamp":
            str(datetime.utcnow()),

            "hypothesis_count":
            len(hypotheses),

            "hypotheses":
            deepcopy(hypotheses)
        })

        return hypotheses

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "history_size":
            len(self.spatial_history),

            "detected_operations":
            self.detected_operations,

            "engine_state":
            self.engine_state
        }


# ============================================
# GLOBAL ENGINE
# ============================================

spatial_reasoning_engine = (
    SpatialReasoningEngine()
)