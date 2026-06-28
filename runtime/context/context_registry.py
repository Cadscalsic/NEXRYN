"""Canonical runtime registry for discovered and semantic contexts."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping

from runtime.context.context_validator import validate_context_collection


class ContextRegistry:
    """Single registration surface for context-producing runtime layers."""

    system_name = "context_registry"

    def __init__(self):
        self._contexts: dict[str, dict[str, Any]] = {}
        self._rejections: list[dict[str, Any]] = []
        self._attempts = 0

    def register_context(
        self,
        context: Mapping[str, Any] | None,
        source: str | None = None,
    ) -> dict[str, Any]:
        self._attempts += 1
        if not isinstance(context, Mapping):
            return self._reject(
                {},
                "context_not_mapping",
                received_type=type(context).__name__,
            )
        normalized = self._normalize_context(context, source=source)
        if not normalized.get("context_id"):
            return self._reject(context, "missing_context_id")
        if normalized.get("confidence", 0.0) <= 0.0:
            return self._reject(context, "non_positive_confidence")

        self._contexts[normalized["context_id"]] = normalized
        return {
            "system": self.system_name,
            "registered": True,
            "context_id": normalized["context_id"],
            "context": dict(normalized),
            "report_state": "final",
        }

    def register_batch(
        self,
        contexts: Iterable[Mapping[str, Any]] | None,
        source: str | None = None,
    ) -> dict[str, Any]:
        valid_contexts, validation = validate_context_collection(contexts)
        self._attempts += len(validation["context_rejection_reasons"])
        validation_rejections = [
            self._reject(
                {},
                reason.get("reason", "context_not_mapping"),
                received_type=reason.get("received_type"),
            )
            for reason in validation["context_rejection_reasons"]
        ]
        results = [
            self.register_context(context, source=source)
            for context in valid_contexts
        ]
        registered = [
            result["context"]
            for result in results
            if result.get("registered")
        ]
        rejected = [
            result
            for result in [*validation_rejections, *results]
            if not result.get("registered")
        ]
        return {
            "system": self.system_name,
            "report_state": "final",
            **self.metrics(),
            "contexts_received": validation["contexts_received"],
            "contexts_valid": validation["contexts_valid"],
            "contexts_registered": len(registered),
            "contexts_rejected": len(rejected),
            "context_rejection_reasons":
            validation["context_rejection_reasons"],
            "registered_contexts": registered,
            "rejection_reasons": [
                result.get("reason", "unknown_rejection")
                for result in rejected
            ],
        }

    def get_context(self, context_id: str) -> dict[str, Any]:
        return dict(self._contexts.get(str(context_id or ""), {}))

    def all_contexts(self) -> list[dict[str, Any]]:
        return [dict(context) for context in self._contexts.values()]

    def report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "report_state": "final",
            "contexts": self.all_contexts(),
            "rejections": list(self._rejections),
            **self.metrics(),
        }

    def metrics(self) -> dict[str, Any]:
        registered = len(self._contexts)
        rejected = len(self._rejections)
        attempts = max(self._attempts, 1)
        return {
            "registered_contexts": registered,
            "rejected_contexts": rejected,
            "active_contexts": registered,
            "context_registration_rate": round(registered / attempts, 4),
        }

    def _reject(
        self,
        context: Mapping[str, Any],
        reason: str,
        received_type: str | None = None,
    ) -> dict[str, Any]:
        rejection = {
            "system": self.system_name,
            "registered": False,
            "reason": reason,
            "context": dict(context),
            "report_state": "final",
        }
        if received_type:
            rejection["received_type"] = received_type
        self._rejections.append(rejection)
        return rejection

    def _normalize_context(
        self,
        context: Mapping[str, Any],
        source: str | None = None,
    ) -> dict[str, Any]:
        normalized = dict(context)
        concept = _first(
            normalized,
            "concept",
            "concept_name",
            "name",
            default="runtime_context",
        )
        context_type = str(
            normalized.get("context_type")
            or normalized.get("type")
            or "SEMANTIC_CONTEXT"
        )
        confidence = _score(
            normalized,
            "confidence",
            "context_confidence",
            "support_score",
            default=0.0,
        )
        normalized["concept"] = str(concept or "runtime_context")
        normalized["context_type"] = context_type
        normalized["confidence"] = confidence
        normalized["source"] = normalized.get("source") or source or "runtime"
        normalized["context_id"] = (
            normalized.get("context_id")
            or normalized.get("context_name")
            or _stable_context_id(normalized)
        )
        return normalized


def _first(mapping: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return default


def _score(
    mapping: Mapping[str, Any],
    *keys: str,
    default: float = 0.0,
) -> float:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return _clamp(value)
    return _clamp(default)


def _clamp(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


def _stable_context_id(context: Mapping[str, Any]) -> str:
    payload = json.dumps(context, sort_keys=True, default=str)
    digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
    concept = str(context.get("concept") or "runtime_context").lower()
    context_type = str(context.get("context_type") or "context").lower()
    return f"{context_type}:{concept}:{digest}"


context_registry = ContextRegistry()


__all__ = ["ContextRegistry", "context_registry"]
