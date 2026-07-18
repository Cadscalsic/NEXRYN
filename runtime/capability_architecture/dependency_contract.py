"""Capability and layer dependency contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DependencyContract:
    capability_dependencies: tuple[str, ...] = ()
    layer_dependencies: tuple[str, ...] = ()
    optional_dependencies: tuple[str, ...] = ()
    policy_dependencies: tuple[str, ...] = ()
    activation_dependencies: tuple[str, ...] = ()
    minimum_versions: dict[str, str] = field(default_factory=dict)
    compatibility_requirements: tuple[str, ...] = ()

    def all_required_capabilities(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((*self.capability_dependencies, *self.activation_dependencies)))

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability_dependencies": list(self.capability_dependencies),
            "layer_dependencies": list(self.layer_dependencies),
            "optional_dependencies": list(self.optional_dependencies),
            "policy_dependencies": list(self.policy_dependencies),
            "activation_dependencies": list(self.activation_dependencies),
            "minimum_versions": dict(self.minimum_versions),
            "compatibility_requirements": list(self.compatibility_requirements),
        }


__all__ = ["DependencyContract"]
