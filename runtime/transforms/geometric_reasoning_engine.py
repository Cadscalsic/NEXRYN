# ============================================
# NEXRYN GEOMETRIC REASONING ENGINE
# EXECUTABLE SPATIAL CAUSALITY SYSTEM
# ============================================

from datetime import datetime

import numpy as np


# ============================================
# GEOMETRIC REASONING ENGINE
# ============================================

class GeometricReasoningEngine:

    # ========================================
    # INITIALIZATION
    # ========================================

    def __init__(self):

        self.reasoning_history = []

        self.operator_statistics = {}

        self.geometric_memory = []

        self.causal_patterns = []

    # ========================================
    # SAFE ARRAY
    # ========================================

    def safe_array(
        self,
        grid
    ):

        if grid is None:

            return np.array([])

        if hasattr(
            grid,
            "grid"
        ):

            return np.array(
                grid.grid
            )

        return np.array(grid)

    # ========================================
    # OBJECT COUNT
    # ========================================

    def infer_object_count_delta(

        self,

        input_objects,

        output_objects
    ):

        input_count = len(
            input_objects or []
        )

        output_count = len(
            output_objects or []
        )

        delta = (
            output_count
            -
            input_count
        )

        if delta > 0:

            operator = (
                "duplicate_object"
            )

        elif delta < 0:

            operator = (
                "remove_object"
            )

        else:

            operator = (
                "preserve_objects"
            )

        return {

            "reasoning_type":
            "object_count_delta",

            "input_count":
            input_count,

            "output_count":
            output_count,

            "delta":
            delta,

            "operator":
            operator,

            "confidence":
            0.95
        }

    # ========================================
    # SHAPE ANALYSIS
    # ========================================

    def infer_shape_transformations(

        self,

        input_array,

        output_array
    ):

        input_shape = (
            input_array.shape
        )

        output_shape = (
            output_array.shape
        )

        shape_changed = (
            input_shape != output_shape
        )

        height_growth = (
            output_shape[0]
            -
            input_shape[0]
        )

        width_growth = (
            output_shape[1]
            -
            input_shape[1]
        )

        operator = (
            "preserve_shape"
        )

        if shape_changed:

            if (

                height_growth > 0

                and

                width_growth > 0
            ):

                operator = (
                    "expand_grid"
                )

            elif width_growth > 0:

                operator = (
                    "horizontal_expansion"
                )

            elif height_growth > 0:

                operator = (
                    "vertical_expansion"
                )

            elif (

                height_growth < 0

                or

                width_growth < 0
            ):

                operator = (
                    "shrink_grid"
                )

        return {

            "reasoning_type":
            "shape_transformation",

            "input_shape":
            input_shape,

            "output_shape":
            output_shape,

            "height_growth":
            int(height_growth),

            "width_growth":
            int(width_growth),

            "operator":
            operator,

            "confidence":
            0.94
        }

    # ========================================
    # DENSITY ANALYSIS
    # ========================================

    def infer_density_changes(

        self,

        input_array,

        output_array
    ):

        input_density = int(
            np.count_nonzero(
                input_array
            )
        )

        output_density = int(
            np.count_nonzero(
                output_array
            )
        )

        density_delta = (
            output_density
            -
            input_density
        )

        operator = (
            "preserve_density"
        )

        if density_delta > 0:

            operator = (
                "expand_pattern"
            )

        elif density_delta < 0:

            operator = (
                "reduce_pattern"
            )

        return {

            "reasoning_type":
            "density_change",

            "input_density":
            input_density,

            "output_density":
            output_density,

            "density_delta":
            density_delta,

            "operator":
            operator,

            "confidence":
            0.90
        }

    # ========================================
    # COLOR ANALYSIS
    # ========================================

    def infer_color_transformations(

        self,

        input_array,

        output_array
    ):

        input_colors = set(

            np.unique(
                input_array
            ).tolist()
        )

        output_colors = set(

            np.unique(
                output_array
            ).tolist()
        )

        added_colors = (
            output_colors
            -
            input_colors
        )

        removed_colors = (
            input_colors
            -
            output_colors
        )

        operator = (
            "preserve_colors"
        )

        if added_colors or removed_colors:

            operator = (
                "replace_color"
            )

        return {

            "reasoning_type":
            "color_transformation",

            "input_colors":
            list(input_colors),

            "output_colors":
            list(output_colors),

            "added_colors":
            list(added_colors),

            "removed_colors":
            list(removed_colors),

            "operator":
            operator,

            "confidence":
            0.91
        }

    # ========================================
    # SYMMETRY ANALYSIS
    # ========================================

    def infer_symmetry(

        self,

        input_array,

        output_array
    ):

        horizontal_input = np.array_equal(

            input_array,

            np.fliplr(
                input_array
            )
        )

        vertical_input = np.array_equal(

            input_array,

            np.flipud(
                input_array
            )
        )

        horizontal_output = np.array_equal(

            output_array,

            np.fliplr(
                output_array
            )
        )

        vertical_output = np.array_equal(

            output_array,

            np.flipud(
                output_array
            )
        )

        symmetry_preserved = (

            horizontal_input
            ==
            horizontal_output

            and

            vertical_input
            ==
            vertical_output
        )

        operator = (
            "preserve_symmetry"
        )

        if not symmetry_preserved:

            operator = (
                "modify_symmetry"
            )

        return {

            "reasoning_type":
            "symmetry_analysis",

            "horizontal_input":
            horizontal_input,

            "vertical_input":
            vertical_input,

            "horizontal_output":
            horizontal_output,

            "vertical_output":
            vertical_output,

            "operator":
            operator,

            "confidence":
            0.82
        }

    # ========================================
    # TOPOLOGY ANALYSIS
    # ========================================

    def infer_topology_changes(

        self,

        input_objects,

        output_objects
    ):

        input_sizes = []

        output_sizes = []

        for obj in input_objects:

            if isinstance(
                obj,
                dict
            ):

                size = obj.get(
                    "size",
                    1
                )

                input_sizes.append(
                    size
                )

        for obj in output_objects:

            if isinstance(
                obj,
                dict
            ):

                size = obj.get(
                    "size",
                    1
                )

                output_sizes.append(
                    size
                )

        input_total = sum(
            input_sizes
        )

        output_total = sum(
            output_sizes
        )

        topology_delta = (
            output_total
            -
            input_total
        )

        operator = (
            "preserve_topology"
        )

        if topology_delta > 0:

            operator = (
                "grow_topology"
            )

        elif topology_delta < 0:

            operator = (
                "compress_topology"
            )

        return {

            "reasoning_type":
            "topology_analysis",

            "input_topology":
            input_total,

            "output_topology":
            output_total,

            "topology_delta":
            topology_delta,

            "operator":
            operator,

            "confidence":
            0.89
        }

    # ========================================
    # RANK OPERATORS
    # ========================================

    def rank_operators(
        self,
        reasoning_reports
    ):

        ranked = sorted(

            reasoning_reports,

            key=lambda x: x.get(
                "confidence",
                0.0
            ),

            reverse=True
        )

        return ranked

    # ========================================
    # BUILD EXECUTABLE HYPOTHESES
    # ========================================

    def build_executable_hypotheses(

        self,

        ranked_reports
    ):

        hypotheses = []

        for report in ranked_reports:

            hypothesis = {

                "type":
                report.get(
                    "reasoning_type"
                ),

                "primitive":
                report.get(
                    "operator"
                ),

                "confidence":
                report.get(
                    "confidence",
                    0.0
                ),

                "execution_score":
                round(

                    report.get(
                        "confidence",
                        0.0
                    ) * 0.95,

                    4
                ),

                "geometric_grounding":
                report
            }

            hypotheses.append(
                hypothesis
            )

        return hypotheses

    # ========================================
    # UPDATE STATISTICS
    # ========================================

    def update_statistics(
        self,
        reports
    ):

        for report in reports:

            operator = report.get(
                "operator"
            )

            if operator not in (
                self.operator_statistics
            ):

                self.operator_statistics[
                    operator
                ] = 0

            self.operator_statistics[
                operator
            ] += 1

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_reasoning_report(

        self,

        ranked_reports,

        executable_hypotheses
    ):

        return {

            "reasoning_events":
            len(ranked_reports),

            "generated_hypotheses":
            len(
                executable_hypotheses
            ),

            "top_operator":

            ranked_reports[0].get(
                "operator"
            )

            if ranked_reports

            else None,

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # RUN REASONING
    # ========================================

    def run_reasoning(

        self,

        input_grid,

        output_grid,

        input_objects,

        output_objects
    ):

        input_array = self.safe_array(
            input_grid
        )

        output_array = self.safe_array(
            output_grid
        )

        reasoning_reports = []

        # ====================================
        # OBJECT DELTAS
        # ====================================

        reasoning_reports.append(

            self.infer_object_count_delta(

                input_objects,

                output_objects
            )
        )

        # ====================================
        # SHAPE
        # ====================================

        reasoning_reports.append(

            self.infer_shape_transformations(

                input_array,

                output_array
            )
        )

        # ====================================
        # DENSITY
        # ====================================

        reasoning_reports.append(

            self.infer_density_changes(

                input_array,

                output_array
            )
        )

        # ====================================
        # COLORS
        # ====================================

        reasoning_reports.append(

            self.infer_color_transformations(

                input_array,

                output_array
            )
        )

        # ====================================
        # SYMMETRY
        # ====================================

        reasoning_reports.append(

            self.infer_symmetry(

                input_array,

                output_array
            )
        )

        # ====================================
        # TOPOLOGY
        # ====================================

        reasoning_reports.append(

            self.infer_topology_changes(

                input_objects,

                output_objects
            )
        )

        # ====================================
        # RANKING
        # ====================================

        ranked_reports = (
            self.rank_operators(
                reasoning_reports
            )
        )

        # ====================================
        # EXECUTABLE HYPOTHESES
        # ====================================

        executable_hypotheses = (

            self.build_executable_hypotheses(
                ranked_reports
            )
        )

        # ====================================
        # UPDATE MEMORY
        # ====================================

        self.reasoning_history.append(
            ranked_reports
        )

        self.geometric_memory.append(
            executable_hypotheses
        )

        self.update_statistics(
            ranked_reports
        )

        # ====================================
        # FINAL REPORT
        # ====================================

        reasoning_report = (

            self.build_reasoning_report(

                ranked_reports,

                executable_hypotheses
            )
        )

        return {

            "ranked_reports":
            ranked_reports,

            "executable_hypotheses":
            executable_hypotheses,

            "reasoning_report":
            reasoning_report
        }


# ============================================
# GLOBAL ENGINE
# ============================================

geometric_reasoning_engine = (
    GeometricReasoningEngine()
)