# ============================================
# NEXRYN WORLD MODEL ENGINE
# ============================================

import numpy as np

from runtime.transforms import (
    primitive_executor
)
from runtime.world.acceptance_calibrator import (
    WorldModelAcceptanceCalibrator,
)
from runtime.evaluation.partial_success_engine import (
    PartialSuccessEngine,
)


# ============================================
# WORLD MODEL ENGINE
# ============================================

class WorldModelEngine:

    def __init__(self, acceptance_calibrator=None):

        self.prediction_history = []

        self.last_ground_truth = None

        self.prediction_accuracy = 0.0

        self.success_state = False

        self.acceptance_calibrator = (
            acceptance_calibrator
            or WorldModelAcceptanceCalibrator()
        )
        self.partial_success_engine = PartialSuccessEngine()

    # ============================================
    # SIMULATE TRANSFORMATION
    # ============================================

    def simulate_transformation(

        self,

        input_grid,

        synthesized_program
    ):

        steps = synthesized_program.get(
            "steps",
            []
        )

        primitives = []

        simulation_trace = []

        for step in steps:

            operation = step.get(
                "operation"
            )

            parameters = step.get(
                "parameters",
                {}
            )

            primitives.append({

                "primitive":
                operation,

                "parameters":
                parameters
            })

        execution_result = (

            primitive_executor
            .run_execution(

                input_grid=
                input_grid,

                primitives=
                primitives
            )
        )

        predicted_grid = execution_result.get(
            "output_grid",
            np.copy(input_grid)
        )

        for event in execution_result.get(
            "execution_trace",
            []
        ):

            simulation_trace.append({

                "operation":
                event.get(
                    "primitive"
                ),

                "status":
                "simulated"
            })

        return {

            "predicted_grid":
            predicted_grid,

            "simulation_trace":
            simulation_trace,

            "step_count":
            len(simulation_trace)
        }

    # ============================================
    # ANTICIPATE PROGRAM
    # ============================================

    def anticipate_program(

        self,

        input_grid,

        target_grid,

        synthesized_program,

        minimum_accuracy=0.75
    ):

        simulation = self.simulate_transformation(

            input_grid,

            synthesized_program
        )

        predicted_grid = simulation.get(
            "predicted_grid"
        )

        prediction_report = self.evaluate_prediction(

            predicted_grid,

            target_grid
        )

        uncertainty_report = self.estimate_simulation_uncertainty(

            synthesized_program,

            simulation.get(
                "simulation_trace",
                []
            ),

            prediction_report
        )

        accuracy = prediction_report.get(
            "prediction_accuracy",
            0.0
        )

        acceptance = self.acceptance_calibrator.evaluate(
            prediction_report,
            uncertainty_report,
            minimum_search_accuracy=minimum_accuracy,
        )

        return {

            **acceptance,
            "minimum_accuracy":
            minimum_accuracy,

            "prediction_report":
            prediction_report,

            "uncertainty_report":
            uncertainty_report,

            "simulation":
            simulation
        }

    # ============================================
    # ESTIMATE SIMULATION UNCERTAINTY
    # ============================================

    def estimate_simulation_uncertainty(

        self,

        synthesized_program,

        simulation_trace,

        prediction_report
    ):

        steps = synthesized_program.get(
            "steps",
            []
        )

        step_count = len(
            steps
        )

        simulated_steps = len(
            simulation_trace
        )

        unexecuted_steps = max(
            step_count - simulated_steps,
            0
        )

        accuracy = prediction_report.get(
            "prediction_accuracy",
            0.0
        )

        unsupported_factor = (
            unexecuted_steps
            /
            max(
                step_count,
                1
            )
        )

        brevity_factor = 0.15 if step_count <= 1 else 0.0

        imperfection_factor = (
            1.0 - accuracy
        )

        uncertainty = (
            unsupported_factor * 0.45
            +
            imperfection_factor * 0.40
            +
            brevity_factor
        )

        ambiguity_score = min(
            unsupported_factor
            +
            brevity_factor,
            1.0
        )

        uncalibrated_prediction_confidence = max(
            1.0 - uncertainty,
            0.0
        )

        prediction_confidence = min(
            uncalibrated_prediction_confidence,
            accuracy
        )

        return {

            "prediction_confidence":
            round(
                prediction_confidence,
                4
            ),

            "uncalibrated_prediction_confidence":
            round(
                uncalibrated_prediction_confidence,
                4
            ),

            "confidence_calibration_gap":
            round(
                uncalibrated_prediction_confidence
                -
                prediction_confidence,
                4
            ),

            "simulation_uncertainty":
            round(
                uncertainty,
                4
            ),

            "ambiguity_score":
            round(
                ambiguity_score,
                4
            ),

            "unsupported_step_count":
            unexecuted_steps
        }

    # ============================================
    # EVALUATE SIMULATION
    # ============================================

    def evaluate_prediction(

        self,

        predicted_grid,

        target_grid
    ):

        total_cells = predicted_grid.size

        correct_cells = np.sum(

            predicted_grid == target_grid
        )

        accuracy = (

            correct_cells

            /

            total_cells
        )

        success = bool(accuracy == 1.0)
        prediction_report = {

            "prediction_accuracy":
            round(
                float(accuracy),
                4
            ),

            "correct_cells":
            int(correct_cells),

            "total_cells":
            int(total_cells),

            "success":
            success,

            **self.partial_success_engine.evaluate(
                accuracy,
                exact_success=success,
            )
        }

        self.prediction_history.append(
            prediction_report
        )

        return prediction_report

    # ============================================
    # GET HISTORY
    # ============================================

    def get_history(self):

        return self.prediction_history

    # ============================================
    # SYNCHRONIZE WITH EVALUATOR
    # ============================================

    def synchronize_with_evaluator(

        self,

        evaluation_result
    ):

        if not isinstance(
            evaluation_result,
            dict
        ):

            evaluation_result = {}

        self.last_ground_truth = dict(
            evaluation_result
        )

        self.prediction_accuracy = (
            evaluation_result.get(
                "accuracy",
                0.0
            )
        )

        self.success_state = (
            evaluation_result.get(
                "success_state",
                evaluation_result.get(
                    "success",
                    False
                )
            )
        )

        sync_event = {

            "synchronized":
            True,

            "prediction_accuracy":
            self.prediction_accuracy,

            "success_state":
            self.success_state
        }

        self.prediction_history.append(
            sync_event
        )

        return sync_event

    # ============================================
    # PRINT REPORT
    # ============================================

    def print_prediction_report(

        self,

        prediction_report
    ):

        print("\n==================================================")
        print("NEXRYN :: WORLD MODEL")
        print("==================================================\n")

        print(
            prediction_report
        )


# ============================================
# GLOBAL WORLD MODEL ENGINE
# ============================================

world_model_engine = (
    WorldModelEngine()
)
