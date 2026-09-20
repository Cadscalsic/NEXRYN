from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from runtime.capability_intelligence.integrated_capability_qualification import (
    capability_id_for_subject,
)


AUTHORITY = {
    "identity_authority": "IDENTITY_ONLY",
    "behavioral_authority": "NONE",
    "qualification_authority": "NONE",
    "evidence_acceptance_authority": "NONE",
    "source_independence_authority": "NONE",
    "truth_authority": "NONE",
    "budget_authority": "NONE",
    "execution_authority": "NONE",
}

CONTEXT_QUALIFIER_KEYS = {
    "validation_context",
    "context_id",
    "task_context",
    "validation_scenario",
}


def _token(value: Any) -> str:
    return str(value or "UNKNOWN")


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return f"{prefix}_{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def intrinsic_capability_payload(subject: Mapping[str, Any]) -> dict[str, Any]:
    item = subject if isinstance(subject, Mapping) else {}
    qualifiers = item.get("qualifiers")
    qualifiers = qualifiers if isinstance(qualifiers, Mapping) else {}
    intrinsic_qualifiers = {
        str(key): qualifiers[key]
        for key in sorted(qualifiers)
        if str(key) not in CONTEXT_QUALIFIER_KEYS
    }
    return {
        "schema_version": "capability_identity.v2",
        "capability_name": _token(item.get("capability_name")),
        "domain": _token(item.get("domain", "UNKNOWN")),
        "intrinsic_qualifiers": intrinsic_qualifiers,
    }


def capability_operation_payload(subject: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "capability_operation_identity.v2",
        "canonical_capability_id": canonical_capability_id_v2(subject),
        "operation": _token(subject.get("operation") if isinstance(subject, Mapping) else None),
    }


def canonical_capability_id_v2(subject: Mapping[str, Any]) -> str:
    return _stable_id("capability_v2", intrinsic_capability_payload(subject))


def capability_operation_id_v2(subject: Mapping[str, Any]) -> str:
    return _stable_id("capability_operation_v2", capability_operation_payload(subject))


def validation_context_payload(
    *,
    subject: Mapping[str, Any],
    qualification_claim_id: str,
    context: Mapping[str, Any],
) -> dict[str, Any]:
    context_item = context if isinstance(context, Mapping) else {}
    return {
        "schema_version": "validation_context_identity.v1",
        "canonical_capability_id": canonical_capability_id_v2(subject),
        "capability_operation_id": capability_operation_id_v2(subject),
        "operation": _token(subject.get("operation") if isinstance(subject, Mapping) else None),
        "qualification_claim_id": _token(qualification_claim_id),
        "context_type": _token(context_item.get("context_type", "VALIDATION_SCENARIO")),
        "context_parameters": context_item.get("context_parameters", {}),
        "structural_signature": context_item.get("structural_signature"),
        "causal_intervention_signature": context_item.get(
            "causal_intervention_signature"
        ),
        "counterfactual_contract": context_item.get("counterfactual_contract"),
    }


def validation_context_id(
    *,
    subject: Mapping[str, Any],
    qualification_claim_id: str,
    context: Mapping[str, Any],
) -> str:
    return _stable_id(
        "validation_context",
        validation_context_payload(
            subject=subject,
            qualification_claim_id=qualification_claim_id,
            context=context,
        ),
    )


def classify_context_diversity(
    *,
    baseline_context: Mapping[str, Any],
    candidate_context: Mapping[str, Any],
) -> dict[str, Any]:
    baseline = baseline_context if isinstance(baseline_context, Mapping) else {}
    candidate = candidate_context if isinstance(candidate_context, Mapping) else {}
    compared_fields = (
        "structural_signature",
        "causal_intervention_signature",
        "counterfactual_contract",
    )
    changed = [
        field
        for field in compared_fields
        if baseline.get(field) != candidate.get(field)
    ]
    if not changed:
        state = "SAME_CONTEXT_REPLAY"
    elif changed == ["structural_signature"]:
        state = "STRUCTURAL_VARIATION"
    elif "causal_intervention_signature" in changed or (
        "counterfactual_contract" in changed
    ):
        state = "DISTINCT_CAUSAL_CONTEXT"
    else:
        state = "COSMETIC_VARIATION"
    return {
        "context_diversity_state": state,
        "changed_semantic_dimensions": changed,
        "counts_for_c5_context_diversity": state
        in {"STRUCTURAL_VARIATION", "DISTINCT_CAUSAL_CONTEXT"},
        **AUTHORITY,
    }


def legacy_identity_mapping(
    subject: Mapping[str, Any],
    *,
    qualification_claim_id: str,
    validation_context: Mapping[str, Any],
) -> dict[str, Any]:
    legacy_capability_id = capability_id_for_subject(subject)
    canonical_id = canonical_capability_id_v2(subject)
    operation_id = capability_operation_id_v2(subject)
    context_id = validation_context_id(
        subject=subject,
        qualification_claim_id=qualification_claim_id,
        context=validation_context,
    )
    return {
        "schema_version": "legacy_identity_mapping.v1",
        "mapping_version": "capability_identity_v1_to_v2_context_separation",
        "legacy_capability_id": legacy_capability_id,
        "canonical_capability_id_v2": canonical_id,
        "capability_operation_id_v2": operation_id,
        "validation_context_id": context_id,
        "qualification_claim_id": qualification_claim_id,
        "historical_artifact_mutation_required": False,
        "mapping_reason": (
            "legacy capability identity includes validation context in qualifiers; "
            "v2 separates intrinsic capability identity, operation identity, and "
            "validation context identity"
        ),
        **AUTHORITY,
    }


__all__ = [
    "AUTHORITY",
    "CONTEXT_QUALIFIER_KEYS",
    "canonical_capability_id_v2",
    "capability_operation_id_v2",
    "classify_context_diversity",
    "intrinsic_capability_payload",
    "legacy_identity_mapping",
    "validation_context_id",
    "validation_context_payload",
]
