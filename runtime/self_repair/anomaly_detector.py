"""Operational anomaly detection for safe self-repair."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


SEVERITY_LEVELS = {
    "INFO",
    "MINOR",
    "MODERATE",
    "CRITICAL",
}


@dataclass
class Anomaly:
    anomaly_type: str
    severity: str
    evidence: dict[str, Any] = field(default_factory=dict)
    recommended_action: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class AnomalyDetector:
    """Detect runtime operation inconsistencies without reasoning expansion."""

    def detect(
        self,
        runtime_context: Mapping[str, Any] | None,
    ) -> list[Anomaly]:
        context = runtime_context if isinstance(runtime_context, Mapping) else {}
        anomalies: list[Anomaly] = []
        evaluation = self._first_mapping(
            context,
            "evaluation_result",
            "evaluation_report",
            "success_semantics_report",
        )
        shutdown = self._mapping(context.get("post_success_shutdown"))
        governance = self._first_mapping(
            context,
            "governance_report",
            "cognitive_governance_report",
            "governance_cache_report",
        )
        learning = self._first_mapping(
            context,
            "learning_saturation_report",
            "LEARNING_SATURATION_REPORT",
        )
        localization = self._first_mapping(
            context,
            "transformation_localization",
            "transformation_report",
        )
        execution = self._first_mapping(
            context,
            "execution_report",
            "execution_integrity_report",
            "transformation_report",
        )

        self._detect_termination_desync(context, evaluation, shutdown, anomalies)
        self._detect_success_conflict(context, evaluation, anomalies)
        self._detect_cache_reuse_failure(context, governance, anomalies)
        self._detect_learning_saturation_conflict(context, learning, governance, anomalies)
        self._detect_localization_state_conflict(evaluation, localization, anomalies)
        self._detect_execution_integrity_conflict(execution, anomalies)
        self._detect_identity_state_conflict(context, anomalies)
        self._detect_governance_loop(context, anomalies)
        return anomalies

    def _detect_termination_desync(self, context, evaluation, shutdown, anomalies):
        episode_completed = (
            context.get("episode_completed") is True
            or evaluation.get("episode_completed") is True
            or shutdown.get("episode_completed") is True
        )
        failure_detected = evaluation.get("failure_detected") is True
        retry_allowed = evaluation.get("retry_allowed") is True
        shutdown_mode = context.get("shutdown_mode") or shutdown.get("mode")
        reasoning_report = self._mapping(context.get("reasoning_report"))
        continued = (
            reasoning_report.get("reasoning_invoked") is True
            or context.get("active_routes", 0)
            or context.get("background_loops_active") is True
        )
        if episode_completed and not failure_detected and not retry_allowed and (
            shutdown_mode != "fast" or continued
        ):
            anomalies.append(Anomaly(
                anomaly_type="TERMINATION_DESYNC",
                severity="MINOR" if not continued else "MODERATE",
                evidence={
                    "episode_completed": episode_completed,
                    "failure_detected": failure_detected,
                    "retry_allowed": retry_allowed,
                    "shutdown_mode": shutdown_mode,
                    "continued_cognition": bool(continued),
                },
                recommended_action="SET_SHUTDOWN_FAST",
            ))

    def _detect_success_conflict(self, context, evaluation, anomalies):
        states = [
            evaluation.get("success_state"),
            context.get("success_state"),
            self._mapping(context.get("finalization_report")).get("success_state"),
        ]
        normalized = {state for state in states if state}
        if len(normalized) > 1:
            anomalies.append(Anomaly(
                anomaly_type="SUCCESS_SEMANTICS_CONFLICT",
                severity="MODERATE",
                evidence={"success_states": sorted(normalized)},
                recommended_action="SYNC_SUCCESS_FLAGS",
            ))

    def _detect_cache_reuse_failure(self, context, governance, anomalies):
        locked_truth = (
            governance.get("final_commit_state") == "LOCKED_TRUTH_PRESERVED"
            or governance.get("locked_truth_preserved") is True
            or self._mapping(context.get("truth_commit_result")).get(
                "final_commit_state"
            ) == "LOCKED_TRUTH_PRESERVED"
        )
        cache_hits = int(self._number(
            self._mapping(context.get("performance_report")).get("cache_hits")
            or context.get("cache_hits")
            or 0
        ))
        if locked_truth and cache_hits == 0:
            anomalies.append(Anomaly(
                anomaly_type="CACHE_REUSE_FAILURE",
                severity="MODERATE",
                evidence={
                    "locked_truth": True,
                    "cache_hits": cache_hits,
                },
                recommended_action="INVALIDATE_TEMP_CACHE",
            ))

    def _detect_learning_saturation_conflict(self, context, learning, governance, anomalies):
        saturated = (
            learning.get("evidence_saturated") is True
            or context.get("evidence_saturated") is True
        )
        next_step = (
            learning.get("recommended_next_step")
            or context.get("recommended_next_step")
        )
        locked_truth = (
            governance.get("final_commit_state") == "LOCKED_TRUTH_PRESERVED"
            or self._mapping(context.get("truth_commit_result")).get(
                "final_commit_state"
            ) == "LOCKED_TRUTH_PRESERVED"
        )
        if saturated and next_step == "continue_adaptive_training":
            anomalies.append(Anomaly(
                anomaly_type="LEARNING_SATURATION_CONFLICT",
                severity="MINOR" if locked_truth else "MODERATE",
                evidence={
                    "evidence_saturated": saturated,
                    "recommended_next_step": next_step,
                    "locked_truth": locked_truth,
                },
                recommended_action="SYNC_RECOMMENDED_NEXT_STEP",
            ))

    def _detect_localization_state_conflict(self, evaluation, localization, anomalies):
        exact_success = (
            evaluation.get("exact_success") is True
            or evaluation.get("success_state") in {"EXACT_SUCCESS", "SUCCESS"}
        )
        localization_ready = localization.get("localization_ready")
        if exact_success and localization_ready is False:
            anomalies.append(Anomaly(
                anomaly_type="LOCALIZATION_STATE_CONFLICT",
                severity="MODERATE",
                evidence={
                    "exact_success": exact_success,
                    "localization_ready": localization_ready,
                },
                recommended_action="REQUEST_GOVERNANCE_REVIEW",
            ))

    def _detect_execution_integrity_conflict(self, execution, anomalies):
        execution_authorized = execution.get("execution_authorized") is True
        executed_steps = int(self._number(
            execution.get("executed_steps")
            or execution.get("step_count")
            or len(execution.get("execution_trace", []) or [])
        ))
        planned_ops = execution.get("planned_ops")
        executed_ops = execution.get("executed_ops")
        if execution_authorized and executed_steps == 0:
            anomalies.append(Anomaly(
                anomaly_type="EXECUTION_INTEGRITY_CONFLICT",
                severity="CRITICAL",
                evidence={
                    "execution_authorized": execution_authorized,
                    "executed_steps": executed_steps,
                },
                recommended_action="REQUEST_GOVERNANCE_REVIEW",
            ))
        if planned_ops is not None and executed_ops is not None and planned_ops != executed_ops:
            anomalies.append(Anomaly(
                anomaly_type="EXECUTION_INTEGRITY_CONFLICT",
                severity="CRITICAL",
                evidence={
                    "planned_ops": planned_ops,
                    "executed_ops": executed_ops,
                },
                recommended_action="REQUEST_GOVERNANCE_REVIEW",
            ))

    def _detect_identity_state_conflict(self, context, anomalies):
        identity_state = (
            context.get("identity_runtime_state")
            or self._mapping(context.get("identity_governance_report")).get(
                "identity_runtime_state"
            )
        )
        continuity = (
            context.get("identity_continuity")
            or self._mapping(context.get("identity_governance_report")).get(
                "identity_continuity"
            )
        )
        if identity_state in {"unstable", "UNSTABLE", "conflict"} and continuity in {
            True,
            "preserved",
            "stable",
        }:
            anomalies.append(Anomaly(
                anomaly_type="IDENTITY_STATE_CONFLICT",
                severity="CRITICAL",
                evidence={
                    "identity_runtime_state": identity_state,
                    "identity_continuity": continuity,
                },
                recommended_action="REQUEST_GOVERNANCE_REVIEW",
            ))

    def _detect_governance_loop(self, context, anomalies):
        report = self._mapping(context.get("META_SUPERVISOR_REPORT"))
        if (
            report.get("selected_action") == "REUSE_LOCKED_TRUTH"
            and context.get("truth_revalidation_count", 0)
            and int(self._number(context.get("truth_revalidation_count"))) > 1
        ):
            anomalies.append(Anomaly(
                anomaly_type="GOVERNANCE_REVALIDATION_LOOP",
                severity="MODERATE",
                evidence={
                    "selected_action": report.get("selected_action"),
                    "truth_revalidation_count": context.get("truth_revalidation_count"),
                },
                recommended_action="REQUEST_GOVERNANCE_REVIEW",
            ))

    def _first_mapping(self, context, *keys):
        for key in keys:
            value = self._mapping(context.get(key))
            if value:
                return value
        return {}

    def _mapping(self, value):
        return value if isinstance(value, Mapping) else {}

    def _number(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


anomaly_detector = AnomalyDetector()


__all__ = [
    "Anomaly",
    "AnomalyDetector",
    "SEVERITY_LEVELS",
    "anomaly_detector",
]
