# ============================================
# NEXRYN PROGRAM SYNTHESIS ENGINE
# ============================================

from datetime import datetime

from copy import deepcopy

from runtime.synthesis.transformation_operator_library import (

    transformation_operator_library
)


# ============================================
# PROGRAM SYNTHESIS ENGINE
# ============================================

class ProgramSynthesisEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.program_history = []

        self.generated_programs = []

        self.operator_library = (
            transformation_operator_library
        )

        self.engine_state = {

            "program_generation":
            True,

            "operator_selection":
            True,

            "parameter_synthesis":
            True,

            "execution_planning":
            True,

            "adaptive_program_building":
            True
        }

    # ========================================
    # MAP HYPOTHESIS TO OPERATOR
    # ========================================

    def map_hypothesis_to_operator(

        self,

        hypothesis
    ):

        hypothesis_type = hypothesis.get(
            "type",
            ""
        )

        # ====================================
        # COLOR TRANSFORMATION
        # ====================================

        if "color" in hypothesis_type:

            return "replace_color"

        # ====================================
        # TRANSLATION
        # ====================================

        if "translation" in hypothesis_type:

            return "translate_object"

        # ====================================
        # REFLECTION
        # ====================================

        if "reflection" in hypothesis_type:

            return "mirror_pattern"

        # ====================================
        # ROTATION
        # ====================================

        if "rotation" in hypothesis_type:

            return "rotate_pattern"

        return None

    # ========================================
    # SYNTHESIZE PARAMETERS
    # ========================================

    def synthesize_parameters(

        self,

        hypothesis
    ):

        metadata = hypothesis.get(
            "metadata",
            {}
        )

        parameters = {}

        # ====================================
        # COLOR REPLACEMENT
        # ====================================

        if hypothesis.get(
            "type"
        ) == "color_transformation":

            parameters = {

                "source_color":

                metadata.get(
                    "source_color",
                    1
                ),

                "target_color":

                metadata.get(
                    "target_color",
                    2
                )
            }

        # ====================================
        # TRANSLATION
        # ====================================

        elif hypothesis.get(
            "type"
        ) == "object_translation":

            parameters = {

                "source_color":

                metadata.get(
                    "color",
                    1
                ),

                "delta_row":

                int(
                    metadata.get(
                        "delta_row",
                        0
                    )
                ),

                "delta_col":

                int(
                    metadata.get(
                        "delta_col",
                        0
                    )
                )
            }

        # ====================================
        # REFLECTION
        # ====================================

        elif "reflection" in str(

            hypothesis.get(
                "type"
            )
        ):

            parameters = {

                "axis":

                "horizontal"
                if "horizontal" in str(
                    hypothesis.get(
                        "type"
                    )
                )
                else "vertical"
            }

        # ====================================
        # ROTATION
        # ====================================

        elif hypothesis.get(
            "type"
        ) == "rotation":

            parameters = {

                "degrees":

                metadata.get(
                    "rotation",
                    90
                )
            }

        return parameters

    # ========================================
    # BUILD PROGRAM STEP
    # ========================================

    def build_program_step(

        self,

        hypothesis
    ):

        operator_name = (

            self.map_hypothesis_to_operator(
                hypothesis
            )
        )

        if operator_name is None:

            return {}

        parameters = (

            self.synthesize_parameters(
                hypothesis
            )
        )

        program_step = {

            "operator":
            operator_name,

            "parameters":
            parameters,

            "confidence":

            hypothesis.get(
                "confidence",
                0.0
            ),

            "source_hypothesis":
            hypothesis
        }

        return program_step

    # ========================================
    # BUILD EXECUTION PROGRAM
    # ========================================

    def build_execution_program(

        self,

        hypotheses
    ):

        program_steps = []

        for hypothesis in hypotheses:

            program_step = (

                self.build_program_step(
                    hypothesis
                )
            )

            if program_step:

                program_steps.append(
                    program_step
                )

        execution_program = {

            "program_step_count":
            len(program_steps),

            "program_steps":
            program_steps,

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.program_history.append(
            deepcopy(execution_program)
        )

        self.generated_programs.append(
            program_steps
        )

        return execution_program

    # ========================================
    # EXECUTE PROGRAM
    # ========================================

    def execute_program(

        self,

        grid,

        execution_program
    ):

        current_grid = deepcopy(grid)

        program_steps = execution_program.get(

            "program_steps",

            []
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

            previous_grid = deepcopy(
                current_grid
            )

            current_grid = (

                self.operator_library
                .apply_operator(

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

        latest_program = {}

        if self.program_history:

            latest_program = (

                self.program_history[-1]
            )

        return {

            "generated_programs":

            len(
                self.generated_programs
            ),

            "program_cycles":

            len(
                self.program_history
            ),

            "available_operators":

            self.operator_library
            .available_operators,

            "engine_state":
            self.engine_state,

            "latest_program":
            latest_program
        }


# ============================================
# GLOBAL ENGINE
# ============================================

program_synthesis_engine = (
    ProgramSynthesisEngine()
)