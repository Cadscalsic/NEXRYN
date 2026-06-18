"""Typed process dependency memory for Alpha 1.1.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp
from runtime.process.process_dependency_types import (
    ProcessDependencyType,
    normalize_dependency_type,
)


DEFAULT_TYPED_PROCESS_DEPENDENCIES = {
    "shape_preservation": [
        ("shape_preservation", "requires", "local_geometry_tracking", 0.92),
        ("local_geometry_tracking", "requires", "object_identity", 0.91),
        ("object_identity", "preserves", "topology_preservation", 0.90),
        ("topology_preservation", "requires", "connectivity_preservation", 0.90),
        ("connectivity_preservation", "preserves", "object_core", 0.88),
    ],
    "topology_preservation": [
        ("topology_preservation", "requires", "connectivity_preservation", 0.90),
        ("connectivity_preservation", "requires", "object_identity", 0.89),
        ("object_identity", "preserves", "object_core", 0.88),
        ("object_core", "enables", "shape_preservation", 0.86),
    ],
    "position_preservation": [
        ("position_preservation", "requires", "position_tracking", 0.90),
        ("position_tracking", "requires", "object_identity", 0.89),
        ("object_identity", "preserves", "object_core", 0.88),
        ("object_core", "enables", "spatial_reference_frame", 0.86),
    ],
    "color_preservation": [
        ("color_preservation", "requires", "color_state_tracking", 0.90),
        ("color_state_tracking", "requires", "object_identity", 0.89),
        ("object_identity", "preserves", "object_core", 0.88),
        ("object_core", "enables", "attribute_binding", 0.86),
    ],
    "growth": [
        ("growth", "requires", "identity_persistence", 0.91),
        ("growth", "preserves", "topology_preservation", 0.90),
        ("growth", "modifies", "area", 0.90),
        ("growth", "forbids", "identity_split", 0.94),
        ("growth", "constrains", "object_count_constant", 0.90),
        ("identity_persistence", "derives_from", "object_persistence", 0.92),
        ("object_persistence", "derives_from", "object_core", 0.91),
        ("object_core", "derives_from", "shape_preservation", 0.90),
    ],
    "replication": [
        ("replication", "requires", "identity_forking", 0.91),
        ("replication", "modifies", "object_count", 0.92),
        ("replication", "enables", "topology_splitting", 0.88),
        ("replication", "preserves", "local_shape", 0.88),
    ],
    "propagation": [
        ("propagation", "requires", "source_pattern_preserved", 0.89),
        ("propagation", "causes", "neighbor_state_change", 0.90),
        ("propagation", "constrains", "directional_motion", 0.88),
    ],
    "directional_motion": [
        ("directional_motion", "requires", "position_delta", 0.87),
        ("directional_motion", "modifies", "position", 0.89),
        ("directional_motion", "preserves", "object_identity", 0.88),
        ("directional_motion", "constrains", "direction_vector", 0.87),
    ],
    "topological_growth": [
        ("topological_growth", "derives_from", "growth", 0.88),
        ("topological_growth", "requires", "identity_persistence", 0.91),
        ("identity_persistence", "derives_from", "object_identity", 0.91),
        ("object_identity", "preserves", "topology_preservation", 0.90),
        ("topology_preservation", "requires", "connectivity_preservation", 0.90),
        ("topological_growth", "requires", "topology_anchor", 0.89),
        ("topological_growth", "modifies", "connectivity", 0.90),
        ("topological_growth", "preserves", "local_shape", 0.87),
        ("topological_growth", "constrains", "expanded_connectivity", 0.87),
    ],
    "size_preservation": [
        ("size_preservation", "requires", "object_extent_tracking", 0.90),
        ("object_extent_tracking", "requires", "object_identity", 0.89),
        ("object_identity", "preserves", "object_core", 0.88),
        ("object_core", "enables", "size_preservation", 0.86),
    ],
    "symbolic_remapping": [
        ("symbolic_remapping", "requires", "symbol_identity_tracking", 0.90),
        ("symbolic_remapping", "modifies", "symbol_value", 0.89),
        ("symbol_identity_tracking", "preserves", "mapping_domain", 0.88),
        ("mapping_domain", "enables", "mapping_consistency", 0.87),
    ],
    "density_preservation": [
        ("density_preservation", "requires", "density_ratio_tracking", 0.90),
        ("density_ratio_tracking", "requires", "occupied_cell_count", 0.88),
        ("occupied_cell_count", "preserves", "coverage_pattern", 0.87),
        ("coverage_pattern", "enables", "density_preservation", 0.86),
    ],
}


@dataclass(frozen=True)
class TypedProcessDependency:
    source: str
    dependency_type: str
    target: str
    confidence: float = 0.86
    process_family: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        source = str(self.source or "").strip()
        target = str(self.target or "").strip()
        if not source or not target:
            raise ValueError("typed process dependencies require source and target")
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "target", target)
        object.__setattr__(
            self,
            "dependency_type",
            normalize_dependency_type(self.dependency_type),
        )
        object.__setattr__(self, "confidence", clamp(self.confidence))
        object.__setattr__(
            self,
            "process_family",
            str(self.process_family or source).strip(),
        )
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    def as_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "relation": self.dependency_type,
            "typed_process_dependency": True,
        }


class TypedProcessDependencyMemory:
    """In-memory typed dependency store with process-relevant retrieval."""

    system_name = "typed_process_dependency_memory"

    def __init__(self, seed_defaults: bool = True):
        self._links: dict[str, list[TypedProcessDependency]] = {}
        if seed_defaults:
            self.ingest(DEFAULT_TYPED_PROCESS_DEPENDENCIES)
            self._ingest_core_defaults()

    @property
    def links_loaded(self) -> int:
        return sum(len(items) for items in self._links.values())

    def ingest(self, dependencies: Mapping[str, Iterable[Any]]) -> dict[str, Any]:
        ingested = 0
        for process_family, links in dependencies.items():
            for item in links or []:
                link = self._coerce(process_family, item)
                bucket = self._links.setdefault(link.process_family, [])
                if not any(
                    existing.source == link.source
                    and existing.target == link.target
                    and existing.dependency_type == link.dependency_type
                    for existing in bucket
                ):
                    bucket.append(link)
                    ingested += 1
        return {
            "system": self.system_name,
            "typed_process_dependencies": "enabled",
            "typed_process_dependencies_enabled": True,
            "process_dependency_links_ingested": ingested,
            "process_dependency_links_loaded": self.links_loaded,
        }

    def links_for(
        self,
        process_family: str,
        relevant_targets: Iterable[str] | None = None,
    ) -> list[TypedProcessDependency]:
        links = list(self._links.get(str(process_family or "").strip(), []))
        targets = {str(item) for item in relevant_targets or [] if item}
        if not targets:
            return links
        relevant = [
            link
            for link in links
            if link.target in targets or link.source in targets
        ]
        if len(relevant) / max(len(links), 1) >= 0.75:
            return relevant
        return links

    def all_links(self) -> list[TypedProcessDependency]:
        return [
            link
            for links in self._links.values()
            for link in links
        ]

    def resolve(
        self,
        process_family: str,
        relevant_targets: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        links = self.links_for(process_family, relevant_targets)
        confidences = [link.confidence for link in links]
        targets = [link.target for link in links]
        return {
            "system": self.system_name,
            "typed_process_dependencies": "enabled",
            "typed_process_dependencies_enabled": True,
            "concept": process_family,
            "process_family": process_family,
            "typed_dependency_relations": [
                link.as_dict() for link in links
            ],
            "typed_dependency_relation_count": len(links),
            "resolved_dependency_chain": [process_family, *targets],
            "missing_dependencies": [],
            "dependency_confidence": (
                round(sum(confidences) / len(confidences), 4)
                if confidences
                else 0.0
            ),
            "dependency_chain_depth": len(links),
            "dependency_chain_coverage": 1.0 if links else 0.0,
            "process_dependency_links_loaded": self.links_loaded,
            "process_dependency_links_used": len(links),
            "relevant_process_dependency_links": len(links),
            "dependency_type_coverage": sorted(
                {link.dependency_type for link in links}
            ),
        }

    def report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "typed_process_dependencies": "enabled",
            "typed_process_dependencies_enabled": True,
            "process_dependency_links_loaded": self.links_loaded,
            "process_families": sorted(self._links),
            "dependency_types": [
                item.value for item in ProcessDependencyType
            ],
            "process_dependencies": {
                process: [link.as_dict() for link in links]
                for process, links in sorted(self._links.items())
            },
        }

    def _coerce(self, process_family: str, item: Any) -> TypedProcessDependency:
        if isinstance(item, TypedProcessDependency):
            return item
        if isinstance(item, Mapping):
            return TypedProcessDependency(
                source=item.get("source") or process_family,
                dependency_type=(
                    item.get("dependency_type")
                    or item.get("relation")
                    or item.get("type")
                ),
                target=item.get("target"),
                confidence=item.get("confidence", 0.86),
                process_family=item.get("process_family") or process_family,
                metadata=dict(item.get("metadata", {}) or {}),
            )
        source, dependency_type, target, *rest = list(item)
        return TypedProcessDependency(
            source=source,
            dependency_type=dependency_type,
            target=target,
            confidence=rest[0] if rest else 0.86,
            process_family=process_family,
        )

    def _ingest_core_defaults(self) -> None:
        try:
            from core.dependency.process_dependency_memory import (
                DEFAULT_PROCESS_DEPENDENCY_CHAINS,
            )
        except Exception:
            return
        self.ingest(DEFAULT_PROCESS_DEPENDENCY_CHAINS)


__all__ = [
    "DEFAULT_TYPED_PROCESS_DEPENDENCIES",
    "TypedProcessDependency",
    "TypedProcessDependencyMemory",
]
