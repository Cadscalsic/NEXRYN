from core.process_abstraction import ProcessAbstractionLayer


def _normalize(value, default="unknown"):
    if value is None:
        return default
    return str(value).strip().lower().replace(" ", "_") or default


class ProcessContextGenerationEngine:
    """Generates first-class semantic contexts for process concepts."""

    def generate_context(self, concept, evidence=None):
        concept = _normalize(concept)
        abstraction = ProcessAbstractionLayer.get(concept)
        if abstraction is None:
            return {
                "system": "process_context_generation_engine",
                "concept": concept,
                "process_context_generated": False,
                "process_context_ready": False,
                "reason": "no_process_abstraction_registered",
            }

        evidence = evidence if isinstance(evidence, dict) else {}
        surface = abstraction.discovery_surface()
        semantic = abstraction.semantic_context()
        context = {
            "system": "process_context_generation_engine",
            "concept": abstraction.concept,
            "process_operator": abstraction.concept,
            "process_context": abstraction.context_id,
            "context_id": abstraction.context_id,
            "context_name": abstraction.context_id,
            "context_family": abstraction.context_family,
            "context_surface": abstraction.surface,
            "definition": abstraction.definition,
            "properties": list(abstraction.properties),
            "capabilities": list(abstraction.capabilities),
            "constraints": list(abstraction.constraints),
            "implications": list(abstraction.implications),
            "transfer_conditions": list(abstraction.transfer_conditions),
            "validation_criteria": list(abstraction.validation_criteria),
            "native_contexts": list(abstraction.native_contexts),
            "dependency_contexts": list(abstraction.dependency_contexts),
            "inherited_features": list(abstraction.inherited_features),
            "discovery_surface": surface,
            "semantic_context": semantic,
            "hierarchy_root": abstraction.context_id,
            "hierarchy_children": sorted(
                set(abstraction.native_contexts + (abstraction.concept,))
            ),
            "process_context_generated": True,
            "process_context_ready": True,
            "evidence": dict(evidence),
        }
        return context

    def generate_contexts(self, concepts=None):
        concepts = concepts or sorted(ProcessAbstractionLayer.ABSTRACTIONS)
        return [
            self.generate_context(concept)
            for concept in concepts
        ]

    @classmethod
    def discovery_surfaces(cls):
        engine = cls()
        return {
            item["concept"]: {
                **item["discovery_surface"],
                "process_context": item["process_context"],
                "process_context_generated": True,
            }
            for item in engine.generate_contexts()
            if item["process_context_generated"]
        }

    @classmethod
    def semantic_contexts(cls):
        engine = cls()
        contexts = {}
        for item in engine.generate_contexts():
            if not item["process_context_generated"]:
                continue
            semantic = {
                **item["semantic_context"],
                "process_context_generated": True,
                "process_context": item["process_context"],
            }
            contexts[item["concept"]] = semantic
            contexts[item["process_context"]] = semantic
        return contexts

    @classmethod
    def report(cls, concepts=None):
        contexts = cls().generate_contexts(concepts)
        generated = [
            item
            for item in contexts
            if item.get("process_context_generated")
        ]
        return {
            "system": "process_context_generation_engine",
            "process_context_count": len(generated),
            "process_contexts": generated,
            "process_context_generation_ready": bool(generated),
        }


__all__ = [
    "ProcessContextGenerationEngine",
]
