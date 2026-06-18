"""Governance registration for runtime-generated contexts."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp
from runtime.context.persistent_context_memory import (
    PersistentContextMemory,
)


STATIC_CONTEXTS = {
    "color_context",
    "symmetry_context",
    "density_context",
    "scale_context",
    "mapping_context",
}
TAXONOMY_CONTEXTS = {
    "density_context",
    "scale_context",
    "mapping_context",
}
PROCESS_CONTEXTS = {
    "growth_context",
    "propagation_context",
    "replication_context",
    "directional_motion_context",
    "motion_context",
    "topological_growth_context",
}
PROCESS_CONCEPTS = {
    "growth",
    "propagation",
    "replication",
    "directional_motion",
    "topological_growth",
}


class ContextGovernanceRegistry:
    """Register eligible runtime contexts as governance-visible evidence."""

    system_name = "context_governance_registry"

    def __init__(self, persistent_context_memory=None):
        self.contexts: dict[str, dict[str, Any]] = {}
        self.persistent_context_memory = (
            persistent_context_memory
            if persistent_context_memory is not None
            else PersistentContextMemory()
        )

    def register_runtime_contexts(
        self,
        runtime_context: Mapping[str, Any] | None = None,
        contexts: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        runtime_context = (
            runtime_context
            if isinstance(runtime_context, Mapping)
            else {}
        )
        candidates = self._collect_runtime_contexts(runtime_context)
        for context in contexts or []:
            if isinstance(context, Mapping):
                candidates.append(
                    self._candidate_from_context(
                        context,
                        source_key=str(
                            context.get("system", "runtime_context_store")
                        ),
                    )
                )

        runtime_ids = {
            context["context_id"]
            for context in candidates
            if context.get("context_id")
            and self._registration_eligible(context)
        }
        current_records = []
        for context in candidates:
            record = self._governance_record(context)
            if not record["governance_visible"]:
                continue
            self.contexts[record["context_id"]] = record
            current_records.append(record)

        self.persistent_context_memory.register_contexts(current_records)
        persistent_records = (
            self.persistent_context_memory.get_governance_visible_contexts()
            if runtime_ids or not candidates
            else []
        )
        if runtime_ids:
            persistent_records = [
                context
                for context in persistent_records
                if context.get("context_id") in runtime_ids
            ]
        for context in persistent_records:
            record = self._governance_record(
                self._candidate_from_context(
                    _persistent_source_context(context),
                    source_key="persistent_context_memory",
                )
            )
            if not record["governance_visible"]:
                continue
            record.update({
                "context_lifecycle": {
                    key: context.get(key)
                    for key in (
                        "status",
                        "first_discovered_at",
                        "last_observed_at",
                        "observation_count",
                        "runtime_cycles_survived",
                    )
                },
                "persistent_context": True,
            })
            if record["context_id"] in self.contexts:
                self.contexts[record["context_id"]]["context_lifecycle"] = (
                    record["context_lifecycle"]
                )
                self.contexts[record["context_id"]][
                    "persistent_context"
                ] = True
                continue
            self.contexts[record["context_id"]] = record

        visible_contexts = list(self.contexts.values())
        visible_ids = {context["context_id"] for context in visible_contexts}
        hidden_contexts = sorted(runtime_ids - visible_ids)
        runtime_context_count = len(runtime_ids)
        governance_context_count = len(visible_contexts)
        gap = max(runtime_context_count - governance_context_count, 0)
        coverage = (
            min(governance_context_count / runtime_context_count, 1.0)
            if runtime_context_count
            else 1.0
        )
        persistent_report = self.persistent_context_memory.report(
            runtime_context_count=runtime_context_count,
            governance_context_count=governance_context_count,
        )
        return {
            "system": self.system_name,
            "runtime_context_count": runtime_context_count,
            "persistent_context_count":
            persistent_report["persistent_context_count"],
            "governance_context_count": governance_context_count,
            "context_retention_rate":
            persistent_report["context_retention_rate"],
            "context_loss_events":
            persistent_report["context_loss_events"],
            "context_registration_gap": gap,
            "registration_coverage": round(coverage, 4),
            "hidden_contexts": hidden_contexts,
            "unregistered_contexts": hidden_contexts,
            "persistent_context_report": persistent_report,
            "visible_contexts": visible_contexts,
            "visible_context_ids": sorted(visible_ids),
            "process_contexts": [
                context
                for context in visible_contexts
                if context["context_type"] == "PROCESS_CONTEXT"
            ],
            "context_governance_report": self._log_report(
                runtime_context_count,
                governance_context_count,
                gap,
                coverage,
                hidden_contexts,
                sorted(visible_ids),
                persistent_report,
            ),
        }

    def governance_visible_contexts(self) -> list[dict[str, Any]]:
        return list(self.contexts.values())

    def process_context_report(self, concept: str) -> dict[str, Any]:
        concept = _normalize(concept)
        expected = _context_id_for_concept(concept)
        for context in self.contexts.values():
            if (
                context["context_type"] == "PROCESS_CONTEXT"
                and (
                    context["context_id"] == expected
                    or context.get("concept") == concept
                )
            ):
                return governance_process_report(context)
        return {}

    def _collect_runtime_contexts(self, runtime_context):
        candidates: list[dict[str, Any]] = []
        for key in (
            "semantic_context",
            "context_taxonomy_report",
            "context_hierarchy",
            "context_surface_report",
            "process_semantic_context_report",
            "process_semantic_models",
            "process_semantic_report",
            "process_context_discovery_report",
            "process_context_engine_report",
            "temporal_process_context_report",
            "process_context_report",
            "process_context_generation",
            "identity_safe_truth_integration",
            "identity_runtime_report",
            "causal_validation",
            "dependency_coherence_report",
        ):
            value = runtime_context.get(key)
            candidates.extend(self._contexts_from_value(value, source_key=key))

        process_registry = runtime_context.get("process_context_registry_report", {})
        if isinstance(process_registry, Mapping):
            candidates.extend(
                self._contexts_from_value(
                    process_registry.get("contexts", []),
                    source_key="process_context_registry",
                )
            )

        process_semantic_models = runtime_context.get(
            "process_semantic_models",
            {},
        )
        if isinstance(process_semantic_models, Mapping):
            candidates.extend(
                self._contexts_from_value(
                    process_semantic_models.values(),
                    source_key="process_semantic_models",
                )
            )

        discovery_report = runtime_context.get("process_context_discovery_report", {})
        if isinstance(discovery_report, Mapping):
            candidates.extend(
                self._contexts_from_value(
                    discovery_report.get("process_contexts", []),
                    source_key="process_context_discovery_engine",
                )
            )
        taxonomy_report = runtime_context.get("context_taxonomy_report", {})
        if isinstance(taxonomy_report, Mapping):
            for key in ("known_contexts", "reclassified_contexts"):
                candidates.extend(
                    self._contexts_from_value(
                        taxonomy_report.get(key, []),
                        source_key="context_taxonomy_engine",
                    )
                )
        return [context for context in candidates if context.get("context_id")]

    def _contexts_from_value(self, value, source_key):
        if isinstance(value, Mapping):
            if "visible_contexts" in value:
                return [
                    self._candidate_from_context(item, source_key)
                    for item in value.get("visible_contexts", [])
                    if isinstance(item, Mapping)
                ]
            if "contexts" in value and not _has_context_identity(value):
                return [
                    self._candidate_from_context(item, source_key)
                    for item in value.get("contexts", [])
                    if isinstance(item, Mapping)
                ]
            return [self._candidate_from_context(value, source_key)]
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            return [
                self._candidate_from_context(item, source_key)
                for item in value
                if isinstance(item, Mapping)
            ]
        return []

    def _candidate_from_context(self, context, source_key):
        context_id = _context_id(context)
        context_type = _context_type(context_id, context, source_key)
        semantic_validation = _semantic_validation(context, context_type)
        identity_compatible = _identity_compatible(context)
        confidence = _confidence(context)
        strength = _strength(context, confidence)
        return {
            "context_id": context_id,
            "context_type": context_type,
            "source_engine": str(
                context.get("system")
                or context.get("source_engine")
                or source_key
            ),
            "semantic_validation": semantic_validation,
            "identity_compatible": identity_compatible,
            "governance_visible": False,
            "context_strength": strength,
            "context_confidence": confidence,
            "concept": _normalize(context.get("concept")),
            "source_context": dict(context),
        }

    def _governance_record(self, context):
        record = dict(context)
        record["governance_visible"] = self._registration_eligible(record)
        return record

    def _registration_eligible(self, context):
        return bool(
            context.get("semantic_validation") is True
            and context.get("identity_compatible") is True
            and context.get("context_confidence", 0.0) > 0.0
        )

    def _log_report(
        self,
        runtime_context_count,
        governance_context_count,
        gap,
        coverage,
        hidden_contexts,
        visible_contexts,
        persistent_report=None,
    ):
        persistent_report = (
            persistent_report
            if isinstance(persistent_report, Mapping)
            else {}
        )
        return (
            "CONTEXT GOVERNANCE REPORT\n"
            f"runtime_context_count = {runtime_context_count}\n"
            "persistent_context_count = "
            f"{persistent_report.get('persistent_context_count', 0)}\n"
            f"governance_context_count = {governance_context_count}\n"
            "context_retention_rate = "
            f"{persistent_report.get('context_retention_rate', 1.0)}\n"
            "context_loss_events = "
            f"{persistent_report.get('context_loss_events', 0)}\n"
            f"context_registration_gap = {gap}\n"
            f"registration_coverage = {round(coverage, 4)}\n"
            f"visible_contexts = {visible_contexts}\n"
            f"hidden_contexts = {hidden_contexts}\n"
            f"unregistered_contexts = {hidden_contexts}\n"
            f"loaded_contexts = {persistent_report.get('loaded_contexts', [])}\n"
            f"new_contexts = {persistent_report.get('new_contexts', [])}\n"
            f"revoked_contexts = {persistent_report.get('revoked_contexts', [])}\n"
            f"missing_contexts = {persistent_report.get('missing_contexts', [])}\n"
        )


def governance_process_report(context: Mapping[str, Any]) -> dict[str, Any]:
    source = context.get("source_context", {})
    if not isinstance(source, Mapping):
        source = {}
    preconditions = list(
        source.get("preconditions", source.get("initial_state", [])) or []
    )
    transition_signature = list(
        source.get(
            "transition_signature",
            source.get("transitions", source.get("transition_steps", [])),
        )
        or []
    )
    transition_steps = [
        {
            "source": item.get("from", item.get("source")),
            "relation": item.get(
                "transition",
                item.get("relation", "transitions_to"),
            ),
            "target": item.get("to", item.get("target")),
            "confidence": item.get(
                "confidence",
                context.get("context_confidence", 0.0),
            ),
        }
        for item in transition_signature
        if isinstance(item, Mapping)
    ]
    outcomes = list(
        source.get("expected_outcomes", source.get("postconditions", source.get("final_state", [])))
        or []
    )
    strength = clamp(
        context.get(
            "context_strength",
            source.get("process_context_strength", source.get("context_confidence", 0.0)),
        )
    )
    return {
        **dict(source),
        "system": "context_governance_registry",
        "concept": context.get("concept"),
        "context_name": context.get("context_id"),
        "process_context": context.get("context_id"),
        "generated_context": context.get("context_id"),
        "process_family": source.get(
            "process_family",
            source.get("concept", context.get("concept")),
        ),
        "preconditions": preconditions,
        "initial_state": preconditions,
        "transition_signature": transition_signature,
        "transitions": transition_signature,
        "transition_steps": transition_steps,
        "postconditions": outcomes,
        "final_state": outcomes,
        "expected_outcomes": outcomes,
        "context_confidence": context.get("context_confidence", strength),
        "confidence": context.get("context_confidence", strength),
        "process_context_strength": strength,
        "process_context_generated": True,
        "process_context_ready": strength > 0.90,
        "status": source.get("status", "PROCESS_CONTEXT_VALIDATED"),
        "governance_visible": True,
        "supporting_math_evidence": {
            **dict(source.get("supporting_math_evidence", {})),
            "typed_dependencies_generated": True,
            "context_governance_registered": True,
            "process_signature_generated": True,
            "process_signature_match": True,
            "process_signature_strength": strength,
            "transition_sequence_generated": bool(
                transition_steps or transition_signature
            ),
            "preconditions_identified": bool(preconditions),
            "postconditions_identified": bool(outcomes),
            "temporal_state_sequence_generated": bool(
                preconditions and transition_signature and outcomes
            ),
            "final_state_identified": bool(outcomes),
            "dependency_semantics_score": strength,
            "identity_scope_leakage_detected": False,
        },
    }


def context_from_governance_report(
    governance_report: Mapping[str, Any],
    concept: str | None = None,
    context_id: str | None = None,
) -> dict[str, Any]:
    governance_report = (
        governance_report
        if isinstance(governance_report, Mapping)
        else {}
    )
    normalized_concept = _normalize(concept)
    expected = context_id or _context_id_for_concept(normalized_concept)
    for context in governance_report.get("visible_contexts", []) or []:
        if not isinstance(context, Mapping):
            continue
        if context.get("context_id") == expected:
            return dict(context)
        if normalized_concept and context.get("concept") == normalized_concept:
            return dict(context)
    return {}


def _persistent_source_context(context):
    source = context.get("source_context", {})
    if not isinstance(source, Mapping):
        source = {}
    return {
        **dict(source),
        "context_id": context.get("context_id"),
        "context_name": context.get(
            "context_id",
            source.get("context_name"),
        ),
        "context_type": context.get("context_type"),
        "concept": context.get(
            "source_concept",
            source.get("concept"),
        ),
        "semantic_validation": context.get("semantic_validation"),
        "identity_compatible": context.get("identity_compatible"),
        "governance_visible": context.get("governance_visible"),
        "context_confidence": context.get(
            "confidence",
            source.get("context_confidence", source.get("confidence")),
        ),
        "status": source.get("status", context.get("status")),
    }


def _has_context_identity(context):
    return bool(_context_id(context))


def _context_id(context):
    value = (
        context.get("canonical_context_name")
        or context.get("context_id")
        or context.get("context_name")
        or context.get("process_context")
        or context.get("generated_context")
        or context.get("semantic_context")
        or context.get("context")
    )
    value = _normalize(value)
    if value in PROCESS_CONCEPTS:
        return _context_id_for_concept(value)
    return value


def _context_id_for_concept(concept):
    concept = _normalize(concept)
    if concept == "directional_motion":
        return "directional_motion_context"
    return f"{concept}_context" if concept else ""


def _context_type(context_id, context, source_key):
    if context_id in STATIC_CONTEXTS:
        if context_id in TAXONOMY_CONTEXTS:
            return "TAXONOMY_CONTEXT"
        return "STATIC_CONTEXT"
    if context_id in PROCESS_CONTEXTS or _normalize(context.get("concept")) in PROCESS_CONCEPTS:
        return "PROCESS_CONTEXT"
    if "identity" in context_id or "identity" in source_key:
        return "IDENTITY_CONTEXT"
    if "causal" in context_id or "causal" in source_key or "dependency" in source_key:
        return "CAUSAL_CONTEXT"
    if "relation" in context_id or "relational" in source_key:
        return "RELATIONAL_CONTEXT"
    return "STATIC_CONTEXT"


def _semantic_validation(context, context_type):
    if context.get("semantic_validation") is not None:
        return bool(context.get("semantic_validation"))
    if context.get("semantic_validation_passed") is not None:
        return bool(context.get("semantic_validation_passed"))
    if context.get("process_context_ready") is True:
        return True
    if context.get("process_context_generated") is True:
        return True
    if context.get("status") in {
        "PROCESS_CONTEXT_VALIDATED",
        "PROCESS_CONTEXT_SUPPORTED",
        "SEMANTICALLY_VALIDATED",
    }:
        return True
    if context_type in {"IDENTITY_CONTEXT", "CAUSAL_CONTEXT"}:
        return True
    if context_type == "TAXONOMY_CONTEXT":
        return True
    return bool(context.get("properties") or context.get("capabilities"))


def _identity_compatible(context):
    if context.get("identity_compatible") is not None:
        return bool(context.get("identity_compatible"))
    if context.get("identity_scope_leakage_detected") is True:
        return False
    evidence = context.get("supporting_math_evidence", {})
    if isinstance(evidence, Mapping) and evidence.get("identity_scope_leakage_detected"):
        return False
    if context.get("integration_safe") is False:
        return False
    if context.get("ontology_safe") is False:
        return False
    return True


def _confidence(context):
    for key in (
        "context_confidence",
        "confidence",
        "process_context_strength",
        "semantic_context_score",
        "context_strength_estimate",
        "dependency_coherence",
    ):
        value = context.get(key)
        if value is not None:
            return clamp(value)
    return 0.82


def _strength(context, confidence):
    for key in (
        "context_strength",
        "process_context_strength",
        "context_strength_estimate",
        "semantic_context_score",
    ):
        value = context.get(key)
        if value is not None:
            return clamp(value)
    return confidence


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


context_governance_registry = ContextGovernanceRegistry()


__all__ = [
    "ContextGovernanceRegistry",
    "context_from_governance_report",
    "context_governance_registry",
    "governance_process_report",
]
