# ============================================
# NEXRYN SPATIAL OPERATOR ENGINE
# ============================================

import numpy as np

from copy import deepcopy

from datetime import datetime

from runtime.synthesis.transformation_operator_library import (

    transformation_operator_library
)


# ============================================
# SPATIAL OPERATOR ENGINE
# ============================================

class SpatialOperatorEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.execution_history = []

        self.operator_library = (
            transformation_operator_library
        )

        self.engine_state = {

            "spatial_execution":
            True,

            "coordinate_manipulation":
            True,

            "topology_execution":
            True,

            "movement_execution":
            True,

            "adaptive_spatial_planning":
            True
        }

    # ========================================
    # EXECUTE TRANSLATION
    # ========================================

    def execute_translation(

        self,

        grid,

        parameters
    ):

        return (

            self.operator_library
            .translate_object(

                grid,

                source_color=

                parameters.get(
                    "source_color",
                    1
                ),

                delta_row=

                parameters.get(
                    "delta_row",
                    0
                ),

                delta_col=

                parameters.get(
                    "delta_col",
                    0
                )
            )
        )

    # ========================================
    # EXECUTE MIRROR
    # ========================================

    def execute_mirror(

        self,

        grid,

        parameters
    ):

        return (

            self.operator_library
            .mirror_pattern(

                grid,

                axis=

                parameters.get(
                    "axis",
                    "horizontal"
                )
            )
        )

    # ========================================
    # EXECUTE ROTATION
    # ========================================

    def execute_rotation(

        self,

        grid,

        parameters
    ):

        return (

            self.operator_library
            .rotate_pattern(

                grid,

                degrees=

                parameters.get(
                    "degrees",
                    90
                )
            )
        )

    # ========================================
    # EXECUTE EXPANSION
    # ========================================

    def execute_expansion(

        self,

        grid,

        parameters
    ):

        return (

            self.operator_library
            .expand_object(

                grid,

                source_color=

                parameters.get(
                    "source_color",
                    1
                )
            )
        )

    # ========================================
    # EXECUTE DUPLICATION
    # ========================================

    def execute_duplication(

        self,

        grid,

        parameters
    ):

        return (

            self.operator_library
            .duplicate_object(

                grid,

                source_color=

                parameters.get(
                    "source_color",
                    1
                ),

                offset_row=

                parameters.get(
                    "offset_row",
                    1
                ),

                offset_col=

                parameters.get(
                    "offset_col",
                    1
                )
            )
        )

    # ========================================
    # EXECUTE SPATIAL OPERATOR
    # ========================================

    def execute_spatial_operator(

        self,

        operator_name,

        grid,

        parameters={}
    ):

        try:

            # ====================================
            # TRANSLATION
            # ====================================

            if operator_name == (

                "translate_object"
            ):

                result = (

                    self.execute_translation(

                        grid,

                        parameters
                    )
                )

            # ====================================
            # MIRROR
            # ====================================

            elif operator_name == (

                "mirror_pattern"
            ):

                result = (

                    self.execute_mirror(

                        grid,

                        parameters
                    )
                )

            # ====================================
            # ROTATION
            # ====================================

            elif operator_name == (

                "rotate_pattern"
            ):

                result = (

                    self.execute_rotation(

                        grid,

                        parameters
                    )
                )

            # ====================================
            # EXPANSION
            # ====================================

            elif operator_name == (

                "expand_object"
            ):

                result = (

                    self.execute_expansion(

                        grid,

                        parameters
                    )
                )

            # ====================================
            # DUPLICATION
            # ====================================

            elif operator_name == (

                "duplicate_object"
            ):

                result = (

                    self.execute_duplication(

                        grid,

                        parameters
                    )
                )

            # ====================================
            # FALLBACK
            # ====================================

            else:

                result = deepcopy(grid)

            # ====================================
            # STORE HISTORY
            # ====================================

            self.execution_history.append({

                "operator":
                operator_name,

                "parameters":
                parameters,

                "success":
                True,

                "timestamp":
                str(datetime.utcnow())
            })

            return result

        except Exception:

            self.execution_history.append({

                "operator":
                operator_name,

                "parameters":
                parameters,

                "success":
                False,

                "timestamp":
                str(datetime.utcnow())
            })

            return deepcopy(grid)

    # ========================================
    # EXECUTE SPATIAL PROGRAM
    # ========================================

    def execute_spatial_program(

        self,

        grid,

        program_steps
    ):

        current_grid = np.array(
            deepcopy(grid)
        )

        execution_trace = []

        for step in program_steps:

            operator_name = step.get(
                "operator"
            )

            parameters = step.get(
                "parameters",
                {}
            )

            current_grid = (

                self.execute_spatial_operator(

                    operator_name,

                    current_grid,

                    parameters
                )
            )

            execution_trace.append({

                "operator":
                operator_name,

                "parameters":
                parameters,

                "execution_success":
                True
            })

        return {

            "final_grid":
            current_grid,

            "execution_trace":
            execution_trace,

            "step_count":
            len(execution_trace)
        }

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_execution = {}

        if self.execution_history:

            latest_execution = (

                self.execution_history[-1]
            )

        return {

            "execution_cycles":

            len(
                self.execution_history
            ),

            "engine_state":
            self.engine_state,

            "latest_execution":
            latest_execution
        }


# ============================================
# GLOBAL ENGINE
# ============================================

spatial_operator_engine = (
    SpatialOperatorEngine()
)