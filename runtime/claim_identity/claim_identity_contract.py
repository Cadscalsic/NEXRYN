from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


CLAIM_SUBJECT_SCHEMA_VERSION = "1.0"
CLAIM_ID_PREFIX = "claim_sha256_"
_WHITESPACE_RE = re.compile(r"\s+")
_SNAKE_BOUNDARY_RE = re.compile(r"[^0-9a-zA-Z]+")
_RUN_LOCAL_REF_PREFIXES = (
    "accepted_evidence:",
    "candidate:",
    "evidence_decision:",
    "evidence_plan:",
    "plan:",
    "raw_result:",
    "run:",
    "target_candidate:",
    "target_operation:",
    "task:",
)


class ClaimIdentityError(ValueError):
    """Raised when a ClaimSubject cannot safely participate in identity."""


class ClaimKind(str, Enum):
    CANDIDATE_OPERATION = "candidate_operation"
    CONCEPT_TRUTH = "concept_truth"
    CAPABILITY_STATEMENT = "capability_statement"
    CONTEXTUAL_ASSERTION = "contextual_assertion"


class SemanticScope(str, Enum):
    TASK = "task"
    RUN = "run"
    CROSS_RUN = "cross_run"
    GLOBAL = "global"


@dataclass(frozen=True)
class ClaimSubject:
    kind: ClaimKind | str
    semantic_scope: SemanticScope | str
    subject_ref: str | None = None
    operation: str | None = None
    normalized_statement: str | None = None
    qualifiers: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = CLAIM_SUBJECT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "qualifiers", _freeze_value(self.qualifiers))

    def canonical_payload(self) -> dict[str, Any]:
        payload = {
            "schema_version": _required_text(
                self.schema_version,
                "schema_version",
                enum_like=False,
            ),
            "kind": _enum_text(self.kind, "kind"),
            "semantic_scope": _enum_text(self.semantic_scope, "semantic_scope"),
        }

        subject_ref = _optional_text(self.subject_ref, enum_like=False)
        operation = _optional_text(self.operation, enum_like=True)
        statement = _optional_text(self.normalized_statement, enum_like=False)
        qualifiers = _canonical_qualifiers(self.qualifiers)

        if subject_ref is not None:
            payload["subject_ref"] = subject_ref
        if operation is not None:
            payload["operation"] = operation
        if statement is not None:
            payload["normalized_statement"] = statement
        if qualifiers:
            payload["qualifiers"] = qualifiers

        _validate_required_fields(payload)
        _validate_scope_reference(payload)
        return _canonical_value(payload)


def canonical_claim_subject_text(subject: ClaimSubject) -> str:
    payload = subject.canonical_payload()
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def canonical_claim_subject_bytes(subject: ClaimSubject) -> bytes:
    return canonical_claim_subject_text(subject).encode("utf-8")


def derive_claim_id(subject: ClaimSubject) -> str:
    digest = hashlib.sha256(canonical_claim_subject_bytes(subject)).hexdigest()
    return f"{CLAIM_ID_PREFIX}{digest}"


def _normalize_text(value: str, *, enum_like: bool) -> str:
    text = unicodedata.normalize("NFC", value)
    text = _WHITESPACE_RE.sub(" ", text.strip())
    if enum_like:
        text = _SNAKE_BOUNDARY_RE.sub("_", text).strip("_").lower()
        text = _WHITESPACE_RE.sub("_", text)
    return text


def _enum_text(value: Any, field_name: str) -> str:
    if isinstance(value, Enum):
        value = value.value
    return _required_text(value, field_name, enum_like=True)


def _required_text(value: Any, field_name: str, *, enum_like: bool) -> str:
    if value is None:
        raise ClaimIdentityError(f"{field_name} cannot be null")
    text = _normalize_text(str(value), enum_like=enum_like)
    if not text:
        raise ClaimIdentityError(f"{field_name} cannot be empty")
    return text


def _optional_text(value: Any, *, enum_like: bool) -> str | None:
    if value is None:
        return None
    text = _normalize_text(str(value), enum_like=enum_like)
    return text or None


def _canonical_qualifiers(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, MappingABC):
        raise ClaimIdentityError("qualifiers must be a mapping")
    canonical = {}
    for key, item in value.items():
        canonical_key = _required_text(key, "qualifier key", enum_like=False)
        canonical_item = _canonical_value(item)
        if canonical_item is not None:
            canonical[canonical_key] = canonical_item
    return canonical


def _canonical_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Enum):
        return _normalize_text(value.value, enum_like=True)
    if isinstance(value, str):
        return _normalize_text(value, enum_like=False)
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        raise ClaimIdentityError("floating-point values are not valid in ClaimSubject")
    if isinstance(value, MappingABC):
        canonical = {}
        for key, item in value.items():
            canonical_key = _required_text(key, "mapping key", enum_like=False)
            canonical_item = _canonical_value(item)
            if canonical_item is not None:
                canonical[canonical_key] = canonical_item
        return canonical
    if isinstance(value, (list, tuple)):
        items = [_canonical_value(item) for item in value]
        items = [item for item in items if item is not None]
        return sorted(items, key=_canonical_sort_key)
    raise ClaimIdentityError(
        f"unsupported ClaimSubject value type: {type(value).__name__}"
    )


def _canonical_sort_key(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _validate_required_fields(payload: Mapping[str, Any]) -> None:
    kind = payload["kind"]
    required_by_kind = {
        ClaimKind.CANDIDATE_OPERATION.value: (
            "semantic_scope",
            "subject_ref",
            "operation",
        ),
        ClaimKind.CONCEPT_TRUTH.value: (
            "semantic_scope",
            "subject_ref",
            "normalized_statement",
        ),
        ClaimKind.CAPABILITY_STATEMENT.value: (
            "semantic_scope",
            "subject_ref",
            "normalized_statement",
        ),
        ClaimKind.CONTEXTUAL_ASSERTION.value: (
            "semantic_scope",
            "normalized_statement",
            "qualifiers",
        ),
    }
    required = required_by_kind.get(kind)
    if required is None:
        raise ClaimIdentityError(f"unsupported claim kind: {kind}")

    missing = [field_name for field_name in required if field_name not in payload]
    if missing:
        raise ClaimIdentityError(
            f"ambiguous ClaimSubject missing required fields: {', '.join(missing)}"
        )

    scope = payload["semantic_scope"]
    allowed_scopes = {item.value for item in SemanticScope}
    if scope not in allowed_scopes:
        raise ClaimIdentityError(f"unsupported semantic scope: {scope}")


def _validate_scope_reference(payload: Mapping[str, Any]) -> None:
    scope = payload["semantic_scope"]
    subject_ref = str(payload.get("subject_ref") or "")
    if scope not in {SemanticScope.CROSS_RUN.value, SemanticScope.GLOBAL.value}:
        return
    if subject_ref.lower().startswith(_RUN_LOCAL_REF_PREFIXES):
        raise ClaimIdentityError(
            "cross-run or global ClaimSubject requires durable semantic subject_ref"
        )


def _freeze_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, MappingABC):
        frozen = {
            key: _freeze_value(item)
            for key, item in value.items()
        }
        return MappingProxyType(frozen)
    if isinstance(value, list):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze_value(item) for item in value)
    return value


__all__ = [
    "CLAIM_ID_PREFIX",
    "CLAIM_SUBJECT_SCHEMA_VERSION",
    "ClaimIdentityError",
    "ClaimKind",
    "ClaimSubject",
    "SemanticScope",
    "canonical_claim_subject_bytes",
    "canonical_claim_subject_text",
    "derive_claim_id",
]
