"""Immutable constitutional identity principles for NEXRYN."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class ConstitutionalPrinciple:
    name: str
    description: str


CORE_CONSTITUTIONAL_PRINCIPLES: tuple[ConstitutionalPrinciple, ...] = (
    ConstitutionalPrinciple(
        "truth_priority",
        "Truth governance remains prior to convenience, speed, and adaptation.",
    ),
    ConstitutionalPrinciple(
        "identity_continuity",
        "NEXRYN must preserve coherent identity across learning and repair.",
    ),
    ConstitutionalPrinciple(
        "anti_domination",
        "No strategy, module, or voting coalition may dominate the whole mind.",
    ),
    ConstitutionalPrinciple(
        "human_support_mission",
        "Cognitive growth remains aligned with supporting human users.",
    ),
    ConstitutionalPrinciple(
        "safe_adaptive_growth",
        "Evolution is permitted only through bounded, reviewable adaptation.",
    ),
    ConstitutionalPrinciple(
        "evidence_before_truth",
        "Claims require evidence before becoming treated as truth.",
    ),
    ConstitutionalPrinciple(
        "governance_before_commitment",
        "Durable cognitive commitments require governance evaluation first.",
    ),
    ConstitutionalPrinciple(
        "efficiency_without_forgetting",
        "Optimization must not erase memory, lineage, or validation context.",
    ),
)

LOCKED_CORE_PRINCIPLE_NAMES: tuple[str, ...] = tuple(
    principle.name
    for principle in CORE_CONSTITUTIONAL_PRINCIPLES
)

PROTECTED_CORE_NAMES: frozenset[str] = frozenset({
    "truth_priority",
    "identity_continuity",
    "anti_domination",
    "locked_truth_integrity",
    "human_support_mission",
    "evidence_before_truth",
})

CONSTITUTIONAL_IDENTITY: Mapping[str, ConstitutionalPrinciple] = MappingProxyType({
    principle.name: principle
    for principle in CORE_CONSTITUTIONAL_PRINCIPLES
})


def is_protected_core_name(name: object) -> bool:
    return str(name or "").strip().lower() in PROTECTED_CORE_NAMES


def protect_core(candidate: object) -> dict:
    if isinstance(candidate, dict):
        data = dict(candidate)
    else:
        data = {}
        for key in dir(candidate):
            if key.startswith("_"):
                continue
            item = getattr(candidate, key)
            if not callable(item):
                data[key] = item

    touched = set()
    for key in ("modifies", "targets", "overrides", "weakens"):
        values = data.get(key, []) or []
        if isinstance(values, str):
            values = [values]
        touched.update(str(value).strip().lower() for value in values)
    direct_names = set(str(key).lower() for key in data.keys())
    protected = sorted((touched | direct_names) & PROTECTED_CORE_NAMES)

    return {
        "protected_core_touched": bool(protected),
        "protected_principles": protected,
        "allowed": not protected,
        "reason": (
            "candidate_attempts_to_modify_protected_core"
            if protected
            else "protected_core_not_touched"
        ),
    }


__all__ = [
    "ConstitutionalPrinciple",
    "CORE_CONSTITUTIONAL_PRINCIPLES",
    "LOCKED_CORE_PRINCIPLE_NAMES",
    "PROTECTED_CORE_NAMES",
    "CONSTITUTIONAL_IDENTITY",
    "is_protected_core_name",
    "protect_core",
]
