# ============================================
# NEXRYN PRIMITIVE EXECUTOR
# EXECUTABLE SPATIAL OPERATION ENGINE
# ============================================

from datetime import datetime

import copy
import numpy as np


# ============================================
# PRIMITIVE EXECUTOR
# ============================================

class PrimitiveExecutor:

    # ========================================
    # INITIALIZATION
    # ========================================

    def __init__(self):

        self.execution_history = []

        self.execution_failures = []

        self.operator_statistics = {}

        self.execution_memory = []

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
    # REGISTER OPERATOR
    # ========================================

    def register_operator(
        self,
        operator
    ):

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
    # DUPLICATE OBJECT
    # ========================================

    def duplicate_object(

        self,

        grid,

        parameters=None
    ):

        output = np.array(
            grid,
            copy=True
        )

        non_zero = np.argwhere(
            output != 0
        )

        if len(non_zero) == 0:

            return output

        min_row = int(
            np.min(
                non_zero[:, 0]
            )
        )

        max_row = int(
            np.max(
                non_zero[:, 0]
            )
        )

        max_col = int(
            np.max(
                non_zero[:, 1]
            )
        )

        target_col = min(

            output.shape[1] - 1,

            max_col + 2
        )

        for row in range(
            min_row,
            max_row + 1
        ):

            output[
                row,
                target_col
            ] = output[
                non_zero[0][0],
                non_zero[0][1]
            ]

        return output

    # ========================================
    # EXPAND OBJECT
    # ========================================

    def expand_object(

        self,

        grid,

        parameters=None
    ):

        output = np.array(
            grid,
            copy=True
        )

        non_zero = np.argwhere(
            output != 0
        )

        if len(non_zero) == 0:

            return output

        color = output[
            non_zero[0][0],
            non_zero[0][1]
        ]

        min_row = int(
            np.min(
                non_zero[:, 0]
            )
        )

        min_col = int(
            np.min(
                non_zero[:, 1]
            )
        )

        max_row = min(
            min_row + 1,
            output.shape[0] - 1
        )

        max_col = min(
            min_col + 1,
            output.shape[1] - 1
        )

        output[
            min_row:max_row + 1,
            min_col:max_col + 1
        ] = color

        return output

    # ========================================
    # SHRINK OBJECT
    # ========================================

    def shrink_object(

        self,

        grid,

        parameters=None
    ):

        output = np.array(
            grid,
            copy=True
        )

        non_zero = np.argwhere(
            output != 0
        )

        if len(non_zero) == 0:

            return output

        for row, col in non_zero[1:]:

            output[
                row,
                col
            ] = 0

        return output

    # ========================================
    # REMOVE OBJECT
    # ========================================

    def remove_object(

        self,

        grid,

        parameters=None
    ):

        output = np.array(
            grid,
            copy=True
        )

        non_zero = np.argwhere(
            output != 0
        )

        if len(non_zero) == 0:

            return output

        row, col = non_zero[-1]

        output[
            row,
            col
        ] = 0

        return output

    # ========================================
    # EXPAND GRID
    # ========================================

    def expand_grid(

        self,

        grid,

        parameters=None
    ):

        output = np.array(
            grid,
            copy=True
        )

        height_growth = 1
        width_growth = 1

        if parameters:

            height_growth = parameters.get(
                "height_growth",
                1
            )

            width_growth = parameters.get(
                "width_growth",
                1
            )

        new_height = (
            output.shape[0]
            +
            max(height_growth, 0)
        )

        new_width = (
            output.shape[1]
            +
            max(width_growth, 0)
        )

        expanded = np.zeros(

            (
                new_height,
                new_width
            ),

            dtype=output.dtype
        )

        expanded[
            :output.shape[0],
            :output.shape[1]
        ] = output

        return expanded

    # ========================================
    # SHRINK GRID
    # ========================================

    def shrink_grid(

        self,

        grid,

        parameters=None
    ):

        output = np.array(
            grid,
            copy=True
        )

        if (

            output.shape[0] <= 1

            or

            output.shape[1] <= 1
        ):

            return output

        return output[
            :-1,
            :-1
        ]

    # ========================================
    # TRANSLATE RIGHT
    # ========================================

    def translate_right(

        self,

        grid,

        parameters=None
    ):

        steps = 1

        if parameters:

            translation = parameters.get(
                "translation"
            )

            if translation:

                steps = abs(
                    int(
                        translation[1]
                    )
                )

        output = np.zeros_like(
            grid
        )

        if steps <= 0:

            return np.array(
                grid,
                copy=True
            )

        output[
            :,
            steps:
        ] = grid[
            :,
            :-steps
        ]

        return output

    # ========================================
    # TRANSLATE LEFT
    # ========================================

    def translate_left(

        self,

        grid,

        parameters=None
    ):

        steps = 1

        if parameters:

            translation = parameters.get(
                "translation"
            )

            if translation:

                steps = abs(
                    int(
                        translation[1]
                    )
                )

        output = np.zeros_like(
            grid
        )

        if steps <= 0:

            return np.array(
                grid,
                copy=True
            )

        output[
            :,
            :-steps
        ] = grid[
            :,
            steps:
        ]

        return output

    # ========================================
    # TRANSLATE UP
    # ========================================

    def translate_up(

        self,

        grid,

        parameters=None
    ):

        steps = 1

        if parameters:

            translation = parameters.get(
                "translation"
            )

            if translation:

                steps = abs(
                    int(
                        translation[0]
                    )
                )

        output = np.zeros_like(
            grid
        )

        if steps <= 0:

            return np.array(
                grid,
                copy=True
            )

        output[
            :-steps,
            :
        ] = grid[
            steps:,
            :
        ]

        return output

    # ========================================
    # TRANSLATE DOWN
    # ========================================

    def translate_down(

        self,

        grid,

        parameters=None
    ):

        steps = 1

        if parameters:

            translation = parameters.get(
                "translation"
            )

            if translation:

                steps = abs(
                    int(
                        translation[0]
                    )
                )

        output = np.zeros_like(
            grid
        )

        if steps <= 0:

            return np.array(
                grid,
                copy=True
            )

        output[
            steps:,
            :
        ] = grid[
            :-steps,
            :
        ]

        return output

    # ========================================
    # REPLACE COLOR
    # ========================================

    def replace_color(

        self,

        grid,

        parameters=None
    ):

        output = np.array(
            grid,
            copy=True
        )

        removed_colors = []

        added_colors = []

        if parameters:

            removed_colors = parameters.get(
                "removed_colors",
                []
            )

            added_colors = parameters.get(
                "added_colors",
                []
            )

        if not removed_colors:

            removed_colors = [

                color

                for color in np.unique(
                    output
                )

                if color != 0
            ]

        if not added_colors:

            added_colors = [
                removed_colors[0] + 1
            ] if removed_colors else []

        if not removed_colors or not added_colors:

            return output

        old_color = removed_colors[0]

        new_color = added_colors[0]

        output[
            output == old_color
        ] = new_color

        return output

    # ========================================
    # EXPAND PATTERN
    # ========================================

    def expand_pattern(

        self,

        grid,

        parameters=None
    ):

        output = np.array(
            grid,
            copy=True
        )

        non_zero = np.argwhere(
            output != 0
        )

        for row, col in non_zero:

            for dy in [-1, 0, 1]:

                for dx in [-1, 0, 1]:

                    nr = row + dy
                    nc = col + dx

                    if (

                        0 <= nr < output.shape[0]

                        and

                        0 <= nc < output.shape[1]
                    ):

                        output[
                            nr,
                            nc
                        ] = output[
                            row,
                            col
                        ]

        return output

    # ========================================
    # GROW TOPOLOGY
    # ========================================

    def grow_topology(

        self,

        grid,

        parameters=None
    ):

        output = np.array(
            grid,
            copy=True
        )

        non_zero = np.argwhere(
            output != 0
        )

        if len(non_zero) == 0:

            return output

        for row, col in non_zero:

            if row + 1 < output.shape[0]:

                output[
                    row + 1,
                    col
                ] = output[
                    row,
                    col
                ]

        return output

    # ========================================
    # MIRROR OBJECT
    # ========================================

    def mirror_object(

        self,

        grid,

        parameters=None
    ):

        return np.fliplr(
            grid
        )

    # ========================================
    # PRESERVE GRID
    # ========================================

    def preserve_grid(

        self,

        grid,

        parameters=None
    ):

        return np.array(
            grid,
            copy=True
        )

    # ========================================
    # EXECUTE PRIMITIVE
    # ========================================

    def execute_primitive(

        self,

        grid,

        primitive
    ):

        primitive_name = (
            primitive.get(
                "primitive"
            )
        )

        parameters = (
            primitive.get(
                "parameters",
                {}
            )
        )

        self.register_operator(
            primitive_name
        )

        execution_map = {

            "duplicate_object":
            self.duplicate_object,

            "remove_object":
            self.remove_object,

            "expand_object":
            self.expand_object,

            "shrink_object":
            self.shrink_object,

            "expand_grid":
            self.expand_grid,

            "horizontal_expansion":
            self.expand_grid,

            "vertical_expansion":
            self.expand_grid,

            "shrink_grid":
            self.shrink_grid,

            "translate_right":
            self.translate_right,

            "translate_left":
            self.translate_left,

            "translate_up":
            self.translate_up,

            "translate_down":
            self.translate_down,

            "replace_color":
            self.replace_color,

            "expand_pattern":
            self.expand_pattern,

            "grow_topology":
            self.grow_topology,

            "mirror_object":
            self.mirror_object,

            "preserve_objects":
            self.preserve_grid,

            "preserve_shape":
            self.preserve_grid,

            "preserve_density":
            self.preserve_grid,

            "preserve_colors":
            self.preserve_grid,

            "preserve_topology":
            self.preserve_grid,

            "preserve_symmetry":
            self.preserve_grid
        }

        execution_function = (
            execution_map.get(
                primitive_name
            )
        )

        if execution_function is None:

            return np.array(
                grid,
                copy=True
            )

        return execution_function(

            grid,

            parameters
        )

    # ========================================
    # EXECUTION PIPELINE
    # ========================================

    def execute_pipeline(

        self,

        input_grid,

        primitives
    ):

        working_grid = self.safe_array(
            input_grid
        )

        execution_trace = []

        primitives = primitives or []

        for primitive in primitives:

            primitive_name = (
                primitive.get(
                    "primitive",
                    "unknown"
                )
            )

            try:

                previous_grid = np.array(
                    working_grid,
                    copy=True
                )

                working_grid = (

                    self.execute_primitive(

                        working_grid,

                        primitive
                    )
                )

                execution_event = {

                    "primitive":
                    primitive_name,

                    "status":
                    "completed",

                    "input_shape":
                    previous_grid.shape,

                    "output_shape":
                    working_grid.shape,

                    "timestamp":
                    str(datetime.utcnow())
                }

            except Exception as error:

                execution_event = {

                    "primitive":
                    primitive_name,

                    "status":
                    "failed",

                    "error":
                    repr(error),

                    "timestamp":
                    str(datetime.utcnow())
                }

                self.execution_failures.append(
                    execution_event
                )

            execution_trace.append(
                execution_event
            )

        self.execution_history.append(
            execution_trace
        )

        self.execution_memory.append({

            "primitive_count":
            len(primitives),

            "final_shape":
            working_grid.shape,

            "timestamp":
            str(datetime.utcnow())
        })

        return {

            "output_grid":
            working_grid,

            "execution_trace":
            execution_trace,

            "execution_success":
            True
        }

    # ========================================
    # BUILD EXECUTION REPORT
    # ========================================

    def build_execution_report(

        self,

        execution_trace,

        output_grid
    ):

        successful = len([

            event

            for event in execution_trace

            if event.get(
                "status"
            ) == "completed"
        ])

        failed = len([

            event

            for event in execution_trace

            if event.get(
                "status"
            ) == "failed"
        ])

        return {

            "executed_primitives":
            len(execution_trace),

            "successful_executions":
            successful,

            "failed_executions":
            failed,

            "final_output_shape":
            output_grid.shape,

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # RUN EXECUTION
    # ========================================

    def run_execution(

        self,

        input_grid,

        primitives
    ):

        execution_result = (

            self.execute_pipeline(

                input_grid,

                primitives
            )
        )

        output_grid = (
            execution_result.get(
                "output_grid"
            )
        )

        execution_trace = (
            execution_result.get(
                "execution_trace",
                []
            )
        )

        execution_report = (

            self.build_execution_report(

                execution_trace,

                output_grid
            )
        )

        return {

            "output_grid":
            output_grid,

            "execution_trace":
            execution_trace,

            "execution_report":
            execution_report
        }


# ============================================
# GLOBAL EXECUTOR
# ============================================

primitive_executor = (
    PrimitiveExecutor()
)
