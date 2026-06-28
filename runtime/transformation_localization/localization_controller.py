"""Coordinates localization confidence, fallback, and execution readiness."""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any, Mapping

from runtime.transformation_localization.execution_readiness_calibrator import (
    execution_readiness_calibrator,
)
from runtime.transformation_localization.localization_budget_controller import (
    localization_budget_controller,
)
from runtime.transformation_localization.localization_confidence_engine import (
    localization_confidence_engine,
)
from runtime.transformation_localization.localization_fallback_manager import (
    localization_fallback_manager,
)
from runtime.transformation_localization.localization_reporter import (
    localization_reporter,
)
from runtime.transformation_localization.object_targeting_engine import (
    object_targeting_engine,
)
from runtime.transformation_localization.localization_metrics import clamp
from runtime.grounding.object_grounding_engine import object_grounding_engine

logger = logging.getLogger(__name__)


class LocalizationController:
    def calibrate(
        self,
        localization: Mapping[str, Any] | None,
        synthesized_program: Mapping[str, Any] | None = None,
        hypothesis: Mapping[str, Any] | None = None,
        prediction_accuracy: float = 0.0,
        integrity_preserved: bool = True,
        identity_stable: bool = True,
        contradiction_detected: bool = False,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        logger.info("[LOCALIZATION] start")
        budget = localization_budget_controller.start()
        localization_budget_controller.record_attempt(budget)

        result = deepcopy(localization if isinstance(localization, Mapping) else {})
        synthesized_program = (
            synthesized_program if isinstance(synthesized_program, Mapping) else {}
        )
        hypothesis = hypothesis if isinstance(hypothesis, Mapping) else {}
        runtime_context = (
            runtime_context if isinstance(runtime_context, Mapping) else {}
        )
        original_ready = result.get("localization_ready") is True
        original_confidence = clamp(result.get("localization_confidence"))
        original_step_count = int(result.get("localized_step_count", 0) or 0)

        targeting = object_targeting_engine.identify(result, synthesized_program)
        result.update({
            "target_objects": targeting.target_objects,
            "transformation_scope": targeting.transformation_scope,
        })
        grounding_report = object_grounding_engine.ground(
            hypothesis=hypothesis,
            localization=result,
            synthesized_program=synthesized_program,
            runtime_context=runtime_context,
        )
        result = object_grounding_engine.recover_localization(
            result,
            grounding_report,
            synthesized_program=synthesized_program,
        )

        confidence = localization_confidence_engine.evaluate(
            result,
            hypothesis=hypothesis,
            synthesized_program=synthesized_program,
        )
        result.update(confidence)
        logger.info("[LOCALIZATION] confidence=%s", result.get("localization_confidence"))

        if (
            not original_ready
            or original_confidence <= 0.0
            or original_step_count <= 0
            or clamp(result.get("localization_confidence")) < 0.70
            or localization_budget_controller.exceeded(budget)
        ):
            force_fallback = (
                not original_ready
                or original_confidence <= 0.0
                or original_step_count <= 0
            )
            result = localization_fallback_manager.apply(
                result,
                synthesized_program,
                hypothesis=hypothesis,
                force=force_fallback,
            )
        logger.info("[LOCALIZATION] fallback=%s", result.get("fallback_used"))

        hypothesis_confidence = clamp(
            hypothesis.get(
                "confidence",
                max(
                    clamp(synthesized_program.get("confidence")),
                    prediction_accuracy,
                ),
            )
        )
        readiness = execution_readiness_calibrator.evaluate(
            hypothesis_confidence=hypothesis_confidence,
            localization_confidence=clamp(result.get("localization_confidence")),
            prediction_accuracy=prediction_accuracy,
            integrity_preserved=integrity_preserved,
            identity_stable=identity_stable,
            identity_confidence=1.0 if identity_stable else 0.0,
            dependency_support=max(
                clamp(hypothesis.get("semantic_support")),
                clamp(hypothesis.get("causal_support")),
                0.70
                if result.get("target_objects")
                or result.get("localized_step_count", 0) > 0
                else 0.0,
            ),
            arbitration_score=clamp(
                hypothesis.get("arbitration_score", hypothesis_confidence)
            ),
            winning_hypothesis_stable=hypothesis.get(
                "winning_hypothesis_stable",
                True,
            ) is not False,
            dependency_evidence_exists=bool(
                result.get("target_objects")
                or result.get("localized_step_count", 0) > 0
                or hypothesis.get("semantic_support")
                or hypothesis.get("causal_support")
            ),
            contradiction_detected=contradiction_detected,
        )
        if (
            result.get("localization_recovery_mode") is True
            and prediction_accuracy >= 0.90
            and readiness.get("safety_blocked") is not True
        ):
            readiness = {
                **readiness,
                "execution_ready": False,
                "sandbox_execution_authorized": True,
                "execution_governance_state": "EXECUTION_PROBATION",
                "readiness_state": "EXECUTION_PROBATION",
            }
        result.update(readiness)
        logger.info("[LOCALIZATION] execution_ready=%s", readiness.get("execution_ready"))
        from runtime.execution.execution_readiness_explainer import (
            execution_readiness_explainer,
        )

        governance = (
            runtime_context.get("WORLD GOVERNANCE INTROSPECTION REPORT")
            or runtime_context.get("world_governance_introspection_report")
            or {}
        )
        if not isinstance(governance, Mapping):
            governance = {}
        readiness_report = execution_readiness_explainer.explain(
            readiness=readiness,
            localization=result,
            grounding=grounding_report,
            governance=governance,
        )
        result["EXECUTION READINESS REPORT"] = readiness_report
        result["execution_readiness_report"] = readiness_report
        if readiness_report.get("readiness_class") == "EXECUTION_PROBATION":
            result["execution_probation"] = True
            result["execution_governance_state"] = "EXECUTION_PROBATION"

        budget_report = localization_budget_controller.report(budget)
        result.update(budget_report)
        result["LOCALIZATION_REPORT"] = localization_reporter.build(
            result,
            readiness,
            budget_report,
        )
        return result


localization_controller = LocalizationController()


__all__ = [
    "LocalizationController",
    "localization_controller",
]
