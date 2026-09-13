from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from runtime.capability_intelligence.integrated_capability_qualification import (
    CapabilityQualificationLevel,
    IntegratedCapabilityQualificationEngine,
    capability_id_for_subject,
)
from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore


UNKNOWN = {"", "NONE", "None", "Not Available", "UNKNOWN", "null", "NULL"}


class NaturalQualificationAssessmentBinding:
    """Authority-free runtime bridge into the canonical qualification engine."""

    SYSTEM = "natural_qualification_assessment_binding"
    AUTHORITY = "NONE"
    BEHAVIORAL_AUTHORITY = "NONE"

    def __init__(
        self,
        *,
        evidence_plan_store: EvidenceAcquisitionPlanStore | None = None,
        qualification_engine: IntegratedCapabilityQualificationEngine | None = None,
        state_dir: str | os.PathLike[str] = (
            "runtime/state/qualification_assessment_binding"
        ),
    ) -> None:
        self.evidence_plan_store = evidence_plan_store or EvidenceAcquisitionPlanStore()
        self.qualification_engine = (
            qualification_engine or IntegratedCapabilityQualificationEngine()
        )
        self.state_dir = Path(state_dir)
        self.assessments_dir = self.state_dir / "assessments"

    def assess_current_accepted_evidence(
        self,
        *,
        run_id: str,
        accepted_evidence: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        self.assessments_dir.mkdir(parents=True, exist_ok=True)
        evidence_rows = (
            [dict(item) for item in accepted_evidence]
            if accepted_evidence is not None
            else self.load_current_accepted_evidence()
        )
        groups = self._groups(evidence_rows)
        results: list[dict[str, Any]] = []
        inapplicable: list[dict[str, Any]] = []
        replayed = 0
        for group in groups:
            if group["input_state"] != "QUALIFICATION_INPUT_CONTRACT_SATISFIED":
                inapplicable.append(group)
                continue
            fingerprint = self.assessment_fingerprint(
                run_id=run_id,
                capability_id=group["capability_id"],
                requested_level=group["requested_level"],
                evidence_rows=group["accepted_evidence"],
            )
            replay = self._read_assessment(fingerprint)
            if replay:
                replayed += 1
                result = dict(replay["qualification_result"])
                result.setdefault("qualification_binding", {})
                result["qualification_binding"].update({
                    "assessment_replay_state": "SAME_STATE_REPLAY",
                    "assessment_state_fingerprint": fingerprint,
                    "run_id": run_id,
                })
                results.append(result)
                continue
            result = self.qualification_engine.decide(
                group["capability_subject"],
                group["accepted_evidence"],
                requested_level=group["requested_level"],
                current_level=group["current_level"],
                architecture_present=True,
                runtime_reachable=True,
                required_independent_sources=group[
                    "required_independent_sources"
                ],
                assessment_run_id=run_id,
            )
            result["qualification_binding"] = {
                "system": self.SYSTEM,
                "authority": self.AUTHORITY,
                "behavioral_authority": self.BEHAVIORAL_AUTHORITY,
                "run_id": run_id,
                "capability_id": group["capability_id"],
                "assessment_state_fingerprint": fingerprint,
                "assessment_replay_state": "NEW_EVIDENCE_STATE",
                "governed_accepted_evidence_only": True,
                "downstream_synthetic_object_injection": False,
                "main_grants_qualification": False,
            }
            self._write_assessment(fingerprint, result)
            results.append(result)
        return {
            "system": self.SYSTEM,
            "authority": self.AUTHORITY,
            "behavioral_authority": self.BEHAVIORAL_AUTHORITY,
            "run_id": run_id,
            "qualification_assessment_invocation_count": len(results),
            "qualification_assessment_replay_count": replayed,
            "qualification_assessment_not_applicable_count": len(inapplicable),
            "accepted_evidence_input_count": len(evidence_rows),
            "capability_ids": sorted({
                str(result.get("qualification_decision", {}).get("capability_id"))
                for result in results
                if result.get("qualification_decision", {}).get("capability_id")
                not in UNKNOWN
            }),
            "qualification_decision_ids": [
                result.get("qualification_decision", {}).get(
                    "qualification_decision_id"
                )
                for result in results
            ],
            "promotion_failure_count": sum(
                len(result.get("qualification_decision", {}).get(
                    "promotion_failures",
                    [],
                ))
                for result in results
            ),
            "structured_deficit_count": sum(
                1
                for result in results
                if result.get("qualification_decision", {}).get(
                    "decision_state"
                )
                == "PROMOTION_DENIED"
                and result.get("qualification_decision", {}).get(
                    "promotion_failures"
                )
            ),
            "qualification_results": results,
            "inapplicable_inputs": inapplicable,
            "governed_accepted_evidence_only": True,
            "downstream_synthetic_object_injection": False,
            "main_grants_qualification": False,
            "truth_authority": "NONE",
            "budget_authority": "NONE",
            "evidence_acceptance_authority": "NONE",
        }

    def load_current_accepted_evidence(self) -> list[dict[str, Any]]:
        directory = self.evidence_plan_store.root_path / "accepted_evidence"
        if not directory.exists():
            return []
        rows = []
        for path in sorted(directory.glob("*.json")):
            if path.name.endswith(".tmp"):
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                continue
            if isinstance(payload, Mapping):
                rows.append(dict(payload))
        return rows

    def assessment_fingerprint(
        self,
        *,
        run_id: str,
        capability_id: str,
        requested_level: str,
        evidence_rows: Iterable[Mapping[str, Any]],
    ) -> str:
        payload = {
            "run_id": str(run_id or "Not Available"),
            "capability_id": capability_id,
            "requested_level": requested_level,
            "accepted_evidence": [
                {
                    "accepted_evidence_id": item.get("accepted_evidence_id"),
                    "evidence_decision_id": item.get("evidence_decision_id"),
                    "current_state_fingerprint": (
                        item.get("accepted_evidence_current_state", {}) or {}
                    ).get("fingerprint")
                    if isinstance(item.get("accepted_evidence_current_state"), Mapping)
                    else item.get("accepted_evidence_current_status"),
                    "source": item.get("canonical_source_identity")
                    or item.get("producer_operation_id"),
                }
                for item in sorted(
                    [dict(row) for row in evidence_rows],
                    key=lambda row: str(row.get("accepted_evidence_id") or ""),
                )
            ],
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
        ).hexdigest()

    def _groups(self, evidence_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, dict[str, Any]] = {}
        inapplicable: list[dict[str, Any]] = []
        for row in evidence_rows:
            subject = row.get("capability_subject")
            if not isinstance(subject, Mapping):
                inapplicable.append({
                    "input_state": "QUALIFICATION_ASSESSMENT_NOT_APPLICABLE",
                    "reason": "missing_capability_subject",
                    "accepted_evidence_id": row.get("accepted_evidence_id"),
                })
                continue
            target = self._requested_level(row)
            if target is None:
                inapplicable.append({
                    "input_state": "QUALIFICATION_ASSESSMENT_NOT_APPLICABLE",
                    "reason": "missing_explicit_qualification_target_level",
                    "accepted_evidence_id": row.get("accepted_evidence_id"),
                    "capability_id": row.get("capability_id"),
                })
                continue
            capability_id = capability_id_for_subject(subject)
            if row.get("capability_id") not in UNKNOWN and row.get("capability_id") != capability_id:
                inapplicable.append({
                    "input_state": "QUALIFICATION_ASSESSMENT_NOT_APPLICABLE",
                    "reason": "capability_id_mismatch",
                    "accepted_evidence_id": row.get("accepted_evidence_id"),
                    "capability_id": row.get("capability_id"),
                    "expected_capability_id": capability_id,
                })
                continue
            key = json.dumps(
                {
                    "capability_id": capability_id,
                    "requested_level": target,
                },
                sort_keys=True,
            )
            grouped.setdefault(key, {
                "input_state": "QUALIFICATION_INPUT_CONTRACT_SATISFIED",
                "capability_id": capability_id,
                "capability_subject": dict(subject),
                "requested_level": target,
                "current_level": str(row.get("current_qualification_level") or "NOT_QUALIFIED"),
                "required_independent_sources": int(
                    row.get("required_independent_sources")
                    or row.get("qualification_required_independent_sources")
                    or 2
                ),
                "accepted_evidence": [],
            })["accepted_evidence"].append(row)
        return list(grouped.values()) + inapplicable

    def _requested_level(self, row: Mapping[str, Any]) -> str | None:
        value = (
            row.get("qualification_target_level")
            or row.get("requested_qualification_level")
            or row.get("target_qualification_level")
        )
        if str(value or "").strip() in UNKNOWN:
            return None
        try:
            return CapabilityQualificationLevel(str(value)).value
        except ValueError:
            return None

    def _read_assessment(self, fingerprint: str) -> dict[str, Any] | None:
        path = self.assessments_dir / f"{fingerprint}.json"
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    def _write_assessment(
        self,
        fingerprint: str,
        qualification_result: Mapping[str, Any],
    ) -> None:
        path = self.assessments_dir / f"{fingerprint}.json"
        payload = {
            "system": "qualification_assessment_binding_record",
            "assessment_state_fingerprint": fingerprint,
            "qualification_result": dict(qualification_result),
            "authority": "NONE",
        }
        encoded = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
        json.loads(encoded)
        path.write_text(encoded + "\n", encoding="utf-8")


__all__ = ["NaturalQualificationAssessmentBinding"]
