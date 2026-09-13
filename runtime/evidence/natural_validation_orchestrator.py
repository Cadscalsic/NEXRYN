from __future__ import annotations

import json
from typing import Any, Iterable, Mapping

from runtime.evidence.current_evidence_need import (
    CurrentEvidenceNeedAuthorityEngine,
)
from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.evidence.validation_request import ValidationRequestAuthorityEngine
from runtime.evidence.validation_sponsorship import (
    ValidationSponsorshipAuthorityEngine,
)


UNKNOWN = {"", "NONE", "None", "Not Available", "UNKNOWN", "null", "NULL"}


class NaturalCanonicalValidationOrchestrator:
    """Authority-free bridge from current qualification deficits to validation work."""

    SYSTEM = "natural_canonical_validation_orchestrator"
    AUTHORITY = "NONE"
    BEHAVIORAL_AUTHORITY = "NONE"

    def __init__(
        self,
        *,
        need_authority: CurrentEvidenceNeedAuthorityEngine | None = None,
        sponsorship_authority: ValidationSponsorshipAuthorityEngine | None = None,
        request_authority: ValidationRequestAuthorityEngine | None = None,
        evidence_plan_store: EvidenceAcquisitionPlanStore | None = None,
    ) -> None:
        self.need_authority = need_authority or CurrentEvidenceNeedAuthorityEngine()
        self.sponsorship_authority = (
            sponsorship_authority
            or ValidationSponsorshipAuthorityEngine(
                need_authority=self.need_authority,
            )
        )
        self.request_authority = (
            request_authority
            or ValidationRequestAuthorityEngine(
                sponsorship_authority=self.sponsorship_authority,
            )
        )
        self.evidence_plan_store = evidence_plan_store or EvidenceAcquisitionPlanStore()

    def orchestrate(
        self,
        qualification_results: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
        *,
        max_new_needs: int = 3,
    ) -> dict[str, Any]:
        results = self.extract_qualification_results(qualification_results)
        rows: list[dict[str, Any]] = []
        bounded = max(0, int(max_new_needs or 0))
        candidate_count = 0
        decision_count = 0
        active_need_ids: list[str] = []
        active_sponsorship_ids: list[str] = []
        pending_request_ids: list[str] = []
        plan_reports: list[dict[str, Any]] = []

        for result in results:
            if candidate_count >= bounded:
                rows.append({
                    "orchestration_state": "BOUNDED_ORCHESTRATION_LIMIT_REACHED",
                    "qualification_decision_id": self._decision_id(result),
                })
                continue
            eligibility = self._deficit_eligibility(result)
            if eligibility["eligibility_state"] != "ELIGIBLE_CURRENT_DEFICIT":
                rows.append(eligibility)
                continue
            try:
                candidates = self.need_authority.candidates_from_qualification_deficit(
                    result,
                    producer="IntegratedCapabilityQualificationEngine",
                )
            except Exception as error:
                rows.append({
                    **eligibility,
                    "orchestration_state": "FAILED_CLOSED_NEED_CANDIDATE_ERROR",
                    "failure_reason": str(error),
                })
                continue
            for candidate in candidates:
                if candidate_count >= bounded:
                    rows.append({
                        **eligibility,
                        "orchestration_state": (
                            "BOUNDED_ORCHESTRATION_LIMIT_REACHED"
                        ),
                    })
                    break
                if self._missing(candidate.get("evidence_need_id")):
                    rows.append({
                        **eligibility,
                        "orchestration_state": "NEED_CANDIDATE_REJECTED",
                        "candidate": candidate,
                    })
                    continue
                candidate_count += 1
                row = self._orchestrate_candidate(
                    candidate,
                    current_source_decision_id=eligibility[
                        "qualification_decision_id"
                    ],
                )
                rows.append({**eligibility, **row})
                decision_count += int(row.get("need_decision_recorded", False))
                if row.get("active_need_id"):
                    active_need_ids.append(row["active_need_id"])
                if row.get("active_sponsorship_id"):
                    active_sponsorship_ids.append(row["active_sponsorship_id"])
                if row.get("pending_request_id"):
                    pending_request_ids.append(row["pending_request_id"])
                if row.get("plan_admission_report"):
                    plan_reports.append(row["plan_admission_report"])

        return {
            "system": self.SYSTEM,
            "authority": self.AUTHORITY,
            "behavioral_authority": self.BEHAVIORAL_AUTHORITY,
            "natural_deficit_count": len({
                row.get("qualification_decision_id")
                for row in rows
                if row.get("eligibility_state") == "ELIGIBLE_CURRENT_DEFICIT"
                and row.get("qualification_decision_id") not in UNKNOWN
            }),
            "natural_need_candidate_count": candidate_count,
            "natural_need_decision_count": decision_count,
            "natural_active_need_count": len(set(active_need_ids)),
            "natural_active_need_ids": sorted(set(active_need_ids)),
            "natural_active_sponsorship_count": len(set(active_sponsorship_ids)),
            "natural_active_sponsorship_ids": sorted(set(active_sponsorship_ids)),
            "natural_pending_request_count": len(set(pending_request_ids)),
            "natural_pending_request_ids": sorted(set(pending_request_ids)),
            "natural_plan_admission_count": len(plan_reports),
            "natural_plan_created_count": sum(
                1 for report in plan_reports
                if report.get("evidence_plan_created") is True
            ),
            "orchestration_rows": rows,
            "max_new_needs_per_run": bounded,
            "selector_authority": "NONE",
            "realized_yield_selector_consumption": False,
            "raw_evidence_created_directly": False,
            "accepted_evidence_created_directly": False,
            "truth_authority": "NONE",
            "knowledge_authority": "NONE",
            "planning_authority": "NONE",
            "goal_authority": "NONE",
            "intent_authority": "NONE",
            "budget_authority": "NONE",
        }

    def _orchestrate_candidate(
        self,
        candidate: Mapping[str, Any],
        *,
        current_source_decision_id: str,
    ) -> dict[str, Any]:
        try:
            need_decision = self.need_authority.decide_current_need(
                candidate,
                current_source_decision_id=current_source_decision_id,
            )
        except Exception as error:
            return {
                "orchestration_state": "FAILED_CLOSED_NEED_DECISION_ERROR",
                "need_decision_recorded": False,
                "failure_reason": str(error),
            }
        need_state = dict(need_decision.get("current_state") or {})
        if need_state.get("lifecycle_status") != "ACTIVE":
            return {
                "orchestration_state": "NEED_NOT_CURRENT_DOWNSTREAM_BLOCKED",
                "need_decision_recorded": True,
                "need_decision_state": self._decision_state(need_decision),
                "active_need_id": None,
            }

        sponsorship_candidate = self.sponsorship_authority.candidate_from_current_need(
            need_state["evidence_need_id"],
        )
        sponsorship_decision = self.sponsorship_authority.decide_sponsorship(
            sponsorship_candidate,
        )
        sponsorship_state = dict(sponsorship_decision.get("current_state") or {})
        if sponsorship_state.get("lifecycle_status") != "ACTIVE":
            return {
                "orchestration_state": "SPONSORSHIP_NOT_CURRENT_REQUEST_BLOCKED",
                "need_decision_recorded": True,
                "need_decision_state": self._decision_state(need_decision),
                "sponsorship_decision_state": self._decision_state(
                    sponsorship_decision
                ),
                "active_need_id": need_state["evidence_need_id"],
                "active_sponsorship_id": None,
            }

        existing_plan_index = self._existing_work_index(
            evidence_need_id=need_state["evidence_need_id"],
            validation_sponsorship_id=sponsorship_state[
                "validation_sponsorship_id"
            ],
        )
        request_candidate = self.request_authority.candidate_from_current_sponsorship(
            sponsorship_state["validation_sponsorship_id"],
            existing_plan_index=existing_plan_index,
        )
        request_decision = self.request_authority.decide_request(request_candidate)
        request_state = dict(request_decision.get("current_state") or {})
        if request_state.get("lifecycle_status") != "PENDING":
            return {
                "orchestration_state": "REQUEST_NOT_PENDING_PLAN_BLOCKED",
                "need_decision_recorded": True,
                "need_decision_state": self._decision_state(need_decision),
                "sponsorship_decision_state": self._decision_state(
                    sponsorship_decision
                ),
                "request_decision_state": self._decision_state(request_decision),
                "active_need_id": need_state["evidence_need_id"],
                "active_sponsorship_id": sponsorship_state[
                    "validation_sponsorship_id"
                ],
                "pending_request_id": None,
            }

        plan_report = self.evidence_plan_store.admit_validation_request_to_plan(
            request_state["validation_request_id"],
            request_authority=self.request_authority,
            active_schedule_index=self._active_schedule_index(
                evidence_need_id=need_state["evidence_need_id"],
                validation_request_id=request_state["validation_request_id"],
            ),
        )
        return {
            "orchestration_state": "REQUEST_ROUTED_TO_EVIDENCE_PLAN_ADMISSION",
            "need_decision_recorded": True,
            "need_decision_state": self._decision_state(need_decision),
            "sponsorship_decision_state": self._decision_state(
                sponsorship_decision
            ),
            "request_decision_state": self._decision_state(request_decision),
            "active_need_id": need_state["evidence_need_id"],
            "active_sponsorship_id": sponsorship_state[
                "validation_sponsorship_id"
            ],
            "pending_request_id": request_state["validation_request_id"],
            "plan_admission_report": plan_report,
        }

    def _deficit_eligibility(
        self,
        result: Mapping[str, Any],
    ) -> dict[str, Any]:
        decision = dict(result.get("qualification_decision") or {})
        assessment = dict(result.get("capability_evidence_assessment") or {})
        failures = [
            str(item)
            for item in decision.get("promotion_failures", []) or []
        ]
        if decision.get("qualification_authority") != (
            "INTEGRATED_CAPABILITY_QUALIFICATION_ENGINE"
        ):
            state = "INELIGIBLE_MISSING_QUALIFICATION_AUTHORITY"
        elif decision.get("decision_state") != "PROMOTION_DENIED":
            state = "INELIGIBLE_NO_CURRENT_PROMOTION_DEFICIT"
        elif not decision.get("qualification_decision_id"):
            state = "INELIGIBLE_MISSING_DECISION_ID"
        elif not assessment.get("capability_evidence_assessment_id"):
            state = "INELIGIBLE_MISSING_ASSESSMENT_ID"
        elif not failures:
            state = "INELIGIBLE_NO_GOVERNED_DEFICIT_FAILURES"
        else:
            state = "ELIGIBLE_CURRENT_DEFICIT"
        return {
            "eligibility_state": state,
            "qualification_decision_id": decision.get("qualification_decision_id"),
            "capability_evidence_assessment_id": assessment.get(
                "capability_evidence_assessment_id"
            ),
            "capability_id": decision.get("capability_id"),
            "promotion_failures": failures,
        }

    def _existing_work_index(
        self,
        *,
        evidence_need_id: str,
        validation_sponsorship_id: str,
    ) -> list[dict[str, Any]]:
        matches = []
        for plan in self._plan_rows(("pending", "active")):
            if (
                plan.get("source_evidence_need_id") == evidence_need_id
                or plan.get("source_validation_sponsorship_id")
                == validation_sponsorship_id
            ):
                matches.append({
                    "plan_id": plan.get("plan_id"),
                    "source_evidence_need_id": plan.get("source_evidence_need_id"),
                    "source_validation_sponsorship_id": plan.get(
                        "source_validation_sponsorship_id"
                    ),
                    "lifecycle_state": plan.get("lifecycle_state"),
                })
        return matches

    def _active_schedule_index(
        self,
        *,
        evidence_need_id: str,
        validation_request_id: str,
    ) -> list[dict[str, Any]]:
        matches = []
        for plan in self._plan_rows(("schedules",)):
            if (
                plan.get("source_evidence_need_id") == evidence_need_id
                or plan.get("source_validation_request_id") == validation_request_id
            ):
                matches.append({
                    "schedule_id": plan.get("schedule_id"),
                    "source_evidence_need_id": plan.get("source_evidence_need_id"),
                    "source_validation_request_id": plan.get(
                        "source_validation_request_id"
                    ),
                    "scheduling_state": plan.get("scheduling_state"),
                })
        return matches

    def _plan_rows(self, names: Iterable[str]) -> list[dict[str, Any]]:
        rows = []
        for name in names:
            directory = self.evidence_plan_store.root_path / name
            if not directory.exists():
                continue
            for path in sorted(directory.glob("*.json")):
                if path.name.endswith(".tmp"):
                    continue
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                    continue
                if isinstance(payload, dict):
                    rows.append(payload)
        return rows

    @classmethod
    def extract_qualification_results(
        cls,
        payload: Iterable[Mapping[str, Any]] | Mapping[str, Any] | None,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in cls._walk(payload):
            if not isinstance(item, Mapping):
                continue
            if not (
                isinstance(item.get("qualification_decision"), Mapping)
                and isinstance(item.get("capability_evidence_assessment"), Mapping)
            ):
                continue
            result = {
                "qualification_decision": dict(item["qualification_decision"]),
                "capability_evidence_assessment": dict(
                    item["capability_evidence_assessment"]
                ),
            }
            decision_id = cls._decision_id(result)
            key = decision_id if decision_id not in UNKNOWN else json.dumps(
                result,
                sort_keys=True,
                default=str,
            )
            if key in seen:
                continue
            seen.add(key)
            rows.append(result)
        return rows

    @classmethod
    def _walk(cls, value: Any) -> Iterable[Any]:
        yield value
        if isinstance(value, Mapping):
            for item in value.values():
                yield from cls._walk(item)
        elif isinstance(value, list):
            for item in value:
                yield from cls._walk(item)

    @staticmethod
    def _decision_id(result: Mapping[str, Any]) -> str:
        decision = result.get("qualification_decision")
        if isinstance(decision, Mapping):
            return str(decision.get("qualification_decision_id") or "Not Available")
        return "Not Available"

    @staticmethod
    def _missing(value: Any) -> bool:
        return str(value or "").strip() in UNKNOWN

    @staticmethod
    def _decision_state(decision: Mapping[str, Any]) -> str | None:
        payload = decision.get("decision")
        if isinstance(payload, Mapping):
            return payload.get("decision_state")
        return decision.get("decision_state")


__all__ = ["NaturalCanonicalValidationOrchestrator"]
