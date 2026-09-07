# ============================================
# NEXRYN WORLD MODEL ENGINE
# ============================================

import hashlib
import json
import os
import time
from pathlib import Path

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

        self._telemetry_call_counter = 0

    # ============================================
    # OBSERVATION-ONLY TELEMETRY
    # ============================================

    def _telemetry_path(self):

        path = os.environ.get(
            "NEXRYN_WORLD_MODEL_TELEMETRY_PATH"
        )

        if not path:

            return None

        return Path(
            path
        )

    def _grid_shape(self, grid):

        if grid is None:

            return None

        if hasattr(
            grid,
            "grid"
        ):

            grid = grid.grid

        try:

            array = np.array(
                grid
            )

            if array.ndim != 2:

                return None

            return [
                int(array.shape[0]),
                int(array.shape[1])
            ]

        except Exception:

            return None

    def _stable_telemetry_id(self, value):

        text = json.dumps(
            self._telemetry_safe_value(value),
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()[:16]

    def _telemetry_safe_value(self, value):

        if isinstance(
            value,
            np.ndarray
        ):

            return {
                "ndarray_shape": [
                    int(item)
                    for item in value.shape
                ]
            }

        if isinstance(
            value,
            (np.integer,)
        ):

            return int(value)

        if isinstance(
            value,
            (np.floating,)
        ):

            return float(value)

        if isinstance(
            value,
            dict
        ):

            return {
                str(key):
                self._telemetry_safe_value(item)
                for key, item in value.items()
                if key not in {
                    "input_grid",
                    "output_grid",
                    "target_grid",
                    "predicted_output",
                    "predicted_grid",
                    "hidden_test_outputs",
                }
            }

        if isinstance(
            value,
            (list, tuple)
        ):

            return [
                self._telemetry_safe_value(item)
                for item in list(value)[:20]
            ]

        if isinstance(
            value,
            (str, int, float, bool)
        ) or value is None:

            return value

        return type(value).__name__

    def _emit_world_model_telemetry(
        self,
        *,
        event_type,
        phase,
        subcall_name,
        call_id,
        parent_call_id=None,
        started_at=None,
        parent_started_at=None,
        **fields
    ):

        path = self._telemetry_path()

        if path is None:

            return

        now = time.perf_counter()

        event = {
            "system":
            "world_model_inner_progress_telemetry",
            "authority":
            "OBSERVATION_ONLY",
            "behavioral_authority":
            "NONE",
            "event_type":
            event_type,
            "phase":
            phase,
            "task_id":
            os.environ.get(
                "NEXRYN_WORLD_MODEL_TELEMETRY_TASK_ID"
            ),
            "call_id":
            call_id,
            "parent_call_id":
            parent_call_id,
            "subcall_name":
            subcall_name,
            "monotonic_timestamp":
            round(
                now,
                6
            ),
            "elapsed_total_ms":
            round(
                (now - started_at) * 1000,
                3
            )
            if started_at is not None
            else 0.0,
            "elapsed_parent_ms":
            round(
                (now - parent_started_at) * 1000,
                3
            )
            if parent_started_at is not None
            else 0.0,
        }

        event.update({
            key:
            self._telemetry_safe_value(value)
            for key, value in fields.items()
        })

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "a",
            encoding="utf-8"
        ) as handle:

            handle.write(
                json.dumps(
                    event,
                    sort_keys=True,
                    ensure_ascii=True,
                )
                +
                "\n"
            )

            handle.flush()

            os.fsync(
                handle.fileno()
            )

    def _next_world_model_call_id(self):

        self._telemetry_call_counter += 1

        return "world_model_call_{}".format(
            self._telemetry_call_counter
        )

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

        minimum_accuracy=0.75,

        runtime_context=None,
    ):

        telemetry_started_at = time.perf_counter()
        telemetry_call_id = self._next_world_model_call_id()
        program_fingerprint = self._stable_telemetry_id(
            synthesized_program
        )

        self._emit_world_model_telemetry(
            event_type="world_model_inner_progress",
            phase="ENTER",
            subcall_name="anticipate_program",
            call_id=telemetry_call_id,
            started_at=telemetry_started_at,
            parent_started_at=telemetry_started_at,
            world_model_call_index=self._telemetry_call_counter,
            program_fingerprint=program_fingerprint,
            program_count=1,
            input_shape=self._grid_shape(input_grid),
            target_shape=self._grid_shape(target_grid),
        )

        localization_started_at = time.perf_counter()
        self._emit_world_model_telemetry(
            event_type="world_model_inner_progress",
            phase="ENTER",
            subcall_name="object_localization",
            call_id=telemetry_call_id + ":localization",
            parent_call_id=telemetry_call_id,
            started_at=telemetry_started_at,
            parent_started_at=telemetry_started_at,
            localization_index=1,
            declared_bound=1,
        )

        localization_report = (
            self.transformation_localization_engine
            .localize_program(
                input_grid,
                target_grid,
                synthesized_program,
                runtime_context=runtime_context,
            )
        )

        self._emit_world_model_telemetry(
            event_type="world_model_inner_progress",
            phase="EXIT",
            subcall_name="object_localization",
            call_id=telemetry_call_id + ":localization",
            parent_call_id=telemetry_call_id,
            started_at=telemetry_started_at,
            parent_started_at=localization_started_at,
            exit_reason="completed",
            localized_step_count=localization_report.get(
                "localized_step_count"
            ),
        )

        motion_started_at = time.perf_counter()
        self._emit_world_model_telemetry(
            event_type="world_model_inner_progress",
            phase="ENTER",
            subcall_name="object_motion",
            call_id=telemetry_call_id + ":motion",
            parent_call_id=telemetry_call_id,
            started_at=telemetry_started_at,
            parent_started_at=telemetry_started_at,
            motion_index=1,
            declared_bound=1,
        )

        object_motion_report = self.object_motion_engine.analyze(
            input_grid,
            target_grid,
        )

        self._emit_world_model_telemetry(
            event_type="world_model_inner_progress",
            phase="EXIT",
            subcall_name="object_motion",
            call_id=telemetry_call_id + ":motion",
            parent_call_id=telemetry_call_id,
            started_at=telemetry_started_at,
            parent_started_at=motion_started_at,
            exit_reason="completed",
            motion_pattern=object_motion_report.get(
                "motion_pattern"
            ),
            object_count=len(
                object_motion_report.get(
                    "movable_objects",
                    []
                )
                or []
            )
            +
            len(
                object_motion_report.get(
                    "fixed_objects",
                    []
                )
                or []
            ),
        )

        localized_program = localization_report.get(
            "localized_program",
            synthesized_program,
        )

        simulation_started_at = time.perf_counter()
        self._emit_world_model_telemetry(
            event_type="world_model_inner_progress",
            phase="ENTER",
            subcall_name="simulation",
            call_id=telemetry_call_id + ":simulation:1",
            parent_call_id=telemetry_call_id,
            started_at=telemetry_started_at,
            parent_started_at=telemetry_started_at,
            simulation_index=1,
            declared_bound=1,
            program_fingerprint=self._stable_telemetry_id(
                localized_program
            ),
        )

        simulation = self.simulate_transformation(

            input_grid,

            localized_program
        )

        self._emit_world_model_telemetry(
            event_type="world_model_inner_progress",
            phase="EXIT",
            subcall_name="simulation",
            call_id=telemetry_call_id + ":simulation:1",
            parent_call_id=telemetry_call_id,
            started_at=telemetry_started_at,
            parent_started_at=simulation_started_at,
            exit_reason="completed",
            simulation_index=1,
            step_count=simulation.get(
                "step_count"
            ),
            predicted_shape=self._grid_shape(
                simulation.get(
                    "predicted_grid"
                )
            ),
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

            motion_eval_started_at = time.perf_counter()
            self._emit_world_model_telemetry(
                event_type="world_model_inner_progress",
                phase="ENTER",
                subcall_name="prediction_evaluation",
                call_id=telemetry_call_id + ":motion_prediction_evaluation",
                parent_call_id=telemetry_call_id,
                started_at=telemetry_started_at,
                parent_started_at=telemetry_started_at,
                evaluation_index=1,
                prediction_kind="motion",
                predicted_shape=self._grid_shape(
                    motion_prediction
                ),
                target_shape=self._grid_shape(
                    target_grid
                ),
            )

            motion_prediction_report = self.evaluate_prediction(

                motion_prediction,

                target_grid
            )

            self._emit_world_model_telemetry(
                event_type="world_model_inner_progress",
                phase="EXIT",
                subcall_name="prediction_evaluation",
                call_id=telemetry_call_id + ":motion_prediction_evaluation",
                parent_call_id=telemetry_call_id,
                started_at=telemetry_started_at,
                parent_started_at=motion_eval_started_at,
                evaluation_index=1,
                prediction_kind="motion",
                prediction_accuracy=motion_prediction_report.get(
                    "prediction_accuracy"
                ),
                exit_reason="completed",
            )

            current_eval_started_at = time.perf_counter()
            self._emit_world_model_telemetry(
                event_type="world_model_inner_progress",
                phase="ENTER",
                subcall_name="prediction_evaluation",
                call_id=telemetry_call_id + ":current_prediction_evaluation",
                parent_call_id=telemetry_call_id,
                started_at=telemetry_started_at,
                parent_started_at=telemetry_started_at,
                evaluation_index=2,
                prediction_kind="current",
                predicted_shape=self._grid_shape(
                    predicted_grid
                ),
                target_shape=self._grid_shape(
                    target_grid
                ),
            )

            current_accuracy = self.evaluate_prediction(

                predicted_grid,

                target_grid
            ).get(
                "prediction_accuracy",
                0.0
            )

            self._emit_world_model_telemetry(
                event_type="world_model_inner_progress",
                phase="EXIT",
                subcall_name="prediction_evaluation",
                call_id=telemetry_call_id + ":current_prediction_evaluation",
                parent_call_id=telemetry_call_id,
                started_at=telemetry_started_at,
                parent_started_at=current_eval_started_at,
                evaluation_index=2,
                prediction_kind="current",
                prediction_accuracy=current_accuracy,
                exit_reason="completed",
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

        final_eval_started_at = time.perf_counter()
        self._emit_world_model_telemetry(
            event_type="world_model_inner_progress",
            phase="ENTER",
            subcall_name="prediction_evaluation",
            call_id=telemetry_call_id + ":final_prediction_evaluation",
            parent_call_id=telemetry_call_id,
            started_at=telemetry_started_at,
            parent_started_at=telemetry_started_at,
            evaluation_index=3,
            prediction_kind="final",
            predicted_shape=self._grid_shape(
                predicted_grid
            ),
            target_shape=self._grid_shape(
                target_grid
            ),
        )

        prediction_report = self.evaluate_prediction(

            predicted_grid,

            target_grid
        )

        self._emit_world_model_telemetry(
            event_type="world_model_inner_progress",
            phase="EXIT",
            subcall_name="prediction_evaluation",
            call_id=telemetry_call_id + ":final_prediction_evaluation",
            parent_call_id=telemetry_call_id,
            started_at=telemetry_started_at,
            parent_started_at=final_eval_started_at,
            evaluation_index=3,
            prediction_kind="final",
            prediction_accuracy=prediction_report.get(
                "prediction_accuracy"
            ),
            exit_reason="completed",
        )

        scoring_started_at = time.perf_counter()
        self._emit_world_model_telemetry(
            event_type="world_model_inner_progress",
            phase="ENTER",
            subcall_name="confidence_scoring",
            call_id=telemetry_call_id + ":confidence_scoring",
            parent_call_id=telemetry_call_id,
            started_at=telemetry_started_at,
            parent_started_at=telemetry_started_at,
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

        self._emit_world_model_telemetry(
            event_type="world_model_inner_progress",
            phase="EXIT",
            subcall_name="confidence_scoring",
            call_id=telemetry_call_id + ":confidence_scoring",
            parent_call_id=telemetry_call_id,
            started_at=telemetry_started_at,
            parent_started_at=scoring_started_at,
            prediction_accuracy=accuracy,
            acceptance_state=acceptance.get(
                "acceptance_state"
            ),
            exit_reason="completed",
        )

        aggregation_started_at = time.perf_counter()
        self._emit_world_model_telemetry(
            event_type="world_model_inner_progress",
            phase="ENTER",
            subcall_name="candidate_aggregation",
            call_id=telemetry_call_id + ":candidate_aggregation",
            parent_call_id=telemetry_call_id,
            started_at=telemetry_started_at,
            parent_started_at=telemetry_started_at,
        )

        localization_report = localization_controller.calibrate(
            localization_report,
            synthesized_program=localized_program,
            prediction_accuracy=prediction_report.get(
                "prediction_accuracy",
                0.0,
            ),
            runtime_context={
                "input_grid": input_grid,
                "output_grid": target_grid,
                "target_grid": target_grid,
                "predicted_output": predicted_grid,
                "prediction_report": prediction_report,
                "object_motion_report": object_motion_report,
                "OBJECT_MOTION_REPORT": object_motion_report,
            },
        )
        localized_program = localization_report.get(
            "localized_program",
            localized_program,
        )

        if object_level_motion_selected:

            localization_report["localized_program"] = localized_program
            localization_report["localized_step_count"] = 1

        motion_targets = (
            object_motion_report.get("movable_objects")
            or object_motion_report.get("fixed_objects")
            or localization_report.get("target_objects", [])
        )
        localization_report.update({
            "target_objects":
            motion_targets,
            "translation_per_object":
            object_motion_report.get("translation_per_object", {}),
            "support_objects":
            object_motion_report.get("support_objects", []),
            "motion_constraints":
            object_motion_report.get("motion_constraints", {}),
            "motion_pattern":
            object_motion_report.get("motion_pattern"),
        })

        result = {

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

        self._emit_world_model_telemetry(
            event_type="world_model_inner_progress",
            phase="EXIT",
            subcall_name="candidate_aggregation",
            call_id=telemetry_call_id + ":candidate_aggregation",
            parent_call_id=telemetry_call_id,
            started_at=telemetry_started_at,
            parent_started_at=aggregation_started_at,
            exit_reason="completed",
        )

        self._emit_world_model_telemetry(
            event_type="world_model_inner_progress",
            phase="EXIT",
            subcall_name="anticipate_program",
            call_id=telemetry_call_id,
            started_at=telemetry_started_at,
            parent_started_at=telemetry_started_at,
            exit_reason="completed",
            acceptance_state=result.get(
                "acceptance_state"
            ),
        )

        return result

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

        predicted_shape = list(predicted_grid.shape)
        target_shape = list(target_grid.shape)

        if predicted_shape != target_shape:

            total_cells = target_grid.size

            accuracy = 0.0

            success = False

            prediction_report = {

                "prediction_accuracy":
                accuracy,

                "correct_cells":
                0,

                "total_cells":
                int(total_cells),

                "success":
                success,

                "comparable":
                False,

                "failure_reason":
                "SHAPE_MISMATCH",

                "predicted_shape":
                predicted_shape,

                "target_shape":
                target_shape,

                **self.partial_success_engine.evaluate(
                    accuracy,
                    exact_success=success,
                )
            }

            self.prediction_history.append(
                prediction_report
            )

            return prediction_report

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
