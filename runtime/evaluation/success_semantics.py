# ============================================
# NEXRYN SUCCESS SEMANTICS
# ============================================

from datetime import datetime

import numpy as np


TERMINAL_SUCCESS_STATES = {
    "EXACT_SUCCESS",
    "SUCCESS_WITH_RESIDUALS",
    "LEARNING_PROGRESS",
}

RETRY_SUCCESS_STATES = {
    "RECOVERABLE_FAILURE",
    "CRITICAL_FAILURE",
}


class SuccessSemanticsEngine:

    def classify(self, evaluation_result=None, runtime_context=None):

        evaluation = (
            dict(evaluation_result)
            if isinstance(evaluation_result, dict)
            else {}
        )
        context = runtime_context if isinstance(runtime_context, dict) else {}

        gate_report = self._first_mapping(
            context,
            [
                "world_model_gate_report",
                "world_model_report",
            ],
        )
        if not gate_report:
            transformation_report = self._mapping(
                context.get("transformation_report")
            )
            gate_report = self._mapping(
                transformation_report.get("world_model_gate")
            )

        integrity_report = self._first_mapping(
            context,
            [
                "execution_integrity_report",
            ],
        )
        if not integrity_report:
            transformation_report = self._mapping(
                context.get("transformation_report")
            )
            integrity_report = self._mapping(
                transformation_report.get("execution_integrity")
            )

        localization_report = self._mapping(
            context.get("transformation_localization")
        )
        prediction_report = self._mapping(
            context.get("prediction_report")
        )

        prediction_accuracy = self._number(
            evaluation.get(
                "accuracy",
                prediction_report.get(
                    "prediction_accuracy",
                    context.get("prediction_accuracy", 0.0),
                ),
            )
        )
        residual_difference_count = self._integer(
            context.get(
                "residual_difference_count",
                evaluation.get(
                    "difference_count",
                    prediction_report.get("residual_difference_count"),
                ),
            )
        )
        if residual_difference_count is None:
            residual_difference_count = self._integer(
                self._mapping(
                    context.get("world_model_anticipation")
                ).get("residual_difference_count")
            )
        if residual_difference_count is None:
            residual_difference_count = 0

        execution_authorized = (
            gate_report.get("execution_authorized") is True
            or context.get("execution_authorized") is True
        )
        integrity_preserved = (
            integrity_report.get("integrity_preserved") is True
            or context.get("execution_integrity_preserved") is True
        )
        contradiction_detected = (
            context.get("contradiction_detected") is True
            or bool(context.get("unresolved_contradictions"))
            or bool(context.get("semantic_contradictions"))
        )
        identity_unstable = self._identity_unstable(context)

        exact_success = (
            evaluation.get("exact_success") is True
            or (
                evaluation.get("success") is True
                and residual_difference_count == 0
                and prediction_accuracy >= 1.0
            )
        )

        success_state = "RECOVERABLE_FAILURE"
        termination_reason = None
        episode_completed = False
        failure_detected = True
        partial_success_detected = evaluation.get("partial_success") is True
        retry_allowed = True

        if contradiction_detected or identity_unstable:
            success_state = "CRITICAL_FAILURE"
            termination_reason = "GOVERNANCE_OR_IDENTITY_VIOLATION"
        elif exact_success:
            success_state = "EXACT_SUCCESS"
            termination_reason = "EXACT_SUCCESS"
            episode_completed = True
            failure_detected = False
            partial_success_detected = False
            retry_allowed = False
        elif (
            execution_authorized
            and integrity_preserved
            and prediction_accuracy >= 0.97
            and residual_difference_count <= 1
        ):
            success_state = "SUCCESS_WITH_RESIDUALS"
            termination_reason = "HIGH_CONFIDENCE_RESIDUAL_ACCEPTANCE"
            episode_completed = True
            failure_detected = False
            partial_success_detected = False
            retry_allowed = False
        elif (
            localization_report.get("localization_ready") is True
            and localization_report.get("localization_confidence", 0.0) >= 0.90
            and prediction_accuracy >= 0.80
        ):
            success_state = "HIGH_VALUE_PARTIAL_SUCCESS"
            termination_reason = "LOCALIZED_TRANSFORMATION_PROGRESS"
            failure_detected = False
            retry_allowed = False
        elif self._learning_progress(context, localization_report):
            success_state = "LEARNING_PROGRESS"
            termination_reason = "NEW_KNOWLEDGE_SIGNAL_RECORDED"
            episode_completed = True
            failure_detected = False
            partial_success_detected = False
            retry_allowed = False

        shutdown_mode = (
            "fast"
            if success_state in TERMINAL_SUCCESS_STATES
            else "normal"
        )

        residual_analysis = self.build_residual_analysis(
            context,
            residual_difference_count,
            success_state,
        )

        return {
            "system": "success_semantics_engine",
            "success_state": success_state,
            "exact_success": exact_success,
            "execution_success": bool(
                execution_authorized and integrity_preserved
            ),
            "reasoning_success": success_state in {
                "EXACT_SUCCESS",
                "SUCCESS_WITH_RESIDUALS",
                "HIGH_VALUE_PARTIAL_SUCCESS",
                "LEARNING_PROGRESS",
            },
            "learning_success": success_state in {
                "SUCCESS_WITH_RESIDUALS",
                "HIGH_VALUE_PARTIAL_SUCCESS",
                "LEARNING_PROGRESS",
            },
            "failure_detected": failure_detected,
            "partial_success_detected": partial_success_detected,
            "episode_completed": episode_completed,
            "retry_allowed": retry_allowed,
            "shutdown_mode": shutdown_mode,
            "termination_reason": termination_reason,
            "prediction_accuracy": round(prediction_accuracy, 4),
            "residual_difference_count": residual_difference_count,
            "execution_authorized": execution_authorized,
            "integrity_preserved": integrity_preserved,
            "residual_analysis": residual_analysis,
            "background_task_control": self.background_task_control(
                episode_completed
            ),
            "timestamp": str(datetime.utcnow()),
        }

    def apply(self, evaluation_result=None, runtime_context=None):

        evaluation = (
            dict(evaluation_result)
            if isinstance(evaluation_result, dict)
            else {}
        )
        report = self.classify(evaluation, runtime_context)
        success_state = report["success_state"]

        evaluation.update({
            "success_state": success_state,
            "exact_success": report["exact_success"],
            "success": success_state in TERMINAL_SUCCESS_STATES,
            "failure_detected": report["failure_detected"],
            "partial_success": report["partial_success_detected"],
            "partial_success_detected": report[
                "partial_success_detected"
            ],
            "episode_completed": report["episode_completed"],
            "retry_allowed": report["retry_allowed"],
            "shutdown_mode": report["shutdown_mode"],
            "termination_reason": report["termination_reason"],
            "residual_analysis": report["residual_analysis"],
        })

        return evaluation, report

    def build_residual_analysis(
        self,
        context,
        residual_difference_count,
        success_state,
    ):

        predicted = context.get("predicted_output")
        target = context.get("output_grid")
        if hasattr(target, "grid"):
            target = target.grid

        residual_locations = []
        residual_type = "none"
        probable_root_cause = "none"
        future_learning_priority = "none"

        try:
            predicted_array = np.array(predicted)
            target_array = np.array(target)
            if (
                predicted_array.size
                and target_array.size
                and predicted_array.shape == target_array.shape
            ):
                differences = np.argwhere(predicted_array != target_array)
                residual_locations = [
                    [int(row), int(col)]
                    for row, col in differences[:10]
                ]
                if len(differences):
                    residual_values = [
                        (
                            int(predicted_array[row, col]),
                            int(target_array[row, col]),
                        )
                        for row, col in differences[:10]
                    ]
                    residual_type = (
                        "localized_color_residual"
                        if all(left != right for left, right in residual_values)
                        else "localized_residual"
                    )
                    probable_root_cause = (
                        "localized_prediction_mismatch"
                    )
                    future_learning_priority = (
                        "refine_residual_localization"
                    )
            elif residual_difference_count > 0:
                residual_type = "shape_or_alignment_residual"
                probable_root_cause = "output_shape_mismatch"
                future_learning_priority = "preserve_spatial_safety_gate"
        except Exception:
            if residual_difference_count > 0:
                residual_type = "unknown_residual"
                probable_root_cause = "residual_analysis_unavailable"
                future_learning_priority = "collect_residual_evidence"

        if (
            residual_difference_count > 0
            and future_learning_priority == "none"
        ):
            residual_type = "localized_residual"
            probable_root_cause = "localized_prediction_mismatch"
            future_learning_priority = "refine_residual_localization"

        return {
            "system": "RESIDUAL_ANALYSIS_REPORT",
            "residual_difference_count": residual_difference_count,
            "residual_locations": residual_locations,
            "residual_type": residual_type,
            "probable_root_cause": probable_root_cause,
            "future_learning_priority": future_learning_priority,
            "blocks_runtime_termination": False,
            "success_state": success_state,
        }

    def background_task_control(self, episode_completed):

        disabled = {
            "self_improvement": bool(episode_completed),
            "strategy_evolution": bool(episode_completed),
            "deep_introspection": bool(episode_completed),
            "curiosity_expansion": bool(episode_completed),
            "reward_optimization": bool(episode_completed),
            "governance_rehearsal": bool(episode_completed),
        }
        return {
            "episode_completed": bool(episode_completed),
            "disabled_tasks": disabled,
            "reason": (
                "episode_completed"
                if episode_completed
                else "episode_active"
            ),
        }

    def build_audit_report(self):

        return {
            "system": "SUCCESS_SEMANTICS_AUDIT_REPORT",
            "modules": [
                {
                    "module": "runtime/evaluation/evaluation_engine.py",
                    "success_criteria": ["accuracy == 1.0"],
                    "failure_criteria": ["accuracy < 1.0"],
                    "exact_success_dependencies": ["success flag"],
                    "shutdown_dependencies": [],
                    "retry_triggers": [],
                    "learning_triggers": ["evaluation history"],
                },
                {
                    "module": "runtime/stages/evaluation.py",
                    "success_criteria": [
                        "success_semantics_engine terminal states",
                    ],
                    "failure_criteria": [
                        "RECOVERABLE_FAILURE",
                        "CRITICAL_FAILURE",
                    ],
                    "exact_success_dependencies": [
                        "meta outcome feedback",
                        "temporal memory",
                    ],
                    "shutdown_dependencies": [
                        "episode_completed",
                        "shutdown_mode",
                    ],
                    "retry_triggers": ["retry_allowed"],
                    "learning_triggers": [
                        "residual_analysis",
                        "learning_signal",
                    ],
                },
                {
                    "module": "runtime/reflection/failure_analyzer.py",
                    "success_criteria": [
                        "terminal success states suppress failure",
                    ],
                    "failure_criteria": [
                        "RECOVERABLE_FAILURE",
                        "CRITICAL_FAILURE",
                    ],
                    "exact_success_dependencies": ["legacy success flag"],
                    "shutdown_dependencies": [],
                    "retry_triggers": ["recovery_plan"],
                    "learning_triggers": ["failure_history"],
                },
                {
                    "module": "runtime/meta/meta_controller.py",
                    "success_criteria": [
                        "EXACT_SUCCESS",
                        "SUCCESS_WITH_RESIDUALS",
                    ],
                    "failure_criteria": ["critical motivation/governance"],
                    "exact_success_dependencies": [
                        "STOP_AFTER_SUCCESS action",
                    ],
                    "shutdown_dependencies": ["shutdown_mode"],
                    "retry_triggers": ["RUN_LOCALIZATION"],
                    "learning_triggers": ["meta_action_history"],
                },
                {
                    "module": "runtime/pipeline.py",
                    "success_criteria": [
                        "terminal success shutdown allowed",
                    ],
                    "failure_criteria": ["failed stages"],
                    "exact_success_dependencies": [
                        "_exact_success_shutdown_allowed",
                    ],
                    "shutdown_dependencies": [
                        "post_success_shutdown",
                        "finalize_runtime_fast",
                    ],
                    "retry_triggers": ["stage recovery"],
                    "learning_triggers": [
                        "minimal_success_record",
                        "essential metrics",
                    ],
                },
                {
                    "module": "runtime/motivation/*",
                    "success_criteria": [
                        "outcome_class exact_success",
                        "outcome_class success_with_residuals",
                    ],
                    "failure_criteria": [
                        "recoverable_failure",
                        "critical_failure",
                    ],
                    "exact_success_dependencies": ["reward floor"],
                    "shutdown_dependencies": [],
                    "retry_triggers": ["penalty severity"],
                    "learning_triggers": [
                        "reward_distribution",
                        "penalty_distribution",
                    ],
                },
            ],
            "timestamp": str(datetime.utcnow()),
        }

    def _learning_progress(self, context, localization_report):

        return any([
            bool(context.get("new_dependencies")),
            bool(context.get("new_contexts")),
            bool(context.get("semantic_abstractions")),
            localization_report.get("localization_ready") is True,
        ])

    def _identity_unstable(self, context):

        state = str(
            context.get(
                "identity_runtime_state",
                context.get("identity_governance_state", ""),
            )
        ).upper()
        return state in {
            "UNSTABLE",
            "IDENTITY_GOVERNANCE_UNSTABLE",
            "TEMPORARY_RECOVERY_HOLD",
        }

    def _first_mapping(self, context, keys):

        for key in keys:
            value = self._mapping(context.get(key))
            if value:
                return value
        return {}

    def _mapping(self, value):

        return value if isinstance(value, dict) else {}

    def _number(self, value, default=0.0):

        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _integer(self, value):

        try:
            return int(value)
        except (TypeError, ValueError):
            return None


success_semantics_engine = SuccessSemanticsEngine()
