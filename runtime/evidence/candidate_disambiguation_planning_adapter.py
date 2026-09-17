"""No-authority adapter from Arena disambiguation needs to validation planning."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from runtime.evidence.current_evidence_need import (
    CurrentEvidenceNeedAuthorityEngine,
    DeficitSignalType,
    EvidenceNeedType,
)
from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.evidence.validation_request import ValidationRequestAuthorityEngine
from runtime.evidence.validation_sponsorship import ValidationSponsorshipAuthorityEngine


class CandidateDisambiguationPlanningAdapter:
    """Transport candidate disambiguation needs into the governed evidence spine."""

    AUTHORITY = "NONE"
    CONTRACT_VERSION = "candidate_disambiguation_validation_intent.v1"
    SUPPORTED_METHODS = {"DISCRIMINATIVE_VALIDATION"}

    def __init__(
        self,
        root_path: str | os.PathLike[str] = "runtime/state/candidate_disambiguation_planning",
        *,
        need_authority: CurrentEvidenceNeedAuthorityEngine | None = None,
        sponsorship_authority: ValidationSponsorshipAuthorityEngine | None = None,
        request_authority: ValidationRequestAuthorityEngine | None = None,
        plan_store: EvidenceAcquisitionPlanStore | None = None,
    ) -> None:
        self.root_path = Path(root_path)
        self.need_authority = need_authority or CurrentEvidenceNeedAuthorityEngine(
            self.root_path / "current_evidence_needs"
        )
        self.sponsorship_authority = (
            sponsorship_authority
            or ValidationSponsorshipAuthorityEngine(
                self.root_path / "validation_sponsorships",
                need_authority=self.need_authority,
            )
        )
        self.request_authority = (
            request_authority
            or ValidationRequestAuthorityEngine(
                self.root_path / "validation_requests",
                sponsorship_authority=self.sponsorship_authority,
            )
        )
        self.plan_store = plan_store or EvidenceAcquisitionPlanStore(
            self.root_path / "evidence_acquisition_plans"
        )

    def admit_need_to_plan(
        self,
        disambiguation_need: Mapping[str, Any],
    ) -> dict[str, Any]:
        intent = self.validation_intent(disambiguation_need)
        if intent.get("intent_state") != "SUPPORTED":
            return self._blocked(intent, intent.get("intent_state", "INVALID_INTENT"))

        current_need_candidate = self.need_authority.propose_candidate(
            subject=self._current_need_subject(intent),
            need_type=EvidenceNeedType.CANDIDATE_DISAMBIGUATION_REQUIRED.value,
            deficit_signal_type=DeficitSignalType.CANDIDATE_DISAMBIGUATION_DEFICIT.value,
            source_deficit_refs=[
                {
                    "source_decision_id": intent["disambiguation_need_id"],
                    "source_authority": "CandidateDisambiguationEvidenceLayer",
                    "source_failure": "candidate_tie_requires_discriminating_evidence",
                    "disagreement_id": intent["disagreement_id"],
                    "candidate_pair_or_set_fingerprint": intent[
                        "candidate_pair_or_set_fingerprint"
                    ],
                }
            ],
            current_support_summary={
                "candidate_disambiguation_state": "UNRESOLVED",
                "outcome_blind_selection": True,
            },
            proposal_reason="candidate_tie_requires_discriminating_evidence",
            producer="CandidateDisambiguationEvidenceLayer",
            provenance={
                "source": "candidate_disambiguation_evidence_need",
                "source_deficit_current": True,
                "validation_intent": intent,
            },
        )
        current_need_decision = self.need_authority.decide_current_need(
            current_need_candidate
        )
        current_need_state = current_need_decision.get("current_state") or {}
        if not self.need_authority.is_evidence_need_current(
            current_need_state.get("evidence_need_id")
        ):
            return self._blocked(
                intent,
                "CURRENT_EVIDENCE_NEED_NOT_ACTIVE",
                current_need_decision=current_need_decision,
            )

        sponsorship_candidate = self.sponsorship_authority.candidate_from_current_need(
            current_need_state.get("evidence_need_id")
        )
        sponsorship_decision = self.sponsorship_authority.decide_sponsorship(
            sponsorship_candidate
        )
        sponsorship_state = sponsorship_decision.get("current_state") or {}
        if not self.sponsorship_authority.is_validation_sponsorship_current(
            sponsorship_state.get("validation_sponsorship_id")
        ):
            return self._blocked(
                intent,
                "VALIDATION_SPONSORSHIP_NOT_ACTIVE",
                current_need_decision=current_need_decision,
                sponsorship_decision=sponsorship_decision,
            )

        request_candidate = self.request_authority.candidate_from_current_sponsorship(
            sponsorship_state.get("validation_sponsorship_id")
        )
        request_candidate = self._attach_intent_to_request_candidate(
            request_candidate,
            intent,
        )
        request_decision = self.request_authority.decide_request(request_candidate)
        request_state = request_decision.get("current_state") or {}
        if not self.request_authority.is_validation_request_current(
            request_state.get("validation_request_id")
        ):
            return self._blocked(
                intent,
                "VALIDATION_REQUEST_NOT_PENDING",
                current_need_decision=current_need_decision,
                sponsorship_decision=sponsorship_decision,
                request_decision=request_decision,
            )

        plan_report = self.plan_store.admit_validation_request_to_plan(
            request_state.get("validation_request_id"),
            request_authority=self.request_authority,
        )
        reached = plan_report.get("evidence_plan_storage_state") in {
            "NEW_PLAN_PERSISTED",
            "EQUIVALENT_PENDING_PLAN_REUSED",
        }
        return {
            "system": "candidate_disambiguation_planning_adapter",
            "adapter_authority": self.AUTHORITY,
            "contract_version": self.CONTRACT_VERSION,
            "planning_status": (
                "D6_EVIDENCE_PLAN_REACHED" if reached else "D5_STOPPED_BEFORE_PLAN"
            ),
            "outcome_blind_selection": True,
            "duplicate_semantic_work_count": (
                0
                if plan_report.get("evidence_plan_storage_state")
                == "NEW_PLAN_PERSISTED"
                else 1
                if plan_report.get("evidence_plan_storage_state")
                == "EQUIVALENT_PENDING_PLAN_REUSED"
                else 0
            ),
            "validation_intent": intent,
            "current_need_decision": current_need_decision,
            "validation_sponsorship_decision": sponsorship_decision,
            "validation_request_decision": request_decision,
            "evidence_plan_report": plan_report,
            "disambiguation_need_reachable": True,
            "governed_sponsorship_reachable": (
                self.sponsorship_authority.is_validation_sponsorship_current(
                    sponsorship_state.get("validation_sponsorship_id")
                )
            ),
            "validation_request_reachable": (
                plan_report.get("request_consumed") is True
                or self.request_authority.is_validation_request_current(
                    request_state.get("validation_request_id")
                )
            ),
            "evidence_plan_reachable": reached,
            "safe_winner_forced": False,
            "tie_resolved": False,
            "execution_authority_changed": False,
            "evidence_acceptance_authority_changed": False,
            "causal_authority_changed": False,
            "source_independence_authority_changed": False,
            "qualification_authority_changed": False,
            "truth_authority_changed": False,
            "budget_authority_changed": False,
            "accepted_evidence_created": False,
            "raw_evidence_created": False,
        }

    def validation_intent(self, need: Mapping[str, Any]) -> dict[str, Any]:
        need = dict(need or {})
        failures = self._intent_failures(need)
        method = str(need.get("proposed_evidence_method") or "").strip()
        if method and method not in self.SUPPORTED_METHODS:
            failures.append("unsupported_disambiguation_method")
        expected = need.get("expected_candidate_predictions")
        if method == "DISCRIMINATIVE_VALIDATION" and not self._predictions_differ(expected):
            failures.append("missing_measurable_prediction_disagreement")
        candidate_ids = [str(item) for item in need.get("candidate_ids", []) or []]
        pair_fingerprint = self._fingerprint(
            {
                "candidate_set_id": need.get("candidate_set_id"),
                "candidate_ids": sorted(candidate_ids),
                "candidate_pair": need.get("candidate_pair") or candidate_ids[:2],
            }
        )
        disagreement_id = (
            str(need.get("disagreement_id"))
            if need.get("disagreement_id")
            else "candidate_disagreement_" + self._fingerprint(
                {
                    "candidate_set_id": need.get("candidate_set_id"),
                    "candidate_ids": sorted(candidate_ids),
                    "disagreement_type": need.get("disagreement_type"),
                    "missing_evidence": need.get("missing_discriminating_evidence"),
                }
            )[:16]
        )
        intent = {
            "contract_version": self.CONTRACT_VERSION,
            "intent_state": "SUPPORTED" if not failures else "INVALID",
            "intent_failures": sorted(set(failures)),
            "disambiguation_need_id": need.get("disambiguation_need_id"),
            "arena_decision_id": need.get("arena_decision_id")
            or f"arena_decision:{need.get('candidate_set_id', 'unknown')}",
            "arena_run_id": (need.get("task_binding") or {}).get("run_id"),
            "candidate_ids": candidate_ids,
            "candidate_source_lineages": need.get("candidate_source_lineages", {}),
            "candidate_pair_or_set_fingerprint": pair_fingerprint,
            "candidate_set_id": need.get("candidate_set_id"),
            "candidate_pair": need.get("candidate_pair") or candidate_ids[:2],
            "disagreement_id": disagreement_id,
            "disagreement_type": need.get("disagreement_type"),
            "evidence_requirement": need.get("missing_discriminating_evidence"),
            "requested_validation_method": method,
            "expected_discriminating_outcome": {
                "candidate_predictions_differ": self._predictions_differ(expected),
                "candidate_predictions": expected or {},
            },
            "non_discriminating_outcome_semantics": (
                "TIE_CONFIRMED_NON_DISCRIMINATING_EVIDENCE"
            ),
            "claim_or_hypothesis_refs": need.get("claim_or_hypothesis_refs", []),
            "context_refs": need.get("context_refs", []),
            "source_refs": need.get("source_refs", []),
            "lineage_metadata": {
                "created_at": need.get("created_at"),
                "task_binding": need.get("task_binding", {}),
                "authority_state": need.get("authority_state"),
            },
            "what_is_being_tested": (
                "measure a validation outcome that discriminates tied candidates"
            ),
            "candidate_winner_preference": "NONE",
            "future_outcome_fields_used_for_selection": [],
            "outcome_blind_selection": True,
            "adapter_authority": self.AUTHORITY,
        }
        if intent["intent_failures"]:
            intent["intent_state"] = (
                "UNSUPPORTED_METHOD"
                if "unsupported_disambiguation_method" in intent["intent_failures"]
                else "INVALID"
            )
        return intent

    def _current_need_subject(self, intent: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "target_type": "candidate_disambiguation",
            "capability_id": str(intent.get("disambiguation_need_id")),
            "qualification_subject_id": str(intent.get("candidate_set_id")),
            "claim_id": str(intent.get("disambiguation_need_id")),
            "claim_subject_ref": {
                "kind": "candidate_disambiguation_need",
                "candidate_set_id": intent.get("candidate_set_id"),
                "candidate_ids": list(intent.get("candidate_ids") or []),
                "disagreement_id": intent.get("disagreement_id"),
            },
            "domain": "candidate_disambiguation",
            "context_class": "arena_tie_review",
            "evidence_scope": "candidate_disambiguation_planning",
            "capability_subject": {
                "operation": "candidate_discriminative_probe",
                "validation_intent": dict(intent),
            },
        }

    def _attach_intent_to_request_candidate(
        self,
        candidate: Mapping[str, Any],
        intent: Mapping[str, Any],
    ) -> dict[str, Any]:
        candidate = json.loads(json.dumps(candidate, sort_keys=True, default=str))
        evidence_need = dict(candidate.get("evidence_need") or {})
        evidence_need.update(
            {
                "required_evidence_category": "CANDIDATE_DISAMBIGUATION",
                "required_evidence": "candidate_discriminative_probe_evidence",
                "required_validation_task": (
                    "candidate_discriminative_probe_validation_task"
                ),
                "tie_break_strategy": "candidate_discriminative_probe",
                "expected_tie_break_impact": "HIGH",
                "target_candidate": ",".join(intent.get("candidate_ids") or []),
                "target_operation": "candidate_discriminative_probe",
                "governed_reentry_action": (
                    "return_candidate_disambiguation_result_to_arena_reentry_gate_without_winner_authority"
                ),
                "canonical_source_identity": intent.get("disambiguation_need_id"),
                "source_lineage": [
                    intent.get("disambiguation_need_id"),
                    intent.get("candidate_set_id"),
                    intent.get("disagreement_id"),
                ],
                "candidate_disambiguation_validation_intent": dict(intent),
            }
        )
        candidate["evidence_need"] = evidence_need
        candidate["provenance"] = {
            **dict(candidate.get("provenance") or {}),
            "candidate_disambiguation_validation_intent": dict(intent),
        }
        candidate["candidate_fingerprint"] = self._fingerprint(
            self.request_authority._candidate_fingerprint_payload(candidate)
        )
        return candidate

    def _intent_failures(self, need: Mapping[str, Any]) -> list[str]:
        failures = []
        required = {
            "disambiguation_need_id": "missing_disambiguation_need_id",
            "candidate_set_id": "missing_candidate_set_id",
            "disagreement_type": "missing_disagreement_identity",
            "missing_discriminating_evidence": "missing_evidence_requirement",
            "proposed_evidence_method": "missing_requested_validation_method",
        }
        for field, failure in required.items():
            if not str(need.get(field) or "").strip():
                failures.append(failure)
        candidate_ids = need.get("candidate_ids")
        if not isinstance(candidate_ids, list) or len(candidate_ids) < 2:
            failures.append("missing_candidate_identity")
        binding = need.get("task_binding") if isinstance(need.get("task_binding"), Mapping) else {}
        if not str(binding.get("run_id") or "").strip():
            failures.append("missing_arena_run_lineage")
        return failures

    def _predictions_differ(self, predictions: Any) -> bool:
        if not isinstance(predictions, Mapping) or len(predictions) < 2:
            return False
        encoded = {
            json.dumps(value, sort_keys=True, default=str)
            for value in predictions.values()
        }
        return len(encoded) > 1

    def _blocked(self, intent: Mapping[str, Any], state: str, **extra: Any) -> dict[str, Any]:
        return {
            "system": "candidate_disambiguation_planning_adapter",
            "adapter_authority": self.AUTHORITY,
            "contract_version": self.CONTRACT_VERSION,
            "planning_status": state,
            "validation_intent": dict(intent),
            "disambiguation_need_reachable": bool(intent.get("disambiguation_need_id")),
            "governed_sponsorship_reachable": False,
            "validation_request_reachable": False,
            "evidence_plan_reachable": False,
            "outcome_blind_selection": True,
            "duplicate_semantic_work_count": 0,
            "safe_winner_forced": False,
            "tie_resolved": False,
            "execution_authority_changed": False,
            "evidence_acceptance_authority_changed": False,
            "causal_authority_changed": False,
            "source_independence_authority_changed": False,
            "qualification_authority_changed": False,
            "truth_authority_changed": False,
            "budget_authority_changed": False,
            "accepted_evidence_created": False,
            "raw_evidence_created": False,
            **extra,
        }

    def _fingerprint(self, payload: Mapping[str, Any]) -> str:
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()


__all__ = ["CandidateDisambiguationPlanningAdapter"]
