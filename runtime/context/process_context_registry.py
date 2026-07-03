"""Registry for reusable process contexts learned from promoted strategies."""

from __future__ import annotations

from typing import Any, Mapping

from core.epistemic_models import clamp
from runtime.context.process_context_models import (
    ProcessContext,
    normalize_context_name,
    process_context_from_mapping,
)
from runtime.context.process_context_report_builder import (
    context_from_registry_report,
    process_report_from_registry_context,
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
    """Consolidate validated process strategies into reusable context records."""

    system_name = "process_context_registry"

    def __init__(self):
        self.contexts: dict[str, dict[str, Any]] = {}
        self.strategy_index: dict[str, list[str]] = {}

    def register(self, process_context: ProcessContext | Mapping[str, Any]) -> dict[str, Any]:
        context = self._coerce_context(process_context)
        if not context:
            return {}
        context_name = str(
            context.get("context_name")
            or context.get("name")
            or context.get("process_id")
            or context.get("concept", "")
            or ""
        ).strip()
        if not context_name:
            context_name = f"{context.get('concept', 'process')}_context"
        self.contexts[context_name] = context
        self.strategy_index.setdefault(
            str(context.get("source_strategy", "unknown")),
            [],
        )
        if context_name not in self.strategy_index[str(context.get("source_strategy", "unknown"))]:
            self.strategy_index[str(context.get("source_strategy", "unknown"))].append(context_name)
        return dict(context)

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
            context_name = context.get("context_name", f"{concept}_context")
            existing = self.contexts.get(context_name)
            if existing and existing.get("source_strategy") != source_strategy:
                continue
            self.contexts[context_name] = context
            self.strategy_index.setdefault(source_strategy, [])
            if context_name not in self.strategy_index[source_strategy]:
                self.strategy_index[source_strategy].append(context_name)
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
        return {
            "system": self.system_name,
            "dependency_semantics_score": clamp(
                process_report.get("process_context_strength", 0.0)
            ),
            "typed_dependencies": [
                {
                    "source": item.get("source"),
                    "target": item.get("target"),
                    "relation": item.get("relation"),
                    "confidence": item.get("confidence", 0.0),
                }
                for item in process_report.get("transition_steps", [])
                if isinstance(item, Mapping)
            ],
            "semantic_dependency_signature": {
                "relation_types": sorted(
                    {
                        str(item.get("relation"))
                        for item in process_report.get("transition_steps", [])
                        if isinstance(item, Mapping) and item.get("relation")
                    }
                ),
                "process_context": process_report.get("context_name"),
                "has_causal_chain": bool(process_report.get("transition_steps")),
                "temporal_transition_context": True,
            },
        }

    def _coerce_context(self, process_context: ProcessContext | Mapping[str, Any]) -> dict[str, Any]:
        if isinstance(process_context, ProcessContext):
            return process_context.as_dict(compact=False)
        if isinstance(process_context, Mapping):
            return dict(process_context)
        return {}

    def _build_context(self, source_strategy, concept, strategy):
        confidence = clamp(strategy.get("confidence", 0.90))
        context_name = f"{concept}_context"
        return {
            "context_name": context_name,
            "source_strategy": source_strategy,
            "preconditions": list(strategy.get("preconditions", []) or []),
            "transitions": list(strategy.get("transitions", []) or []),
            "expected_outcomes": list(strategy.get("expected_outcomes", []) or []),
            "context_confidence": round(confidence, 4),
            "concept": concept,
            "status": (
                "PROCESS_CONTEXT_VALIDATED"
                if confidence > 0.90
                else "PROCESS_CONTEXT_SUPPORTED"
            ),
            "temporal_consistency": 0.0,
            "process_context_strength": confidence,
            "ontology_safe": True,
            "auto_merged": False,
            "anti_domination_checked": True,
        }

    def _as_process_context_report(self, context: Mapping[str, Any]) -> dict[str, Any]:
        return process_report_from_registry_context(dict(context))

    def _select_context(self, concept=None, context_name=None):
        if context_name and context_name in self.contexts:
            return self.contexts[context_name]
        normalized_concept = normalize_context_name(concept)
        for context in self.contexts.values():
            if context.get("concept") == normalized_concept:
                return context
        return {}

    def _strategy_process_concepts(self, source_strategy, strategy):
        normalized = normalize_context_name(source_strategy)
        mapped = set(STRATEGY_PROCESS_MAP.get(normalized, ()))
        primitive = normalize_context_name(strategy.get("primitive"))
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


def _strategy_name(strategy: Mapping[str, Any]) -> str:
    return str(
        strategy.get(
            "strategy",
            strategy.get("type", strategy.get("source_strategy", "unknown")),
        )
        or "unknown"
    )


process_context_registry = ProcessContextRegistry()


__all__ = [
    "ProcessContext",
    "ProcessContextRegistry",
    "context_from_registry_report",
    "process_context_registry",
    "process_context_from_mapping",
    "process_report_from_registry_context",
]
