# ============================================
# NEXRYN SPATIAL OPERATOR LIBRARY
# EXECUTABLE SPATIAL PRIMITIVE SYSTEM
# ============================================

from datetime import datetime

import numpy as np


# ============================================
# SPATIAL OPERATOR LIBRARY
# ============================================

class SpatialOperatorLibrary:

    # ========================================
    # INITIALIZATION
    # ========================================

    def __init__(self):

        self.operator_registry = {}

        self.execution_history = []

        self.operator_statistics = {}

        self.failed_operations = []

        self.register_default_operators()

    # ========================================
    # REGISTER OPERATOR
    # ========================================

    def register_operator(

        self,

        operator_name,

        operator_function
    ):

        self.operator_registry[
            operator_name
        ] = operator_function

        if operator_name not in (
            self.operator_statistics
        ):

            self.operator_statistics[
                operator_name
            ] = 0

    # ========================================
    # REGISTER DEFAULT OPERATORS
    # ========================================

    def register_default_operators(self):

        self.register_operator(
            "duplicate_object",
            self.duplicate_object
        )

        self.register_operator(
            "remove_object",
            self.remove_object
        )

        self.register_operator(
            "expand_grid",
            self.expand_grid
        )

        self.register_operator(
            "horizontal_expansion",
            self.horizontal_expansion
        )

        self.register_operator(
            "vertical_expansion",
            self.vertical_expansion
        )

        self.register_operator(
            "translate_right",
            self.translate_right
        )

        self.register_operator(
            "translate_left",
            self.translate_left
        )

        self.register_operator(
            "translate_up",
            self.translate_up
        )

        self.register_operator(
            "translate_down",
            self.translate_down
        )

        self.register_operator(
            "replace_color",
            self.replace_color
        )

        self.register_operator(
            "mirror_object",
            self.mirror_object
        )

        self.register_operator(
            "rotate_clockwise",
            self.rotate_clockwise
        )

        self.register_operator(
            "rotate_counterclockwise",
            self.rotate_counterclockwise
        )

        self.register_operator(
            "expand_pattern",
            self.expand_pattern
        )

        self.register_operator(
            "grow_topology",
            self.grow_topology
        )

        self.register_operator(
            "flood_fill",
            self.flood_fill
        )

        self.register_operator(
            "draw_line",
            self.draw_line
        )

        self.register_operator(
            "preserve_grid",
            self.preserve_grid
        )

    # ========================================
    # SAFE GRID
    # ========================================

    def safe_grid(
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
    # UPDATE STATS
    # ========================================

    def update_stats(
        self,
        operator_name
    ):

        if operator_name not in (
            self.operator_statistics
        ):

            self.operator_statistics[
                operator_name
            ] = 0

        self.operator_statistics[
            operator_name
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

        for row, col in non_zero:

            new_col = col + 1

            if new_col < output.shape[1]:

                output[
                    row,
                    new_col
                ] = output[
                    row,
                    col
                ]

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
    # HORIZONTAL EXPANSION
    # ========================================

    def horizontal_expansion(

        self,

        grid,

        parameters=None
    ):

        return self.expand_grid(

            grid,

            {

                "height_growth": 0,

                "width_growth": 1
            }
        )

    # ========================================
    # VERTICAL EXPANSION
    # ========================================

    def vertical_expansion(

        self,

        grid,

        parameters=None
    ):

        return self.expand_grid(

            grid,

            {

                "height_growth": 1,

                "width_growth": 0
            }
        )

    # ========================================
    # TRANSLATE RIGHT
    # ========================================

    def translate_right(

        self,

        grid,

        parameters=None
    ):

        output = np.zeros_like(
            grid
        )

        output[
            :,
            1:
        ] = grid[
            :,
            :-1
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

        output = np.zeros_like(
            grid
        )

        output[
            :,
            :-1
        ] = grid[
            :,
            1:
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

        output = np.zeros_like(
            grid
        )

        output[
            :-1,
            :
        ] = grid[
            1:,
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

        output = np.zeros_like(
            grid
        )

        output[
            1:,
            :
        ] = grid[
            :-1,
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

        unique_colors = [

            c

            for c in np.unique(
                output
            )

            if c != 0
        ]

        if not unique_colors:

            return output

        old_color = unique_colors[0]

        new_color = old_color + 1

        output[
            output == old_color
        ] = new_color

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
    # ROTATE CLOCKWISE
    # ========================================

    def rotate_clockwise(

        self,

        grid,

        parameters=None
    ):

        return np.rot90(
            grid,
            -1
        )

    # ========================================
    # ROTATE COUNTERCLOCKWISE
    # ========================================

    def rotate_counterclockwise(

        self,

        grid,

        parameters=None
    ):

        return np.rot90(
            grid,
            1
        )

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
    # FLOOD FILL
    # ========================================

    def flood_fill(

        self,

        grid,

        parameters=None
    ):

        output = np.array(
            grid,
            copy=True
        )

        fill_color = 1

        if parameters:

            fill_color = parameters.get(
                "fill_color",
                1
            )

        output[
            output == 0
        ] = fill_color

        return output

    # ========================================
    # DRAW LINE
    # ========================================

    def draw_line(

        self,

        grid,

        parameters=None
    ):

        output = np.array(
            grid,
            copy=True
        )

        line_color = 1

        if parameters:

            line_color = parameters.get(
                "line_color",
                1
            )

        np.fill_diagonal(
            output,
            line_color
        )

        return output

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
    # EXECUTE OPERATOR
    # ========================================

    def execute_operator(

        self,

        operator_name,

        grid,

        parameters=None
    ):

        grid = self.safe_grid(
            grid
        )

        operator_function = (

            self.operator_registry.get(
                operator_name
            )
        )

        if operator_function is None:

            self.failed_operations.append({

                "operator":
                operator_name,

                "error":
                "operator_not_found",

                "timestamp":
                str(datetime.utcnow())
            })

            return grid

        try:

            output = operator_function(

                grid,

                parameters
            )

            self.update_stats(
                operator_name
            )

            self.execution_history.append({

                "operator":
                operator_name,

                "status":
                "completed",

                "timestamp":
                str(datetime.utcnow())
            })

            return output

        except Exception as error:

            self.failed_operations.append({

                "operator":
                operator_name,

                "error":
                repr(error),

                "timestamp":
                str(datetime.utcnow())
            })

            return grid

    # ========================================
    # EXECUTE PIPELINE
    # ========================================

    def execute_pipeline(

        self,

        input_grid,

        operators
    ):

        working_grid = self.safe_grid(
            input_grid
        )

        execution_trace = []

        for operator in operators:

            operator_name = (
                operator.get(
                    "primitive"
                )
            )

            parameters = (
                operator.get(
                    "parameters",
                    {}
                )
            )

            previous_shape = (
                working_grid.shape
            )

            working_grid = (

                self.execute_operator(

                    operator_name,

                    working_grid,

                    parameters
                )
            )

            execution_trace.append({

                "operator":
                operator_name,

                "input_shape":
                previous_shape,

                "output_shape":
                working_grid.shape,

                "timestamp":
                str(datetime.utcnow())
            })

        return {

            "output_grid":
            working_grid,

            "execution_trace":
            execution_trace
        }

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_library_report(self):

        return {

            "registered_operators":
            len(
                self.operator_registry
            ),

            "executions":
            len(
                self.execution_history
            ),

            "failures":
            len(
                self.failed_operations
            ),

            "operator_statistics":
            self.operator_statistics,

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL LIBRARY
# ============================================

spatial_operator_library = (
    SpatialOperatorLibrary()
)