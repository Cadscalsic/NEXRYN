"""Type-safe validation and normalization for runtime context collections."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


SCALAR_CONTEXT_TYPES = (int, float, bool, str, type(None))


def is_valid_context(context: Any) -> bool:
    """Return True only for mapping-like context objects."""
    return isinstance(context, Mapping) and not isinstance(
        context,
        SCALAR_CONTEXT_TYPES,
    )


def normalize_context(context: Any) -> dict[str, Any] | None:
    """Return a shallow dict copy for valid contexts, otherwise None."""
    if not is_valid_context(context):
        return None
    return dict(context)


def validate_context_collection(
    contexts: Iterable[Any] | Mapping[str, Any] | Any | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Normalize a collection of contexts and report rejected entries."""
    entries = _as_entries(contexts)
    valid_contexts: list[dict[str, Any]] = []
    rejection_reasons: list[dict[str, Any]] = []

    for index, context in enumerate(entries):
        normalized = normalize_context(context)
        if normalized is None:
            rejection_reasons.append({
                "index": index,
                "reason": "context_not_mapping",
                "received_type": type(context).__name__,
            })
            continue
        valid_contexts.append(normalized)

    telemetry = {
        "contexts_received": len(entries),
        "contexts_valid": len(valid_contexts),
        "contexts_rejected": len(rejection_reasons),
        "context_rejection_reasons": rejection_reasons,
    }
    return valid_contexts, telemetry


def _as_entries(contexts: Any) -> list[Any]:
    if contexts is None:
        return []
    if isinstance(contexts, Mapping):
        return [contexts]
    if isinstance(contexts, SCALAR_CONTEXT_TYPES):
        return [contexts]
    if isinstance(contexts, Iterable):
        return list(contexts)
    return [contexts]


__all__ = [
    "is_valid_context",
    "normalize_context",
    "validate_context_collection",
]
