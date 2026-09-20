# ============================================
# NEXRYN EARLY EXIT CONTROLLER
# ============================================

from dataclasses import dataclass


@dataclass
class EarlyExitDecision:

    should_stop: bool

    reason: str

    confidence: float

    uncertainty: float

    current_accuracy: float


class EarlyExitController:

    def __init__(
        self,
        accuracy_threshold=0.99,
        uncertainty_threshold=0.15,
        identity_threshold=0.95,
        world_model_threshold=0.95,
        contradiction_threshold=0.0,
    ):

        self.accuracy_threshold = accuracy_threshold
        self.uncertainty_threshold = uncertainty_threshold
        self.identity_threshold = identity_threshold
        self.world_model_threshold = world_model_threshold
        self.contradiction_threshold = contradiction_threshold

    def evaluate(self, runtime_context):

        prediction_accuracy = self._first_float(
            runtime_context,
            [
                ("prediction_report", "prediction_accuracy"),
                ("prediction_report", "accuracy"),
                ("transformation_stage_report", "prediction_accuracy"),
                ("evaluation_result", "accuracy"),
                ("evaluation_report", "accuracy"),
            ],
            0.0,
        )
        confidence = self._first_float(
            runtime_context,
            [
                ("prediction_report", "prediction_confidence"),
                ("cognitive_governance_report", "prediction_confidence"),
                ("winner_hypothesis", "confidence"),
            ],
            prediction_accuracy,
        )
        uncertainty = self._first_float(
            runtime_context,
            [
                ("prediction_report", "uncertainty"),
                ("uncertainty_report", "uncertainty"),
                ("current_task_profile", "uncertainty"),
            ],
            max(0.0, 1.0 - confidence),
        )
        identity_continuity = self._first_float(
            runtime_context,
            [
                ("identity_continuity_guardian_report", "identity_continuity"),
                ("identity_continuity_engine_report", "identity_continuity"),
                ("prediction_report", "identity_continuity"),
            ],
            1.0,
        )
        world_model_fit = self._first_float(
            runtime_context,
            [
                ("prediction_report", "world_model_fit"),
                ("world_model_report", "world_model_fit"),
                ("execution_integrity_report", "world_model_fit"),
            ],
            prediction_accuracy,
        )
        contradiction_score = self._contradiction_score(runtime_context)
        unresolved_contradictions = self._has_items(
            runtime_context,
            [
                "unresolved_contradictions",
                "semantic_contradictions",
            ],
        )
        missing_dependencies = self._has_items(
            runtime_context,
            [
                "missing_critical_dependencies",
                "missing_dependencies",
            ],
        )
        governance_violations = self._has_items(
            runtime_context,
            [
                "governance_violations",
                "truth_gate_violations",
            ],
        )

        if unresolved_contradictions:
            return self._decision(
                False,
                "unresolved_contradictions_present",
                confidence,
                uncertainty,
                prediction_accuracy,
            )

        if missing_dependencies:
            return self._decision(
                False,
                "missing_critical_dependencies_present",
                confidence,
                uncertainty,
                prediction_accuracy,
            )

        if governance_violations:
            return self._decision(
                False,
                "governance_violations_present",
                confidence,
                uncertainty,
                prediction_accuracy,
            )

        if (
            prediction_accuracy >= self.accuracy_threshold
            and uncertainty <= self.uncertainty_threshold
            and identity_continuity >= self.identity_threshold
            and world_model_fit >= self.world_model_threshold
            and contradiction_score <= self.contradiction_threshold
        ):

            return self._decision(
                True,
                "sufficient_trustworthy_confidence",
                confidence,
                uncertainty,
                prediction_accuracy,
            )

        return self._decision(
            False,
            "confidence_or_safety_threshold_not_met",
            confidence,
            uncertainty,
            prediction_accuracy,
        )

    def build_report(self, decision):

        return {
            "should_stop": decision.should_stop,
            "reason": decision.reason,
            "confidence": decision.confidence,
            "uncertainty": decision.uncertainty,
            "prediction_accuracy": decision.current_accuracy,
        }

    def _decision(
        self,
        should_stop,
        reason,
        confidence,
        uncertainty,
        current_accuracy,
    ):

        return EarlyExitDecision(
            should_stop=bool(should_stop),
            reason=reason,
            confidence=round(float(confidence), 4),
            uncertainty=round(float(uncertainty), 4),
            current_accuracy=round(float(current_accuracy), 4),
        )

    def _first_float(self, runtime_context, paths, default):

        for root, key in paths:
            source = runtime_context.get(root)
            value = None
            if isinstance(source, dict):
                value = source.get(key)
            elif hasattr(source, key):
                value = getattr(source, key)
            if isinstance(value, (int, float)):
                return float(value)
        return float(default)

    def _has_items(self, runtime_context, keys):

        for key in keys:
            value = runtime_context.get(key)
            if isinstance(value, list) and value:
                return True
            if isinstance(value, dict) and value:
                return True
        return False

    def _contradiction_score(self, runtime_context):

        contradiction_report = runtime_context.get(
            "contradiction_resolution_report",
            {},
        )
        if isinstance(contradiction_report, dict):
            value = contradiction_report.get(
                "contradiction_score",
                contradiction_report.get("unresolved_count"),
            )
            if isinstance(value, (int, float)):
                return float(value)

        cognitive_report = runtime_context.get(
            "cognitive_governance_report",
            {},
        )
        if isinstance(cognitive_report, dict):
            contradictions = cognitive_report.get(
                "semantic_contradictions",
                [],
            )
            if isinstance(contradictions, list):
                return float(len(contradictions))

        return 0.0


early_exit_controller = EarlyExitController()
