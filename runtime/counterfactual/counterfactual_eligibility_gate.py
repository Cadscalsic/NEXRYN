"""Eligibility gate for bounded counterfactual reasoning."""

from __future__ import annotations

from typing import Any, Mapping


DEFAULT_BUDGET = {
    "max_counterfactuals": 4,
    "max_depth": 2,
    "max_simulation_time_seconds": 1.0,
    "max_total_cells_evaluated": 500,
}


class CounterfactualEligibilityGate:
    system_name = "counterfactual_eligibility_gate"

    def evaluate(
        self,
        arena_report: Mapping[str, Any] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        arena_report = arena_report if isinstance(arena_report, Mapping) else {}
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        trigger_reasons = []
        skip_reasons = []
        if _score(arena_report.get("selection_margin")) < float(runtime_context.get("safe_selection_margin", 0.05)):
            trigger_reasons.append("selection_margin_below_threshold")
        if arena_report.get("selection_state") in {"CONDITIONAL_WINNER", "TIE_REQUIRES_REVIEW", "SANDBOX_ONLY_WINNER"}:
            trigger_reasons.append(f"arena_state_{arena_report.get('selection_state')}")
        if _score(arena_report.get("winner_score")) < float(runtime_context.get("high_winner_score", 0.90)):
            trigger_reasons.append("winner_score_not_high")
        if int(arena_report.get("residual_difference_count", arena_report.get("winner_difference_count", 0)) or 0) > 0:
            trigger_reasons.append("residual_difference_present")
        if _score(arena_report.get("localization_support", 1.0)) < float(runtime_context.get("preferred_localization_support", 0.75)):
            trigger_reasons.append("localization_confidence_low")
        if arena_report.get("candidate_count", 0) and arena_report.get("candidate_count", 0) > 1:
            trigger_reasons.append("multiple_candidates_available")
        if arena_report.get("selection_state") == "WINNER_SELECTED" and _score(arena_report.get("winner_score")) >= 0.95 and _score(arena_report.get("selection_margin")) >= 0.10:
            skip_reasons.append("exact_or_high_confidence_success")
        if runtime_context.get("cognitive_budget_exhausted"):
            skip_reasons.append("cognitive_budget_exhausted")
        if runtime_context.get("counterfactual_governance_disabled"):
            skip_reasons.append("governance_disables_exploration")
        if runtime_context.get("execution_mode") == "fast" and not trigger_reasons:
            skip_reasons.append("fast_mode_without_risk_signal")
        if runtime_context.get("cached_counterfactual_task_signature") == runtime_context.get("task_signature") and runtime_context.get("task_signature"):
            skip_reasons.append("recent_counterfactual_cache_hit")

        blocked = any(reason in skip_reasons for reason in ("cognitive_budget_exhausted", "governance_disables_exploration"))
        required = bool(trigger_reasons) and not blocked and "exact_or_high_confidence_success" not in skip_reasons
        state = "BLOCKED" if blocked else "REQUIRED" if required else "SKIPPED" if skip_reasons else "OPTIONAL"
        risk_level = "HIGH" if len(trigger_reasons) >= 3 else "MEDIUM" if trigger_reasons else "LOW"
        budget = dict(DEFAULT_BUDGET)
        budget.update(runtime_context.get("counterfactual_budget", {}) if isinstance(runtime_context.get("counterfactual_budget"), Mapping) else {})
        return {
            "system": self.system_name,
            "counterfactual_required": required,
            "trigger_reasons": trigger_reasons,
            "skip_reasons": skip_reasons,
            "risk_level": risk_level,
            "counterfactual_budget": budget,
            "budget_source": "runtime_profile" if runtime_context.get("counterfactual_budget") else "default",
            "eligibility_state": state,
        }


def _score(value: Any) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0


counterfactual_eligibility_gate = CounterfactualEligibilityGate()

__all__ = ["CounterfactualEligibilityGate", "counterfactual_eligibility_gate", "DEFAULT_BUDGET"]
