"""Structured dependency graph construction."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Mapping


NODE_FAMILIES = {
    "OBJECT",
    "CONCEPT",
    "STATE",
    "TRANSFORMATION",
    "GOAL",
    "CONDITION",
    "CONSTRAINT",
    "PROCESS_STEP",
}

EDGE_TYPES = {
    "requires",
    "enables",
    "depends_on",
    "precedes",
    "follows",
    "causes",
    "blocks",
    "supports",
    "produces",
    "transforms",
    "transforms_into",
    "connects",
}


@dataclass
class DependencyNode:
    node_id: str
    label: str
    node_family: str
    concept: str | None = None
    node_confidence: float = 0.82
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["id"] = self.node_id
        data["name"] = self.label
        data["type"] = self.node_family
        data["node_type"] = self.node_family
        data["confidence"] = round(float(self.node_confidence or 0.0), 4)
        data["node_confidence"] = data["confidence"]
        return data


@dataclass
class DependencyEdge:
    edge_id: str
    source: str
    target: str
    relationship: str
    concept: str | None = None
    edge_confidence: float = 0.82
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["id"] = self.edge_id
        data["relation"] = self.relationship
        data["dependency_type"] = self.relationship
        data["edge_type"] = self.relationship
        data["confidence"] = round(float(self.edge_confidence or 0.0), 4)
        data["edge_confidence"] = data["confidence"]
        return data


@dataclass
class DependencyGraph:
    graph_id: str
    root_concepts: list[str] = field(default_factory=list)
    nodes: dict[str, DependencyNode] = field(default_factory=dict)
    edges: list[DependencyEdge] = field(default_factory=list)
    graph_confidence: float = 0.0
    support_score: float = 0.0
    contradiction_score: float = 0.0
    graph_reuse_hits: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: DependencyNode) -> None:
        existing = self.nodes.get(node.node_id)
        if existing is None or node.node_confidence > existing.node_confidence:
            self.nodes[node.node_id] = node

    def add_edge(self, edge: DependencyEdge) -> None:
        if edge.relationship not in EDGE_TYPES:
            return
        if edge.source not in self.nodes or edge.target not in self.nodes:
            return
        key = (edge.source, edge.target, edge.relationship)
        if key not in {
            (item.source, item.target, item.relationship)
            for item in self.edges
        }:
            self.edges.append(edge)

    def depth(self) -> int:
        adjacency: dict[str, list[str]] = {}
        for edge in self.edges:
            adjacency.setdefault(edge.source, []).append(edge.target)

        def visit(node_id: str, path: set[str]) -> int:
            if node_id in path:
                return 0
            children = adjacency.get(node_id, [])
            if not children:
                return 0
            return 1 + max(visit(child, path | {node_id}) for child in children)

        return max((visit(node_id, set()) for node_id in self.nodes), default=0)

    def as_dict(self) -> dict[str, Any]:
        nodes = [node.as_dict() for node in self.nodes.values()]
        edges = [edge.as_dict() for edge in self.edges]
        return {
            "graph_id": self.graph_id,
            "root_concepts": list(self.root_concepts),
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "graph_depth": self.depth(),
            "graph_confidence": round(float(self.graph_confidence or 0.0), 4),
            "support_score": round(float(self.support_score or 0.0), 4),
            "contradiction_score": round(float(self.contradiction_score or 0.0), 4),
            "graph_reuse_hits": int(self.graph_reuse_hits or 0),
            "metadata": dict(self.metadata),
        }


class DependencyGraphBuilder:
    """Build dependency graphs from concepts, execution chains, and context."""

    system_name = "dependency_graph_builder"

    LEGACY_CHAINS = {
        "path_finding": ["goal", "reachability", "path_construction", "completion"],
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
        "gravity": ["object", "support", "fall", "rest_state"],
        "falling": ["unsupported_object", "fall", "rest_state"],
        "support": ["supported_object", "support_surface", "stable_state"],
        "collision": ["moving_object", "contact", "constraint", "rest_state"],
        "relative_position": ["object", "spatial_reference", "relative_position"],
        "spatial_relation": ["object", "reference_object", "spatial_relation"],
        "color_mapping": ["source_color", "mapping_rule", "target_color"],
        "symbolic_remapping": ["source_color", "mapping_rule", "target_color"],
    }

    GRAPH_CHAINS = {
        "gravity": ["unsupported_object", "falling", "collision", "rest_state"],
        "falling": ["unsupported_object", "falling", "collision", "rest_state"],
        "support": ["supported_object", "support_surface", "stable_state"],
        "collision": ["moving_object", "collision", "rest_state"],
        "path_finding": ["start", "reachable_nodes", "candidate_paths", "goal"],
        "route_completion": ["start", "reachable_nodes", "candidate_paths", "goal"],
        "bridge_creation": ["component_A", "connector", "component_B"],
        "component_connection": ["component_A", "connector", "component_B"],
        "transformation_sequence": [
            "input_state",
            "transformation_step",
            "output_state",
        ],
        "multi_step_reasoning": [
            "initial_state",
            "process_step",
            "intermediate_state",
            "final_state",
        ],
        "color_mapping": ["source_color", "mapping_rule", "target_color"],
        "symbolic_remapping": ["source_color", "mapping_rule", "target_color"],
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
        "falling": "directional_motion",
        "support": "directional_motion",
        "collision": "directional_motion",
        "relative_position": "directional_motion",
        "spatial_relation": "directional_motion",
        "color_mapping": "attribute_transformation",
        "symbolic_remapping": "attribute_transformation",
    }

    CAUSAL_TRANSITIONS = {
        "path_finding": [
            ("start", "reachable_nodes"),
            ("reachable_nodes", "candidate_paths"),
            ("candidate_paths", "goal"),
        ],
        "route_completion": [
            ("start", "reachable_nodes"),
            ("reachable_nodes", "candidate_paths"),
            ("candidate_paths", "goal"),
        ],
        "bridge_creation": [
            ("component_A", "connector"),
            ("connector", "component_B"),
        ],
        "component_connection": [
            ("component_A", "connector"),
            ("connector", "component_B"),
        ],
        "gravity": [
            ("support_removed", "gravity_activated"),
            ("gravity_activated", "object_falls"),
            ("object_falls", "new_stable_position"),
            ("unsupported_object", "falling"),
            ("falling", "collision"),
            ("collision", "rest_state"),
        ],
        "falling": [
            ("unsupported_object", "falling"),
            ("falling", "collision"),
            ("collision", "rest_state"),
        ],
        "support": [("support_surface", "stable_state")],
        "collision": [("moving_object", "collision"), ("collision", "rest_state")],
        "transformation_sequence": [
            ("input_state", "transformation_step"),
            ("transformation_step", "output_state"),
        ],
        "color_mapping": [
            ("source_color", "mapping_rule"),
            ("mapping_rule", "target_color"),
        ],
    }

    def build(
        self,
        detected_concepts: list[str] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
        dependency_outputs: list[Mapping[str, Any]] | None = None,
        reuse_graph: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        concepts = self._normalize_concepts(detected_concepts or [])
        concepts.extend(
            concept
            for concept in self._concepts_from_context(runtime_context)
            if concept not in concepts
        )
        concepts.extend(
            concept
            for concept in self._concepts_from_outputs(dependency_outputs or [])
            if concept not in concepts
        )

        graph = DependencyGraph(
            graph_id=self._graph_id(concepts, dependency_outputs or [], runtime_context),
            root_concepts=concepts,
            metadata={"generated_by": self.system_name},
        )
        chains = []
        links = []
        causal_contexts = []

        for concept in concepts:
            legacy_chain = self._legacy_chain_for(concept)
            graph_chain = self._graph_chain_for(
                concept,
                dependency_outputs or [],
                runtime_context,
            )
            if not graph_chain and not legacy_chain:
                continue
            if not legacy_chain:
                legacy_chain = list(graph_chain)
            process_concept = self.PROCESS_CONCEPTS.get(concept, concept)
            confidence = self._confidence(concept, graph_chain or legacy_chain)
            chains.append({
                "concept": concept,
                "process_concept": process_concept,
                "chain": list(legacy_chain),
                "graph_chain": list(graph_chain or legacy_chain),
                "dependency_depth": max(len(legacy_chain) - 1, 0),
                "dependency_confidence": confidence,
            })
            self._add_chain_to_graph(
                graph,
                concept,
                graph_chain or legacy_chain,
                confidence,
                process_concept,
            )
            links.extend(
                self._links_for_chain(
                    concept,
                    legacy_chain,
                    confidence,
                    process_concept,
                )
            )
            causal_contexts.extend(
                self._causal_contexts_for(concept, process_concept)
            )

        self._add_context_nodes(graph, runtime_context)
        self._apply_reuse(graph, reuse_graph)
        self._score_graph(graph)

        graph_dict = graph.as_dict()
        depth = max(
            [chain.get("dependency_depth", 0) for chain in chains]
            + [graph_dict.get("graph_depth", 0)]
        )
        coverage = round(len(chains) / max(len(concepts), 1), 4) if concepts else 0.0
        confidence = graph_dict["graph_confidence"]
        validation = self._validate_inline(graph_dict)

        report = {
            "system": self.system_name,
            "detected_concepts": concepts,
            "dependency_chains": chains,
            "dependency_links": links,
            "dependency_depth": depth,
            "dependency_coverage": coverage,
            "dependency_confidence": confidence,
            "dependency_graph": graph_dict,
            "dependency_graphs": [graph_dict] if graph_dict["node_count"] else [],
            "causal_context_templates": causal_contexts,
            "node_confidence": self._average(
                node["node_confidence"] for node in graph_dict["nodes"]
            ),
            "edge_confidence": self._average(
                edge["edge_confidence"] for edge in graph_dict["edges"]
            ),
            "graph_confidence": confidence,
            "support_score": graph_dict["support_score"],
            "contradiction_score": graph_dict["contradiction_score"],
            "dependency_graph_validation": validation,
            "DEPENDENCY_GRAPH_REPORT": {
                "graphs_generated": 1 if graph_dict["node_count"] else 0,
                "node_count": graph_dict["node_count"],
                "edge_count": graph_dict["edge_count"],
                "graph_depth": graph_dict["graph_depth"],
                "graph_confidence": confidence,
                "graph_reuse_hits": graph_dict["graph_reuse_hits"],
                "graph_failures": validation["graph_failures"],
                "orphan_nodes": validation["orphan_nodes"],
                "cycle_count": validation["cycle_count"],
            },
            "dependency_graph_count": 1 if graph_dict["node_count"] else 0,
            "dependency_node_count": graph_dict["node_count"],
            "dependency_edge_count": graph_dict["edge_count"],
            "dependency_graph_depth": graph_dict["graph_depth"],
            "dependency_graph_reuse_rate": (
                1.0 if graph_dict["graph_reuse_hits"] > 0 else 0.0
            ),
            "dependency_graph_validation_score": validation["validation_score"],
            "timestamp": str(datetime.utcnow()),
        }
        return report

    def _add_chain_to_graph(
        self,
        graph: DependencyGraph,
        concept: str,
        chain: list[str],
        confidence: float,
        process_concept: str,
    ) -> None:
        concept_node = DependencyNode(
            node_id=self._node_id(concept, concept),
            label=concept,
            node_family="CONCEPT",
            concept=concept,
            node_confidence=confidence,
            metadata={"process_concept": process_concept},
        )
        graph.add_node(concept_node)
        previous = concept_node.node_id
        for index, label in enumerate(chain):
            node = DependencyNode(
                node_id=self._node_id(concept, label),
                label=label,
                node_family=self._node_family(label, index, len(chain)),
                concept=concept,
                node_confidence=confidence,
                metadata={"position": index, "process_concept": process_concept},
            )
            graph.add_node(node)
            relationship = "requires" if index == 0 else self._relationship_for(
                chain[index - 1],
                label,
                index,
            )
            graph.add_edge(
                DependencyEdge(
                    edge_id=f"{previous}->{node.node_id}:{relationship}",
                    source=previous,
                    target=node.node_id,
                    relationship=relationship,
                    concept=concept,
                    edge_confidence=confidence,
                )
            )
            previous = node.node_id

    def _links_for_chain(
        self,
        concept: str,
        chain: list[str],
        confidence: float,
        process_concept: str,
    ) -> list[dict[str, Any]]:
        links = []
        if chain:
            links.append({
                "source": concept,
                "target": chain[0],
                "dependency_type": "requires",
                "confidence": confidence,
                "concept": concept,
                "process_concept": process_concept,
                "generated_by": self.system_name,
            })
        for index, source in enumerate(chain[:-1]):
            target = chain[index + 1]
            links.append({
                "source": source,
                "target": target,
                "dependency_type": self._relationship_for(source, target, index + 1),
                "confidence": confidence,
                "concept": concept,
                "process_concept": process_concept,
                "generated_by": self.system_name,
            })
        return links

    def _add_context_nodes(
        self,
        graph: DependencyGraph,
        runtime_context: Mapping[str, Any],
    ) -> None:
        for index, obj in enumerate(runtime_context.get("objects", []) or []):
            label = str(obj.get("id", f"object_{index}") if isinstance(obj, Mapping) else obj)
            graph.add_node(
                DependencyNode(
                    node_id=self._node_id("context", label),
                    label=label,
                    node_family="OBJECT",
                    node_confidence=0.78,
                    metadata={"source": "runtime_context"},
                )
            )
        transitions = runtime_context.get("state_transitions", []) or []
        for index, transition in enumerate(transitions):
            source, target = self._transition_pair(transition, index)
            source_id = self._node_id("state_transition", source)
            target_id = self._node_id("state_transition", target)
            graph.add_node(
                DependencyNode(source_id, source, "STATE", node_confidence=0.80)
            )
            graph.add_node(
                DependencyNode(target_id, target, "STATE", node_confidence=0.80)
            )
            graph.add_edge(
                DependencyEdge(
                    f"{source_id}->{target_id}:transforms",
                    source_id,
                    target_id,
                    "transforms",
                    edge_confidence=0.80,
                )
            )

    def _apply_reuse(
        self,
        graph: DependencyGraph,
        reuse_graph: Mapping[str, Any] | None,
    ) -> None:
        if not isinstance(reuse_graph, Mapping):
            return
        motif_nodes = reuse_graph.get("nodes", []) or []
        motif_edges = reuse_graph.get("edges", []) or []
        if not motif_nodes and not motif_edges:
            return
        graph.graph_reuse_hits += 1
        graph.metadata["reuse_source"] = reuse_graph.get("graph_id", "dependency_memory")
        for node in motif_nodes:
            if not isinstance(node, Mapping):
                continue
            label = str(node.get("label") or node.get("name") or node.get("id") or "")
            if not label:
                continue
            graph.add_node(
                DependencyNode(
                    node_id=self._node_id("reuse", label),
                    label=label,
                    node_family=str(node.get("node_family") or node.get("type") or "PROCESS_STEP"),
                    node_confidence=float(node.get("node_confidence", 0.76) or 0.76),
                    metadata={"reused": True},
                )
            )

    def _score_graph(self, graph: DependencyGraph) -> None:
        node_conf = self._average(node.node_confidence for node in graph.nodes.values())
        edge_conf = self._average(edge.edge_confidence for edge in graph.edges)
        connectivity = min(len(graph.edges) / max(len(graph.nodes) - 1, 1), 1.0)
        graph.support_score = round((node_conf + edge_conf + connectivity) / 3, 4)
        graph.contradiction_score = 0.0
        graph.graph_confidence = round(
            max(0.0, graph.support_score - graph.contradiction_score),
            4,
        )

    def _validate_inline(self, graph: Mapping[str, Any]) -> dict[str, Any]:
        nodes = {node["id"] for node in graph.get("nodes", [])}
        connected = set()
        broken = []
        for edge in graph.get("edges", []):
            source = edge.get("source")
            target = edge.get("target")
            if source not in nodes or target not in nodes:
                broken.append(edge)
            connected.update([source, target])
        root_ids = {
            self._node_id(concept, concept)
            for concept in graph.get("root_concepts", [])
        }
        orphan_nodes = sorted(nodes - connected - root_ids)
        cycles = self._cycle_count(graph)
        failures = len(broken) + len(orphan_nodes) + cycles
        denominator = max(len(nodes) + len(graph.get("edges", [])), 1)
        return {
            "connectivity_valid": not orphan_nodes and not broken,
            "consistency_valid": not broken,
            "cycle_count": cycles,
            "orphan_nodes": orphan_nodes,
            "broken_chains": len(broken),
            "missing_prerequisites": [],
            "invalid_transitions": [],
            "graph_failures": failures,
            "validation_score": round(max(0.0, 1.0 - failures / denominator), 4),
        }

    def _cycle_count(self, graph: Mapping[str, Any]) -> int:
        adjacency: dict[str, list[str]] = {}
        for edge in graph.get("edges", []) or []:
            adjacency.setdefault(edge.get("source"), []).append(edge.get("target"))
        cycles = 0
        visiting = set()
        visited = set()

        def visit(node_id: str) -> None:
            nonlocal cycles
            if node_id in visiting:
                cycles += 1
                return
            if node_id in visited:
                return
            visiting.add(node_id)
            for child in adjacency.get(node_id, []):
                visit(child)
            visiting.remove(node_id)
            visited.add(node_id)

        for node in graph.get("nodes", []) or []:
            visit(node.get("id"))
        return cycles

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
                if token in self.LEGACY_CHAINS or token in self.GRAPH_CHAINS:
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
            "color_mapping_report",
            "transformation_report",
            "state_transitions",
        ]:
            visit(runtime_context.get(key))
        return list(dict.fromkeys(concepts))

    def _concepts_from_outputs(self, dependency_outputs):
        concepts = []
        for output in dependency_outputs:
            if isinstance(output, Mapping) and output.get("concept"):
                concepts.append(
                    str(output["concept"]).lower().replace("-", "_").replace(" ", "_")
                )
        return list(dict.fromkeys(concepts))

    def _legacy_chain_for(self, concept):
        if concept in self.LEGACY_CHAINS:
            return list(self.LEGACY_CHAINS[concept])
        if any(marker in concept for marker in ["path", "route"]):
            return list(self.LEGACY_CHAINS["path_finding"])
        if any(marker in concept for marker in ["bridge", "connect"]):
            return list(self.LEGACY_CHAINS["bridge_creation"])
        if any(marker in concept for marker in ["sequence", "multi_step", "process"]):
            return list(self.LEGACY_CHAINS["transformation_sequence"])
        if any(marker in concept for marker in ["topology", "growth"]):
            return list(self.LEGACY_CHAINS["topology_change"])
        if any(marker in concept for marker in ["color", "mapping"]):
            return list(self.LEGACY_CHAINS["color_mapping"])
        return []

    def _graph_chain_for(self, concept, dependency_outputs, runtime_context):
        for output in dependency_outputs:
            if not isinstance(output, Mapping):
                continue
            if output.get("concept") == concept:
                chain = list(output.get("resolved_dependency_chain", []) or [])
                if chain and chain[0] == concept:
                    return chain[1:]
                return chain
        if concept in self.GRAPH_CHAINS:
            return list(self.GRAPH_CHAINS[concept])
        if any(marker in concept for marker in ["path", "route"]):
            return list(self.GRAPH_CHAINS["path_finding"])
        if any(marker in concept for marker in ["bridge", "connect"]):
            return list(self.GRAPH_CHAINS["bridge_creation"])
        if any(marker in concept for marker in ["color", "mapping"]):
            return list(self.GRAPH_CHAINS["color_mapping"])
        if runtime_context.get("state_transitions"):
            return ["input_state", "state_transition", "output_state"]
        return []

    def _relationship_for(self, source, target, index):
        text = f"{source} {target}".lower()
        if "color" in text or "transform" in text:
            return "transforms"
        if "connector" in text or "component" in text:
            return "connects"
        if "support" in text:
            return "supports"
        if "collision" in text or "fall" in text:
            return "causes"
        if "goal" in text:
            return "produces"
        return ["precedes", "enables", "causes"][min(index - 1, 2)]

    def _node_family(self, label, index, chain_length):
        text = str(label).lower()
        if index == chain_length - 1 and ("goal" in text or "completion" in text):
            return "GOAL"
        if "unsupported" in text or "support" in text or "reachable" in text:
            return "CONDITION"
        if "object" in text or "component" in text or "connector" in text:
            return "OBJECT"
        if "state" in text or text in {"start", "rest_state"}:
            return "STATE"
        if "transform" in text or "mapping" in text or "rule" in text:
            return "TRANSFORMATION"
        if "constraint" in text or "collision" in text:
            return "CONSTRAINT"
        if "goal" in text:
            return "GOAL"
        return "PROCESS_STEP"

    def _confidence(self, concept, chain):
        base = 0.82
        if concept in {
            "path_finding",
            "route_completion",
            "bridge_creation",
            "component_connection",
            "gravity",
            "falling",
            "support",
            "collision",
            "color_mapping",
        }:
            base = 0.90
        return round(min(base + max(len(chain) - 3, 0) * 0.02, 0.96), 4)

    def _causal_contexts_for(self, concept, process_concept):
        transitions = self.CAUSAL_TRANSITIONS.get(concept)
        if not transitions:
            chain = self._graph_chain_for(concept, [], {})
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

    def _transition_pair(self, transition, index):
        if isinstance(transition, Mapping):
            return (
                str(transition.get("from") or transition.get("source") or f"state_{index}"),
                str(transition.get("to") or transition.get("target") or f"state_{index + 1}"),
            )
        if isinstance(transition, (list, tuple)) and len(transition) >= 2:
            return str(transition[0]), str(transition[1])
        text = str(transition)
        if "->" in text:
            source, target = text.split("->", 1)
            return source.strip(), target.strip()
        return f"state_{index}", text

    def _node_id(self, concept, label):
        return f"{str(concept).lower()}:{str(label).strip().lower().replace(' ', '_')}"

    def _graph_id(self, concepts, dependency_outputs, runtime_context):
        parts = list(concepts)
        for output in dependency_outputs:
            if isinstance(output, Mapping):
                parts.extend(str(item) for item in output.get("resolved_dependency_chain", []) or [])
        if runtime_context.get("task_id"):
            parts.append(str(runtime_context["task_id"]))
        return "dependency_graph:" + "|".join(parts or ["empty"])

    def _average(self, values):
        numbers = [float(value or 0.0) for value in values]
        return round(sum(numbers) / len(numbers), 4) if numbers else 0.0


dependency_graph_builder = DependencyGraphBuilder()


__all__ = [
    "DependencyEdge",
    "DependencyGraph",
    "DependencyGraphBuilder",
    "DependencyNode",
    "EDGE_TYPES",
    "NODE_FAMILIES",
    "dependency_graph_builder",
]
