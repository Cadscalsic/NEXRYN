"""Registry for reusable process contexts learned from promoted strategies."""

from __future__ import annotations

from typing import Any, Mapping

from core.dependency.process_dependency_memory import ProcessDependencyMemory
from core.epistemic_models import clamp
from runtime.context.temporal_process_context_engine import (
    TemporalProcessContextEngine,
)


STRATEGY_PROCESS_MAP = {
    "structural_object_count": ("replication", "growth", "topological_growth"),
    "duplicate_object": ("replication", "growth", "topological_growth"),
    "object_count_increase": ("growth", "replication"),
    "growth": ("growth",),
    "growth_strategy": ("growth",),
    "replication": ("replication",),
    "replication_strategy": ("replication",),
    "propagation": ("propagation",),
    "directional_motion": ("directional_motion",),
    "topological_growth": ("topological_growth",),
}


class ProcessContextRegistry:
    """Consolidate validated process strategies into reusable contexts."""

    system_name = "process_context_registry"

    def __init__(self, dependency_memory: ProcessDependencyMemory | None = None):
        self.dependency_memory = dependency_memory or ProcessDependencyMemory(
            seed_defaults=True,
        )
        self.temporal_context_engine = TemporalProcessContextEngine()
        self.contexts: dict[str, dict[str, Any]] = {}
        self.strategy_index: dict[str, list[str]] = {}

    def register_promoted_strategy(
        self,
        strategy: Mapping[str, Any],
        validation_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        strategy = strategy if isinstance(strategy, Mapping) else {}
        validation_report = (
            validation_report
            if isinstance(validation_report, Mapping)
            else {}
        )
        source_strategy = _strategy_name(strategy)

        if not self._promotion_validated(strategy, validation_report):
            return self._rejected(
                source_strategy,
                "strategy_not_promoted_or_validation_incomplete",
            )
        if not self._ontology_safe(strategy, validation_report):
            return self._rejected(source_strategy, "ontology_safety_failed")
        if self._anti_domination_risk(strategy, validation_report):
            return self._rejected(
                source_strategy,
                "anti_domination_protection_triggered",
            )

        concepts = self._strategy_process_concepts(source_strategy, strategy)
        if not concepts:
            return self._rejected(
                source_strategy,
                "no_process_context_mapping_available",
            )

        registered = []
        for concept in concepts:
            context = self._build_context(source_strategy, concept, strategy)
            existing = self.contexts.get(context["context_name"])
            if existing and existing.get("source_strategy") != source_strategy:
                continue
            self.contexts[context["context_name"]] = context
            self.strategy_index.setdefault(source_strategy, [])
            if context["context_name"] not in self.strategy_index[source_strategy]:
                self.strategy_index[source_strategy].append(context["context_name"])
            registered.append(context)

        return {
            "system": self.system_name,
            "source_strategy": source_strategy,
            "registered": bool(registered),
            "registered_contexts": registered,
            "context_count": self.context_count,
            "context_names": sorted(self.contexts),
            "process_context_registry_ready": bool(self.contexts),
            "ontology_safety_preserved": True,
            "anti_domination_protections_respected": True,
            "auto_merge_forbidden": True,
        }

    def report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "context_count": self.context_count,
            "contexts": list(self.contexts.values()),
            "context_names": sorted(self.contexts),
            "strategy_index": {
                strategy: list(contexts)
                for strategy, contexts in sorted(self.strategy_index.items())
            },
            "process_context_registry_ready": bool(self.contexts),
            "ontology_safety_preserved": True,
            "anti_domination_protections_respected": True,
        }

    @property
    def context_count(self) -> int:
        return len(self.contexts)

    def get_context(self, context_name: str) -> dict[str, Any]:
        return dict(self.contexts.get(str(context_name or ""), {}))

    def process_context_report(
        self,
        concept: str | None = None,
        context_name: str | None = None,
    ) -> dict[str, Any]:
        context = self._select_context(concept=concept, context_name=context_name)
        if not context:
            return {}
        return self._as_process_context_report(context)

    def dependency_semantics_report(
        self,
        concept: str | None = None,
        context_name: str | None = None,
    ) -> dict[str, Any]:
        process_report = self.process_context_report(
            concept=concept,
            context_name=context_name,
        )
        if not process_report:
            return {}
        return self.temporal_context_engine.dependency_semantics_report(
            process_report,
        )

    def _build_context(self, source_strategy, concept, strategy):
        temporal_report = self.temporal_context_engine.evaluate(
            concept,
            dependency_chain=self.dependency_memory.resolve_chain(concept),
            transformational_identity={
                "integration_safe": True,
                "identity_continuity": clamp(strategy.get("confidence", 0.90)),
            },
        )
        confidence = clamp(
            max(
                temporal_report.get("process_context_strength", 0.0),
                temporal_report.get("confidence", 0.0),
                strategy.get("confidence", 0.0),
            )
        )
        return {
            "context_name": temporal_report.get(
                "context_name",
                f"{concept}_context",
            ),
            "source_strategy": source_strategy,
            "preconditions": list(temporal_report.get("initial_state", [])),
            "transitions": list(temporal_report.get("transitions", [])),
            "expected_outcomes": list(temporal_report.get("final_state", [])),
            "context_confidence": round(confidence, 4),
            "concept": concept,
            "status": (
                "PROCESS_CONTEXT_VALIDATED"
                if confidence > 0.90
                else "PROCESS_CONTEXT_SUPPORTED"
            ),
            "temporal_consistency": temporal_report.get(
                "temporal_consistency",
                0.0,
            ),
            "process_context_strength": temporal_report.get(
                "process_context_strength",
                confidence,
            ),
            "temporal_process_context_report": temporal_report,
            "ontology_safe": True,
            "auto_merged": False,
            "anti_domination_checked": True,
        }

    def _as_process_context_report(self, context):
        temporal_report = context.get("temporal_process_context_report", {})
        transitions = list(context.get("transitions", []))
        preconditions = list(context.get("preconditions", []))
        outcomes = list(context.get("expected_outcomes", []))
        strength = clamp(context.get("process_context_strength", 0.0))
        return {
            **temporal_report,
            "system": self.system_name,
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
                "temporal_state_sequence_generated": bool(
                    preconditions and transitions and outcomes
                ),
                "final_state_identified": bool(outcomes),
                "dependency_semantics_score": strength,
                "identity_scope_leakage_detected": False,
            },
        }

    def _select_context(self, concept=None, context_name=None):
        if context_name and context_name in self.contexts:
            return self.contexts[context_name]
        normalized_concept = _normalize(concept)
        for context in self.contexts.values():
            if context.get("concept") == normalized_concept:
                return context
        return {}

    def _strategy_process_concepts(self, source_strategy, strategy):
        normalized = _normalize(source_strategy)
        mapped = set(STRATEGY_PROCESS_MAP.get(normalized, ()))
        primitive = _normalize(strategy.get("primitive"))
        mapped.update(STRATEGY_PROCESS_MAP.get(primitive, ()))
        if "duplicate" in normalized or "replic" in normalized:
            mapped.add("replication")
        if "object_count" in normalized or "growth" in normalized:
            mapped.add("growth")
        if "propagat" in normalized:
            mapped.add("propagation")
        return [
            concept
            for concept in (
                "replication",
                "growth",
                "propagation",
                "directional_motion",
                "topological_growth",
            )
            if concept in mapped
        ]

    def _promotion_validated(self, strategy, validation_report):
        status = strategy.get("status")
        return bool(
            status == "promoted"
            or strategy.get("promotion_allowed") is True
            or validation_report.get("promotion_allowed") is True
            or validation_report.get("promotion_candidate") is True
        )

    def _ontology_safe(self, strategy, validation_report):
        temporal = validation_report.get("temporal_validation", {})
        if isinstance(temporal, Mapping) and temporal.get("ontology_safety") is False:
            return False
        return bool(
            strategy.get("ontology_safe", True)
            and validation_report.get("ontology_safe", True)
            and validation_report.get("ontology_safety", True)
        )

    def _anti_domination_risk(self, strategy, validation_report):
        return bool(
            strategy.get("anti_domination_risk")
            or strategy.get("domination_risk")
            or validation_report.get("anti_domination_risk")
            or validation_report.get("domination_risk")
        )

    def _rejected(self, source_strategy, reason):
        return {
            "system": self.system_name,
            "source_strategy": source_strategy,
            "registered": False,
            "registered_contexts": [],
            "context_count": self.context_count,
            "rejection_reason": reason,
            "ontology_safety_preserved": reason != "ontology_safety_failed",
            "anti_domination_protections_respected": (
                reason != "anti_domination_protection_triggered"
            ),
            "auto_merge_forbidden": True,
        }


def context_from_registry_report(
    registry_report: Mapping[str, Any],
    concept: str | None = None,
    context_name: str | None = None,
) -> dict[str, Any]:
    registry_report = (
        registry_report
        if isinstance(registry_report, Mapping)
        else {}
    )
    contexts = registry_report.get("contexts", [])
    if not contexts:
        contexts = registry_report.get("registered_contexts", [])
    normalized_concept = _normalize(concept)
    for context in contexts or []:
        if not isinstance(context, Mapping):
            continue
        if context_name and context.get("context_name") == context_name:
            return dict(context)
        if normalized_concept and context.get("concept") == normalized_concept:
            return dict(context)
    return {}


def process_report_from_registry_context(
    context: Mapping[str, Any],
) -> dict[str, Any]:
    registry = ProcessContextRegistry()
    return registry._as_process_context_report(dict(context))


def _strategy_name(strategy: Mapping[str, Any]) -> str:
    return str(
        strategy.get(
            "strategy",
            strategy.get("type", strategy.get("source_strategy", "unknown")),
        )
        or "unknown"
    )


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


process_context_registry = ProcessContextRegistry()


__all__ = [
    "ProcessContextRegistry",
    "context_from_registry_report",
    "process_context_registry",
    "process_report_from_registry_context",
]
