"""Process-side registry for semantic process contexts."""

from __future__ import annotations

from typing import Any, Mapping

from core.epistemic_models import clamp
from runtime.context.process_context_models import (
    ProcessContext,
    process_context_from_mapping,
)


class ProcessContextRegistry:
    """In-memory process context registry for runtime process cognition."""

    system_name = "process_context_registry"

    def __init__(self, max_contexts: int = 512):
        self._contexts: dict[str, ProcessContext] = {}
        self.max_contexts = max_contexts
        self.registration_count = 0
        self.replacement_count = 0
        self.usage_frequency: dict[str, int] = {}
        self.reuse_frequency: dict[str, int] = {}
        self.success_records: dict[str, list[float]] = {}
        self.process_evolution: dict[str, list[dict[str, Any]]] = {}

    def register(self, process_context: ProcessContext | Mapping[str, Any]) -> dict[str, Any]:
        context = (
            process_context
            if isinstance(process_context, ProcessContext)
            else process_context_from_mapping(process_context)
        )
        name = str(context.name or context.process_id or context.concept or "")
        if not name:
            name = "process_context"

        if name in self._contexts:
            self.replacement_count += 1

        self._contexts[name] = context
        self.registration_count += 1
        self.usage_frequency[name] = self.usage_frequency.get(name, 0) + 1
        self.process_evolution.setdefault(name, [])
        self.process_evolution[name].append(
            {
                "event": "registered",
                "context_strength": clamp(context.context_strength),
                "transition_count": len(context.transition_signature or []),
            }
        )

        if len(self._contexts) > self.max_contexts:
            oldest_key = next(iter(self._contexts))
            self._contexts.pop(oldest_key, None)

        return context.as_dict(compact=True)

    def record_usage(
        self,
        context_name: str,
        success: bool | None = None,
        accuracy: float | None = None,
        reused: bool = False,
    ) -> dict[str, Any]:
        name = str(context_name)
        self.usage_frequency[name] = self.usage_frequency.get(name, 0) + 1
        if reused:
            self.reuse_frequency[name] = self.reuse_frequency.get(name, 0) + 1
        if accuracy is not None:
            self.success_records.setdefault(name, [])
            self.success_records[name].append(clamp(accuracy))
        elif success is not None:
            self.success_records.setdefault(name, [])
            self.success_records[name].append(1.0 if success else 0.0)
        self.process_evolution.setdefault(name, [])
        self.process_evolution[name].append(
            {
                "event": "used",
                "success": success,
                "accuracy": accuracy,
                "reused": reused,
            }
        )
        return self.lifecycle_report(name)

    def lifecycle_report(self, context_name: str) -> dict[str, Any]:
        name = str(context_name)
        successes = self.success_records.get(name, [])
        return {
            "context_name": name,
            "usage_frequency": self.usage_frequency.get(name, 0),
            "reuse_frequency": self.reuse_frequency.get(name, 0),
            "success_rate": (
                round(sum(successes) / len(successes), 4)
                if successes
                else 0.0
            ),
            "process_evolution": list(self.process_evolution.get(name, [])),
        }

    def register_semantic_model(self, model: Mapping[str, Any]) -> dict[str, Any]:
        context = process_context_from_mapping(
            {
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
            }
        )

        self.register(context)
        registered = context.as_dict(compact=False)

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
        return [context.as_dict(compact=compact) for context in self._contexts.values()]

    def report(self, compact: bool = True) -> dict[str, Any]:
        contexts = self.all(compact=compact)

        visible = [context for context in contexts if context.get("governance_visible")]

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
            "usage_frequency": dict(self.usage_frequency),
            "reuse_frequency": dict(self.reuse_frequency),
            "success_rate": self._success_rates(),
            "process_evolution": dict(self.process_evolution),
            "compact_report": compact,
            "process_context_registration_rate": (
                round(len(visible) / len(contexts), 4) if contexts else 1.0
            ),
        }

    def _success_rates(self) -> dict[str, float]:
        return {
            name: round(sum(values) / len(values), 4)
            for name, values in self.success_records.items()
            if values
        }


__all__ = [
    "ProcessContext",
    "ProcessContextRegistry",
    "process_context_from_mapping",
]
