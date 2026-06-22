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
    ) -> dict[str, Any]:
        logger.info("[LOCALIZATION] start")
        budget = localization_budget_controller.start()
        localization_budget_controller.record_attempt(budget)

        result = deepcopy(localization if isinstance(localization, Mapping) else {})
        synthesized_program = (
            synthesized_program if isinstance(synthesized_program, Mapping) else {}
        )
        hypothesis = hypothesis if isinstance(hypothesis, Mapping) else {}
        original_ready = result.get("localization_ready") is True
        original_confidence = clamp(result.get("localization_confidence"))
        original_step_count = int(result.get("localized_step_count", 0) or 0)

        targeting = object_targeting_engine.identify(result, synthesized_program)
        result.update({
            "target_objects": targeting.target_objects,
            "transformation_scope": targeting.transformation_scope,
        })

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
            contradiction_detected=contradiction_detected,
        )
        result.update(readiness)
        logger.info("[LOCALIZATION] execution_ready=%s", readiness.get("execution_ready"))

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
