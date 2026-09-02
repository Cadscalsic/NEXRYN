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


class AcceptedEvidenceEpistemicAssessmentEngine:
    """Assess bound accepted evidence without granting truth authority."""

    system_name = "accepted_evidence_epistemic_assessment_engine"
    schema_version = "1.0"
    authority = "EPISTEMIC_ASSESSMENT_ONLY"

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
        state = (
            "TRUTH_CANDIDATE_REVIEW_READY"
            if sufficient_for_candidate
            else "CONTRADICTORY_EVIDENCE_PRESENT"
            if contradicting
            else "INSUFFICIENT_FOR_TRUTH_CANDIDACY"
            if supporting
            else "NO_BOUND_ACCEPTED_EVIDENCE"
        )
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
            "supporting_accepted_evidence_ids": [
                item.get("accepted_evidence_id") for item in supporting
            ],
            "contradicting_accepted_evidence_ids": [
                item.get("accepted_evidence_id") for item in contradicting
            ],
            "historical_unbound_evidence": historical_unbound,
            "rejected_evidence": rejected,
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
        return assessment

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


__all__ = ["AcceptedEvidenceEpistemicAssessmentEngine"]
