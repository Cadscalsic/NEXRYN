"""Safe context serialization, access, and bounded printing."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Mapping


MAX_SERIALIZED_CONTEXT_BYTES = 1_000_000
MAX_CONTEXT_DEPTH = 8


@dataclass(frozen=True)
class SerializedContext:
    context_id: str | None
    payload: str
    format: str = "json"

    def to_dict(self) -> dict[str, Any]:
        return {
            "serialized_context": True,
            "context_id": self.context_id,
            "payload": self.payload,
            "format": self.format,
        }


class ContextSerializationEngine:
    system_name = "context_serialization_engine"

    def normalize_context(self, context: Any) -> dict[str, Any]:
        return _normalize(context, seen=set(), depth=0)

    def serialize_context(self, context: Any) -> SerializedContext:
        normalized = self.normalize_context(context)
        payload = json.dumps(normalized, sort_keys=True, default=str)
        if len(payload.encode("utf-8")) > MAX_SERIALIZED_CONTEXT_BYTES:
            normalized = {
                "context_id": normalized.get("context_id"),
                "concept": normalized.get("concept"),
                "context_type": normalized.get("context_type"),
                "confidence": normalized.get("confidence"),
                "serialization_truncated": True,
                "original_serialized_context_bytes": len(payload.encode("utf-8")),
            }
            payload = json.dumps(normalized, sort_keys=True, default=str)
        context_id = normalized.get("context_id") or normalized.get("context_name")
        return SerializedContext(
            context_id=str(context_id) if context_id else None,
            payload=payload,
        )

    def deserialize_context(self, context: Any) -> dict[str, Any]:
        if isinstance(context, SerializedContext):
            return self.normalize_context(context.payload)
        if isinstance(context, Mapping) and context.get("serialized_context") is True:
            return self.normalize_context(context.get("payload", {}))
        return self.normalize_context(context)

    def safe_context_access(
        self,
        context: Any,
        key: str | None = None,
        default: Any = None,
    ) -> Any:
        normalized = self.deserialize_context(context)
        if key is None:
            return normalized
        return normalized.get(key, default)

    def safe_context_print(self, context: Any) -> str:
        try:
            normalized = self.deserialize_context(context)
            return json.dumps(normalized, sort_keys=True, default=str)
        except Exception as exc:
            return json.dumps({
                "CONTEXT PRINT FAILURE": False,
                "context_print_repaired": True,
                "received_type": type(context).__name__,
                "error": str(exc),
            })


def normalize_context(context: Any) -> dict[str, Any]:
    return context_serialization_engine.normalize_context(context)


def serialize_context(context: Any) -> SerializedContext:
    return context_serialization_engine.serialize_context(context)


def deserialize_context(context: Any) -> dict[str, Any]:
    return context_serialization_engine.deserialize_context(context)


def safe_context_access(context: Any, key: str | None = None, default: Any = None) -> Any:
    return context_serialization_engine.safe_context_access(context, key, default)


def safe_context_print(context: Any) -> str:
    return context_serialization_engine.safe_context_print(context)


def _normalize(value: Any, seen: set[int], depth: int) -> dict[str, Any]:
    if depth > MAX_CONTEXT_DEPTH:
        return {"serialization_depth_limited": True}
    if isinstance(value, SerializedContext):
        return _normalize(value.payload, seen, depth + 1)
    if isinstance(value, str):
        decoded = _decode_json_string(value)
        if decoded is _JSON_DECODE_FAILED:
            return {
                "context_id": value,
                "context_text": value,
                "context_type": "TEXT_CONTEXT",
            }
        return _normalize(decoded, seen, depth + 1)
    if isinstance(value, Mapping):
        object_id = id(value)
        if object_id in seen:
            return {"recursive_context_reference": True}
        seen.add(object_id)
        return {
            str(key): _normalize_value(item, seen, depth + 1)
            for key, item in value.items()
        }
    if hasattr(value, "to_dict"):
        return _normalize(value.to_dict(), seen, depth + 1)
    if hasattr(value, "__dict__"):
        return _normalize(vars(value), seen, depth + 1)
    return {"context_value": value}


def _normalize_value(value: Any, seen: set[int], depth: int) -> Any:
    if depth > MAX_CONTEXT_DEPTH:
        return {"serialization_depth_limited": True}
    if isinstance(value, (str, int, float, bool)) or value is None:
        if isinstance(value, str):
            decoded = _decode_json_string(value)
            if decoded is _JSON_DECODE_FAILED:
                return value
            return _normalize_value(decoded, seen, depth + 1)
        return value
    if isinstance(value, Mapping):
        return _normalize(value, seen, depth)
    if isinstance(value, (list, tuple, set)):
        return [_normalize_value(item, seen, depth + 1) for item in list(value)[:200]]
    if hasattr(value, "to_dict"):
        return _normalize_value(value.to_dict(), seen, depth + 1)
    if hasattr(value, "__dict__"):
        return _normalize_value(vars(value), seen, depth + 1)
    return str(value)


_JSON_DECODE_FAILED = object()


def _decode_json_string(value: str) -> Any:
    if not _looks_like_serialized_context(value):
        return _JSON_DECODE_FAILED
    try:
        return json.loads(value)
    except Exception:
        return _JSON_DECODE_FAILED


def _looks_like_serialized_context(value: str) -> bool:
    stripped = value.lstrip()
    return stripped.startswith("{") or stripped.startswith("[")


context_serialization_engine = ContextSerializationEngine()


__all__ = [
    "SerializedContext",
    "ContextSerializationEngine",
    "context_serialization_engine",
    "normalize_context",
    "serialize_context",
    "deserialize_context",
    "safe_context_access",
    "safe_context_print",
]
