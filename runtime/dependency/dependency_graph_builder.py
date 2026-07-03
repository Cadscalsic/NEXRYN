"""Concept-driven dependency graph construction."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping


class DependencyGraphBuilder:
    """Build dependency links from discovered process-bearing concepts."""

    system_name = "dependency_graph_builder"

    CONCEPT_CHAINS = {
        "path_finding": [
            "goal",
            "reachability",
            "path_construction",
            "completion",
        ],
        "route_completion": [
            "start_state",
            "candidate_paths",
            "reachability_evaluation",
            "selected_path",
            "final_state",
        ],
        "bridge_creation": [
            "component_a",
            "connector",
            "component_b",
            "connected_components",
        ],
        "component_connection": [
            "component_a",
            "connector",
            "component_b",
            "connected_components",
        ],
        "connectivity_change": [
            "initial_connectivity",
            "connection_operation",
            "updated_connectivity",
        ],
        "topology_change": [
            "initial_topology",
            "topology_operation",
            "final_topology",
        ],
        "transformation_sequence": [
            "input_state",
            "transform_a",
            "transform_b",
            "output_state",
        ],
        "multi_step_reasoning": [
            "initial_state",
            "intermediate_state",
            "final_state",
        ],
        "gravity": [
            "object",
            "support",
            "fall",
            "rest_state",
        ],
        "relative_position": [
            "object",
            "spatial_reference",
            "relative_position",
        ],
        "spatial_relation": [
            "object",
            "reference_object",
            "spatial_relation",
        ],
    }

    PROCESS_CONCEPTS = {
        "path_finding": "topological_growth",
        "route_completion": "topological_growth",
        "bridge_creation": "topological_growth",
        "component_connection": "topological_growth",
        "connectivity_change": "topological_growth",
        "topology_change": "topological_growth",
        "transformation_sequence": "directional_motion",
        "multi_step_reasoning": "directional_motion",
        "gravity": "directional_motion",
        "relative_position": "directional_motion",
        "spatial_relation": "directional_motion",
    }

    CAUSAL_TRANSITIONS = {
        "path_finding": [
            ("start_state", "candidate_paths"),
            ("candidate_paths", "selected_path"),
            ("selected_path", "final_state"),
        ],
        "route_completion": [
            ("start_state", "candidate_paths"),
            ("reachability_evaluation", "selected_path"),
            ("selected_path", "final_state"),
        ],
        "bridge_creation": [
            ("disconnected_objects", "connection_strategy"),
            ("connection_strategy", "bridge_construction"),
            ("bridge_construction", "connected_objects"),
        ],
        "component_connection": [
            ("disconnected_components", "connector"),
            ("connector", "connected_components"),
        ],
        "gravity": [
            ("support_removed", "gravity_activated"),
            ("gravity_activated", "object_falls"),
            ("object_falls", "new_stable_position"),
        ],
        "transformation_sequence": [
            ("input_state", "transform_a"),
            ("transform_a", "transform_b"),
            ("transform_b", "output_state"),
        ],
    }

    def build(
        self,
        detected_concepts: list[str] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        concepts = self._normalize_concepts(detected_concepts or [])
        if not concepts:
            concepts = self._concepts_from_context(runtime_context)

        chains = []
        links = []
        nodes = []
        edges = []
        causal_contexts = []

        for concept in concepts:
            chain = self._chain_for(concept)
            if not chain:
                continue
            process_concept = self.PROCESS_CONCEPTS.get(concept, concept)
            chain_record = {
                "concept": concept,
                "process_concept": process_concept,
                "chain": chain,
                "dependency_depth": max(len(chain) - 1, 0),
                "dependency_confidence": self._confidence(concept, chain),
            }
            chains.append(chain_record)
            nodes.append({
                "id": concept,
                "concept": concept,
                "process_concept": process_concept,
                "name": concept,
            })
            for node in chain:
                nodes.append({
                    "id": f"{concept}:{node}",
                    "concept": concept,
                    "process_concept": process_concept,
                    "name": node,
                })
            if chain:
                root_link = {
                    "source": concept,
                    "target": chain[0],
                    "dependency_type": "requires",
                    "confidence": chain_record["dependency_confidence"],
                    "concept": concept,
                    "process_concept": process_concept,
                    "generated_by": self.system_name,
                }
                links.append(root_link)
                edges.append({
                    "source": concept,
                    "target": f"{concept}:{chain[0]}",
                    "relation": root_link["dependency_type"],
                    "confidence": root_link["confidence"],
                })
            for index in range(len(chain) - 1):
                source = chain[index]
                target = chain[index + 1]
                link = {
                    "source": source,
                    "target": target,
                    "dependency_type": self._relation_for(index),
                    "confidence": chain_record["dependency_confidence"],
                    "concept": concept,
                    "process_concept": process_concept,
                    "generated_by": self.system_name,
                }
                links.append(link)
                edges.append({
                    "source": f"{concept}:{source}",
                    "target": f"{concept}:{target}",
                    "relation": link["dependency_type"],
                    "confidence": link["confidence"],
                })
            causal_contexts.extend(
                self._causal_contexts_for(concept, process_concept)
            )

        depth = max(
            [chain.get("dependency_depth", 0) for chain in chains] or [0]
        )
        coverage = (
            round(len(chains) / max(len(concepts), 1), 4)
            if concepts
            else 0.0
        )
        confidence = (
            round(
                sum(chain["dependency_confidence"] for chain in chains)
                / len(chains),
                4,
            )
            if chains
            else 0.0
        )

        return {
            "system": self.system_name,
            "detected_concepts": concepts,
            "dependency_chains": chains,
            "dependency_links": links,
            "dependency_depth": depth,
            "dependency_coverage": coverage,
            "dependency_confidence": confidence,
            "dependency_graph": {
                "nodes": nodes,
                "edges": edges,
                "node_count": len(nodes),
                "edge_count": len(edges),
            },
            "causal_context_templates": causal_contexts,
            "timestamp": str(datetime.utcnow()),
        }

    def _normalize_concepts(self, concepts):
        normalized = []
        for concept in concepts:
            token = str(concept).strip().lower().replace("-", "_").replace(" ", "_")
            if token and token not in normalized:
                normalized.append(token)
        return normalized

    def _concepts_from_context(self, runtime_context):
        concepts = []

        def visit(value):
            if isinstance(value, str):
                token = value.lower().replace("-", "_").replace(" ", "_")
                if token in self.CONCEPT_CHAINS:
                    concepts.append(token)
            elif isinstance(value, Mapping):
                for item in value.values():
                    visit(item)
            elif isinstance(value, (list, tuple, set)):
                for item in value:
                    visit(item)

        for key in [
            "detected_concepts",
            "suspected_concepts",
            "semantic_abstractions",
            "concept_attribution_report",
            "tool_selection_report",
            "pre_reasoning_task_profile",
            "task_profile",
        ]:
            visit(runtime_context.get(key))
        return list(dict.fromkeys(concepts))

    def _chain_for(self, concept):
        if concept in self.CONCEPT_CHAINS:
            return list(self.CONCEPT_CHAINS[concept])
        if any(marker in concept for marker in ["path", "route", "bridge", "connect"]):
            return list(self.CONCEPT_CHAINS["path_finding"])
        if any(marker in concept for marker in ["sequence", "multi_step", "process"]):
            return list(self.CONCEPT_CHAINS["transformation_sequence"])
        if any(marker in concept for marker in ["topology", "growth"]):
            return list(self.CONCEPT_CHAINS["topology_change"])
        return []

    def _relation_for(self, index):
        relations = ["requires", "enables", "causes", "derives_from"]
        return relations[min(index, len(relations) - 1)]

    def _confidence(self, concept, chain):
        base = 0.82
        if concept in {
            "path_finding",
            "route_completion",
            "bridge_creation",
            "component_connection",
            "gravity",
        }:
            base = 0.90
        return round(min(base + max(len(chain) - 3, 0) * 0.02, 0.96), 4)

    def _causal_contexts_for(self, concept, process_concept):
        transitions = self.CAUSAL_TRANSITIONS.get(concept)
        if not transitions:
            chain = self._chain_for(concept)
            transitions = list(zip(chain, chain[1:]))
        contexts = []
        for cause, effect in transitions or []:
            contexts.append({
                "concept": concept,
                "process_concept": process_concept,
                "cause": cause,
                "effect": effect,
                "dependency_relationship": "causes",
                "state_transition": f"{cause}->{effect}",
                "causal_confidence": 0.86,
            })
        return contexts


dependency_graph_builder = DependencyGraphBuilder()


__all__ = [
    "DependencyGraphBuilder",
    "dependency_graph_builder",
]
