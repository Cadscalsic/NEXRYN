from __future__ import annotations

from typing import Any, Mapping


class ResidualImprovementGate:
    """Compare before/after repair metrics under governance constraints."""

    def compare(
        self,
        before: Mapping[str, Any] | None,
        after: Mapping[str, Any] | None,
        *,
        governance: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        before_metrics = before if isinstance(before, Mapping) else {}
        after_metrics = after if isinstance(after, Mapping) else {}
        governance_report = governance if isinstance(governance, Mapping) else {}

        if governance_report.get("governance_valid") is False or governance_report.get("critical_governance_block") is True:
            decision = "REPAIR_GOVERNANCE_BLOCKED"
        else:
            before_residual = _integer(
                before_metrics.get("residual_count", before_metrics.get("difference_count", before_metrics.get("residual_difference_count", 0))),
                0,
            )
            after_residual = _integer(
                after_metrics.get("residual_count", after_metrics.get("difference_count", after_metrics.get("residual_difference_count", 0))),
                0,
            )
            before_accuracy = _number(
                before_metrics.get("prediction_accuracy", before_metrics.get("accuracy", 0.0)),
            )
            after_accuracy = _number(
                after_metrics.get("prediction_accuracy", after_metrics.get("accuracy", 0.0)),
            )
            identity_preserved = after_metrics.get("identity_integrity", True) is not False
            topology_preserved = after_metrics.get("topology_integrity", True) is not False
            if after_residual == 0 and after_accuracy >= 1.0 and identity_preserved and topology_preserved:
                decision = "REPAIR_EXACT_SUCCESS"
            elif (
                (after_residual < before_residual or after_accuracy > before_accuracy)
                and identity_preserved
                and topology_preserved
            ):
                decision = "REPAIR_IMPROVED"
            elif after_residual > before_residual or after_accuracy < before_accuracy:
                decision = "REPAIR_REGRESSED"
            else:
                decision = "REPAIR_NO_CHANGE"

        return {
            "repair_improvement_decision": decision,
            "repair_improved": decision in {"REPAIR_IMPROVED", "REPAIR_EXACT_SUCCESS"},
            "repair_exact_success": decision == "REPAIR_EXACT_SUCCESS",
            "before": dict(before_metrics),
            "after": dict(after_metrics),
        }


def _integer(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


residual_improvement_gate = ResidualImprovementGate()


__all__ = ["ResidualImprovementGate", "residual_improvement_gate"]
