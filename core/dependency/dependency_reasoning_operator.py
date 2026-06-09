"""Reason over semantic dependency signals as ordered causal chains."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from core.epistemic_models import clamp
from core.dependency.process_dependency_graph import ProcessDependencyGraph


@dataclass(frozen=True)
class DependencyChain:
    """A compact causal bridge from a source concept to a target concept."""

    source: str
    target: str
    confidence: float
    path: list[str]

    @property
    def nodes(self) -> list[str]:
        return [self.source, *self.path, self.target]

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "confidence": self.confidence,
            "path": list(self.path),
            "nodes": self.nodes,
            "chain_depth": max(len(self.nodes) - 1, 0),
        }

    def as_path_dict(self) -> dict[str, Any]:
        return {
            "root": self.source,
            "chain": [*self.path, self.target],
            "confidence": self.confidence,
            "nodes": self.nodes,
            "chain_depth": max(len(self.nodes) - 1, 0),
        }


class DependencyReasoningOperator:
    """Convert known semantic signals into explainable dependency chains."""

    PROCESS_CONCEPTS = {
        "growth",
        "propagation",
        "replication",
        "topological_growth",
        "directional_motion",
        "object_identity_preservation",
    }

    DUPLICATION_CHAIN = [
        "duplication",
        "identity_split",
        "object_count_increase",
        "topology_splitting",
        "color_reassigned",
    ]
    MERGE_CHAIN = [
        "object_convergence",
        "identity_merged",
        "object_count_decrease",
        "topology_compaction",
        "color_reassigned",
    ]
    CREATION_CHAIN = [
        "object_appearance",
        "identity_created",
        "object_count_increase",
        "scene_expansion",
    ]
    DESTRUCTION_CHAIN = [
        "object_disappearance",
        "identity_destroyed",
        "object_count_decrease",
        "scene_contraction",
    ]
    GROWTH_CHAIN = [
        "growth",
        "cell_count_increase",
        "topology_expansion",
        "local_shape",
        "shape_preservation",
    ]
    PROPAGATION_CHAIN = [
        "propagation",
        "source_pattern_preserved",
        "directional_motion",
        "position_preservation",
    ]
    REPLICATION_CHAIN = [
        "replication",
        "identity_split",
        "object_count_increase",
        "topology_splitting",
        "local_shape",
        "shape_preservation",
    ]
    IDENTITY_PRESERVATION_CHAIN = [
        "object_identity_preservation",
        "identity_preserved",
        "local_shape",
        "shape_preservation",
    ]

    IMPLIED_SIGNALS = {
        ("duplication", "identity_split"): "object_count_increase",
        ("identity_split", "topology_splitting"): "object_count_increase",
        ("object_convergence", "identity_merged"): "object_count_decrease",
        ("identity_merged", "topology_compaction"): "object_count_decrease",
        ("object_appearance", "identity_created"): "object_count_increase",
        ("object_disappearance", "identity_destroyed"): "object_count_decrease",
        ("growth", "topology_expansion"): "cell_count_increase",
        ("topology_expansion", "shape_preservation"): "local_shape",
        ("propagation", "directional_motion"): "source_pattern_preserved",
        ("replication", "identity_split"): "object_count_increase",
        ("topology_splitting", "shape_preservation"): "local_shape",
        ("object_identity_preservation", "shape_preservation"): "local_shape",
    }

    def __init__(
        self,
        process_dependency_graph: ProcessDependencyGraph | None = None,
    ) -> None:
        self.process_dependency_graph = (
            process_dependency_graph
            or ProcessDependencyGraph()
        )

    def reason(
        self,
        signals: Iterable[str],
        source: str | None = None,
        target: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build the strongest ordered dependency chain supported by signals."""

        observed = self._normalize_signals(signals)
        if not observed:
            return self._empty_report()

        process_memory_resolution = self._process_memory_resolution(
            observed,
            source=source,
        )
        chain_nodes = self._select_chain(observed, source=source, target=target)
        inferred = self._inferred_nodes(chain_nodes, observed)
        confidence = self._confidence(chain_nodes, observed, inferred, evidence)
        dependency_chain = DependencyChain(
            source=chain_nodes[0],
            target=chain_nodes[-1],
            confidence=confidence,
            path=chain_nodes[1:-1],
        )
        dependency_evidence = self._dependency_evidence(
            dependency_chain,
            observed=observed,
            inferred=inferred,
            evidence=evidence or {},
        )

        return {
            "system": "dependency_reasoning_operator",
            "reasoning_state": (
                "DEPENDENCY_CHAIN_REASONED"
                if len(chain_nodes) > 1
                else "INSUFFICIENT_DEPENDENCY_SIGNALS"
            ),
            "source": dependency_chain.source,
            "target": dependency_chain.target,
            "confidence": dependency_chain.confidence,
            "dependency_chain": dependency_chain.as_dict(),
            "dependency_path": dependency_chain.as_path_dict(),
            "chain_complete": len(chain_nodes) > 1,
            "observed_signals": observed,
            "inferred_signals": inferred,
            "dependency_evidence": dependency_evidence,
            "process_dependency_memory": process_memory_resolution,
            "process_dependency_links_loaded": process_memory_resolution.get(
                "process_dependency_links_loaded",
                0,
            ),
            "process_dependency_links_used": self._process_links_used(
                chain_nodes,
                process_memory_resolution,
            ),
            "dependency_chain_depth": dependency_chain.as_dict()["chain_depth"],
            "dependency_chain_coverage": self._chain_coverage(
                chain_nodes,
                observed,
                inferred,
            ),
            "recommended_action": (
                "INGEST_REASONED_DEPENDENCY_CHAIN"
                if confidence >= 0.80 and len(chain_nodes) > 1
                else "COLLECT_DEPENDENCY_REASONING_EVIDENCE"
            ),
        }

    def _normalize_signals(self, signals: Iterable[str]) -> list[str]:
        normalized = []
        for signal in signals:
            value = str(signal).strip()
            if value and value not in normalized:
                normalized.append(value)
        return normalized

    def _select_chain(
        self,
        observed: list[str],
        source: str | None = None,
        target: str | None = None,
    ) -> list[str]:
        canonical = self._canonical_chain(observed, source=source)
        expanded = list(canonical)
        filtered = [node for node in expanded if node in observed]
        for node in expanded:
            if node not in filtered and self._is_implied_between(node, expanded, observed):
                filtered.append(node)
        ordered = [node for node in expanded if node in filtered]

        if source and source in ordered:
            ordered = ordered[ordered.index(source):]
        if target and target in ordered:
            ordered = ordered[:ordered.index(target) + 1]
        if len(ordered) > 1:
            return ordered
        return observed[:1]

    def _canonical_chain(
        self,
        observed: list[str],
        source: str | None = None,
    ) -> list[str]:
        candidates = [
            self.DUPLICATION_CHAIN,
            self.MERGE_CHAIN,
            self.CREATION_CHAIN,
            self.DESTRUCTION_CHAIN,
            self.GROWTH_CHAIN,
            self.PROPAGATION_CHAIN,
            self.REPLICATION_CHAIN,
            self.IDENTITY_PRESERVATION_CHAIN,
        ]
        candidates.extend(self._process_memory_chains(observed, source=source))
        if source:
            candidates = [
                chain
                for chain in candidates
                if chain and chain[0] == source
            ] or candidates
        return max(
            candidates,
            key=lambda chain: (
                sum(1 for node in chain if node in observed),
                chain[0] in observed,
                len(chain),
            ),
        )

    def _process_memory_resolution(
        self,
        observed: list[str],
        source: str | None = None,
    ) -> dict[str, Any]:
        process = self._process_concept(observed, source=source)
        links_loaded = (
            self.process_dependency_graph
            .process_dependency_memory
            .links_loaded
        )
        if not process:
            return {
                "queried": False,
                "concept": None,
                "resolved_dependency_chain": [],
                "missing_dependencies": [],
                "dependency_confidence": 0.0,
                "process_dependency_links_loaded": links_loaded,
                "process_dependency_links_used": 0,
                "dependency_chain_depth": 0,
                "dependency_chain_coverage": 0.0,
            }
        resolution = self.process_dependency_graph.resolve_dependency_chain(
            process,
        )
        return {
            **resolution,
            "queried": True,
            "process_dependency_links_loaded": links_loaded,
        }

    def _process_memory_chains(
        self,
        observed: list[str],
        source: str | None = None,
    ) -> list[list[str]]:
        process = self._process_concept(observed, source=source)
        if not process:
            return []
        return self.process_dependency_graph.typed_chains_for(process)

    def _process_concept(
        self,
        observed: list[str],
        source: str | None = None,
    ) -> str | None:
        if source in self.PROCESS_CONCEPTS:
            return source
        return next(
            (
                signal
                for signal in observed
                if signal in self.PROCESS_CONCEPTS
            ),
            None,
        )

    def _chain_coverage(
        self,
        chain_nodes: list[str],
        observed: list[str],
        inferred: list[str],
    ) -> float:
        if not chain_nodes:
            return 0.0
        covered = len([node for node in chain_nodes if node in observed])
        covered += len([node for node in chain_nodes if node in inferred])
        return round(clamp(covered / len(chain_nodes)), 4)

    def _process_links_used(
        self,
        chain_nodes: list[str],
        process_memory_resolution: dict[str, Any],
    ) -> int:
        concept = process_memory_resolution.get("concept")
        if not concept:
            return 0
        relation_edges = {
            (relation.source, relation.target)
            for relation in self.process_dependency_graph.relations_for(concept)
        }
        return sum(
            1
            for source, target in zip(chain_nodes, chain_nodes[1:])
            if (source, target) in relation_edges
        )

    def _is_implied_between(
        self,
        node: str,
        chain: list[str],
        observed: list[str],
    ) -> bool:
        if node in observed:
            return True
        for (left, right), implied in self.IMPLIED_SIGNALS.items():
            if implied != node:
                continue
            return left in observed and right in observed and node in chain
        return False

    def _inferred_nodes(
        self,
        chain_nodes: list[str],
        observed: list[str],
    ) -> list[str]:
        return [
            node
            for node in chain_nodes
            if node not in observed
        ]

    def _confidence(
        self,
        chain_nodes: list[str],
        observed: list[str],
        inferred: list[str],
        evidence: dict[str, Any] | None,
    ) -> float:
        if len(chain_nodes) <= 1:
            return 0.0
        observed_count = len([
            node
            for node in chain_nodes
            if node in observed
        ])
        coverage = (
            observed_count + len(inferred) * 0.65
        ) / len(chain_nodes)
        inference_penalty = min(len(inferred) * 0.02, 0.08)
        context_confidence = self._read_evidence_score(
            evidence or {},
            [
                "context_confidence",
                "semantic_context_score",
                "context_hierarchy_score",
                "causal_graph_alignment",
            ],
            default=0.86,
        )
        return round(
            clamp(
                coverage * 0.56
                + context_confidence * 0.40
                + 0.08
                - inference_penalty
            ),
            4,
        )

    def _read_evidence_score(
        self,
        evidence: dict[str, Any],
        keys: list[str],
        default: float,
    ) -> float:
        values = []
        for key in keys:
            value = evidence.get(key)
            try:
                values.append(float(value))
            except Exception:
                continue
        if not values:
            return clamp(default)
        return clamp(sum(values) / len(values))

    def _dependency_evidence(
        self,
        dependency_chain: DependencyChain,
        observed: list[str],
        inferred: list[str],
        evidence: dict[str, Any],
    ) -> list[dict[str, Any]]:
        chain = dependency_chain.nodes
        dependencies = []
        for source, target in zip(chain, chain[1:]):
            dependencies.append({
                "source": source,
                "target": target,
                "relation": "causes",
                "confidence": dependency_chain.confidence,
                "dependency_type": "reasoned_dependency",
                "required": True,
                "supported": True,
                "transfer_success": True,
                "metadata": {
                    "operator": "dependency_reasoning_operator",
                    "chain": list(chain),
                    "observed_signals": list(observed),
                    "inferred_signals": list(inferred),
                    "evidence": dict(evidence),
                },
            })
        return dependencies

    def _empty_report(self) -> dict[str, Any]:
        return {
            "system": "dependency_reasoning_operator",
            "reasoning_state": "NO_DEPENDENCY_SIGNALS",
            "source": None,
            "target": None,
            "confidence": 0.0,
            "dependency_chain": None,
            "dependency_path": None,
            "chain_complete": False,
            "observed_signals": [],
            "inferred_signals": [],
            "dependency_evidence": [],
            "process_dependency_memory": {
                "queried": False,
                "concept": None,
                "resolved_dependency_chain": [],
                "missing_dependencies": [],
                "dependency_confidence": 0.0,
            },
            "process_dependency_links_loaded": (
                self.process_dependency_graph
                .process_dependency_memory
                .links_loaded
            ),
            "process_dependency_links_used": 0,
            "dependency_chain_depth": 0,
            "dependency_chain_coverage": 0.0,
            "recommended_action": "COLLECT_DEPENDENCY_REASONING_EVIDENCE",
        }


__all__ = [
    "DependencyChain",
    "DependencyReasoningOperator",
]
