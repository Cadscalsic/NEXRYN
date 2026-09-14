from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


class CausalValidationEvidenceEvaluator:
    """Classify sandbox causal operation-effect results without qualification authority."""

    AUTHORITY = "CAUSAL_VALIDATION_EVIDENCE_EVALUATOR"
    METHOD = "CONTROLLED_TRANSFORMATION_EFFECT"
    DEFAULT_MIN_EFFECT = 1.0

    def evaluate(
        self,
        raw_result: Mapping[str, Any],
        *,
        minimum_effect: float | None = None,
    ) -> dict[str, Any]:
        raw = raw_result if isinstance(raw_result, Mapping) else {}
        causal = raw.get("causal_validation_result")
        causal = causal if isinstance(causal, Mapping) else {}
        min_effect = (
            float(minimum_effect)
            if minimum_effect is not None
            else float(causal.get("minimum_effect", self.DEFAULT_MIN_EFFECT) or 0.0)
        )
        failures = self._contract_failures(raw, causal)
        treatment_score = float(causal.get("treatment_score", 0.0) or 0.0)
        control_score = float(causal.get("control_score", 0.0) or 0.0)
        effect = round(treatment_score - control_score, 6)
        positive_effect = effect >= min_effect and effect > 0.0
        state = (
            "CAUSALLY_SUPPORTED"
            if not failures and positive_effect
            else "CAUSAL_SUPPORT_NOT_ESTABLISHED"
        )
        payload = {
            "schema_version": "1.0",
            "system": "causal_validation_evidence_evaluator",
            "causal_evidence_authority": self.AUTHORITY,
            "behavioral_authority": "NONE",
            "qualification_authority": "NONE",
            "truth_authority": "NONE",
            "budget_authority": "NONE",
            "method": causal.get("method") or self.METHOD,
            "capability_id": raw.get("capability_id"),
            "capability_identity_schema": raw.get("capability_identity_schema")
            or causal.get("capability_identity_schema"),
            "capability_id_v2": raw.get("capability_id_v2")
            or causal.get("capability_id_v2"),
            "capability_operation_id_v2": raw.get("capability_operation_id_v2")
            or causal.get("capability_operation_id_v2"),
            "validation_context_identity_schema": raw.get(
                "validation_context_identity_schema"
            )
            or causal.get("validation_context_identity_schema"),
            "validation_context_id": raw.get("validation_context_id")
            or causal.get("validation_context_id"),
            "operation": causal.get("operation") or raw.get("target_operation"),
            "qualification_claim_id": (
                causal.get("qualification_claim_id") or raw.get("claim_id")
            ),
            "validation_request_id": raw.get("source_run_id") or raw.get("run_id"),
            "evidence_plan_id": raw.get("plan_id"),
            "validation_execution_id": raw.get("execution_id"),
            "validation_attempt_id": raw.get("validation_attempt_id"),
            "treatment_execution_id": causal.get("treatment_execution_id"),
            "counterfactual_id": causal.get("counterfactual_id"),
            "target_operation_executed": bool(causal.get("operation_executed")),
            "target_operation_output_consumed": bool(
                causal.get("operation_output_consumed")
            ),
            "counterfactual_state": (
                "COUNTERFACTUAL_VALID"
                if causal.get("counterfactual_valid") is True
                else "COUNTERFACTUAL_INVALID"
            ),
            "treatment_outcome": causal.get("treatment_outcome"),
            "control_outcome": causal.get("control_outcome"),
            "treatment_score": treatment_score,
            "control_score": control_score,
            "minimum_effect": min_effect,
            "causal_effect": effect,
            "causal_support_state": state,
            "capability_causal_support_state": state,
            "causal_support_contract_failures": failures,
            "causal_support_reason": (
                "target_operation_materially_caused_outcome"
                if state == "CAUSALLY_SUPPORTED"
                else failures[0]
                if failures
                else "effect_below_minimum"
            ),
            "source_provenance": raw.get("source_provenance"),
        }
        payload["causal_evidence_id"] = self._stable_id("causal_evidence", payload)
        payload["causal_evidence_fingerprint"] = self._fingerprint(payload)
        return payload

    def _contract_failures(
        self,
        raw: Mapping[str, Any],
        causal: Mapping[str, Any],
    ) -> list[str]:
        failures: list[str] = []
        if not causal:
            failures.append("missing_causal_validation_result")
        if not raw.get("capability_id"):
            failures.append("missing_capability_id")
        if "operation" in causal and causal.get("operation") in (None, ""):
            failures.append("missing_operation")
        elif not (causal.get("operation") or raw.get("target_operation")):
            failures.append("missing_operation")
        if "qualification_claim_id" in causal and causal.get(
            "qualification_claim_id"
        ) in (None, ""):
            failures.append("missing_qualification_claim_id")
        elif not (causal.get("qualification_claim_id") or raw.get("claim_id")):
            failures.append("missing_qualification_claim_id")
        if causal.get("operation_executed") is not True:
            failures.append("target_operation_not_executed")
        if causal.get("operation_output_consumed") is not True:
            failures.append("target_operation_output_not_consumed")
        if causal.get("counterfactual_valid") is not True:
            failures.append("invalid_counterfactual")
        if causal.get("same_input") is not True:
            failures.append("counterfactual_input_mismatch")
        if causal.get("same_non_target_operations") is not True:
            failures.append("counterfactual_non_target_operations_mismatch")
        if causal.get("unrelated_control") is True:
            failures.append("unrelated_control_candidate")
        return sorted(set(failures))

    def _stable_id(self, prefix: str, payload: Mapping[str, Any]) -> str:
        return f"{prefix}_{self._fingerprint(payload)[:12]}"

    def _fingerprint(self, payload: Mapping[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=True)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


__all__ = ["CausalValidationEvidenceEvaluator"]
