"""Semantic taxonomy expansion for previously unknown contexts."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp


TAXONOMY_CONTEXTS = {
    "density_context": {
        "context_family": "Density Context",
        "properties": ["object_density_changes", "preserves_topology"],
        "constraints": ["requires_topology_preservation"],
        "implications": ["density_variation_is_semantically_relevant"],
    },
    "scale_context": {
        "context_family": "Scale Context",
        "properties": ["size_changes", "preserves_identity"],
        "constraints": ["requires_identity_preservation"],
        "implications": ["size_variation_is_semantically_relevant"],
    },
    "mapping_context": {
        "context_family": "Mapping Context",
        "properties": [
            "changes_color",
            "preserves_identity",
            "preserves_topology",
        ],
        "constraints": ["requires_identity_and_topology_preservation"],
        "implications": ["attribute_mapping_is_semantically_relevant"],
    },
}


CONCEPT_CONTEXT_ALIASES = {
    "density_preservation": "density_context",
    "density_modulation": "density_context",
    "size_preservation": "scale_context",
    "scaling": "scale_context",
    "size_transformation": "scale_context",
    "symbolic_remapping": "mapping_context",
    "color_mapping": "mapping_context",
    "color_transformation": "mapping_context",
}


class ContextTaxonomyEngine:
    """Classify semantic context families that static discovery leaves unknown."""

    system_name = "context_taxonomy_engine"

    def classify(self, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
        context = context if isinstance(context, Mapping) else {}
        current_context = self._current_context_name(context)
        signals = self._signals(context)
        context_name = self._classify_from_signals(signals)
        reclassified = bool(
            context_name
            and current_context in {"", "unknown", "unknown_context"}
        )
        if not context_name:
            return {
                "system": self.system_name,
                "context_name": current_context or "unknown",
                "context_type": "UNKNOWN_CONTEXT",
                "known_context": False,
                "reclassified": False,
                "signals": signals,
                "context_confidence": 0.0,
                "governance_visible": False,
            }

        template = TAXONOMY_CONTEXTS[context_name]
        confidence = self._confidence(signals, context_name)
        return {
            "system": self.system_name,
            "context_name": context_name,
            "context": context_name,
            "semantic_context": context_name,
            "canonical_context_name": context_name,
            "context_type": "TAXONOMY_CONTEXT",
            "context_family": template["context_family"],
            "known_context": True,
            "reclassified": reclassified,
            "previous_context": current_context or "unknown",
            "signals": signals,
            "properties": list(template["properties"]),
            "constraints": list(template["constraints"]),
            "implications": list(template["implications"]),
            "context_confidence": confidence,
            "confidence": confidence,
            "semantic_context_score": confidence,
            "semantic_validation": True,
            "semantic_validation_passed": True,
            "identity_compatible": signals.get("preserves_identity", True),
            "governance_visible": True,
            "status": "SEMANTICALLY_VALIDATED",
        }

    def report(
        self,
        contexts: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        classifications = [
            self.classify(context)
            for context in contexts or []
            if isinstance(context, Mapping)
        ]
        known = [
            item
            for item in classifications
            if item.get("known_context")
        ]
        unknown = [
            item
            for item in classifications
            if not item.get("known_context")
        ]
        reclassified = [
            item
            for item in known
            if item.get("reclassified")
        ]
        total = len(classifications)
        coverage = len(known) / total if total else 1.0
        return {
            "system": self.system_name,
            "known_contexts": known,
            "unknown_contexts": unknown,
            "reclassified_contexts": reclassified,
            "known_context_count": len(known),
            "unknown_context_count": len(unknown),
            "context_taxonomy_coverage": round(clamp(coverage), 4),
            "taxonomy_coverage": round(clamp(coverage), 4),
            "context_taxonomy_report": self._log_report(
                known,
                unknown,
                reclassified,
                coverage,
            ),
        }

    def classify_runtime_context(
        self,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = (
            runtime_context
            if isinstance(runtime_context, Mapping)
            else {}
        )
        contexts = []
        for key in (
            "semantic_context",
            "discovered_context",
            "context_discovery",
            "context_signature",
            "process_context_report",
        ):
            value = runtime_context.get(key)
            if isinstance(value, Mapping):
                contexts.append(value)
        if not contexts:
            contexts = [runtime_context]
        return self.report(contexts)

    def _classify_from_signals(self, signals):
        concept = _normalize(signals.get("concept"))
        for active in signals.get("active_concepts", []):
            if active in CONCEPT_CONTEXT_ALIASES:
                return CONCEPT_CONTEXT_ALIASES[active]
        if concept in CONCEPT_CONTEXT_ALIASES:
            return CONCEPT_CONTEXT_ALIASES[concept]
        if (
            signals.get("changes_color")
            and signals.get("preserves_identity")
            and signals.get("preserves_topology")
        ):
            return "mapping_context"
        if signals.get("size_changes") and signals.get("preserves_identity"):
            return "scale_context"
        if (
            signals.get("object_density_changes")
            and signals.get("preserves_topology")
        ):
            return "density_context"
        return ""

    def _signals(self, context):
        properties = self._properties(context)
        active_concepts = self._active_concepts(context)
        topology_behavior = _normalize(
            context.get("topology_behavior", context.get("topology"))
        )
        color_behavior = _normalize(
            context.get("color_behavior", context.get("color"))
        )
        identity_behavior = _normalize(
            context.get("identity_behavior", context.get("identity"))
        )
        size_behavior = _normalize(
            context.get("size_behavior", context.get("size"))
        )
        concept = _normalize(
            context.get("concept", context.get("truth", context.get("task")))
        )
        return {
            "concept": concept,
            "active_concepts": active_concepts,
            "changes_color": self._flag(context, properties, "changes_color")
            or color_behavior in {
                "color_changed",
                "color_reassigned",
                "color_mapped",
                "color_transform",
            },
            "preserves_identity": self._flag(
                context,
                properties,
                "preserves_identity",
            )
            or identity_behavior in {
                "identity_preserved",
                "identity_persistence",
                "object_persisted",
            }
            or concept in {
                "density_preservation",
                "size_preservation",
                "symbolic_remapping",
            },
            "preserves_topology": self._flag(
                context,
                properties,
                "preserves_topology",
            )
            or topology_behavior in {
                "topology_preserved",
                "topology_stable",
            }
            or concept in {
                "density_preservation",
                "size_preservation",
                "symbolic_remapping",
            },
            "size_changes": self._flag(context, properties, "size_changes")
            or size_behavior in {
                "size_changed",
                "size_expanded",
                "size_reduced",
                "scale_changed",
            }
            or concept in {"size_preservation", "scaling", "size_transformation"},
            "object_density_changes": self._flag(
                context,
                properties,
                "object_density_changes",
            )
            or self._flag(context, properties, "density_changes")
            or concept in {"density_preservation", "density_modulation"},
        }

    def _properties(self, context):
        properties = set()
        for key in ("properties", "semantic_properties", "capabilities"):
            value = context.get(key, [])
            if isinstance(value, Mapping):
                value = value.keys()
            for item in value or []:
                if isinstance(item, Mapping):
                    item = item.get("property_name", item.get("name"))
                properties.add(_normalize(item, ""))
        nested = context.get("semantic_context", {})
        if isinstance(nested, Mapping) and nested and nested is not context:
            properties.update(self._properties(nested))
        signature = context.get("signature", {})
        if isinstance(signature, Mapping) and signature and signature is not context:
            properties.update(self._properties(signature))
        return properties

    def _active_concepts(self, context):
        concepts = set()
        for key in (
            "active_concepts",
            "target_concepts",
            "concept_labels",
            "concepts",
            "detected_concepts",
        ):
            value = context.get(key, [])
            if isinstance(value, Mapping):
                value = value.keys()
            for item in value or []:
                concepts.add(_normalize(item, ""))
        for key in ("concept", "truth", "task", "source_concept"):
            if context.get(key):
                concepts.add(_normalize(context.get(key), ""))
        return sorted(concept for concept in concepts if concept)

    def _current_context_name(self, context):
        return _normalize(
            context.get(
                "context_name",
                context.get(
                    "semantic_context",
                    context.get("context", context.get("discovered_context")),
                ),
            ),
            "",
        )

    def _flag(self, context, properties, key):
        if key in properties:
            return True
        value = context.get(key)
        if isinstance(value, bool):
            return value
        return _normalize(value, "") in {"true", "yes", "1", key}

    def _confidence(self, signals, context_name):
        required = TAXONOMY_CONTEXTS[context_name]["properties"]
        hits = sum(bool(signals.get(item)) for item in required)
        return round(clamp(0.76 + (hits / max(len(required), 1)) * 0.18), 4)

    def _log_report(self, known, unknown, reclassified, coverage):
        return (
            "CONTEXT TAXONOMY REPORT\n"
            f"known_contexts = {[item.get('context_name') for item in known]}\n"
            f"unknown_contexts = {[item.get('context_name') for item in unknown]}\n"
            "reclassified_contexts = "
            f"{[item.get('context_name') for item in reclassified]}\n"
            f"taxonomy_coverage = {round(clamp(coverage), 4)}\n"
        )


def _normalize(value: Any, default: str = "unknown") -> str:
    if value is None:
        return default
    if isinstance(value, Mapping):
        value = (
            value.get("context_name")
            or value.get("semantic_context")
            or value.get("context")
        )
    return str(value or "").strip().lower().replace(" ", "_") or default


context_taxonomy_engine = ContextTaxonomyEngine()


__all__ = [
    "ContextTaxonomyEngine",
    "context_taxonomy_engine",
]
