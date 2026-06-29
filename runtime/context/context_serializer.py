"""Compatibility exports for the safe context serialization engine."""

from runtime.context.context_serialization_engine import (
    ContextSerializationEngine,
    SerializedContext,
    context_serialization_engine,
    deserialize_context,
    normalize_context,
    safe_context_access,
    safe_context_print,
    serialize_context,
)


def safe_context_accessor(context, key=None, default=None):
    return safe_context_access(context, key, default)


__all__ = [
    "ContextSerializationEngine",
    "SerializedContext",
    "context_serialization_engine",
    "normalize_context",
    "serialize_context",
    "deserialize_context",
    "safe_context_access",
    "safe_context_accessor",
    "safe_context_print",
]
