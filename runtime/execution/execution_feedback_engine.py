from __future__ import annotations

from typing import Any


class ExecutionFeedbackEngine:
    """Transform execution validation and residual evidence into learning signals."""

    def feedback(
        self,
        *,
        execution_result: dict[str, Any] | None = None,
        residual_report: dict[str, Any] | None = None,
        repair_report: dict[str, Any] | None = None,
        adaptation_report: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = execution_result if isinstance(execution_result, dict) else {}
        residual = residual_report if isinstance(residual_report, dict) else {}
        repair = repair_report if isinstance(repair_report, dict) else {}
        adaptation = adaptation_report if isinstance(adaptation_report, dict) else {}
        success = result.get("validation_success") is True and residual.get("residual_count", 0) == 0
        feedback = {
            "knowledge_feedback": "execution_success" if success else "execution_requires_repair",
            "truth_updates": ["program_validated"] if result.get("validation_success") else ["program_blocked"],
            "hypothesis_updates": ["increase_execution_confidence"] if success else ["attach_residual_evidence"],
            "execution_improvements": self._improvements(residual, repair, adaptation),
            "execution_feedback": "AVAILABLE",
            "knowledge_feedback_operational": True,
        }
        return feedback

    def _improvements(
        self,
        residual: dict[str, Any],
        repair: dict[str, Any],
        adaptation: dict[str, Any],
    ) -> list[str]:
        improvements = []
        if residual.get("missing_primitives"):
            improvements.append("learn_missing_primitives")
        if repair.get("generated_repairs"):
            improvements.append("reuse_localized_repairs")
        if adaptation.get("execution_adaptations"):
            improvements.append("prefer_adapted_program_ordering")
        return improvements or ["preserve_successful_program"]


execution_feedback_engine = ExecutionFeedbackEngine()


__all__ = ["ExecutionFeedbackEngine", "execution_feedback_engine"]
