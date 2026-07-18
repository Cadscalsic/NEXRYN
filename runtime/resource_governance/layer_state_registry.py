"""Canonical layer states and registration metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping


class LayerState(str, Enum):
    NOT_REGISTERED = "NOT_REGISTERED"
    REGISTERED = "REGISTERED"
    REQUIRED = "REQUIRED"
    ACTIVE = "ACTIVE"
    ON_DEMAND = "ON_DEMAND"
    DEFERRED = "DEFERRED"
    SUSPENDED = "SUSPENDED"
    BLOCKED = "BLOCKED"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class LayerExecutionCategory(str, Enum):
    CRITICAL_RUNTIME = "CRITICAL_RUNTIME"
    COGNITIVE_REASONING = "COGNITIVE_REASONING"
    COGNITIVE_MEMORY = "COGNITIVE_MEMORY"
    POST_SUCCESS = "POST_SUCCESS"
    MAINTENANCE = "MAINTENANCE"
    REPORTING = "REPORTING"
    DIAGNOSTIC = "DIAGNOSTIC"
    ARCHITECTURAL = "ARCHITECTURAL"


@dataclass(frozen=True)
class LayerMetadata:
    name: str
    description: str = ""
    dependencies: tuple[str, ...] = ()
    owner: str = "runtime"
    default_state: LayerState = LayerState.REGISTERED
    execution_category: LayerExecutionCategory = (
        LayerExecutionCategory.COGNITIVE_REASONING
    )
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        name: str,
        description: str = "",
        dependencies: Iterable[str] | None = None,
        owner: str = "runtime",
        default_state: str | LayerState = LayerState.REGISTERED,
        execution_category: str | LayerExecutionCategory = (
            LayerExecutionCategory.COGNITIVE_REASONING
        ),
        metadata: Mapping[str, Any] | None = None,
    ) -> "LayerMetadata":
        return cls(
            name=str(name),
            description=str(description or ""),
            dependencies=tuple(str(item) for item in (dependencies or ())),
            owner=str(owner or "runtime"),
            default_state=normalize_layer_state(default_state),
            execution_category=normalize_execution_category(execution_category),
            metadata=dict(metadata or {}),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "dependencies": list(self.dependencies),
            "owner": self.owner,
            "default_state": self.default_state.value,
            "execution_category": self.execution_category.value,
            "metadata": dict(self.metadata),
        }


def normalize_layer_state(state: str | LayerState | None) -> LayerState:
    if isinstance(state, LayerState):
        return state
    value = str(state or LayerState.REGISTERED.value).upper()
    return LayerState.__members__.get(value, LayerState.REGISTERED)


def normalize_execution_category(
    category: str | LayerExecutionCategory | None,
) -> LayerExecutionCategory:
    if isinstance(category, LayerExecutionCategory):
        return category
    value = str(category or LayerExecutionCategory.COGNITIVE_REASONING.value).upper()
    return LayerExecutionCategory.__members__.get(
        value,
        LayerExecutionCategory.COGNITIVE_REASONING,
    )


class LayerStateRegistry:
    def __init__(self):
        self._states: dict[str, LayerState] = {}
        self._metadata: dict[str, LayerMetadata] = {}

    def register_layer(self, metadata: LayerMetadata) -> LayerMetadata:
        self._metadata[metadata.name] = metadata
        self._states.setdefault(metadata.name, metadata.default_state)
        return metadata

    def set_state(self, layer_name: str, state: str | LayerState) -> LayerState:
        name = str(layer_name)
        if name not in self._metadata:
            return LayerState.NOT_REGISTERED
        normalized = normalize_layer_state(state)
        self._states[name] = normalized
        return normalized

    def get_state(self, layer_name: str) -> LayerState:
        return self._states.get(str(layer_name), LayerState.NOT_REGISTERED)

    def get_metadata(self, layer_name: str) -> LayerMetadata | None:
        return self._metadata.get(str(layer_name))

    def registered_layers(self) -> list[str]:
        return sorted(self._metadata)

    def metadata(self) -> dict[str, dict[str, Any]]:
        return {
            name: item.as_dict()
            for name, item in sorted(self._metadata.items())
        }

    def states(self) -> dict[str, str]:
        return {
            name: self.get_state(name).value
            for name in self.registered_layers()
        }

    def layers_by_state(self, state: str | LayerState) -> list[str]:
        normalized = normalize_layer_state(state)
        return [
            name
            for name in self.registered_layers()
            if self.get_state(name) == normalized
        ]


__all__ = [
    "LayerExecutionCategory",
    "LayerMetadata",
    "LayerState",
    "LayerStateRegistry",
    "normalize_execution_category",
    "normalize_layer_state",
]
