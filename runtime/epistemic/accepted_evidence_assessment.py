from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from runtime.claim_identity import (
    ClaimEvidenceBindingError,
    build_claim_evidence_binding,
)
from runtime.epistemic.evidence_source_independence import (
    EvidenceSourceIndependenceEngine,
)
from runtime.epistemic.truth_candidate_engine import TruthCandidateEngine
from runtime.validation.accepted_evidence_lifecycle import (
    AcceptedEvidenceLifecycleEngine,
    AcceptedEvidenceLifecycleStatus,
)


class AcceptedEvidenceEpistemicAssessmentEngine:
    """Assess bound accepted evidence without granting truth authority."""

    system_name = "accepted_evidence_epistemic_assessment_engine"
    schema_version = "1.0"
    authority = "EPISTEMIC_ASSESSMENT_ONLY"

    def __init__(
        self,
        evidence_lifecycle_engine: AcceptedEvidenceLifecycleEngine | None = None,
    ) -> None:
        self.evidence_lifecycle_engine = (
            evidence_lifecycle_engine or AcceptedEvidenceLifecycleEngine()
        )

    def promotion_contract(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "contract_owner": self.system_name,
            "minimum_bound_accepted_evidence_for_assessment": 1,
            "minimum_independent_sources_for_truth_candidate": (
                TruthCandidateEngine.MINIMUM_INDEPENDENT_SOURCES
            ),
            "truth_candidate_metric_requirements": list(TruthCandidateEngine.METRICS),
            "duplicate_independence_key": [
                "claim_id",
                "canonical_source_identity",
                "producer_component_id",
                "producer_source_type",
                "producer_operation_id",
                "source_lineage",
                "evidence_direction",
            ],
            "weak_identifier_independence_forbidden": True,
            "unknown_provenance_counts_as_independent": False,
            "accepted_evidence_is_not_truth": True,
            "assessment_is_not_truth_candidate": True,
            "truth_candidate_is_not_truth_commitment": True,
        }

    def assess(
        self,
        accepted_evidence: Iterable[Mapping[str, Any]],
        *,
        claim_id: str | None = None,
        assessment_run_id: str = "current_run",
    ) -> dict[str, Any]:
        items = [dict(item) for item in accepted_evidence if isinstance(item, Mapping)]
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        historical_unbound = []
        rejected = []
        excluded_noncurrent = []
        current_lifecycle_bindings = []
        for item in items:
            item_claim = item.get("claim_id")
            binding = item.get("claim_evidence_binding")
            if not binding or item.get("claim_evidence_binding_state") != "BOUND":
                historical_unbound.append({
                    "accepted_evidence_id": item.get("accepted_evidence_id"),
                    "classification": "HISTORICAL_PRE_E1_UNBOUND",
                    "claim_id": item_claim,
                })
                continue
            admission = self._admit_current_accepted_evidence(item)
            if not admission["admitted"]:
                excluded_noncurrent.append(admission)
                continue
            if claim_id and item_claim != claim_id:
                rejected.append({
                    "accepted_evidence_id": item.get("accepted_evidence_id"),
                    "rejection_reason": "wrong_claim",
                    "claim_id": item_claim,
                })
                continue
            try:
                rebuilt = build_claim_evidence_binding(
                    claim_subject=item.get("claim_subject"),
                    evidence_plan={
                        "plan_id": item.get("plan_id"),
                        "claim_id": item.get("claim_id"),
                        "claim_subject": item.get("claim_subject"),
                        "target_candidate": item.get("target_candidate"),
                        "target_operation": item.get("target_operation"),
                    },
                    evidence_decision={
                        "plan_id": item.get("plan_id"),
                        "evidence_decision_id": item.get("evidence_decision_id"),
                        "claim_id": item.get("claim_id"),
                        "claim_subject": item.get("claim_subject"),
                        "target_candidate": item.get("target_candidate"),
                        "target_operation": item.get("target_operation"),
                        "evidence_direction": item.get("evidence_direction"),
                        "evidence_acceptance_state": item.get(
                            "evidence_acceptance_state"
                        ),
                    },
                    accepted_evidence=item,
                )
            except (ClaimEvidenceBindingError, ValueError) as exc:
                rejected.append({
                    "accepted_evidence_id": item.get("accepted_evidence_id"),
                    "rejection_reason": "claim_binding_invalid",
                    "error": str(exc),
                    "claim_id": item_claim,
                })
                continue
            if rebuilt.get("claim_evidence_binding_id") != item.get(
                "claim_evidence_binding_id"
            ):
                rejected.append({
                    "accepted_evidence_id": item.get("accepted_evidence_id"),
                    "rejection_reason": "claim_binding_id_mismatch",
                    "claim_id": item_claim,
                })
                continue
            current_lifecycle_bindings.append(admission["current_lifecycle_binding"])
            grouped[item_claim].append(item)

        effective_claim_id = claim_id or next(iter(grouped), "NOT_AVAILABLE")
        supporting = [
            item for item in grouped.get(effective_claim_id, [])
            if item.get("evidence_direction") == "SUPPORTING"
        ]
        contradicting = [
            item for item in grouped.get(effective_claim_id, [])
            if item.get("evidence_direction") == "CONTRADICTING"
        ]
        support_lineage = [
            self._accepted_evidence_lineage(item)
            for item in supporting + contradicting
        ]
        source_engine = EvidenceSourceIndependenceEngine()
        source_coverage = source_engine.source_coverage(
            supporting,
            claim_id=effective_claim_id,
            required_independent_sources=(
                TruthCandidateEngine.MINIMUM_INDEPENDENT_SOURCES
            ),
        )
        independent_count = source_coverage[
            "current_proven_independent_source_count"
        ]
        duplicate_count = source_coverage["duplicate_supporting_evidence_count"]
        contract = self.promotion_contract()
        sufficient_for_candidate = (
            independent_count
            >= contract["minimum_independent_sources_for_truth_candidate"]
            and not contradicting
        )
        if sufficient_for_candidate:
            state = "TRUTH_CANDIDATE_REVIEW_READY"
        elif contradicting:
            state = "CONTRADICTORY_EVIDENCE_PRESENT"
        elif supporting:
            state = "INSUFFICIENT_FOR_TRUTH_CANDIDACY"
        elif excluded_noncurrent:
            state = "NO_CURRENT_ADMISSIBLE_EVIDENCE"
        else:
            state = "NO_BOUND_ACCEPTED_EVIDENCE"
        assessment = {
            "schema_version": self.schema_version,
            "system": self.system_name,
            "epistemic_assessment_id": self._assessment_id(
                effective_claim_id,
                assessment_run_id,
                [item.get("accepted_evidence_id") for item in supporting],
            ),
            "assessment_run_id": assessment_run_id,
            "claim_id": effective_claim_id,
            "accepted_evidence_ids": [
                item.get("accepted_evidence_id") for item in supporting + contradicting
            ],
            "current_accepted_evidence_ids": [
                item.get("accepted_evidence_id") for item in supporting + contradicting
            ],
            "accepted_evidence_lineage": support_lineage,
            "supporting_evidence_lineage": [
                self._accepted_evidence_lineage(item) for item in supporting
            ],
            "contradicting_evidence_lineage": [
                self._accepted_evidence_lineage(item) for item in contradicting
            ],
            "raw_evidence_ids": sorted({
                str(item.get("raw_evidence_id") or item.get("raw_result_id"))
                for item in support_lineage
                if item.get("raw_evidence_id") or item.get("raw_result_id")
            }),
            "origin_task_execution_ids": sorted({
                str(item.get("origin_task_execution_id"))
                for item in support_lineage
                if item.get("origin_task_execution_id") not in {None, ""}
            }),
            "origin_task_ids": sorted({
                str(item.get("origin_task_id"))
                for item in support_lineage
                if item.get("origin_task_id") not in {None, ""}
            }),
            "epistemic_lineage_state": (
                "EPISTEMIC_LINEAGE_COMPLETE"
                if support_lineage and all(
                    item.get("accepted_evidence_origin_state")
                    == "TASK_ORIGIN_PRESERVED"
                    for item in support_lineage
                )
                else "EPISTEMIC_LINEAGE_NOT_APPLICABLE"
                if not support_lineage
                else "EPISTEMIC_LINEAGE_PARTIAL"
            ),
            "task_provenance_authority": "NONE",
            "supporting_accepted_evidence_ids": [
                item.get("accepted_evidence_id") for item in supporting
            ],
            "contradicting_accepted_evidence_ids": [
                item.get("accepted_evidence_id") for item in contradicting
            ],
            "historical_unbound_evidence": historical_unbound,
            "rejected_evidence": rejected,
            "excluded_noncurrent_evidence": excluded_noncurrent,
            "excluded_evidence_ids": [
                item.get("accepted_evidence_id") for item in excluded_noncurrent
            ],
            "input_evidence_count": len(items),
            "admitted_current_evidence_count": len(
                grouped.get(effective_claim_id, [])
            ),
            "excluded_noncurrent_evidence_count": len(excluded_noncurrent),
            "current_lifecycle_bindings": current_lifecycle_bindings,
            "admission_integrity_state": (
                "CURRENT_EPISTEMIC_EVIDENCE_AUTHORITY_VERIFIED"
                if grouped.get(effective_claim_id)
                else "NO_CURRENT_ADMISSIBLE_EVIDENCE"
                if excluded_noncurrent
                else "NO_BOUND_ACCEPTED_EVIDENCE"
            ),
            "bound_accepted_evidence_count": len(grouped.get(effective_claim_id, [])),
            "supporting_evidence_count": len(supporting),
            "contradicting_evidence_count": len(contradicting),
            "independent_supporting_source_count": independent_count,
            "source_coverage": source_coverage,
            "duplicate_supporting_evidence_count": duplicate_count,
            "evidence_diversity_state": (
                "DUPLICATES_DEDUPED"
                if duplicate_count
                else "UNKNOWN_SOURCE_PROVENANCE_FAIL_CLOSED"
                if source_coverage.get("unknown_dependence_artifacts")
                else "NO_DUPLICATE_INFLATION_OBSERVED"
            ),
            "epistemic_assessment_state": state,
            "truth_candidate_creation_state": "NOT_REACHED_BY_E2_R1_BOUNDARY",
            "truth_candidate_id": "NOT_REACHED",
            "truth_decision_id": "NOT_REACHED",
            "truth_id": "NOT_REACHED",
            "knowledge_object_id": "NOT_REACHED",
            "promotion_contract": contract,
            "highest_epistemic_level": "E4",
            "authority": {
                "assessment": self.authority,
                "truth_candidate": "NONE",
                "truth_commitment": "NONE",
                "knowledge_projection": "NONE",
                "execution": "NONE",
                "trust": "NONE",
                "graduation": "NONE",
                "budget": "NONE",
            },
            "accepted_evidence_is_not_truth": True,
            "assessment_is_not_truth_candidate": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        assessment["assessment_fingerprint"] = self._assessment_fingerprint(
            assessment
        )
        return assessment

    def is_epistemic_assessment_current(
        self,
        assessment: Mapping[str, Any],
    ) -> dict[str, Any]:
        report = dict(assessment or {})
        stale_bindings = []
        verified_bindings = []
        integrity_failures = []
        assessment_evidence_ids = {
            str(item)
            for item in (
                report.get("current_accepted_evidence_ids")
                or report.get("accepted_evidence_ids")
                or []
            )
            if item not in {None, ""}
        }
        if not report.get("epistemic_assessment_id"):
            integrity_failures.append("assessment_id_missing")
        if not self._assessment_fingerprint_valid(report):
            integrity_failures.append("assessment_fingerprint_invalid")
        if not report.get("current_lifecycle_bindings"):
            integrity_failures.append("current_lifecycle_bindings_missing")
        for binding in report.get("current_lifecycle_bindings") or []:
            if not isinstance(binding, Mapping):
                stale_bindings.append({
                    "accepted_evidence_id": None,
                    "stale_reason": "lifecycle_binding_missing",
                })
                continue
            evidence_id = binding.get("accepted_evidence_id")
            if str(evidence_id) not in assessment_evidence_ids:
                stale_bindings.append({
                    "accepted_evidence_id": evidence_id,
                    "stale_reason": "assessment_evidence_identity_mismatch",
                    "stale_reasons": ["assessment_evidence_identity_mismatch"],
                })
                continue
            current_state = self._resolve_current_state(
                {"accepted_evidence_id": evidence_id}
            )
            if not current_state:
                stale_bindings.append({
                    "accepted_evidence_id": evidence_id,
                    "stale_reason": "current_evidence_state_unresolved",
                })
                continue
            failures = self._current_state_failures(
                {"accepted_evidence_id": evidence_id},
                current_state,
            )
            if (
                binding.get("current_lifecycle_decision_id")
                != current_state.get("current_lifecycle_decision_id")
            ):
                failures.append("lifecycle_decision_changed")
            if binding.get("current_status") != current_state.get("current_status"):
                failures.append("current_status_changed")
            if (
                binding.get("current_state_fingerprint")
                != current_state.get("fingerprint")
            ):
                failures.append("current_state_fingerprint_changed")
            if failures:
                stale_bindings.append({
                    "accepted_evidence_id": evidence_id,
                    "stale_reason": sorted(set(failures))[0],
                    "stale_reasons": sorted(set(failures)),
                })
            else:
                verified_bindings.append(dict(binding))

        current = (
            not integrity_failures
            and not stale_bindings
            and bool(verified_bindings)
        )
        return {
            "schema_version": self.schema_version,
            "system": "epistemic_assessment_current_state_validator",
            "epistemic_assessment_id": report.get("epistemic_assessment_id"),
            "assessment_current_state": (
                "CURRENT_EPISTEMIC_ASSESSMENT"
                if current
                else "STALE_EPISTEMIC_ASSESSMENT"
            ),
            "current_support_available": current,
            "integrity_failures": integrity_failures,
            "verified_lifecycle_bindings": verified_bindings,
            "stale_lifecycle_bindings": stale_bindings,
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "runtime_authority": "NONE",
            "budget_authority": "NONE",
            "execution_authority": "NONE",
        }

    def _accepted_evidence_lineage(
        self,
        accepted_evidence: Mapping[str, Any],
    ) -> dict[str, Any]:
        item = dict(accepted_evidence or {})
        origin = item.get("accepted_evidence_origin")
        origin = dict(origin) if isinstance(origin, Mapping) else {}
        provenance = item.get("source_provenance")
        provenance = dict(provenance) if isinstance(provenance, Mapping) else {}
        return {
            "accepted_evidence_id": item.get("accepted_evidence_id"),
            "evidence_decision_id": item.get("evidence_decision_id"),
            "raw_evidence_id": (
                origin.get("raw_evidence_id")
                or item.get("raw_evidence_id")
                or item.get("raw_result_id")
                or provenance.get("raw_validation_result_id")
            ),
            "raw_result_id": (
                origin.get("raw_result_id")
                or item.get("raw_result_id")
                or provenance.get("raw_validation_result_id")
            ),
            "origin_task_execution_id": (
                origin.get("origin_task_execution_id")
                or item.get("origin_task_execution_id")
                or provenance.get("origin_task_execution_id")
            ),
            "origin_run_id": (
                origin.get("origin_run_id")
                or item.get("origin_run_id")
                or provenance.get("origin_run_id")
            ),
            "origin_task_id": (
                origin.get("origin_task_id")
                or item.get("origin_task_id")
                or provenance.get("origin_task_id")
            ),
            "origin_attempt_id": (
                origin.get("origin_attempt_id")
                or item.get("origin_attempt_id")
                or provenance.get("origin_attempt_id")
            ),
            "origin_operation_id": (
                origin.get("origin_operation_id")
                or item.get("origin_operation_id")
                or provenance.get("origin_operation_id")
            ),
            "origin_lineage_fingerprint": (
                origin.get("origin_lineage_fingerprint")
                or item.get("origin_lineage_fingerprint")
                or provenance.get("origin_lineage_fingerprint")
            ),
            "accepted_evidence_origin_state": (
                origin.get("accepted_evidence_origin_state")
                or item.get("accepted_evidence_origin_state")
                or "LEGACY_ORIGIN_UNVERIFIED"
            ),
            "source_provenance_fingerprint": (
                origin.get("source_provenance_fingerprint")
                or item.get("source_provenance_fingerprint")
                or provenance.get("source_provenance_fingerprint")
            ),
            "task_provenance_authority": "NONE",
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
        }

    def _admit_current_accepted_evidence(
        self,
        accepted_evidence: Mapping[str, Any],
    ) -> dict[str, Any]:
        item = dict(accepted_evidence or {})
        evidence_id = item.get("accepted_evidence_id")
        base = {
            "accepted_evidence_id": evidence_id,
            "admission_state": "DENY_CURRENT_SUPPORT",
            "rejection_reason": "DENIED_CURRENT_LIFECYCLE_UNVERIFIED",
        }
        if not evidence_id:
            return {
                **base,
                "rejection_reason": "DENIED_EVIDENCE_IDENTITY_MISMATCH",
                "admitted": False,
            }
        current_state = self._resolve_current_state(item)
        if not current_state:
            return {
                **base,
                "rejection_reason": "DENIED_STALE_ACCEPTANCE_STATE",
                "admitted": False,
            }
        failures = self._current_state_failures(item, current_state)
        if failures:
            return {
                **base,
                "rejection_reason": self._primary_rejection_reason(failures),
                "rejection_reasons": failures,
                "current_status": current_state.get("current_status"),
                "current_lifecycle_decision_id": current_state.get(
                    "current_lifecycle_decision_id"
                ),
                "admitted": False,
            }
        binding = {
            "accepted_evidence_id": evidence_id,
            "current_lifecycle_decision_id": current_state.get(
                "current_lifecycle_decision_id"
            ),
            "current_acceptance_decision_id": current_state.get(
                "current_acceptance_decision_id"
            ),
            "current_status": current_state.get("current_status"),
            "is_currently_accepted": current_state.get("is_currently_accepted"),
            "current_state_fingerprint": current_state.get("fingerprint"),
        }
        return {
            "accepted_evidence_id": evidence_id,
            "admission_state": "CURRENT_EPISTEMIC_EVIDENCE_ADMITTED",
            "admitted": True,
            "current_lifecycle_binding": binding,
        }

    def _resolve_current_state(
        self,
        accepted_evidence: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        embedded = accepted_evidence.get("accepted_evidence_current_state")
        if isinstance(embedded, Mapping):
            return dict(embedded)
        evidence_id = accepted_evidence.get("accepted_evidence_id")
        if evidence_id:
            current = self.evidence_lifecycle_engine.get_current_evidence_state(
                str(evidence_id)
            )
            if current is not None:
                return dict(current)
        return None

    def _current_state_failures(
        self,
        accepted_evidence: Mapping[str, Any],
        current_state: Mapping[str, Any],
    ) -> list[str]:
        failures: list[str] = []
        evidence_id = accepted_evidence.get("accepted_evidence_id")
        state_evidence_id = (
            current_state.get("accepted_evidence_id") or current_state.get("evidence_id")
        )
        if state_evidence_id != evidence_id:
            failures.append("DENIED_EVIDENCE_IDENTITY_MISMATCH")
        if current_state.get("authority") != self.evidence_lifecycle_engine.authority:
            failures.append("DENIED_CURRENT_LIFECYCLE_UNVERIFIED")
        if current_state.get("current_lifecycle_decision_id") in {
            None,
            "",
            "UNKNOWN",
            "NOT_AVAILABLE",
            "Not Available",
        }:
            failures.append("DENIED_CURRENT_LIFECYCLE_UNVERIFIED")
        if current_state.get("current_acceptance_decision_id") in {
            None,
            "",
            "UNKNOWN",
            "NOT_AVAILABLE",
            "Not Available",
        }:
            failures.append("DENIED_CURRENT_LIFECYCLE_UNVERIFIED")
        if not self.evidence_lifecycle_engine._fingerprint_valid(current_state):
            failures.append("DENIED_CURRENT_LIFECYCLE_UNVERIFIED")
        status = current_state.get("current_status")
        if status == AcceptedEvidenceLifecycleStatus.UNDER_REVIEW.value:
            failures.append("DENIED_EVIDENCE_UNDER_REVIEW")
        elif status == AcceptedEvidenceLifecycleStatus.REVOKED.value:
            failures.append("DENIED_EVIDENCE_REVOKED")
        elif status == AcceptedEvidenceLifecycleStatus.INVALIDATED.value:
            failures.append("DENIED_EVIDENCE_INVALIDATED")
        elif status == AcceptedEvidenceLifecycleStatus.SUPERSEDED.value:
            failures.append("DENIED_EVIDENCE_SUPERSEDED")
        elif status == AcceptedEvidenceLifecycleStatus.REVALIDATION_REQUIRED.value:
            failures.append("DENIED_REVALIDATION_REQUIRED")
        elif status != AcceptedEvidenceLifecycleStatus.ACTIVE.value:
            failures.append("DENIED_EVIDENCE_NOT_CURRENT")
        if current_state.get("is_currently_accepted") is not True:
            failures.append("DENIED_EVIDENCE_NOT_CURRENT")
        if current_state.get("superseded_by"):
            failures.append("DENIED_EVIDENCE_SUPERSEDED")
        provenance = accepted_evidence.get("source_provenance")
        if isinstance(provenance, Mapping) and (
            provenance.get("source_provenance_state") != "SOURCE_PROVENANCE_BOUND"
        ):
            failures.append("DENIED_PROVENANCE_INVALID")
        return sorted(set(failures))

    def _primary_rejection_reason(self, failures: Iterable[str]) -> str:
        priority = [
            "DENIED_EVIDENCE_IDENTITY_MISMATCH",
            "DENIED_CURRENT_LIFECYCLE_UNVERIFIED",
            "DENIED_EVIDENCE_UNDER_REVIEW",
            "DENIED_EVIDENCE_REVOKED",
            "DENIED_EVIDENCE_INVALIDATED",
            "DENIED_EVIDENCE_SUPERSEDED",
            "DENIED_REVALIDATION_REQUIRED",
            "DENIED_PROVENANCE_INVALID",
            "DENIED_EVIDENCE_NOT_CURRENT",
        ]
        observed = set(failures)
        for reason in priority:
            if reason in observed:
                return reason
        return next(iter(observed), "DENIED_CURRENT_LIFECYCLE_UNVERIFIED")

    def _assessment_id(
        self,
        claim_id: str,
        assessment_run_id: str,
        accepted_evidence_ids: Iterable[Any],
    ) -> str:
        payload = {
            "claim_id": claim_id,
            "assessment_run_id": assessment_run_id,
            "accepted_evidence_ids": sorted(str(item) for item in accepted_evidence_ids),
            "schema_version": self.schema_version,
        }
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return (
            "epistemic_assessment_"
            f"{hashlib.sha1(encoded.encode('utf-8')).hexdigest()[:12]}"
        )

    def _assessment_fingerprint(self, assessment: Mapping[str, Any]) -> str:
        payload = {
            key: value
            for key, value in dict(assessment).items()
            if key != "assessment_fingerprint"
        }
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _assessment_fingerprint_valid(self, assessment: Mapping[str, Any]) -> bool:
        fingerprint = assessment.get("assessment_fingerprint")
        return bool(fingerprint and fingerprint == self._assessment_fingerprint(assessment))


__all__ = ["AcceptedEvidenceEpistemicAssessmentEngine"]
