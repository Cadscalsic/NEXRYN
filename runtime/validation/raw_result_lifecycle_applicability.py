"""Raw Result lifecycle applicability decisions.

This module decides whether a canonical Raw Result obligation existed. It does
not create Raw Results, issue identities, or repair envelopes.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime
from typing import Any, Mapping


APPLICABLE = "RAW_RESULT_APPLICABLE"
NOT_APPLICABLE = "RAW_RESULT_NOT_APPLICABLE"
UNDETERMINED = "RAW_RESULT_APPLICABILITY_UNDETERMINED"


class RawResultLifecycleApplicabilityEvaluator:
    """Evaluate Raw Result applicability from current-run producer evidence."""

    schema_version = "1.0"
    source_stage = "raw_result_lifecycle_applicability_evaluator"

    RAW_RESULT_STATES = {
        "RAW_RESULT_CAPTURED",
        "RAW_RESULT_EMPTY_VALID_OUTPUT_CAPTURED",
        "RAW_RESULT_ARTIFACT_MISSING",
        "RAW_RESULT_ENVELOPE_INCOMPLETE",
    }
    PRE_OBLIGATION_STATES = {
        "DEFERRED_BY_BUDGET",
        "REJECTED_BY_BUDGET",
        "DEPTH_ENTRY_BLOCKED_BY_BUDGET",
        "BRANCH_PRUNED_BY_BUDGET",
        "BOUNDED_REASONING_LIMIT_REACHED",
        "CANCELLED_BEFORE_PRODUCER_ACTIVATION",
        "NOT_STARTED",
        "NOT_SCHEDULED",
        "NOT_PRODUCED",
    }
    MISSING_IDS = {
        "",
        "NOT_ISSUED",
        "NOT AVAILABLE",
        "NOT_AVAILABLE",
        "NOT_PRODUCED",
        "RAW_VALIDATION_RESULT_ID_NOT_ISSUED",
        "RAW_RESULT_ID_NOT_ISSUED",
    }

    def evaluate(
        self,
        *,
        run_id: str | None,
        execution_plan_id: str | None,
        task_id: str | None = None,
        validation_task_execution_report: Mapping[str, Any] | None = None,
        validation_scheduling_report: Mapping[str, Any] | None = None,
        route_lifecycle_records: list[dict[str, Any]] | None = None,
        reasoning_depth_lifecycle_records: list[dict[str, Any]] | None = None,
        existing_decisions: list[Mapping[str, Any]] | None = None,
        source_timestamp: str | None = None,
    ) -> dict[str, Any]:
        source_timestamp = source_timestamp or self._now()
        run_id = self._identity(run_id, "RUN_ID_UNBOUND")
        execution_plan_id = self._identity(
            execution_plan_id,
            "EXECUTION_PLAN_ID_UNBOUND",
        )
        decisions = [
            deepcopy(dict(decision))
            for decision in existing_decisions or []
            if isinstance(decision, Mapping)
        ]
        transitions = [
            self._transition(
                "RAW_RESULT_APPLICABILITY_EVALUATION_STARTED",
                1,
                run_id,
                execution_plan_id,
                task_id,
                None,
                source_timestamp,
            )
        ]

        route_records = [
            row for row in (route_lifecycle_records or [])
            if isinstance(row, Mapping)
        ]
        depth_records = [
            row for row in (reasoning_depth_lifecycle_records or [])
            if isinstance(row, Mapping)
        ]
        validation_decision = self._validation_decision(
            run_id=run_id,
            execution_plan_id=execution_plan_id,
            task_id=task_id,
            validation_task_execution_report=validation_task_execution_report,
            validation_scheduling_report=validation_scheduling_report,
            source_timestamp=source_timestamp,
        )
        decisions.append(validation_decision)
        transitions.append(
            self._transition(
                "RAW_RESULT_PRODUCER_OBLIGATION_EVALUATED",
                2,
                run_id,
                execution_plan_id,
                task_id,
                validation_decision.get("producer_operation_id"),
                source_timestamp,
            )
        )

        for index, row in enumerate(route_records, start=1):
            state = str(row.get("state") or row.get("lifecycle_state") or "")
            if state in {"DEFERRED_BY_BUDGET", "REJECTED_BY_BUDGET"}:
                decisions.append(self._pre_obligation_decision(
                    run_id=run_id,
                    execution_plan_id=execution_plan_id,
                    task_id=row.get("task_id") or task_id,
                    route_id=row.get("route_id"),
                    producer_operation_id=f"route_pre_obligation_{index}",
                    producer_type="route",
                    reason=state,
                    terminal_state=state,
                    source_timestamp=source_timestamp,
                ))
        for index, row in enumerate(depth_records, start=1):
            state = str(row.get("state") or row.get("event") or "")
            if state in {
                "DEPTH_ENTRY_BLOCKED_BY_BUDGET",
                "BRANCH_PRUNED_BY_BUDGET",
                "BOUNDED_REASONING_LIMIT_REACHED",
            }:
                decisions.append(self._pre_obligation_decision(
                    run_id=run_id,
                    execution_plan_id=execution_plan_id,
                    task_id=row.get("task_id") or task_id,
                    route_id=row.get("route_id"),
                    reasoning_context_id=row.get("reasoning_context_id"),
                    producer_operation_id=f"reasoning_pre_obligation_{index}",
                    producer_type="reasoning_branch",
                    reason=state,
                    terminal_state=state,
                    source_timestamp=source_timestamp,
                ))

        report = self._aggregate(
            decisions,
            run_id,
            execution_plan_id,
            task_id,
            source_timestamp,
        )
        transitions.append(
            self._transition(
                "RAW_RESULT_APPLICABILITY_FINALIZED",
                3,
                run_id,
                execution_plan_id,
                task_id,
                None,
                source_timestamp,
            )
        )
        report["lifecycle_transitions"] = transitions
        report["raw_result_applicability_lifecycle_transitions"] = transitions
        report["applicability_decision_fingerprint"] = self._stable_id(
            "raw_result_applicability_fingerprint",
            {
                "run_id": run_id,
                "execution_plan_id": execution_plan_id,
                "decisions": decisions,
                "state": report.get("raw_result_applicability_state"),
            },
        )
        return report

    def bind_to_canonical_report(self, report: Mapping[str, Any] | None) -> dict[str, Any]:
        bound = deepcopy(dict(report or {}))
        if not bound:
            return {}
        transitions = list(bound.get("lifecycle_transitions") or [])
        transitions.append(
            self._transition(
                "RAW_RESULT_APPLICABILITY_BOUND_TO_CANONICAL_REPORT",
                len(transitions) + 1,
                bound.get("run_id"),
                bound.get("execution_plan_id"),
                bound.get("task_id"),
                None,
                self._now(),
            )
        )
        bound["lifecycle_transitions"] = transitions
        bound["raw_result_applicability_lifecycle_transitions"] = transitions
        bound["canonical_binding_state"] = "RAW_RESULT_APPLICABILITY_BOUND_TO_CANONICAL_REPORT"
        return bound

    def _validation_decision(
        self,
        *,
        run_id: str,
        execution_plan_id: str,
        task_id: str | None,
        validation_task_execution_report: Mapping[str, Any] | None,
        validation_scheduling_report: Mapping[str, Any] | None,
        source_timestamp: str,
    ) -> dict[str, Any]:
        report = validation_task_execution_report if isinstance(validation_task_execution_report, Mapping) else {}
        schedule = validation_scheduling_report if isinstance(validation_scheduling_report, Mapping) else {}
        envelope = self._first_dict(report, "RAW_VALIDATION_RESULT_ENVELOPE", "raw_validation_result_envelope")
        execution_state = self._identity(
            envelope.get("raw_validation_result_state")
            or report.get("execution_state")
            or report.get("validation_execution_lifecycle_state")
            or schedule.get("execution_state")
            or "NOT_PRODUCED"
        )
        report_run_id = report.get("run_id") or envelope.get("run_id")
        report_plan_id = report.get("execution_plan_id") or envelope.get("execution_plan_id")
        current_run_lineage = report_run_id == run_id
        current_plan_lineage = (
            report_plan_id in (None, "", execution_plan_id)
            if current_run_lineage
            else False
        )
        has_current_run_conflict = (
            report_run_id not in (None, "", run_id)
            or (current_run_lineage and report_plan_id not in (None, "", execution_plan_id))
        )
        execution_admission_state = self._identity(
            report.get("execution_admission_state")
            or report.get("validation_execution_admission_state")
            or "NOT_EVALUATED"
        )
        execution_started = self._bool(report.get("execution_started")) or self._bool(
            report.get("execution_invoked")
        )
        raw_result_id = (
            envelope.get("raw_validation_result_id")
            or report.get("raw_validation_result_id")
            or report.get("raw_result_id")
        )
        raw_result_present = (
            current_run_lineage
            and current_plan_lineage
            and
            execution_state in {
                "RAW_RESULT_CAPTURED",
                "RAW_RESULT_EMPTY_VALID_OUTPUT_CAPTURED",
            }
            and self._identity(raw_result_id).upper() not in self.MISSING_IDS
        )
        raw_result_missing = execution_state in self.RAW_RESULT_STATES and not raw_result_present
        admitted = execution_admission_state == "ADMITTED"
        boundary_signal = (
            execution_started
            or execution_state in {"EXECUTION_FAILED", "EXECUTION_COMPLETED_RESULT_CAPTURE_PENDING"}
        )
        previous_or_unbound_raw_artifact = (
            execution_state in self.RAW_RESULT_STATES
            and not current_run_lineage
            and not self._bool(report.get("current_run_producer_activation"))
        )
        obligation_boundary = admitted and boundary_signal and current_run_lineage and current_plan_lineage
        lineage_uncertain_after_start = admitted and boundary_signal and (
            not current_run_lineage or not current_plan_lineage
        ) and not previous_or_unbound_raw_artifact
        producer_exists = (
            bool(report)
            and execution_state not in {"NOT_PRODUCED", "NOT_AVAILABLE", "NOT PRODUCED"}
        )
        if previous_or_unbound_raw_artifact:
            applicability_state = NOT_APPLICABLE
            reason = "PREVIOUS_OR_UNBOUND_RAW_RESULT_ARTIFACT_IGNORED_NO_CURRENT_RUN_PRODUCER"
            raw_required = False
        elif has_current_run_conflict or lineage_uncertain_after_start:
            applicability_state = UNDETERMINED
            reason = "CURRENT_RUN_OR_EXECUTION_PLAN_PROVENANCE_CONFLICT"
            raw_required = False
        elif obligation_boundary:
            applicability_state = APPLICABLE
            reason = "ADMITTED_VALIDATION_EXECUTION_CROSSED_RAW_RESULT_OBLIGATION_BOUNDARY"
            raw_required = True
        elif producer_exists and execution_state in self.PRE_OBLIGATION_STATES:
            applicability_state = NOT_APPLICABLE
            reason = f"STOPPED_BEFORE_RAW_RESULT_OBLIGATION:{execution_state}"
            raw_required = False
        else:
            applicability_state = NOT_APPLICABLE
            reason = "NO_QUALIFYING_RAW_RESULT_PRODUCER_OBLIGATION_IN_CURRENT_RUN"
            raw_required = False
        return {
            "applicability_decision_id": self._stable_id(
                "raw_result_applicability_decision",
                {
                    "run_id": run_id,
                    "execution_plan_id": execution_plan_id,
                    "task_id": task_id,
                    "producer_type": "scheduled_validation_execution",
                    "terminal_state": execution_state,
                },
            ),
            "run_id": run_id,
            "execution_plan_id": execution_plan_id,
            "task_id": task_id,
            "producer_operation_id": report.get("execution_id") or report.get("validation_execution_id"),
            "validation_attempt_id": report.get("validation_attempt_id"),
            "producer_type": "scheduled_validation_execution",
            "producer_contract": "VALIDATION_TASK_EXECUTION_PIPELINE_RAW_RESULT_CAPTURE",
            "execution_admission_state": execution_admission_state,
            "execution_started": execution_started,
            "obligation_boundary_reached": obligation_boundary,
            "terminal_state": execution_state,
            "raw_result_required": raw_required,
            "raw_result_present": raw_result_present,
            "raw_result_missing": raw_result_missing if raw_required else False,
            "applicability_state": applicability_state,
            "applicability_reason": reason,
            "source_stage": self.source_stage,
            "source_timestamp": source_timestamp,
            "is_current_run": not has_current_run_conflict,
        }

    def _pre_obligation_decision(self, **kwargs: Any) -> dict[str, Any]:
        run_id = self._identity(kwargs.get("run_id"))
        execution_plan_id = self._identity(kwargs.get("execution_plan_id"))
        producer_operation_id = kwargs.get("producer_operation_id")
        return {
            "applicability_decision_id": self._stable_id(
                "raw_result_applicability_decision",
                {
                    "run_id": run_id,
                    "execution_plan_id": execution_plan_id,
                    "producer_operation_id": producer_operation_id,
                    "terminal_state": kwargs.get("terminal_state"),
                },
            ),
            "run_id": run_id,
            "execution_plan_id": execution_plan_id,
            "task_id": kwargs.get("task_id"),
            "route_id": kwargs.get("route_id"),
            "reasoning_context_id": kwargs.get("reasoning_context_id"),
            "producer_operation_id": producer_operation_id,
            "producer_type": kwargs.get("producer_type"),
            "producer_contract": "NO_RAW_RESULT_CONTRACT_BEFORE_PRODUCER_ACTIVATION",
            "execution_admission_state": kwargs.get("terminal_state"),
            "execution_started": False,
            "obligation_boundary_reached": False,
            "terminal_state": kwargs.get("terminal_state"),
            "raw_result_required": False,
            "raw_result_present": False,
            "raw_result_missing": False,
            "applicability_state": NOT_APPLICABLE,
            "applicability_reason": f"PRE_OBLIGATION_STOP:{kwargs.get('reason')}",
            "source_stage": self.source_stage,
            "source_timestamp": kwargs.get("source_timestamp"),
            "is_current_run": True,
        }

    def _aggregate(
        self,
        decisions: list[dict[str, Any]],
        run_id: str,
        execution_plan_id: str,
        task_id: str | None,
        source_timestamp: str,
    ) -> dict[str, Any]:
        applicable = [d for d in decisions if d.get("applicability_state") == APPLICABLE]
        non_applicable = [d for d in decisions if d.get("applicability_state") == NOT_APPLICABLE]
        undetermined = [d for d in decisions if d.get("applicability_state") == UNDETERMINED]
        required = [d for d in decisions if d.get("raw_result_required") is True]
        present = [d for d in applicable if d.get("raw_result_present") is True]
        missing = [d for d in applicable if d.get("raw_result_missing") is True]
        if applicable:
            state = APPLICABLE
            reason = "ONE_OR_MORE_RAW_RESULT_PRODUCER_OBLIGATIONS_EXIST"
            lifecycle = (
                "RAW_RESULT_LIFECYCLE_EVALUATED"
                if not missing
                else "RAW_RESULT_LIFECYCLE_APPLICABLE_RESULT_MISSING"
            )
        elif undetermined:
            state = UNDETERMINED
            reason = "RAW_RESULT_PRODUCER_PROVENANCE_UNDETERMINED"
            lifecycle = "NOT_EVALUATED_APPLICABILITY_UNDETERMINED"
        else:
            state = NOT_APPLICABLE
            reason = "NO_QUALIFYING_RAW_RESULT_PRODUCER_OBLIGATION_IN_CURRENT_RUN"
            lifecycle = "NOT_EVALUATED_NOT_APPLICABLE"
        return {
            "raw_result_applicability_schema_version": self.schema_version,
            "raw_result_applicability_state": state,
            "raw_result_applicability_reason": reason,
            "raw_result_lifecycle_completeness_state": lifecycle,
            "run_id": run_id,
            "execution_plan_id": execution_plan_id,
            "task_id": task_id,
            "is_current_run": True,
            "current_run_binding_state": "CURRENT_RUN_BOUND",
            "authoritative_execution_plan_id": execution_plan_id,
            "applicability_evaluation_source": self.source_stage,
            "source_stage": self.source_stage,
            "source_timestamp": source_timestamp,
            "raw_result_applicability_finalized": True,
            "operation_applicability_decisions": decisions,
            "raw_result_producer_obligation_count": len(required),
            "qualifying_producer_count": len(applicable),
            "applicable_operation_count": len(applicable),
            "non_applicable_operation_count": len(non_applicable),
            "undetermined_operation_count": len(undetermined),
            "raw_result_required_count": len(required),
            "applicable_raw_result_present_count": len(present),
            "applicable_raw_result_missing_count": len(missing),
            "pre_obligation_deferred_count": len([
                d for d in non_applicable
                if str(d.get("terminal_state")) == "DEFERRED_BY_BUDGET"
            ]),
            "pre_obligation_blocked_count": len([
                d for d in non_applicable
                if str(d.get("terminal_state")) in {
                    "REJECTED_BY_BUDGET",
                    "DEPTH_ENTRY_BLOCKED_BY_BUDGET",
                    "BRANCH_PRUNED_BY_BUDGET",
                    "BOUNDED_REASONING_LIMIT_REACHED",
                }
            ]),
        }

    def _transition(
        self,
        name: str,
        sequence_index: int,
        run_id: str | None,
        execution_plan_id: str | None,
        task_id: str | None,
        producer_operation_id: str | None,
        source_timestamp: str,
    ) -> dict[str, Any]:
        row = {
            "transition_name": name,
            "sequence_index": sequence_index,
            "run_id": self._identity(run_id),
            "execution_plan_id": self._identity(execution_plan_id),
            "task_id": task_id,
            "source_stage": self.source_stage,
            "source_timestamp": source_timestamp,
            "is_current_run": True,
        }
        if producer_operation_id:
            row["producer_operation_id"] = producer_operation_id
        return row

    def _now(self) -> str:
        return datetime.utcnow().isoformat()

    def _first_dict(self, mapping: Mapping[str, Any], *keys: str) -> dict[str, Any]:
        for key in keys:
            value = mapping.get(key)
            if isinstance(value, Mapping):
                return dict(value)
        return {}

    def _identity(self, value: Any, default: str = "") -> str:
        text = str(value or "").strip()
        return text or default

    def _bool(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().upper() in {"TRUE", "YES", "1"}
        return bool(value)

    def _stable_id(self, prefix: str, payload: Any) -> str:
        text = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


raw_result_lifecycle_applicability_evaluator = (
    RawResultLifecycleApplicabilityEvaluator()
)


__all__ = [
    "APPLICABLE",
    "NOT_APPLICABLE",
    "UNDETERMINED",
    "RawResultLifecycleApplicabilityEvaluator",
    "raw_result_lifecycle_applicability_evaluator",
]
