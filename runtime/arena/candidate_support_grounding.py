"""Evidence-grounded, observation-only support metrics for Arena candidates."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping


NEUTRAL_MISSING_VALUE = 0.5
NON_SPATIAL_OPERATIONS = {"classify", "compare", "reason", "select_label"}


class CandidateSupportGroundingEngine:
    system_name = "candidate_support_grounding"

    def ground(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        item = dict(candidate or {})
        candidate_id = str(item.get("candidate_id") or "UNKNOWN")
        lineage = item.get("route_origin_lineage")
        lineage = lineage if isinstance(lineage, Mapping) else {}
        run_id = str(item.get("run_id") or lineage.get("run_id") or "UNKNOWN")
        task_id = str(item.get("task_id") or lineage.get("task_id") or "UNKNOWN")
        plan_id = item.get("execution_plan_id")
        candidate_fingerprint = self._fingerprint(item)
        truth = self._truth_metric(
            item, candidate_id, candidate_fingerprint, run_id, task_id, plan_id
        )
        localization = self._localization_metric(
            item, candidate_id, candidate_fingerprint, run_id, task_id, plan_id
        )
        payload = {
            "schema_version": "candidate_support_grounding.v1",
            "candidate_id": candidate_id,
            "candidate_fingerprint": candidate_fingerprint,
            "run_id": run_id,
            "task_id": task_id,
            "execution_plan_id": plan_id,
            "truth_support_metric": truth,
            "localization_quality_metric": localization,
            "authority": "OBSERVATION_ONLY",
            "behavioral_authority": "NONE",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        payload["immutable_fingerprint"] = self._fingerprint(payload)
        return payload

    def _truth_metric(self, candidate, candidate_id, candidate_fingerprint, run_id, task_id, plan_id):
        observations = candidate.get("truth_support_observations") or candidate.get("accepted_evidence") or []
        observations = observations if isinstance(observations, list) else []
        accepted = []
        rejected = []
        seen = set()
        contradictions = 0
        duplicates = 0
        for raw in observations:
            row = dict(raw) if isinstance(raw, Mapping) else {}
            evidence_id = str(row.get("accepted_evidence_id") or row.get("evidence_id") or "")
            reason = self._truth_rejection(row, candidate_id, run_id, evidence_id, seen)
            if evidence_id in seen and evidence_id:
                duplicates += 1
            if evidence_id:
                seen.add(evidence_id)
            if row.get("contradiction") is True:
                contradictions += 1
            if reason:
                rejected.append({"evidence_id": evidence_id or None, "reason": reason})
            else:
                accepted.append(row)
        values = [self._unit(row.get("support_value")) for row in accepted]
        if values:
            value = sum(values) / len(values)
            origin = "EVIDENCE_DERIVED"
            missing_reason = None
        else:
            value = NEUTRAL_MISSING_VALUE
            origin = "INSUFFICIENT_EVIDENCE"
            missing_reason = "NO_CURRENT_INDEPENDENT_ACCEPTED_CANDIDATE_BOUND_EVIDENCE"
        return self._metric(
            "truth_support_metric.v1", "truth_support", candidate_id,
            candidate_fingerprint, run_id, task_id, plan_id, value, origin,
            [str(row.get("accepted_evidence_id") or row.get("evidence_id")) for row in accepted],
            len(accepted) / len(observations) if observations else 0.0,
            observations, rejected, contradictions, duplicates, missing_reason,
        )

    def _localization_metric(self, candidate, candidate_id, candidate_fingerprint, run_id, task_id, plan_id):
        operation = str(candidate.get("operation") or "")
        observations = candidate.get("localization_observations") or []
        observations = observations if isinstance(observations, list) else []
        if operation in NON_SPATIAL_OPERATIONS:
            return self._metric(
                "localization_quality_metric.v1", "localization_quality",
                candidate_id, candidate_fingerprint, run_id, task_id, plan_id,
                NEUTRAL_MISSING_VALUE, "NOT_APPLICABLE", [], 0.0,
                observations, [], 0, 0, "OPERATION_HAS_NO_SPATIAL_LOCALIZATION_SEMANTICS",
            )
        accepted = []
        rejected = []
        seen = set()
        duplicates = 0
        for raw in observations:
            row = dict(raw) if isinstance(raw, Mapping) else {}
            observation_id = str(row.get("observation_id") or "")
            reason = self._localization_rejection(row, candidate_id, run_id, observation_id, seen)
            if observation_id in seen and observation_id:
                duplicates += 1
            if observation_id:
                seen.add(observation_id)
            if reason:
                rejected.append({"observation_id": observation_id or None, "reason": reason})
            else:
                accepted.append(row)
        values = []
        for row in accepted:
            predicted = self._cells(row.get("predicted_affected_cells"))
            observed = self._cells(row.get("observed_affected_cells"))
            union = predicted | observed
            values.append(len(predicted & observed) / len(union) if union else 1.0)
        if values:
            value = sum(values) / len(values)
            origin = "MEASURED"
            missing_reason = None
        else:
            value = NEUTRAL_MISSING_VALUE
            origin = "INSUFFICIENT_EVIDENCE"
            missing_reason = "NO_CURRENT_INDEPENDENT_CANDIDATE_BOUND_LOCALIZATION_OBSERVATION"
        return self._metric(
            "localization_quality_metric.v1", "localization_quality",
            candidate_id, candidate_fingerprint, run_id, task_id, plan_id,
            value, origin, [str(row.get("observation_id")) for row in accepted],
            len(accepted) / len(observations) if observations else 0.0,
            observations, rejected, 0, duplicates, missing_reason,
        )

    def _metric(self, schema, name, candidate_id, candidate_fingerprint, run_id, task_id, plan_id, value, origin, references, coverage, raw, rejected, contradictions, duplicates, missing_reason):
        payload = {
            "metric_id": f"{name}_{self._fingerprint([candidate_id, run_id, references, value])[:16]}",
            "schema_version": schema,
            "metric_name": name,
            "candidate_id": candidate_id,
            "candidate_fingerprint": candidate_fingerprint,
            "claim_or_operation_identity": candidate_id,
            "raw_observations": raw,
            "evidence_references": references,
            "source_independence_state": "VERIFIED" if references else "NOT_AVAILABLE",
            "provenance_state": "VERIFIED" if references else "NOT_AVAILABLE",
            "contradiction_count": contradictions,
            "duplicate_count": duplicates,
            "raw_metric_value": value,
            "normalized_value": round(self._unit(value), 4),
            "coverage": round(self._unit(coverage), 4),
            "value_origin": origin,
            "missing_data_reason": missing_reason,
            "rejected_inputs": rejected,
            "producer_component": self.system_name,
            "run_id": run_id,
            "task_id": task_id,
            "execution_plan_id": plan_id,
            "authority": "OBSERVATION_ONLY",
            "behavioral_authority": "NONE",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        payload["immutable_fingerprint"] = self._fingerprint(payload)
        return payload

    def _truth_rejection(self, row, candidate_id, run_id, evidence_id, seen):
        if not evidence_id:
            return "MISSING_EVIDENCE_ID"
        if evidence_id in seen:
            return "DUPLICATE_EVIDENCE"
        if row.get("evidence_type") == "D8_DIRECTIONAL":
            return "D8_DIRECTION_IS_NOT_ACCEPTED_EVIDENCE"
        if row.get("evidence_acceptance_state") != "ACCEPTED":
            return "EVIDENCE_NOT_ACCEPTED"
        if row.get("candidate_id") != candidate_id:
            return "CANDIDATE_IDENTITY_MISMATCH"
        if str(row.get("run_id")) != run_id:
            return "SOURCE_RUN_MISMATCH"
        if row.get("independence_state") != "INDEPENDENT":
            return "SOURCE_NOT_INDEPENDENT"
        if row.get("provenance_verified") is not True or not row.get("immutable_fingerprint"):
            return "PROVENANCE_NOT_VERIFIED"
        if row.get("contradiction") is True:
            return "CONTRADICTORY_EVIDENCE"
        if row.get("support_value") is None:
            return "MISSING_SUPPORT_VALUE"
        return None

    def _localization_rejection(self, row, candidate_id, run_id, observation_id, seen):
        if not observation_id:
            return "MISSING_OBSERVATION_ID"
        if observation_id in seen:
            return "DUPLICATE_OBSERVATION"
        if row.get("candidate_id") != candidate_id:
            return "CANDIDATE_IDENTITY_MISMATCH"
        if str(row.get("run_id")) != run_id:
            return "SOURCE_RUN_MISMATCH"
        if not str(row.get("independence_state") or "").startswith("INDEPENDENT"):
            return "OBSERVATION_NOT_INDEPENDENT"
        if row.get("provenance_verified") is not True or not row.get("immutable_fingerprint"):
            return "PROVENANCE_NOT_VERIFIED"
        if not isinstance(row.get("predicted_affected_cells"), list) or not isinstance(row.get("observed_affected_cells"), list):
            return "LOCALIZATION_MASK_MISSING"
        return None

    @staticmethod
    def _cells(value):
        return {tuple(cell) for cell in value or [] if isinstance(cell, (list, tuple)) and len(cell) == 2}

    @staticmethod
    def _unit(value):
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _fingerprint(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True, default=str, separators=(",", ":")).encode()).hexdigest()


candidate_support_grounding_engine = CandidateSupportGroundingEngine()


def apply_candidate_support_grounding(candidate: Mapping[str, Any]) -> dict[str, Any]:
    proposal = dict(candidate or {})
    grounding = candidate_support_grounding_engine.ground(proposal)
    proposal["truth_support_metric"] = grounding["truth_support_metric"]
    proposal["localization_quality_metric"] = grounding[
        "localization_quality_metric"
    ]
    proposal["candidate_support_grounding"] = grounding
    proposal["truth_support"] = grounding["truth_support_metric"][
        "normalized_value"
    ]
    proposal["localization_support"] = grounding[
        "localization_quality_metric"
    ]["normalized_value"]
    return proposal


__all__ = [
    "CandidateSupportGroundingEngine",
    "apply_candidate_support_grounding",
    "candidate_support_grounding_engine",
]
