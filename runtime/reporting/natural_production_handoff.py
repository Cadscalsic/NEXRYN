"""Observation-only natural production authority handoff tracing."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


PASSED_VALIDATION_STATES = {
    "PASSED",
    "SANDBOX_VALIDATION_PASSED",
    "ACCEPTED",
}
PASSED_QUALIFICATION_STATES = {"QUALIFIED", "EXECUTION_ELIGIBLE"}
SAFE_WINNER_STATES = {"WINNER_SELECTED", "EXECUTION_ELIGIBLE", "SAFE_WINNER"}
ADMITTED_BUDGET_STATES = {
    "RUNTIME_BUDGET_FINALIZED",
    "ROUTE_BUDGET_ADMITTED",
    "BUDGET_ADMITTED",
}


class NaturalProductionHandoffObserver:
    """Classify the natural candidate -> grant -> executor lifecycle."""

    system_name = "natural_production_handoff_observer"

    def build_trace(
        self,
        *,
        run_id: str | None = None,
        task_id: str | None = None,
        candidate: Mapping[str, Any] | None = None,
        materialization: Mapping[str, Any] | None = None,
        sandbox_validation: Mapping[str, Any] | None = None,
        qualification: Mapping[str, Any] | None = None,
        arena_selection: Mapping[str, Any] | None = None,
        execution_grant: Mapping[str, Any] | None = None,
        budget_admission: Mapping[str, Any] | None = None,
        production_execution: Mapping[str, Any] | None = None,
        production_outcome: Mapping[str, Any] | None = None,
        run_budget_state: str | None = None,
        synthetic_assistance_used: bool = False,
        test_fixture_used: bool = False,
        manual_grant_issuance: bool = False,
        manual_executor_invocation: bool = False,
    ) -> dict[str, Any]:
        candidate_map = dict(candidate or {})
        materialization_map = dict(materialization or {})
        validation_map = dict(sandbox_validation or {})
        qualification_map = dict(qualification or {})
        arena_map = dict(arena_selection or {})
        grant_map = dict(execution_grant or {})
        budget_map = dict(budget_admission or {})
        production_map = dict(production_execution or {})
        outcome_map = dict(production_outcome or {})

        selected_candidate = arena_map.get("selected_candidate")
        selected_candidate = selected_candidate if isinstance(selected_candidate, Mapping) else {}
        candidate_identity = self._candidate_identity(candidate_map or selected_candidate)
        selected_candidate_id = (
            arena_map.get("selected_candidate_id")
            or selected_candidate.get("candidate_id")
        )
        arena_decision = str(
            arena_map.get("selection_state")
            or arena_map.get("arena_decision")
            or "NOT_REACHED"
        )
        candidate_generated = bool(candidate_identity.get("candidate_id"))
        materialized = self._materialized(candidate_map, materialization_map)
        validation_passed = self._validation_passed(validation_map)
        qualified = self._qualified(qualification_map)
        arena_reached = bool(arena_map)
        safe_winner = (
            arena_decision in SAFE_WINNER_STATES
            and bool(selected_candidate_id)
        )
        grant_expected = safe_winner
        grant_state = str(grant_map.get("grant_state") or "NOT_REACHED")
        grant_issued = grant_state in {"ISSUED", "CONSUMED"}
        budget_expected = grant_issued
        budget_state = self._budget_state(budget_map)
        budget_admitted = budget_state in ADMITTED_BUDGET_STATES
        executor_expected = grant_issued and budget_admitted
        executor_called = bool(
            production_map.get("underlying_executor_called") is True
            or production_map.get("real_execution_performed") is True
        )
        executor_reached = executor_called
        real_execution = production_map.get("real_execution_performed") is True
        outcome_state = str(
            production_map.get("outcome_provenance_state")
            or outcome_map.get("outcome_provenance_state")
            or "OUTCOME_PROVENANCE_NOT_REACHED"
        )
        outcome_complete = outcome_state == "OUTCOME_PROVENANCE_COMPLETE"
        lineage = self._lineage_state(
            run_id=run_id,
            candidate_identity=candidate_identity,
            selected_candidate_id=selected_candidate_id,
            grant=grant_map,
            production=production_map,
        )
        contamination = any(
            [
                synthetic_assistance_used,
                test_fixture_used,
                manual_grant_issuance,
                manual_executor_invocation,
            ]
        )
        unauthorized = self._unauthorized_activity(
            arena_decision=arena_decision,
            grant_expected=grant_expected,
            grant_issued=grant_issued,
            budget_expected=budget_expected,
            budget_admitted=budget_admitted,
            executor_expected=executor_expected,
            executor_called=executor_called,
            real_execution=real_execution,
        )
        expectations = self._expectations(
            candidate_generated=candidate_generated,
            materialized=materialized,
            validation_passed=validation_passed,
            qualified=qualified,
            arena_reached=arena_reached,
            safe_winner=safe_winner,
            grant_issued=grant_issued,
            budget_admitted=budget_admitted,
            executor_called=executor_called,
            real_execution=real_execution,
            outcome_complete=outcome_complete,
        )
        reachability_gaps = [
            row["boundary"]
            for row in expectations
            if row["expected"] is True
            and row["observed"] is not True
            and row["reachability_gap"] is True
        ]
        first_block = self._first_block(
            candidate_generated=candidate_generated,
            materialized=materialized,
            validation_passed=validation_passed,
            qualified=qualified,
            qualification=qualification_map,
            arena_reached=arena_reached,
            arena_decision=arena_decision,
            safe_winner=safe_winner,
            grant_expected=grant_expected,
            grant_issued=grant_issued,
            budget_expected=budget_expected,
            budget_admitted=budget_admitted,
            executor_expected=executor_expected,
            executor_called=executor_called,
            real_execution=real_execution,
            outcome_complete=outcome_complete,
            contamination=contamination,
        )
        phase_state = self._phase_state(
            unauthorized=bool(unauthorized),
            contamination=contamination,
            natural_e7=real_execution and outcome_complete,
            reachability_gaps=reachability_gaps,
            candidate_generated=candidate_generated,
            first_block=first_block,
        )
        boundaries = {
            "candidate_generated": "PASSED" if candidate_generated else "BLOCKED",
            "materialization": self._boundary_state(candidate_generated, materialized),
            "sandbox_validation": self._boundary_state(materialized, validation_passed),
            "qualification": self._boundary_state(validation_passed, qualified),
            "arena": self._arena_boundary_state(qualified, arena_reached, arena_decision, safe_winner),
            "execution_grant": self._expected_boundary_state(grant_expected, grant_issued),
            "candidate_budget_admission": self._expected_boundary_state(budget_expected, budget_admitted),
            "production_executor": self._expected_boundary_state(executor_expected, executor_called),
            "outcome_provenance": self._expected_boundary_state(real_execution, outcome_complete),
        }
        highest_natural_level = self._highest_level(
            candidate_generated=candidate_generated,
            materialized=materialized,
            validation_passed=validation_passed,
            qualified=qualified,
            arena_reached=arena_reached,
            safe_winner=safe_winner,
            grant_issued=grant_issued,
            budget_admitted=budget_admitted,
            executor_called=executor_called,
            real_execution=real_execution,
            outcome_complete=outcome_complete,
        )
        trace = {
            "system": self.system_name,
            "trace_state": "FINAL",
            "authority": "OBSERVATION_ONLY",
            "behavioral_authority": "NONE",
            "phase_3_state": phase_state,
            "run_id": str(run_id or production_map.get("run_id") or grant_map.get("run_id") or "UNKNOWN"),
            "task_id": str(task_id or candidate_map.get("task_id") or "UNKNOWN"),
            "candidate_generated": "PASSED" if candidate_generated else "BLOCKED",
            "candidate_id": candidate_identity.get("candidate_id"),
            "candidate_source": candidate_identity.get("candidate_source"),
            "candidate_type": candidate_identity.get("candidate_type"),
            "candidate_fingerprint": candidate_identity.get("candidate_fingerprint"),
            "learned_object_id": candidate_identity.get("learned_object_id"),
            "source_program_id": candidate_identity.get("source_program_id"),
            "producer_operation_id": candidate_identity.get("producer_operation_id"),
            "materialized": "PASSED" if materialized else "NOT_REACHED",
            "materialization_id": materialization_map.get("materialization_id"),
            "sandbox_validation_reached": bool(validation_map),
            "sandbox_validation_state": self._validation_state(validation_map),
            "qualification_reached": bool(qualification_map),
            "qualification_state": self._qualification_state(qualification_map),
            "qualification_id": qualification_map.get("qualification_id"),
            "arena_reached": arena_reached,
            "arena_decision": arena_decision,
            "arena_selected_candidate_id": selected_candidate_id,
            "safe_winner_selected": safe_winner,
            "grant_boundary_reached": bool(grant_map),
            "grant_expected": grant_expected,
            "grant_state": grant_state,
            "grant_id": grant_map.get("grant_id"),
            "budget_boundary_reached": bool(budget_map),
            "candidate_budget_admission_expected": budget_expected,
            "budget_admission_state": budget_state,
            "run_budget_state": run_budget_state,
            "production_candidate_budget_admission_state": budget_state,
            "production_executor_expected": executor_expected,
            "production_executor_reached": executor_reached,
            "production_executor_called": executor_called,
            "underlying_executor_called": executor_called,
            "real_execution_performed": real_execution,
            "execution_result_id": production_map.get("execution_result_id"),
            "outcome_provenance_state": outcome_state,
            "highest_contract_proven_level": "E7",
            "highest_natural_execution_level": highest_natural_level,
            "highest_natural_runtime_level": highest_natural_level,
            "first_unreached_boundary": self._first_unreached(boundaries),
            "first_blocked_boundary": first_block,
            "blocking_state": first_block,
            "blocking_reason": self._blocking_reason(first_block, arena_decision),
            "candidate_lineage_state": lineage,
            "boundary_states": boundaries,
            "expected_vs_observed_reachability": expectations,
            "synthetic_assistance_used": bool(synthetic_assistance_used),
            "test_fixture_used": bool(test_fixture_used),
            "manual_grant_issuance": bool(manual_grant_issuance),
            "manual_executor_invocation": bool(manual_executor_invocation),
            "authority_bypass_detected": bool(unauthorized),
            "unauthorized_downstream_activity": unauthorized or "NONE",
            "reachability_gap": bool(reachability_gaps),
            "reachability_gap_boundaries": reachability_gaps,
        }
        trace["trace_id"] = self._stable_id("natural_production_handoff", trace)
        return trace

    def _candidate_identity(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), Mapping) else {}
        learned_object_id = (
            candidate.get("learned_object_id")
            or candidate.get("source_learned_object_id")
            or metadata.get("learned_object_id")
            or metadata.get("source_learned_object_id")
        )
        fingerprint = (
            candidate.get("candidate_fingerprint")
            or metadata.get("candidate_fingerprint")
            or self._stable_id("candidate_fingerprint", candidate)
            if candidate.get("candidate_id")
            else None
        )
        return {
            "candidate_id": candidate.get("candidate_id"),
            "candidate_source": candidate.get("source") or metadata.get("source"),
            "candidate_type": candidate.get("candidate_type")
            or candidate.get("learned_object_type")
            or metadata.get("candidate_type")
            or metadata.get("learned_object_type"),
            "candidate_fingerprint": fingerprint,
            "learned_object_id": learned_object_id,
            "source_program_id": candidate.get("source_program_id")
            or candidate.get("program_id")
            or learned_object_id,
            "producer_operation_id": candidate.get("producer_operation_id")
            or metadata.get("producer_operation_id"),
            "run_id": candidate.get("run_id") or candidate.get("target_run_id"),
        }

    def _materialized(
        self,
        candidate: Mapping[str, Any],
        materialization: Mapping[str, Any],
    ) -> bool:
        state = str(materialization.get("materialization_state") or "")
        return bool(
            candidate.get("candidate_id")
            and (
                not materialization
                or materialization.get("materialized") is True
                or state in {"MATERIALIZED", "PASSED", "CANDIDATE_MATERIALIZED"}
            )
        )

    def _validation_passed(self, validation: Mapping[str, Any]) -> bool:
        return bool(
            validation.get("validation_success") is True
            or validation.get("validation_state") in PASSED_VALIDATION_STATES
        )

    def _qualified(self, qualification: Mapping[str, Any]) -> bool:
        return qualification.get("qualification_state") in PASSED_QUALIFICATION_STATES

    def _budget_state(self, budget: Mapping[str, Any]) -> str:
        return str(
            budget.get("budget_admission_state")
            or budget.get("runtime_budget_state")
            or budget.get("route_budget_enforcement_state")
            or "NOT_REACHED"
        )

    def _validation_state(self, validation: Mapping[str, Any]) -> str:
        if not validation:
            return "NOT_REACHED"
        if self._validation_passed(validation):
            return "PASSED"
        return str(validation.get("validation_state") or "BLOCKED")

    def _qualification_state(self, qualification: Mapping[str, Any]) -> str:
        if not qualification:
            return "NOT_REACHED"
        if self._qualified(qualification):
            return "PASSED"
        return str(qualification.get("qualification_state") or "BLOCKED")

    def _boundary_state(self, expected: bool, passed: bool) -> str:
        if passed:
            return "PASSED"
        return "BLOCKED" if expected else "NOT_REACHED"

    def _arena_boundary_state(
        self,
        expected: bool,
        reached: bool,
        decision: str,
        safe_winner: bool,
    ) -> str:
        if not expected:
            return "NOT_REACHED"
        if safe_winner:
            return "PASSED"
        if reached and decision in {"TIE_REQUIRES_REVIEW", "NO_SAFE_WINNER"}:
            return "BLOCKED"
        return "REACHED" if reached else "NOT_REACHED"

    def _expected_boundary_state(self, expected: bool, observed: bool) -> str:
        if observed:
            return "PASSED"
        return "NOT_REACHED" if not expected else "BLOCKED"

    def _expectations(self, **state: bool) -> list[dict[str, Any]]:
        rows = [
            ("candidate_generated", True, state["candidate_generated"]),
            ("materialization", state["candidate_generated"], state["materialized"]),
            ("sandbox_validation", state["materialized"], state["validation_passed"]),
            ("qualification", state["validation_passed"], state["qualified"]),
            ("arena_selection", state["qualified"], state["arena_reached"]),
            ("execution_grant", state["safe_winner"], state["grant_issued"]),
            ("candidate_budget_admission", state["grant_issued"], state["budget_admitted"]),
            ("production_executor", state["grant_issued"] and state["budget_admitted"], state["executor_called"]),
            ("outcome_provenance", state["real_execution"], state["outcome_complete"]),
        ]
        return [
            {
                "boundary": boundary,
                "expected": bool(expected),
                "observed": bool(observed),
                "state": (
                    "OBSERVED"
                    if observed
                    else "EXPECTED_NOT_OBSERVED"
                    if expected
                    else "NOT_EXPECTED"
                ),
                "reachability_gap": bool(expected and not observed),
            }
            for boundary, expected, observed in rows
        ]

    def _unauthorized_activity(
        self,
        *,
        arena_decision: str,
        grant_expected: bool,
        grant_issued: bool,
        budget_expected: bool,
        budget_admitted: bool,
        executor_expected: bool,
        executor_called: bool,
        real_execution: bool,
    ) -> str | None:
        blocked_arena = arena_decision in {"TIE_REQUIRES_REVIEW", "NO_SAFE_WINNER"}
        if blocked_arena and grant_issued:
            return "UNEXPECTED_GRANT_AFTER_BLOCK"
        if blocked_arena and executor_called:
            return "UNAUTHORIZED_EXECUTOR_REACHABILITY"
        if blocked_arena and real_execution:
            return "UNAUTHORIZED_PRODUCTION_EXECUTION"
        if not grant_expected and grant_issued:
            return "UNEXPECTED_GRANT_AFTER_BLOCK"
        if not budget_expected and budget_admitted:
            return "UNEXPECTED_BUDGET_ADMISSION_AFTER_BLOCK"
        if not executor_expected and executor_called:
            return "UNAUTHORIZED_EXECUTOR_REACHABILITY"
        return None

    def _first_block(self, **state: Any) -> str:
        if state["contamination"]:
            return "NATURAL_E7_PROOF_INVALID"
        if not state["candidate_generated"]:
            return "CANDIDATE_NOT_GENERATED"
        if not state["materialized"]:
            return "MATERIALIZATION_BLOCKED"
        if not state["validation_passed"]:
            return "SANDBOX_VALIDATION_FAILED"
        if not state["qualified"]:
            return (
                "QUALIFICATION_BLOCKED"
                if state["qualification"]
                else "EVIDENCE_INSUFFICIENT"
            )
        if not state["arena_reached"]:
            return "ARENA_ADMISSION_BLOCKED"
        if state["arena_decision"] == "TIE_REQUIRES_REVIEW":
            return "ARENA_TIE_REQUIRES_REVIEW"
        if state["arena_decision"] == "NO_SAFE_WINNER" or not state["safe_winner"]:
            return "ARENA_NO_SAFE_WINNER"
        if state["grant_expected"] and not state["grant_issued"]:
            return "EXECUTION_GRANT_BLOCKED"
        if state["budget_expected"] and not state["budget_admitted"]:
            return "RUNTIME_BUDGET_BLOCKED"
        if state["executor_expected"] and not state["executor_called"]:
            return "PRODUCTION_EXECUTOR_NOT_REACHED"
        if not state["real_execution"]:
            return "EXECUTION_INTEGRITY_BLOCKED"
        if not state["outcome_complete"]:
            return "OUTCOME_PROVENANCE_INCOMPLETE"
        return "NATURAL_E7_REACHED"

    def _phase_state(
        self,
        *,
        unauthorized: bool,
        contamination: bool,
        natural_e7: bool,
        reachability_gaps: list[str],
        candidate_generated: bool,
        first_block: str,
    ) -> str:
        if unauthorized:
            return "UNAUTHORIZED_DOWNSTREAM_REACHABILITY"
        if contamination:
            return "INSUFFICIENT_OBSERVABILITY"
        if natural_e7:
            return "NATURAL_END_TO_END_REACHABILITY_PROVEN"
        if reachability_gaps and first_block not in {
            "ARENA_TIE_REQUIRES_REVIEW",
            "ARENA_NO_SAFE_WINNER",
            "QUALIFICATION_BLOCKED",
            "EVIDENCE_INSUFFICIENT",
            "SANDBOX_VALIDATION_FAILED",
        }:
            return "NATURAL_HANDOFF_GAP_PROVEN"
        if candidate_generated:
            return "NATURAL_RUNTIME_LAWFULLY_BLOCKED_UPSTREAM"
        return "INSUFFICIENT_OBSERVABILITY"

    def _lineage_state(
        self,
        *,
        run_id: str | None,
        candidate_identity: Mapping[str, Any],
        selected_candidate_id: Any,
        grant: Mapping[str, Any],
        production: Mapping[str, Any],
    ) -> str:
        candidate_id = str(candidate_identity.get("candidate_id") or "")
        if not candidate_id:
            return "CANDIDATE_LINEAGE_UNDETERMINED"
        if selected_candidate_id and str(selected_candidate_id) != candidate_id:
            return "CANDIDATE_LINEAGE_BREAK"
        if grant.get("candidate_id") and str(grant.get("candidate_id")) != candidate_id:
            return "CANDIDATE_LINEAGE_BREAK"
        if production.get("candidate_id") and str(production.get("candidate_id")) != candidate_id:
            return "CANDIDATE_LINEAGE_BREAK"
        learned = str(candidate_identity.get("learned_object_id") or "")
        if grant.get("learned_object_id") and str(grant.get("learned_object_id")) != learned:
            return "CANDIDATE_LINEAGE_BREAK"
        if production.get("learned_object_id") and str(production.get("learned_object_id")) != learned:
            return "CANDIDATE_LINEAGE_BREAK"
        expected_run = str(run_id or "")
        if expected_run:
            for source in (grant, production):
                if source.get("run_id") and str(source.get("run_id")) != expected_run:
                    return "CANDIDATE_LINEAGE_BREAK"
        if grant.get("candidate_fingerprint") and (
            grant.get("candidate_fingerprint")
            != candidate_identity.get("candidate_fingerprint")
        ):
            return "CANDIDATE_FINGERPRINT_DRIFT"
        return "CANDIDATE_LINEAGE_CONTINUITY_VERIFIED"

    def _highest_level(self, **state: bool) -> str:
        levels = [
            ("E0", state["candidate_generated"]),
            ("E1", state["materialized"]),
            ("E2", state["validation_passed"]),
            ("E3", state["qualified"]),
            ("E4", state["arena_reached"]),
            ("E5", state["safe_winner"]),
            ("E6", state["grant_issued"] and state["budget_admitted"]),
            ("E7", state["executor_called"] and state["real_execution"] and state["outcome_complete"]),
        ]
        highest = "E0_NOT_REACHED"
        for level, reached in levels:
            if reached:
                highest = level
        return highest

    def _first_unreached(self, boundaries: Mapping[str, str]) -> str:
        for boundary, state in boundaries.items():
            if state in {"BLOCKED", "NOT_REACHED", "UNDETERMINED"}:
                return boundary
        return "NONE"

    def _blocking_reason(self, first_block: str, arena_decision: str) -> str:
        if first_block == "ARENA_TIE_REQUIRES_REVIEW":
            return "Arena decision TIE_REQUIRES_REVIEW lawfully prevents grant expectation."
        if first_block == "ARENA_NO_SAFE_WINNER":
            return f"Arena decision {arena_decision} produced no safe winner."
        if first_block == "NATURAL_E7_REACHED":
            return "NONE"
        return first_block

    def _stable_id(self, prefix: str, payload: Any) -> str:
        text = json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=True,
            default=str,
            separators=(",", ":"),
        )
        return f"{prefix}_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


natural_production_handoff_observer = NaturalProductionHandoffObserver()


__all__ = [
    "NaturalProductionHandoffObserver",
    "natural_production_handoff_observer",
]
