# ============================================
# NEXRYN PRIMITIVE EXECUTOR
# EXECUTABLE SPATIAL OPERATION ENGINE
# ============================================

from datetime import datetime

import copy
import numpy as np

from core.perception import ObjectExtractor


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

        parameters = parameters or {}

        non_zero = np.argwhere(
            output != 0
        )

        if len(non_zero) == 0:

            return output

        relative_offset = parameters.get(
            "relative_offset"
        )

        placement_vector = parameters.get(
            "placement_vector",
            {}
        )

        if relative_offset or placement_vector:

            if relative_offset:

                delta_row = int(
                    relative_offset[0]
                )

                delta_col = int(
                    relative_offset[1]
                )

            else:

                delta_row = int(
                    placement_vector.get(
                        "delta_row",
                        0
                    )
                )

                delta_col = int(
                    placement_vector.get(
                        "delta_col",
                        0
                    )
                )

            source_object = parameters.get(
                "source_object",
                parameters.get(
                    "anchor_object"
                )
            )

            source_cells = self._source_object_cells(
                output,
                source_object
            )

            for row, col in source_cells:

                target_row = row + delta_row

                target_col = col + delta_col

                if (

                    0 <= target_row < output.shape[0]

                    and

                    0 <= target_col < output.shape[1]
                ):

                    output[
                        target_row,
                        target_col
                    ] = output[
                        row,
                        col
                    ]

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

    def _source_object_cells(

        self,

        grid,

        source_object=None
    ):

        try:

            extractor = ObjectExtractor()

            objects = extractor.extract_objects(
                extractor.normalize_grid(
                    grid
                )
            )

            selected = None

            for candidate in objects:

                if candidate.get(
                    "id"
                ) == source_object:

                    selected = candidate

                    break

            if selected is None and objects:

                selected = objects[0]

            if selected is not None:

                return [
                    (
                        int(row),
                        int(col)
                    )
                    for row, col in selected.get(
                        "cells",
                        []
                    )
                ]

        except Exception:

            pass

        return [
            (
                int(row),
                int(col)
            )
            for row, col in np.argwhere(
                grid != 0
            )
        ]

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

        parameters = parameters or {}

        background_color = int(
            parameters.get(
                "background_color",
                0
            )
        )

        cells_to_clear = parameters.get(
            "cells_to_clear",
            []
        ) or []

        if cells_to_clear:

            for row, col in cells_to_clear:

                output[
                    int(row),
                    int(col)
                ] = background_color

            return output

        remove_colors = parameters.get(
            "remove_colors",
            []
        ) or []

        if remove_colors:

            for color in remove_colors:

                output[
                    output == int(color)
                ] = background_color

            return output

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

            if parameters.get("scale_mode") == "cell_repeat":

                row_scale = int(
                    parameters.get(
                        "row_scale",
                        parameters.get(
                            "scale_factor",
                            1
                        )
                    )
                )

                col_scale = int(
                    parameters.get(
                        "col_scale",
                        parameters.get(
                            "scale_factor",
                            1
                        )
                    )
                )

                return np.repeat(
                    np.repeat(
                        output,
                        max(row_scale, 1),
                        axis=0
                    ),
                    max(col_scale, 1),
                    axis=1
                )

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
    # OBJECT LEVEL TRANSLATE
    # ========================================

    def object_level_translate(

        self,

        grid,

        parameters=None
    ):

        output = np.array(
            grid,
            copy=True
        )

        parameters = parameters or {}

        translation_per_object = parameters.get(
            "translation_per_object",
            {}
        )

        if not isinstance(translation_per_object, dict):

            return output

        try:

            extractor = ObjectExtractor()

            objects = extractor.extract_objects(
                extractor.normalize_grid(
                    output
                )
            )

        except Exception:

            objects = []

        movable_objects = set(
            parameters.get(
                "movable_objects",
                []
            )
        )

        fixed_objects = set(
            parameters.get(
                "fixed_objects",
                []
            )
        )

        for obj in objects:

            object_id = obj.get(
                "id"
            )

            if object_id in fixed_objects:

                continue

            if movable_objects and object_id not in movable_objects:

                continue

            translation = translation_per_object.get(
                object_id,
                (0, 0)
            )

            if tuple(translation) == (0, 0):

                continue

            for row, col in obj.get(
                "cells",
                []
            ):

                output[
                    int(row),
                    int(col)
                ] = 0

        for obj in objects:

            object_id = obj.get(
                "id"
            )

            if object_id in fixed_objects:

                continue

            if movable_objects and object_id not in movable_objects:

                continue

            translation = translation_per_object.get(
                object_id,
                (0, 0)
            )

            delta_row, delta_col = (
                int(translation[0]),
                int(translation[1])
            )

            for row, col in obj.get(
                "cells",
                []
            ):

                target_row = int(row) + delta_row

                target_col = int(col) + delta_col

                if (
                    0 <= target_row < output.shape[0]
                    and
                    0 <= target_col < output.shape[1]
                ):

                    output[
                        target_row,
                        target_col
                    ] = int(
                        obj.get(
                            "color",
                            output[int(row), int(col)]
                        )
                    )

        return output

    # ========================================
    # GENERIC TRANSLATE
    # ========================================

    def translate(

        self,

        grid,

        parameters=None
    ):

        output = np.zeros_like(
            grid
        )

        parameters = parameters or {}

        translation = parameters.get(
            "translation",
            [
                parameters.get("delta_row", 0),
                parameters.get("delta_col", 0)
            ]
        )

        delta_row = int(
            translation[0]
        )

        delta_col = int(
            translation[1]
        )

        for row, col in np.argwhere(
            grid != 0
        ):

            target_row = int(row) + delta_row

            target_col = int(col) + delta_col

            if (
                0 <= target_row < output.shape[0]
                and
                0 <= target_col < output.shape[1]
            ):

                output[
                    target_row,
                    target_col
                ] = grid[
                    row,
                    col
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

        parameters = parameters or {}

        mapping = (
            parameters.get("mapping")
            or parameters.get("color_mapping")
            or {}
        )

        if mapping:

            original = np.array(
                output,
                copy=True
            )

            for old_color, new_color in mapping.items():

                output[
                    original == int(old_color)
                ] = int(new_color)

            return output

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

            source_color = parameters.get(
                "source_color"
            )

            target_color = parameters.get(
                "target_color"
            )

            if source_color is not None and target_color is not None:

                removed_colors = [source_color]

                added_colors = [target_color]

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
    # MIRROR VERTICAL
    # ========================================

    def mirror_vertical(

        self,

        grid,

        parameters=None
    ):

        return np.flipud(
            grid
        )

    # ========================================
    # ROTATE GRID
    # ========================================

    def rotate_grid(

        self,

        grid,

        parameters=None
    ):

        parameters = parameters or {}

        degrees = int(
            parameters.get(
                "degrees",
                parameters.get(
                    "rotation",
                    90
                )
            )
        )

        return np.rot90(
            grid,
            k=(degrees // 90) % 4
        )

    # ========================================
    # CONSTRUCT PATH
    # ========================================

    def construct_path(

        self,

        grid,

        parameters=None
    ):

        output = np.array(
            grid,
            copy=True
        )

        parameters = parameters or {}

        path_cells = parameters.get(
            "path_cells",
            []
        ) or []

        if path_cells:

            path_color = int(
                parameters.get(
                    "path_color",
                    1
                )
            )

            for row, col in path_cells:

                output[
                    int(row),
                    int(col)
                ] = path_color

            return output

        non_zero = np.argwhere(
            output != 0
        )

        if len(non_zero) < 2:

            return output

        start = parameters.get(
            "start",
            non_zero[0].tolist()
        )

        end = parameters.get(
            "end",
            non_zero[-1].tolist()
        )

        path_color = int(
            parameters.get(
                "path_color",
                output[
                    int(start[0]),
                    int(start[1])
                ]
            )
        )

        row = int(start[0])

        col = int(start[1])

        end_row = int(end[0])

        end_col = int(end[1])

        while row != end_row:

            output[
                row,
                col
            ] = path_color

            row += 1 if end_row > row else -1

        while col != end_col:

            output[
                row,
                col
            ] = path_color

            col += 1 if end_col > col else -1

        output[
            end_row,
            end_col
        ] = path_color

        return output

    # ========================================
    # CONNECT COMPONENTS
    # ========================================

    def connect_components(

        self,

        grid,

        parameters=None
    ):

        return self.construct_path(
            grid,
            parameters
        )

    # ========================================
    # FILL REGION
    # ========================================

    def fill_region(

        self,

        grid,

        parameters=None
    ):

        output = np.array(
            grid,
            copy=True
        )

        parameters = parameters or {}

        fill_color = int(
            parameters.get(
                "fill_color",
                parameters.get(
                    "path_color",
                    1
                )
            )
        )

        non_zero = np.argwhere(
            output != 0
        )

        if len(non_zero) == 0:

            return output

        min_row = int(np.min(non_zero[:, 0]))
        max_row = int(np.max(non_zero[:, 0]))
        min_col = int(np.min(non_zero[:, 1]))
        max_col = int(np.max(non_zero[:, 1]))

        region = output[
            min_row:max_row + 1,
            min_col:max_col + 1
        ]

        region[
            region == 0
        ] = fill_color

        output[
            min_row:max_row + 1,
            min_col:max_col + 1
        ] = region

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

            "object_level_translate":
            self.object_level_translate,

            "translate":
            self.translate,

            "replace_color":
            self.replace_color,

            "expand_pattern":
            self.expand_pattern,

            "grow_topology":
            self.grow_topology,

            "mirror_object":
            self.mirror_object,

            "mirror_horizontal":
            self.mirror_object,

            "mirror_vertical":
            self.mirror_vertical,

            "rotate":
            self.rotate_grid,

            "rotate_grid":
            self.rotate_grid,

            "construct_path":
            self.construct_path,

            "connect_components":
            self.connect_components,

            "bridge_creation":
            self.connect_components,

            "topological_change":
            self.construct_path,

            "topological_reasoning":
            self.construct_path,

            "fill_region":
            self.fill_region,

            "recolor":
            self.replace_color,

            "duplicate":
            self.duplicate_object,

            "replicate":
            self.duplicate_object,

            "grow":
            self.grow_topology,

            "expand":
            self.expand_pattern,

            "scale_up":
            self.expand_grid,

            "scale_down":
            self.shrink_grid,

            "preserve_grid":
            self.preserve_grid,

            "preserve_objects":
            self.preserve_grid,

            "preserve_size":
            self.preserve_grid,

            "preserve_shape":
            self.preserve_grid,

            "preserve_density":
            self.preserve_grid,

            "density_modulation":
            self.expand_pattern,

            "pattern_completion":
            self.expand_pattern,

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
