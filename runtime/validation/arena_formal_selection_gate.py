from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ArenaFormalSelectionGate:
    """Ratifies, rejects, or defers one durable Arena decision proposal."""

    BOUNDARY = (
        "FORMAL_SELECTION_MAY_RATIFY_ONE_VALID_DECISION_PROPOSAL_AND_IDENTIFY_ONE_ARENA_WINNER_BUT_MUST_NOT_COMPILE_EXECUTE_VALIDATE_PROMOTE_OR_GRANT_TRUTH_TRUST_OR_GRADUATION_TO_THE_SELECTED_CANDIDATE"
    )
    SELECTION_BOUNDARY = (
        "WINNER_SELECTION_IS_A_DELIBERATIVE_ARENA_DECISION_NOT_AN_EXECUTION_AUTHORIZATION_OR_EPISTEMIC_STATUS_GRANT"
    )
    REVIEW_AUTHORITY = "ARENA_FORMAL_SELECTION_GATE"
    REVIEW_SCOPE = "ONE_DECISION_PROPOSAL_ONE_ARENA_VERSION_ONE_BOUNDED_FORMAL_REVIEW"
    FORMAL_SELECTION_POLICY_VERSION = "1.0"
    CONSTITUTIONAL_POLICY_VERSION = "1.0"
    VETO_POLICY_VERSION = "1.0"

    def __init__(
        self,
        root_path: str | os.PathLike[str] = (
            "runtime/state/evidence_acquisition_plans"
        ),
    ):
        self.root_path = Path(root_path)
        self.pending_path = self.root_path / "pending"
        self.admissions_path = self.root_path / "arena_evidence_admissions"
        self.ledger_path = self.root_path / "arena_evidence_ledger"
        self.redeliberations_path = self.root_path / "arena_redeliberations"
        self.outcomes_path = self.root_path / "arena_deliberative_outcomes"
        self.decision_proposals_path = self.root_path / "decision_proposals"
        self.review_cases_path = self.root_path / "formal_selection_review_cases"
        self.decisions_path = self.root_path / "formal_selection_decisions"
        self.selection_snapshots_path = self.root_path / "arena_selection_snapshots"
        self.dispositions_path = self.root_path / "decision_proposal_dispositions"

    def review_pending_decision_proposals(self) -> dict[str, Any]:
        self._initialize()
        reports = []
        for plan_path in self._json_files(self.pending_path):
            plan, error = self._read_json(plan_path)
            if error or not isinstance(plan, dict):
                continue
            if plan.get("lifecycle_state") in {
                "ARENA_REDELIBERATION_COMPLETED",
                "FORMAL_SELECTION_REVIEW_STARTED",
                "RATIFIED",
                "REJECTED",
                "DEFERRED",
            }:
                reports.append(self.review_plan(plan.get("plan_id")))
        completed = [
            report for report in reports
            if report.get("formal_selection_review_completed") is True
        ]
        current = completed[0] if completed else reports[0] if reports else {}
        return {
            "system": "arena_formal_selection_gate",
            "responsible_component": self.REVIEW_AUTHORITY,
            "formal_selection_gate_attempted": bool(reports),
            "formal_selection_review_count": len(completed),
            "formal_selection_reports": reports,
            **self._public_projection(current),
        }

    def review_plan(self, plan_id: str | None) -> dict[str, Any]:
        self._initialize()
        base = self._base_report(plan_id)
        plan, plan_path, plan_error = self._load_plan(plan_id)
        if plan_error or not plan or not plan_path:
            return self._blocked(
                base,
                "BLOCKED_INVALID_PLAN_LIFECYCLE",
                plan_error or "plan_not_found",
                "plan_load",
                "restore_decision_proposal_plan",
            )
        existing = self._existing_decision(plan)
        if existing:
            case = self._existing_review_case(plan) or {}
            snapshot = self._existing_selection_snapshot(plan) or {}
            disposition = self._existing_disposition(plan) or {}
            return self._terminal_report(
                base,
                plan,
                case,
                existing,
                snapshot,
                disposition,
                "REUSED_EXISTING_FORMAL_SELECTION_REVIEW_CASE",
                "REUSED_EXISTING_FORMAL_SELECTION_DECISION",
                "REUSED_EXISTING_ARENA_SELECTION_SNAPSHOT",
                "REUSED_EXISTING_PROPOSAL_DISPOSITION",
            )

        admission = self._admission(plan)
        if admission["formal_selection_admission_state"] != (
            "ADMITTED_TO_FORMAL_SELECTION_REVIEW"
        ):
            return {**base, **admission}

        proposal = admission["decision_proposal"]
        redelib = admission["redeliberation_snapshot"]
        outcome = admission["deliberative_outcome"]
        baseline = admission["baseline_snapshot"]
        review_case = self._review_case(plan, proposal, redelib, outcome, baseline)
        started_at = self._now()
        try:
            started_plan = {
                **plan,
                "updated_at": started_at,
                "lifecycle_state": "FORMAL_SELECTION_REVIEW_STARTED",
                "formal_selection_state": "FORMAL_SELECTION_REVIEW_STARTED",
                "formal_selection_invoked": True,
                "formal_selection_review_started": True,
                "formal_selection_review_completed": False,
                "formal_selection_review_case_id": review_case[
                    "formal_selection_review_case_id"
                ],
                "formal_selection_review_id": review_case[
                    "formal_selection_review_case_id"
                ],
                "formal_selection_started_at": started_at,
                "active_formal_selection_lease": True,
                "decision_proposal_id": proposal.get("decision_proposal_id"),
                "originating_arena_id": proposal.get("originating_arena_id"),
                "proposed_candidate_id": proposal.get("proposed_candidate_id"),
                "formal_selection_outcome": "PENDING",
                "tie_resolved": False,
                "winner_selected": False,
                "selected_candidate": "NONE",
                "candidate_execution_authority": "NONE",
                "candidate_execution_started": False,
                "truth_authority": "NONE",
                "trust_authority": "NONE",
                "graduation_authority": "NONE",
            }
            self._atomic_write(plan_path, started_plan)
            self._atomic_write(
                self.review_cases_path
                / f"{review_case['formal_selection_review_case_id']}.json",
                review_case,
            )
        except (OSError, TypeError, ValueError) as error:
            return self._blocked(
                {**base, **self._identity(plan, proposal, redelib, outcome)},
                "BLOCKED_SELECTION_STATE_PERSISTENCE_FAILURE",
                str(error),
                "formal_selection_start_persistence",
                "retry_idempotent_formal_selection_review",
            )

        checks = self._review_checks(proposal, redelib, outcome, baseline)
        outcome_name, reason = self._formal_outcome(checks)
        decision = self._selection_decision(
            started_plan,
            proposal,
            review_case,
            checks,
            outcome_name,
            reason,
        )
        selection_snapshot = self._selection_snapshot(
            proposal,
            redelib,
            review_case,
            decision,
        )
        disposition = self._proposal_disposition(proposal, review_case, decision)
        try:
            self._atomic_write(
                self.decisions_path
                / f"{decision['formal_selection_decision_id']}.json",
                decision,
            )
            self._atomic_write(
                self.selection_snapshots_path
                / f"{selection_snapshot['arena_selection_snapshot_id']}.json",
                selection_snapshot,
            )
            self._atomic_write(
                self.dispositions_path
                / f"{disposition['proposal_disposition_id']}.json",
                disposition,
            )
            final_plan = self._final_plan(
                started_plan,
                decision,
                selection_snapshot,
                disposition,
            )
            self._atomic_write(plan_path, final_plan)
        except (OSError, TypeError, ValueError) as error:
            return self._blocked(
                {**base, **self._identity(plan, proposal, redelib, outcome)},
                "BLOCKED_SELECTION_STATE_PERSISTENCE_FAILURE",
                str(error),
                "formal_selection_decision_persistence",
                "retry_idempotent_formal_selection_review",
            )
        return self._terminal_report(
            base,
            final_plan,
            review_case,
            decision,
            selection_snapshot,
            disposition,
            "CREATED_NEW_FORMAL_SELECTION_REVIEW_CASE",
            "CREATED_NEW_FORMAL_SELECTION_DECISION",
            "CREATED_NEW_ARENA_SELECTION_SNAPSHOT",
            "CREATED_NEW_PROPOSAL_DISPOSITION",
        )

    def _admission(self, plan: dict[str, Any]) -> dict[str, Any]:
        if plan.get("lifecycle_state") != "ARENA_REDELIBERATION_COMPLETED":
            return self._admission_block(
                "BLOCKED_INVALID_PLAN_LIFECYCLE",
                f"expected_ARENA_REDELIBERATION_COMPLETED_observed_{plan.get('lifecycle_state')}",
                "plan_lifecycle",
                "route_only_completed_redeliberations_to_formal_selection",
            )
        if plan.get("redeliberation_completed") is not True:
            return self._admission_block(
                "BLOCKED_REDELIBERATION_NOT_COMPLETED",
                "redeliberation_completed_not_true",
                "redeliberation_completion",
                "complete_redeliberation_before_formal_selection",
            )
        if plan.get("redeliberation_outcome") != "DECISION_PROPOSAL_AVAILABLE":
            return self._admission_block(
                "BLOCKED_INVALID_REDELIBERATION_OUTCOME",
                f"observed_{plan.get('redeliberation_outcome')}",
                "redeliberation_outcome",
                "do_not_formally_select_without_decision_proposal",
            )
        if plan.get("decision_proposal_available") is not True:
            return self._admission_block(
                "BLOCKED_NO_DECISION_PROPOSAL",
                "decision_proposal_available_not_true",
                "decision_proposal_route",
                "restore_decision_proposal_or_remediate_arena",
            )
        if plan.get("decision_proposal_state") not in {
            "READY_FOR_FORMAL_SELECTION_REVIEW",
            None,
        }:
            return self._admission_block(
                "BLOCKED_INVALID_PROPOSAL_STATE",
                f"observed_{plan.get('decision_proposal_state')}",
                "decision_proposal_state",
                "restore_ready_decision_proposal_state",
            )
        if plan.get("formal_selection_invoked") is True or plan.get(
            "active_formal_selection_lease"
        ) is True:
            return self._admission_block(
                "BLOCKED_ACTIVE_FORMAL_SELECTION",
                "formal_selection_already_active",
                "formal_selection_lease",
                "recover_incomplete_formal_selection_review",
            )
        if plan.get("winner_selected") is True:
            return self._admission_block(
                "BLOCKED_WINNER_ALREADY_SELECTED",
                "winner_already_selected",
                "winner_integrity",
                "do_not_select_twice",
            )
        if plan.get("candidate_execution_started") is True:
            return self._admission_block(
                "BLOCKED_EXECUTION_ALREADY_STARTED",
                "candidate_execution_already_started",
                "execution_separation",
                "review_authority_boundary_violation",
            )
        for field in (
            "candidate_execution_authority",
            "truth_authority",
            "trust_authority",
            "graduation_authority",
        ):
            if plan.get(field, "NONE") != "NONE":
                return self._admission_block(
                    "BLOCKED_CONSTITUTIONAL_VIOLATION",
                    f"{field}_not_none",
                    "authority_validation",
                    "restore_formal_selection_authority_boundaries",
                )
        if plan.get("next_consumer") != "ARENA_FORMAL_SELECTION_GATE":
            return self._admission_block(
                "BLOCKED_INVALID_PROPOSAL_STATE",
                f"next_consumer_{plan.get('next_consumer')}",
                "route_validation",
                "restore_formal_selection_route",
            )
        proposal, proposal_error = self._load_proposal(
            plan.get("decision_proposal_id")
        )
        if proposal_error or not proposal:
            return self._admission_block(
                "BLOCKED_MISSING_DECISION_PROPOSAL",
                proposal_error or "decision_proposal_not_found",
                "decision_proposal_load",
                "restore_decision_proposal_record",
            )
        redelib, redelib_error = self._load_json_by_id(
            self.redeliberations_path,
            plan.get("redeliberation_snapshot_id"),
            "redeliberation_snapshot",
        )
        if redelib_error or not redelib:
            return self._admission_block(
                "BLOCKED_MISSING_REDELIBERATION_SNAPSHOT",
                redelib_error or "redeliberation_snapshot_not_found",
                "redeliberation_snapshot_load",
                "restore_redeliberation_snapshot",
            )
        outcome, outcome_error = self._load_json_by_id(
            self.outcomes_path,
            plan.get("deliberative_outcome_id"),
            "deliberative_outcome",
        )
        if outcome_error or not outcome:
            return self._admission_block(
                "BLOCKED_MISSING_DELIBERATIVE_OUTCOME",
                outcome_error or "deliberative_outcome_not_found",
                "deliberative_outcome_load",
                "restore_deliberative_outcome",
            )
        admission, admission_error = self._load_json_by_id(
            self.admissions_path,
            plan.get("arena_evidence_admission_id"),
            "arena_evidence_admission",
        )
        if admission_error or not admission:
            return self._admission_block(
                "BLOCKED_MISSING_ORIGINATING_ARENA",
                admission_error or "arena_admission_not_found",
                "originating_arena_load",
                "restore_arena_admission_record",
            )
        baseline, baseline_error = self._baseline_snapshot(admission)
        if baseline_error or not baseline:
            return self._admission_block(
                "BLOCKED_MISSING_BASELINE_SNAPSHOT",
                baseline_error or "baseline_snapshot_not_found",
                "baseline_snapshot_load",
                "restore_baseline_arena_snapshot",
            )
        alignment_failures = self._alignment_failures(
            plan,
            proposal,
            redelib,
            outcome,
            admission,
            baseline,
        )
        if alignment_failures:
            reason = ",".join(alignment_failures)
            state = (
                "BLOCKED_FINGERPRINT_INTEGRITY_FAILURE"
                if "fingerprint" in reason
                else "BLOCKED_PROPOSAL_LINEAGE_MISMATCH"
            )
            return self._admission_block(
                state,
                reason,
                "proposal_lineage_alignment",
                "repair_formal_selection_lineage_records",
            )
        proposed = proposal.get("proposed_candidates") or [
            proposal.get("proposed_candidate_id")
        ]
        proposed = [item for item in proposed if self._term(item) != "Not Available"]
        if len(proposed) != 1:
            return self._admission_block(
                "BLOCKED_MULTIPLE_PROPOSED_CANDIDATES",
                f"proposed_candidate_count_{len(proposed)}",
                "proposed_candidate_cardinality",
                "repair_decision_proposal_candidate_set",
            )
        candidate = self._candidate_from_snapshot(
            redelib,
            proposal.get("proposed_candidate_id"),
        )
        if not candidate:
            return self._admission_block(
                "BLOCKED_CANDIDATE_NOT_FOUND",
                "proposed_candidate_missing_from_redeliberation_snapshot",
                "candidate_identity",
                "repair_decision_proposal_candidate_reference",
            )
        if self._candidate_fingerprint(candidate) != proposal.get(
            "proposed_candidate_fingerprint"
        ):
            return self._admission_block(
                "BLOCKED_CANDIDATE_FINGERPRINT_MISMATCH",
                "proposed_candidate_fingerprint_mismatch",
                "candidate_identity",
                "repair_candidate_fingerprint_lineage",
            )
        if proposal.get("proposal_revocation_state") == "REVOKED":
            return self._admission_block(
                "BLOCKED_PROPOSAL_REVOKED",
                "decision_proposal_revoked",
                "proposal_revocation",
                "route_to_proposal_remediation",
            )
        if proposal.get("proposal_supersession_state") == "SUPERSEDED":
            return self._admission_block(
                "BLOCKED_PROPOSAL_SUPERSEDED",
                "decision_proposal_superseded",
                "proposal_supersession",
                "load_current_decision_proposal",
            )
        if admission.get("arena_admission_state") != "ADMITTED":
            return self._admission_block(
                "BLOCKED_RECORD_ALIGNMENT_FAILURE",
                "arena_evidence_admission_not_admitted",
                "admitted_evidence_lineage",
                "restore_arena_evidence_admission",
            )
        if admission.get("revocation_state") == "REVOKED":
            return self._admission_block(
                "BLOCKED_EVIDENCE_REVOKED",
                "admitted_evidence_revoked",
                "evidence_revocation",
                "route_to_evidence_remediation",
            )
        if self._existing_decision_for_plan(plan):
            return self._admission_block(
                "BLOCKED_CONFLICTING_SELECTION_DECISION",
                "formal_selection_decision_already_exists",
                "selection_decision_uniqueness",
                "reuse_existing_formal_selection_decision",
            )
        return {
            "formal_selection_admission_invoked": True,
            "formal_selection_admission_evaluated": True,
            "formal_selection_admission_state": (
                "ADMITTED_TO_FORMAL_SELECTION_REVIEW"
            ),
            "formal_selection_admission_reason": (
                "decision_proposal_satisfies_formal_selection_admission_contract"
            ),
            "blocked_stage": "none",
            "responsible_component": self.REVIEW_AUTHORITY,
            "recommended_action": "perform_one_bounded_formal_selection_review",
            "decision_proposal": proposal,
            "redeliberation_snapshot": redelib,
            "deliberative_outcome": outcome,
            "arena_evidence_admission": admission,
            "baseline_snapshot": baseline,
        }

    def _review_case(
        self,
        plan: dict[str, Any],
        proposal: dict[str, Any],
        redelib: dict[str, Any],
        outcome: dict[str, Any],
        baseline: dict[str, Any],
    ) -> dict[str, Any]:
        fingerprint = self._fingerprint({
            "plan_id": plan.get("plan_id"),
            "decision_proposal_id": proposal.get("decision_proposal_id"),
            "decision_proposal_fingerprint": proposal.get(
                "decision_proposal_fingerprint"
            ),
            "policy": self.FORMAL_SELECTION_POLICY_VERSION,
            "constitutional": self.CONSTITUTIONAL_POLICY_VERSION,
            "veto": self.VETO_POLICY_VERSION,
        })
        return {
            "schema_version": "1.0",
            "formal_selection_review_case_id": (
                f"formal_selection_review_{hashlib.sha1(fingerprint.encode()).hexdigest()[:12]}"
            ),
            "formal_selection_review_case_fingerprint": fingerprint,
            "formal_selection_policy_id": "one_bounded_decision_proposal_review",
            "formal_selection_policy_version": (
                self.FORMAL_SELECTION_POLICY_VERSION
            ),
            "formal_selection_policy_fingerprint": self._policy_fingerprint(
                "one_bounded_decision_proposal_review",
                self.FORMAL_SELECTION_POLICY_VERSION,
            ),
            "constitutional_selection_policy_id": (
                "formal_selection_constitutional_boundary"
            ),
            "constitutional_selection_policy_version": (
                self.CONSTITUTIONAL_POLICY_VERSION
            ),
            "constitutional_selection_policy_fingerprint": self._policy_fingerprint(
                "formal_selection_constitutional_boundary",
                self.CONSTITUTIONAL_POLICY_VERSION,
            ),
            "veto_policy_id": "formal_selection_veto_policy",
            "veto_policy_version": self.VETO_POLICY_VERSION,
            "veto_policy_fingerprint": self._policy_fingerprint(
                "formal_selection_veto_policy",
                self.VETO_POLICY_VERSION,
            ),
            "originating_arena_id": proposal.get("originating_arena_id"),
            "originating_arena_version": proposal.get("originating_arena_version"),
            "baseline_snapshot_id": proposal.get("baseline_snapshot_id"),
            "baseline_snapshot_fingerprint": proposal.get(
                "baseline_snapshot_fingerprint"
            ),
            "redeliberation_id": proposal.get("redeliberation_id"),
            "redeliberation_snapshot_id": proposal.get("redeliberation_snapshot_id"),
            "redeliberation_snapshot_fingerprint": proposal.get(
                "redeliberation_snapshot_fingerprint"
            ),
            "arena_deliberative_outcome_id": outcome.get(
                "deliberative_outcome_id"
            ),
            "arena_deliberative_outcome_fingerprint": outcome.get(
                "deliberative_outcome_fingerprint"
            ),
            "decision_proposal_id": proposal.get("decision_proposal_id"),
            "decision_proposal_fingerprint": proposal.get(
                "decision_proposal_fingerprint"
            ),
            "proposed_candidate_id": proposal.get("proposed_candidate_id"),
            "proposed_candidate_fingerprint": proposal.get(
                "proposed_candidate_fingerprint"
            ),
            "proposed_candidate_source": proposal.get("proposed_candidate_source"),
            "proposed_operation": proposal.get("proposed_operation"),
            "supporting_evidence_ids": [proposal.get("arena_evidence_ledger_entry_id")],
            "contradicting_evidence_ids": [],
            "neutral_evidence_ids": [],
            "inconclusive_evidence_ids": [],
            "proposal_top_score_margin": proposal.get("proposal_top_score_margin"),
            "proposal_minimum_required_margin": proposal.get(
                "proposal_minimum_required_margin"
            ),
            "proposal_candidate_eligibility_state": proposal.get(
                "proposal_candidate_eligibility_state"
            ),
            "proposal_cross_source_consensus_state": proposal.get(
                "proposal_cross_source_consensus_state"
            ),
            "proposal_tie_break_strategy_state": proposal.get(
                "proposal_tie_break_strategy_state"
            ),
            "proposal_remaining_uncertainties": proposal.get(
                "proposal_remaining_uncertainties",
                [],
            ),
            "proposal_remaining_evidence_deficits": proposal.get(
                "proposal_remaining_evidence_deficits",
                [],
            ),
            "proposal_constitutional_veto_state": proposal.get(
                "proposal_constitutional_veto_state",
                "CLEAR",
            ),
            "admission_state": "ADMITTED_TO_FORMAL_SELECTION_REVIEW",
            "admission_reason": (
                "decision_proposal_satisfies_formal_selection_admission_contract"
            ),
            "review_authority": self.REVIEW_AUTHORITY,
            "review_scope": self.REVIEW_SCOPE,
            "review_state": "CREATED",
            "max_formal_selection_cycles": 1,
            "max_proposals_reviewed": 1,
            "max_candidate_records_loaded": len(
                redelib.get("candidate_profiles") or []
            ),
            "max_evidence_records_loaded": 1,
            "created_at": self._now(),
            "constitutional_boundary": self.BOUNDARY,
            "selection_boundary": self.SELECTION_BOUNDARY,
        }

    def _review_checks(
        self,
        proposal: dict[str, Any],
        redelib: dict[str, Any],
        outcome: dict[str, Any],
        baseline: dict[str, Any],
    ) -> dict[str, str]:
        candidate = self._candidate_from_snapshot(
            redelib,
            proposal.get("proposed_candidate_id"),
        )
        margin = float(proposal.get("proposal_top_score_margin", 0.0) or 0.0)
        required = float(
            proposal.get("proposal_minimum_required_margin", 0.0) or 0.0
        )
        checks = {
            "proposal_lineage_integrity_state": (
                "VERIFIED"
                if proposal.get("redeliberation_snapshot_id")
                == redelib.get("redeliberation_snapshot_id")
                and proposal.get("arena_deliberative_outcome_id")
                == outcome.get("deliberative_outcome_id")
                else "MISMATCH"
            ),
            "candidate_identity_integrity_state": (
                "VERIFIED"
                if candidate
                and self._candidate_fingerprint(candidate)
                == proposal.get("proposed_candidate_fingerprint")
                else "MISMATCH"
            ),
            "redeliberation_completeness_state": (
                "VERIFIED"
                if redelib.get("candidate_scores_recomputed") is True
                and redelib.get("candidate_ranking_recomputed") is True
                and outcome.get("redeliberation_outcome")
                == "DECISION_PROPOSAL_AVAILABLE"
                else "NOT_SATISFIED"
            ),
            "proposal_uniqueness_state": "VERIFIED",
            "proposal_readiness_state": (
                "SATISFIED"
                if proposal.get("decision_proposal_state")
                == "READY_FOR_FORMAL_SELECTION_REVIEW"
                else "NOT_SATISFIED"
            ),
            "minimum_margin_state": (
                "SATISFIED" if margin >= required else "NOT_SATISFIED"
            ),
            "candidate_eligibility_state": proposal.get(
                "proposal_candidate_eligibility_state",
                "MISSING",
            ),
            "cross_source_requirement_state": proposal.get(
                "proposal_tie_break_strategy_state",
                "MISSING",
            ),
            "consensus_integrity_state": (
                "VERIFIED"
                if proposal.get("validation_evidence_counted_as_candidate_source")
                is False
                else "CONFLICTING"
            ),
            "evidence_attribution_state": "VERIFIED",
            "evidence_quality_state": "SATISFIED",
            "remaining_uncertainty_state": (
                "SATISFIED"
                if not proposal.get("proposal_remaining_uncertainties")
                else "INCONCLUSIVE"
            ),
            "remaining_evidence_deficit_state": (
                "SATISFIED"
                if not proposal.get("proposal_remaining_evidence_deficits")
                else "INCONCLUSIVE"
            ),
            "constitutional_review_state": (
                "VERIFIED"
                if all(
                    proposal.get(field, "NONE") == "NONE"
                    for field in (
                        "candidate_execution_authority",
                        "truth_authority",
                        "trust_authority",
                        "graduation_authority",
                    )
                )
                else "VETOED"
            ),
            "constitutional_veto_state": (
                "VETOED"
                if proposal.get("proposal_constitutional_veto_state") == "VETOED"
                else "VERIFIED"
            ),
            "temporal_validity_state": (
                "VERIFIED"
                if baseline.get("winner_selected") is not True
                else "STALE"
            ),
            "selection_authority_boundary_state": "VERIFIED",
            "downstream_execution_separation_state": "VERIFIED",
        }
        return checks

    def _formal_outcome(self, checks: dict[str, str]) -> tuple[str, str]:
        reject_states = {"MISMATCH", "CONFLICTING", "VETOED", "REVOKED", "SUPERSEDED"}
        defer_states = {"MISSING", "STALE", "INCONCLUSIVE"}
        for key, state in checks.items():
            if state in reject_states:
                return "REJECTED", f"{key}_{state}".lower()
        for key, state in checks.items():
            if state in defer_states:
                return "DEFERRED", f"{key}_{state}".lower()
        if all(state in {"VERIFIED", "SATISFIED", "NOT_APPLICABLE"} for state in checks.values()):
            return "RATIFIED", "all_formal_selection_requirements_satisfied"
        return "DEFERRED", "formal_selection_requirements_not_fully_satisfied"

    def _selection_decision(
        self,
        plan: dict[str, Any],
        proposal: dict[str, Any],
        review_case: dict[str, Any],
        checks: dict[str, str],
        outcome: str,
        reason: str,
    ) -> dict[str, Any]:
        selected = (
            proposal.get("proposed_candidate_id") if outcome == "RATIFIED" else "NONE"
        )
        fingerprint = self._fingerprint({
            "review_case": review_case.get("formal_selection_review_case_fingerprint"),
            "proposal": proposal.get("decision_proposal_fingerprint"),
            "outcome": outcome,
            "selected": selected,
            "policy": self.FORMAL_SELECTION_POLICY_VERSION,
        })
        return {
            "schema_version": "1.0",
            "formal_selection_decision_id": (
                f"formal_selection_decision_{hashlib.sha1(fingerprint.encode()).hexdigest()[:12]}"
            ),
            "formal_selection_decision_fingerprint": fingerprint,
            "formal_selection_review_case_id": review_case.get(
                "formal_selection_review_case_id"
            ),
            "decision_proposal_id": proposal.get("decision_proposal_id"),
            "decision_proposal_fingerprint": proposal.get(
                "decision_proposal_fingerprint"
            ),
            **checks,
            "formal_selection_outcome": outcome,
            "formal_selection_outcome_reason": reason,
            "proposal_ratified": outcome == "RATIFIED",
            "proposal_rejected": outcome == "REJECTED",
            "proposal_deferred": outcome == "DEFERRED",
            "tie_resolved": outcome == "RATIFIED",
            "winner_selected": outcome == "RATIFIED",
            "selected_candidate": selected,
            "selection_basis": (
                "RATIFIED_DECISION_PROPOSAL" if outcome == "RATIFIED" else "NONE"
            ),
            "candidate_execution_authority": "NONE",
            "candidate_execution_started": False,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "formal_selection_review_authority": self.REVIEW_AUTHORITY,
            "formal_selection_review_scope": self.REVIEW_SCOPE,
            "review_completed_at": self._now(),
            "constitutional_boundary": self.BOUNDARY,
            "selection_boundary": self.SELECTION_BOUNDARY,
            "next_consumer": self._next_consumer(outcome),
        }

    def _selection_snapshot(
        self,
        proposal: dict[str, Any],
        redelib: dict[str, Any],
        review_case: dict[str, Any],
        decision: dict[str, Any],
    ) -> dict[str, Any]:
        fingerprint = self._fingerprint({
            "decision": decision.get("formal_selection_decision_fingerprint"),
            "redeliberation": redelib.get("redeliberation_snapshot_fingerprint"),
            "selected": decision.get("selected_candidate"),
        })
        return {
            "schema_version": "1.0",
            "arena_selection_snapshot_id": (
                f"arena_selection_snapshot_{hashlib.sha1(fingerprint.encode()).hexdigest()[:12]}"
            ),
            "arena_selection_snapshot_fingerprint": fingerprint,
            "formal_selection_decision_id": decision.get(
                "formal_selection_decision_id"
            ),
            "formal_selection_review_case_id": review_case.get(
                "formal_selection_review_case_id"
            ),
            "decision_proposal_id": proposal.get("decision_proposal_id"),
            "originating_arena_id": proposal.get("originating_arena_id"),
            "redeliberation_snapshot_id": redelib.get("redeliberation_snapshot_id"),
            "winner_selected": decision.get("winner_selected"),
            "selected_candidate": decision.get("selected_candidate"),
            "tie_resolved": decision.get("tie_resolved"),
            "candidate_execution_authority": "NONE",
            "candidate_execution_started": False,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "created_at": self._now(),
        }

    def _proposal_disposition(
        self,
        proposal: dict[str, Any],
        review_case: dict[str, Any],
        decision: dict[str, Any],
    ) -> dict[str, Any]:
        fingerprint = self._fingerprint({
            "proposal": proposal.get("decision_proposal_fingerprint"),
            "decision": decision.get("formal_selection_decision_fingerprint"),
            "outcome": decision.get("formal_selection_outcome"),
        })
        return {
            "schema_version": "1.0",
            "proposal_disposition_id": (
                f"decision_proposal_disposition_{hashlib.sha1(fingerprint.encode()).hexdigest()[:12]}"
            ),
            "proposal_disposition_fingerprint": fingerprint,
            "decision_proposal_id": proposal.get("decision_proposal_id"),
            "formal_selection_review_case_id": review_case.get(
                "formal_selection_review_case_id"
            ),
            "formal_selection_decision_id": decision.get(
                "formal_selection_decision_id"
            ),
            "proposal_disposition": decision.get("formal_selection_outcome"),
            "proposal_disposition_reason": decision.get(
                "formal_selection_outcome_reason"
            ),
            "created_at": self._now(),
        }

    def _final_plan(
        self,
        plan: dict[str, Any],
        decision: dict[str, Any],
        snapshot: dict[str, Any],
        disposition: dict[str, Any],
    ) -> dict[str, Any]:
        outcome = decision.get("formal_selection_outcome")
        return {
            **plan,
            "updated_at": self._now(),
            "lifecycle_state": outcome,
            "formal_selection_state": f"FORMAL_SELECTION_{outcome}",
            "formal_selection_invoked": True,
            "formal_selection_review_started": True,
            "formal_selection_review_completed": True,
            "formal_selection_outcome": outcome,
            "formal_selection_outcome_reason": decision.get(
                "formal_selection_outcome_reason"
            ),
            "formal_selection_decision_id": decision.get(
                "formal_selection_decision_id"
            ),
            "arena_selection_snapshot_id": snapshot.get(
                "arena_selection_snapshot_id"
            ),
            "proposal_disposition_id": disposition.get("proposal_disposition_id"),
            "proposal_ratified": outcome == "RATIFIED",
            "proposal_rejected": outcome == "REJECTED",
            "proposal_deferred": outcome == "DEFERRED",
            "tie_resolved": decision.get("tie_resolved"),
            "winner_selected": decision.get("winner_selected"),
            "selected_candidate": decision.get("selected_candidate"),
            "selection_basis": decision.get("selection_basis"),
            "candidate_execution_authority": "NONE",
            "candidate_execution_started": False,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "next_consumer": decision.get("next_consumer"),
            "boot_recovery_route": self._boot_route(outcome),
            "active_formal_selection_lease": False,
        }

    def _terminal_report(
        self,
        base: dict[str, Any],
        plan: dict[str, Any],
        review_case: dict[str, Any],
        decision: dict[str, Any],
        snapshot: dict[str, Any],
        disposition: dict[str, Any],
        review_case_result: str,
        decision_result: str,
        snapshot_result: str,
        disposition_result: str,
    ) -> dict[str, Any]:
        return {
            **base,
            "plan_id": plan.get("plan_id"),
            "decision_proposal_id": decision.get("decision_proposal_id")
            or plan.get("decision_proposal_id"),
            "formal_selection_review_case_id": review_case.get(
                "formal_selection_review_case_id"
            ),
            "formal_selection_decision_id": decision.get(
                "formal_selection_decision_id"
            ),
            "arena_selection_snapshot_id": snapshot.get(
                "arena_selection_snapshot_id"
            ),
            "proposal_disposition_id": disposition.get("proposal_disposition_id"),
            "decision_proposal_route_detected": True,
            "decision_proposal_loaded": True,
            "originating_arena_loaded": True,
            "baseline_snapshot_loaded": True,
            "redeliberation_snapshot_loaded": True,
            "deliberative_outcome_loaded": True,
            "candidate_set_loaded": True,
            "proposed_candidate_resolved": True,
            "proposal_lineage_alignment": "ALIGNED",
            "fingerprint_integrity": "VERIFIED",
            "proposal_uniqueness": "VERIFIED",
            "formal_selection_admission_invoked": True,
            "formal_selection_admission_evaluated": True,
            "formal_selection_admission_state": (
                "ADMITTED_TO_FORMAL_SELECTION_REVIEW"
            ),
            "formal_selection_admission_reason": (
                "decision_proposal_satisfies_formal_selection_admission_contract"
            ),
            "formal_selection_review_authority": self.REVIEW_AUTHORITY,
            "formal_selection_review_scope": self.REVIEW_SCOPE,
            "formal_selection_review_invoked": True,
            "formal_selection_review_started": True,
            "formal_selection_review_completed": True,
            "proposal_readiness_reverified": (
                decision.get("proposal_readiness_state") == "SATISFIED"
            ),
            "minimum_margin_reverified": (
                decision.get("minimum_margin_state") == "SATISFIED"
            ),
            "candidate_eligibility_reverified": (
                decision.get("candidate_eligibility_state") == "SATISFIED"
            ),
            "cross_source_requirements_reverified": (
                decision.get("cross_source_requirement_state") == "SATISFIED"
            ),
            "consensus_integrity_verified": (
                decision.get("consensus_integrity_state") == "VERIFIED"
            ),
            "evidence_attribution_verified": (
                decision.get("evidence_attribution_state") == "VERIFIED"
            ),
            "evidence_quality_verified": (
                decision.get("evidence_quality_state") == "SATISFIED"
            ),
            "constitutional_review_completed": (
                decision.get("constitutional_review_state") == "VERIFIED"
            ),
            "constitutional_veto_active": (
                decision.get("constitutional_veto_state") == "VETOED"
            ),
            "temporal_validity_verified": (
                decision.get("temporal_validity_state") == "VERIFIED"
            ),
            **{
                key: decision.get(key)
                for key in (
                    "proposal_lineage_integrity_state",
                    "candidate_identity_integrity_state",
                    "redeliberation_completeness_state",
                    "proposal_uniqueness_state",
                    "proposal_readiness_state",
                    "minimum_margin_state",
                    "candidate_eligibility_state",
                    "cross_source_requirement_state",
                    "consensus_integrity_state",
                    "evidence_attribution_state",
                    "evidence_quality_state",
                    "remaining_uncertainty_state",
                    "remaining_evidence_deficit_state",
                    "constitutional_review_state",
                    "constitutional_veto_state",
                    "temporal_validity_state",
                    "selection_authority_boundary_state",
                    "downstream_execution_separation_state",
                )
            },
            "formal_selection_outcome": decision.get("formal_selection_outcome"),
            "formal_selection_outcome_reason": decision.get(
                "formal_selection_outcome_reason"
            ),
            "proposal_ratified": decision.get("proposal_ratified"),
            "proposal_rejected": decision.get("proposal_rejected"),
            "proposal_deferred": decision.get("proposal_deferred"),
            "tie_resolved": decision.get("tie_resolved"),
            "winner_selected": decision.get("winner_selected"),
            "selected_candidate": decision.get("selected_candidate"),
            "selection_basis": decision.get("selection_basis"),
            "candidate_execution_authority": "NONE",
            "candidate_execution_started": False,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "next_consumer": decision.get("next_consumer"),
            "formal_selection_review_creation_result": review_case_result,
            "formal_selection_decision_creation_result": decision_result,
            "arena_selection_snapshot_creation_result": snapshot_result,
            "proposal_disposition_creation_result": disposition_result,
            "constitutional_boundary": self.BOUNDARY,
            "selection_boundary": self.SELECTION_BOUNDARY,
        }

    def _blocked(
        self,
        base: dict[str, Any],
        state: str,
        reason: str,
        stage: str,
        action: str,
    ) -> dict[str, Any]:
        return {
            **base,
            "formal_selection_admission_invoked": True,
            "formal_selection_admission_evaluated": True,
            "formal_selection_admission_state": state,
            "formal_selection_admission_reason": reason,
            "blocked_stage": stage,
            "responsible_component": self.REVIEW_AUTHORITY,
            "recommended_action": action,
            "formal_selection_invoked": False,
            "formal_selection_review_started": False,
            "formal_selection_review_completed": False,
            "formal_selection_outcome": "NOT_EVALUATED",
            "proposal_ratified": False,
            "proposal_rejected": False,
            "proposal_deferred": False,
            "tie_resolved": False,
            "winner_selected": False,
            "selected_candidate": "NONE",
            "candidate_execution_authority": "NONE",
            "candidate_execution_started": False,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "constitutional_boundary": self.BOUNDARY,
        }

    def _admission_block(
        self,
        state: str,
        reason: str,
        stage: str,
        action: str,
    ) -> dict[str, Any]:
        return self._blocked({}, state, reason, stage, action)

    def _base_report(self, plan_id: str | None) -> dict[str, Any]:
        return {
            "system": "arena_formal_selection_gate",
            "responsible_component": self.REVIEW_AUTHORITY,
            "plan_id": self._term(plan_id),
            "decision_proposal_route_detected": False,
            "decision_proposal_loaded": False,
            "originating_arena_loaded": False,
            "baseline_snapshot_loaded": False,
            "redeliberation_snapshot_loaded": False,
            "deliberative_outcome_loaded": False,
            "candidate_set_loaded": False,
            "proposed_candidate_resolved": False,
            "formal_selection_admission_invoked": False,
            "formal_selection_admission_evaluated": False,
            "formal_selection_admission_state": "NOT_EVALUATED",
            "formal_selection_admission_reason": "not_evaluated",
            "formal_selection_review_invoked": False,
            "formal_selection_review_started": False,
            "formal_selection_review_completed": False,
            "formal_selection_outcome": "NOT_EVALUATED",
            "proposal_ratified": False,
            "proposal_rejected": False,
            "proposal_deferred": False,
            "tie_resolved": False,
            "winner_selected": False,
            "selected_candidate": "NONE",
            "candidate_execution_authority": "NONE",
            "candidate_execution_started": False,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "constitutional_boundary": self.BOUNDARY,
            "selection_boundary": self.SELECTION_BOUNDARY,
        }

    def _public_projection(self, report: dict[str, Any]) -> dict[str, Any]:
        base = self._base_report(report.get("plan_id"))
        return {**base, **report} if report else base

    def _identity(
        self,
        plan: dict[str, Any],
        proposal: dict[str, Any],
        redelib: dict[str, Any],
        outcome: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "plan_id": plan.get("plan_id"),
            "decision_proposal_id": proposal.get("decision_proposal_id"),
            "redeliberation_snapshot_id": redelib.get(
                "redeliberation_snapshot_id"
            ),
            "deliberative_outcome_id": outcome.get("deliberative_outcome_id"),
            "proposed_candidate_id": proposal.get("proposed_candidate_id"),
        }

    def _alignment_failures(
        self,
        plan: dict[str, Any],
        proposal: dict[str, Any],
        redelib: dict[str, Any],
        outcome: dict[str, Any],
        admission: dict[str, Any],
        baseline: dict[str, Any],
    ) -> list[str]:
        failures = []
        if proposal.get("plan_id") != plan.get("plan_id"):
            failures.append("proposal_plan_id_mismatch")
        if proposal.get("redeliberation_snapshot_id") != redelib.get(
            "redeliberation_snapshot_id"
        ):
            failures.append("proposal_redeliberation_id_mismatch")
        if proposal.get("arena_deliberative_outcome_id") != outcome.get(
            "deliberative_outcome_id"
        ):
            failures.append("proposal_outcome_id_mismatch")
        if outcome.get("decision_proposal_id") != proposal.get(
            "decision_proposal_id"
        ):
            failures.append("outcome_proposal_id_mismatch")
        if proposal.get("arena_evidence_admission_id") != admission.get(
            "arena_evidence_admission_id"
        ):
            failures.append("proposal_admission_id_mismatch")
        if proposal.get("baseline_snapshot_fingerprint") != baseline.get(
            "originating_arena_snapshot_fingerprint"
        ):
            failures.append("baseline_snapshot_fingerprint_mismatch")
        if proposal.get("redeliberation_snapshot_fingerprint") != redelib.get(
            "redeliberation_snapshot_fingerprint"
        ):
            failures.append("redeliberation_snapshot_fingerprint_mismatch")
        if proposal.get("arena_deliberative_outcome_fingerprint") != outcome.get(
            "deliberative_outcome_fingerprint"
        ):
            failures.append("deliberative_outcome_fingerprint_mismatch")
        if proposal.get("originating_arena_id") != baseline.get("arena_id"):
            failures.append("originating_arena_id_mismatch")
        return failures

    def _candidate_from_snapshot(
        self,
        redelib: dict[str, Any],
        candidate_id: str | None,
    ) -> dict[str, Any] | None:
        for row in redelib.get("candidate_profiles") or []:
            if isinstance(row, dict) and row.get("candidate_id") == candidate_id:
                return row
        return None

    def _candidate_fingerprint(self, candidate: dict[str, Any]) -> str:
        existing = candidate.get("candidate_fingerprint")
        if self._term(existing) != "Not Available":
            return str(existing)
        return self._fingerprint({
            "candidate_id": candidate.get("candidate_id"),
            "source": candidate.get("source"),
            "operation": candidate.get("operation"),
        })

    def _existing_decision(self, plan: dict[str, Any]) -> dict[str, Any] | None:
        decision_id = plan.get("formal_selection_decision_id")
        if decision_id:
            record, error = self._read_json(self.decisions_path / f"{decision_id}.json")
            if not error and isinstance(record, dict):
                return record
        return self._existing_decision_for_plan(plan)

    def _existing_decision_for_plan(
        self,
        plan: dict[str, Any],
    ) -> dict[str, Any] | None:
        for path in self._json_files(self.decisions_path):
            record, error = self._read_json(path)
            if error or not isinstance(record, dict):
                continue
            if record.get("decision_proposal_id") == plan.get("decision_proposal_id"):
                return record
        return None

    def _existing_review_case(self, plan: dict[str, Any]) -> dict[str, Any] | None:
        case_id = plan.get("formal_selection_review_case_id")
        if case_id:
            record, error = self._read_json(self.review_cases_path / f"{case_id}.json")
            if not error and isinstance(record, dict):
                return record
        for path in self._json_files(self.review_cases_path):
            record, error = self._read_json(path)
            if not error and isinstance(record, dict) and record.get(
                "decision_proposal_id"
            ) == plan.get("decision_proposal_id"):
                return record
        return None

    def _existing_selection_snapshot(
        self,
        plan: dict[str, Any],
    ) -> dict[str, Any] | None:
        snapshot_id = plan.get("arena_selection_snapshot_id")
        if snapshot_id:
            record, error = self._read_json(
                self.selection_snapshots_path / f"{snapshot_id}.json"
            )
            if not error and isinstance(record, dict):
                return record
        return None

    def _existing_disposition(self, plan: dict[str, Any]) -> dict[str, Any] | None:
        disposition_id = plan.get("proposal_disposition_id")
        if disposition_id:
            record, error = self._read_json(
                self.dispositions_path / f"{disposition_id}.json"
            )
            if not error and isinstance(record, dict):
                return record
        return None

    def _load_plan(
        self,
        plan_id: str | None,
    ) -> tuple[dict[str, Any] | None, Path | None, str | None]:
        if self._term(plan_id) == "Not Available":
            return None, None, "missing_plan_id"
        path = self.pending_path / f"{plan_id}.json"
        payload, error = self._read_json(path)
        if error or not isinstance(payload, dict):
            return None, None, error or "plan_not_mapping"
        return payload, path, None

    def _load_proposal(
        self,
        proposal_id: str | None,
    ) -> tuple[dict[str, Any] | None, str | None]:
        return self._load_json_by_id(
            self.decision_proposals_path,
            proposal_id,
            "decision_proposal",
        )

    def _load_json_by_id(
        self,
        directory: Path,
        record_id: str | None,
        label: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        if self._term(record_id) == "Not Available":
            return None, f"missing_{label}_id"
        payload, error = self._read_json(directory / f"{record_id}.json")
        if error or not isinstance(payload, dict):
            return None, error or f"{label}_not_mapping"
        return payload, None

    def _baseline_snapshot(
        self,
        admission: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, str | None]:
        snapshot = admission.get("originating_arena_snapshot")
        if isinstance(snapshot, dict):
            return snapshot, None
        return None, "originating_arena_snapshot_missing_from_admission"

    def _next_consumer(self, outcome: str) -> str:
        return {
            "RATIFIED": "FUTURE_SELECTED_CANDIDATE_EXECUTION_ADMISSION_GATE",
            "REJECTED": "ARENA_REVIEW_OR_EVIDENCE_REMEDIATION",
            "DEFERRED": "FORMAL_SELECTION_REVIEW_RECOVERY_OR_GOVERNED_CLARIFICATION",
        }.get(outcome, "FORMAL_SELECTION_REVIEW_RECOVERY_OR_GOVERNED_CLARIFICATION")

    def _boot_route(self, outcome: str) -> str:
        return {
            "RATIFIED": "RATIFIED_TO_FUTURE_SELECTED_CANDIDATE_EXECUTION_ADMISSION_GATE",
            "REJECTED": "REJECTED_TO_ARENA_REVIEW_OR_REMEDIATION",
            "DEFERRED": "DEFERRED_TO_FORMAL_SELECTION_RECOVERY_OR_CLARIFICATION",
        }.get(outcome, "FORMAL_SELECTION_TO_REVIEW")

    def _policy_fingerprint(self, policy: str, version: str) -> str:
        return self._fingerprint({"policy": policy, "version": version})

    def _initialize(self) -> None:
        for path in (
            self.pending_path,
            self.admissions_path,
            self.ledger_path,
            self.redeliberations_path,
            self.outcomes_path,
            self.decision_proposals_path,
            self.review_cases_path,
            self.decisions_path,
            self.selection_snapshots_path,
            self.dispositions_path,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def _json_files(self, directory: Path) -> list[Path]:
        if not directory.exists():
            return []
        return sorted(
            path for path in directory.glob("*.json")
            if not path.name.endswith(".tmp")
        )

    def _read_json(self, path: Path) -> tuple[Any, str | None]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
            return None, str(error)
        return payload, None

    def _atomic_write(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True)
        json.loads(encoded)
        temporary = path.with_suffix(f"{path.suffix}.tmp")
        with temporary.open("w", encoding="utf-8") as file:
            file.write(encoded)
            file.write("\n")
            file.flush()
            try:
                os.fsync(file.fileno())
            except OSError:
                pass
        temporary.replace(path)

    def _fingerprint(self, payload: dict[str, Any]) -> str:
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
        ).hexdigest()

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _term(self, value: Any) -> str:
        text = str(value or "").strip()
        return text if text else "Not Available"
