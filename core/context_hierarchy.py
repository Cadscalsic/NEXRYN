from dataclasses import dataclass, field

from core.context_discovery import ContextDescriptor
from core.epistemic_models import clamp


def _normalize(value, default="unknown"):
    if value is None:
        return default
    return str(value).strip().lower().replace(" ", "_") or default


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _signature(context):
    if isinstance(context, ContextDescriptor):
        return dict(context.features or {})
    if not isinstance(context, dict):
        return {}
    if isinstance(context.get("context_signature"), dict):
        return dict(context["context_signature"])
    if isinstance(context.get("signature"), dict):
        return dict(context["signature"])
    discovered = context.get("discovered_context", {})
    if isinstance(discovered, dict):
        features = discovered.get("features", {})
        if isinstance(features, dict):
            return dict(features)
    features = context.get("features", {})
    if isinstance(features, dict):
        return dict(features)
    return dict(context)


def _context_name(context):
    if isinstance(context, ContextNode):
        return context.context_name
    if isinstance(context, ContextDescriptor):
        return context.context_name
    if isinstance(context, str):
        return _normalize(context)
    if isinstance(context, dict):
        signature = _signature(context)
        return _normalize(
            context.get(
                "context_name",
                context.get(
                    "transformation_family",
                    signature.get("transformation_family"),
                ),
            )
        )
    return "unknown"


def _confidence(context):
    if isinstance(context, ContextNode):
        return context.confidence
    if isinstance(context, ContextDescriptor):
        return context.confidence
    if isinstance(context, dict):
        return clamp(
            context.get(
                "confidence",
                _signature(context).get("confidence", 0.0),
            )
        )
    return 0.0


def _tasks(context):
    if isinstance(context, ContextNode):
        return list(context.originating_tasks)
    if isinstance(context, ContextDescriptor):
        return list(context.originating_tasks)
    if isinstance(context, dict):
        return _as_list(
            context.get(
                "originating_tasks",
                context.get("task_ids", context.get("task")),
            )
        )
    return []


@dataclass
class ContextNode:
    context_id: str
    context_name: str
    confidence: float = 0.0
    stability: float = 0.0
    parent_context: str = None
    child_contexts: list = field(default_factory=list)
    originating_tasks: list = field(default_factory=list)
    inherited_features: list = field(default_factory=list)
    features: dict = field(default_factory=dict)

    def __post_init__(self):
        self.context_name = _normalize(self.context_name)
        self.context_id = self.context_id or f"context:{self.context_name}"
        self.confidence = clamp(self.confidence)
        self.stability = clamp(self.stability or self.confidence)
        self.originating_tasks = sorted(set(self.originating_tasks or []))
        self.child_contexts = sorted(set(self.child_contexts or []))

    def add_child(self, child):
        child_id = child.context_id if isinstance(child, ContextNode) else child
        child_id = _normalize(child_id)
        if child_id not in self.child_contexts:
            self.child_contexts.append(child_id)
            self.child_contexts.sort()
        return self

    def set_parent(self, parent):
        self.parent_context = (
            parent.context_id if isinstance(parent, ContextNode) else parent
        )
        self.parent_context = _normalize(self.parent_context)
        return self

    def get_ancestors(self, hierarchy=None):
        ancestors = []
        current = self.parent_context
        seen = set()
        while current and current not in seen:
            seen.add(current)
            ancestors.append(current)
            if hierarchy is None:
                break
            parent = hierarchy.nodes.get(current)
            current = parent.parent_context if parent else None
        return ancestors

    def get_descendants(self, hierarchy=None):
        descendants = []
        stack = list(self.child_contexts)
        seen = set()
        while stack:
            child_id = stack.pop(0)
            if child_id in seen:
                continue
            seen.add(child_id)
            descendants.append(child_id)
            if hierarchy is not None and child_id in hierarchy.nodes:
                stack.extend(hierarchy.nodes[child_id].child_contexts)
        return descendants

    def as_dict(self):
        return {
            "context_id": self.context_id,
            "context_name": self.context_name,
            "confidence": self.confidence,
            "stability": self.stability,
            "parent_context": self.parent_context,
            "child_contexts": list(self.child_contexts),
            "originating_tasks": list(self.originating_tasks),
            "inherited_features": list(self.inherited_features),
            "features": dict(self.features),
        }


class ContextHierarchy:
    ROOT_CONTEXTS = {
        "geometric_transformation": {
            "translation",
            "rotation",
            "reflection",
            "scaling",
        },
        "structural_transformation": {
            "duplication",
            "deletion",
            "insertion",
            "growth",
            "topology_change",
            "topology_expansion",
            "topological_growth",
            "topological_expansion",
            "object_splitting",
            "object_merging",
            "replication",
        },
        "color_transformation": {
            "recoloring",
            "symbolic_remapping",
            "color_mapping",
            "attribute_remapping",
            "color_expansion",
        },
        "propagation_transformation": {
            "propagation",
            "directional_motion",
        },
        "identity_preservation": {
            "identity_preservation",
            "object_identity_preservation",
            "object_persistence",
            "identity_continuity",
            "object_core",
        },
    }

    PROCESS_DEPENDENCY_CONTEXTS = {
        "growth": [
            "object_identity_preservation",
            "object_persistence",
            "identity_continuity",
            "object_core",
            "shape_preservation",
            "topology_expansion",
        ],
        "propagation": [
            "source_pattern_preserved",
            "directional_motion",
            "position_change",
            "position_preservation",
            "local_shape",
        ],
        "replication": [
            "identity_split",
            "object_count_increase",
            "topology_splitting",
            "local_shape",
            "shape_preservation",
        ],
        "topological_growth": [
            "growth",
            "topology_expansion",
            "local_shape",
            "shape_preservation",
        ],
        "object_identity_preservation": [
            "object_persistence",
            "identity_continuity",
            "object_core",
            "shape_preservation",
            "topology_preservation",
        ],
        "directional_motion": [
            "position_delta",
            "position_change",
            "propagation",
            "object_identity_preservation",
        ],
    }

    INHERITED_FEATURES = {
        "geometric_transformation": [
            "position_change",
            "object_count_preserved",
            "topology_reference_preserved",
        ],
        "structural_transformation": [
            "object_creation_or_removal",
            "topology_change",
            "structure_delta",
        ],
        "color_transformation": [
            "attribute_change",
            "topology_preserved",
            "identity_may_be_modified",
        ],
        "propagation_transformation": [
            "recursive_spread",
            "multi_cell_effect",
            "source_pattern_preserved",
        ],
        "identity_preservation": [
            "object_identity_consistent",
            "semantic_anchor_stable",
        ],
        "growth": [
            "object_expansion",
            "dependency_chain_supported",
            "identity_continuity_required",
            "shape_anchor_required",
        ],
        "propagation": [
            "directional_dependency",
            "source_pattern_required",
            "position_change_expected",
        ],
        "replication": [
            "identity_split_expected",
            "object_count_increase_expected",
            "local_shape_preserved",
        ],
        "topological_growth": [
            "topology_expansion_expected",
            "growth_dependency_required",
            "shape_anchor_required",
        ],
        "object_identity_preservation": [
            "object_persistence_required",
            "identity_continuity_required",
            "object_core_preserved",
        ],
    }

    def __init__(self):
        self.nodes = {}
        self.build_hierarchy([])

    def _parent_for_name(self, context_name):
        name = _normalize(context_name)
        if name in self.ROOT_CONTEXTS:
            return None
        for parent, children in self.ROOT_CONTEXTS.items():
            if name in children:
                return parent
        for process, dependencies in self.PROCESS_DEPENDENCY_CONTEXTS.items():
            if name in dependencies:
                return process
        return "unknown_context_family" if name != "unknown" else None

    def _ensure_root(self, context_name):
        context_name = _normalize(context_name)
        return self.nodes.setdefault(
            context_name,
            ContextNode(
                context_id=context_name,
                context_name=context_name,
                confidence=1.0,
                stability=1.0,
                inherited_features=self.INHERITED_FEATURES.get(
                    context_name,
                    [],
                ),
            ),
        )

    def add_context(self, context):
        name = _context_name(context)
        features = _signature(context)
        node_id = (
            context.context_id
            if isinstance(context, ContextDescriptor)
            else context.context_id
            if isinstance(context, ContextNode)
            else name
        )

        node = self.nodes.get(node_id)

        if node is None:
            node = ContextNode(
                context_id=node_id,
                context_name=name,
                confidence=_confidence(context),
                stability=_confidence(context),
                originating_tasks=_tasks(context),
                features=features,
            )
            self.nodes[node.context_id] = node
        else:
            node.confidence = max(node.confidence, _confidence(context))
            node.stability = max(node.stability, node.confidence)
            node.originating_tasks = sorted(
                set(node.originating_tasks + _tasks(context))
            )
            node.features.update(features)

        parent = self._parent_for_name(name)
        if parent:
            self.link_contexts(parent, node.context_id)

        self._link_process_dependencies(name)

        return node

    def _link_process_dependencies(self, process_name):
        process_name = _normalize(process_name)
        dependencies = self.PROCESS_DEPENDENCY_CONTEXTS.get(
            process_name,
            [],
        )
        if not dependencies:
            return

        process_node = self._ensure_root(process_name)

        for dependency in dependencies:
            dependency = _normalize(dependency)
            dependency_node = self.nodes.get(dependency)
            if dependency_node is None:
                dependency_node = ContextNode(
                    context_id=dependency,
                    context_name=dependency,
                    confidence=0.86,
                    stability=0.86,
                    inherited_features=self.INHERITED_FEATURES.get(
                        dependency,
                        [],
                    ),
                    features={
                        "process_dependency_context": True,
                        "required_by": process_name,
                    },
                )
                self.nodes[dependency] = dependency_node

            dependency_node.set_parent(process_node)
            dependency_node.inherited_features = sorted(
                set(
                    dependency_node.inherited_features
                    + self.INHERITED_FEATURES.get(process_name, [])
                    + ["process_dependency_inherited"]
                )
            )
            process_node.add_child(dependency_node)

    def add_relation(self, parent, child):
        return self.link_contexts(parent, child)

    def link_contexts(self, parent, child):
        parent_name = _context_name(parent)
        parent_node = self._ensure_root(parent_name)

        if isinstance(child, ContextNode):
            child_node = child
            self.nodes.setdefault(child_node.context_id, child_node)
        elif isinstance(child, str) and child in self.nodes:
            child_node = self.nodes[child]
        else:
            child_node = self.add_context(child)

        child_node.set_parent(parent_node)

        inherited = self.INHERITED_FEATURES.get(parent_node.context_name, [])
        child_node.inherited_features = sorted(
            set(child_node.inherited_features + inherited)
        )

        parent_node.add_child(child_node)

        return {
            "parent": parent_node.as_dict(),
            "child": child_node.as_dict(),
        }

    def build_hierarchy(self, contexts=None):
        for parent in self.ROOT_CONTEXTS:
            self._ensure_root(parent)

        for context in list(contexts or []):
            self.add_context(context)

        for process in self.PROCESS_DEPENDENCY_CONTEXTS:
            self._ensure_root(process)
            self._link_process_dependencies(process)

        return self.report()

    def find_parent(self, context):
        node = self.add_context(context)
        return self.nodes.get(node.parent_context)

    def find_specialization(self, context):
        node = self.add_context(context)
        return node.as_dict()

    def find_generalization(self, context):
        parent = self.find_parent(context)
        return parent.as_dict() if parent else {}

    def context_inheritance(self, context):
        node = self.add_context(context)
        inherited = list(node.inherited_features)

        if node.parent_context in self.INHERITED_FEATURES:
            inherited.extend(self.INHERITED_FEATURES[node.parent_context])

        process_dependencies = self.PROCESS_DEPENDENCY_CONTEXTS.get(
            node.context_name,
            [],
        )

        return {
            "context": node.context_name,
            "parent_context": node.parent_context,
            "ancestors": node.get_ancestors(self),
            "descendants": node.get_descendants(self),
            "process_dependency_contexts": list(process_dependencies),
            "inherited_features": sorted(set(inherited)),
            "inheritance_integrity": 1.0
            if (
                node.parent_context
                or node.context_name in self.ROOT_CONTEXTS
                or node.context_name in self.PROCESS_DEPENDENCY_CONTEXTS
            )
            else 0.0,
        }

    def process_context_dependencies(self, context):
        name = _context_name(context)
        dependencies = self.PROCESS_DEPENDENCY_CONTEXTS.get(name, [])
        return {
            "context": name,
            "process_dependency_contexts": list(dependencies),
            "process_dependency_context_count": len(dependencies),
            "process_dependency_context_ready": bool(dependencies),
        }

    def report(self):
        return {
            "system": "context_hierarchy",
            "nodes": [
                node.as_dict()
                for node in self.nodes.values()
            ],
            "root_contexts": sorted(self.ROOT_CONTEXTS),
            "process_dependency_contexts":
            dict(self.PROCESS_DEPENDENCY_CONTEXTS),
            "hierarchy_ready": True,
        }


class ContextDifferentiationEngine:
    FAMILY_DISTANCE = {
        ("translation", "reflection"): 0.30,
        ("duplication", "propagation"): 0.40,
        ("translation", "recoloring"): 0.90,
        ("duplication", "rotation"): 0.95,
        ("growth", "duplication"): 0.35,
        ("growth", "propagation"): 0.40,
        ("growth", "topological_growth"): 0.25,
        ("replication", "duplication"): 0.25,
        ("propagation", "directional_motion"): 0.25,
    }

    def __init__(self, hierarchy=None):
        self.hierarchy = hierarchy or ContextHierarchy()
        self.history = []

    def _parent_name(self, context):
        node = self.hierarchy.add_context(context)
        return node.parent_context

    def compute_context_distance(self, first, second):
        first_name = _context_name(first)
        second_name = _context_name(second)

        if first_name == second_name:
            return 0.0

        pair = tuple(sorted([first_name, second_name]))

        for known_pair, distance in self.FAMILY_DISTANCE.items():
            if tuple(sorted(known_pair)) == pair:
                return distance

        first_parent = self._parent_name(first)
        second_parent = self._parent_name(second)

        if first_parent and first_parent == second_parent:
            return 0.35

        if {first_parent, second_parent} == {
            "geometric_transformation",
            "color_transformation",
        }:
            return 0.90

        return 0.75 if first_parent and second_parent else 1.0

    def differentiate_contexts(self, contexts):
        contexts = [self.hierarchy.add_context(item) for item in contexts]
        differentiators = []

        for node in contexts:
            features = node.features
            process_dependencies = (
                self.hierarchy.process_context_dependencies(
                    node.context_name
                )
            )
            differentiators.append({
                "context": node.context_name,
                "parent_context": node.parent_context,
                "differentiators": [
                    item
                    for item in [
                        features.get("topology_behavior"),
                        features.get("color_behavior"),
                        features.get("identity_behavior"),
                        features.get("symmetry_behavior"),
                    ]
                    if item and item != "unknown"
                ],
                "process_dependency_contexts":
                process_dependencies["process_dependency_contexts"],
                "process_dependency_context_ready":
                process_dependencies[
                    "process_dependency_context_ready"
                ],
            })

        confidence = clamp(
            sum(
                1
                for item in differentiators
                if (
                    item["parent_context"]
                    or item["process_dependency_context_ready"]
                )
            )
            / max(len(differentiators), 1)
        )

        return {
            "system": "context_differentiation_engine",
            "differentiators": differentiators,
            "differentiation_confidence": confidence,
        }

    def discover_specializations(self, contexts):
        specializations = []

        for context in contexts:
            node = self.hierarchy.add_context(context)
            features = node.features
            name = node.context_name

            if (
                name == "duplication"
                and features.get("symmetry_behavior") in [
                    "symmetry_preserved",
                    "preserved",
                    "retained",
                ]
            ):
                specializations.append("symmetric_duplication")
            elif name == "duplication" and (
                "recursive" in " ".join(
                    _as_list(features.get("active_concepts"))
                )
            ):
                specializations.append("recursive_duplication")
            elif name == "translation" and (
                features.get("color_behavior") == "color_preserved"
            ):
                specializations.append("color_preserving_translation")
            else:
                specializations.append(name)

        consistency = clamp(
            sum(item != "unknown" for item in specializations)
            / max(len(specializations), 1)
        )

        return {
            "specializations": sorted(set(specializations)),
            "specialization_consistency": consistency,
        }

    def refine_clusters(self, contexts):
        contexts = list(contexts or [])
        nodes = [
            self.hierarchy.add_context(item)
            for item in contexts
        ]

        differentiation = self.differentiate_contexts(nodes)
        specialization = self.discover_specializations(nodes)
        inheritances = [
            self.hierarchy.context_inheritance(node)
            for node in nodes
        ]

        context_stability = clamp(
            sum(node.stability for node in nodes)
            / max(len(nodes), 1)
        )

        inheritance_integrity = clamp(
            sum(
                item["inheritance_integrity"]
                for item in inheritances
            )
            / max(len(inheritances), 1)
        )

        dependency_context_support = clamp(
            sum(
                1
                for item in inheritances
                if item["process_dependency_contexts"]
            )
            / max(len(inheritances), 1)
        )

        score = clamp(
            (
                context_stability
                + specialization["specialization_consistency"]
                + differentiation["differentiation_confidence"]
                + inheritance_integrity
                + dependency_context_support
            )
            / 5.0
        )

        hierarchy_required = any(
            node.context_name != "unknown" or node.confidence >= 0.50
            for node in nodes
        )

        report = {
            "system": "context_hierarchy_engine",
            "phase": "5.6",
            "contexts": [
                node.as_dict()
                for node in nodes
            ],
            "hierarchy": self.hierarchy.report(),
            "differentiation": differentiation,
            "specialization": specialization,
            "inheritance": inheritances,
            "context_stability": context_stability,
            "specialization_consistency":
            specialization["specialization_consistency"],
            "differentiation_confidence":
            differentiation["differentiation_confidence"],
            "inheritance_integrity": inheritance_integrity,
            "dependency_context_support": dependency_context_support,
            "context_hierarchy_score": score,
            "hierarchy_required": hierarchy_required,
            "hierarchy_ready": (not hierarchy_required) or score >= 0.75,
            "advanced_contextual_truth_promotion_ready":
            (not hierarchy_required) or score >= 0.75,
        }

        self.history.append(report)
        self.history = self.history[-256:]

        return report

    def detect_context_conflicts(self, contexts):
        names = {
            self.hierarchy.add_context(item).context_name
            for item in list(contexts or [])
        }

        hybrid = any(
            "hybrid" in " ".join(
                _as_list(
                    _signature(item).get(
                        "active_concepts",
                        [],
                    )
                )
            )
            for item in list(contexts or [])
        )

        conflict = (
            "translation" in names
            and "rotation" in names
            and not hybrid
        )

        return {
            "system": "context_conflict_detector",
            "contexts": sorted(names),
            "conflict_state":
            "CONTEXT_CONFLICT" if conflict else "CONTEXT_COMPATIBLE",
            "conflicts": (
                ["translation_rotation_boundary"]
                if conflict
                else []
            ),
        }


def build_context_hierarchy(contexts=None):
    hierarchy = ContextHierarchy()
    return hierarchy.build_hierarchy(contexts or [])


def context_inheritance(context, hierarchy=None):
    hierarchy = hierarchy or ContextHierarchy()
    return hierarchy.context_inheritance(context)


def detect_context_conflicts(contexts=None):
    return ContextDifferentiationEngine().detect_context_conflicts(
        contexts or []
    )


__all__ = [
    "ContextDifferentiationEngine",
    "ContextHierarchy",
    "ContextNode",
    "build_context_hierarchy",
    "context_inheritance",
    "detect_context_conflicts",
]