from __future__ import annotations

from typing import Any


class ReportBudgetManager:
    def __init__(self, max_runtime_fraction: float = 0.05):
        self.max_runtime_fraction = max_runtime_fraction

    def evaluate(
        self,
        report_seconds: float,
        total_runtime_seconds: float,
        report: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        total = max(float(total_runtime_seconds or 0.0), 0.0)
        budget = round(total * self.max_runtime_fraction, 4)
        seconds = round(float(report_seconds or 0.0), 4)
        exceeded = bool(total > 0 and seconds > budget)
        ratio = round(seconds / total, 4) if total else 0.0
        return {
            "system": "report_budget_manager",
            "report_generation_cost": seconds,
            "total_runtime_seconds": total,
            "report_budget_seconds": budget,
            "report_budget_usage": ratio,
            "report_budget_fraction": self.max_runtime_fraction,
            "report_budget_exceeded": exceeded,
            "report_compression_required": exceeded,
            "report_compression_ratio": self._compression_ratio(report),
        }

    def should_compress(
        self,
        report_seconds: float,
        total_runtime_seconds: float,
    ) -> bool:
        return self.evaluate(report_seconds, total_runtime_seconds).get(
            "report_compression_required",
            False,
        )

    def _compression_ratio(self, report: dict[str, Any] | None) -> float:
        if not isinstance(report, dict):
            return 0.0
        compact = report.get("compact_report", {})
        if not isinstance(compact, dict):
            return 0.0
        before = float(compact.get("final_context_size_estimate_before", 0) or 0)
        after = float(compact.get("final_context_size_estimate_after", 0) or 0)
        if before <= 0:
            return 0.0
        return round(max(0.0, 1.0 - (after / before)), 4)


report_budget_manager = ReportBudgetManager()


__all__ = ["ReportBudgetManager", "report_budget_manager"]
