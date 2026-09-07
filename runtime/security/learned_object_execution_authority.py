from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime
from typing import Any, Mapping


REQUIRED_PRECONDITIONS = [
    "learned_object_provenance_valid",
    "candidate_materialized",
    "sandbox_validation_passed",
    "evidence_sufficient_for_execution_use",
    "candidate_qualified",
    "arena_selection_valid",
    "no_contradiction_or_rejection_gate_active",
    "execution_scope_permitted",
    "runtime_budget_available",
    "governance_constraints_satisfied",
]


class LearnedObjectExecutionGrantAuthority:
    """Issue and verify run-scoped learned-object execution grants."""

    schema_version = "1.0"
    system_name = "learned_object_execution_grant_authority"

    def contract(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "contract_owner": self.system_name,
            "grant_object": "LearnedObjectExecutionGrant",
            "authority": "EXECUTION",
            "scope": "CURRENT_RUN_ONLY",
            "persistent": False,
            "inheritable": False,
            "promotable": False,
            "transferable": False,
            "revocable": True,
            "wildcard_candidate_grant_allowed": False,
            "historical_grant_reuse_allowed": False,
            "required_bindings": [
                "run_id",
                "candidate_id",
                "learned_object_id",
                "canonical_provenance",
                "arena_selection_identity",
                "validation_identity",
                "qualification_identity",
                "execution_operation_scope",
                "budget_admission_context",
                "grant_issuer",
                "grant_timestamp",
                "grant_lifecycle_identity",
            ],
            "required_preconditions": list(REQUIRED_PRECONDITIONS),
        }

    def issue_grant(
        self,
        *,
        run_id: str,
        candidate: Mapping[str, Any],
        learned_object: Mapping[str, Any],
        arena_selection: Mapping[str, Any],
        validation: Mapping[str, Any],
        qualification: Mapping[str, Any],
        execution_scope: Mapping[str, Any],
        budget_admission: Mapping[str, Any],
        grant_issuer: str = "learned_object_execution_grant_authority",
    ) -> dict[str, Any]:
        inputs = {
            "run_id": run_id,
            "candidate": dict(candidate or {}),
            "learned_object": dict(learned_object or {}),
            "arena_selection": dict(arena_selection or {}),
            "validation": dict(validation or {}),
            "qualification": dict(qualification or {}),
            "execution_scope": dict(execution_scope or {}),
            "budget_admission": dict(budget_admission or {}),
            "grant_issuer": grant_issuer,
        }
        preconditions = self.evaluate_preconditions(**inputs)
        if preconditions["precondition_state"] != "SATISFIED":
            return self._blocked_grant(inputs, preconditions)

        timestamp = str(datetime.utcnow())
        payload = self._grant_payload(inputs, timestamp)
        grant_id = self._stable_id("learned_object_execution_grant", payload)
        grant = {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "grant_id": grant_id,
            "grant_state": "ISSUED",
            "authority": "EXECUTION",
            "scope": "CURRENT_RUN_ONLY",
            "persistent": False,
            "inheritable": False,
            "promotable": False,
            "transferable": False,
            "revocable": True,
            "revoked": False,
            "run_id": str(run_id),
            "candidate_id": str(candidate.get("candidate_id")),
            "learned_object_id": str(learned_object.get("learned_object_id")),
            "candidate_fingerprint": candidate.get("candidate_fingerprint"),
            "program_fingerprint": (
                execution_scope.get("program_fingerprint")
                or candidate.get("program_fingerprint")
            ),
            "canonical_provenance": deepcopy(
                learned_object.get("canonical_provenance")
                or candidate.get("canonical_provenance")
                or {}
            ),
            "arena_selection_identity": self._identity(
                arena_selection,
                "arena_selection",
            ),
            "validation_identity": self._identity(validation, "validation"),
            "qualification_identity": self._identity(
                qualification,
                "qualification",
            ),
            "execution_operation_scope": deepcopy(dict(execution_scope)),
            "budget_admission_context": deepcopy(dict(budget_admission)),
            "grant_issuer": str(grant_issuer),
            "grant_timestamp": timestamp,
            "grant_lifecycle_identity": self._stable_id(
                "grant_lifecycle",
                {
                    "grant_id": grant_id,
                    "run_id": run_id,
                    "candidate_id": candidate.get("candidate_id"),
                    "learned_object_id": learned_object.get("learned_object_id"),
                    "grant_issuer": grant_issuer,
                },
            ),
            "preconditions": preconditions,
            "grant_fingerprint": "",
        }
        grant["grant_fingerprint"] = self._fingerprint(grant)
        return grant

    def validate_for_consumption(
        self,
        grant: Mapping[str, Any] | None,
        *,
        run_id: str,
        candidate_id: str,
        learned_object_id: str,
        requested_operation: str,
        budget_admission: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(grant, Mapping):
            return self._denied("GRANT_MISSING")
        if grant.get("revoked") is True:
            return self._denied("GRANT_REVOKED")
        if grant.get("grant_state") == "CONSUMED":
            return self._denied("DENIED_GRANT_ALREADY_CONSUMED")
        if grant.get("grant_state") != "ISSUED":
            return self._denied(str(grant.get("grant_state") or "GRANT_NOT_ISSUED"))
        if grant.get("persistent") is True:
            return self._denied("PERSISTED_HISTORICAL_GRANT_FORBIDDEN")
        if self._fingerprint(grant) != grant.get("grant_fingerprint"):
            return self._denied("GRANT_FINGERPRINT_MISMATCH")
        checks = {
            "run_id": str(run_id),
            "candidate_id": str(candidate_id),
            "learned_object_id": str(learned_object_id),
        }
        for key, expected in checks.items():
            if str(grant.get(key)) != expected:
                return self._denied(f"{key.upper()}_SCOPE_MISMATCH")
        allowed_operation = (
            grant.get("execution_operation_scope", {}).get("operation")
            if isinstance(grant.get("execution_operation_scope"), Mapping)
            else None
        )
        if allowed_operation and str(allowed_operation) != str(requested_operation):
            return self._denied("EXECUTION_SCOPE_EXCEEDED")
        supplied_budget = dict(budget_admission or {})
        budget_run_id = supplied_budget.get("run_id") or supplied_budget.get(
            "execution_id"
        )
        if budget_run_id is not None and str(budget_run_id) != str(run_id):
            return self._denied("BUDGET_RUN_SCOPE_MISMATCH")
        grant_budget = (
            grant.get("budget_admission_context", {})
            if isinstance(grant.get("budget_admission_context"), Mapping)
            else {}
        )
        grant_budget_run_id = grant_budget.get("run_id") or grant_budget.get(
            "execution_id"
        )
        if grant_budget_run_id is not None and str(grant_budget_run_id) != str(run_id):
            return self._denied("BUDGET_RUN_SCOPE_MISMATCH")
        if not self._budget_admitted(
            supplied_budget,
            grant.get("budget_admission_context", {}),
        ):
            return self._denied("BUDGET_ADMISSION_GAP")
        return {
            "consumption_state": "AUTHORIZED_FOR_PRODUCTION_EXECUTION",
            "production_execution_authorized": True,
            "grant_id": grant.get("grant_id"),
            "run_id": str(run_id),
            "candidate_id": str(candidate_id),
            "learned_object_id": str(learned_object_id),
            "requested_operation": str(requested_operation),
            "authority": "EXECUTION",
            "budget_authority_composed": True,
        }

    def consume_grant(self, grant: Mapping[str, Any]) -> dict[str, Any]:
        consumed = deepcopy(dict(grant or {}))
        consumed["grant_state"] = "CONSUMED"
        consumed["grant_consumed"] = True
        consumed["consumed_at"] = str(datetime.utcnow())
        consumed["persistent"] = False
        consumed["inheritable"] = False
        consumed["promotable"] = False
        consumed["transferable"] = False
        consumed["reusable_execution_authority"] = False
        consumed["grant_fingerprint"] = self._fingerprint(consumed)
        if isinstance(grant, dict):
            grant.clear()
            grant.update(consumed)
        return consumed

    def revoke(self, grant: Mapping[str, Any]) -> dict[str, Any]:
        revoked = deepcopy(dict(grant or {}))
        revoked["revoked"] = True
        revoked["grant_state"] = "REVOKED"
        revoked["revoked_at"] = str(datetime.utcnow())
        revoked["grant_fingerprint"] = self._fingerprint(revoked)
        return revoked

    def evaluate_preconditions(
        self,
        *,
        run_id: str,
        candidate: Mapping[str, Any],
        learned_object: Mapping[str, Any],
        arena_selection: Mapping[str, Any],
        validation: Mapping[str, Any],
        qualification: Mapping[str, Any],
        execution_scope: Mapping[str, Any],
        budget_admission: Mapping[str, Any],
        grant_issuer: str,
    ) -> dict[str, Any]:
        checks = {
            "learned_object_provenance_valid": bool(
                learned_object.get("learned_object_id")
                and learned_object.get("canonical_provenance")
            ),
            "candidate_materialized": bool(
                candidate.get("candidate_id")
                and candidate.get("learned_object_id")
                == learned_object.get("learned_object_id")
            ),
            "sandbox_validation_passed": bool(
                validation.get("validation_state") in {
                    "PASSED",
                    "SANDBOX_VALIDATION_PASSED",
                    "ACCEPTED",
                }
                or validation.get("validation_success") is True
            ),
            "evidence_sufficient_for_execution_use": bool(
                validation.get("evidence_sufficient_for_execution_use") is True
                or validation.get("evidence_acceptance_state") == "ACCEPTED"
            ),
            "candidate_qualified": bool(
                qualification.get("qualification_state") in {
                    "QUALIFIED",
                    "EXECUTION_ELIGIBLE",
                }
            ),
            "arena_selection_valid": bool(
                arena_selection.get("selection_state")
                in {"WINNER_SELECTED", "EXECUTION_ELIGIBLE"}
                and arena_selection.get("selected_candidate_id")
                == candidate.get("candidate_id")
            ),
            "no_contradiction_or_rejection_gate_active": not bool(
                validation.get("contradiction_gate_active")
                or validation.get("rejection_gate_active")
                or qualification.get("contradiction_gate_active")
                or qualification.get("rejection_gate_active")
            ),
            "execution_scope_permitted": bool(
                execution_scope.get("operation")
                and execution_scope.get("operation")
                in set(candidate.get("permitted_operations") or [])
            ),
            "runtime_budget_available": self._budget_admitted(
                dict(budget_admission or {}),
                {},
            ),
            "governance_constraints_satisfied": bool(
                qualification.get("governance_constraints_satisfied") is True
                and grant_issuer
                and run_id
            ),
        }
        missing = [
            key for key in REQUIRED_PRECONDITIONS if checks.get(key) is not True
        ]
        return {
            "precondition_state": "SATISFIED" if not missing else "BLOCKED",
            "checks": checks,
            "missing_preconditions": missing,
            "actual_canonical_predicate": " AND ".join(REQUIRED_PRECONDITIONS),
        }

    def _blocked_grant(
        self,
        inputs: Mapping[str, Any],
        preconditions: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "grant_state": "BLOCKED",
            "authority": "NONE",
            "run_id": str(inputs.get("run_id") or "UNKNOWN"),
            "candidate_id": inputs.get("candidate", {}).get("candidate_id"),
            "learned_object_id": inputs.get("learned_object", {}).get(
                "learned_object_id"
            ),
            "preconditions": dict(preconditions),
            "block_reason": preconditions.get("missing_preconditions", []),
            "production_execution_authorized": False,
        }

    def _grant_payload(
        self,
        inputs: Mapping[str, Any],
        timestamp: str,
    ) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": inputs["run_id"],
            "candidate_id": inputs["candidate"].get("candidate_id"),
            "learned_object_id": inputs["learned_object"].get("learned_object_id"),
            "arena_selection_identity": self._identity(
                inputs["arena_selection"],
                "arena_selection",
            ),
            "validation_identity": self._identity(
                inputs["validation"],
                "validation",
            ),
            "qualification_identity": self._identity(
                inputs["qualification"],
                "qualification",
            ),
            "execution_operation_scope": inputs["execution_scope"],
            "budget_admission_context": inputs["budget_admission"],
            "grant_issuer": inputs["grant_issuer"],
            "grant_timestamp": timestamp,
        }

    def _identity(self, value: Mapping[str, Any], prefix: str) -> str:
        for key in (
            f"{prefix}_id",
            "selection_id",
            "validation_id",
            "qualification_id",
            "arena_id",
            "id",
        ):
            if value.get(key):
                return str(value[key])
        return self._stable_id(prefix, dict(value or {}))

    def _budget_admitted(
        self,
        supplied: Mapping[str, Any],
        grant_budget: Mapping[str, Any],
    ) -> bool:
        budget = dict(supplied or grant_budget or {})
        state = str(
            budget.get("runtime_budget_state")
            or budget.get("budget_admission_state")
            or budget.get("route_budget_enforcement_state")
            or ""
        )
        if state not in {
            "RUNTIME_BUDGET_FINALIZED",
            "ROUTE_BUDGET_ADMITTED",
            "BUDGET_ADMITTED",
        }:
            return False
        if budget.get("budget_state") in {"STALE", "EXPIRED"}:
            return False
        if budget.get("stale") is True:
            return False
        if budget.get("realized_overrun_state") == "REALIZED_OVERRUN":
            return False
        if budget.get("violation_reason") not in {None, "", "NONE"}:
            return False
        return True

    def _denied(self, reason: str) -> dict[str, Any]:
        return {
            "consumption_state": "DENIED",
            "production_execution_authorized": False,
            "denial_reason": reason,
            "authority": "NONE",
        }

    def _fingerprint(self, grant: Mapping[str, Any]) -> str:
        payload = dict(grant)
        payload.pop("grant_fingerprint", None)
        return self._stable_id("learned_object_execution_grant_fingerprint", payload)

    def _stable_id(self, prefix: str, payload: Any) -> str:
        text = json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=True,
            default=str,
            separators=(",", ":"),
        )
        return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


learned_object_execution_grant_authority = LearnedObjectExecutionGrantAuthority()


__all__ = [
    "LearnedObjectExecutionGrantAuthority",
    "REQUIRED_PRECONDITIONS",
    "learned_object_execution_grant_authority",
]
