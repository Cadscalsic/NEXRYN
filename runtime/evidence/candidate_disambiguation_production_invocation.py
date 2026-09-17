"""Production invocation policy for candidate-disambiguation planning."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from runtime.evidence.candidate_disambiguation_planning_adapter import (
    CandidateDisambiguationPlanningAdapter,
)


UNKNOWN = {"", "NONE", "None", "Not Available", "UNKNOWN", "null", "NULL"}


class CandidateDisambiguationProductionInvocationPolicy:
    """Route natural Arena D3 needs into D6 planning without adding authority."""

    SYSTEM = "candidate_disambiguation_production_invocation_policy"
    AUTHORITY = "NONE"
    BEHAVIORAL_AUTHORITY = "NONE"
    SUPPORTED_METHODS = {"DISCRIMINATIVE_VALIDATION"}
    SUPPORTED_EVIDENCE_REQUIREMENTS = {
        "VALID_OBSERVATION_FOR_WHICH_TIED_CANDIDATES_PREDICT_DIFFERENT_OUTPUTS",
        "VALID_CONTEXT_THAT_EXERCISES_THE_DIFFERENT_CANDIDATE_OPERATION_SEMANTICS",
    }

    def __init__(
        self,
        adapter: CandidateDisambiguationPlanningAdapter | None = None,
    ) -> None:
        self.adapter = adapter or CandidateDisambiguationPlanningAdapter()
        self._bindings_by_need_id: dict[str, str] = {}
        self._need_ids_by_disagreement: dict[str, set[str]] = {}

    def invoke_from_arena_report(
        self,
        arena_report: Mapping[str, Any] | None,
        *,
        current_run_id: str | None = None,
        max_needs: int = 3,
    ) -> dict[str, Any]:
        arena_report = arena_report if isinstance(arena_report, Mapping) else {}
        needs = self._extract_needs(arena_report)
        rows: list[dict[str, Any]] = []
        plan_ids: list[str] = []
        bounded = max(0, int(max_needs or 0))

        for need in needs[:bounded]:
            row = self._invoke_need(
                need,
                arena_report=arena_report,
                current_run_id=current_run_id,
            )
            rows.append(row)
            plan_id = (
                (row.get("adapter_report") or {})
                .get("evidence_plan_report", {})
                .get("evidence_plan_id")
            )
            if plan_id:
                plan_ids.append(str(plan_id))
        for need in needs[bounded:]:
            rows.append({
                "semantic_replay_state": "NOT_EVALUATED_BOUND_REACHED",
                "invocation_state": "FAILED_CLOSED",
                "disambiguation_need_id": need.get("disambiguation_need_id"),
                "failure_reasons": ["bounded_invocation_limit_reached"],
            })

        reached = [
            row
            for row in rows
            if row.get("invocation_state") == "PLANNING_ADMITTED_TO_D6"
        ]
        return {
            "system": self.SYSTEM,
            "authority": self.AUTHORITY,
            "behavioral_authority": self.BEHAVIORAL_AUTHORITY,
            "invocation_trigger": "NATURAL_ARENA_TIE_REQUIRES_REVIEW_D3_NEED",
            "temporal_semantics": "SAME_RUN_PLANNING",
            "arena_selection_authority": "NONE",
            "execution_authority": "NONE",
            "evidence_acceptance_authority": "NONE",
            "causal_authority": "NONE",
            "source_independence_authority": "NONE",
            "qualification_authority": "NONE",
            "truth_authority": "NONE",
            "budget_authority": "NONE",
            "arena_selection_authority_changed": False,
            "execution_authority_changed": False,
            "evidence_acceptance_authority_changed": False,
            "causal_authority_changed": False,
            "source_independence_authority_changed": False,
            "qualification_authority_changed": False,
            "truth_authority_changed": False,
            "budget_authority_changed": False,
            "safe_winner_forced": False,
            "tie_resolved": False,
            "raw_evidence_created": False,
            "accepted_evidence_created": False,
            "candidate_disambiguation_need_count": len(needs),
            "planning_invocation_count": len(rows),
            "d6_plan_reached_count": len(reached),
            "created_or_reused_evidence_plan_ids": sorted(set(plan_ids)),
            "duplicate_semantic_work_count": sum(
                int((row.get("adapter_report") or {}).get("duplicate_semantic_work_count") or 0)
                for row in rows
            ),
            "synthetic_downstream_object_count": 0,
            "invocation_rows": rows,
        }

    def _invoke_need(
        self,
        need: Mapping[str, Any],
        *,
        arena_report: Mapping[str, Any],
        current_run_id: str | None,
    ) -> dict[str, Any]:
        need = dict(need or {})
        eligibility = self._eligibility(need, arena_report, current_run_id)
        if eligibility["eligibility_state"] != "ELIGIBLE_NATURAL_D3_NEED":
            return {
                **eligibility,
                "semantic_replay_state": "INVALID_OR_STALE_NEED",
                "invocation_state": "FAILED_CLOSED",
                "adapter_report": None,
            }

        replay_state = self._semantic_replay_state(need)
        if replay_state == "INVALID_OR_STALE_NEED":
            return {
                **eligibility,
                "semantic_replay_state": replay_state,
                "invocation_state": "FAILED_CLOSED",
                "failure_reasons": [
                    *eligibility.get("failure_reasons", []),
                    "semantic_identity_binding_changed",
                ],
                "adapter_report": None,
            }

        adapter_report = self.adapter.admit_need_to_plan(need)
        reached = adapter_report.get("planning_status") == "D6_EVIDENCE_PLAN_REACHED"
        return {
            **eligibility,
            "semantic_replay_state": replay_state,
            "invocation_state": (
                "PLANNING_ADMITTED_TO_D6" if reached else "ADAPTER_FAILED_CLOSED"
            ),
            "adapter_report": adapter_report,
            "d3_to_d4": bool(adapter_report.get("disambiguation_need_reachable")),
            "d4_to_d5": bool(adapter_report.get("validation_request_reachable")),
            "d5_to_d6": bool(adapter_report.get("evidence_plan_reachable")),
            "safe_winner_forced": False,
            "tie_resolved": False,
        }

    def _eligibility(
        self,
        need: Mapping[str, Any],
        arena_report: Mapping[str, Any],
        current_run_id: str | None,
    ) -> dict[str, Any]:
        failures: list[str] = []
        if arena_report.get("selection_state") != "TIE_REQUIRES_REVIEW":
            failures.append("arena_decision_not_tie_requires_review")
        disambiguation = self._disambiguation_report(arena_report)
        if not isinstance(disambiguation, Mapping):
            failures.append("missing_canonical_disagreement_report")
        elif disambiguation.get("disagreement_model_state") not in {
            "DISAGREEMENT_IDENTIFIED",
        }:
            failures.append("no_canonical_disagreement")

        required = {
            "disambiguation_need_id": "malformed_need_missing_identity",
            "candidate_set_id": "missing_candidate_set_identity",
            "disagreement_id": "missing_disagreement_identity",
            "arena_decision_id": "missing_arena_lineage",
            "missing_discriminating_evidence": "missing_evidence_requirement",
            "proposed_evidence_method": "missing_requested_method",
        }
        for field, failure in required.items():
            if self._missing(need.get(field)):
                failures.append(failure)

        candidate_ids = need.get("candidate_ids")
        if not isinstance(candidate_ids, list) or len(candidate_ids) < 2:
            failures.append("fewer_than_two_discriminating_candidates")
        expected = need.get("expected_candidate_predictions")
        if not self._predictions_differ(expected):
            failures.append("candidate_predictions_non_discriminating")
        if need.get("proposed_evidence_method") not in self.SUPPORTED_METHODS:
            failures.append("unsupported_disambiguation_method")
        if (
            not self._missing(need.get("missing_discriminating_evidence"))
            and need.get("missing_discriminating_evidence")
            not in self.SUPPORTED_EVIDENCE_REQUIREMENTS
        ):
            failures.append("unsupported_or_forged_evidence_requirement")

        binding = need.get("task_binding") if isinstance(need.get("task_binding"), Mapping) else {}
        need_run_id = need.get("arena_run_id") or binding.get("run_id")
        if self._missing(need_run_id):
            failures.append("missing_arena_run_lineage")
        elif current_run_id and str(need_run_id) != str(current_run_id):
            failures.append("stale_or_invalid_runtime_lineage")

        top_ids = {
            str(item)
            for item in (
                disambiguation.get("top_tied_candidate_ids", [])
                if isinstance(disambiguation, Mapping)
                else []
            )
        }
        if candidate_ids and top_ids and not set(map(str, candidate_ids)).issubset(top_ids):
            failures.append("candidate_identity_binding_failed")
        if (
            isinstance(disambiguation, Mapping)
            and not self._missing(disambiguation.get("candidate_set_id"))
            and need.get("candidate_set_id") != disambiguation.get("candidate_set_id")
        ):
            failures.append("candidate_set_identity_binding_failed")

        return {
            "eligibility_state": (
                "ELIGIBLE_NATURAL_D3_NEED" if not failures else "INELIGIBLE_D3_NEED"
            ),
            "disambiguation_need_id": need.get("disambiguation_need_id"),
            "candidate_set_id": need.get("candidate_set_id"),
            "disagreement_id": need.get("disagreement_id"),
            "arena_decision_id": need.get("arena_decision_id"),
            "requested_method": need.get("proposed_evidence_method"),
            "failure_reasons": sorted(set(failures)),
            "candidate_identity_binding": "PRESERVED" if "candidate_identity_binding_failed" not in failures else "FAILED",
            "candidate_set_identity_binding": "PRESERVED" if "candidate_set_identity_binding_failed" not in failures else "FAILED",
            "disagreement_identity_binding": "PRESERVED" if "missing_disagreement_identity" not in failures else "FAILED",
            "arena_lineage_binding": "PRESERVED" if "missing_arena_lineage" not in failures and "missing_arena_run_lineage" not in failures else "FAILED",
            "evidence_requirement_binding": "PRESERVED" if "missing_evidence_requirement" not in failures else "FAILED",
        }

    def _semantic_replay_state(self, need: Mapping[str, Any]) -> str:
        need_id = str(need.get("disambiguation_need_id") or "")
        disagreement_id = str(need.get("disagreement_id") or "")
        binding = self._binding_fingerprint(need)
        if need_id in self._bindings_by_need_id:
            if self._bindings_by_need_id[need_id] == binding:
                return "SAME_STATE_REPLAY"
            return "INVALID_OR_STALE_NEED"

        seen_for_disagreement = self._need_ids_by_disagreement.setdefault(
            disagreement_id,
            set(),
        )
        replay_state = (
            "UPDATED_DISAGREEMENT_STATE"
            if seen_for_disagreement and need_id not in seen_for_disagreement
            else "NEW_DISAMBIGUATION_NEED"
        )
        self._bindings_by_need_id[need_id] = binding
        seen_for_disagreement.add(need_id)
        return replay_state

    def _binding_fingerprint(self, need: Mapping[str, Any]) -> str:
        return self._fingerprint({
            "arena_decision_id": need.get("arena_decision_id"),
            "arena_run_id": need.get("arena_run_id"),
            "candidate_set_id": need.get("candidate_set_id"),
            "candidate_ids": sorted(str(item) for item in need.get("candidate_ids", []) or []),
            "disagreement_id": need.get("disagreement_id"),
            "evidence_requirement": need.get("missing_discriminating_evidence"),
            "method": need.get("proposed_evidence_method"),
            "expected_candidate_predictions": need.get("expected_candidate_predictions"),
        })

    def _extract_needs(self, arena_report: Mapping[str, Any]) -> list[dict[str, Any]]:
        disambiguation = self._disambiguation_report(arena_report)
        if not isinstance(disambiguation, Mapping):
            return []
        return [
            dict(item)
            for item in disambiguation.get("candidate_disambiguation_evidence_needs", []) or []
            if isinstance(item, Mapping)
        ]

    @staticmethod
    def _disambiguation_report(arena_report: Mapping[str, Any]) -> Mapping[str, Any] | None:
        diagnostics = arena_report.get("candidate_arena_diagnostics")
        if isinstance(diagnostics, Mapping) and isinstance(
            diagnostics.get("candidate_disambiguation_report"),
            Mapping,
        ):
            return diagnostics["candidate_disambiguation_report"]
        return None

    @staticmethod
    def _predictions_differ(predictions: Any) -> bool:
        if not isinstance(predictions, Mapping) or len(predictions) < 2:
            return False
        encoded = {
            json.dumps(value, sort_keys=True, default=str)
            for value in predictions.values()
        }
        return len(encoded) > 1

    @staticmethod
    def _missing(value: Any) -> bool:
        return str(value or "").strip() in UNKNOWN

    @staticmethod
    def _fingerprint(payload: Mapping[str, Any]) -> str:
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()


__all__ = ["CandidateDisambiguationProductionInvocationPolicy"]
