from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from core.epistemic_models import clamp
from core.dependency.process_dependency_memory import (
    ProcessDependencyMemory,
    normalize_process_dependency_relation,
)


@dataclass(frozen=True)
class ProcessDependencyRelation:
    process: str
    source: str
    relation: str
    target: str
    confidence: float = 0.86

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "relation",
            normalize_process_dependency_relation(self.relation),
        )
        object.__setattr__(self, "confidence", clamp(self.confidence))

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_dependency(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "confidence": clamp(self.confidence),
            "dependency_type": "process_dependency",
            "required": self.relation in {"requires", "causes", "supports"},
            "supported": True,
            "transfer_success": True,
            "metadata": {
                "process_dependency_graph": True,
                "process": self.process,
                "relation": self.relation,
            },
        }


class ProcessDependencyGraph:
    """Typed dependency knowledge for process concepts."""

    PROCESS_RELATIONS = {
        "growth": [
            ("growth", "requires", "object_persistence", 0.91),
            ("object_persistence", "requires", "identity_continuity", 0.90),
            ("identity_continuity", "supports", "object_identity_preservation", 0.88),
            ("growth", "causes", "area_increase", 0.88),
            ("area_increase", "may_affect", "topology_change", 0.78),
            ("growth", "preserves", "object_core", 0.84),
            ("object_core", "supports", "object_identity_preservation", 0.86),
        ],
        "topological_growth": [
            ("topological_growth", "requires", "object_persistence", 0.90),
            ("topological_growth", "causes", "topology_expansion", 0.91),
            ("topology_expansion", "may_affect", "boundary_geometry", 0.80),
            ("topology_expansion", "preserves", "local_shape", 0.84),
            ("local_shape", "supports", "shape_preservation", 0.86),
        ],
        "duplication": [
            ("duplication", "causes", "identity_split", 0.92),
            ("identity_split", "causes", "object_count_increase", 0.90),
            ("object_count_increase", "enables", "replication", 0.86),
            ("replication", "may_cause", "topology_splitting", 0.82),
            ("topology_splitting", "preserves", "local_shape", 0.86),
            ("local_shape", "supports", "shape_preservation", 0.86),
            ("duplication", "may_affect", "color_assignment", 0.76),
        ],
        "replication": [
            ("replication", "requires", "source_pattern_preserved", 0.88),
            ("replication", "causes", "identity_split", 0.90),
            ("identity_split", "causes", "object_count_increase", 0.89),
            ("object_count_increase", "causes", "topology_splitting", 0.84),
            ("topology_splitting", "preserves", "local_shape", 0.86),
            ("local_shape", "supports", "shape_preservation", 0.84),
        ],
        "propagation": [
            ("propagation", "requires", "source_pattern_preserved", 0.88),
            ("source_pattern_preserved", "enables", "directional_motion", 0.86),
            ("directional_motion", "may_affect", "position", 0.80),
            ("source_pattern_preserved", "preserves", "local_shape", 0.82),
            ("position", "supports", "position_preservation", 0.82),
        ],
        "object_identity_preservation": [
            ("object_identity_preservation", "requires", "object_persistence", 0.92),
            ("object_persistence", "requires", "identity_continuity", 0.92),
            ("identity_continuity", "preserves", "object_core", 0.90),
            ("object_core", "supports", "shape_preservation", 0.86),
            ("object_core", "supports", "topology_preservation", 0.84),
        ],
        "directional_motion": [
            ("directional_motion", "requires", "position_delta", 0.86),
            ("directional_motion", "requires", "object_persistence", 0.84),
            ("position_delta", "causes", "position_change", 0.88),
            ("position_change", "supports", "propagation", 0.80),
        ],
    }

    def __init__(
        self,
        process_relations: dict[str, list[tuple[str, str, str, float]]] | None = None,
        process_dependency_memory: ProcessDependencyMemory | None = None,
    ):
        self.process_dependency_memory = (
            process_dependency_memory
            or ProcessDependencyMemory(seed_defaults=process_relations is None)
        )
        if process_relations is not None:
            self.process_dependency_memory.ingest_chains(
                process_relations,
                persist=False,
            )
        self.process_relations = {
            process: [
                (
                    link.source,
                    link.relation,
                    link.target,
                    link.confidence,
                )
                for link in self.process_dependency_memory.links_for(process)
            ]
            for process in self.process_dependency_memory.process_links
        } or self.PROCESS_RELATIONS

    def relations_for(self, process: str) -> list[ProcessDependencyRelation]:
        process = str(process or "").strip()
        memory_links = self.process_dependency_memory.links_for(process)
        if memory_links:
            return [
                ProcessDependencyRelation(
                    process=link.process,
                    source=link.source,
                    relation=link.relation,
                    target=link.target,
                    confidence=link.confidence,
                )
                for link in memory_links
            ]
        return [
            ProcessDependencyRelation(
                process=process,
                source=source,
                relation=relation,
                target=target,
                confidence=confidence,
            )
            for source, relation, target, confidence
            in self.process_relations.get(process, [])
        ]

    def dependencies_for(self, process: str) -> list[dict[str, Any]]:
        return [
            relation.as_dependency()
            for relation in self.relations_for(process)
        ]

    def resolve_dependency_chain(self, process: str) -> dict[str, Any]:
        return self.process_dependency_memory.resolve_chain(process)

    def chain_records_for(self, process: str) -> list[dict[str, Any]]:
        records = []
        for relation in self.relations_for(process):
            records.append({
                "source": relation.source,
                "target": relation.target,
                "signals": [relation.source, relation.target],
                "evidence": {
                    "confidence": relation.confidence,
                    "process": process,
                },
                "metadata": {
                    "process_dependency_graph": True,
                    "relation": relation.relation,
                },
            })
        for chain in self.typed_chains_for(process):
            records.append({
                "source": chain[0],
                "target": chain[-1],
                "signals": chain,
                "evidence": {
                    "confidence": self._chain_confidence(process, chain),
                    "process": process,
                },
                "metadata": {
                    "process_dependency_graph": True,
                    "relation": "typed_process_chain",
                },
            })
        return records

    def typed_chains_for(self, process: str) -> list[list[str]]:
        relations = self.relations_for(process)
        adjacency: dict[str, list[str]] = {}
        targets = set()
        for relation in relations:
            adjacency.setdefault(relation.source, []).append(relation.target)
            targets.add(relation.target)
        roots = [process]
        if process not in adjacency:
            roots = sorted(set(adjacency) - targets)
        chains = []
        for root in roots:
            self._walk_chains(root, adjacency, [root], chains)
        return [chain for chain in chains if len(chain) > 1]

    def _walk_chains(
        self,
        node: str,
        adjacency: dict[str, list[str]],
        path: list[str],
        chains: list[list[str]],
    ) -> None:
        children = adjacency.get(node, [])
        if not children:
            chains.append(path)
            return
        for child in children:
            if child in path:
                chains.append(path)
                continue
            self._walk_chains(child, adjacency, [*path, child], chains)

    def _chain_confidence(self, process: str, chain: list[str]) -> float:
        confidence_by_edge = {
            (relation.source, relation.target): relation.confidence
            for relation in self.relations_for(process)
        }
        scores = [
            confidence_by_edge.get((source, target), 0.86)
            for source, target in zip(chain, chain[1:])
        ]
        return round(sum(scores) / len(scores), 4) if scores else 0.0

    def build_report(self, processes: list[str] | None = None) -> dict[str, Any]:
        processes = processes or sorted(self.process_relations)
        reports = {}
        dependencies = []
        chain_records = []
        for process in processes:
            process_dependencies = self.dependencies_for(process)
            reports[process] = {
                "process": process,
                "relations": [
                    relation.as_dict()
                    for relation in self.relations_for(process)
                ],
                "typed_chains": self.typed_chains_for(process),
                "resolved_dependency_chain":
                self.resolve_dependency_chain(process),
                "dependency_count": len(process_dependencies),
            }
            dependencies.extend(process_dependencies)
            chain_records.extend(self.chain_records_for(process))
        return {
            "system": "process_dependency_graph",
            "process_count": len(reports),
            "processes": reports,
            "dependency_evidence": dependencies,
            "chain_records": chain_records,
            "process_dependency_graph_available": True,
            "process_dependency_memory":
            self.process_dependency_memory.report(),
            "process_dependency_links_loaded":
            self.process_dependency_memory.links_loaded,
        }


__all__ = [
    "ProcessDependencyGraph",
    "ProcessDependencyRelation",
]
