"""Report-building helpers for process contexts without registry-side coupling."""

from __future__ import annotations

from typing import Any, Mapping

from core.epistemic_models import clamp
from runtime.context.process_context_models import normalize_context_name


def context_from_registry_report(
    registry_report: Mapping[str, Any],
    concept: str | None = None,
    context_name: str | None = None,
) -> dict[str, Any]:
    registry_report = registry_report if isinstance(registry_report, Mapping) else {}
    contexts = registry_report.get("contexts", [])
    if not contexts:
        contexts = registry_report.get("registered_contexts", [])
    normalized_concept = normalize_context_name(concept)
    for context in contexts or []:
        if not isinstance(context, Mapping):
            continue
        if context_name and context.get("context_name") == context_name:
            return dict(context)
        if normalized_concept and context.get("concept") == normalized_concept:
            return dict(context)
    return {}


def process_report_from_registry_context(context: Mapping[str, Any]) -> dict[str, Any]:
    context = context if isinstance(context, Mapping) else {}
    transitions = list(context.get("transitions", []) or [])
    preconditions = list(context.get("preconditions", []) or [])
    outcomes = list(context.get("expected_outcomes", []) or [])
    strength = clamp(context.get("process_context_strength", 0.0))
    temporal_report = dict(context.get("temporal_process_context_report", {}) or {})
    return {
        **temporal_report,
        "system": "process_context_registry",
        "concept": context.get("concept"),
        "context_name": context.get("context_name"),
        "process_context": context.get("context_name"),
        "generated_context": context.get("context_name"),
        "source_strategy": context.get("source_strategy"),
        "preconditions": preconditions,
        "initial_state": preconditions,
        "transitions": transitions,
        "transition_steps": [
            {
                "source": item.get("from"),
                "relation": item.get("transition", "transitions_to"),
                "target": item.get("to"),
                "confidence": item.get("confidence", 0.0),
            }
            for item in transitions
            if isinstance(item, Mapping)
        ],
        "postconditions": outcomes,
        "final_state": outcomes,
        "expected_outcomes": outcomes,
        "context_confidence": context.get("context_confidence", strength),
        "confidence": context.get("context_confidence", strength),
        "process_context_strength": strength,
        "temporal_consistency": context.get("temporal_consistency", 0.0),
        "process_context_generated": True,
        "process_context_ready": strength > 0.90,
        "status": context.get("status", "PROCESS_CONTEXT_SUPPORTED"),
        "supporting_math_evidence": {
            **temporal_report.get("supporting_math_evidence", {}),
            "typed_dependencies_generated": True,
            "process_context_registry_consolidated": True,
            "process_signature_generated": True,
            "process_signature_match": True,
            "process_signature_strength": strength,
            "transition_sequence_generated": bool(transitions),
            "preconditions_identified": bool(preconditions),
            "postconditions_identified": bool(outcomes),
            "temporal_state_sequence_generated": bool(preconditions and transitions and outcomes),
            "final_state_identified": bool(outcomes),
            "dependency_semantics_score": strength,
            "identity_scope_leakage_detected": False,
        },
    }


__all__ = ["context_from_registry_report", "process_report_from_registry_context"]
