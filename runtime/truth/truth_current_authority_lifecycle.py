"""Govern current Truth authority separately from historical Truth records."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from runtime.epistemic.accepted_evidence_assessment import (
        AcceptedEvidenceEpistemicAssessmentEngine,
    )


UNKNOWN = {None, "", "UNKNOWN", "NOT_AVAILABLE", "Not Available"}


class TruthLifecycleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    INVALIDATED = "INVALIDATED"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    SUPERSEDED = "SUPERSEDED"


REVIEW_TRIGGERS = {
    "SUPPORTING_EVIDENCE_REVOKED",
    "SUPPORTING_EVIDENCE_INVALIDATED",
    "SUPPORTING_EVIDENCE_SUPERSEDED",
    "SUPPORTING_EPISTEMIC_ASSESSMENT_STALE",
    "SOURCE_INDEPENDENCE_COLLAPSED",
    "CAUSAL_SUPPORT_WITHDRAWN",
    "CONTRADICTORY_CURRENT_SUPPORT",
    "TRUTH_DECISION_INTEGRITY_FAILURE",
    "TRUTH_PROVENANCE_INVALID",
    "GOVERNANCE_REVIEW_REQUIRED",
}


class TruthCurrentAuthorityLifecycleEngine:
    """Own the current lifecycle state of Truth and TruthCandidate artifacts."""

    schema_version = "1.0"
    system_name = "truth_current_authority_lifecycle_engine"
    authority = "TRUTH_CURRENT_AUTHORITY"

    def __init__(
        self,
        state_dir: str | Path | None = None,
        *,
        epistemic_assessment_engine: (
            "AcceptedEvidenceEpistemicAssessmentEngine | None"
        ) = None,
    ) -> None:
        self.state_dir = Path(state_dir) if state_dir is not None else None
        self.epistemic_assessment_engine = epistemic_assessment_engine

    def create_active_truth(
        self,
        *,
        truth_id: str,
        claim_id: str,
        truth_candidate_id: str | None = None,
        support: Mapping[str, Any] | None = None,
        semantic_state: str = "COMMITTED_TRUTH",
        confidence: float | int = 1.0,
    ) -> dict[str, Any]:
        if truth_id in UNKNOWN:
            raise ValueError("truth_id_required")
        if claim_id in UNKNOWN:
            raise ValueError("claim_id_required")
        decision = self._decision(
            kind="activation",
            truth_id=truth_id,
            claim_id=claim_id,
            truth_candidate_id=truth_candidate_id,
            previous_decision_id=None,
            previous_status=None,
            new_status=TruthLifecycleStatus.ACTIVE.value,
            reason="initial_truth_current_authority",
            support=support,
            semantic_state=semantic_state,
            confidence=confidence,
        )
        return self.current_state_from_decision({}, decision)

    def open_review(
        self,
        current_state: Mapping[str, Any],
        *,
        review_trigger: str,
        support_signal: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        self._assert_current_state(state)
        if review_trigger not in REVIEW_TRIGGERS:
            raise ValueError("unsupported_truth_review_trigger")
        decision = self._decision(
            kind="review",
            truth_id=state["truth_id"],
            claim_id=state["claim_id"],
            truth_candidate_id=state.get("truth_candidate_id"),
            previous_decision_id=state["current_truth_decision_id"],
            previous_status=state["lifecycle_status"],
            new_status=TruthLifecycleStatus.UNDER_REVIEW.value,
            reason=review_trigger,
            support=state.get("support_dependency_graph", {}),
            support_signal=support_signal,
            extra={"review_trigger": review_trigger},
        )
        return decision

    def reassess_under_review(
        self,
        current_state: Mapping[str, Any],
        *,
        current_support: Mapping[str, Any] | None = None,
        decision_result: str | None = None,
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        self._assert_current_state(state)
        if state["lifecycle_status"] != TruthLifecycleStatus.UNDER_REVIEW.value:
            raise ValueError("truth_under_review_required")
        support_report = self._support_report(current_support)
        if decision_result is None:
            decision_result = (
                "RESTORED_SAME_STATE"
                if support_report["truth_policy_satisfied"]
                else "INVALIDATED"
            )
        status = (
            TruthLifecycleStatus.ACTIVE.value
            if decision_result in {
                "RESTORED_SAME_STATE",
                "REQUALIFIED_LOWER_CONFIDENCE_OR_LEVEL",
            }
            else TruthLifecycleStatus.INVALIDATED.value
            if decision_result == "INVALIDATED"
            else TruthLifecycleStatus.REVALIDATION_REQUIRED.value
            if decision_result == "REVALIDATION_REQUIRED"
            else TruthLifecycleStatus.SUPERSEDED.value
            if decision_result == "SUPERSEDED"
            else None
        )
        if status is None:
            raise ValueError("unsupported_truth_reassessment_result")
        decision = self._decision(
            kind="reassessment",
            truth_id=state["truth_id"],
            claim_id=state["claim_id"],
            truth_candidate_id=state.get("truth_candidate_id"),
            previous_decision_id=state["current_truth_decision_id"],
            previous_status=state["lifecycle_status"],
            new_status=status,
            reason=decision_result,
            support=current_support,
            extra={
                "reassessment_result": decision_result,
                "support_reassessment": support_report,
            },
        )
        return decision

    def invalidate_truth(
        self,
        current_state: Mapping[str, Any],
        *,
        reason: str,
        current_support: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        self._assert_current_state(state)
        if state["lifecycle_status"] != TruthLifecycleStatus.UNDER_REVIEW.value:
            raise ValueError("truth_review_required_before_invalidation")
        return self._decision(
            kind="invalidation",
            truth_id=state["truth_id"],
            claim_id=state["claim_id"],
            truth_candidate_id=state.get("truth_candidate_id"),
            previous_decision_id=state["current_truth_decision_id"],
            previous_status=state["lifecycle_status"],
            new_status=TruthLifecycleStatus.INVALIDATED.value,
            reason=reason,
            support=current_support,
        )

    def revalidate_truth(
        self,
        current_state: Mapping[str, Any],
        *,
        current_support: Mapping[str, Any],
        reason: str = "fresh_current_support_verified",
    ) -> dict[str, Any]:
        state = dict(current_state or {})
        self._assert_current_state(state)
        if state["lifecycle_status"] not in {
            TruthLifecycleStatus.INVALIDATED.value,
            TruthLifecycleStatus.UNDER_REVIEW.value,
            TruthLifecycleStatus.REVALIDATION_REQUIRED.value,
        }:
            raise ValueError("revalidation_requires_non_active_truth_state")
        support_report = self._support_report(current_support)
        if not support_report["truth_policy_satisfied"]:
            raise ValueError("fresh_current_truth_support_required")
        decision = self._decision(
            kind="revalidation",
            truth_id=state["truth_id"],
            claim_id=state["claim_id"],
            truth_candidate_id=state.get("truth_candidate_id"),
            previous_decision_id=state["current_truth_decision_id"],
            previous_status=state["lifecycle_status"],
            new_status=TruthLifecycleStatus.ACTIVE.value,
            reason=reason,
            support=current_support,
            extra={"support_reassessment": support_report},
        )
        return decision

    def supersede_truth(
        self,
        current_state: Mapping[str, Any],
        *,
        replacement_truth_id: str,
        replacement_claim_id: str,
        reason: str,
        replacement_support: Mapping[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        state = dict(current_state or {})
        self._assert_current_state(state)
        if replacement_truth_id in UNKNOWN:
            raise ValueError("replacement_truth_id_required")
        decision = self._decision(
            kind="supersession",
            truth_id=state["truth_id"],
            claim_id=state["claim_id"],
            truth_candidate_id=state.get("truth_candidate_id"),
            previous_decision_id=state["current_truth_decision_id"],
            previous_status=state["lifecycle_status"],
            new_status=TruthLifecycleStatus.SUPERSEDED.value,
            reason=reason,
            support=state.get("support_dependency_graph", {}),
        )
        decision["replacement_truth_id"] = replacement_truth_id
        decision["supersession_relation"] = "EXPLICIT_GOVERNED_REPLACEMENT"
        decision["decision_fingerprint"] = self._fingerprint(decision)
        replacement = self.create_active_truth(
            truth_id=replacement_truth_id,
            claim_id=replacement_claim_id,
            support=replacement_support,
            semantic_state=state.get("truth_semantic_state", "COMMITTED_TRUTH"),
            confidence=state.get("truth_confidence", 1.0),
        )
        replacement["supersedes_truth_id"] = state["truth_id"]
        replacement["fingerprint"] = self._fingerprint(replacement)
        return decision, replacement

    def current_state_from_decision(
        self,
        current_state: Mapping[str, Any],
        decision: Mapping[str, Any],
    ) -> dict[str, Any]:
        previous = dict(current_state or {})
        item = dict(decision or {})
        self._assert_decision(item)
        if previous:
            if item.get("truth_id") != previous.get("truth_id"):
                raise ValueError("cross_truth_decision_rejected")
            if item.get("claim_id") != previous.get("claim_id"):
                raise ValueError("cross_claim_decision_rejected")
            if item.get("previous_truth_decision_id") != previous.get(
                "current_truth_decision_id"
            ):
                raise ValueError("out_of_order_truth_decision_rejected")
        state = {
            "schema_version": self.schema_version,
            "system": "current_truth_state",
            "truth_id": item["truth_id"],
            "truth_candidate_id": item.get("truth_candidate_id"),
            "claim_id": item["claim_id"],
            "truth_semantic_state": item.get("truth_semantic_state", "COMMITTED_TRUTH"),
            "truth_confidence": item.get("truth_confidence", 1.0),
            "lifecycle_status": item["new_status"],
            "current_authority_status": (
                "CURRENT_TRUTH_AUTHORITY_VERIFIED"
                if item["new_status"] == TruthLifecycleStatus.ACTIVE.value
                else "NO_CURRENT_ACTIVE_TRUTH_AUTHORITY"
            ),
            "current_truth_decision_id": self._decision_id(item),
            "previous_truth_decision_id": item.get("previous_truth_decision_id"),
            "support_dependency_graph": dict(item.get("support_dependency_graph") or {}),
            "truth_under_review": item["new_status"]
            == TruthLifecycleStatus.UNDER_REVIEW.value,
            "truth_invalidated": item["new_status"]
            == TruthLifecycleStatus.INVALIDATED.value,
            "truth_superseded": item["new_status"]
            == TruthLifecycleStatus.SUPERSEDED.value,
            "authority": self.authority,
            "truth_authority": self.authority,
            "knowledge_authority": "NONE",
            "capability_authority": "NONE",
            "runtime_authority": "NONE",
            "budget_authority": "NONE",
            "execution_authority": "NONE",
            "updated_at": item.get("created_at"),
        }
        state["fingerprint"] = self._fingerprint(state)
        return state

    def support_change_review_signal(
        self,
        current_state: Mapping[str, Any],
        *,
        trigger: str,
        upstream_report: Mapping[str, Any],
    ) -> dict[str, Any]:
        decision = self.open_review(
            current_state,
            review_trigger=trigger,
            support_signal=upstream_report,
        )
        return {
            "schema_version": self.schema_version,
            "system": "truth_support_change_review_signal",
            "signal_state": "TRUTH_REVIEW_DECISION_AVAILABLE",
            "truth_review_decision": decision,
            "direct_truth_mutation": False,
            "evidence_layer_truth_authority": "NONE",
            "epistemic_layer_truth_authority": "NONE",
        }

    def is_truth_current(self, truth_id: str) -> bool:
        current = self.get_current_truth_state(truth_id)
        return bool(
            current
            and current.get("lifecycle_status") == TruthLifecycleStatus.ACTIVE.value
            and current.get("current_authority_status")
            == "CURRENT_TRUTH_AUTHORITY_VERIFIED"
        )

    def persist_current_state(
        self,
        current_state: Mapping[str, Any],
        *,
        lifecycle_decision: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.state_dir is None:
            raise ValueError("state_dir_required_for_persistence")
        state = dict(current_state or {})
        self._assert_current_state(state)
        root = self.state_dir
        current_dir = root / "current_truth_state"
        history_dir = root / "truth_history"
        decision_dir = root / "truth_decisions"
        pointer_dir = root / "current_truth_decision_pointer"
        current_dir.mkdir(parents=True, exist_ok=True)
        history_dir.mkdir(parents=True, exist_ok=True)
        decision_dir.mkdir(parents=True, exist_ok=True)
        pointer_dir.mkdir(parents=True, exist_ok=True)
        truth_id = state["truth_id"]
        current_path = current_dir / f"{truth_id}.json"
        pointer_path = pointer_dir / f"{truth_id}.json"
        current_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        pointer = {
            "truth_id": truth_id,
            "current_truth_decision_id": state["current_truth_decision_id"],
            "current_state_fingerprint": state["fingerprint"],
            "authority": self.authority,
        }
        pointer["fingerprint"] = self._fingerprint(pointer)
        pointer_path.write_text(
            json.dumps(pointer, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        decision = dict(lifecycle_decision or {})
        if decision:
            self._assert_decision(decision)
            decision_path = decision_dir / f"{self._decision_id(decision)}.json"
            decision_path.write_text(
                json.dumps(decision, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        history_path = history_dir / f"{truth_id}.json"
        history = []
        if history_path.exists():
            loaded = json.loads(history_path.read_text(encoding="utf-8"))
            history = loaded if isinstance(loaded, list) else []
        history.append({
            "current_state": state,
            "lifecycle_decision": decision,
        })
        history_path.write_text(json.dumps(history, indent=2, sort_keys=True), encoding="utf-8")
        return {
            "persistence_state": "PERSISTED_BY_TRUTH_CURRENT_AUTHORITY",
            "current_state_path": str(current_path),
            "current_decision_pointer_path": str(pointer_path),
            "history_path": str(history_path),
            "persistence_implies_truth": False,
            "persistence_implies_truth_invalidation": False,
        }

    def get_current_truth_state(self, truth_id: str) -> dict[str, Any] | None:
        if self.state_dir is None:
            return None
        path = self.state_dir / "current_truth_state" / f"{truth_id}.json"
        if not path.exists():
            return None
        state = json.loads(path.read_text(encoding="utf-8"))
        pointer_path = (
            self.state_dir
            / "current_truth_decision_pointer"
            / f"{truth_id}.json"
        )
        if not pointer_path.exists():
            return None
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        if pointer.get("authority") != self.authority:
            return None
        if not self._fingerprint_valid(pointer):
            return None
        if pointer.get("current_truth_decision_id") != state.get(
            "current_truth_decision_id"
        ):
            return None
        if pointer.get("current_state_fingerprint") != state.get("fingerprint"):
            return None
        if state.get("authority") != self.authority:
            return None
        if not self._fingerprint_valid(state):
            return None
        return state

    def get_truth_history(self, truth_id: str) -> list[dict[str, Any]]:
        if self.state_dir is None:
            return []
        path = self.state_dir / "truth_history" / f"{truth_id}.json"
        if not path.exists():
            return []
        history = json.loads(path.read_text(encoding="utf-8"))
        return history if isinstance(history, list) else []

    def truth_support_dependency_graph(
        self,
        *,
        accepted_evidence_ids: Iterable[str] | None = None,
        epistemic_assessment_ids: Iterable[str] | None = None,
        truth_candidate_ids: Iterable[str] | None = None,
        source_identities: Iterable[str] | None = None,
        causal_support_refs: Iterable[str] | None = None,
        sufficient: bool = True,
        contradictory: bool = False,
    ) -> dict[str, Any]:
        return {
            "accepted_evidence_ids": sorted(str(item) for item in accepted_evidence_ids or []),
            "epistemic_assessment_ids": sorted(str(item) for item in epistemic_assessment_ids or []),
            "truth_candidate_ids": sorted(str(item) for item in truth_candidate_ids or []),
            "source_identities": sorted(str(item) for item in source_identities or []),
            "causal_support_refs": sorted(str(item) for item in causal_support_refs or []),
            "current_support_sufficient": bool(sufficient),
            "contradictory_current_support": bool(contradictory),
        }

    def _support_report(self, support: Mapping[str, Any] | None) -> dict[str, Any]:
        item = dict(support or {})
        stale_assessment_count = 0
        for assessment in item.get("epistemic_assessments") or []:
            if not isinstance(assessment, Mapping):
                continue
            currentness = (
                self._epistemic_assessment_engine()
                .is_epistemic_assessment_current(assessment)
            )
            if currentness.get("assessment_current_state") != (
                "CURRENT_EPISTEMIC_ASSESSMENT"
            ):
                stale_assessment_count += 1
        sufficient = bool(item.get("current_support_sufficient", True))
        contradictory = bool(item.get("contradictory_current_support", False))
        source_independence_current = item.get("source_independence_state") not in {
            "COLLAPSED",
            "NOT_CURRENT",
        }
        causal_support_current = item.get("causal_support_state") not in {
            "WITHDRAWN",
            "NOT_CURRENT",
        }
        return {
            "current_support_sufficient": sufficient,
            "stale_epistemic_assessment_count": stale_assessment_count,
            "source_independence_current": source_independence_current,
            "causal_support_current": causal_support_current,
            "contradictory_current_support": contradictory,
            "truth_policy_satisfied": (
                sufficient
                and stale_assessment_count == 0
                and source_independence_current
                and causal_support_current
                and not contradictory
            ),
        }

    def _epistemic_assessment_engine(self):
        if self.epistemic_assessment_engine is None:
            from runtime.epistemic.accepted_evidence_assessment import (
                AcceptedEvidenceEpistemicAssessmentEngine,
            )

            self.epistemic_assessment_engine = (
                AcceptedEvidenceEpistemicAssessmentEngine()
            )
        return self.epistemic_assessment_engine

    def _decision(
        self,
        *,
        kind: str,
        truth_id: str,
        claim_id: str,
        truth_candidate_id: str | None,
        previous_decision_id: str | None,
        previous_status: str | None,
        new_status: str,
        reason: str,
        support: Mapping[str, Any] | None,
        support_signal: Mapping[str, Any] | None = None,
        semantic_state: str = "COMMITTED_TRUTH",
        confidence: float | int = 1.0,
        extra: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "schema_version": self.schema_version,
            "system": f"truth_{kind}_decision",
            "truth_id": truth_id,
            "truth_candidate_id": truth_candidate_id,
            "claim_id": claim_id,
            "previous_truth_decision_id": previous_decision_id,
            "previous_status": previous_status,
            "new_status": new_status,
            "truth_semantic_state": semantic_state,
            "truth_confidence": float(confidence),
            "decision_reason": reason,
            "support_dependency_graph": dict(support or {}),
            "support_change_signal": dict(support_signal or {}),
            "authority": self._authority(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        payload.update(dict(extra or {}))
        payload[f"truth_{kind}_decision_id"] = self._stable_id(kind, payload)
        payload["decision_fingerprint"] = self._fingerprint(payload)
        return payload

    def _assert_current_state(self, state: Mapping[str, Any]) -> None:
        if state.get("truth_id") in UNKNOWN:
            raise ValueError("truth_id_required")
        if state.get("claim_id") in UNKNOWN:
            raise ValueError("claim_id_required")
        if state.get("current_truth_decision_id") in UNKNOWN:
            raise ValueError("current_truth_decision_id_required")
        if state.get("authority") != self.authority:
            raise ValueError("truth_current_authority_required")
        if not self._fingerprint_valid(state):
            raise ValueError("corrupted_truth_state_fingerprint")

    def _assert_decision(self, decision: Mapping[str, Any]) -> None:
        if self._decision_id(decision) in UNKNOWN:
            raise ValueError("truth_decision_id_required")
        authority = decision.get("authority")
        if not isinstance(authority, Mapping) or (
            authority.get("truth_current_authority") != self.authority
        ):
            raise ValueError("truth_current_authority_required")
        if decision.get("truth_id") in UNKNOWN:
            raise ValueError("truth_id_required")
        if decision.get("claim_id") in UNKNOWN:
            raise ValueError("claim_id_required")
        if not self._fingerprint_valid(decision):
            raise ValueError("corrupted_truth_decision_fingerprint")

    def _decision_id(self, decision: Mapping[str, Any]) -> str | None:
        for key in (
            "truth_activation_decision_id",
            "truth_review_decision_id",
            "truth_reassessment_decision_id",
            "truth_invalidation_decision_id",
            "truth_revalidation_decision_id",
            "truth_supersession_decision_id",
        ):
            if decision.get(key):
                return str(decision[key])
        return None

    def _authority(self) -> dict[str, str]:
        return {
            "truth_current_authority": self.authority,
            "evidence": "NONE",
            "epistemic_assessment": "NONE",
            "knowledge": "NONE",
            "capability": "NONE",
            "runtime": "NONE",
            "budget": "NONE",
            "execution": "NONE",
        }

    def _stable_id(self, kind: str, payload: Mapping[str, Any]) -> str:
        seed = {
            key: value
            for key, value in dict(payload).items()
            if key not in {"created_at", "decision_fingerprint"}
        }
        encoded = json.dumps(seed, sort_keys=True, ensure_ascii=True, default=str)
        return f"truth_{kind}_decision_{hashlib.sha1(encoded.encode('utf-8')).hexdigest()[:12]}"

    def _fingerprint(self, payload: Mapping[str, Any]) -> str:
        item = {
            key: value
            for key, value in dict(payload).items()
            if key not in {"fingerprint", "decision_fingerprint"}
        }
        encoded = json.dumps(item, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _fingerprint_valid(self, payload: Mapping[str, Any]) -> bool:
        fingerprint = payload.get("decision_fingerprint") or payload.get("fingerprint")
        return bool(fingerprint and fingerprint == self._fingerprint(payload))


truth_current_authority_lifecycle_engine = TruthCurrentAuthorityLifecycleEngine()


__all__ = [
    "REVIEW_TRIGGERS",
    "TruthCurrentAuthorityLifecycleEngine",
    "TruthLifecycleStatus",
    "truth_current_authority_lifecycle_engine",
]
