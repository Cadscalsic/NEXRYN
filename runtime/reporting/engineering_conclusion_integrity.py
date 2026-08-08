"""Authoritative integrity contract for engineering conclusions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


_MISSING_VALUES = {None, "", "Not Available", "NOT_AVAILABLE", "NOT_PRODUCED"}
_SCHEMA_VERSION = "1.0"
_MISSING_STABLE_FIELD = "__MISSING_STABLE_FIELD__"
_FINALIZED_TRANSITION = "ENGINEERING_CONCLUSION_FINALIZED"
_EVALUATED_TRANSITION = "ENGINEERING_CONCLUSION_INTEGRITY_EVALUATED"
_BOUND_TRANSITION = "ENGINEERING_CONCLUSION_BOUND_TO_CANONICAL_REPORT"
_PERSISTENCE_APPLICABILITY_EVALUATED_TRANSITION = (
    "ENGINEERING_CONCLUSION_PERSISTENCE_APPLICABILITY_EVALUATED"
)
_PERSISTED_TRANSITION = "ENGINEERING_CONCLUSION_PERSISTED"
_READBACK_TRANSITION = "ENGINEERING_CONCLUSION_PERSISTENCE_READBACK_COMPLETED"
_PERSISTENCE_INTEGRITY_EVALUATED_TRANSITION = (
    "ENGINEERING_CONCLUSION_PERSISTENCE_INTEGRITY_EVALUATED"
)
_PERSISTENCE_WRITE_STARTED_TRANSITION = (
    "ENGINEERING_CONCLUSION_PERSISTENCE_WRITE_STARTED"
)
_PERSISTENCE_READBACK_STARTED_TRANSITION = (
    "ENGINEERING_CONCLUSION_PERSISTENCE_READBACK_STARTED"
)
_EMISSION_INTEGRITY_EVALUATED_TRANSITION = (
    "ENGINEERING_CONCLUSION_EMISSION_INTEGRITY_EVALUATED"
)
_PERSISTENCE_EMISSION_PARITY_EVALUATED_TRANSITION = (
    "ENGINEERING_CONCLUSION_PERSISTENCE_EMISSION_PARITY_EVALUATED"
)
_HUMAN_REPORT_PROJECTED_TRANSITION = "ENGINEERING_CONCLUSION_HUMAN_REPORT_PROJECTED"
_LIFECYCLE_ORDER = [
    _FINALIZED_TRANSITION,
    _EVALUATED_TRANSITION,
    _BOUND_TRANSITION,
]
STABLE_SEMANTIC_FIELDS = [
    "schema_version",
    "engineering_conclusion_state",
    "conclusion_state",
    "engineering_conclusion_integrity_state",
    "engineering_conclusion_integrity_reason",
    "failure_reason",
    "root_cause",
    "recommended_action",
    "responsible_area",
    "next_gate",
    "conclusion_source_stage",
    "conclusion_source",
    "conclusion_evaluation_source",
    "conclusion_run_id",
    "authoritative_run_id",
    "authoritative_execution_plan_id",
    "conclusion_task_id",
    "canonical_raw_result_id",
    "conclusion_fingerprint",
]
FINGERPRINT_PAYLOAD_FIELDS = [
    field for field in STABLE_SEMANTIC_FIELDS
    if field != "conclusion_fingerprint"
]


def _first_meaningful(*values: Any, default: Any = None) -> Any:
    for value in values:
        if value in ({}, []):
            continue
        if value is None:
            continue
        if isinstance(value, str) and value in _MISSING_VALUES:
            continue
        return value
    return default


def _first_dict(mapping: dict[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _stable_fingerprint(payload: Any) -> str:
    encoded = json.dumps(
        _fingerprint_normalized(payload),
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _fingerprint_normalized(value: Any) -> Any:
    if isinstance(value, str):
        return " ".join(value.strip().split())
    if isinstance(value, list):
        return [_fingerprint_normalized(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _fingerprint_normalized(item)
            for key, item in value.items()
        }
    return value


def _transition(
    conclusion: dict[str, Any],
    transition_name: str,
    *,
    source_stage: str,
    source_timestamp: Any,
) -> dict[str, Any]:
    transitions = conclusion.get("engineering_conclusion_lifecycle_transitions")
    transitions = transitions if isinstance(transitions, list) else []
    return {
        "transition_name": transition_name,
        "state": transition_name,
        "sequence_index": len(transitions) + 1,
        "conclusion_id": conclusion.get("engineering_conclusion_id"),
        "run_id": conclusion.get("authoritative_run_id")
        or conclusion.get("conclusion_run_id"),
        "execution_plan_id": conclusion.get("authoritative_execution_plan_id"),
        "task_id": conclusion.get("conclusion_task_id"),
        "source_stage": source_stage,
        "source_timestamp": source_timestamp,
        "is_current_run": conclusion.get("conclusion_is_current") is not False,
    }


def _append_transition(
    conclusion: dict[str, Any],
    transition_name: str,
    *,
    source_stage: str,
    source_timestamp: Any,
) -> None:
    transitions = conclusion.setdefault(
        "engineering_conclusion_lifecycle_transitions",
        [],
    )
    if not isinstance(transitions, list):
        transitions = []
        conclusion["engineering_conclusion_lifecycle_transitions"] = transitions
    if any(
        isinstance(row, dict) and row.get("transition_name") == transition_name
        for row in transitions
    ):
        return
    transitions.append(
        _transition(
            conclusion,
            transition_name,
            source_stage=source_stage,
            source_timestamp=source_timestamp,
        )
    )


def _raw_stable_value(conclusion: dict[str, Any], field: str) -> Any:
    if field in conclusion:
        return conclusion.get(field)
    return _MISSING_STABLE_FIELD


def _canonical_payload(
    conclusion: dict[str, Any],
    *,
    include_fingerprint: bool = True,
    preserve_missing: bool = False,
) -> dict[str, Any]:
    fields = STABLE_SEMANTIC_FIELDS if include_fingerprint else FINGERPRINT_PAYLOAD_FIELDS
    payload: dict[str, Any] = {}
    for field in fields:
        value = (
            _raw_stable_value(conclusion, field)
            if preserve_missing
            else conclusion.get(field)
        )
        if (
            field == "canonical_raw_result_id"
            and value == _MISSING_STABLE_FIELD
        ):
            value = None
        payload[field] = value
    return payload


def _recomputed_payload_fingerprint(payload: dict[str, Any]) -> str:
    return _stable_fingerprint(
        _canonical_payload(
            payload,
            include_fingerprint=False,
            preserve_missing=True,
        )
    )


def _infer_execution_plan_id(report_state: dict[str, Any]) -> Any:
    canonical_plan = _first_dict(
        report_state,
        "CANONICAL_EXECUTION_PLAN",
        "canonical_execution_plan",
        "CANONICAL_EXECUTION_PLAN_REPORT",
        "canonical_execution_plan_report",
    )
    legacy_plan = _first_dict(
        report_state,
        "EXECUTION_PLAN_REPORT",
        "execution_plan_report",
    )
    validation = _first_dict(
        report_state,
        "VALIDATION_TASK_EXECUTION_REPORT",
        "validation_task_execution_report",
    )
    raw_applicability = _first_dict(
        report_state,
        "RAW_RESULT_APPLICABILITY_REPORT",
        "raw_result_applicability_report",
    )
    audit = _first_dict(
        report_state,
        "ACTIVE_RUNTIME_REACHABILITY_AUDIT",
        "active_runtime_reachability_audit",
    )
    return _first_meaningful(
        canonical_plan.get("execution_plan_id"),
        raw_applicability.get("authoritative_execution_plan_id"),
        audit.get("execution_plan_id"),
        validation.get("execution_plan_id"),
        legacy_plan.get("execution_plan_id"),
        report_state.get("execution_plan_id"),
        default="EXECUTION_PLAN_ID_UNBOUND",
    )


class EngineeringConclusionIntegrityEvaluator:
    """Normalizes and evaluates the one authoritative engineering conclusion."""

    def create_authoritative_conclusion(
        self,
        report_state: dict[str, Any],
        *,
        runtime_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = report_state if isinstance(report_state, dict) else {}
        metadata = runtime_metadata if isinstance(runtime_metadata, dict) else {}
        raw_applicability = _first_dict(
            state,
            "RAW_RESULT_APPLICABILITY_REPORT",
            "raw_result_applicability_report",
        )
        validation = _first_dict(
            state,
            "VALIDATION_TASK_EXECUTION_REPORT",
            "validation_task_execution_report",
        )
        evaluation = _first_dict(
            state,
            "VALIDATION_EVIDENCE_EVALUATION_REPORT",
            "validation_evidence_evaluation_report",
        )
        arena = _first_dict(
            state,
            "COGNITIVE_CANDIDATE_ARENA_REPORT",
            "cognitive_candidate_arena_report",
        )
        if isinstance(arena.get("candidate_arena_summary"), dict):
            arena = arena["candidate_arena_summary"]
        failures = _first_dict(state, "failure_summary", "FAILURE_SUMMARY")
        latest_failure = _first_dict(failures, "latest_failure")
        raw_applicability_state = str(
            raw_applicability.get("raw_result_applicability_state") or ""
        ).upper()
        validation_state = str(
            _first_meaningful(
                validation.get("execution_state"),
                validation.get("validation_execution_lifecycle_state"),
                default="",
            )
        ).upper()
        evidence_state = str(
            evaluation.get("evidence_acceptance_state")
            or evaluation.get("evidence_evaluation_state")
            or ""
        ).upper()
        if raw_applicability_state == "RAW_RESULT_NOT_APPLICABLE":
            payload = {
                "conclusion_state": "NOT_APPLICABLE",
                "largest_success": "scheduled_validation_task_executed_and_raw_result_contained",
                "largest_regression": "none",
                "current_open_decision": "none",
                "next_decision_gate": "none",
                "current_bottleneck": "none",
                "failure_reason": "none",
                "root_cause": "RAW_RESULT_NOT_APPLICABLE",
                "responsible_component": "none",
                "next_task": "none",
                "engineering_priority": "LOW",
            }
        elif validation_state in {
            "RAW_RESULT_CAPTURED",
            "RAW_RESULT_EMPTY_VALID_OUTPUT_CAPTURED",
        }:
            payload = {
                "conclusion_state": "UNDETERMINED",
                "largest_success": "scheduled_validation_task_executed_and_raw_result_captured",
                "largest_regression": "none",
                "current_open_decision": "WAITING_RAW_RESULT_EVIDENCE_EVALUATION",
                "next_decision_gate": "evaluate_raw_validation_result",
                "current_bottleneck": "validation_evidence_evaluation",
                "failure_reason": "none",
                "root_cause": "raw_validation_result_not_yet_evaluated",
                "responsible_component": "VALIDATION_EVIDENCE_EVALUATOR",
                "next_task": "evaluate_raw_validation_result_without_truth_grant",
                "engineering_priority": "HIGH",
            }
        elif latest_failure.get("failure_detected") is True:
            failure_causes = latest_failure.get("failure_causes")
            if isinstance(failure_causes, list) and failure_causes:
                failure_reason = str(failure_causes[0])
            else:
                failure_reason = str(
                    _first_meaningful(
                        latest_failure.get("failure_reason"),
                        latest_failure.get("success_state"),
                        default="runtime_failure_detected",
                    )
                )
            payload = {
                "conclusion_state": "FAILURE",
                "largest_success": "none",
                "largest_regression": failure_reason,
                "current_open_decision": "WAITING_FAILURE_REPAIR",
                "next_decision_gate": "repair_runtime_failure",
                "current_bottleneck": "runtime_failure",
                "failure_reason": failure_reason,
                "root_cause": failure_reason,
                "responsible_component": "RUNTIME_FAILURE_REPAIR",
                "next_task": "repair_runtime_failure",
                "engineering_priority": "HIGH",
            }
        elif evidence_state in {
            "",
            "PENDING",
            "NOT_EVALUATED",
            "BLOCKED_MISSING_EVALUATION_CONTRACT",
        }:
            payload = {
                "conclusion_state": "UNDETERMINED",
                "largest_success": _first_meaningful(
                    arena.get("arena_decision"),
                    arena.get("selection_state"),
                    default="none",
                ),
                "largest_regression": "none",
                "current_open_decision": "WAITING_GOVERNED_EVIDENCE_DECISION",
                "next_decision_gate": "complete_governed_evidence_decision",
                "current_bottleneck": "evidence_decision_pending",
                "failure_reason": "none",
                "root_cause": "evidence_decision_not_finalized",
                "responsible_component": "VALIDATION_EVIDENCE_EVALUATOR",
                "next_task": "complete_governed_evidence_decision",
                "engineering_priority": "MEDIUM",
            }
        else:
            payload = {
                "conclusion_state": "NO_FAILURE",
                "largest_success": "runtime_completed_without_open_engineering_failure",
                "largest_regression": "none",
                "current_open_decision": "none",
                "next_decision_gate": "continue_with_next_governed_runtime_stage",
                "current_bottleneck": "none",
                "failure_reason": "none",
                "root_cause": "none",
                "responsible_component": "none",
                "next_task": "continue_with_next_governed_runtime_stage",
                "engineering_priority": "LOW",
            }
        payload.update({
            "conclusion_source": "engineering_conclusion_integrity_evaluator",
            "conclusion_source_stage": "engineering_conclusion_integrity_evaluator",
            "conclusion_source_timestamp": _first_meaningful(
                metadata.get("timestamp"),
                state.get("timestamp"),
                default="TIMESTAMP_UNBOUND",
            ),
            "conclusion_is_current": True,
        })
        return self.normalize(
            payload,
            report_state=state,
            runtime_metadata=metadata,
        )

    def ensure_authoritative_conclusion(
        self,
        report_state: dict[str, Any],
        *,
        runtime_metadata: dict[str, Any] | None = None,
        derived_conclusion: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = dict(report_state if isinstance(report_state, dict) else {})
        metadata = runtime_metadata if isinstance(runtime_metadata, dict) else {}
        existing = _first_dict(state, "ENGINEERING_CONCLUSION", "engineering_conclusion")
        conclusion = dict(
            existing
            or derived_conclusion
            or self.create_authoritative_conclusion(
                state,
                runtime_metadata=metadata,
            )
        )
        conclusion = self.normalize(
            conclusion,
            report_state=state,
            runtime_metadata=metadata,
        )
        state["ENGINEERING_CONCLUSION"] = conclusion
        state["engineering_conclusion"] = dict(conclusion)
        return state

    def normalize(
        self,
        conclusion: dict[str, Any],
        *,
        report_state: dict[str, Any] | None = None,
        runtime_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = report_state if isinstance(report_state, dict) else {}
        metadata = runtime_metadata if isinstance(runtime_metadata, dict) else {}
        normalized = dict(conclusion if isinstance(conclusion, dict) else {})
        normalized["schema_version"] = _first_meaningful(
            normalized.get("schema_version"),
            default=_SCHEMA_VERSION,
        )
        expected_run_id = _first_meaningful(
            metadata.get("run_id"),
            metadata.get("execution_id"),
            state.get("run_id"),
            state.get("execution_id"),
            default="RUN_ID_UNBOUND",
        )
        observed_run_id = _first_meaningful(
            normalized.get("authoritative_run_id"),
            normalized.get("conclusion_run_id"),
            default=expected_run_id,
        )
        expected_execution_plan_id = _infer_execution_plan_id(state)
        observed_execution_plan_id = _first_meaningful(
            normalized.get("authoritative_execution_plan_id"),
            normalized.get("execution_plan_id"),
            default=expected_execution_plan_id,
        )
        run_mismatch = (
            expected_run_id not in {"RUN_ID_UNBOUND", None, ""}
            and observed_run_id not in {"RUN_ID_UNBOUND", None, ""}
            and observed_run_id != expected_run_id
        )
        plan_mismatch = (
            expected_execution_plan_id not in {"EXECUTION_PLAN_ID_UNBOUND", None, ""}
            and observed_execution_plan_id not in {"EXECUTION_PLAN_ID_UNBOUND", None, ""}
            and observed_execution_plan_id != expected_execution_plan_id
        )
        run_id = _first_meaningful(
            observed_run_id,
            default="RUN_ID_UNBOUND",
        )
        execution_plan_id = _first_meaningful(
            observed_execution_plan_id,
            default="EXECUTION_PLAN_ID_UNBOUND",
        )
        validation = _first_dict(
            state,
            "VALIDATION_TASK_EXECUTION_REPORT",
            "validation_task_execution_report",
        )
        raw_applicability = _first_dict(
            state,
            "RAW_RESULT_APPLICABILITY_REPORT",
            "raw_result_applicability_report",
        )
        raw_applicability_state = str(
            raw_applicability.get("raw_result_applicability_state") or ""
        ).upper()
        leading_candidate = _first_dict(state, "leading_candidate")
        raw_id = _first_meaningful(
            normalized.get("canonical_raw_result_id"),
            validation.get("canonical_raw_result_id"),
            validation.get("raw_validation_result_id"),
            validation.get("raw_result_id"),
            default=None,
        )
        normalized["engineering_conclusion_state"] = _first_meaningful(
            normalized.get("engineering_conclusion_state"),
            "AUTHORITATIVE_ENGINEERING_CONCLUSION_FINALIZED",
        )
        normalized["conclusion_state"] = _first_meaningful(
            normalized.get("conclusion_state"),
            default="UNDETERMINED",
        )
        normalized["conclusion_scope"] = _first_meaningful(
            normalized.get("conclusion_scope"),
            "current_run",
        )
        normalized["conclusion_is_current"] = _first_meaningful(
            normalized.get("conclusion_is_current"),
            default=True,
        )
        normalized["conclusion_run_id"] = run_id
        normalized["authoritative_run_id"] = run_id
        normalized["authoritative_execution_plan_id"] = execution_plan_id
        normalized["conclusion_task_id"] = _first_meaningful(
            normalized.get("conclusion_task_id"),
            metadata.get("task_id"),
            metadata.get("current_task_id"),
            validation.get("task_id"),
            leading_candidate.get("candidate_id"),
            state.get("task_id"),
            default="TASK_ID_UNBOUND",
        )
        normalized["failure_reason"] = _first_meaningful(
            normalized.get("failure_reason"),
            normalized.get("largest_regression"),
            default="none",
        )
        normalized["recommended_action"] = _first_meaningful(
            normalized.get("recommended_action"),
            normalized.get("immediate_next_development_task"),
            normalized.get("next_task"),
            default="monitor_current_run",
        )
        normalized["next_task"] = _first_meaningful(
            normalized.get("next_task"),
            normalized.get("immediate_next_development_task"),
            normalized.get("recommended_action"),
            default="monitor_current_run",
        )
        normalized["immediate_next_development_task"] = _first_meaningful(
            normalized.get("immediate_next_development_task"),
            normalized.get("next_task"),
            normalized.get("recommended_action"),
            default="monitor_current_run",
        )
        normalized["responsible_area"] = _first_meaningful(
            normalized.get("responsible_area"),
            normalized.get("responsible_component"),
            default="none",
        )
        normalized["next_gate"] = _first_meaningful(
            normalized.get("next_gate"),
            normalized.get("next_decision_gate"),
            default="none",
        )
        if raw_applicability_state == "RAW_RESULT_NOT_APPLICABLE":
            normalized.pop("canonical_raw_result_id", None)
        elif raw_id is not None and str(raw_id).strip().upper() not in {
            "",
            "NOT_ISSUED",
            "NOT_PRODUCED",
            "NOT_AVAILABLE",
            "NOT EXPECTED AT CURRENT LIFECYCLE STATE",
        }:
            normalized["canonical_raw_result_id"] = raw_id
        normalized["conclusion_source"] = _first_meaningful(
            normalized.get("conclusion_source"),
            normalized.get("conclusion_source_stage"),
            default="engineering_conclusion_integrity_evaluator",
        )
        normalized["conclusion_source_stage"] = _first_meaningful(
            normalized.get("conclusion_source_stage"),
            normalized.get("conclusion_source"),
            default="engineering_conclusion_integrity_evaluator",
        )
        normalized["conclusion_source_timestamp"] = _first_meaningful(
            normalized.get("conclusion_source_timestamp"),
            metadata.get("timestamp"),
            state.get("timestamp"),
            default="TIMESTAMP_UNBOUND",
        )
        normalized["conclusion_evaluation_source"] = (
            "engineering_conclusion_integrity_evaluator"
        )
        normalized["persistence_applicability"] = _first_meaningful(
            normalized.get("persistence_applicability"),
            default="NOT_APPLICABLE",
        )
        normalized["persistence_applicability_reason"] = _first_meaningful(
            normalized.get("persistence_applicability_reason"),
            default="no_engineering_conclusion_persistence_obligation_at_this_lifecycle_point",
        )
        normalized["persistence_write_attempted"] = _first_meaningful(
            normalized.get("persistence_write_attempted"),
            default=False,
        )
        normalized["persistence_write_completed"] = _first_meaningful(
            normalized.get("persistence_write_completed"),
            default=False,
        )
        normalized["persistence_readback_attempted"] = _first_meaningful(
            normalized.get("persistence_readback_attempted"),
            default=False,
        )
        normalized["persistence_readback_completed"] = _first_meaningful(
            normalized.get("persistence_readback_completed"),
            default=False,
        )
        normalized["persistence_integrity"] = _first_meaningful(
            normalized.get("persistence_integrity"),
            default="NOT_APPLICABLE",
        )
        normalized["persistence_integrity_reason"] = _first_meaningful(
            normalized.get("persistence_integrity_reason"),
            default="no_engineering_conclusion_persistence_obligation_at_this_lifecycle_point",
        )
        normalized["emission_integrity"] = _first_meaningful(
            normalized.get("emission_integrity"),
            default="NOT_EVALUATED",
        )
        normalized["emission_integrity_reason"] = _first_meaningful(
            normalized.get("emission_integrity_reason"),
            default="structured_emission_integrity_not_evaluated",
        )
        normalized["emission_conflict_count"] = _first_meaningful(
            normalized.get("emission_conflict_count"),
            default=0,
        )
        normalized["emission_conflict_fields"] = _first_meaningful(
            normalized.get("emission_conflict_fields"),
            default=[],
        )
        normalized["authoritative_fingerprint"] = _first_meaningful(
            normalized.get("authoritative_fingerprint"),
            normalized.get("conclusion_fingerprint"),
        )
        normalized["emitted_fingerprint"] = _first_meaningful(
            normalized.get("emitted_fingerprint"),
            default=None,
        )
        normalized["authoritative_emitted_stable_field_comparison"] = _first_meaningful(
            normalized.get("authoritative_emitted_stable_field_comparison"),
            default=[],
        )
        normalized["persistence_matches_emission"] = _first_meaningful(
            normalized.get("persistence_matches_emission"),
            default="NOT_APPLICABLE",
        )
        normalized["persistence_emission_conflict_count"] = _first_meaningful(
            normalized.get("persistence_emission_conflict_count"),
            default=0,
        )
        normalized["persistence_emission_conflict_fields"] = _first_meaningful(
            normalized.get("persistence_emission_conflict_fields"),
            default=[],
        )
        normalized["current_run_binding_state"] = (
            "PREVIOUS_RUN_REJECTED"
            if run_mismatch
            else "EXECUTION_PLAN_MISMATCH_REJECTED"
            if plan_mismatch
            else
            "BOUND_TO_CURRENT_RUN"
            if run_id not in {"RUN_ID_UNBOUND", None, ""}
            else "RUN_ID_UNBOUND"
        )
        normalized["_run_binding_mismatch"] = run_mismatch
        normalized["_execution_plan_binding_mismatch"] = plan_mismatch
        normalized["conclusion_historical_issue_count"] = _first_meaningful(
            normalized.get("conclusion_historical_issue_count"),
            default=0,
        )
        normalized["engineering_conclusion_id"] = _first_meaningful(
            normalized.get("engineering_conclusion_id"),
            f"engineering_conclusion_{_stable_fingerprint(_canonical_payload(normalized, include_fingerprint=False))[:16]}",
        )
        supplied_pre_fingerprint = normalized.get("pre_reconciliation_fingerprint")
        conflicts = self.integrity_conflicts(normalized)
        normalized["integrity_conflicts"] = conflicts
        normalized["conclusion_conflict_count"] = len(conflicts)
        normalized["engineering_conclusion_integrity_state"] = (
            "ENGINEERING_CONCLUSION_CONFLICT"
            if conflicts
            else "ENGINEERING_CONCLUSION_INTEGRITY_VERIFIED"
        )
        normalized["integrity"] = "INVALID" if conflicts else "VALID"
        normalized["engineering_conclusion_integrity_reason"] = (
            "; ".join(conflicts)
            if conflicts
            else "authoritative_conclusion_fields_are_consistent"
        )
        semantic_fingerprint = _stable_fingerprint(
            _canonical_payload(normalized, include_fingerprint=False)
        )
        normalized["post_reconciliation_fingerprint"] = semantic_fingerprint
        normalized["pre_reconciliation_fingerprint"] = _first_meaningful(
            supplied_pre_fingerprint,
            normalized["post_reconciliation_fingerprint"],
        )
        normalized["conclusion_fingerprint"] = semantic_fingerprint
        normalized["authoritative_fingerprint"] = _first_meaningful(
            normalized.get("authoritative_fingerprint"),
            normalized["conclusion_fingerprint"],
        )
        _append_transition(
            normalized,
            _FINALIZED_TRANSITION,
            source_stage=str(normalized.get("conclusion_source")),
            source_timestamp=_first_meaningful(
                normalized.get("conclusion_source_timestamp"),
                metadata.get("timestamp"),
                default="TIMESTAMP_UNBOUND",
            ),
        )
        _append_transition(
            normalized,
            _EVALUATED_TRANSITION,
            source_stage="engineering_conclusion_integrity_evaluator",
            source_timestamp=_first_meaningful(
                metadata.get("timestamp"),
                normalized.get("conclusion_source_timestamp"),
                default="TIMESTAMP_UNBOUND",
            ),
        )
        return normalized

    def evaluate_persistence_applicability(
        self,
        conclusion: dict[str, Any],
        *,
        artifact_path: str | Path | None = None,
        persistence_required: bool = False,
    ) -> dict[str, Any]:
        normalized = self.normalize(conclusion)
        applicable = bool(persistence_required or artifact_path is not None)
        state = "APPLICABLE" if applicable else "NOT_APPLICABLE"
        normalized["persistence_applicability"] = state
        normalized["persistence_applicability_reason"] = (
            "persistence_requested_for_engineering_conclusion"
            if applicable
            else "no_engineering_conclusion_persistence_obligation_at_this_lifecycle_point"
        )
        normalized["persistence_integrity"] = (
            "NOT_EVALUATED" if applicable else "NOT_APPLICABLE"
        )
        normalized["persistence_integrity_reason"] = normalized[
            "persistence_applicability_reason"
        ]
        _append_transition(
            normalized,
            _PERSISTENCE_APPLICABILITY_EVALUATED_TRANSITION,
            source_stage="engineering_conclusion_integrity_evaluator",
            source_timestamp=normalized.get("conclusion_source_timestamp"),
        )
        return normalized

    def integrity_conflicts(self, conclusion: dict[str, Any]) -> list[str]:
        conflicts: list[str] = []
        explicit_conflicts = conclusion.get("integrity_conflicts")
        if isinstance(explicit_conflicts, list):
            conflicts.extend(str(item) for item in explicit_conflicts if item)
        integrity = str(
            _first_meaningful(
                conclusion.get("integrity"),
                conclusion.get("engineering_conclusion_integrity"),
                default="",
            )
        ).upper()
        if integrity == "INVALID" and not conflicts:
            conflicts.append("engineering_conclusion_marked_invalid")
        if conclusion.get("_run_binding_mismatch") is True:
            conflicts.append("previous_run_conclusion_cannot_bind_to_current_run")
        if conclusion.get("_execution_plan_binding_mismatch") is True:
            conflicts.append("execution_plan_id_mismatch_rejected")
        failure = str(conclusion.get("failure_reason") or "none").lower()
        root = str(conclusion.get("root_cause") or "none").lower()
        conclusion_state = str(
            conclusion.get("conclusion_state") or ""
        ).upper()
        next_gate = str(conclusion.get("next_gate") or "").lower()
        recommended_action = str(
            conclusion.get("recommended_action") or ""
        ).lower()
        next_task = str(conclusion.get("next_task") or "").lower()
        if (
            conclusion_state == "NOT_APPLICABLE"
            and root == "raw_result_not_applicable"
            and (
                "repair_raw_validation_result_identity" in next_gate
                or "repair_raw_validation_result_identity" in recommended_action
                or "repair_raw_validation_result_identity" in next_task
            )
        ):
            conflicts.append(
                "not_applicable_raw_result_identity_repair_gate_incompatible"
            )
        if failure == "none" and root not in {"none", ""}:
            allowed_decision_roots = {
                "raw_validation_result_not_yet_evaluated",
                "raw_validation_result_not_structurally_eligible",
                "raw_validation_idENTITY_input_unavailable".lower(),
                "raw_result_not_applicable",
                "accepted_validation_evidence_not_yet_admitted_to_arena",
                "validation_result_does_not_fully_satisfy_required_evidence_contract",
            }
            if root not in allowed_decision_roots:
                conflicts.append("failure_reason=none conflicts with non_none_root_cause")
        if conclusion.get("conclusion_is_current") is False and conflicts:
            return []
        return list(dict.fromkeys(conflicts))

    def has_conflict(self, conclusion: dict[str, Any]) -> bool:
        normalized = self.normalize(conclusion)
        return bool(normalized.get("integrity_conflicts"))

    def bind_to_canonical_report(
        self,
        conclusion: dict[str, Any],
        *,
        report_state: dict[str, Any] | None = None,
        runtime_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metadata = runtime_metadata if isinstance(runtime_metadata, dict) else {}
        bound = self.normalize(
            conclusion,
            report_state=report_state,
            runtime_metadata=metadata,
        )
        _append_transition(
            bound,
            _BOUND_TRANSITION,
            source_stage="final_report_renderer",
            source_timestamp=_first_meaningful(
                metadata.get("timestamp"),
                bound.get("conclusion_source_timestamp"),
                default="TIMESTAMP_UNBOUND",
            ),
        )
        return bound

    def stable_payload(self, conclusion: dict[str, Any]) -> dict[str, Any]:
        normalized = self.normalize(conclusion)
        return _canonical_payload(normalized)

    def structured_emission_payload(self, conclusion: dict[str, Any]) -> dict[str, Any]:
        normalized = self.normalize(conclusion)
        payload = self.stable_payload(normalized)
        payload["engineering_conclusion_lifecycle_transitions"] = list(
            normalized.get("engineering_conclusion_lifecycle_transitions") or []
        )
        return payload

    def evaluate_emission_integrity(
        self,
        authoritative: dict[str, Any],
        emitted: dict[str, Any] | None,
    ) -> dict[str, Any]:
        authoritative_normalized = self.normalize(authoritative)
        if not isinstance(emitted, dict):
            _append_transition(
                authoritative_normalized,
                _EMISSION_INTEGRITY_EVALUATED_TRANSITION,
                source_stage="engineering_conclusion_integrity_evaluator",
                source_timestamp=authoritative_normalized.get(
                    "conclusion_source_timestamp"
                ),
            )
            return {
                "emission_integrity": "NOT_EVALUATED",
                "emission_integrity_reason": (
                    "structured_emission_payload_not_available"
                ),
                "emission_conflict_count": 0,
                "emission_conflict_fields": [],
                "authoritative_fingerprint": authoritative_normalized.get(
                    "conclusion_fingerprint"
                ),
                "emitted_fingerprint": None,
                "authoritative_run_id": authoritative_normalized.get(
                    "authoritative_run_id"
                ),
                "emitted_run_id": None,
                "authoritative_execution_plan_id": authoritative_normalized.get(
                    "authoritative_execution_plan_id"
                ),
                "emitted_execution_plan_id": None,
                "authoritative_emitted_stable_field_comparison": [],
                "mismatch_count": 0,
                "mismatches": [],
                "engineering_conclusion_lifecycle_transitions": list(
                    authoritative_normalized.get(
                        "engineering_conclusion_lifecycle_transitions"
                    )
                    or []
                ),
            }

        comparison = self.compare_semantic_payloads(
            authoritative_normalized,
            emitted,
        )
        emitted_payload = _canonical_payload(emitted, preserve_missing=True)
        matches = comparison["comparison_state"] == "SEMANTIC_PAYLOAD_MATCH"
        _append_transition(
            authoritative_normalized,
            _EMISSION_INTEGRITY_EVALUATED_TRANSITION,
            source_stage="engineering_conclusion_integrity_evaluator",
            source_timestamp=authoritative_normalized.get(
                "conclusion_source_timestamp"
            ),
        )
        stable_field_comparison = [
            {
                "field": field,
                "state": "MATCH"
                if not any(row["field"] == field for row in comparison["mismatches"])
                else "CONFLICT",
            }
            for field in STABLE_SEMANTIC_FIELDS
        ]
        return {
            "emission_integrity": (
                "EMISSION_VERIFIED" if matches else "EMISSION_FAILED"
            ),
            "emission_integrity_reason": (
                "authoritative_and_emitted_payloads_match"
                if matches
                else "authoritative_and_emitted_payloads_differ"
            ),
            "emission_conflict_count": comparison["mismatch_count"],
            "emission_conflict_fields": [
                row["field"] for row in comparison["mismatches"]
            ],
            "authoritative_fingerprint": comparison["expected_fingerprint"],
            "emitted_fingerprint": comparison["observed_fingerprint"],
            "authoritative_run_id": authoritative_normalized.get(
                "authoritative_run_id"
            ),
            "emitted_run_id": emitted_payload.get("authoritative_run_id"),
            "authoritative_execution_plan_id": authoritative_normalized.get(
                "authoritative_execution_plan_id"
            ),
            "emitted_execution_plan_id": emitted_payload.get(
                "authoritative_execution_plan_id"
            ),
            "authoritative_emitted_stable_field_comparison": (
                stable_field_comparison
            ),
            "mismatch_count": comparison["mismatch_count"],
            "mismatches": comparison["mismatches"],
            "binding_state": comparison["binding_state"],
            "engineering_conclusion_lifecycle_transitions": list(
                authoritative_normalized.get(
                    "engineering_conclusion_lifecycle_transitions"
                )
                or []
            ),
        }

    def compare_semantic_payloads(
        self,
        expected: dict[str, Any],
        observed: dict[str, Any],
    ) -> dict[str, Any]:
        expected_normalized = self.normalize(expected)
        expected_payload = _canonical_payload(
            expected_normalized,
            preserve_missing=False,
        )
        observed_payload = _canonical_payload(
            observed,
            preserve_missing=True,
        )
        observed_recomputed_fingerprint = _recomputed_payload_fingerprint(observed)
        mismatches = []
        for field in STABLE_SEMANTIC_FIELDS:
            expected_value = expected_payload.get(field)
            observed_value = observed_payload.get(field)
            if observed_value == _MISSING_STABLE_FIELD:
                mismatches.append({
                    "field": field,
                    "conflict_type": "STABLE_FIELD_MISSING",
                    "expected_value": expected_value,
                    "observed_value": "MISSING",
                })
                continue
            if (
                field == "conclusion_fingerprint"
                and observed_value != expected_value
            ):
                mismatches.append({
                    "field": field,
                    "conflict_type": "FINGERPRINT_MISMATCH",
                    "expected_value": expected_value,
                    "observed_value": observed_value,
                })
                continue
            if self._format_insensitive_value(expected_value) != (
                self._format_insensitive_value(observed_value)
            ):
                mismatches.append({
                    "field": field,
                    "conflict_type": "STABLE_VALUE_MISMATCH",
                    "expected_value": expected_value,
                    "observed_value": observed_value,
                })
        if observed_recomputed_fingerprint != expected_payload.get(
            "conclusion_fingerprint"
        ):
            mismatches.append({
                "field": "conclusion_fingerprint",
                "conflict_type": "RECOMPUTED_FINGERPRINT_MISMATCH",
                "expected_value": expected_payload.get("conclusion_fingerprint"),
                "observed_value": observed_recomputed_fingerprint,
            })
        expected_run = expected_payload.get("authoritative_run_id")
        observed_run = observed_payload.get("authoritative_run_id")
        expected_plan = expected_payload.get("authoritative_execution_plan_id")
        observed_plan = observed_payload.get("authoritative_execution_plan_id")
        return {
            "comparison_state": (
                "SEMANTIC_PAYLOAD_MATCH"
                if not mismatches
                else "SEMANTIC_PAYLOAD_MISMATCH"
            ),
            "mismatch_count": len(mismatches),
            "mismatches": mismatches,
            "expected_fingerprint": expected_payload.get("conclusion_fingerprint"),
            "observed_fingerprint": observed_payload.get("conclusion_fingerprint"),
            "observed_recomputed_fingerprint": observed_recomputed_fingerprint,
            "binding_state": (
                "RUN_ID_MISMATCH_REJECTED"
                if self._format_insensitive_value(expected_run)
                != self._format_insensitive_value(observed_run)
                else "EXECUTION_PLAN_ID_MISMATCH_REJECTED"
                if self._format_insensitive_value(expected_plan)
                != self._format_insensitive_value(observed_plan)
                else "BOUND_TO_CURRENT_RUN"
            ),
        }

    def persist_conclusion(
        self,
        conclusion: dict[str, Any],
        artifact_path: str | Path,
    ) -> dict[str, Any]:
        path = Path(artifact_path)
        normalized = self.evaluate_persistence_applicability(
            conclusion,
            artifact_path=path,
        )
        payload = self.stable_payload(normalized)
        normalized["persistence_write_attempted"] = True
        _append_transition(
            normalized,
            _PERSISTENCE_WRITE_STARTED_TRANSITION,
            source_stage="engineering_conclusion_integrity_evaluator",
            source_timestamp=normalized.get("conclusion_source_timestamp"),
        )
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(payload, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            write_completed = True
            integrity = "NOT_EVALUATED"
            reason = "stable_payload_written_readback_not_yet_evaluated"
        except OSError as exc:
            write_completed = False
            integrity = "FAILED"
            reason = f"persistence_write_failed:{exc.__class__.__name__}"
        normalized["persistence_write_completed"] = write_completed
        normalized["persistence_integrity"] = integrity
        normalized["persistence_integrity_reason"] = reason
        if write_completed:
            _append_transition(
                normalized,
                _PERSISTED_TRANSITION,
                source_stage="engineering_conclusion_integrity_evaluator",
                source_timestamp=normalized.get("conclusion_source_timestamp"),
            )
        if not write_completed:
            _append_transition(
                normalized,
                _PERSISTENCE_INTEGRITY_EVALUATED_TRANSITION,
                source_stage="engineering_conclusion_integrity_evaluator",
                source_timestamp=normalized.get("conclusion_source_timestamp"),
            )
        return {
            "persistence_applicability": "APPLICABLE",
            "persistence_applicability_reason": (
                "persistence_requested_for_engineering_conclusion"
            ),
            "persistence_write_attempted": True,
            "persistence_write_completed": write_completed,
            "persistence_readback_attempted": False,
            "persistence_readback_completed": False,
            "persistence_integrity": integrity,
            "persistence_integrity_reason": reason,
            "artifact_path": str(path),
            "conclusion_fingerprint": payload.get("conclusion_fingerprint"),
            "stored_fingerprint": (
                payload.get("conclusion_fingerprint") if write_completed else None
            ),
            "persisted_payload": payload,
            "engineering_conclusion_lifecycle_transitions": list(
                normalized.get("engineering_conclusion_lifecycle_transitions") or []
            ),
        }

    def read_persisted_conclusion(self, artifact_path: str | Path) -> dict[str, Any]:
        path = Path(artifact_path)
        readback = {
            "persistence_readback_attempted": True,
            "persistence_readback_completed": False,
            "persistence_integrity": "FAILED",
            "persistence_integrity_reason": "persistence_readback_not_completed",
            "artifact_path": str(path),
            "engineering_conclusion_lifecycle_transitions": [],
        }
        _append_transition(
            readback,
            _PERSISTENCE_READBACK_STARTED_TRANSITION,
            source_stage="engineering_conclusion_integrity_evaluator",
            source_timestamp="TIMESTAMP_UNBOUND",
        )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            readback["persistence_integrity_reason"] = "persistence_artifact_missing"
            _append_transition(
                readback,
                _PERSISTENCE_INTEGRITY_EVALUATED_TRANSITION,
                source_stage="engineering_conclusion_integrity_evaluator",
                source_timestamp="TIMESTAMP_UNBOUND",
            )
            return readback
        except json.JSONDecodeError:
            readback["persistence_integrity_reason"] = (
                "persistence_readback_corrupt_json"
            )
            _append_transition(
                readback,
                _PERSISTENCE_INTEGRITY_EVALUATED_TRANSITION,
                source_stage="engineering_conclusion_integrity_evaluator",
                source_timestamp="TIMESTAMP_UNBOUND",
            )
            return readback
        except OSError as exc:
            readback["persistence_integrity_reason"] = (
                f"persistence_readback_failed:{exc.__class__.__name__}"
            )
            _append_transition(
                readback,
                _PERSISTENCE_INTEGRITY_EVALUATED_TRANSITION,
                source_stage="engineering_conclusion_integrity_evaluator",
                source_timestamp="TIMESTAMP_UNBOUND",
            )
            return readback
        normalized = self.normalize(payload)
        normalized["persistence_readback_attempted"] = True
        normalized["persistence_readback_completed"] = True
        normalized["stored_fingerprint"] = payload.get("conclusion_fingerprint")
        normalized["recomputed_readback_fingerprint"] = (
            _recomputed_payload_fingerprint(payload)
        )
        _append_transition(
            normalized,
            _PERSISTENCE_READBACK_STARTED_TRANSITION,
            source_stage="engineering_conclusion_integrity_evaluator",
            source_timestamp=normalized.get("conclusion_source_timestamp"),
        )
        _append_transition(
            normalized,
            _READBACK_TRANSITION,
            source_stage="engineering_conclusion_integrity_evaluator",
            source_timestamp=normalized.get("conclusion_source_timestamp"),
        )
        return normalized

    def evaluate_persistence_integrity(
        self,
        authoritative: dict[str, Any],
        readback: dict[str, Any] | None,
    ) -> dict[str, Any]:
        authoritative_normalized = self.normalize(authoritative)
        if not isinstance(readback, dict) or readback.get(
            "persistence_readback_completed"
        ) is not True:
            reason = (
                readback.get("persistence_integrity_reason")
                if isinstance(readback, dict)
                else "persistence_readback_not_available"
            )
            transitions = (
                list(readback.get("engineering_conclusion_lifecycle_transitions") or [])
                if isinstance(readback, dict)
                else list(
                    authoritative_normalized.get(
                        "engineering_conclusion_lifecycle_transitions"
                    )
                    or []
                )
            )
            result = {
                **authoritative_normalized,
                "persistence_applicability": "APPLICABLE",
                "persistence_applicability_reason": (
                    "persistence_requested_for_engineering_conclusion"
                ),
                "persistence_readback_attempted": bool(
                    isinstance(readback, dict)
                    and readback.get("persistence_readback_attempted")
                ),
                "persistence_readback_completed": False,
                "persistence_integrity": "FAILED",
                "persistence_integrity_reason": reason,
                "persistence_matches_emission": "NOT_EVALUATED",
                "persistence_emission_conflict_count": 0,
                "persistence_emission_conflict_fields": [],
                "stored_fingerprint": (
                    readback.get("stored_fingerprint")
                    if isinstance(readback, dict)
                    else None
                ),
                "recomputed_readback_fingerprint": (
                    readback.get("recomputed_readback_fingerprint")
                    if isinstance(readback, dict)
                    else None
                ),
                "readback_run_id": (
                    readback.get("authoritative_run_id")
                    if isinstance(readback, dict)
                    else None
                ),
                "readback_execution_plan_id": (
                    readback.get("authoritative_execution_plan_id")
                    if isinstance(readback, dict)
                    else None
                ),
                "authoritative_readback_stable_field_comparison": [],
                "mismatches": [],
                "engineering_conclusion_lifecycle_transitions": transitions,
            }
            _append_transition(
                result,
                _PERSISTENCE_INTEGRITY_EVALUATED_TRANSITION,
                source_stage="engineering_conclusion_integrity_evaluator",
                source_timestamp=result.get("conclusion_source_timestamp"),
            )
            return result

        comparison = self.compare_semantic_payloads(
            authoritative_normalized,
            readback,
        )
        matches = comparison["comparison_state"] == "SEMANTIC_PAYLOAD_MATCH"
        result = {
            **authoritative_normalized,
            "persistence_applicability": "APPLICABLE",
            "persistence_applicability_reason": (
                "persistence_requested_for_engineering_conclusion"
            ),
            "persistence_write_attempted": True,
            "persistence_write_completed": True,
            "persistence_readback_attempted": True,
            "persistence_readback_completed": True,
            "persistence_integrity": "VERIFIED" if matches else "FAILED",
            "persistence_integrity_reason": (
                "authoritative_and_persisted_readback_payloads_match"
                if matches
                else "authoritative_and_persisted_readback_payloads_differ"
            ),
            "persistence_matches_emission": "NOT_EVALUATED",
            "persistence_emission_conflict_count": comparison["mismatch_count"],
            "persistence_emission_conflict_fields": [
                row["field"] for row in comparison["mismatches"]
            ],
            "authoritative_fingerprint": comparison["expected_fingerprint"],
            "stored_fingerprint": comparison["observed_fingerprint"],
            "recomputed_readback_fingerprint": comparison[
                "observed_recomputed_fingerprint"
            ],
            "readback_run_id": readback.get("authoritative_run_id"),
            "readback_execution_plan_id": readback.get(
                "authoritative_execution_plan_id"
            ),
            "authoritative_readback_stable_field_comparison": [
                {
                    "field": field,
                    "state": "MATCH"
                    if not any(row["field"] == field for row in comparison["mismatches"])
                    else "CONFLICT",
                    "conflict_type": next(
                        (
                            row["conflict_type"]
                            for row in comparison["mismatches"]
                            if row["field"] == field
                        ),
                        "NONE",
                    ),
                }
                for field in STABLE_SEMANTIC_FIELDS
            ],
            "mismatch_count": comparison["mismatch_count"],
            "mismatches": comparison["mismatches"],
            "binding_state": comparison["binding_state"],
            "engineering_conclusion_lifecycle_transitions": list(
                readback.get("engineering_conclusion_lifecycle_transitions") or []
            ),
        }
        _append_transition(
            result,
            _PERSISTENCE_INTEGRITY_EVALUATED_TRANSITION,
            source_stage="engineering_conclusion_integrity_evaluator",
            source_timestamp=result.get("conclusion_source_timestamp"),
        )
        return result

    def persistence_emission_parity(
        self,
        persisted: dict[str, Any] | None,
        emitted: dict[str, Any],
        *,
        authoritative: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if persisted is None:
            emitted_normalized = self.normalize(emitted)
            _append_transition(
                emitted_normalized,
                _EMISSION_INTEGRITY_EVALUATED_TRANSITION,
                source_stage="engineering_conclusion_integrity_evaluator",
                source_timestamp=emitted_normalized.get("conclusion_source_timestamp"),
            )
            _append_transition(
                emitted_normalized,
                _PERSISTENCE_EMISSION_PARITY_EVALUATED_TRANSITION,
                source_stage="engineering_conclusion_integrity_evaluator",
                source_timestamp=emitted_normalized.get("conclusion_source_timestamp"),
            )
            return {
                "persistence_applicability": "NOT_APPLICABLE",
                "persistence_integrity": "NOT_APPLICABLE",
                "persistence_integrity_reason": (
                    "no_engineering_conclusion_persistence_obligation_at_this_lifecycle_point"
                ),
                "emission_integrity": "NOT_EVALUATED",
                "emission_integrity_reason": (
                    "authoritative_emission_comparison_not_performed"
                ),
                "persistence_matches_emission": "NOT_APPLICABLE",
                "persistence_emission_conflict_count": 0,
                "persistence_emission_conflict_fields": [],
                "emission_conflict_count": 0,
                "emission_conflict_fields": [],
                "authoritative_fingerprint": None,
                "emitted_fingerprint": emitted_normalized.get(
                    "conclusion_fingerprint"
                ),
                "mismatch_count": 0,
                "mismatches": [],
                "engineering_conclusion_lifecycle_transitions": list(
                    emitted_normalized.get(
                        "engineering_conclusion_lifecycle_transitions",
                    )
                    or []
                ),
            }
        if isinstance(authoritative, dict):
            persistence = self.evaluate_persistence_integrity(authoritative, persisted)
            emission = self.evaluate_emission_integrity(authoritative, emitted)
            matches = (
                persistence["persistence_integrity"] == "VERIFIED"
                and emission["emission_integrity"] == "EMISSION_VERIFIED"
            )
            conflict_fields = list(dict.fromkeys(
                list(persistence.get("persistence_emission_conflict_fields") or [])
                + list(emission.get("emission_conflict_fields") or [])
            ))
            persisted_payload = _canonical_payload(persisted, preserve_missing=True)
            emitted_payload = _canonical_payload(emitted, preserve_missing=True)
            stable_field_comparison = [
                {
                    "field": field,
                    "applicability": (
                        "OPTIONAL_NOT_APPLICABLE"
                        if field in {"canonical_raw_result_id", "conclusion_task_id"}
                        and _canonical_payload(authoritative).get(field) in {None, "TASK_ID_UNBOUND"}
                        else "APPLICABLE"
                    ),
                    "authoritative_value": _canonical_payload(authoritative).get(field),
                    "persisted_readback_value": persisted_payload.get(field),
                    "emitted_value": emitted_payload.get(field),
                    "comparison_result": (
                        "MATCH"
                        if field not in conflict_fields
                        else "CONFLICT"
                    ),
                    "conflict_type": next(
                        (
                            row["conflict_type"]
                            for row in (
                                list(persistence.get("mismatches") or [])
                                + list(emission.get("mismatches") or [])
                            )
                            if row["field"] == field
                        ),
                        "NONE",
                    ),
                }
                for field in STABLE_SEMANTIC_FIELDS
            ]
            emitted_normalized = self.normalize(emitted)
            transitions = list(
                persistence.get("engineering_conclusion_lifecycle_transitions") or []
            )
            if transitions:
                emitted_normalized["engineering_conclusion_lifecycle_transitions"] = (
                    transitions
                )
            _append_transition(
                emitted_normalized,
                _PERSISTENCE_EMISSION_PARITY_EVALUATED_TRANSITION,
                source_stage="engineering_conclusion_integrity_evaluator",
                source_timestamp=emitted_normalized.get("conclusion_source_timestamp"),
            )
            return {
                "persistence_applicability": "APPLICABLE",
                "persistence_applicability_reason": (
                    "persistence_requested_for_engineering_conclusion"
                ),
                "persistence_write_attempted": persistence.get(
                    "persistence_write_attempted"
                ),
                "persistence_write_completed": persistence.get(
                    "persistence_write_completed"
                ),
                "persistence_readback_attempted": persistence.get(
                    "persistence_readback_attempted"
                ),
                "persistence_readback_completed": persistence.get(
                    "persistence_readback_completed"
                ),
                "persistence_integrity": persistence["persistence_integrity"],
                "persistence_integrity_reason": persistence[
                    "persistence_integrity_reason"
                ],
                "emission_integrity": emission["emission_integrity"],
                "emission_integrity_reason": emission["emission_integrity_reason"],
                "persistence_matches_emission": matches,
                "persistence_emission_conflict_count": len(conflict_fields),
                "persistence_emission_conflict_fields": conflict_fields,
                "emission_conflict_count": emission["emission_conflict_count"],
                "emission_conflict_fields": emission["emission_conflict_fields"],
                "authoritative_fingerprint": persistence.get(
                    "authoritative_fingerprint"
                ),
                "stored_fingerprint": persistence.get("stored_fingerprint"),
                "recomputed_readback_fingerprint": persistence.get(
                    "recomputed_readback_fingerprint"
                ),
                "emitted_fingerprint": emission.get("emitted_fingerprint"),
                "authoritative_run_id": persistence.get("authoritative_run_id"),
                "persisted_run_id": persisted_payload.get("authoritative_run_id"),
                "readback_run_id": persistence.get("readback_run_id"),
                "emitted_run_id": emission.get("emitted_run_id"),
                "authoritative_execution_plan_id": persistence.get(
                    "authoritative_execution_plan_id"
                ),
                "persisted_execution_plan_id": persisted_payload.get(
                    "authoritative_execution_plan_id"
                ),
                "readback_execution_plan_id": persistence.get(
                    "readback_execution_plan_id"
                ),
                "emitted_execution_plan_id": emission.get(
                    "emitted_execution_plan_id"
                ),
                "authoritative_persisted_emitted_stable_field_comparison": (
                    stable_field_comparison
                ),
                "mismatch_count": len(conflict_fields),
                "mismatches": list(persistence.get("mismatches") or [])
                + list(emission.get("mismatches") or []),
                "binding_state": persistence.get("binding_state"),
                "engineering_conclusion_lifecycle_transitions": list(
                    emitted_normalized.get(
                        "engineering_conclusion_lifecycle_transitions"
                    )
                    or []
                ),
            }
        comparison = self.compare_semantic_payloads(persisted, emitted)
        matches = comparison["comparison_state"] == "SEMANTIC_PAYLOAD_MATCH"
        emitted_normalized = self.normalize(emitted)
        _append_transition(
            emitted_normalized,
            _PERSISTENCE_EMISSION_PARITY_EVALUATED_TRANSITION,
            source_stage="engineering_conclusion_integrity_evaluator",
            source_timestamp=emitted_normalized.get("conclusion_source_timestamp"),
        )
        return {
            "persistence_applicability": "APPLICABLE",
            "persistence_integrity": "VERIFIED" if matches else "FAILED",
            "persistence_integrity_reason": (
                "persisted_payload_matches_emitted_payload"
                if matches
                else "persisted_payload_differs_from_emitted_payload"
            ),
            "emission_integrity": (
                "EMISSION_VERIFIED" if matches else "EMISSION_FAILED"
            ),
            "emission_integrity_reason": (
                "authoritative_and_emitted_payloads_match"
                if matches
                else "authoritative_and_emitted_payloads_differ"
            ),
            "persistence_matches_emission": matches,
            "persistence_emission_conflict_count": comparison["mismatch_count"],
            "persistence_emission_conflict_fields": [
                row["field"] for row in comparison["mismatches"]
            ],
            "emission_conflict_count": comparison["mismatch_count"],
            "emission_conflict_fields": [
                row["field"] for row in comparison["mismatches"]
            ],
            "mismatch_count": comparison["mismatch_count"],
            "mismatches": comparison["mismatches"],
            "persisted_fingerprint": comparison["expected_fingerprint"],
            "emitted_fingerprint": comparison["observed_fingerprint"],
            "binding_state": comparison["binding_state"],
            "engineering_conclusion_lifecycle_transitions": list(
                emitted_normalized.get("engineering_conclusion_lifecycle_transitions")
                or []
            ),
        }

    def mark_human_report_projected(
        self,
        conclusion: dict[str, Any],
    ) -> dict[str, Any]:
        projected = self.normalize(conclusion)
        _append_transition(
            projected,
            _PERSISTENCE_APPLICABILITY_EVALUATED_TRANSITION,
            source_stage="engineering_conclusion_integrity_evaluator",
            source_timestamp=projected.get("conclusion_source_timestamp"),
        )
        already_evaluated = projected.get("emission_integrity") in {
            "EMISSION_VERIFIED",
            "EMISSION_FAILED",
        } and projected.get("emission_integrity_reason") not in {
            "structured_emission_payload_available",
            "structured_engineering_conclusion_emission_payload_built",
        }
        if already_evaluated:
            _append_transition(
                projected,
                _EMISSION_INTEGRITY_EVALUATED_TRANSITION,
                source_stage="engineering_conclusion_integrity_evaluator",
                source_timestamp=projected.get("conclusion_source_timestamp"),
            )
        else:
            emitted = self.structured_emission_payload(projected)
            emission = self.evaluate_emission_integrity(projected, emitted)
            projected.update({
                key: value
                for key, value in emission.items()
                if key != "engineering_conclusion_lifecycle_transitions"
            })
            projected["engineering_conclusion_lifecycle_transitions"] = list(
                emission.get("engineering_conclusion_lifecycle_transitions") or []
            )
        _append_transition(
            projected,
            _PERSISTENCE_EMISSION_PARITY_EVALUATED_TRANSITION,
            source_stage="engineering_conclusion_integrity_evaluator",
            source_timestamp=projected.get("conclusion_source_timestamp"),
        )
        _append_transition(
            projected,
            _HUMAN_REPORT_PROJECTED_TRANSITION,
            source_stage="final_report_renderer",
            source_timestamp=projected.get("conclusion_source_timestamp"),
        )
        return projected

    def _format_insensitive_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return " ".join(value.strip().split())
        return value


engineering_conclusion_integrity_evaluator = EngineeringConclusionIntegrityEvaluator()
