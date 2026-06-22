"""Bounded evaluation controller."""

from __future__ import annotations

from dataclasses import asdict
import logging
import time
from typing import Any

from .async_metrics_writer import AsyncMetricsWriter
from .deferred_reporting_queue import DeferredReportingQueue
from .evaluation_reporter import EvaluationReporter
from .evaluation_result import EvaluationResult
from .evaluation_timeout_guard import EvaluationTimeoutGuard
from .metrics_budget_controller import MetricsBudgetController
from .metrics_collector import MetricsCollector
from .post_success_fast_path import PostSuccessFastPath


class EvaluationController:
    """Collect minimal metrics, enforce budgets, and hand off to shutdown."""

    def __init__(
        self,
        metrics_collector: MetricsCollector | None = None,
        budget_controller: MetricsBudgetController | None = None,
        fast_path: PostSuccessFastPath | None = None,
        reporting_queue: DeferredReportingQueue | None = None,
        metrics_writer: AsyncMetricsWriter | None = None,
        timeout_guard: EvaluationTimeoutGuard | None = None,
        reporter: EvaluationReporter | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.metrics_collector = metrics_collector or MetricsCollector()
        self.budget_controller = budget_controller or MetricsBudgetController()
        self.fast_path = fast_path or PostSuccessFastPath()
        self.reporting_queue = reporting_queue or DeferredReportingQueue()
        self.metrics_writer = metrics_writer or AsyncMetricsWriter()
        self.timeout_guard = timeout_guard or EvaluationTimeoutGuard()
        self.reporter = reporter or EvaluationReporter()
        self.logger = logger or logging.getLogger(__name__)

    def evaluate(self, runtime_context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = runtime_context if isinstance(runtime_context, dict) else {}
        started_at = time.perf_counter()
        self.logger.info("[EVAL] start")
        metrics = self.metrics_collector.collect(context)
        if self.timeout_guard.exceeded(started_at):
            metrics = self.timeout_guard.force_minimal_evaluation(context)
        metrics, budget_report = self.budget_controller.enforce(metrics, started_at)
        self.logger.info("[EVAL] metrics collected")
        context, fast_path_activated = self.fast_path.activate_if_complete(
            context,
            metrics,
        )
        if fast_path_activated:
            self.logger.info("[EVAL] fast path activated")
            report_deferred_count = self.reporting_queue.defer_expensive_defaults()
        else:
            report_deferred_count = 0
        duration = time.perf_counter() - started_at
        result = EvaluationResult(
            accuracy=float(metrics.get("accuracy", 0.0)),
            success_state=str(metrics.get("success_state", "INCOMPLETE")),
            difference_count=int(metrics.get("difference_count", 0)),
            confidence=float(metrics.get("confidence_score", 0.0)),
            episode_completed=bool(metrics.get("episode_completed", False)),
            retry_allowed=bool(metrics.get("retry_allowed", True)),
            shutdown_mode=str(metrics.get("shutdown_mode", context.get("shutdown_mode", "normal"))),
            evaluation_duration=round(duration, 4),
        )
        context["evaluation_result"] = asdict(result)
        context["evaluation_metrics"] = dict(metrics)
        context["evaluation_budget_report"] = dict(budget_report)
        context["deferred_reporting_queue"] = self.reporting_queue.snapshot()
        context["evaluation_report"] = self.reporter.build(
            result,
            budget_report,
            report_deferred_count,
        )
        context["report_deferred_count"] = report_deferred_count
        context["metrics_truncated"] = bool(budget_report.get("metrics_truncated"))
        self.metrics_writer.write_async({
            "evaluation_summary": asdict(result),
            "success_statistics": {
                "episode_completed": result.episode_completed,
                "retry_allowed": result.retry_allowed,
            },
            "resource_usage": {
                "evaluation_duration": result.evaluation_duration,
                "report_deferred_count": report_deferred_count,
                "metrics_truncated": context["metrics_truncated"],
            },
        })
        self.logger.info("[EVAL] shutdown handoff")
        return context
