# ============================================
# NEXRYN TRANSFORMATION OPERATOR LIBRARY
# ============================================

import numpy as np

from copy import deepcopy


# ============================================
# TRANSFORMATION OPERATOR LIBRARY
# ============================================

class TransformationOperatorLibrary:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.operator_history = []

        self.available_operators = [

            "replace_color",

            "translate_object",

            "move_object",

            "mirror_pattern",

            "rotate_pattern",

            "duplicate_object",

            "expand_object",

            "fill_region",

            "connect_objects"
        ]

    # ========================================
    # REPLACE COLOR
    # ========================================

    def replace_color(

        self,

        grid,

        source_color,

        target_color
    ):

        grid = np.array(
            deepcopy(grid)
        )

        grid[
            grid == source_color
        ] = target_color

        return grid

    # ========================================
    # TRANSLATE OBJECT
    # ========================================

    def translate_object(

        self,

        grid,

        source_color,

        delta_row,

        delta_col
    ):

        grid = np.array(
            deepcopy(grid)
        )

        translated_grid = np.zeros_like(
            grid
        )

        coordinates = np.argwhere(

            grid == source_color
        )

        for row, col in coordinates:

            new_row = row + delta_row

            new_col = col + delta_col

            if (

                0 <= new_row < grid.shape[0]

                and

                0 <= new_col < grid.shape[1]
            ):

                translated_grid[
                    new_row,
                    new_col
                ] = source_color

        return translated_grid

    # ========================================
    # MOVE OBJECT
    # ========================================

    def move_object(

        self,

        grid,

        source_color,

        target_row,

        target_col
    ):

        grid = np.array(
            deepcopy(grid)
        )

        moved_grid = np.zeros_like(
            grid
        )

        coordinates = np.argwhere(

            grid == source_color
        )

        if len(coordinates) == 0:

            return moved_grid

        base_row, base_col = (
            coordinates[0]
        )

        delta_row = (
            target_row - base_row
        )

        delta_col = (
            target_col - base_col
        )

        for row, col in coordinates:

            new_row = row + delta_row

            new_col = col + delta_col

            if (

                0 <= new_row < grid.shape[0]

                and

                0 <= new_col < grid.shape[1]
            ):

                moved_grid[
                    new_row,
                    new_col
                ] = source_color

        return moved_grid

    # ========================================
    # MIRROR PATTERN
    # ========================================

    def mirror_pattern(

        self,

        grid,

        axis="horizontal"
    ):

        grid = np.array(
            deepcopy(grid)
        )

        if axis == "horizontal":

            return np.fliplr(grid)

        return np.flipud(grid)

    # ========================================
    # ROTATE PATTERN
    # ========================================

    def rotate_pattern(

        self,

        grid,

        degrees=90
    ):

        grid = np.array(
            deepcopy(grid)
        )

        return np.rot90(

            grid,

            k=degrees // 90
        )

    # ========================================
    # DUPLICATE OBJECT
    # ========================================

    def duplicate_object(

        self,

        grid,

        source_color,

        offset_row,

        offset_col
    ):

        grid = np.array(
            deepcopy(grid)
        )

        duplicated_grid = np.array(
            deepcopy(grid)
        )

        coordinates = np.argwhere(

            grid == source_color
        )

        for row, col in coordinates:

            new_row = row + offset_row

            new_col = col + offset_col

            if (

                0 <= new_row < grid.shape[0]

                and

                0 <= new_col < grid.shape[1]
            ):

                duplicated_grid[
                    new_row,
                    new_col
                ] = source_color

        return duplicated_grid

    # ========================================
    # EXPAND OBJECT
    # ========================================

    def expand_object(

        self,

        grid,

        source_color
    ):

        grid = np.array(
            deepcopy(grid)
        )

        expanded_grid = np.array(
            deepcopy(grid)
        )

        coordinates = np.argwhere(

            grid == source_color
        )

        directions = [

            (-1, 0),

            (1, 0),

            (0, -1),

            (0, 1)
        ]

        for row, col in coordinates:

            for d_row, d_col in directions:

                new_row = row + d_row

                new_col = col + d_col

                if (

                    0 <= new_row < grid.shape[0]

                    and

                    0 <= new_col < grid.shape[1]
                ):

                    expanded_grid[
                        new_row,
                        new_col
                    ] = source_color

        return expanded_grid

    # ========================================
    # FILL REGION
    # ========================================

    def fill_region(

        self,

        grid,

        target_color
    ):

        grid = np.array(
            deepcopy(grid)
        )

        filled_grid = np.array(
            deepcopy(grid)
        )

        filled_grid[
            filled_grid == 0
        ] = target_color

        return filled_grid

    # ========================================
    # CONNECT OBJECTS
    # ========================================

    def connect_objects(

        self,

        grid,

        source_color
    ):

        grid = np.array(
            deepcopy(grid)
        )

        connected_grid = np.array(
            deepcopy(grid)
        )

        coordinates = np.argwhere(

            grid == source_color
        )

        if len(coordinates) < 2:

            return connected_grid

        sorted_coordinates = sorted(

            coordinates,

            key=lambda point:

            (
                point[0],
                point[1]
            )
        )

        for index in range(

            len(sorted_coordinates) - 1
        ):

            row_a, col_a = (
                sorted_coordinates[index]
            )

            row_b, col_b = (
                sorted_coordinates[index + 1]
            )

            # ====================================
            # HORIZONTAL CONNECTION
            # ====================================

            for col in range(

                min(col_a, col_b),

                max(col_a, col_b) + 1
            ):

                connected_grid[
                    row_a,
                    col
                ] = source_color

            # ====================================
            # VERTICAL CONNECTION
            # ====================================

            for row in range(

                min(row_a, row_b),

                max(row_a, row_b) + 1
            ):

                connected_grid[
                    row,
                    col_b
                ] = source_color

        return connected_grid

    # ========================================
    # APPLY OPERATOR
    # ========================================

    def apply_operator(

        self,

        operator_name,

        grid,

        parameters={}
    ):

        if not hasattr(

            self,

            operator_name
        ):

            return grid

        operator = getattr(

            self,

            operator_name
        )

        try:

            result = operator(

                grid,

                **parameters
            )

            self.operator_history.append({

                "operator":
                operator_name,

                "parameters":
                parameters,

                "success":
                True
            })

            return result

        except Exception:

            self.operator_history.append({

                "operator":
                operator_name,

                "parameters":
                parameters,

                "success":
                False
            })

            return grid

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        return {

            "available_operators":

            self.available_operators,

            "operator_count":

            len(
                self.available_operators
            ),

            "history_size":

            len(
                self.operator_history
            )
        }


# ============================================
# GLOBAL LIBRARY
# ============================================

transformation_operator_library = (
    TransformationOperatorLibrary()
)