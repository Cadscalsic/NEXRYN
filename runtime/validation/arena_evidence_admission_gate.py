from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ArenaEvidenceAdmissionGate:
    """Admits accepted validation evidence into a bounded Arena redeliberation."""

    BOUNDARY = (
        "ARENA_EVIDENCE_ADMISSION_AUTHORITY_MAY_ADMIT_ONE_VERIFIED_ACCEPTED_EVIDENCE_ARTIFACT_AND_AUTHORIZE_BOUNDED_REDELIBERATION_BUT_CANNOT_SELECT_A_WINNER_OR_GRANT_EXECUTION_TRUTH_TRUST_OR_GRADUATION_AUTHORITY"
    )
    IMMUTABILITY_BOUNDARY = (
        "ACCEPTED_EVIDENCE_AND_ORIGINAL_CANDIDATES_REMAIN_IMMUTABLE_WHILE_ARENA_ADMISSION_AND_REDELIBERATION_CREATE_NEW_AUDITABLE_DERIVED_RECORDS"
    )
    ADMISSION_AUTHORITY = "ARENA_EVIDENCE_ADMISSION_GATE"
    REDELIBERATION_AUTHORITY = "COGNITIVE_CANDIDATE_ARENA"
    ADMISSION_POLICY_VERSION = "1.0"
    REDELIBERATION_POLICY_VERSION = "1.0"
    EFFECT_POLICY_VERSION = "1.0"
    POSITIVE_EFFECT = 0.05
    CONTRADICTION_EFFECT = -0.05
    MIN_PROPOSAL_MARGIN = 0.02

    def __init__(
        self,
        root_path: str | os.PathLike[str] = (
            "runtime/state/evidence_acquisition_plans"
        ),
    ):
        self.root_path = Path(root_path)
        self.pending_path = self.root_path / "pending"
        self.evidence_decisions_path = self.root_path / "evidence_decisions"
        self.accepted_evidence_path = self.root_path / "accepted_evidence"
        self.admissions_path = self.root_path / "arena_evidence_admissions"
        self.ledger_path = self.root_path / "arena_evidence_ledger"
        self.redeliberations_path = self.root_path / "arena_redeliberations"
        self.outcomes_path = self.root_path / "arena_deliberative_outcomes"
        self.decision_proposals_path = self.root_path / "decision_proposals"

    def admit_accepted_evidence(self) -> dict[str, Any]:
        self._initialize()
        reports = []
        for plan_path in self._plan_files(self.pending_path):
            plan, error = self._read_json(plan_path)
            if error or not isinstance(plan, dict):
                continue
            if plan.get("lifecycle_state") in {
                "EVIDENCE_ACCEPTED",
                "EVIDENCE_ADMITTED_TO_ARENA",
                "ARENA_REDELIBERATION_COMPLETED",
            }:
                reports.append(self.admit_plan(plan.get("plan_id")))
        terminal = [
            report for report in reports
            if report.get("redeliberation_completed") is True
        ]
        current = terminal[0] if terminal else reports[0] if reports else {}
        return {
            "system": "arena_evidence_admission_gate",
            "responsible_component": "ARENA_EVIDENCE_ADMISSION_GATE",
            "arena_evidence_admission_attempted": bool(reports),
            "arena_redeliberation_count": len(terminal),
            "arena_admission_reports": reports,
            **self._public_projection(current),
        }

    def admit_plan(self, plan_id: str | None) -> dict[str, Any]:
        self._initialize()
        base = self._base_report(plan_id)
        plan, plan_path, plan_error = self._load_plan(plan_id)
        if plan_error or not plan or not plan_path:
            return self._blocked(
                base,
                "BLOCKED_INVALID_PLAN_STATE",
                plan_error or "plan_not_found",
                "plan_load",
                "restore_accepted_evidence_plan",
            )
        existing_outcome = self._existing_outcome(plan)
        if existing_outcome:
            admission = self._existing_admission(plan) or {}
            ledger = self._existing_ledger(plan) or {}
            snapshot = self._existing_redeliberation(plan) or {}
            return self._terminal_report(
                base,
                plan,
                admission,
                ledger,
                snapshot,
                existing_outcome,
                admission_creation_result="REUSED_EXISTING_ARENA_ADMISSION",
                ledger_creation_result="REUSED_EXISTING_ARENA_LEDGER_ENTRY",
                redeliberation_snapshot_creation_result=(
                    "REUSED_EXISTING_REDELIBERATION_SNAPSHOT"
                ),
                deliberative_outcome_creation_result=(
                    "REUSED_EXISTING_DELIBERATIVE_OUTCOME"
                ),
            )

        admission = self._admission(plan)
        if admission["arena_admission_state"] != "ADMITTED":
            return {**base, **admission}

        evidence_decision = admission["evidence_decision"]
        accepted_evidence = admission["accepted_evidence"]
        snapshot = admission["originating_arena_snapshot"]
        admission_started_at = self._now()
        fingerprint = self._admission_fingerprint(
            plan,
            evidence_decision,
            accepted_evidence,
            snapshot,
        )
        admission_id = (
            f"arena_evidence_admission_{hashlib.sha1(fingerprint.encode()).hexdigest()[:12]}"
        )
        ledger_fingerprint = self._ledger_fingerprint(
            admission_id,
            plan,
            evidence_decision,
            accepted_evidence,
            snapshot,
        )
        ledger_id = (
            f"arena_evidence_ledger_{hashlib.sha1(ledger_fingerprint.encode()).hexdigest()[:12]}"
        )
        existing_admission = self._existing_admission_by_fingerprint(fingerprint)
        if existing_admission:
            return self._blocked(
                {**base, **self._identity(plan, evidence_decision, accepted_evidence)},
                "BLOCKED_DUPLICATE_ARENA_ADMISSION",
                "equivalent_evidence_already_admitted",
                "duplicate_admission_check",
                "reuse_existing_arena_admission",
            )
        admission_record = self._admission_record(
            admission_id,
            fingerprint,
            plan,
            evidence_decision,
            accepted_evidence,
            snapshot,
            admission_started_at,
        )
        ledger_entry = self._ledger_entry(
            ledger_id,
            ledger_fingerprint,
            admission_record,
            plan,
            evidence_decision,
            accepted_evidence,
            snapshot,
        )
        try:
            reviewing_plan = {
                **plan,
                "updated_at": admission_started_at,
                "lifecycle_state": "ARENA_EVIDENCE_ADMISSION_REVIEW",
                "arena_admission_invoked": True,
                "arena_admission_state": "ADMISSION_REVIEW_STARTED",
                "active_arena_admission_lease": True,
            }
            self._atomic_write(plan_path, reviewing_plan)
            self._atomic_write(
                self.admissions_path / f"{admission_id}.json",
                admission_record,
            )
            self._atomic_write(self.ledger_path / f"{ledger_id}.json", ledger_entry)
            admitted_plan = {
                **reviewing_plan,
                "updated_at": self._now(),
                "lifecycle_state": "EVIDENCE_ADMITTED_TO_ARENA",
                "arena_admission_state": "ADMITTED",
                "arena_evidence_admission_id": admission_id,
                "arena_evidence_ledger_entry_id": ledger_id,
                "arena_evidence_admitted": True,
                "arena_evidence_consumed": False,
                "active_arena_admission_lease": False,
                "boot_recovery_route": "ADMITTED_EVIDENCE_TO_ARENA_REDELIBERATION",
            }
            self._atomic_write(plan_path, admitted_plan)
        except (OSError, TypeError, ValueError) as error:
            return self._blocked(
                {**base, **self._identity(plan, evidence_decision, accepted_evidence)},
                "BLOCKED_ADMISSION_PERSISTENCE_FAILURE",
                str(error),
                "arena_admission_persistence",
                "retry_idempotent_arena_evidence_admission",
            )

        return self._redeliberate(
            base,
            admitted_plan,
            plan_path,
            admission_record,
            ledger_entry,
            snapshot,
            evidence_decision,
            accepted_evidence,
            "CREATED_NEW_ARENA_ADMISSION",
            "CREATED_NEW_ARENA_LEDGER_ENTRY",
        )

    def _admission(self, plan: dict[str, Any]) -> dict[str, Any]:
        if plan.get("lifecycle_state") != "EVIDENCE_ACCEPTED":
            return self._admission_block(
                "BLOCKED_INVALID_PLAN_STATE",
                f"expected_EVIDENCE_ACCEPTED_observed_{plan.get('lifecycle_state')}",
                "plan_lifecycle",
                "restore_accepted_evidence_state_before_arena_admission",
            )
        if plan.get("active_arena_admission_lease") is True:
            return self._admission_block(
                "BLOCKED_ACTIVE_ADMISSION",
                "active_arena_admission_lease_present",
                "arena_admission_lease",
                "recover_or_clear_active_admission_lease",
            )
        for field in (
            "truth_authority",
            "trust_authority",
            "graduation_authority",
            "candidate_execution_authority",
        ):
            if plan.get(field) != "NONE":
                return self._admission_block(
                    "BLOCKED_CONSTITUTIONAL_VIOLATION",
                    f"{field}_not_none",
                    "authority_validation",
                    "restore_constitutional_authority_boundaries",
                )
        decision, decision_error = self._load_evidence_decision(
            plan.get("evidence_decision_id")
        )
        if decision_error or not decision:
            return self._admission_block(
                "BLOCKED_MISSING_EVIDENCE_DECISION",
                decision_error or "evidence_decision_not_found",
                "evidence_decision_load",
                "restore_evidence_decision",
            )
        accepted, accepted_error = self._load_accepted_evidence(
            plan.get("accepted_evidence_id")
        )
        if accepted_error or not accepted:
            return self._admission_block(
                "BLOCKED_MISSING_ACCEPTED_EVIDENCE",
                accepted_error or "accepted_evidence_not_found",
                "accepted_evidence_load",
                "restore_accepted_evidence_artifact",
            )
        if decision.get("evidence_acceptance_state") != "ACCEPTED":
            return self._admission_block(
                "BLOCKED_EVIDENCE_NOT_ACCEPTED",
                f"observed_{decision.get('evidence_acceptance_state')}",
                "evidence_acceptance_validation",
                "do_not_admit_nonaccepted_evidence",
            )
        if (
            decision.get("evidence_admissibility_state") != "ADMISSIBLE"
            or decision.get("evidence_sufficiency_state") != "SUFFICIENT"
        ):
            return self._admission_block(
                "BLOCKED_EVIDENCE_NOT_ACCEPTED",
                "accepted_state_without_admissible_sufficient_decision",
                "evidence_contract_validation",
                "review_evidence_decision_integrity",
            )
        alignment = self._alignment_failures(plan, decision, accepted)
        if alignment:
            return self._admission_block(
                "BLOCKED_RECORD_ALIGNMENT_FAILURE",
                ",".join(alignment),
                "record_alignment",
                "repair_plan_decision_evidence_alignment",
            )
        direction = decision.get("evidence_direction")
        if direction not in {"SUPPORTING", "CONTRADICTING", "NEUTRAL", "INCONCLUSIVE"}:
            return self._admission_block(
                "BLOCKED_EVIDENCE_DIRECTION_MISSING",
                f"unsupported_or_missing_direction_{direction}",
                "evidence_direction",
                "repair_evidence_direction",
            )
        if decision.get("candidate_attribution_state") != "ATTRIBUTED":
            return self._admission_block(
                "BLOCKED_CANDIDATE_ATTRIBUTION_FAILURE",
                "candidate_attribution_not_satisfied",
                "candidate_attribution",
                "review_candidate_attribution",
            )
        if decision.get("operation_attribution_state") != "ATTRIBUTED":
            return self._admission_block(
                "BLOCKED_OPERATION_ATTRIBUTION_FAILURE",
                "operation_attribution_not_satisfied",
                "operation_attribution",
                "review_operation_attribution",
            )
        if decision.get("evidence_contamination_state") != "CLEAR":
            return self._admission_block(
                "BLOCKED_POST_EVALUATION_INTEGRITY_FAILURE",
                "evidence_contamination_not_clear",
                "post_evaluation_integrity",
                "review_contaminated_evidence",
            )
        snapshot = accepted.get("originating_arena_snapshot")
        if not isinstance(snapshot, dict):
            return self._admission_block(
                "BLOCKED_MISSING_ORIGINATING_ARENA",
                "originating_arena_snapshot_missing",
                "originating_arena_load",
                "restore_originating_arena_snapshot",
            )
        if snapshot.get("winner_selected") is True:
            return self._admission_block(
                "BLOCKED_WINNER_ALREADY_SELECTED",
                "originating_arena_winner_already_selected",
                "arena_open_state",
                "do_not_redeliberate_closed_arena",
            )
        target = accepted.get("target_candidate")
        candidates = self._candidate_rows(snapshot)
        target_row = next(
            (row for row in candidates if row.get("candidate_id") == target),
            None,
        )
        if not target_row:
            return self._admission_block(
                "BLOCKED_TARGET_CANDIDATE_NOT_IN_ARENA",
                "target_candidate_missing_from_originating_arena",
                "target_candidate_resolution",
                "repair_arena_evidence_target_reference",
            )
        if target_row.get("operation") != accepted.get("target_operation"):
            return self._admission_block(
                "BLOCKED_TARGET_OPERATION_MISMATCH",
                "target_operation_not_represented_by_candidate",
                "target_operation_resolution",
                "repair_operation_attribution",
            )
        if self._existing_admission(plan):
            return self._admission_block(
                "BLOCKED_DUPLICATE_ARENA_ADMISSION",
                "accepted_evidence_already_admitted_to_arena",
                "duplicate_admission_check",
                "reuse_existing_arena_admission",
            )
        return {
            "arena_admission_state": "ADMITTED",
            "arena_admission_reason": (
                "accepted_evidence_satisfies_arena_admission_contract"
            ),
            "blocked_stage": "none",
            "responsible_component": "ARENA_EVIDENCE_ADMISSION_GATE",
            "recoverability": "IDEMPOTENT",
            "recommended_action": "create_arena_admission_and_redeliberate_once",
            "evidence_decision": decision,
            "accepted_evidence": accepted,
            "originating_arena_snapshot": snapshot,
        }

    def _redeliberate(
        self,
        base: dict[str, Any],
        plan: dict[str, Any],
        plan_path: Path,
        admission: dict[str, Any],
        ledger: dict[str, Any],
        baseline: dict[str, Any],
        decision: dict[str, Any],
        accepted: dict[str, Any],
        admission_result: str,
        ledger_result: str,
    ) -> dict[str, Any]:
        started_at = self._now()
        redelib_fingerprint = self._redeliberation_fingerprint(
            admission,
            ledger,
            baseline,
        )
        redelib_id = (
            f"arena_redeliberation_{hashlib.sha1(redelib_fingerprint.encode()).hexdigest()[:12]}"
        )
        existing_snapshot = self._existing_redeliberation_by_fingerprint(
            redelib_fingerprint
        )
        if existing_snapshot:
            existing_outcome = self._existing_outcome(plan) or {}
            return self._terminal_report(
                base,
                plan,
                admission,
                ledger,
                existing_snapshot,
                existing_outcome,
                admission_creation_result=admission_result,
                ledger_creation_result=ledger_result,
                redeliberation_snapshot_creation_result=(
                    "REUSED_EXISTING_REDELIBERATION_SNAPSHOT"
                ),
                deliberative_outcome_creation_result=(
                    "REUSED_EXISTING_DELIBERATIVE_OUTCOME"
                ),
            )
        try:
            started_plan = {
                **plan,
                "updated_at": started_at,
                "lifecycle_state": "ARENA_REDELIBERATION_STARTED",
                "redeliberation_invoked": True,
                "redeliberation_started": True,
                "redeliberation_id": redelib_id,
                "active_redeliberation_lease": True,
            }
            self._atomic_write(plan_path, started_plan)
            redelib_snapshot = self._redeliberation_snapshot(
                redelib_id,
                redelib_fingerprint,
                admission,
                ledger,
                baseline,
                decision,
                accepted,
                started_at,
            )
            outcome = self._deliberative_outcome(
                started_plan,
                admission,
                ledger,
                redelib_snapshot,
            )
            self._atomic_write(
                self.redeliberations_path / f"{redelib_id}.json",
                redelib_snapshot,
            )
            self._atomic_write(
                self.outcomes_path / f"{outcome['deliberative_outcome_id']}.json",
                outcome,
            )
            proposal_record = self._decision_proposal_record(
                started_plan,
                admission,
                ledger,
                redelib_snapshot,
                outcome,
                baseline,
            )
            if proposal_record:
                self._atomic_write(
                    self.decision_proposals_path
                    / f"{proposal_record['decision_proposal_id']}.json",
                    proposal_record,
                )
            consumed_at = self._now()
            consumed_ledger = {
                **ledger,
                "consumed_by_redeliberation_id": redelib_id,
                "consumed_at": consumed_at,
            }
            self._atomic_write(
                self.ledger_path / f"{ledger['arena_evidence_ledger_entry_id']}.json",
                consumed_ledger,
            )
            final_plan = {
                **started_plan,
                "updated_at": consumed_at,
                "lifecycle_state": "ARENA_REDELIBERATION_COMPLETED",
                "arena_evidence_consumed": True,
                "redeliberation_completed": True,
                "redeliberation_snapshot_id": redelib_id,
                "deliberative_outcome_id": outcome["deliberative_outcome_id"],
                "redeliberation_outcome": outcome["redeliberation_outcome"],
                "next_consumer": outcome.get("next_consumer"),
                "decision_proposal_id": outcome.get("decision_proposal_id"),
                "decision_proposal_state": outcome.get(
                    "decision_proposal_state",
                    "NONE",
                ),
                "decision_proposal_available": outcome.get(
                    "decision_proposal_available",
                    False,
                ),
                "boot_recovery_route": self._route(outcome["redeliberation_outcome"]),
                "active_redeliberation_lease": False,
                "formal_selection_invoked": False,
                "tie_resolved": False,
                "winner_selected": False,
                "selected_candidate": "NONE",
                "candidate_execution_authority": "NONE",
                "truth_authority": "NONE",
                "trust_authority": "NONE",
                "graduation_authority": "NONE",
            }
            self._atomic_write(plan_path, final_plan)
        except (OSError, TypeError, ValueError) as error:
            return self._blocked(
                {**base, **self._identity(plan, decision, accepted)},
                "BLOCKED_ADMISSION_PERSISTENCE_FAILURE",
                str(error),
                "redeliberation_persistence",
                "retry_idempotent_arena_redeliberation",
            )
        return self._terminal_report(
            base,
            final_plan,
            admission,
            consumed_ledger,
            redelib_snapshot,
            outcome,
            admission_creation_result=admission_result,
            ledger_creation_result=ledger_result,
            redeliberation_snapshot_creation_result=(
                "CREATED_NEW_REDELIBERATION_SNAPSHOT"
            ),
            deliberative_outcome_creation_result=(
                "CREATED_NEW_DELIBERATIVE_OUTCOME"
            ),
        )

    def _redeliberation_snapshot(
        self,
        redelib_id: str,
        fingerprint: str,
        admission: dict[str, Any],
        ledger: dict[str, Any],
        baseline: dict[str, Any],
        decision: dict[str, Any],
        accepted: dict[str, Any],
        started_at: str,
    ) -> dict[str, Any]:
        target = accepted.get("target_candidate")
        direction = decision.get("evidence_direction")
        candidates = []
        for row in self._candidate_rows(baseline):
            baseline_score = float(row.get("baseline_score", row.get("score", 0.0)) or 0.0)
            effect = 0.0
            if row.get("candidate_id") == target:
                if direction == "SUPPORTING":
                    effect = self.POSITIVE_EFFECT
                elif direction == "CONTRADICTING":
                    effect = self.CONTRADICTION_EFFECT
            derived_score = max(0.0, min(1.0, baseline_score + effect))
            candidates.append({
                **row,
                "original_score": baseline_score,
                "evidence_effect": effect,
                "derived_score": round(derived_score, 4),
                "evidence_direction_applied": direction,
                "evidence_counted_as_candidate_source": False,
            })
        ranked = sorted(
            candidates,
            key=lambda item: (-float(item.get("derived_score", 0.0)), str(item.get("candidate_id"))),
        )
        for index, row in enumerate(ranked, start=1):
            row["derived_rank"] = index
        original_order = [
            row.get("candidate_id")
            for row in sorted(
                candidates,
                key=lambda item: (-float(item.get("original_score", 0.0)), str(item.get("candidate_id"))),
            )
        ]
        derived_order = [row.get("candidate_id") for row in ranked]
        return {
            "schema_version": "1.0",
            "redeliberation_snapshot_id": redelib_id,
            "redeliberation_snapshot_fingerprint": fingerprint,
            "arena_evidence_admission_id": admission.get(
                "arena_evidence_admission_id"
            ),
            "arena_evidence_ledger_entry_id": ledger.get(
                "arena_evidence_ledger_entry_id"
            ),
            "originating_arena_id": baseline.get("arena_id"),
            "originating_arena_snapshot_id": admission.get(
                "originating_arena_snapshot_id"
            ),
            "baseline_snapshot_loaded": True,
            "candidate_evidence_profiles_rebuilt": True,
            "evidence_direction_preserved": True,
            "evidence_direction": direction,
            "evidence_effect_policy_id": "bounded_directional_evidence_effect",
            "evidence_effect_policy_version": self.EFFECT_POLICY_VERSION,
            "evidence_effect_applied": True,
            "candidate_profiles": ranked,
            "candidate_scores_recomputed": True,
            "candidate_score_changed": any(
                row.get("evidence_effect") != 0.0 for row in ranked
            ),
            "candidate_ranking_recomputed": True,
            "candidate_ranking_changed": original_order != derived_order,
            "cross_source_consensus_recomputed": True,
            "cross_source_consensus_changed": False,
            "cross_source_consensus_state": "NO_CROSS_SOURCE_CONSENSUS",
            "validation_evidence_counted_as_candidate_source": False,
            "redeliberation_started_at": started_at,
            "redeliberation_completed_at": self._now(),
            "formal_selection_invoked": False,
            "tie_resolved": False,
            "winner_selected": False,
            "selected_candidate": "NONE",
            "candidate_execution_authority": "NONE",
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "constitutional_boundary": self.IMMUTABILITY_BOUNDARY,
        }

    def _deliberative_outcome(
        self,
        plan: dict[str, Any],
        admission: dict[str, Any],
        ledger: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        ranked = snapshot.get("candidate_profiles") or []
        top = ranked[0] if ranked else {}
        second = ranked[1] if len(ranked) > 1 else {}
        margin = round(
            float(top.get("derived_score", 0.0) or 0.0)
            - float(second.get("derived_score", 0.0) or 0.0),
            4,
        ) if top else 0.0
        eligible = bool(top.get("eligible_for_proposal", True)) if top else False
        if not ranked:
            outcome = "NO_SAFE_PROPOSAL"
            proposal_available = False
            next_consumer = "ARENA_REVIEW_OR_EVIDENCE_REMEDIATION"
        elif not eligible:
            outcome = "NO_SAFE_PROPOSAL"
            proposal_available = False
            next_consumer = "ARENA_REVIEW_OR_EVIDENCE_REMEDIATION"
        elif margin >= self.MIN_PROPOSAL_MARGIN:
            outcome = "DECISION_PROPOSAL_AVAILABLE"
            proposal_available = True
            next_consumer = "ARENA_FORMAL_SELECTION_GATE"
        elif len(ranked) > 1:
            outcome = "TIE_PERSISTS"
            proposal_available = False
            next_consumer = "EVIDENCE_REMEDIATION_PLANNER"
        else:
            outcome = "ADDITIONAL_EVIDENCE_REQUIRED"
            proposal_available = False
            next_consumer = "EVIDENCE_REMEDIATION_PLANNER"
        fingerprint = self._fingerprint({
            "plan_id": plan.get("plan_id"),
            "redeliberation_snapshot_id": snapshot.get("redeliberation_snapshot_id"),
            "outcome": outcome,
            "top_candidate": top.get("candidate_id"),
            "margin": margin,
            "policy": self.REDELIBERATION_POLICY_VERSION,
        })
        return {
            "schema_version": "1.0",
            "deliberative_outcome_id": (
                f"arena_deliberative_outcome_{hashlib.sha1(fingerprint.encode()).hexdigest()[:12]}"
            ),
            "deliberative_outcome_fingerprint": fingerprint,
            "arena_evidence_admission_id": admission.get(
                "arena_evidence_admission_id"
            ),
            "arena_evidence_ledger_entry_id": ledger.get(
                "arena_evidence_ledger_entry_id"
            ),
            "redeliberation_snapshot_id": snapshot.get(
                "redeliberation_snapshot_id"
            ),
            "redeliberation_outcome": outcome,
            "decision_proposal_available": proposal_available,
            "decision_proposal_id": (
                f"decision_proposal_{hashlib.sha1(fingerprint.encode()).hexdigest()[:12]}"
                if proposal_available
                else "NONE"
            ),
            "decision_proposal_fingerprint": fingerprint if proposal_available else "NONE",
            "decision_proposal_state": (
                "READY_FOR_FORMAL_SELECTION_REVIEW"
                if proposal_available
                else "NONE"
            ),
            "provisional_leader_available": proposal_available,
            "provisional_leader": top.get("candidate_id") if proposal_available else "NONE",
            "proposed_candidate_id": top.get("candidate_id") if proposal_available else "NONE",
            "proposed_candidate_fingerprint": (
                top.get("candidate_fingerprint")
                or self._fingerprint({
                    "candidate_id": top.get("candidate_id"),
                    "source": top.get("source"),
                    "operation": top.get("operation"),
                })
                if proposal_available else "NONE"
            ),
            "proposed_candidate_source": top.get("source") if proposal_available else "NONE",
            "proposed_operation": top.get("operation") if proposal_available else "NONE",
            "proposal_candidate_eligibility_state": (
                "SATISFIED" if eligible and proposal_available else "NOT_SATISFIED"
            ),
            "proposal_tie_break_strategy_state": (
                "SATISFIED" if proposal_available else "NOT_SATISFIED"
            ),
            "proposal_cross_source_consensus_state": "NO_CROSS_SOURCE_CONSENSUS",
            "proposal_constitutional_veto_state": "CLEAR",
            "proposal_remaining_uncertainties": [],
            "proposal_remaining_evidence_deficits": [],
            "selection_margin": margin,
            "minimum_proposal_margin": self.MIN_PROPOSAL_MARGIN,
            "remaining_tie_count": len([
                row for row in ranked
                if row.get("derived_score") == top.get("derived_score")
            ]) if top else 0,
            "next_consumer": next_consumer,
            "formal_selection_invoked": False,
            "tie_resolved": False,
            "winner_selected": False,
            "selected_candidate": "NONE",
            "candidate_execution_authority": "NONE",
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
        }

    def _admission_record(
        self,
        admission_id: str,
        fingerprint: str,
        plan: dict[str, Any],
        decision: dict[str, Any],
        accepted: dict[str, Any],
        snapshot: dict[str, Any],
        started_at: str,
    ) -> dict[str, Any]:
        target_candidate = accepted.get("target_candidate")
        target_row = next(
            (
                row
                for row in self._candidate_rows(snapshot)
                if row.get("candidate_id") == target_candidate
            ),
            {},
        )
        return {
            "schema_version": "1.0",
            "arena_evidence_admission_id": admission_id,
            "arena_evidence_admission_fingerprint": fingerprint,
            "accepted_evidence_id": accepted.get("accepted_evidence_id"),
            "accepted_evidence_fingerprint": accepted.get(
                "accepted_evidence_fingerprint"
            ),
            "evidence_decision_id": decision.get("evidence_decision_id"),
            "evidence_decision_fingerprint": decision.get(
                "evidence_decision_fingerprint"
            ),
            "plan_id": plan.get("plan_id"),
            "plan_fingerprint": plan.get("plan_fingerprint"),
            "originating_arena_id": snapshot.get("arena_id"),
            "originating_arena_snapshot_id": accepted.get(
                "originating_arena_snapshot_id"
            ),
            "originating_arena_snapshot_fingerprint": snapshot.get(
                "originating_arena_snapshot_fingerprint"
            ),
            "originating_arena_snapshot": snapshot,
            "target_candidate": target_candidate,
            "target_candidate_fingerprint": target_row.get("candidate_fingerprint"),
            "target_candidate_source": target_row.get("source"),
            "target_operation": accepted.get("target_operation"),
            "required_evidence": accepted.get("required_evidence"),
            "required_evidence_category": accepted.get(
                "required_evidence_category"
            ),
            "evidence_direction": decision.get("evidence_direction"),
            "evidence_scope": "TARGET_CANDIDATE_TARGET_OPERATION_CURRENT_ARENA_ONLY",
            "candidate_attribution_state": decision.get(
                "candidate_attribution_state"
            ),
            "operation_attribution_state": decision.get(
                "operation_attribution_state"
            ),
            "independent_validation_state": decision.get(
                "independent_validation_state"
            ),
            "contamination_state": decision.get("evidence_contamination_state"),
            "duplicate_admission_checked": True,
            "duplicate_counting_checked": True,
            "admission_policy_id": "accepted_validation_evidence_arena_admission",
            "admission_policy_version": self.ADMISSION_POLICY_VERSION,
            "admission_policy_fingerprint": self._fingerprint({
                "policy": "accepted_validation_evidence_arena_admission",
                "version": self.ADMISSION_POLICY_VERSION,
            }),
            "arena_evidence_admission_authority": self.ADMISSION_AUTHORITY,
            "arena_evidence_admission_scope": (
                "ONE_ACCEPTED_EVIDENCE_ARTIFACT_TO_ONE_ORIGINATING_ARENA"
            ),
            "admission_review_started_at": started_at,
            "admission_review_completed_at": self._now(),
            "admission_review_duration": 0,
            "arena_admission_state": "ADMITTED",
            "arena_admission_reason": (
                "accepted_evidence_satisfies_arena_admission_contract"
            ),
            "redeliberation_authorized": True,
            "redeliberation_invoked": False,
            "arena_consumed": False,
            "formal_selection_invoked": False,
            "winner_selected": False,
            "candidate_execution_authority": "NONE",
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "constitutional_boundary": self.BOUNDARY,
        }

    def _decision_proposal_record(
        self,
        plan: dict[str, Any],
        admission: dict[str, Any],
        ledger: dict[str, Any],
        snapshot: dict[str, Any],
        outcome: dict[str, Any],
        baseline: dict[str, Any],
    ) -> dict[str, Any] | None:
        if outcome.get("redeliberation_outcome") != "DECISION_PROPOSAL_AVAILABLE":
            return None
        proposal_id = outcome.get("decision_proposal_id")
        proposed_candidate = outcome.get("proposed_candidate_id")
        profiles = snapshot.get("candidate_profiles") or []
        proposed_row = next(
            (
                row for row in profiles
                if row.get("candidate_id") == proposed_candidate
            ),
            {},
        )
        fingerprint = self._fingerprint({
            "decision_proposal_id": proposal_id,
            "plan_id": plan.get("plan_id"),
            "deliberative_outcome_id": outcome.get("deliberative_outcome_id"),
            "redeliberation_snapshot_id": snapshot.get("redeliberation_snapshot_id"),
            "proposed_candidate_id": proposed_candidate,
            "proposed_candidate_fingerprint": outcome.get(
                "proposed_candidate_fingerprint"
            ),
            "selection_margin": outcome.get("selection_margin"),
            "policy": self.REDELIBERATION_POLICY_VERSION,
        })
        return {
            "schema_version": "1.0",
            "decision_proposal_id": proposal_id,
            "decision_proposal_fingerprint": fingerprint,
            "decision_proposal_state": "READY_FOR_FORMAL_SELECTION_REVIEW",
            "plan_id": plan.get("plan_id"),
            "plan_fingerprint": plan.get("plan_fingerprint"),
            "originating_arena_id": baseline.get("arena_id"),
            "originating_arena_version": baseline.get(
                "arena_version",
                "1.0",
            ),
            "baseline_snapshot_id": admission.get("originating_arena_snapshot_id"),
            "baseline_snapshot_fingerprint": baseline.get(
                "originating_arena_snapshot_fingerprint"
            ),
            "arena_evidence_admission_id": admission.get(
                "arena_evidence_admission_id"
            ),
            "arena_evidence_ledger_entry_id": ledger.get(
                "arena_evidence_ledger_entry_id"
            ),
            "redeliberation_id": snapshot.get("redeliberation_snapshot_id"),
            "redeliberation_snapshot_id": snapshot.get(
                "redeliberation_snapshot_id"
            ),
            "redeliberation_snapshot_fingerprint": snapshot.get(
                "redeliberation_snapshot_fingerprint"
            ),
            "arena_deliberative_outcome_id": outcome.get(
                "deliberative_outcome_id"
            ),
            "arena_deliberative_outcome_fingerprint": outcome.get(
                "deliberative_outcome_fingerprint"
            ),
            "proposed_candidate_id": proposed_candidate,
            "proposed_candidate_fingerprint": outcome.get(
                "proposed_candidate_fingerprint"
            ),
            "proposed_candidate_source": outcome.get("proposed_candidate_source"),
            "proposed_operation": outcome.get("proposed_operation"),
            "proposed_candidate_record": proposed_row,
            "proposed_candidates": [proposed_candidate],
            "candidate_set": profiles,
            "proposal_top_score_margin": outcome.get("selection_margin"),
            "proposal_minimum_required_margin": outcome.get(
                "minimum_proposal_margin"
            ),
            "proposal_candidate_eligibility_state": outcome.get(
                "proposal_candidate_eligibility_state"
            ),
            "proposal_cross_source_consensus_state": outcome.get(
                "proposal_cross_source_consensus_state"
            ),
            "proposal_tie_break_strategy_state": outcome.get(
                "proposal_tie_break_strategy_state"
            ),
            "proposal_remaining_uncertainties": outcome.get(
                "proposal_remaining_uncertainties",
                [],
            ),
            "proposal_remaining_evidence_deficits": outcome.get(
                "proposal_remaining_evidence_deficits",
                [],
            ),
            "proposal_constitutional_veto_state": "CLEAR",
            "validation_evidence_counted_as_candidate_source": False,
            "formal_selection_state": "NOT_INVOKED",
            "formal_selection_invoked": False,
            "winner_selected": False,
            "selected_candidate": "NONE",
            "candidate_execution_authority": "NONE",
            "candidate_execution_started": False,
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "proposal_policy_id": "bounded_arena_redeliberation_decision_proposal",
            "proposal_policy_version": self.REDELIBERATION_POLICY_VERSION,
            "proposal_policy_fingerprint": self._fingerprint({
                "policy": "bounded_arena_redeliberation_decision_proposal",
                "version": self.REDELIBERATION_POLICY_VERSION,
            }),
            "created_at": self._now(),
        }

    def _ledger_entry(
        self,
        ledger_id: str,
        fingerprint: str,
        admission: dict[str, Any],
        plan: dict[str, Any],
        decision: dict[str, Any],
        accepted: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "arena_evidence_ledger_entry_id": ledger_id,
            "arena_evidence_ledger_entry_fingerprint": fingerprint,
            "arena_evidence_admission_id": admission.get(
                "arena_evidence_admission_id"
            ),
            "accepted_evidence_id": accepted.get("accepted_evidence_id"),
            "originating_arena_id": snapshot.get("arena_id"),
            "originating_arena_snapshot_id": admission.get(
                "originating_arena_snapshot_id"
            ),
            "target_candidate": accepted.get("target_candidate"),
            "target_candidate_fingerprint": admission.get(
                "target_candidate_fingerprint"
            ),
            "target_candidate_source": admission.get("target_candidate_source"),
            "target_operation": accepted.get("target_operation"),
            "evidence_direction": decision.get("evidence_direction"),
            "evidence_category": accepted.get("required_evidence_category"),
            "evidence_scope": "TARGET_CANDIDATE_TARGET_OPERATION_CURRENT_ARENA_ONLY",
            "evidence_provenance": {
                "plan_id": plan.get("plan_id"),
                "evidence_decision_id": decision.get("evidence_decision_id"),
                "accepted_evidence_id": accepted.get("accepted_evidence_id"),
            },
            "evidence_measurement_summary": {
                "evidence_direction": decision.get("evidence_direction"),
                "evidence_acceptance_state": decision.get(
                    "evidence_acceptance_state"
                ),
            },
            "candidate_attribution_state": decision.get(
                "candidate_attribution_state"
            ),
            "operation_attribution_state": decision.get(
                "operation_attribution_state"
            ),
            "independent_validation_state": decision.get(
                "independent_validation_state"
            ),
            "contamination_state": decision.get("evidence_contamination_state"),
            "admission_policy_version": self.ADMISSION_POLICY_VERSION,
            "redeliberation_policy_version": self.REDELIBERATION_POLICY_VERSION,
            "counting_scope": "TARGET_CANDIDATE_TARGET_OPERATION_CURRENT_ARENA_ONLY",
            "counting_eligibility": "ELIGIBLE",
            "cross_source_consensus_eligibility": "NOT_A_CANDIDATE_SOURCE",
            "admitted_at": self._now(),
            "consumed_by_redeliberation_id": "NONE",
            "consumed_at": "NONE",
            "revocation_state": "ACTIVE",
            "supersession_state": "CURRENT",
        }

    def _terminal_report(
        self,
        base: dict[str, Any],
        plan: dict[str, Any],
        admission: dict[str, Any],
        ledger: dict[str, Any],
        snapshot: dict[str, Any],
        outcome: dict[str, Any],
        *,
        admission_creation_result: str,
        ledger_creation_result: str,
        redeliberation_snapshot_creation_result: str,
        deliberative_outcome_creation_result: str,
    ) -> dict[str, Any]:
        return {
            **base,
            "plan_id": plan.get("plan_id"),
            "evidence_decision_id": admission.get("evidence_decision_id"),
            "accepted_evidence_id": admission.get("accepted_evidence_id"),
            "originating_arena_id": admission.get("originating_arena_id"),
            "originating_arena_snapshot_id": admission.get(
                "originating_arena_snapshot_id"
            ),
            "target_candidate": admission.get("target_candidate"),
            "target_operation": admission.get("target_operation"),
            "evidence_direction": admission.get("evidence_direction"),
            "evidence_accepted": True,
            "accepted_evidence_artifact_available": True,
            "arena_admission_invoked": True,
            "arena_admission_review_completed": True,
            "arena_admission_state": "ADMITTED",
            "arena_admission_reason": (
                "accepted_evidence_satisfies_arena_admission_contract"
            ),
            "arena_admission_record_created": True,
            "arena_evidence_admission_id": admission.get(
                "arena_evidence_admission_id"
            ),
            "arena_admission_record_creation_result": admission_creation_result,
            "arena_evidence_ledger_entry_created": True,
            "arena_evidence_ledger_entry_id": ledger.get(
                "arena_evidence_ledger_entry_id"
            ),
            "arena_evidence_ledger_creation_result": ledger_creation_result,
            "arena_evidence_admitted": True,
            "arena_evidence_consumed": True,
            "redeliberation_invoked": True,
            "redeliberation_started": True,
            "redeliberation_completed": True,
            "redeliberation_admission_evaluated": True,
            "redeliberation_admission_state": "ADMITTED_TO_REDELIBERATION",
            "arena_redeliberation_authority": self.REDELIBERATION_AUTHORITY,
            "arena_redeliberation_scope": "ONE_BOUNDED_REDELIBERATION_CYCLE",
            "baseline_snapshot_loaded": True,
            "redeliberation_snapshot_created": True,
            "redeliberation_snapshot_id": snapshot.get(
                "redeliberation_snapshot_id"
            ),
            "redeliberation_snapshot_creation_result": (
                redeliberation_snapshot_creation_result
            ),
            "candidate_evidence_profiles_rebuilt": True,
            "evidence_direction_preserved": True,
            "evidence_effect_policy_resolved": True,
            "evidence_effect_applied": True,
            "candidate_scores_recomputed": True,
            "candidate_score_changed": snapshot.get("candidate_score_changed", False),
            "candidate_ranking_recomputed": True,
            "candidate_ranking_changed": snapshot.get(
                "candidate_ranking_changed",
                False,
            ),
            "cross_source_consensus_recomputed": True,
            "cross_source_consensus_changed": False,
            "cross_source_consensus_state": "NO_CROSS_SOURCE_CONSENSUS",
            "validation_evidence_counted_as_candidate_source": False,
            "tie_break_strategy_applied": True,
            "tie_break_strategy_satisfied": outcome.get(
                "decision_proposal_available",
                False,
            ),
            "provisional_leader_available": outcome.get(
                "provisional_leader_available",
                False,
            ),
            "decision_proposal_available": outcome.get(
                "decision_proposal_available",
                False,
            ),
            "decision_proposal_id": outcome.get("decision_proposal_id", "NONE"),
            "deliberative_outcome_id": outcome.get("deliberative_outcome_id"),
            "deliberative_outcome_creation_result": (
                deliberative_outcome_creation_result
            ),
            "redeliberation_outcome": outcome.get("redeliberation_outcome"),
            "remaining_tie_count": outcome.get("remaining_tie_count", 0),
            "next_consumer": outcome.get("next_consumer"),
            "formal_selection_invoked": False,
            "tie_resolved": False,
            "winner_selected": False,
            "selected_candidate": "NONE",
            "candidate_execution_authority": "NONE",
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "constitutional_boundary": self.BOUNDARY,
            "immutability_boundary": self.IMMUTABILITY_BOUNDARY,
        }

    def _alignment_failures(
        self,
        plan: dict[str, Any],
        decision: dict[str, Any],
        accepted: dict[str, Any],
    ) -> list[str]:
        failures = []
        for key in ("plan_id", "evidence_decision_id", "accepted_evidence_id"):
            plan_value = plan.get(key)
            decision_value = decision.get(key)
            accepted_value = accepted.get(key)
            if key == "accepted_evidence_id":
                decision_value = decision.get(key)
            if plan_value and decision_value and plan_value != decision_value:
                failures.append(f"{key}_plan_decision_mismatch")
            if plan_value and accepted_value and plan_value != accepted_value:
                failures.append(f"{key}_plan_evidence_mismatch")
        if accepted.get("evidence_decision_id") != decision.get("evidence_decision_id"):
            failures.append("accepted_evidence_decision_id_mismatch")
        return failures

    def _candidate_rows(self, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
        rows = snapshot.get("candidate_rows") or snapshot.get("candidates") or []
        return [row for row in rows if isinstance(row, dict)]

    def _route(self, outcome: str) -> str:
        return {
            "DECISION_PROPOSAL_AVAILABLE": (
                "DECISION_PROPOSAL_TO_ARENA_FORMAL_SELECTION_GATE"
            ),
            "TIE_PERSISTS": "TIE_PERSISTS_TO_EVIDENCE_REMEDIATION_PLANNER",
            "NO_SAFE_PROPOSAL": "NO_SAFE_PROPOSAL_TO_ARENA_REVIEW_OR_REMEDIATION",
            "CONFLICT_REQUIRES_REVIEW": (
                "CONFLICT_TO_GOVERNED_ARENA_CONFLICT_REVIEW"
            ),
            "ADDITIONAL_EVIDENCE_REQUIRED": (
                "ADDITIONAL_EVIDENCE_TO_EVIDENCE_REMEDIATION_PLANNER"
            ),
        }.get(outcome, "ARENA_REDELIBERATION_TO_REVIEW")

    def _admission_fingerprint(
        self,
        plan: dict[str, Any],
        decision: dict[str, Any],
        accepted: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> str:
        return self._fingerprint({
            "plan_id": plan.get("plan_id"),
            "accepted_evidence_fingerprint": accepted.get(
                "accepted_evidence_fingerprint"
            ),
            "evidence_decision_fingerprint": decision.get(
                "evidence_decision_fingerprint"
            ),
            "arena": snapshot.get("arena_id"),
            "snapshot": snapshot.get("originating_arena_snapshot_fingerprint"),
            "target_candidate": accepted.get("target_candidate"),
            "target_operation": accepted.get("target_operation"),
            "policy": self.ADMISSION_POLICY_VERSION,
        })

    def _ledger_fingerprint(
        self,
        admission_id: str,
        plan: dict[str, Any],
        decision: dict[str, Any],
        accepted: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> str:
        return self._fingerprint({
            "arena_evidence_admission_id": admission_id,
            "plan_id": plan.get("plan_id"),
            "accepted_evidence_id": accepted.get("accepted_evidence_id"),
            "evidence_direction": decision.get("evidence_direction"),
            "arena": snapshot.get("arena_id"),
            "counting_scope": "TARGET_CANDIDATE_TARGET_OPERATION_CURRENT_ARENA_ONLY",
        })

    def _redeliberation_fingerprint(
        self,
        admission: dict[str, Any],
        ledger: dict[str, Any],
        snapshot: dict[str, Any],
    ) -> str:
        return self._fingerprint({
            "admission": admission.get("arena_evidence_admission_fingerprint"),
            "ledger": ledger.get("arena_evidence_ledger_entry_fingerprint"),
            "baseline": snapshot.get("originating_arena_snapshot_fingerprint"),
            "policy": self.REDELIBERATION_POLICY_VERSION,
            "effect_policy": self.EFFECT_POLICY_VERSION,
        })

    def _existing_admission(self, plan: dict[str, Any]) -> dict[str, Any] | None:
        admission_id = plan.get("arena_evidence_admission_id")
        if admission_id:
            record, error = self._read_json(
                self.admissions_path / f"{admission_id}.json"
            )
            if not error and isinstance(record, dict):
                return record
        for path in self._plan_files(self.admissions_path):
            record, error = self._read_json(path)
            if error or not isinstance(record, dict):
                continue
            if record.get("plan_id") == plan.get("plan_id"):
                return record
        return None

    def _existing_admission_by_fingerprint(
        self,
        fingerprint: str,
    ) -> dict[str, Any] | None:
        for path in self._plan_files(self.admissions_path):
            record, error = self._read_json(path)
            if error or not isinstance(record, dict):
                continue
            if record.get("arena_evidence_admission_fingerprint") == fingerprint:
                return record
        return None

    def _existing_ledger(self, plan: dict[str, Any]) -> dict[str, Any] | None:
        ledger_id = plan.get("arena_evidence_ledger_entry_id")
        if ledger_id:
            record, error = self._read_json(self.ledger_path / f"{ledger_id}.json")
            if not error and isinstance(record, dict):
                return record
        for path in self._plan_files(self.ledger_path):
            record, error = self._read_json(path)
            if error or not isinstance(record, dict):
                continue
            if record.get("accepted_evidence_id") == plan.get("accepted_evidence_id"):
                return record
        return None

    def _existing_redeliberation(self, plan: dict[str, Any]) -> dict[str, Any] | None:
        redelib_id = plan.get("redeliberation_snapshot_id") or plan.get(
            "redeliberation_id"
        )
        if redelib_id:
            record, error = self._read_json(
                self.redeliberations_path / f"{redelib_id}.json"
            )
            if not error and isinstance(record, dict):
                return record
        for path in self._plan_files(self.redeliberations_path):
            record, error = self._read_json(path)
            if error or not isinstance(record, dict):
                continue
            if record.get("arena_evidence_admission_id") == plan.get(
                "arena_evidence_admission_id"
            ):
                return record
        return None

    def _existing_redeliberation_by_fingerprint(
        self,
        fingerprint: str,
    ) -> dict[str, Any] | None:
        for path in self._plan_files(self.redeliberations_path):
            record, error = self._read_json(path)
            if error or not isinstance(record, dict):
                continue
            if record.get("redeliberation_snapshot_fingerprint") == fingerprint:
                return record
        return None

    def _existing_outcome(self, plan: dict[str, Any]) -> dict[str, Any] | None:
        outcome_id = plan.get("deliberative_outcome_id")
        if outcome_id:
            record, error = self._read_json(self.outcomes_path / f"{outcome_id}.json")
            if not error and isinstance(record, dict):
                return record
        for path in self._plan_files(self.outcomes_path):
            record, error = self._read_json(path)
            if error or not isinstance(record, dict):
                continue
            snapshot_id = plan.get("redeliberation_snapshot_id") or plan.get(
                "redeliberation_id"
            )
            if snapshot_id and record.get("redeliberation_snapshot_id") == snapshot_id:
                return record
        return None

    def _load_plan(
        self,
        plan_id: str | None,
    ) -> tuple[dict[str, Any] | None, Path | None, str | None]:
        if self._term(plan_id) == "Not Available":
            return None, None, "missing_plan_id"
        path = self.pending_path / f"{plan_id}.json"
        plan, error = self._read_json(path)
        if error or not isinstance(plan, dict):
            return None, None, error or "plan_not_mapping"
        return plan, path, None

    def _load_evidence_decision(
        self,
        decision_id: str | None,
    ) -> tuple[dict[str, Any] | None, str | None]:
        if self._term(decision_id) == "Not Available":
            return None, "missing_evidence_decision_id"
        record, error = self._read_json(
            self.evidence_decisions_path / f"{decision_id}.json"
        )
        if error or not isinstance(record, dict):
            return None, error or "evidence_decision_not_mapping"
        return record, None

    def _load_accepted_evidence(
        self,
        accepted_id: str | None,
    ) -> tuple[dict[str, Any] | None, str | None]:
        if self._term(accepted_id) == "Not Available":
            return None, "missing_accepted_evidence_id"
        record, error = self._read_json(
            self.accepted_evidence_path / f"{accepted_id}.json"
        )
        if error or not isinstance(record, dict):
            return None, error or "accepted_evidence_not_mapping"
        return record, None

    def _base_report(self, plan_id: str | None) -> dict[str, Any]:
        return {
            "system": "arena_evidence_admission_gate",
            "responsible_component": "ARENA_EVIDENCE_ADMISSION_GATE",
            "plan_id": self._term(plan_id),
            "evidence_accepted": False,
            "accepted_evidence_artifact_available": False,
            "arena_admission_invoked": False,
            "arena_admission_review_completed": False,
            "arena_admission_state": "NOT_EVALUATED",
            "arena_admission_reason": "not_evaluated",
            "arena_admission_record_created": False,
            "arena_evidence_ledger_entry_created": False,
            "arena_evidence_admitted": False,
            "arena_evidence_consumed": False,
            "redeliberation_invoked": False,
            "redeliberation_started": False,
            "redeliberation_completed": False,
            "baseline_snapshot_loaded": False,
            "redeliberation_snapshot_created": False,
            "candidate_evidence_profiles_rebuilt": False,
            "candidate_scores_recomputed": False,
            "candidate_score_changed": False,
            "candidate_ranking_recomputed": False,
            "candidate_ranking_changed": False,
            "cross_source_consensus_recomputed": False,
            "cross_source_consensus_changed": False,
            "provisional_leader_available": False,
            "decision_proposal_available": False,
            "formal_selection_invoked": False,
            "tie_resolved": False,
            "winner_selected": False,
            "selected_candidate": "NONE",
            "candidate_execution_authority": "NONE",
            "truth_authority": "NONE",
            "trust_authority": "NONE",
            "graduation_authority": "NONE",
            "constitutional_boundary": self.BOUNDARY,
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
            "arena_admission_evaluated": True,
            "arena_admission_state": state,
            "arena_admission_reason": reason,
            "blocked_stage": stage,
            "responsible_component": "ARENA_EVIDENCE_ADMISSION_GATE",
            "recoverability": "RECOVERABLE",
            "recommended_action": action,
            "evidence_accepted": True,
            "evidence_revoked": False,
            "arena_evidence_admitted": False,
            "arena_evidence_consumed": False,
            "redeliberation_invoked": False,
            "redeliberation_completed": False,
            "candidate_score_changed": False,
            "candidate_ranking_changed": False,
            "tie_resolved": False,
            "winner_selected": False,
            "selected_candidate": "NONE",
        }

    def _admission_block(
        self,
        state: str,
        reason: str,
        stage: str,
        action: str,
    ) -> dict[str, Any]:
        return {
            "arena_admission_evaluated": True,
            "arena_admission_state": state,
            "arena_admission_reason": reason,
            "blocked_stage": stage,
            "responsible_component": "ARENA_EVIDENCE_ADMISSION_GATE",
            "recoverability": "RECOVERABLE",
            "recommended_action": action,
            "evidence_accepted": True,
            "evidence_revoked": False,
            "arena_evidence_admitted": False,
            "arena_evidence_consumed": False,
            "redeliberation_invoked": False,
            "winner_selected": False,
        }

    def _public_projection(self, report: dict[str, Any]) -> dict[str, Any]:
        base = self._base_report(report.get("plan_id"))
        return {**base, **report} if report else base

    def _initialize(self) -> None:
        for path in (
            self.pending_path,
            self.evidence_decisions_path,
            self.accepted_evidence_path,
            self.admissions_path,
            self.ledger_path,
            self.redeliberations_path,
            self.outcomes_path,
            self.decision_proposals_path,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def _plan_files(self, directory: Path) -> list[Path]:
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
