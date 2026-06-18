"""Executable graph engine for dependency reasoning."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Mapping


class DependencyGraphEngine:
    system_name = "dependency_graph_engine"

    def __init__(self, links: Iterable[Mapping] | None = None):
        self.links = [dict(link) for link in links or []]
        self.adjacency = defaultdict(list)
        for link in self.links:
            source = str(link.get("source", ""))
            if source:
                self.adjacency[source].append(link)

    def outgoing(self, node: str) -> list[dict]:
        return list(self.adjacency.get(str(node), []))

    def as_dict(self) -> dict:
        nodes = sorted(
            {
                str(link.get("source"))
                for link in self.links
                if link.get("source")
            }
            | {
                str(link.get("target"))
                for link in self.links
                if link.get("target")
            }
        )
        return {
            "system": self.system_name,
            "nodes": nodes,
            "edges": list(self.links),
            "node_count": len(nodes),
            "edge_count": len(self.links),
        }

    def longest_chain(
        self,
        root: str,
        allowed_types: set[str] | None = None,
        max_depth: int = 8,
    ) -> tuple[list[str], list[dict]]:
        allowed_types = allowed_types or set()

        def walk(node, path, edges):
            if len(edges) >= max_depth:
                return path, edges
            best_path = path
            best_edges = edges
            for link in self.outgoing(node):
                dependency_type = str(link.get("dependency_type", ""))
                target = str(link.get("target", ""))
                if allowed_types and dependency_type not in allowed_types:
                    continue
                if not target or target in path:
                    continue
                candidate_path, candidate_edges = walk(
                    target,
                    [*path, target],
                    [*edges, link],
                )
                if (
                    self._path_score(candidate_edges)
                    > self._path_score(best_edges)
                ):
                    best_path = candidate_path
                    best_edges = candidate_edges
            return best_path, best_edges

        return walk(str(root), [str(root)], [])

    def _path_score(self, edges):
        semantic_weight = {
            "requires": 1.0,
            "derives_from": 1.02,
            "preserves": 0.96,
            "causes": 0.92,
            "enables": 0.88,
            "constrains": 0.86,
            "modifies": 0.82,
        }
        depth_score = min(len(edges), 4) * 1.0
        first_edge_bonus = (
            0.12
            if edges and str(edges[0].get("dependency_type")) == "requires"
            else 0.0
        )
        target_bonus = sum(
            0.05
            for edge in edges
            if str(edge.get("target"))
            in {
                "object_identity",
                "topology_preservation",
                "connectivity_preservation",
            }
        )
        return depth_score + first_edge_bonus + target_bonus + sum(
            semantic_weight.get(str(edge.get("dependency_type")), 0.70)
            for edge in edges
        ) / max(len(edges), 1)


__all__ = ["DependencyGraphEngine"]
