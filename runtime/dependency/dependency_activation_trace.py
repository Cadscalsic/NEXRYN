from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable


TRACE_REPORT_KEY = "DEPENDENCY_ACTIVATION_TRACE_REPORT"
SKIP_REPORT_KEY = "DEPENDENCY_SKIP_REPORT"
MISSING_WARNING = "DEPENDENCY_ACTIVATION_MISSING"


@dataclass
class DependencyActivationTrace:
    """Records dependency activation decisions without executing new semantics."""

    concepts_detected: list[str] = field(default_factory=list)
    dependency_candidates: list[str] = field(default_factory=list)
    activation_requests: list[dict[str, Any]] = field(default_factory=list)
    activation_approvals: list[dict[str, Any]] = field(default_factory=list)
    activation_executions: list[dict[str, Any]] = field(default_factory=list)
    activation_failures: list[dict[str, Any]] = field(default_factory=list)
    skip_reasons: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)

    def detect_concepts(self, concepts: Iterable[Any]) -> None:
        for concept in concepts or []:
            token = _normalize(concept)
            if token and token not in self.concepts_detected:
                self.concepts_detected.append(token)
                self._event("concept_detected", concept=token)

    def set_dependency_candidates(self, candidates: Iterable[Any]) -> None:
        for candidate in candidates or []:
            token = _normalize(candidate)
            if token and token not in self.dependency_candidates:
                self.dependency_candidates.append(token)

    def request(
        self,
        requested_tool: str = "dependency_reasoning",
        requested_by: str = "unknown",
        reason: str | None = None,
        concepts: Iterable[Any] | None = None,
    ) -> dict[str, Any]:
        self.detect_concepts(concepts or [])
        request = {
            "requested_tool": requested_tool,
            "requested_by": requested_by,
            "request_state": "REQUESTED",
            "reason": reason,
            "concepts": list(self.concepts_detected),
            "timestamp": _timestamp(),
        }
        self.activation_requests.append(request)
        self._event("activation_requested", **request)
        return request

    def approve(
        self,
        requested_tool: str = "dependency_reasoning",
        approved_by: str = "unknown",
        reason: str | None = None,
    ) -> dict[str, Any]:
        approval = {
            "requested_tool": requested_tool,
            "approved_by": approved_by,
            "activation_state": "APPROVED",
            "reason": reason,
            "timestamp": _timestamp(),
        }
        self.activation_approvals.append(approval)
        self._event("activation_approved", **approval)
        return approval

    def enter_runtime(
        self,
        runtime_name: str = "dependency_runtime",
        concepts: Iterable[Any] | None = None,
    ) -> None:
        self.detect_concepts(concepts or [])
        self._event(
            "dependency_runtime_entered",
            runtime_name=runtime_name,
            concepts=list(self.concepts_detected),
        )

    def exit_runtime(
        self,
        runtime_name: str = "dependency_runtime",
        executed: bool = False,
        failure: str | None = None,
    ) -> None:
        execution = {
            "runtime_name": runtime_name,
            "executed": bool(executed),
            "timestamp": _timestamp(),
        }
        if failure:
            execution["failure"] = failure
            self.activation_failures.append(execution)
        else:
            self.activation_executions.append(execution)
        self._event("dependency_runtime_exited", **execution)

    def skip_report(
        self,
        requested_tool: str,
        activation_attempted: bool,
        activation_blocked: bool,
        block_reason: str,
        blocking_module: str,
        blocking_condition: str,
    ) -> dict[str, Any]:
        report = {
            "report_type": SKIP_REPORT_KEY,
            "requested_tool": requested_tool,
            "activation_attempted": bool(activation_attempted),
            "activation_blocked": bool(activation_blocked),
            "block_reason": block_reason,
            "blocking_module": blocking_module,
            "blocking_condition": blocking_condition,
            "timestamp": _timestamp(),
        }
        self.skip_reasons.append(report)
        self._event("activation_skipped", **report)
        return report

    def assert_requested_when_concepts_exist(self) -> dict[str, Any] | None:
        if self.concepts_detected and not self.activation_requests:
            warning = {
                "warning": MISSING_WARNING,
                "concepts_detected": list(self.concepts_detected),
                "activation_request_count": 0,
                "timestamp": _timestamp(),
            }
            self.activation_failures.append(warning)
            self._event("activation_missing", **warning)
            return warning
        return None

    def report(self) -> dict[str, Any]:
        request_count = len(self.activation_requests)
        execution_count = len(self.activation_executions)
        failure_count = len(self.activation_failures)
        attempted_count = request_count + len(self.skip_reasons)
        success_rate = (
            round(execution_count / attempted_count, 4)
            if attempted_count
            else 0.0
        )
        return {
            "report_type": TRACE_REPORT_KEY,
            "concepts_detected": list(self.concepts_detected),
            "dependency_candidates": list(self.dependency_candidates),
            "activation_requests": list(self.activation_requests),
            "activation_approvals": list(self.activation_approvals),
            "activation_executions": list(self.activation_executions),
            "activation_failures": list(self.activation_failures),
            "skip_reasons": list(self.skip_reasons),
            "activation_request_count": request_count,
            "activation_approval_count": len(self.activation_approvals),
            "activation_execution_count": execution_count,
            "activation_failure_count": failure_count,
            "activation_success_rate": success_rate,
            "events": list(self.events),
        }

    def _event(self, event_type: str, **payload: Any) -> None:
        self.events.append({
            "event_type": event_type,
            "timestamp": _timestamp(),
            **payload,
        })


def build_trace_from_context(context: dict[str, Any] | None) -> DependencyActivationTrace:
    trace = DependencyActivationTrace()
    if isinstance(context, dict):
        existing = context.get(TRACE_REPORT_KEY, {})
        if isinstance(existing, dict):
            trace.concepts_detected = list(existing.get("concepts_detected", []) or [])
            trace.dependency_candidates = list(
                existing.get("dependency_candidates", []) or []
            )
            trace.activation_requests = list(
                existing.get("activation_requests", []) or []
            )
            trace.activation_approvals = list(
                existing.get("activation_approvals", []) or []
            )
            trace.activation_executions = list(
                existing.get("activation_executions", []) or []
            )
            trace.activation_failures = list(
                existing.get("activation_failures", []) or []
            )
            trace.skip_reasons = list(existing.get("skip_reasons", []) or [])
            trace.events = list(existing.get("events", []) or [])
    return trace


def _normalize(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _timestamp() -> str:
    return str(datetime.utcnow())


__all__ = [
    "DependencyActivationTrace",
    "MISSING_WARNING",
    "SKIP_REPORT_KEY",
    "TRACE_REPORT_KEY",
    "build_trace_from_context",
]
