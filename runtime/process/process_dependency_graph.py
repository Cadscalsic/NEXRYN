"""Graph representation for typed process dependencies."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping


class ProcessDependencyGraph:
    """Directed typed dependency graph."""

    system_name = "process_dependency_graph"

    def __init__(self, links: Iterable[Mapping[str, Any]] | None = None):
        self.links = [dict(link) for link in links or []]
        self.adjacency: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for link in self.links:
            source = str(link.get("source", ""))
            if source:
                self.adjacency[source].append(link)

    def outgoing(self, node: str) -> list[dict[str, Any]]:
        return list(self.adjacency.get(str(node), []))

    def reachable_links(
        self,
        root: str,
        allowed_types: set[str] | None = None,
        max_depth: int = 8,
    ) -> list[dict[str, Any]]:
        allowed_types = allowed_types or set()
        seen_edges: set[tuple[str, str, str]] = set()
        result: list[dict[str, Any]] = []
        stack = [(str(root), 0)]
        seen_nodes = {str(root)}
        while stack:
            node, depth = stack.pop()
            if depth >= max_depth:
                continue
            for link in self.outgoing(node):
                dependency_type = str(link.get("dependency_type", ""))
                if allowed_types and dependency_type not in allowed_types:
                    continue
                edge = (
                    str(link.get("source")),
                    dependency_type,
                    str(link.get("target")),
                )
                if edge in seen_edges:
                    continue
                seen_edges.add(edge)
                result.append(link)
                target = str(link.get("target", ""))
                if target and target not in seen_nodes:
                    seen_nodes.add(target)
                    stack.append((target, depth + 1))
        return result

    def longest_chain(
        self,
        root: str,
        allowed_types: set[str] | None = None,
        max_depth: int = 8,
    ) -> tuple[list[str], list[dict[str, Any]]]:
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
                if len(candidate_edges) > len(best_edges):
                    best_path = candidate_path
                    best_edges = candidate_edges
            return best_path, best_edges

        return walk(str(root), [str(root)], [])


__all__ = ["ProcessDependencyGraph"]
