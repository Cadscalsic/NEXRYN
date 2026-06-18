"""Canonical dependency types for process cognition."""

from __future__ import annotations

from enum import Enum


class ProcessDependencyType(str, Enum):
    REQUIRES = "requires"
    PRESERVES = "preserves"
    MODIFIES = "modifies"
    FORBIDS = "forbids"
    ENABLES = "enables"
    CAUSES = "causes"
    CONSTRAINS = "constrains"
    DERIVES_FROM = "derives_from"


SUPPORTED_PROCESS_DEPENDENCY_TYPES = {
    item.value for item in ProcessDependencyType
}

DEPENDENCY_TYPE_ALIASES = {
    "depends_on": ProcessDependencyType.REQUIRES.value,
    "depends": ProcessDependencyType.REQUIRES.value,
    "derived_from": ProcessDependencyType.DERIVES_FROM.value,
    "derived": ProcessDependencyType.DERIVES_FROM.value,
    "creates": ProcessDependencyType.CAUSES.value,
    "supports": ProcessDependencyType.ENABLES.value,
    "inhibits": ProcessDependencyType.FORBIDS.value,
    "splits": ProcessDependencyType.ENABLES.value,
    "may_cause": ProcessDependencyType.CAUSES.value,
    "may_affect": ProcessDependencyType.MODIFIES.value,
}

TRUTH_SUPPORTING_DEPENDENCY_TYPES = {
    ProcessDependencyType.REQUIRES.value,
    ProcessDependencyType.PRESERVES.value,
    ProcessDependencyType.MODIFIES.value,
    ProcessDependencyType.ENABLES.value,
    ProcessDependencyType.CAUSES.value,
    ProcessDependencyType.CONSTRAINS.value,
    ProcessDependencyType.DERIVES_FROM.value,
}

CONTRADICTION_DEPENDENCY_TYPES = {
    ProcessDependencyType.FORBIDS.value,
}


def normalize_dependency_type(value: object) -> str:
    dependency_type = str(value or "").strip().lower().replace(" ", "_")
    dependency_type = DEPENDENCY_TYPE_ALIASES.get(
        dependency_type,
        dependency_type,
    )
    if dependency_type not in SUPPORTED_PROCESS_DEPENDENCY_TYPES:
        raise ValueError(f"unsupported process dependency type: {value}")
    return dependency_type


__all__ = [
    "CONTRADICTION_DEPENDENCY_TYPES",
    "DEPENDENCY_TYPE_ALIASES",
    "ProcessDependencyType",
    "SUPPORTED_PROCESS_DEPENDENCY_TYPES",
    "TRUTH_SUPPORTING_DEPENDENCY_TYPES",
    "normalize_dependency_type",
]
