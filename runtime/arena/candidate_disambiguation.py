"""Observation-only candidate disambiguation evidence modelling."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from itertools import combinations
from typing import Any, Mapping


class CandidateDisambiguationEvidenceLayer:
    """Describe tied candidate disagreements without changing Arena authority."""

    system_name = "candidate_disambiguation_evidence_layer"
    AUTHORITY = "OBSERVATION_REQUEST_ONLY"
    BEHAVIORAL_AUTHORITY = "NONE"

    def analyze(
        self,
        candidates: list[Mapping[str, Any]] | None,
        scores: list[Mapping[str, Any]] | None,
        simulations: Mapping[str, Mapping[str, Any]] | None,
        selection: Mapping[str, Any] | None,
        runtime_context: Mapping[str, Any] | None = None,
        task_signature: str | None = None,
    ) -> dict[str, Any]:
        candidates = [dict(item) for item in candidates or [] if isinstance(item, Mapping)]
        scores = [dict(item) for item in scores or [] if isinstance(item, Mapping)]
        simulations = simulations if isinstance(simulations, Mapping) else {}
        selection = selection if isinstance(selection, Mapping) else {}
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        score_by_id = {
            str(item.get("candidate_id")): item
            for item in scores
            if item.get("candidate_id")
        }
        eligible_ids = {
            str(item.get("candidate_id"))
            for item in scores
            if item.get("candidate_id") and item.get("eligible_for_selection")
        }
        eligible = [
            candidate
            for candidate in candidates
            if str(candidate.get("candidate_id")) in eligible_ids
        ]
        top_ids = self._top_tie_ids(eligible, score_by_id, selection)
        candidate_identities = [
            self._candidate_identity(candidate, runtime_context, task_signature)
            for candidate in candidates
        ]
        candidate_set_id = self._candidate_set_id(candidate_identities)
        pair_reports = []
        for left_id, right_id in combinations(top_ids, 2):
            left = self._candidate_by_id(eligible, left_id)
            right = self._candidate_by_id(eligible, right_id)
            if not left or not right:
                continue
            pair_reports.append(
                self._pair_disagreement(
                    left,
                    right,
                    simulations,
                    score_by_id,
                    runtime_context,
                    task_signature,
                    candidate_set_id,
                )
            )
        evidence_needs = [
            pair["candidate_disambiguation_evidence_need"]
            for pair in pair_reports
            if pair.get("candidate_disambiguation_evidence_need")
        ]
        state = "NOT_APPLICABLE"
        if selection.get("selection_state") == "TIE_REQUIRES_REVIEW":
            state = "DISAGREEMENT_IDENTIFIED" if pair_reports else "TIE_WITHOUT_PAIRWISE_DISAGREEMENT"
        return {
            "system": self.system_name,
            "authority": self.AUTHORITY,
            "behavioral_authority": self.BEHAVIORAL_AUTHORITY,
            "selection_state": selection.get("selection_state"),
            "candidate_set_id": candidate_set_id,
            "candidate_identity_contract_state": "CANONICAL_OBSERVATION_IDENTITY_DEFINED",
            "candidate_identity_fields": [
                "candidate_id",
                "candidate_fingerprint",
                "semantic_identity",
                "program_identity",
                "source_lineage_identity",
                "task_binding",
                "generation_lineage",
            ],
            "source_lineage_state": "PRESERVED_IF_PRESENT",
            "disagreement_model_state": state,
            "tie_disambiguation_applicable": selection.get("selection_state") == "TIE_REQUIRES_REVIEW",
            "top_tied_candidate_ids": top_ids,
            "candidate_identities": candidate_identities,
            "candidate_pair_disagreements": pair_reports,
            "candidate_disambiguation_evidence_needs": evidence_needs,
            "disambiguation_need_count": len(evidence_needs),
            "evidence_contract_state": (
                "CANDIDATE_DISAMBIGUATION_EVIDENCE_NEED_EMITTED"
                if evidence_needs
                else "NO_DISAMBIGUATION_EVIDENCE_NEED"
            ),
            "evidence_effect_authority": "NONE",
            "score_authority": "NONE",
            "ranking_authority": "NONE",
            "execution_authority": "NONE",
            "truth_authority": "NONE",
            "safe_winner_authority": "NONE",
            "resolution_state": (
                "TIE_REMAINS_INSUFFICIENT_EVIDENCE"
                if evidence_needs
                else "DISAMBIGUATION_NOT_APPLICABLE"
            ),
            "recommended_next_consumer": (
                "EVIDENCE_NEED_TO_GOVERNED_VALIDATION_PLANNING_ADAPTER"
                if evidence_needs
                else "NONE"
            ),
        }

    def _top_tie_ids(
        self,
        eligible: list[Mapping[str, Any]],
        score_by_id: Mapping[str, Mapping[str, Any]],
        selection: Mapping[str, Any],
    ) -> list[str]:
        if selection.get("selection_state") != "TIE_REQUIRES_REVIEW":
            return []
        ids = []
        for item in (
            selection.get("winner_candidate"),
            selection.get("second_best_candidate"),
        ):
            if isinstance(item, Mapping) and item.get("candidate_id"):
                ids.append(str(item.get("candidate_id")))
        if len(ids) >= 2:
            return sorted(set(ids))
        if not eligible:
            return []
        ranked = sorted(
            eligible,
            key=lambda candidate: float(
                score_by_id.get(str(candidate.get("candidate_id")), {}).get("final_score")
                or 0.0
            ),
            reverse=True,
        )
        top_score = float(
            score_by_id.get(str(ranked[0].get("candidate_id")), {}).get("final_score")
            or 0.0
        )
        return sorted(
            str(candidate.get("candidate_id"))
            for candidate in ranked
            if abs(
                top_score
                - float(
                    score_by_id.get(str(candidate.get("candidate_id")), {}).get(
                        "final_score"
                    )
                    or 0.0
                )
            )
            < 0.02
        )

    def _candidate_identity(
        self,
        candidate: Mapping[str, Any],
        runtime_context: Mapping[str, Any],
        task_signature: str | None,
    ) -> dict[str, Any]:
        payload = {
            "candidate_id": candidate.get("candidate_id"),
            "semantic_identity": {
                "operation": candidate.get("operation"),
                "intent": candidate.get("intent"),
            },
            "program_identity": {
                "program_signature": candidate.get("program_signature"),
                "program": candidate.get("program"),
            },
            "source_lineage_identity": {
                "source": candidate.get("source"),
                "sources": candidate.get("sources", []),
                "origin_source": candidate.get("origin_source"),
                "origin_sources": candidate.get("origin_sources", []),
                "normalized_source": candidate.get("normalized_source"),
                "normalized_sources": candidate.get("normalized_sources", []),
                "provenance_history": candidate.get("provenance_history", []),
            },
            "task_binding": {
                "task_signature": task_signature,
                "task_id": runtime_context.get("task_id"),
                "run_id": runtime_context.get("run_id"),
            },
            "generation_lineage": {
                "source_run_id": candidate.get("source_run_id"),
                "target_run_id": candidate.get("target_run_id"),
                "learned_object_id": candidate.get("learned_object_id"),
                "reuse_proposal_id": candidate.get("reuse_proposal_id"),
            },
        }
        return {
            **payload,
            "candidate_fingerprint": self._fingerprint(payload),
        }

    def _candidate_set_id(self, identities: list[Mapping[str, Any]]) -> str:
        fingerprints = sorted(str(item.get("candidate_fingerprint")) for item in identities)
        return "candidate_set:" + self._fingerprint({"candidate_fingerprints": fingerprints})[:16]

    def _pair_disagreement(
        self,
        left: Mapping[str, Any],
        right: Mapping[str, Any],
        simulations: Mapping[str, Mapping[str, Any]],
        score_by_id: Mapping[str, Mapping[str, Any]],
        runtime_context: Mapping[str, Any],
        task_signature: str | None,
        candidate_set_id: str,
    ) -> dict[str, Any]:
        left_id = str(left.get("candidate_id"))
        right_id = str(right.get("candidate_id"))
        left_sim = simulations.get(left_id, {}) if isinstance(simulations.get(left_id), Mapping) else {}
        right_sim = simulations.get(right_id, {}) if isinstance(simulations.get(right_id), Mapping) else {}
        left_prediction = left_sim.get("predicted_output")
        right_prediction = right_sim.get("predicted_output")
        disagreements = []
        if left_prediction != right_prediction:
            disagreements.append("PREDICTION_DISAGREEMENT")
        if left.get("program_signature") != right.get("program_signature"):
            disagreements.append("STRUCTURAL_DISAGREEMENT")
        if left.get("operation") != right.get("operation"):
            disagreements.append("SEMANTIC_DISAGREEMENT")
        if self._sources(left) != self._sources(right):
            disagreements.append("SOURCE_SUPPORT_DISAGREEMENT")
        if not disagreements:
            disagreements.append("OBSERVATIONALLY_EQUIVALENT")
        disagreement_type = self._primary_disagreement(disagreements)
        candidate_pair = [left_id, right_id]
        expected_predictions = {
            left_id: deepcopy(left_prediction),
            right_id: deepcopy(right_prediction),
        }
        need_payload = {
            "candidate_set_id": candidate_set_id,
            "candidate_ids": candidate_pair,
            "task_binding": {
                "task_signature": task_signature,
                "task_id": runtime_context.get("task_id"),
                "run_id": runtime_context.get("run_id"),
            },
            "disagreement_type": disagreement_type,
            "expected_candidate_predictions": expected_predictions,
        }
        need_id = "candidate_disambiguation_need:" + self._fingerprint(need_payload)[:16]
        disagreement_id = "candidate_disagreement:" + self._fingerprint(
            {
                "candidate_set_id": candidate_set_id,
                "candidate_pair": candidate_pair,
                "disagreement_type": disagreement_type,
                "disagreement_types": disagreements,
            }
        )[:16]
        need = {
            "disambiguation_need_id": need_id,
            "arena_decision_id": f"arena_decision:{candidate_set_id}",
            "arena_run_id": runtime_context.get("run_id"),
            "candidate_set_id": candidate_set_id,
            "candidate_ids": candidate_pair,
            "candidate_pair": candidate_pair,
            "task_binding": need_payload["task_binding"],
            "disagreement_id": disagreement_id,
            "disagreement_type": disagreement_type,
            "disagreement_types": disagreements,
            "current_evidence": {
                left_id: {
                    "score": score_by_id.get(left_id, {}).get("final_score"),
                    "simulation_success": left_sim.get("simulation_success"),
                    "prediction_accuracy": left_sim.get("prediction_accuracy"),
                },
                right_id: {
                    "score": score_by_id.get(right_id, {}).get("final_score"),
                    "simulation_success": right_sim.get("simulation_success"),
                    "prediction_accuracy": right_sim.get("prediction_accuracy"),
                },
            },
            "missing_discriminating_evidence": self._missing_evidence(disagreement_type),
            "proposed_evidence_method": self._method(disagreement_type),
            "expected_candidate_predictions": expected_predictions,
            "authority_state": self.AUTHORITY,
            "behavioral_authority": self.BEHAVIORAL_AUTHORITY,
            "source_requirements": "PRESERVE_REAL_SOURCE_INDEPENDENCE_WHEN_USED",
            "counterfactual_requirement": (
                "REQUIRED_IF_DISPUTED_CONDITION_CAN_BE_ISOLATED"
                if disagreement_type in {"CAUSAL_DISAGREEMENT", "STRUCTURAL_DISAGREEMENT"}
                else "NOT_REQUIRED_BY_DEFAULT"
            ),
            "causal_requirement": (
                "REQUIRED_ONLY_FOR_CAUSAL_DISAGREEMENT"
                if disagreement_type == "CAUSAL_DISAGREEMENT"
                else "NOT_CAUSAL_AUTHORITY"
            ),
            "resolution_state": "UNRESOLVED_REQUEST_ONLY",
        }
        return {
            "candidate_pair": candidate_pair,
            "disagreement_type": disagreement_type,
            "disagreement_types": disagreements,
            "evidence_relations": {
                left_id: "INSUFFICIENT",
                right_id: "INSUFFICIENT",
            },
            "candidate_disambiguation_evidence_need": need,
        }

    def _primary_disagreement(self, disagreements: list[str]) -> str:
        for item in (
            "PREDICTION_DISAGREEMENT",
            "CAUSAL_DISAGREEMENT",
            "SEMANTIC_DISAGREEMENT",
            "STRUCTURAL_DISAGREEMENT",
            "SOURCE_SUPPORT_DISAGREEMENT",
            "OBSERVATIONALLY_EQUIVALENT",
        ):
            if item in disagreements:
                return item
        return "UNKNOWN_DISAGREEMENT"

    def _missing_evidence(self, disagreement_type: str) -> str:
        return {
            "PREDICTION_DISAGREEMENT": "VALID_OBSERVATION_FOR_WHICH_TIED_CANDIDATES_PREDICT_DIFFERENT_OUTPUTS",
            "SEMANTIC_DISAGREEMENT": "VALID_CONTEXT_THAT_EXERCISES_THE_DIFFERENT_CANDIDATE_OPERATION_SEMANTICS",
            "STRUCTURAL_DISAGREEMENT": "VALID_CONTEXT_THAT_EXERCISES_THE_DIFFERENT_PROGRAM_STRUCTURE",
            "SOURCE_SUPPORT_DISAGREEMENT": "REAL_INDEPENDENT_SOURCE_OR_VALIDATION_EVIDENCE_BOUND_TO_CANDIDATE_IDENTITY",
            "OBSERVATIONALLY_EQUIVALENT": "NO_CURRENT_MINIMUM_DISCRIMINATING_OBSERVATION_IDENTIFIED",
        }.get(disagreement_type, "MISSING_DISCRIMINATING_EVIDENCE_NOT_CLASSIFIED")

    def _method(self, disagreement_type: str) -> str:
        return {
            "PREDICTION_DISAGREEMENT": "DISCRIMINATIVE_VALIDATION",
            "SEMANTIC_DISAGREEMENT": "DISCRIMINATIVE_VALIDATION",
            "STRUCTURAL_DISAGREEMENT": "COUNTERFACTUAL_DISAMBIGUATION",
            "SOURCE_SUPPORT_DISAGREEMENT": "CROSS_SOURCE_CORROBORATION",
            "OBSERVATIONALLY_EQUIVALENT": "FUTURE_RESEARCH_HYPOTHESIS",
        }.get(disagreement_type, "GOVERNED_REVIEW")

    def _candidate_by_id(
        self,
        candidates: list[Mapping[str, Any]],
        candidate_id: str,
    ) -> Mapping[str, Any] | None:
        return next(
            (candidate for candidate in candidates if str(candidate.get("candidate_id")) == candidate_id),
            None,
        )

    def _sources(self, candidate: Mapping[str, Any]) -> list[str]:
        return sorted(str(item) for item in candidate.get("sources", []) if item)

    def _fingerprint(self, payload: Mapping[str, Any]) -> str:
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()


candidate_disambiguation_evidence_layer = CandidateDisambiguationEvidenceLayer()

__all__ = [
    "CandidateDisambiguationEvidenceLayer",
    "candidate_disambiguation_evidence_layer",
]
