from runtime.world.soft_execution_gate import soft_execution_gate
from runtime.transformation_localization import (
    execution_readiness_calibrator,
    localization_controller,
)
from runtime.transformation_localization.localization_metrics import (
    EXECUTION_THRESHOLD,
    MAX_WORLD_MODEL_RETRIES,
)
from runtime.governance.world_governance_introspection import (
    world_governance_introspection,
)


class WorldModelGate:
    """Requires explicit world-model authorization before transformation."""

    LOCALIZATION_CONFIRMED_STATE = "LOCALIZATION_CONFIRMED_EXECUTION"
    LOCALIZATION_COMPATIBLE_OPERATIONS = {
        "replace_color",
        "preserve_color",
        "object_color_mapping",
        "duplicate_object",
        "translate_down",
        "translate_up",
        "translate_left",
        "translate_right",
        "translation",
        "rotate",
        "rotation",
        "reflect",
        "reflection",
        "scale",
        "scaling",
        "object_level_translate",
    }

    def evaluate(self, anticipation_report=None):
        anticipation_report = (
            anticipation_report
            if isinstance(anticipation_report, dict)
            else {}
        )
        execution_accepted = (
            anticipation_report.get("execution_accepted", False) is True
        )
        soft_execution_report = soft_execution_gate.evaluate(
            anticipation_report
        )
        motion_governance = self._motion_governance_report(
            anticipation_report
        )
        sandbox_execution_accepted = (
            soft_execution_report["soft_execution_authorized"]
        )
        localization_readiness = self._execution_readiness_report(
            anticipation_report
        )
        localization_confirmed = (
            not execution_accepted
            and localization_readiness.get("execution_ready") is True
        )
        probation_execution = (
            not execution_accepted
            and localization_readiness.get("execution_probation") is True
        )
        if localization_confirmed:
            execution_accepted = True
            sandbox_execution_accepted = False
        elif probation_execution:
            sandbox_execution_accepted = True
        if motion_governance.get("execution_rejected") is True:
            execution_accepted = False
            sandbox_execution_accepted = False
            localization_confirmed = False
            probation_execution = False
        base_rejection = (
            not execution_accepted
            and not sandbox_execution_accepted
            and motion_governance.get("execution_rejected") is not True
        )
        governance_introspection = world_governance_introspection.evaluate(
            {
                **anticipation_report,
                "execution_readiness":
                localization_readiness.get("execution_readiness", 0.0),
                "confidence_required": EXECUTION_THRESHOLD,
                "confidence_observed":
                localization_readiness.get("execution_readiness", 0.0),
            },
            current_decision=(
                "EXECUTION_ABORTED_WORLD_MODEL_REJECTION"
                if base_rejection
                else "ALLOW"
                if execution_accepted
                else "ALLOW_SANDBOX"
                if sandbox_execution_accepted
                else "DENY"
            ),
            rejection_reason=(
                "motion_governance_rejection"
                if motion_governance.get("execution_rejected") is True
                else "world_model_rejected_execution_without_explanation"
                if base_rejection
                else None
            ),
            triggered_rules=self._triggered_rules(
                anticipation_report,
                localization_readiness,
                motion_governance,
                base_rejection,
            ),
        )
        governance_decision = governance_introspection["decision"]
        if (
            base_rejection
            and governance_decision in {"ALLOW_SANDBOX", "ALLOW_PROBATION"}
        ):
            sandbox_execution_accepted = True
        elif base_rejection and governance_decision == "ALLOW":
            execution_accepted = True
            sandbox_execution_accepted = False
        gate_state = (
            "EXECUTION_ABORTED_MOTION_GOVERNANCE"
            if motion_governance.get("execution_rejected") is True
            else
            self.LOCALIZATION_CONFIRMED_STATE
            if localization_confirmed
            else
            "EXECUTION_PROBATION"
            if probation_execution
            else
            "EXECUTION_AUTHORIZED"
            if execution_accepted
            else "EXECUTION_ROUTED_TO_SANDBOX"
            if sandbox_execution_accepted
            else "EXECUTION_ABORTED_WORLD_MODEL_REJECTION"
        )
        acceptance_state = (
            "EXECUTION_ACCEPTED"
            if localization_confirmed
            else anticipation_report.get("acceptance_state")
        )
        return {
            "system": "world_model_gate",
            "execution_authorized": execution_accepted,
            "execution_aborted": not execution_accepted,
            "sandbox_execution_authorized": sandbox_execution_accepted,
            "soft_execution_report": soft_execution_report,
            "gate_state": gate_state,
            "acceptance_state":
            acceptance_state,
            "explicit_execution_acceptance_required": True,
            "sandbox_execution_isolated": sandbox_execution_accepted,
            "localization_confirmed": localization_confirmed,
            "probation_execution": probation_execution,
            "execution_probation": probation_execution,
            "execution_readiness":
            localization_readiness.get("execution_readiness", 0.0),
            "localization_execution_ready":
            localization_readiness.get("execution_ready", False),
            "LOCALIZATION_REPORT":
            localization_readiness.get("LOCALIZATION_REPORT", {}),
            "motion_governance":
            motion_governance,
            "governance_decision": governance_decision,
            "governance_decision_report":
            governance_introspection.get("governance_decision_report", {}),
            "WORLD GOVERNANCE INTROSPECTION REPORT":
            governance_introspection,
            "world_governance_introspection_report":
            governance_introspection,
            "learning_credit_authorized":
            governance_introspection.get("learning_credit_authorized", False),
            "evidence_accumulation_authorized":
            governance_introspection.get(
                "evidence_accumulation_authorized",
                False,
            ),
        }

    def _motion_governance_report(self, anticipation_report):

        motion_report = (
            anticipation_report.get("object_motion_report")
            or anticipation_report.get("OBJECT_MOTION_REPORT")
            or {}
        )
        if not isinstance(motion_report, dict):
            motion_report = {}

        motion_pattern = str(
            motion_report.get("motion_pattern", "")
        )
        variance = self._number(
            motion_report.get("translation_variance"),
            0.0,
        )
        global_confidence = self._number(
            anticipation_report.get(
                "global_translation_confidence",
                motion_report.get("global_translation_confidence", 0.0),
            ),
            0.0,
        )
        independent_motion = motion_pattern == "independent_translation"
        reject_global = global_confidence > 0.8 and variance > 0.1
        return {
            "motion_pattern": motion_pattern,
            "translation_variance": variance,
            "global_translation_disabled": independent_motion or reject_global,
            "object_level_simulation_required": independent_motion,
            "execution_rejected": reject_global,
            "reasons": (
                ["global_translation_confidence_conflicts_with_object_variance"]
                if reject_global
                else []
            ),
        }

    def _triggered_rules(
        self,
        anticipation_report,
        localization_readiness,
        motion_governance,
        base_rejection,
    ):
        rules = []
        if base_rejection:
            rules.append("explicit_execution_acceptance_required")
        if motion_governance.get("execution_rejected") is True:
            rules.extend(motion_governance.get("reasons", []))
        readiness_state = localization_readiness.get("readiness_state")
        if readiness_state:
            rules.append(readiness_state)
        if self._contradiction_detected(anticipation_report):
            rules.append("contradiction_detected")
        if self._identity_unstable(anticipation_report):
            rules.append("identity_unstable")
        if anticipation_report.get("ontology_integrity_violation") is True:
            rules.append("ontology_integrity_violation")
        return list(dict.fromkeys(rules))

    def _execution_readiness_report(
        self,
        anticipation_report,
    ):

        localization = anticipation_report.get(
            "transformation_localization",
            {},
        )
        if not isinstance(localization, dict):
            return {
                "execution_ready": False,
                "execution_readiness": 0.0,
                "readiness_state": "NO_LOCALIZATION_REPORT",
            }

        localized_program = (
            anticipation_report.get("localized_synthesized_program")
            or localization.get("localized_program")
        )
        if not isinstance(localized_program, dict):
            return {
                "execution_ready": False,
                "execution_readiness": 0.0,
                "readiness_state": "NO_LOCALIZED_PROGRAM",
            }

        hypothesis = anticipation_report.get("winner_hypothesis", {})
        if not isinstance(hypothesis, dict):
            hypothesis = anticipation_report.get("hypothesis", {})
        if not isinstance(hypothesis, dict):
            hypothesis = {}

        prediction_report = anticipation_report.get("prediction_report", {})
        if not isinstance(prediction_report, dict):
            prediction_report = {}

        prediction_accuracy = prediction_report.get(
            "prediction_accuracy",
            prediction_report.get("accuracy", 0.0),
        )

        if (
            "LOCALIZATION_REPORT" not in localization
            or self._number(localization.get("localization_confidence")) < 0.70
        ):
            localization = localization_controller.calibrate(
                localization,
                synthesized_program=localized_program,
                hypothesis=hypothesis,
                prediction_accuracy=self._number(prediction_accuracy),
                integrity_preserved=(
                    self._mapping(
                        anticipation_report.get("execution_integrity_report")
                    ).get("integrity_preserved") is True
                    or anticipation_report.get("execution_integrity_preserved") is True
                    or anticipation_report.get("preflight_integrity_preserved") is True
                ),
                identity_stable=not self._identity_unstable(anticipation_report),
                contradiction_detected=self._contradiction_detected(
                    anticipation_report
                ),
                runtime_context=anticipation_report,
            )

        if self._contradiction_detected(anticipation_report):
            return {
                "execution_ready": False,
                "execution_readiness": 0.0,
                "readiness_state": "CONTRADICTION_DETECTED",
            }

        if self._identity_unstable(anticipation_report):
            return {
                "execution_ready": False,
                "execution_readiness": 0.0,
                "readiness_state": "IDENTITY_UNSTABLE",
            }

        if not self._localized_program_compatible(localized_program, localization):
            return {
                "execution_ready": False,
                "execution_readiness": 0.0,
                "readiness_state": "LOCALIZED_PROGRAM_INCOMPATIBLE",
            }

        residual_difference_count = anticipation_report.get(
            "residual_difference_count"
        )
        localized_step_count = localization.get(
            "localized_step_count",
            localized_program.get("step_count", 0),
        )
        integrity_report = anticipation_report.get(
            "execution_integrity_report",
            {},
        )
        if not isinstance(integrity_report, dict):
            integrity_report = {}
        localization_confidence = self._number(
            localization.get("localization_confidence"),
            self._localization_confidence(localization),
        )
        hypothesis_confidence = self._number(
            hypothesis.get("confidence"),
            prediction_accuracy,
        )
        integrity_preserved = (
            integrity_report.get("integrity_preserved") is True
            or anticipation_report.get("execution_integrity_preserved") is True
            or anticipation_report.get("preflight_integrity_preserved") is True
        )
        retry_count = int(
            self._number(
                anticipation_report.get(
                    "world_model_retry_count",
                    localization.get("world_model_retry_count", 0),
                ),
                0,
            )
        )
        search_retry_limit_reached = (
            str(anticipation_report.get("acceptance_state", "")).upper()
            == "SEARCH_CANDIDATE_ONLY"
            and retry_count >= MAX_WORLD_MODEL_RETRIES
        )
        readiness = execution_readiness_calibrator.evaluate(
            hypothesis_confidence=hypothesis_confidence,
            localization_confidence=localization_confidence,
            prediction_accuracy=prediction_accuracy,
            integrity_preserved=integrity_preserved,
            identity_stable=True,
            contradiction_detected=False,
        )
        step_ready = isinstance(localized_step_count, int) and localized_step_count > 0
        residual_ready = (
            residual_difference_count is None
            or (
                isinstance(residual_difference_count, int)
                and residual_difference_count <= 2
            )
        )
        topology_safe = (
            self._topology_preserved(localization)
            or localization.get("fallback_used") is not None
        )
        identity_safe = (
            self._identity_confidence(localization) >= 0.70
            or localization.get("fallback_used") is not None
            or localization.get("target_objects")
        )
        shape_safe = (
            self._shape_similarity(localization) >= 0.70
            or localization.get("fallback_used") is not None
            or localization.get("target_objects")
        )
        execution_ready = (
            readiness.get("execution_readiness", 0.0) >= EXECUTION_THRESHOLD
            and localization_confidence >= 0.70
            and step_ready
            and residual_ready
            and topology_safe
            and identity_safe
            and shape_safe
            and integrity_preserved
        )
        probation_execution = localization.get("execution_probation") is True
        if probation_execution:
            execution_ready = False
            readiness["execution_governance_state"] = "EXECUTION_PROBATION"
            readiness["readiness_state"] = "EXECUTION_PROBATION"
            readiness["sandbox_execution_authorized"] = True
        if search_retry_limit_reached and execution_ready:
            readiness["readiness_state"] = "SEARCH_RETRY_LIMIT_EXECUTE_BEST_CANDIDATE"
        readiness["execution_ready"] = execution_ready
        readiness["execution_probation"] = probation_execution
        readiness["localization_recovery_mode"] = (
            localization.get("localization_recovery_mode") is True
        )
        readiness["localized_step_count"] = localized_step_count
        readiness["retry_count"] = retry_count
        readiness["max_world_model_retries"] = MAX_WORLD_MODEL_RETRIES
        readiness["LOCALIZATION_REPORT"] = localization.get(
            "LOCALIZATION_REPORT",
            {},
        )
        readiness["EXECUTION READINESS REPORT"] = localization.get(
            "EXECUTION READINESS REPORT",
            {},
        )
        readiness["OBJECT GROUNDING REPORT"] = localization.get(
            "OBJECT GROUNDING REPORT",
            {},
        )
        readiness["target_objects"] = localization.get("target_objects", [])
        return readiness

    def _localization_confirmed_execution_allowed(
        self,
        anticipation_report,
    ):
        return (
            self._execution_readiness_report(anticipation_report).get(
                "execution_ready"
            )
            is True
        )

    def _localized_program_compatible(
        self,
        localized_program,
        localization,
    ):

        steps = localized_program.get("steps", [])
        if not isinstance(steps, list) or not steps:
            return False

        for step in steps:
            operation = str(step.get("operation", "")).lower()
            parameters = step.get("parameters", {})
            if operation not in self.LOCALIZATION_COMPATIBLE_OPERATIONS:
                return False
            if isinstance(parameters, dict):
                localization_type = str(
                    parameters.get("localization_type", "")
                ).lower()
                if localization_type and localization_type != "color_mapping":
                    return False

        for report in localization.get("localization_reports", []):
            if not isinstance(report, dict):
                continue
            for rule in report.get("localized_rules", []):
                if not isinstance(rule, dict):
                    continue
                mapping_type = str(rule.get("mapping_type", "")).lower()
                localization_type = str(
                    rule.get("localization_type", "")
                ).lower()
                if mapping_type and mapping_type != "object_color_mapping":
                    return False
                if localization_type and localization_type != "color_mapping":
                    return False

        return True

    def _localization_confidence(self, localization):

        values = []
        for report in localization.get("localization_reports", []):
            if isinstance(report, dict):
                values.append(report.get("localization_confidence"))
                for rule in report.get("localized_rules", []):
                    if isinstance(rule, dict):
                        values.append(rule.get("confidence"))
        numeric = [self._number(value, None) for value in values]
        numeric = [value for value in numeric if value is not None]
        if not numeric:
            return 0.0
        return min(numeric)

    def _identity_confidence(self, localization):

        values = []
        for report in localization.get("localization_reports", []):
            if not isinstance(report, dict):
                continue
            for match in report.get("object_matches", []):
                if isinstance(match, dict):
                    values.append(match.get("identity_confidence"))
        numeric = [self._number(value, None) for value in values]
        numeric = [value for value in numeric if value is not None]
        if not numeric:
            return 0.0
        return min(numeric)

    def _topology_preserved(self, localization):

        reports = localization.get("localization_reports", [])
        if not isinstance(reports, list) or not reports:
            return False
        for report in reports:
            if not isinstance(report, dict):
                return False
            matches = report.get("object_matches", [])
            if matches:
                for match in matches:
                    if (
                        isinstance(match, dict)
                        and match.get("topology_preserved") is not True
                    ):
                        return False
        return True

    def _shape_similarity(self, localization):

        values = []
        for report in localization.get("localization_reports", []):
            if not isinstance(report, dict):
                continue
            for match in report.get("object_matches", []):
                if isinstance(match, dict):
                    values.append(match.get("shape_similarity"))
        numeric = [self._number(value, None) for value in values]
        numeric = [value for value in numeric if value is not None]
        if not numeric:
            return 0.0
        return min(numeric)

    def _contradiction_detected(self, anticipation_report):

        return (
            anticipation_report.get("contradiction_detected") is True
            or bool(anticipation_report.get("unresolved_contradictions"))
            or bool(anticipation_report.get("semantic_contradictions"))
        )

    def _identity_unstable(self, anticipation_report):

        state = str(
            anticipation_report.get(
                "identity_runtime_state",
                anticipation_report.get("identity_governance_state", ""),
            )
        ).upper()
        return state in {
            "UNSTABLE",
            "IDENTITY_GOVERNANCE_UNSTABLE",
            "TEMPORARY_RECOVERY_HOLD",
        }

    def _number(self, value, default=0.0):

        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _mapping(self, value):

        return value if isinstance(value, dict) else {}


world_model_gate = WorldModelGate()


__all__ = [
    "WorldModelGate",
    "world_model_gate",
]
