"""Layer dependency validation and activation ordering."""

from __future__ import annotations

from dataclasses import dataclass

from runtime.resource_governance.governor_registry import GovernorRegistry
from runtime.resource_governance.layer_state_registry import LayerState


@dataclass(frozen=True)
class DependencyResolution:
    activation_order: tuple[str, ...]
    missing_dependencies: tuple[str, ...] = ()
    cycle_detected: bool = False
    cycle_path: tuple[str, ...] = ()

    @property
    def approved(self) -> bool:
        return not self.missing_dependencies and not self.cycle_detected


class LayerDependencyResolver:
    def __init__(self, registry: GovernorRegistry, max_dependency_depth: int = 6):
        self.registry = registry
        self.max_dependency_depth = max_dependency_depth

    def resolve(self, layer_name: str, explicit_dependencies: tuple[str, ...] = ()) -> DependencyResolution:
        order: list[str] = []
        missing: list[str] = []
        visiting: list[str] = []
        visited: set[str] = set()

        def visit(name: str, depth: int) -> tuple[bool, tuple[str, ...]]:
            if depth > self.max_dependency_depth:
                missing.append(name)
                return False, ()
            if name in visiting:
                return False, tuple(visiting[visiting.index(name):] + [name])
            if name in visited:
                return True, ()
            state = self.registry.get_state(name)
            if state == LayerState.NOT_REGISTERED:
                missing.append(name)
                return False, ()
            if state == LayerState.BLOCKED:
                missing.append(name)
                return False, ()
            visiting.append(name)
            deps = self._dependencies_for(name)
            if name == layer_name:
                deps = tuple(dict.fromkeys((*deps, *explicit_dependencies)))
            for dep in deps:
                ok, cycle = visit(dep, depth + 1)
                if cycle:
                    return False, cycle
                if not ok:
                    return False, ()
            visiting.pop()
            visited.add(name)
            if name != layer_name:
                order.append(name)
            return True, ()

        ok, cycle = visit(str(layer_name), 0)
        return DependencyResolution(
            activation_order=tuple(order if ok else order),
            missing_dependencies=tuple(dict.fromkeys(missing)),
            cycle_detected=bool(cycle),
            cycle_path=cycle,
        )

    def _dependencies_for(self, layer_name: str) -> tuple[str, ...]:
        metadata = self.registry.state_registry.get_metadata(layer_name)
        return tuple(metadata.dependencies) if metadata is not None else ()


__all__ = [
    "DependencyResolution",
    "LayerDependencyResolver",
]
