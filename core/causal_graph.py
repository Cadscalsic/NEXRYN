from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from enum import Enum

from core.epistemic_models import clamp
from core.perception.scene_graph_engine import SceneGraphEngine


class CausalNodeType(str, Enum):
    OBSERVATION = "OBSERVATION"
    CONCEPT = "CONCEPT"
    CONTEXT = "CONTEXT"
    CAUSE = "CAUSE"
    EFFECT = "EFFECT"
    TRUTH = "TRUTH"


class CausalRelationType(str, Enum):
    CAUSES = "causes"
    SUPPORTS = "supports"
    DEPENDS_ON = "depends_on"
    PRESERVES = "preserves"
    TRANSFORMS_INTO = "transforms_into"
    EXPLAINS = "explains"


@dataclass
class CausalNode:
    node_id: str
    node_type: str
    concept_name: str
    confidence: float = 0.0
    supporting_evidence: list = field(default_factory=list)
    originating_tasks: list = field(default_factory=list)

    def __post_init__(self):
        self.node_type = self.node_type.value if hasattr(
            self.node_type,
            "value",
        ) else str(self.node_type)
        if self.node_type not in {item.value for item in CausalNodeType}:
            raise ValueError(f"invalid causal node type: {self.node_type}")
        self.confidence = clamp(self.confidence)
        self.supporting_evidence = list(self.supporting_evidence or [])
        self.originating_tasks = sorted(
            str(item)
            for item in set(self.originating_tasks or [])
            if item is not None
        )

    def merge(self, other):
        self.confidence = max(self.confidence, clamp(other.confidence))
        for item in other.supporting_evidence:
            if item not in self.supporting_evidence:
                self.supporting_evidence.append(item)
        self.originating_tasks = sorted(
            str(item)
            for item in (
                set(self.originating_tasks) | set(other.originating_tasks)
            )
            if item is not None
        )

    def as_dict(self):
        return asdict(self)


@dataclass
class CausalRelation:
    source: str
    target: str
    relation_type: str
    confidence: float = 0.0

    def __post_init__(self):
        self.relation_type = self.relation_type.value if hasattr(
            self.relation_type,
            "value",
        ) else str(self.relation_type)
        if self.relation_type not in {
            item.value
            for item in CausalRelationType
        }:
            raise ValueError(
                f"invalid causal relation type: {self.relation_type}"
            )
        self.confidence = clamp(self.confidence)

    def as_dict(self):
        return asdict(self)


class CausalGraph:
    """Explicit cause -> context -> evidence -> effect graph."""

    def __init__(self):
        self.nodes = {}
        self.relations = []
        self._relation_index = {}
        self.scene_graph_engine = SceneGraphEngine()

    def add_node(
        self,
        node=None,
        node_id=None,
        node_type=None,
        concept_name=None,
        confidence=0.0,
        supporting_evidence=None,
        originating_tasks=None,
    ):
        if node is None:
            node = CausalNode(
                node_id=node_id,
                node_type=node_type,
                concept_name=concept_name,
                confidence=confidence,
                supporting_evidence=supporting_evidence or [],
                originating_tasks=originating_tasks or [],
            )
        elif isinstance(node, dict):
            node = CausalNode(**node)

        if node.node_id in self.nodes:
            self.nodes[node.node_id].merge(node)
        else:
            self.nodes[node.node_id] = node
        return self.nodes[node.node_id]

    def add_relation(
        self,
        relation=None,
        source=None,
        target=None,
        relation_type=None,
        confidence=0.0,
    ):
        if relation is None:
            relation = CausalRelation(
                source=source,
                target=target,
                relation_type=relation_type,
                confidence=confidence,
            )
        elif isinstance(relation, dict):
            relation = CausalRelation(**relation)

        key = (
            relation.source,
            relation.target,
            relation.relation_type,
        )
        if key in self._relation_index:
            index = self._relation_index[key]
            existing = self.relations[index]
            existing.confidence = max(
                existing.confidence,
                relation.confidence,
            )
            return existing
        self._relation_index[key] = len(self.relations)
        self.relations.append(relation)
        return relation

    def _node_id(self, node_type, concept_name, suffix=None):
        safe_concept = str(concept_name).strip().replace(" ", "_")
        safe_suffix = (
            str(suffix).strip().replace(" ", "_")
            if suffix is not None
            else None
        )
        return ":".join(
            item
            for item in [
                str(node_type).lower(),
                safe_concept,
                safe_suffix,
            ]
            if item
        )

    def _evidence_item(self, item):
        if hasattr(item, "as_dict"):
            item = item.as_dict()
        return dict(item) if isinstance(item, dict) else {"source": str(item)}

    def _context_grid(self, context, key):
        value = context.get(key)
        if value is None and isinstance(context.get("task"), dict):
            value = context["task"].get(key)
        return value

    def _scene_comparison(self, context):
        comparison = context.get("scene_graph_comparison")
        if isinstance(comparison, dict):
            return comparison
        input_grid = self._context_grid(context, "input_grid")
        output_grid = self._context_grid(context, "output_grid")
        if input_grid is None or output_grid is None:
            return {}
        try:
            return self.scene_graph_engine.compare_scene_graphs(
                input_grid,
                output_grid,
            )
        except (TypeError, ValueError, KeyError):
            return {}

    def _attach_scene_evidence(
        self,
        concept_name,
        concept_node,
        truth_node,
        context,
        observations,
        task_ids,
    ):
        comparison = self._scene_comparison(context)
        if not comparison:
            return []

        summary = comparison.get("summary", {})
        object_events = comparison.get("object_events", [])
        relation_changes = comparison.get("relation_changes", {})
        evidence_items = []

        if summary.get("object_level_ready"):
            evidence_items.append({
                "source": "scene_graph:object_level_ready",
                "support_score": 0.90,
                "contradiction_score": 0.0,
                "metadata": {"scene_summary": summary},
            })
        for event in object_events:
            evidence_items.append({
                "source": f"scene_graph:{event.get('event', 'object_event')}",
                "support_score": clamp(event.get("confidence", 0.82)),
                "contradiction_score": 0.0,
                "metadata": {"object_event": dict(event)},
            })
        for relation in relation_changes.get("relations_preserved", []):
            evidence_items.append({
                "source": f"scene_graph:relation_preserved:{relation}",
                "support_score": 0.88,
                "contradiction_score": 0.0,
                "metadata": {"relation": relation},
            })
        for relation in relation_changes.get("relations_added", []):
            evidence_items.append({
                "source": f"scene_graph:relation_added:{relation}",
                "support_score": 0.84,
                "contradiction_score": 0.0,
                "metadata": {"relation": relation},
            })

        if not evidence_items:
            return []

        scene_context = self.add_node(
            node_id=self._node_id("context", concept_name, "scene_graph"),
            node_type=CausalNodeType.CONTEXT,
            concept_name="scene_graph",
            confidence=0.90,
            supporting_evidence=evidence_items,
            originating_tasks=task_ids,
        )
        self.add_relation(
            source=concept_node.node_id,
            target=scene_context.node_id,
            relation_type=CausalRelationType.DEPENDS_ON,
            confidence=0.92,
        )
        self.add_relation(
            source=scene_context.node_id,
            target=truth_node.node_id,
            relation_type=CausalRelationType.SUPPORTS,
            confidence=0.90,
        )

        attached = []
        for index, item in enumerate(evidence_items):
            evidence_node = self.add_node(
                node_id=self._node_id(
                    "observation",
                    concept_name,
                    item["source"],
                ),
                node_type=CausalNodeType.OBSERVATION,
                concept_name=item["source"],
                confidence=item["support_score"],
                supporting_evidence=[item],
                originating_tasks=task_ids,
            )
            relation = self.add_relation(
                source=evidence_node.node_id,
                target=scene_context.node_id,
                relation_type=CausalRelationType.SUPPORTS,
                confidence=item["support_score"],
            )
            attached.append({
                "index": index,
                "node": evidence_node.as_dict(),
                "relation": relation.as_dict(),
            })

        observations.extend(evidence_items)
        return attached

    def build_causal_spine(
        self,
        concept_name,
        observations=None,
        truth_claim=None,
        confidence=0.0,
        originating_tasks=None,
        context=None,
    ):
        context = context if isinstance(context, dict) else {}
        observations = [
            self._evidence_item(item)
            for item in list(observations or [])
        ]
        if isinstance(originating_tasks, (str, int)):
            originating_tasks = [originating_tasks]
        task_ids = set(originating_tasks or [])
        for item in observations:
            metadata = item.get("metadata", {})
            task_id = item.get(
                "task_id",
                item.get("task", metadata.get("task_id")),
            )
            if task_id:
                task_ids.add(str(task_id))
        concept_id = self._node_id("concept", concept_name)
        truth_id = self._node_id("truth", concept_name)
        confidence = clamp(confidence)

        concept_node = self.add_node(
            node_id=concept_id,
            node_type=CausalNodeType.CONCEPT,
            concept_name=concept_name,
            confidence=confidence,
            supporting_evidence=observations,
            originating_tasks=task_ids,
        )
        truth_node = self.add_node(
            node_id=truth_id,
            node_type=CausalNodeType.TRUTH,
            concept_name=truth_claim or f"{concept_name} is stable",
            confidence=confidence,
            supporting_evidence=observations,
            originating_tasks=task_ids,
        )
        self.add_relation(
            source=concept_node.node_id,
            target=truth_node.node_id,
            relation_type=CausalRelationType.EXPLAINS,
            confidence=confidence,
        )

        if not observations:
            observations = [{
                "source": "runtime_observation",
                "support_score": confidence,
                "contradiction_score": 1.0 - confidence,
            }]
        for index, item in enumerate(observations):
            source = item.get("source", f"observation_{index}")
            metadata = item.get("metadata", {})
            task_id = item.get(
                "task_id",
                item.get("task", metadata.get("task_id", source)),
            )
            observation_id = self._node_id(
                "observation",
                concept_name,
                source,
            )
            observation_confidence = clamp(
                item.get(
                    "support_score",
                    item.get("reliability", confidence),
                )
            )
            observation_node = self.add_node(
                node_id=observation_id,
                node_type=CausalNodeType.OBSERVATION,
                concept_name=str(source),
                confidence=observation_confidence,
                supporting_evidence=[item],
                originating_tasks=[task_id],
            )
            self.add_relation(
                source=observation_node.node_id,
                target=concept_node.node_id,
                relation_type=CausalRelationType.SUPPORTS,
                confidence=observation_confidence,
            )

        scene_evidence = self._attach_scene_evidence(
            concept_name,
            concept_node,
            truth_node,
            context,
            observations,
            task_ids,
        )

        context_label = context.get(
            "causal_context",
            context.get("task_context"),
        )
        if context_label:
            context_id = self._node_id(
                "context",
                concept_name,
                context_label,
            )
            context_node = self.add_node(
                node_id=context_id,
                node_type=CausalNodeType.CONTEXT,
                concept_name=str(context_label),
                confidence=confidence,
                supporting_evidence=observations,
                originating_tasks=task_ids,
            )
            self.add_relation(
                source=concept_node.node_id,
                target=context_node.node_id,
                relation_type=CausalRelationType.DEPENDS_ON,
                confidence=confidence,
            )
            self.add_relation(
                source=context_node.node_id,
                target=truth_node.node_id,
                relation_type=CausalRelationType.SUPPORTS,
                confidence=confidence,
            )

        return {
            "concept_node": concept_node.as_dict(),
            "truth_node": truth_node.as_dict(),
            "scene_evidence": scene_evidence,
            "path": self.find_explanation_path(concept_node.node_id),
        }

    def _adjacency(self, reverse=False):
        adjacency = defaultdict(list)
        for relation in self.relations:
            source = relation.target if reverse else relation.source
            target = relation.source if reverse else relation.target
            adjacency[source].append((target, relation))
        return adjacency

    def get_causes(self, node_id):
        return [
            {
                "node": self.nodes[source].as_dict(),
                "relation": relation.as_dict(),
            }
            for source, relation in self._adjacency(reverse=True).get(
                node_id,
                [],
            )
            if source in self.nodes
        ]

    def get_effects(self, node_id):
        return [
            {
                "node": self.nodes[target].as_dict(),
                "relation": relation.as_dict(),
            }
            for target, relation in self._adjacency().get(node_id, [])
            if target in self.nodes
        ]

    def _nodes_for_concept(self, concept):
        return [
            node
            for node in self.nodes.values()
            if node.concept_name == concept
            or node.node_id.endswith(f":{concept}")
        ]

    def find_explanation_path(self, concept):
        concept_id = self._node_id("concept", concept)
        start_nodes = (
            [concept_id]
            if concept_id in self.nodes
            else [
                node.node_id
                for node in self._nodes_for_concept(concept)
                if node.node_type != CausalNodeType.TRUTH.value
            ]
        )
        if concept in self.nodes and concept not in start_nodes:
            start_nodes.append(concept)
        truth_nodes = {
            node.node_id
            for node in self.nodes.values()
            if node.node_type == CausalNodeType.TRUTH.value
            and (
                concept in node.node_id
                or concept in node.concept_name
            )
        }
        queue = deque((node_id, [node_id]) for node_id in start_nodes)
        visited = set()
        adjacency = self._adjacency()
        while queue:
            node_id, path = queue.popleft()
            if node_id in visited:
                continue
            visited.add(node_id)
            if node_id in truth_nodes and len(path) > 1:
                return path
            for target, _relation in adjacency.get(node_id, []):
                queue.append((target, [*path, target]))
        return start_nodes[:1]

    def _evidence_stats(self, concept):
        concept_nodes = self._nodes_for_concept(concept)
        evidence = []
        tasks = set()
        relation_confidences = []
        for node in concept_nodes:
            evidence.extend(node.supporting_evidence)
            tasks.update(node.originating_tasks)
            relation_confidences.extend([
                relation.confidence
                for source, relation in self._adjacency(reverse=True).get(
                    node.node_id,
                    [],
                )
                if source in self.nodes
            ])
        supports = [
            clamp(
                item.get(
                    "support_score",
                    item.get("reliability", item.get("confidence", 0.0)),
                )
            )
            for item in evidence
            if isinstance(item, dict)
        ]
        contradictions = [
            clamp(item.get("contradiction_score", 0.0))
            for item in evidence
            if isinstance(item, dict)
        ]
        return {
            "evidence": evidence,
            "tasks": sorted(task for task in tasks if task is not None),
            "supports": supports,
            "contradictions": contradictions,
            "relation_confidences": relation_confidences,
        }

    def compute_causal_alignment(self, concept):
        stats = self._evidence_stats(concept)
        evidence_count = len(stats["evidence"])
        evidence_consistency = (
            sum(stats["supports"]) / len(stats["supports"])
            if stats["supports"]
            else 0.0
        )
        task_count = len(stats["tasks"])
        cross_task_stability = clamp(
            task_count / 3.0
            if task_count
            else evidence_count / 3.0
        )
        contradiction_resistance = 1.0 - (
            sum(stats["contradictions"]) / len(stats["contradictions"])
            if stats["contradictions"]
            else 0.0
        )
        dependency_coherence = (
            sum(stats["relation_confidences"])
            / len(stats["relation_confidences"])
            if stats["relation_confidences"]
            else 0.0
        )
        alignment_score = clamp(
            (
                evidence_consistency
                + cross_task_stability
                + contradiction_resistance
                + dependency_coherence
            )
            / 4.0
        )
        return {
            "system": "causal_graph",
            "concept": concept,
            "alignment_score": alignment_score,
            "causal_spine_alignment": alignment_score,
            "components": {
                "evidence_consistency": clamp(evidence_consistency),
                "cross_task_stability": cross_task_stability,
                "contradiction_resistance":
                clamp(contradiction_resistance),
                "dependency_coherence": clamp(dependency_coherence),
            },
            "evidence_count": evidence_count,
            "originating_task_count": task_count,
            "explanation_path": self.find_explanation_path(concept),
            "alignment_ready": alignment_score >= 0.80,
        }

    def _cycle_nodes(self):
        adjacency = self._adjacency()
        visited = set()
        active = set()
        cycles = []

        def visit(node_id, path):
            if node_id in active:
                cycle = path[path.index(node_id):] if node_id in path else path
                cycles.append(cycle)
                return
            if node_id in visited:
                return
            visited.add(node_id)
            active.add(node_id)
            for target, relation in adjacency.get(node_id, []):
                if relation.relation_type in {
                    CausalRelationType.CAUSES.value,
                    CausalRelationType.DEPENDS_ON.value,
                    CausalRelationType.EXPLAINS.value,
                    CausalRelationType.SUPPORTS.value,
                }:
                    visit(target, [*path, target])
            active.remove(node_id)

        for node_id in self.nodes:
            visit(node_id, [node_id])
        return cycles

    def validate_chain(self, chain):
        if len(chain) < 2:
            return False
        relation_pairs = {
            (relation.source, relation.target)
            for relation in self.relations
        }
        return all(
            (source, target) in relation_pairs
            for source, target in zip(chain, chain[1:])
        )

    def validate_causal_graph(self):
        referenced = set()
        missing_relation_nodes = []
        for relation in self.relations:
            referenced.add(relation.source)
            referenced.add(relation.target)
            if (
                relation.source not in self.nodes
                or relation.target not in self.nodes
            ):
                missing_relation_nodes.append(relation.as_dict())

        disconnected_nodes = [
            node_id
            for node_id in self.nodes
            if node_id not in referenced and self.relations
        ]
        incoming = self._adjacency(reverse=True)
        outgoing = self._adjacency()
        unsupported_truths = [
            node.node_id
            for node in self.nodes.values()
            if node.node_type == CausalNodeType.TRUTH.value
            and not incoming.get(node.node_id)
        ]
        orphan_concepts = [
            node.node_id
            for node in self.nodes.values()
            if node.node_type == CausalNodeType.CONCEPT.value
            and not incoming.get(node.node_id)
            and not outgoing.get(node.node_id)
        ]
        invalid_cause_chains = [
            node.node_id
            for node in self.nodes.values()
            if node.node_type == CausalNodeType.TRUTH.value
            and not any(
                cause["node"]["node_type"]
                in [
                    CausalNodeType.CONCEPT.value,
                    CausalNodeType.CONTEXT.value,
                ]
                for cause in self.get_causes(node.node_id)
            )
        ]
        cycles = self._cycle_nodes()
        issues = {
            "disconnected_nodes": disconnected_nodes,
            "circular_dependencies": cycles,
            "unsupported_truths": unsupported_truths,
            "orphan_concepts": orphan_concepts,
            "invalid_cause_chains": invalid_cause_chains,
            "missing_relation_nodes": missing_relation_nodes,
        }
        passed = not any(issues.values())
        return {
            "system": "causal_graph",
            "validation_passed": passed,
            "validation_state": (
                "CAUSAL_GRAPH_VALIDATED"
                if passed
                else "CAUSAL_GRAPH_VALIDATION_REQUIRED"
            ),
            "node_count": len(self.nodes),
            "relation_count": len(self.relations),
            **issues,
        }

    def explain_truth(self, concept):
        alignment = self.compute_causal_alignment(concept)
        stats = self._evidence_stats(concept)
        contradiction_average = (
            sum(stats["contradictions"]) / len(stats["contradictions"])
            if stats["contradictions"]
            else 0.0
        )
        return {
            "concept": concept,
            "why": [
                f"observed in {alignment['originating_task_count']} tasks",
                "contradiction remained below threshold"
                if contradiction_average < 0.10
                else "contradiction requires review",
                "dependency coherence remained stable"
                if alignment["components"]["dependency_coherence"] >= 0.80
                else "dependency coherence requires more evidence",
                "causal explanation path is preserved"
                if alignment["explanation_path"]
                else "causal explanation path is missing",
            ],
            "causal_alignment": alignment,
            "explanation_path": alignment["explanation_path"],
        }

    def export_graph(self):
        return {
            "nodes": [
                node.as_dict()
                for node in self.nodes.values()
            ],
            "relations": [
                relation.as_dict()
                for relation in self.relations
            ],
        }


def compute_causal_alignment(concept, graph=None):
    graph = graph or CausalGraph()
    return graph.compute_causal_alignment(concept)["alignment_score"]


def validate_causal_graph(graph):
    graph = graph or CausalGraph()
    return graph.validate_causal_graph()


__all__ = [
    "CausalGraph",
    "CausalNode",
    "CausalNodeType",
    "CausalRelation",
    "CausalRelationType",
    "compute_causal_alignment",
    "validate_causal_graph",
]
