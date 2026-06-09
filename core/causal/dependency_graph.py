"""Compatibility facade for dependency graph cognition.

The implementation lives in ``dependency_graph_engine``. This module exposes
the architectural name used by the higher-level roadmap without duplicating
state or behavior.
"""

from core.causal.dependency_graph_engine import (
    DEFAULT_DEPENDENCY_GRAPH_PATH,
    DEPENDENCY_COHERENCE_REPORT,
    DEPENDENCY_GRAPH_REPORT,
    DEPENDENCY_PATH_REPORT,
    DependencyEdge,
    DependencyGraph,
    DependencyGraphEngine,
    DependencyNode,
    DependencyPath,
)


__all__ = [
    "DEFAULT_DEPENDENCY_GRAPH_PATH",
    "DEPENDENCY_COHERENCE_REPORT",
    "DEPENDENCY_GRAPH_REPORT",
    "DEPENDENCY_PATH_REPORT",
    "DependencyEdge",
    "DependencyGraph",
    "DependencyGraphEngine",
    "DependencyNode",
    "DependencyPath",
]
