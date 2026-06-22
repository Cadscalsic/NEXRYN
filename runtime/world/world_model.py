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
from runtime.spatial import (
    transformation_localization_engine,
)
from runtime.transformation_localization import (
    localization_controller,
)
from runtime.object_motion import (
    object_motion_engine,
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
        self.transformation_localization_engine = (
            transformation_localization_engine
        )
        self.object_motion_engine = object_motion_engine

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

        localization_report = (
            self.transformation_localization_engine
            .localize_program(
                input_grid,
                target_grid,
                synthesized_program,
            )
        )

        object_motion_report = self.object_motion_engine.analyze(
            input_grid,
            target_grid,
        )

        localized_program = localization_report.get(
            "localized_program",
            synthesized_program,
        )

        simulation = self.simulate_transformation(

            input_grid,

            localized_program
        )

        predicted_grid = simulation.get(
            "predicted_grid"
        )

        motion_prediction = object_motion_report.get(
            "predicted_grid"
        )

        motion_prediction_report = None
        object_level_motion_selected = False

        if motion_prediction is not None:

            motion_prediction_report = self.evaluate_prediction(

                motion_prediction,

                target_grid
            )

            current_accuracy = self.evaluate_prediction(

                predicted_grid,

                target_grid
            ).get(
                "prediction_accuracy",
                0.0
            )

            motion_accuracy = motion_prediction_report.get(
                "prediction_accuracy",
                0.0
            )

            if (
                object_motion_report.get("motion_pattern")
                in {
                    "independent_translation",
                    "gravity_motion",
                    "constraint_driven_motion",
                }
                and motion_accuracy >= current_accuracy
            ):

                predicted_grid = motion_prediction

                simulation = {

                    **simulation,

                    "predicted_grid":
                    predicted_grid,

                    "simulation_trace":
                    simulation.get(
                        "simulation_trace",
                        []
                    )
                    +
                    [{
                        "operation":
                        "object_level_translate",

                        "status":
                        "simulated",

                        "motion_pattern":
                        object_motion_report.get(
                            "motion_pattern"
                        ),
                    }],

                    "object_level_simulation":
                    True,
                }

                localized_program = {
                    "step_count": 1,
                    "steps": [{
                        "operation": "object_level_translate",
                        "parameters": {
                            "translation_per_object":
                            object_motion_report.get(
                                "translation_per_object",
                                {},
                            ),
                            "movable_objects":
                            object_motion_report.get(
                                "movable_objects",
                                [],
                            ),
                            "fixed_objects":
                            object_motion_report.get(
                                "fixed_objects",
                                [],
                            ),
                            "motion_pattern":
                            object_motion_report.get(
                                "motion_pattern"
                            ),
                        },
                    }],
                }
                object_level_motion_selected = True
                localization_report["localized_program"] = localized_program
                localization_report["localized_step_count"] = 1

        prediction_report = self.evaluate_prediction(

            predicted_grid,

            target_grid
        )

        uncertainty_report = self.estimate_simulation_uncertainty(

            localized_program,

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

        localization_report = localization_controller.calibrate(
            localization_report,
            synthesized_program=localized_program,
            prediction_accuracy=prediction_report.get(
                "prediction_accuracy",
                0.0,
            ),
        )
        localized_program = localization_report.get(
            "localized_program",
            localized_program,
        )

        if object_level_motion_selected:

            localization_report["localized_program"] = localized_program
            localization_report["localized_step_count"] = 1

        localization_report.update({
            "target_objects":
            object_motion_report.get("movable_objects", []),
            "translation_per_object":
            object_motion_report.get("translation_per_object", {}),
            "support_objects":
            object_motion_report.get("support_objects", []),
            "motion_constraints":
            object_motion_report.get("motion_constraints", {}),
            "motion_pattern":
            object_motion_report.get("motion_pattern"),
        })

        return {

            **acceptance,
            "minimum_accuracy":
            minimum_accuracy,

            "prediction_report":
            prediction_report,

            "uncertainty_report":
            uncertainty_report,

            "simulation":
            simulation,

            "transformation_localization":
            localization_report,

            "localized_synthesized_program":
            localized_program,

            "object_motion_report":
            object_motion_report,

            "OBJECT_MOTION_REPORT":
            object_motion_report,

            "motion_prediction_report":
            motion_prediction_report,
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
