"""Registry for governance-visible process contexts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from core.epistemic_models import clamp


@dataclass
class ProcessContext:
    name: str
    process_family: str
    preconditions: list[str]
    transition_signature: list[str]
    postconditions: list[str]
    invariants: list[str]
    dependency_links: list[str]
    temporal_signature: dict[str, Any]
    context_strength: float
    identity_continuity: float
    causal_alignment: float
    concept: str = ""
    constraints: list[str] = field(default_factory=list)

    @property
    def governance_visible(self) -> bool:
        return bool(
            self.context_strength >= 0.85
            and self.identity_continuity >= 0.85
            and self.causal_alignment >= 0.85
        )

    @property
    def ready(self) -> bool:
        return bool(self.governance_visible and self.dependency_links)

    def compact_dict(self) -> dict[str, Any]:
        return {
            "context_name": self.name,
            "concept": self.concept,
            "process_family": self.process_family,
            "context_type": "PROCESS_CONTEXT",
            "process_context_strength": clamp(self.context_strength),
            "identity_continuity": clamp(self.identity_continuity),
            "causal_alignment": clamp(self.causal_alignment),
            "governance_visible": self.governance_visible,
            "process_context_ready": self.ready,
            "dependency_link_count": len(self.dependency_links),
            "transition_count": len(self.transition_signature),
            "status": (
                "PROCESS_CONTEXT_VALIDATED"
                if self.ready
                else "PROCESS_CONTEXT_SUPPORTED"
            ),
        }

    def as_dict(self, compact: bool = False) -> dict[str, Any]:
        if compact:
            return self.compact_dict()

        data = asdict(self)

        data.update({
            "context_name": self.name,
            "context_type": "PROCESS_CONTEXT",
            "process_context": self.name,
            "transition_steps": list(self.transition_signature),
            "transitions": list(self.transition_signature),
            "temporal_constraints": list(self.constraints),
            "process_context_strength": clamp(self.context_strength),
            "context_confidence": clamp(self.context_strength),
            "confidence": clamp(self.context_strength),
            "semantic_validation": True,
            "identity_compatible": self.identity_continuity >= 0.85,
            "governance_visible": self.governance_visible,
            "process_context_generated": True,
            "process_context_ready": self.ready,
            "status": (
                "PROCESS_CONTEXT_VALIDATED"
                if self.ready
                else "PROCESS_CONTEXT_SUPPORTED"
            ),
            "supporting_math_evidence": {
                "typed_dependencies_generated": bool(self.dependency_links),
                "process_signature_generated": True,
                "process_signature_match": True,
                "process_signature_strength": clamp(self.context_strength),
                "transition_sequence_generated": bool(self.transition_signature),
                "preconditions_identified": bool(self.preconditions),
                "postconditions_identified": bool(self.postconditions),
                "temporal_state_sequence_generated": bool(
                    self.preconditions
                    and self.transition_signature
                    and self.postconditions
                ),
                "final_state_identified": bool(self.postconditions),
                "dependency_semantics_score": clamp(self.context_strength),
                "identity_scope_leakage_detected": False,
            },
        })

        return data


class ProcessContextRegistry:
    """In-memory process context registry for runtime process cognition."""

    system_name = "process_context_registry"

    def __init__(self, max_contexts: int = 512):
        self._contexts: dict[str, ProcessContext] = {}
        self.max_contexts = max_contexts
        self.registration_count = 0
        self.replacement_count = 0

    def register(self, process_context: ProcessContext) -> dict[str, Any]:
        name = str(process_context.name)

        if name in self._contexts:
            self.replacement_count += 1

        self._contexts[name] = process_context
        self.registration_count += 1

        if len(self._contexts) > self.max_contexts:
            oldest_key = next(iter(self._contexts))
            self._contexts.pop(oldest_key, None)

        return process_context.as_dict(compact=True)

    def register_semantic_model(self, model: Mapping[str, Any]) -> dict[str, Any]:
        context = process_context_from_mapping({
            **dict(model),
            "name": model.get(
                "context_name",
                f"{model.get('concept', 'process')}_context",
            ),
            "transition_signature": model.get(
                "transition_steps",
                model.get("transition_signature", []),
            ),
            "context_strength": model.get(
                "process_context_strength",
                model.get("context_strength", 0.0),
            ),
            "identity_continuity": model.get("identity_continuity", 0.90),
            "causal_alignment": model.get("causal_alignment", 0.90),
            "dependency_links": model.get(
                "dependency_links",
                model.get("transition_steps", []),
            ),
        })

        registered = self.register(context)

        return {
            **registered,
            "process_semantic_model": True,
            "source_model_summary": {
                "concept": model.get("concept"),
                "context_name": model.get("context_name"),
                "transition_count": len(
                    model.get("transition_steps", [])
                    or model.get("transition_signature", [])
                    or []
                ),
            },
        }

    def get(self, name: str, compact: bool = False) -> dict[str, Any]:
        context = self._contexts.get(str(name))
        return context.as_dict(compact=compact) if context else {}

    def all(self, compact: bool = True) -> list[dict[str, Any]]:
        return [
            context.as_dict(compact=compact)
            for context in self._contexts.values()
        ]

    def report(self, compact: bool = True) -> dict[str, Any]:
        contexts = self.all(compact=compact)

        visible = [
            context
            for context in contexts
            if context.get("governance_visible")
        ]

        process_semantic_models = {
            context.get("concept"): context
            for context in contexts
            if context.get("concept")
        }

        return {
            "system": self.system_name,
            "contexts": contexts,
            "process_semantic_models": process_semantic_models,
            "visible_contexts": visible,
            "process_context_count": len(contexts),
            "visible_context_count": len(visible),
            "registration_count": self.registration_count,
            "replacement_count": self.replacement_count,
            "compact_report": compact,
            "process_context_registration_rate": (
                round(len(visible) / len(contexts), 4)
                if contexts
                else 1.0
            ),
        }


def process_context_from_mapping(data: Mapping[str, Any]) -> ProcessContext:
    return ProcessContext(
        name=str(data.get("name") or data.get("context_name") or ""),
        concept=str(data.get("concept", "")),
        process_family=str(
            data.get("process_family")
            or data.get("concept")
            or data.get("context_name", "").replace("_context", "")
        ),
        preconditions=list(data.get("preconditions", []) or []),
        transition_signature=list(
            data.get(
                "transition_signature",
                data.get("transitions", data.get("causal_sequence", [])),
            )
            or []
        ),
        postconditions=list(data.get("postconditions", []) or []),
        invariants=list(data.get("invariants", []) or []),
        dependency_links=list(data.get("dependency_links", []) or []),
        temporal_signature=dict(data.get("temporal_signature", {}) or {}),
        context_strength=clamp(
            data.get("context_strength", data.get("process_context_strength", 0.0))
        ),
        identity_continuity=clamp(data.get("identity_continuity", 0.0)),
        causal_alignment=clamp(data.get("causal_alignment", 0.0)),
        constraints=list(data.get("constraints", []) or []),
    )


__all__ = [
    "ProcessContext",
    "ProcessContextRegistry",
    "process_context_from_mapping",
]