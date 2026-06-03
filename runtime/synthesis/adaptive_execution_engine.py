# ============================================
# NEXRYN ADAPTIVE EXECUTION ENGINE
# ============================================

from datetime import datetime

from copy import deepcopy

from runtime.synthesis.spatial_operator_engine import (

    spatial_operator_engine
)

from runtime.synthesis.operator_selection_engine import (

    operator_selection_engine
)

from runtime.synthesis.transformation_validation_engine import (

    transformation_validation_engine
)


# ============================================
# ADAPTIVE EXECUTION ENGINE
# ============================================

class AdaptiveExecutionEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.execution_history = []

        self.recovery_history = []

        self.spatial_engine = (
            spatial_operator_engine
        )

        self.selection_engine = (
            operator_selection_engine
        )

        self.validation_engine = (
            transformation_validation_engine
        )

        self.engine_state = {

            "adaptive_execution":
            True,

            "failure_recovery":
            True,

            "dynamic_mutation":
            True,

            "execution_retry":
            True,

            "runtime_stabilization":
            True
        }

    # ========================================
    # EXECUTE STEP
    # ========================================

    def execute_step(

        self,

        grid,

        program_step
    ):

        operator_name = program_step.get(
            "operator"
        )

        parameters = program_step.get(
            "parameters",
            {}
        )

        result_grid = (

            self.spatial_engine
            .execute_spatial_operator(

                operator_name,

                grid,

                parameters
            )
        )

        return result_grid

    # ========================================
    # RETRY FAILED EXECUTION
    # ========================================

    def retry_execution(

        self,

        grid,

        program_step
    ):

        mutated_step = deepcopy(
            program_step
        )

        parameters = mutated_step.get(
            "parameters",
            {}
        )

        # ====================================
        # MUTATE PARAMETERS
        # ====================================

        if "delta_row" in parameters:

            parameters[
                "delta_row"
            ] = 0

        if "delta_col" in parameters:

            parameters[
                "delta_col"
            ] = 0

        mutated_step[
            "parameters"
        ] = parameters

        retry_result = (

            self.execute_step(

                grid,

                mutated_step
            )
        )

        self.recovery_history.append({

            "recovery_strategy":
            "parameter_mutation",

            "mutated_step":
            mutated_step,

            "timestamp":
            str(datetime.utcnow())
        })

        return retry_result

    # ========================================
    # EXECUTE PROGRAM ADAPTIVELY
    # ========================================

    def execute_program_adaptively(

        self,

        input_grid,

        execution_program
    ):

        current_grid = deepcopy(
            input_grid
        )

        execution_trace = []

        program_steps = execution_program.get(

            "program_steps",

            []
        )

        # ====================================
        # OPERATOR SELECTION
        # ====================================

        selection_report = (

            self.selection_engine
            .build_selection_report(

                program_steps
            )
        )

        ranked_steps = selection_report.get(

            "ranked_steps",

            []
        )

        # ====================================
        # EXECUTE STEPS
        # ====================================

        for ranked_step in ranked_steps:

            program_step = ranked_step.get(
                "program_step",
                {}
            )

            operator_name = program_step.get(
                "operator",
                "unknown"
            )

            try:

                # ================================
                # EXECUTION
                # ================================

                result_grid = (

                    self.execute_step(

                        current_grid,

                        program_step
                    )
                )

                # ================================
                # VALIDATION
                # ================================

                validation_report = (

                    self.validation_engine
                    .validate_transformation(

                        current_grid,

                        result_grid
                    )
                )

                validation_success = (

                    validation_report.get(
                        "validation_success",
                        False
                    )
                )

                # ================================
                # FAILURE RECOVERY
                # ================================

                if not validation_success:

                    result_grid = (

                        self.retry_execution(

                            current_grid,

                            program_step
                        )
                    )

                # ================================
                # UPDATE GRID
                # ================================

                current_grid = result_grid

                # ================================
                # UPDATE OPERATOR PERFORMANCE
                # ================================

                self.selection_engine.update_operator_performance(

                    operator_name,

                    success=True
                )

                execution_trace.append({

                    "operator":
                    operator_name,

                    "execution_success":
                    True,

                    "validation_success":
                    validation_success,

                    "parameters":

                    program_step.get(
                        "parameters",
                        {}
                    )
                })

            except Exception:

                self.selection_engine.update_operator_performance(

                    operator_name,

                    success=False
                )

                execution_trace.append({

                    "operator":
                    operator_name,

                    "execution_success":
                    False,

                    "validation_success":
                    False
                })

        # ====================================
        # BUILD REPORT
        # ====================================

        execution_report = {

            "final_grid":
            current_grid,

            "execution_trace":
            execution_trace,

            "step_count":
            len(execution_trace),

            "successful_steps":

            len([

                step

                for step in execution_trace

                if step.get(
                    "execution_success"
                )
            ]),

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.execution_history.append(
            deepcopy(execution_report)
        )

        return execution_report

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

            "recovery_cycles":

            len(
                self.recovery_history
            ),

            "engine_state":
            self.engine_state,

            "latest_execution":
            latest_execution
        }


# ============================================
# GLOBAL ENGINE
# ============================================

adaptive_execution_engine = (
    AdaptiveExecutionEngine()
)