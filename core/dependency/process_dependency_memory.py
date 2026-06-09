from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from core.epistemic_models import clamp


DEFAULT_PROCESS_DEPENDENCY_MEMORY_PATH = (
    Path("runtime") / "memory" / "storage" / "process_dependency_memory.json"
)

SUPPORTED_PROCESS_DEPENDENCY_RELATIONS = {
    "causes",
    "enables",
    "requires",
    "preserves",
    "modifies",
    "splits",
    "merges",
    "inhibits",
    "supports",
}

RELATION_ALIASES = {
    "may_cause": "causes",
    "may_affect": "modifies",
}

DEFAULT_PROCESS_DEPENDENCY_CHAINS = {
    "duplication": [
        ("duplication", "causes", "identity_split", 0.94),
        ("identity_split", "causes", "object_count_increase", 0.92),
        ("object_count_increase", "enables", "replication", 0.90),
        ("replication", "may_cause", "topological_growth", 0.86),
        ("replication", "causes", "topology_splitting", 0.86),
        ("topology_splitting", "preserves", "local_shape", 0.86),
        ("local_shape", "supports", "shape_preservation", 0.86),
        ("topological_growth", "supports", "growth", 0.88),
        ("growth", "requires", "object_identity_preservation", 0.91),
    ],
    "growth": [
        ("growth", "supports", "identity_continuity", 0.90),
        ("growth", "requires", "object_identity_preservation", 0.91),
        ("object_identity_preservation", "requires", "object_persistence", 0.92),
        ("object_persistence", "requires", "identity_continuity", 0.92),
        ("identity_continuity", "preserves", "object_core", 0.90),
        ("object_core", "supports", "shape_preservation", 0.86),
    ],
    "topological_growth": [
        ("topological_growth", "supports", "growth", 0.88),
        ("topological_growth", "modifies", "topology_expansion", 0.90),
        ("topology_expansion", "preserves", "local_shape", 0.86),
        ("local_shape", "supports", "shape_preservation", 0.86),
    ],
    "replication": [
        ("replication", "requires", "source_pattern_preserved", 0.89),
        ("replication", "causes", "identity_split", 0.91),
        ("identity_split", "causes", "object_count_increase", 0.92),
        ("object_count_increase", "enables", "topological_growth", 0.87),
        ("object_count_increase", "enables", "topology_splitting", 0.86),
        ("topology_splitting", "preserves", "local_shape", 0.86),
        ("local_shape", "supports", "shape_preservation", 0.84),
        ("topological_growth", "supports", "growth", 0.88),
    ],
    "propagation": [
        ("propagation", "requires", "source_pattern_preserved", 0.89),
        ("source_pattern_preserved", "enables", "directional_motion", 0.87),
        ("directional_motion", "modifies", "position_change", 0.88),
        ("position_change", "supports", "position_preservation", 0.84),
    ],
    "directional_motion": [
        ("directional_motion", "requires", "position_delta", 0.87),
        ("directional_motion", "requires", "object_identity_preservation", 0.86),
        ("position_delta", "causes", "position_change", 0.88),
        ("position_change", "supports", "propagation", 0.82),
    ],
    "object_identity_preservation": [
        ("object_identity_preservation", "requires", "object_persistence", 0.92),
        ("object_persistence", "requires", "identity_continuity", 0.92),
        ("identity_continuity", "preserves", "object_core", 0.90),
        ("object_core", "supports", "shape_preservation", 0.86),
        ("object_core", "supports", "topology_preservation", 0.84),
    ],
}


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_process_dependency_relation(relation: Any) -> str:
    value = str(relation or "").strip().lower()
    value = RELATION_ALIASES.get(value, value)
    if value not in SUPPORTED_PROCESS_DEPENDENCY_RELATIONS:
        raise ValueError(f"unsupported process dependency relation: {relation}")
    return value


@dataclass(frozen=True)
class ProcessDependencyLink:
    source: str
    relation: str
    target: str
    confidence: float = 0.86
    process: str = ""
    original_relation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        source = str(self.source or "").strip()
        target = str(self.target or "").strip()
        if not source or not target:
            raise ValueError("process dependency links require source and target")
        relation = normalize_process_dependency_relation(self.relation)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "target", target)
        object.__setattr__(self, "relation", relation)
        object.__setattr__(self, "confidence", clamp(self.confidence))
        object.__setattr__(self, "process", str(self.process or source).strip())
        object.__setattr__(
            self,
            "original_relation",
            str(self.original_relation or self.relation).strip(),
        )
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_dependency(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "confidence": self.confidence,
            "dependency_type": "typed_process_dependency_memory",
            "required": self.relation in {"causes", "requires", "supports"},
            "supported": True,
            "transfer_success": True,
            "metadata": {
                **self.metadata,
                "typed_process_dependency_memory": True,
                "process": self.process,
                "relation": self.relation,
                "original_relation": self.original_relation,
            },
        }


class ProcessDependencyMemory:
    """Persistent typed memory for causal process dependency chains."""

    def __init__(
        self,
        storage_path: str | Path | None = None,
        seed_defaults: bool = True,
    ) -> None:
        self.storage_path = Path(storage_path) if storage_path else None
        self.process_links: dict[str, list[ProcessDependencyLink]] = {}
        self.loaded_from_storage = False
        if seed_defaults:
            self.ingest_chains(DEFAULT_PROCESS_DEPENDENCY_CHAINS, persist=False)
        self._load()

    @property
    def links_loaded(self) -> int:
        return sum(len(links) for links in self.process_links.values())

    def _load(self) -> None:
        if self.storage_path is None or not self.storage_path.exists():
            return
        with self.storage_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        chains = payload.get("process_chains", payload.get("processes", {}))
        self.ingest_chains(chains, persist=False)
        self.loaded_from_storage = True

    def persist(self) -> None:
        if self.storage_path is None:
            return
        temporary_path = self.storage_path.with_suffix(
            f"{self.storage_path.suffix}.tmp"
        )
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(self.report(), file, indent=2, sort_keys=True)
            temporary_path.replace(self.storage_path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    def ingest_chains(
        self,
        chains: dict[str, Iterable[Any]] | Iterable[dict[str, Any]],
        persist: bool = True,
    ) -> dict[str, Any]:
        ingested = 0
        for process, links in self._iter_process_links(chains):
            for item in links:
                link = self._coerce_link(process, item)
                bucket = self.process_links.setdefault(link.process, [])
                if not any(
                    existing.source == link.source
                    and existing.target == link.target
                    and existing.relation == link.relation
                    for existing in bucket
                ):
                    bucket.append(link)
                    ingested += 1
        if persist:
            self.persist()
        return {
            "system": "process_dependency_memory",
            "ingested_links": ingested,
            "process_dependency_links_loaded": self.links_loaded,
        }

    def links_for(self, process: str) -> list[ProcessDependencyLink]:
        process = str(process or "").strip()
        return list(self.process_links.get(process, []))

    def dependencies_for(self, process: str) -> list[dict[str, Any]]:
        return [link.as_dependency() for link in self.links_for(process)]

    def chains_for(self, process: str) -> list[list[str]]:
        links = self.links_for(process)
        adjacency: dict[str, list[str]] = {}
        targets = set()
        for link in links:
            adjacency.setdefault(link.source, []).append(link.target)
            targets.add(link.target)
        roots = [process] if process in adjacency else sorted(set(adjacency) - targets)
        chains: list[list[str]] = []
        for root in roots:
            self._walk(root, adjacency, [root], chains)
        return [chain for chain in chains if len(chain) > 1]

    def resolve_chain(self, concept: str) -> dict[str, Any]:
        chains = self.chains_for(concept)
        best_chain = max(chains, key=len, default=[])
        expected = {
            link.target
            for link in self.links_for(concept)
            if link.source == concept and link.relation in {"causes", "requires", "supports"}
        }
        present = set(best_chain[1:])
        missing = sorted(expected - present)
        confidences = [link.confidence for link in self.links_for(concept)]
        confidence = (
            round(sum(confidences) / len(confidences), 4)
            if confidences
            else 0.0
        )
        return {
            "concept": concept,
            "resolved_dependency_chain": best_chain,
            "missing_dependencies": missing,
            "dependency_confidence": confidence,
            "dependency_chain_depth": max(len(best_chain) - 1, 0),
            "dependency_chain_coverage": (
                round((len(present) - len(missing)) / max(len(present), 1), 4)
                if best_chain
                else 0.0
            ),
            "process_dependency_links_used": max(len(best_chain) - 1, 0),
        }

    def report(self) -> dict[str, Any]:
        return {
            "system": "process_dependency_memory",
            "schema_version": 1,
            "generated_at": _timestamp(),
            "supported_relations": sorted(SUPPORTED_PROCESS_DEPENDENCY_RELATIONS),
            "relation_aliases": dict(RELATION_ALIASES),
            "process_dependency_links_loaded": self.links_loaded,
            "loaded_from_storage": self.loaded_from_storage,
            "storage_path": str(self.storage_path) if self.storage_path else None,
            "process_chains": {
                process: [link.as_dict() for link in links]
                for process, links in sorted(self.process_links.items())
            },
        }

    def _iter_process_links(self, chains: Any) -> Iterable[tuple[str, Iterable[Any]]]:
        if isinstance(chains, dict):
            for process, links in chains.items():
                yield str(process), links or []
            return
        for record in list(chains or []):
            if not isinstance(record, dict):
                continue
            process = record.get("process") or record.get("source")
            links = record.get("links") or record.get("relations") or [record]
            yield str(process or ""), links

    def _coerce_link(self, process: str, item: Any) -> ProcessDependencyLink:
        if isinstance(item, ProcessDependencyLink):
            return item
        if isinstance(item, dict):
            return ProcessDependencyLink(
                process=item.get("process") or process,
                source=item.get("source"),
                relation=item.get("relation"),
                original_relation=item.get("original_relation") or item.get("relation"),
                target=item.get("target"),
                confidence=item.get("confidence", 0.86),
                metadata=item.get("metadata", {}),
            )
        source, relation, target, *rest = list(item)
        return ProcessDependencyLink(
            process=process,
            source=source,
            relation=relation,
            original_relation=relation,
            target=target,
            confidence=rest[0] if rest else 0.86,
        )

    def _walk(
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
            self._walk(child, adjacency, [*path, child], chains)


__all__ = [
    "DEFAULT_PROCESS_DEPENDENCY_MEMORY_PATH",
    "ProcessDependencyLink",
    "ProcessDependencyMemory",
    "RELATION_ALIASES",
    "SUPPORTED_PROCESS_DEPENDENCY_RELATIONS",
    "normalize_process_dependency_relation",
]
