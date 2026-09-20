"""Build a minimal connected hierarchy over registered runtime contexts."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from runtime.context.context_validator import validate_context_collection


ROOT_CONTEXT = "ROOT_CONTEXT"
KNOWN_CONTEXT_TYPES = {
    "PROCESS_CONTEXT",
    "SEMANTIC_CONTEXT",
    "CAUSAL_CONTEXT",
    "WORLD_CONTEXT",
}


class ContextHierarchyEngine:
    """Connect registered contexts to typed parent and child relations."""

    system_name = "context_hierarchy_engine"

    def build(self, contexts: Iterable[Mapping[str, Any]] | None) -> dict[str, Any]:
        contexts, telemetry = validate_context_collection(contexts)
        if not contexts:
            return {
                "system": self.system_name,
                "report_state": "final",
                "result_count": 0,
                "reason": (
                    "no_valid_contexts"
                    if telemetry["contexts_rejected"]
                    else "no_registered_contexts"
                ),
                **telemetry,
                "hierarchy_depth": 0,
                "context_hierarchy_size": 0,
                "hierarchy_connectivity": 0.0,
                "parent_contexts": {},
                "child_contexts": {},
                "dependency_links": [],
                "context_abstractions": [],
                "context_specializations": [],
            }

        nodes = {ROOT_CONTEXT}
        parent_contexts: dict[str, list[str]] = {}
        child_contexts: dict[str, list[str]] = {ROOT_CONTEXT: []}
        dependency_links: list[dict[str, Any]] = []
        abstractions: list[dict[str, str]] = []
        specializations: list[dict[str, str]] = []

        for context in contexts:
            context_id = str(context.get("context_id") or context.get("context_name"))
            context_type = str(context.get("context_type") or "SEMANTIC_CONTEXT")
            if context_type not in KNOWN_CONTEXT_TYPES:
                context_type = "SEMANTIC_CONTEXT"
            nodes.add(context_type)
            nodes.add(context_id)
            _link(parent_contexts, child_contexts, context_type, ROOT_CONTEXT)
            _link(parent_contexts, child_contexts, context_id, context_type)
            abstractions.append({
                "context_id": context_id,
                "abstracted_as": context_type,
            })
            specializations.append({
                "context_type": context_type,
                "specialized_by": context_id,
            })
            for dependency in _dependencies(context):
                dependency_links.append({
                    "source": context_id,
                    "target": str(dependency),
                    "relation": "depends_on",
                })

        edge_count = sum(len(children) for children in child_contexts.values())
        connectivity = round(edge_count / max(len(nodes) - 1, 1), 4)
        return {
            "system": self.system_name,
            "report_state": "final",
            "result_count": len(contexts),
            **telemetry,
            "hierarchy_depth": 3 if contexts else 0,
            "context_hierarchy_size": len(nodes),
            "hierarchy_connectivity": connectivity,
            "parent_contexts": parent_contexts,
            "child_contexts": child_contexts,
            "dependency_links": dependency_links,
            "context_abstractions": abstractions,
            "context_specializations": specializations,
        }


def _link(
    parent_contexts: dict[str, list[str]],
    child_contexts: dict[str, list[str]],
    child: str,
    parent: str,
) -> None:
    parent_contexts.setdefault(child, [])
    if parent not in parent_contexts[child]:
        parent_contexts[child].append(parent)
    child_contexts.setdefault(parent, [])
    if child not in child_contexts[parent]:
        child_contexts[parent].append(child)


def _dependencies(context: Mapping[str, Any]) -> list[Any]:
    dependency_chain = context.get("dependency_chain", [])
    if isinstance(dependency_chain, Mapping):
        dependency_chain = dependency_chain.get("chain", [])
    if isinstance(dependency_chain, list):
        return dependency_chain[:8]
    return []


context_hierarchy_engine = ContextHierarchyEngine()


__all__ = [
    "ContextHierarchyEngine",
    "context_hierarchy_engine",
    "ROOT_CONTEXT",
]
