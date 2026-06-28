"""Safe context normalization and JSON serialization boundary."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping

from runtime.utils.normalization import normalize_context_object, normalize_value


@dataclass(frozen=True)
class SerializedContext:
    context_id: str | None
    payload: str
    format: str = "json"

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "payload": self.payload,
            "format": self.format,
            "serialized_context": True,
        }


def normalize_context(context: Any) -> dict[str, Any]:
    normalized = normalize_context_object(context)
    return {
        str(key): normalize_value(value)
        for key, value in normalized.items()
    }


def serialize_context(context: Any) -> SerializedContext:
    normalized = normalize_context(context)
    context_id = normalized.get("context_id") or normalized.get("context_name")
    return SerializedContext(
        context_id=str(context_id) if context_id else None,
        payload=json.dumps(normalized, sort_keys=True, default=str),
    )


def deserialize_context(context: Any) -> dict[str, Any]:
    if isinstance(context, SerializedContext):
        return normalize_context(context.payload)
    if isinstance(context, Mapping) and context.get("serialized_context") is True:
        payload = context.get("payload")
        if isinstance(payload, str):
            return normalize_context(payload)
    return normalize_context(context)


def safe_context_accessor(context: Any, key: str | None = None, default: Any = None) -> Any:
    normalized = deserialize_context(context)
    if key is None:
        return normalized
    return normalized.get(key, default)


__all__ = [
    "SerializedContext",
    "normalize_context",
    "serialize_context",
    "deserialize_context",
    "safe_context_accessor",
]
