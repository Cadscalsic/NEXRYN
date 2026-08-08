"""Authoritative integrity contract for engineering conclusions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


_MISSING_VALUES = {None, "", "Not Available", "NOT_AVAILABLE", "NOT_PRODUCED"}
_FINALIZED_TRANSITION = "ENGINEERING_CONCLUSION_FINALIZED"
_EVALUATED_TRANSITION = "ENGINEERING_CONCLUSION_INTEGRITY_EVALUATED"
_BOUND_TRANSITION = "ENGINEERING_CONCLUSION_BOUND_TO_CANONICAL_REPORT"
_LIFECYCLE_ORDER = [
    _FINALIZED_TRANSITION,
    _EVALUATED_TRANSITION,
    _BOUND_TRANSITION,
]
STABLE_SEMANTIC_FIELDS = [
    "conclusion_state",
    "failure_reason",
    "root_cause",
    "recommended_action",
    "responsible_area",
    "next_gate",
    "conclusion_source_stage",
    "conclusion_run_id",
    "authoritative_run_id",
    "authoritative_execution_plan_id",
    "conclusion_task_id",
    "canonical_raw_result_id",
    "engineering_conclusion_integrity_state",
]


def _first_meaningful(*values: Any, default: Any = None) -> Any:
    for value in values:
        if value not in _MISSING_VALUES and value != {} and value != []:
            return value
    return default


def _first_dict(mapping: dict[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        value = mapping.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _stable_fingerprint(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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


def _canonical_payload(conclusion: dict[str, Any]) -> dict[str, Any]:
    return {field: conclusion.get(field) for field in STABLE_SEMANTIC_FIELDS}


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
                "current_open_decision": "WAITING_RAW_RESULT_PROVENANCE_REPAIR",
                "next_decision_gate": "repair_raw_validation_result_identity",
                "current_bottleneck": "raw_validation_result_provenance",
                "failure_reason": "none",
                "root_cause": "RAW_RESULT_NOT_APPLICABLE",
                "responsible_component": "VALIDATION_EXECUTION_PIPELINE",
                "next_task": "repair_raw_validation_result_identity_without_evidence_evaluation",
                "engineering_priority": "HIGH",
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
        if raw_id is not None and str(raw_id).strip().upper() not in {
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
            default="PERSISTENCE_NOT_APPLICABLE",
        )
        normalized["persistence_integrity"] = _first_meaningful(
            normalized.get("persistence_integrity"),
            default="NOT_APPLICABLE",
        )
        normalized["emission_integrity"] = _first_meaningful(
            normalized.get("emission_integrity"),
            default="EMISSION_VERIFIED",
        )
        normalized["persistence_matches_emission"] = _first_meaningful(
            normalized.get("persistence_matches_emission"),
            default="NOT_APPLICABLE",
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
            f"engineering_conclusion_{_stable_fingerprint(_canonical_payload(normalized))[:16]}",
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
        normalized["post_reconciliation_fingerprint"] = _stable_fingerprint(
            _canonical_payload(normalized)
        )
        normalized["pre_reconciliation_fingerprint"] = _first_meaningful(
            supplied_pre_fingerprint,
            normalized["post_reconciliation_fingerprint"],
        )
        normalized["conclusion_fingerprint"] = normalized[
            "post_reconciliation_fingerprint"
        ]
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

    def compare_semantic_payloads(
        self,
        expected: dict[str, Any],
        observed: dict[str, Any],
    ) -> dict[str, Any]:
        expected_payload = self.stable_payload(expected)
        observed_payload = self.stable_payload(observed)
        mismatches = []
        for field in STABLE_SEMANTIC_FIELDS:
            expected_value = expected_payload.get(field)
            observed_value = observed_payload.get(field)
            if self._format_insensitive_value(expected_value) != (
                self._format_insensitive_value(observed_value)
            ):
                mismatches.append({
                    "field": field,
                    "expected_value": expected_value,
                    "observed_value": observed_value,
                })
        return {
            "comparison_state": (
                "SEMANTIC_PAYLOAD_MATCH"
                if not mismatches
                else "SEMANTIC_PAYLOAD_MISMATCH"
            ),
            "mismatch_count": len(mismatches),
            "mismatches": mismatches,
            "expected_fingerprint": _stable_fingerprint(expected_payload),
            "observed_fingerprint": _stable_fingerprint(observed_payload),
        }

    def persist_conclusion(
        self,
        conclusion: dict[str, Any],
        artifact_path: str | Path,
    ) -> dict[str, Any]:
        path = Path(artifact_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        normalized = self.normalize(conclusion)
        payload = self.stable_payload(normalized)
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return {
            "persistence_applicability": "PERSISTENCE_APPLICABLE",
            "persistence_integrity": "VERIFIED",
            "artifact_path": str(path),
            "conclusion_fingerprint": _stable_fingerprint(payload),
        }

    def read_persisted_conclusion(self, artifact_path: str | Path) -> dict[str, Any]:
        path = Path(artifact_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        return self.normalize(payload)

    def persistence_emission_parity(
        self,
        persisted: dict[str, Any] | None,
        emitted: dict[str, Any],
    ) -> dict[str, Any]:
        if persisted is None:
            return {
                "persistence_applicability": "PERSISTENCE_NOT_APPLICABLE",
                "persistence_integrity": "NOT_APPLICABLE",
                "emission_integrity": "VERIFIED",
                "persistence_matches_emission": "NOT_APPLICABLE",
                "mismatch_count": 0,
                "mismatches": [],
            }
        comparison = self.compare_semantic_payloads(persisted, emitted)
        matches = comparison["comparison_state"] == "SEMANTIC_PAYLOAD_MATCH"
        return {
            "persistence_applicability": "PERSISTENCE_APPLICABLE",
            "persistence_integrity": "VERIFIED" if matches else "FAILED",
            "emission_integrity": "VERIFIED",
            "persistence_matches_emission": matches,
            "mismatch_count": comparison["mismatch_count"],
            "mismatches": comparison["mismatches"],
            "persisted_fingerprint": comparison["expected_fingerprint"],
            "emitted_fingerprint": comparison["observed_fingerprint"],
        }

    def _format_insensitive_value(self, value: Any) -> Any:
        if isinstance(value, str):
            return " ".join(value.strip().split())
        return value


engineering_conclusion_integrity_evaluator = EngineeringConclusionIntegrityEvaluator()
