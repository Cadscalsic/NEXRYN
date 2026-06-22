"""Lightweight evaluation reporting metadata."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .evaluation_result import EvaluationResult


class EvaluationReporter:
    def build(
        self,
        result: EvaluationResult,
        budget_report: dict[str, Any],
        report_deferred_count: int,
    ) -> dict[str, Any]:
        return {
            "evaluation_result": asdict(result),
            "evaluation_duration": result.evaluation_duration,
            "report_deferred_count": report_deferred_count,
            "metrics_truncated": bool(budget_report.get("metrics_truncated")),
        }
