from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


class ExecutionFeedbackEngine:
    """Transform execution results into non-authoritative learning signals."""

    system_name = "execution_feedback_engine"
    schema_version = "1.0"

    def feedback(
        self,
        *,
        execution_result: dict[str, Any] | None = None,
        residual_report: dict[str, Any] | None = None,
        repair_report: dict[str, Any] | None = None,
        adaptation_report: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = execution_result if isinstance(execution_result, dict) else {}
        residual = residual_report if isinstance(residual_report, dict) else {}
        repair = repair_report if isinstance(repair_report, dict) else {}
        adaptation = adaptation_report if isinstance(adaptation_report, dict) else {}
        success = (
            result.get("validation_success") is True
            and residual.get("residual_count", 0) == 0
        )
        return {
            "knowledge_feedback": (
                "execution_success" if success else "execution_requires_repair"
            ),
            "truth_updates": (
                ["program_validated"]
                if result.get("validation_success")
                else ["program_blocked"]
            ),
            "hypothesis_updates": (
                ["increase_execution_confidence"]
                if success
                else ["attach_residual_evidence"]
            ),
            "execution_improvements": self._improvements(
                residual,
                repair,
                adaptation,
            ),
            "execution_feedback": "AVAILABLE",
            "knowledge_feedback_operational": True,
        }

    def process_production_outcome(
        self,
        production_outcome: Mapping[str, Any] | None,
        *,
        storage_root: str | Path | None = None,
        current_run_id: str | None = None,
        evaluation_result: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        outcome = dict(production_outcome or {})
        if outcome.get("execution_state") != "PRODUCTION_EXECUTED":
            return self._feedback_blocked(
                outcome,
                "NO_PRODUCTION_OUTCOME",
                feedback_level="F0_NOT_REACHED",
            )

        receipt = (
            dict(outcome.get("execution_receipt"))
            if isinstance(outcome.get("execution_receipt"), Mapping)
            else {}
        )
        receipt_check = self._validate_receipt(receipt, outcome, current_run_id)
        if receipt_check["receipt_valid"] is not True:
            return self._feedback_blocked(
                outcome,
                receipt_check["denial_reason"],
                receipt_check=receipt_check,
                feedback_level="F1_BLOCKED",
            )

        evaluation = self._evaluate_outcome(outcome, evaluation_result)
        evidence_candidate = self._evidence_candidate(outcome, evaluation)
        experience_record = self._experience_record(outcome, evaluation)
        performance_history = self._performance_history(outcome, evaluation)
        persistence = self._persist_feedback_records(
            storage_root=storage_root,
            outcome=outcome,
            evidence_candidate=evidence_candidate,
            experience_record=experience_record,
            performance_history=performance_history,
        )
        future_retrieval = self._future_retrieval_observation(
            storage_root=storage_root,
            experience_record=experience_record,
        )

        return {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "feedback_state": "PRODUCTION_OUTCOME_FEEDBACK_RECORDED",
            "feedback_level": (
                "F4"
                if future_retrieval["future_retrieval_state"]
                == "PRIOR_OUTCOME_HISTORY_RETRIEVABLE"
                else "F3"
                if persistence["persistence_state"] == "PERSISTED"
                else "F2"
            ),
            "outcome_identity_contract": self._outcome_identity(outcome),
            "outcome_evaluation": evaluation,
            "evidence_candidate": evidence_candidate,
            "accepted_evidence": {
                "accepted_evidence_state": "NOT_ACCEPTED_BY_OUTCOME_FEEDBACK",
                "authority": "NONE",
            },
            "experience_record": experience_record,
            "performance_history": performance_history,
            "persistence": persistence,
            "future_retrieval": future_retrieval,
            "receipt_check": receipt_check,
            "authority": {
                "execution": "NONE",
                "evidence": "EVIDENCE_INPUT",
                "truth": "NONE",
                "learning": "LEARNING_INPUT",
                "budget": "NONE",
            },
            "execution_receipt_is_execution_token": False,
            "experience_is_execution_token": False,
            "evidence_candidate_is_accepted_evidence": False,
            "successful_outcome_grants_future_execution": False,
            "reusable_execution_authority": False,
        }

    def _improvements(
        self,
        residual: dict[str, Any],
        repair: dict[str, Any],
        adaptation: dict[str, Any],
    ) -> list[str]:
        improvements = []
        if residual.get("missing_primitives"):
            improvements.append("learn_missing_primitives")
        if repair.get("generated_repairs"):
            improvements.append("reuse_localized_repairs")
        if adaptation.get("execution_adaptations"):
            improvements.append("prefer_adapted_program_ordering")
        return improvements or ["preserve_successful_program"]

    def _validate_receipt(
        self,
        receipt: Mapping[str, Any],
        outcome: Mapping[str, Any],
        current_run_id: str | None,
    ) -> dict[str, Any]:
        if not receipt:
            return {"receipt_valid": False, "denial_reason": "EXECUTION_RECEIPT_MISSING"}
        expected = self._receipt_id(receipt)
        if receipt.get("receipt_id") != expected:
            return {
                "receipt_valid": False,
                "denial_reason": "EXECUTION_RECEIPT_ID_MISMATCH",
                "expected_receipt_id": expected,
            }
        if current_run_id and str(receipt.get("run_id")) != str(current_run_id):
            return {
                "receipt_valid": False,
                "denial_reason": "HISTORICAL_RECEIPT_NEW_RUN_REPLAY",
            }
        checks = {
            "run_id_bound": receipt.get("run_id") == outcome.get("run_id"),
            "grant_id_bound": receipt.get("execution_grant_id")
            == outcome.get("grant_id"),
            "candidate_id_bound": receipt.get("candidate_id")
            == outcome.get("candidate_id"),
            "learned_object_id_bound": receipt.get("learned_object_id")
            == outcome.get("learned_object_id"),
            "operation_bound": receipt.get("operation") == outcome.get("operation"),
            "outcome_ref_bound": receipt.get("outcome_ref")
            == outcome.get("execution_result_id"),
            "receipt_has_no_execution_authority": receipt.get("authority") == "NONE",
            "receipt_not_reusable_authority": receipt.get(
                "reusable_execution_authority"
            )
            is False,
        }
        failed = [key for key, value in checks.items() if value is not True]
        return {
            "receipt_valid": not failed,
            "denial_reason": failed[0].upper() if failed else "NONE",
            "checks": checks,
        }

    def _evaluate_outcome(
        self,
        outcome: Mapping[str, Any],
        evaluation_result: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        supplied = dict(evaluation_result or {})
        if supplied.get("governance_rejected") is True:
            outcome_class = "GOVERNANCE_REJECTED"
        elif supplied.get("outcome_class"):
            outcome_class = str(supplied["outcome_class"])
        elif outcome.get("real_execution_performed") is not True:
            outcome_class = "INVALID_OUTCOME"
        elif outcome.get("result"):
            outcome_class = "SUCCESS"
        else:
            outcome_class = "UNKNOWN"
        return {
            "evaluation_id": self._stable_id(
                "production_outcome_evaluation",
                {
                    "execution_result_id": outcome.get("execution_result_id"),
                    "outcome_class": outcome_class,
                    "operation": outcome.get("operation"),
                },
            ),
            "execution_result_id": outcome.get("execution_result_id"),
            "outcome_class": outcome_class,
            "success": outcome_class in {"SUCCESS", "PARTIAL_SUCCESS"},
            "evaluation_authority": "OBSERVATION_ONLY",
            "truth_authority": "NONE",
            "execution_authority": "NONE",
            "learning_value": (
                "LEARNING_INPUT"
                if outcome_class in {"SUCCESS", "PARTIAL_SUCCESS", "FAILURE"}
                else "NONE"
            ),
            "details": supplied,
        }

    def _evidence_candidate(
        self,
        outcome: Mapping[str, Any],
        evaluation: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "evidence_candidate_id": self._stable_id(
                "production_outcome_evidence_candidate",
                {
                    "execution_result_id": outcome.get("execution_result_id"),
                    "evaluation_id": evaluation.get("evaluation_id"),
                    "learned_object_id": outcome.get("learned_object_id"),
                },
            ),
            "source_execution_result_id": outcome.get("execution_result_id"),
            "source_execution_receipt_id": outcome.get("execution_receipt", {}).get(
                "receipt_id"
            ),
            "learned_object_id": outcome.get("learned_object_id"),
            "candidate_id": outcome.get("candidate_id"),
            "run_id": outcome.get("run_id"),
            "operation": outcome.get("operation"),
            "outcome_class": evaluation.get("outcome_class"),
            "authority": "EVIDENCE_INPUT",
            "accepted_evidence_state": "NOT_ACCEPTED",
            "truth_authority": "NONE",
            "execution_authority": "NONE",
        }

    def _experience_record(
        self,
        outcome: Mapping[str, Any],
        evaluation: Mapping[str, Any],
    ) -> dict[str, Any]:
        provenance = (
            outcome.get("outcome_provenance")
            if isinstance(outcome.get("outcome_provenance"), Mapping)
            else {}
        )
        result = outcome.get("result") if isinstance(outcome.get("result"), Mapping) else {}
        executable_payload = (
            dict(outcome.get("executable_payload"))
            if isinstance(outcome.get("executable_payload"), Mapping)
            else {}
        )
        executable_steps = executable_payload.get("steps")
        executable_steps = executable_steps if isinstance(executable_steps, list) else []
        first_step = executable_steps[0] if executable_steps and isinstance(executable_steps[0], Mapping) else {}
        executable_parameters = (
            dict(first_step.get("parameters"))
            if isinstance(first_step.get("parameters"), Mapping)
            else {}
        )
        parameter_provenance = (
            dict(first_step.get("parameter_provenance"))
            if isinstance(first_step.get("parameter_provenance"), Mapping)
            else {}
        )
        return {
            "experience_id": self._stable_id(
                "experience",
                {
                    "execution_result_id": outcome.get("execution_result_id"),
                    "receipt_id": outcome.get("execution_receipt", {}).get(
                        "receipt_id"
                    ),
                },
            ),
            "source": "production_execution_outcome",
            "run_id": outcome.get("run_id"),
            "execution_result_id": outcome.get("execution_result_id"),
            "execution_receipt_id": outcome.get("execution_receipt", {}).get(
                "receipt_id"
            ),
            "execution_grant_id": outcome.get("grant_id"),
            "candidate_id": outcome.get("candidate_id"),
            "learned_object_id": outcome.get("learned_object_id"),
            "operation": outcome.get("operation"),
            "canonical_provenance": provenance.get("retrieval_provenance") or {},
            "evaluation_result": {
                "success": evaluation.get("success"),
                "outcome_class": evaluation.get("outcome_class"),
                "evaluation_id": evaluation.get("evaluation_id"),
            },
            "winner_hypothesis": {
                "type": outcome.get("operation"),
                "operation": outcome.get("operation"),
                "parameters": executable_parameters,
                "parameter_provenance": parameter_provenance,
                "executable_payload": executable_payload,
                "confidence": 1.0 if evaluation.get("success") else 0.0,
                "description": (
                    "governed production outcome for "
                    f"{outcome.get('operation')}"
                ),
                "source_execution_result_id": outcome.get("execution_result_id"),
                "source_experience_authority": "LEARNING_INPUT",
                "execution_authority": "NONE",
            },
            "semantic_graph": {
                "concept_nodes": [
                    {
                        "concept": outcome.get("operation"),
                        "source": "production_outcome_feedback",
                    }
                ]
            },
            "program": {
                "operation": outcome.get("operation"),
                "steps": [
                    {
                        "operation": step.get("operation"),
                        "parameters": (
                            dict(step.get("parameters"))
                            if isinstance(step.get("parameters"), Mapping)
                            else {}
                        ),
                        "parameter_provenance": (
                            dict(step.get("parameter_provenance"))
                            if isinstance(step.get("parameter_provenance"), Mapping)
                            else {}
                        ),
                    }
                    for step in executable_steps
                    if isinstance(step, Mapping) and step.get("operation")
                ],
                "executable_payload_fingerprint": executable_payload.get(
                    "executable_payload_fingerprint"
                ),
                "authority": "LEARNING_DATA",
                "execution_authority": "NONE",
            },
            "execution_plan": {
                "nodes": [
                    {
                        "operation": step.get("operation"),
                        "parameters": (
                            dict(step.get("parameters"))
                            if isinstance(step.get("parameters"), Mapping)
                            else {}
                        ),
                    }
                    for step in executable_steps
                    if isinstance(step, Mapping) and step.get("operation")
                ]
                or [{"operation": outcome.get("operation")}],
            },
            "execution_signature": str(outcome.get("operation") or ""),
            "program_signature": str(outcome.get("operation") or ""),
            "performance_score": 1.0 if evaluation.get("success") else 0.0,
            "success_rate": 1.0 if evaluation.get("success") else 0.0,
            "result": dict(result),
            "authority": "LEARNING_INPUT",
            "execution_authority": "NONE",
            "reusable_execution_authority": False,
            "timestamp": str(datetime.utcnow()),
        }

    def _performance_history(
        self,
        outcome: Mapping[str, Any],
        evaluation: Mapping[str, Any],
    ) -> dict[str, Any]:
        success = evaluation.get("success") is True
        return {
            "performance_history_id": self._stable_id(
                "learned_object_performance_history",
                {
                    "learned_object_id": outcome.get("learned_object_id"),
                    "execution_result_id": outcome.get("execution_result_id"),
                },
            ),
            "learned_object_id": outcome.get("learned_object_id"),
            "execution_count": 1,
            "success_count": 1 if success else 0,
            "failure_count": 0 if success else 1,
            "evaluated_outcomes": [outcome.get("execution_result_id")],
            "evidence_refs": [],
            "source_runs": [outcome.get("run_id")],
            "authority": "LEARNING_INPUT",
            "execution_authority": "NONE",
            "reusable_execution_authority": False,
        }

    def _persist_feedback_records(
        self,
        *,
        storage_root: str | Path | None,
        outcome: Mapping[str, Any],
        evidence_candidate: Mapping[str, Any],
        experience_record: Mapping[str, Any],
        performance_history: Mapping[str, Any],
    ) -> dict[str, Any]:
        if storage_root is None:
            return {
                "persistence_state": "NOT_REQUESTED",
                "records_persisted": 0,
                "idempotent_replay": False,
            }
        root = Path(storage_root)
        records = [
            (
                root / "production_outcomes" / f"{outcome['execution_result_id']}.json",
                dict(outcome),
            ),
            (
                root
                / "evidence_candidates"
                / f"{evidence_candidate['evidence_candidate_id']}.json",
                dict(evidence_candidate),
            ),
            (
                root / "experiences" / f"{experience_record['experience_id']}.json",
                dict(experience_record),
            ),
            (
                root
                / "learned_object_performance"
                / f"{performance_history['performance_history_id']}.json",
                dict(performance_history),
            ),
        ]
        duplicates = 0
        for path, payload in records:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                duplicates += 1
                continue
            path.write_text(
                json.dumps(payload, indent=2, sort_keys=True, default=str),
                encoding="utf-8",
            )
        return {
            "persistence_state": "PERSISTED",
            "records_persisted": len(records) - duplicates,
            "duplicate_records_suppressed": duplicates,
            "idempotent_replay": duplicates == len(records),
            "storage_root": str(root),
            "experience_path": str(records[2][0]),
        }

    def _future_retrieval_observation(
        self,
        *,
        storage_root: str | Path | None,
        experience_record: Mapping[str, Any],
    ) -> dict[str, Any]:
        if storage_root is None:
            return {
                "future_retrieval_state": "NOT_OBSERVED",
                "retrievable_experience_id": experience_record.get("experience_id"),
                "authority": "NONE",
            }
        from runtime.adaptive_reuse.experience_index import ExperienceIndex

        experiences = ExperienceIndex(storage_root).load()
        found = any(
            item.experience_id == experience_record.get("experience_id")
            for item in experiences
        )
        return {
            "future_retrieval_state": (
                "PRIOR_OUTCOME_HISTORY_RETRIEVABLE"
                if found
                else "NOT_RETRIEVABLE"
            ),
            "retrievable_experience_id": (
                experience_record.get("experience_id") if found else None
            ),
            "authority": "NONE",
        }

    def _outcome_identity(self, outcome: Mapping[str, Any]) -> dict[str, Any]:
        fields = {
            "run_id": outcome.get("run_id"),
            "execution_receipt_id": outcome.get("execution_receipt", {}).get(
                "receipt_id"
            ),
            "execution_grant_id": outcome.get("grant_id"),
            "candidate_id": outcome.get("candidate_id"),
            "learned_object_id": outcome.get("learned_object_id"),
            "operation": outcome.get("operation"),
            "canonical_provenance": outcome.get("outcome_provenance", {}).get(
                "retrieval_provenance"
            ),
            "budget_admission_context": outcome.get("budget_context"),
            "execution_result_id": outcome.get("execution_result_id"),
            "evaluation_result": outcome.get("result"),
        }
        return {
            "outcome_identity_id": self._stable_id(
                "production_outcome_identity",
                fields,
            ),
            "fields": fields,
            "identity_complete": all(self._present(value) for value in fields.values()),
        }

    def _feedback_blocked(
        self,
        outcome: Mapping[str, Any],
        reason: str,
        *,
        receipt_check: Mapping[str, Any] | None = None,
        feedback_level: str,
    ) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "feedback_state": "PRODUCTION_OUTCOME_FEEDBACK_BLOCKED",
            "feedback_level": feedback_level,
            "denial_reason": reason,
            "execution_result_id": outcome.get("execution_result_id"),
            "receipt_check": dict(receipt_check or {}),
            "authority": {
                "execution": "NONE",
                "evidence": "NONE",
                "truth": "NONE",
                "learning": "NONE",
                "budget": "NONE",
            },
            "reusable_execution_authority": False,
        }

    def _receipt_id(self, receipt: Mapping[str, Any]) -> str:
        return self._stable_id(
            "learned_object_execution_receipt",
            {
                "run_id": receipt.get("run_id"),
                "execution_grant_id": receipt.get("execution_grant_id"),
                "candidate_id": receipt.get("candidate_id"),
                "learned_object_id": receipt.get("learned_object_id"),
                "operation": receipt.get("operation"),
                "outcome_ref": receipt.get("outcome_ref"),
                "consumption_state": receipt.get("consumption_state"),
            },
        )

    def _present(self, value: Any) -> bool:
        return value is not None and value != "" and value != {}

    def _stable_id(self, prefix: str, payload: Any) -> str:
        text = json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=True,
            default=str,
            separators=(",", ":"),
        )
        return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


execution_feedback_engine = ExecutionFeedbackEngine()


__all__ = ["ExecutionFeedbackEngine", "execution_feedback_engine"]
