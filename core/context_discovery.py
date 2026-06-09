from dataclasses import asdict, dataclass, field
from uuid import uuid4

from core.epistemic_models import clamp


def _normalize(value, default="unknown"):
    if value is None:
        return default
    return str(value).strip().lower().replace(" ", "_") or default


def _grid(context, key):
    value = context.get(key)
    if value is None:
        task = context.get("task", {})
        if isinstance(task, dict):
            value = task.get(key)
    return value if isinstance(value, list) else None


def _flatten_grid(grid):
    if not isinstance(grid, list):
        return []
    flattened = []
    for row in grid:
        if isinstance(row, list):
            flattened.extend(row)
    return flattened


def _grid_shape(grid):
    if not isinstance(grid, list) or not grid:
        return (0, 0)
    return (len(grid), len(grid[0]) if isinstance(grid[0], list) else 0)


def _color_set(grid):
    return {
        item
        for item in _flatten_grid(grid)
        if item not in [0, None]
    }


def _nonzero_cells(grid):
    cells = set()
    if not isinstance(grid, list):
        return cells
    for row_index, row in enumerate(grid):
        if not isinstance(row, list):
            continue
        for column_index, value in enumerate(row):
            if value not in [0, None]:
                cells.add((row_index, column_index, value))
    return cells


def _positions_only(cells):
    return {
        (row, column)
        for row, column, _value in cells
    }


def _count_objects(context, grid_key):
    object_key = "input_objects" if grid_key == "input_grid" else "output_objects"
    objects = context.get(object_key)
    if isinstance(objects, list):
        return len(objects)
    grid = _grid(context, grid_key)
    colors = _color_set(grid)
    return len(colors) if colors else len(_nonzero_cells(grid))


def _active_concepts(context):
    concepts = set()
    for key in [
        "active_concepts",
        "semantic_concepts",
        "concepts",
        "detected_concepts",
    ]:
        value = context.get(key, [])
        if isinstance(value, dict):
            value = value.keys()
        if isinstance(value, (list, tuple, set)):
            concepts.update(_normalize(item) for item in value)
    for key in ["concept", "truth", "target_concept"]:
        value = context.get(key)
        if value:
            concepts.add(_normalize(value))
    return concepts


@dataclass
class ContextDescriptor:
    context_id: str
    context_name: str
    confidence: float
    context_family: str
    originating_tasks: list = field(default_factory=list)
    evidence_count: int = 0
    features: dict = field(default_factory=dict)

    def __post_init__(self):
        self.context_id = self.context_id or f"context:{uuid4().hex}"
        self.context_name = _normalize(self.context_name)
        self.context_family = str(self.context_family or "Unknown Context Family")
        self.confidence = clamp(self.confidence)
        self.originating_tasks = sorted(set(self.originating_tasks or []))
        self.evidence_count = int(self.evidence_count or 0)

    def serialize(self):
        return {
            "context_id": self.context_id,
            "context_name": self.context_name,
            "context_family": self.context_family,
            "confidence": self.confidence,
            "originating_tasks": list(self.originating_tasks),
            "evidence_count": self.evidence_count,
            "features": dict(self.features),
        }

    def describe(self):
        reasons = self.features.get("classification_reasons", [])
        return {
            "context": self.context_name,
            "family": self.context_family,
            "confidence": self.confidence,
            "why": list(reasons),
        }

    def compare(self, other):
        other_features = (
            other.features
            if isinstance(other, ContextDescriptor)
            else dict(other or {})
        )
        keys = sorted(set(self.features) | set(other_features))
        if not keys:
            return 0.0
        return clamp(
            sum(
                self.features.get(key) == other_features.get(key)
                for key in keys
            )
            / len(keys)
        )


@dataclass
class ContextCluster:
    cluster_id: str
    cluster_name: str
    member_contexts: list = field(default_factory=list)
    stability_score: float = 0.0

    def add_context(self, context):
        context = (
            context
            if isinstance(context, ContextDescriptor)
            else ContextDescriptor(**context)
        )
        if context.context_id not in [
            item.context_id
            for item in self.member_contexts
        ]:
            self.member_contexts.append(context)
        self.stability_score = self.compute_stability()
        return self

    def merge(self, other):
        for context in other.member_contexts:
            self.add_context(context)
        return self

    def compute_stability(self):
        if not self.member_contexts:
            return 0.0
        family = self.member_contexts[0].context_family
        return clamp(
            sum(
                item.context_family == family
                for item in self.member_contexts
            )
            / len(self.member_contexts)
        )

    def as_dict(self):
        return {
            "cluster_id": self.cluster_id,
            "cluster_name": self.cluster_name,
            "member_contexts": [
                item.serialize()
                for item in self.member_contexts
            ],
            "stability_score": self.stability_score,
        }


class ContextDiscoveryEngine:
    FAMILY_KEYWORDS = {
        "translation": ["translation", "translate", "move", "shift"],
        "rotation": ["rotation", "rotate"],
        "reflection": ["reflection", "reflect", "mirror"],
        "recoloring": ["recolor", "color_change", "replace_color"],
        "duplication": [
            "duplicate",
            "copy",
            "replicate",
            "identity_split",
            "object_split",
            "object_splitting",
        ],
        "deletion": ["delete", "remove"],
        "insertion": ["insert", "create", "add"],
        "propagation": ["propagate", "spread"],
        "growth": ["growth", "grow", "expand"],
        "topology_change": ["topology_change", "restructure"],
        "topology_expansion": ["topology_expansion", "fill_region"],
        "symbolic_remapping": ["symbolic_remapping", "attribute_remapping"],
    }

    CLUSTER_FAMILIES = {
        "Geometric Transformation": {
            "translation",
            "rotation",
            "reflection",
        },
        "Attribute Transformation": {
            "recoloring",
            "symbolic_remapping",
        },
        "Structural Transformation": {
            "duplication",
            "deletion",
            "insertion",
            "growth",
            "topology_change",
            "topology_expansion",
        },
        "Propagation Transformation": {
            "propagation",
        },
        "Identity Preservation": {
            "identity_preservation",
        },
    }

    def __init__(self):
        self.discovered_contexts = []
        self.clusters = {}

    def extract_context_features(self, observation=None):
        context = observation if isinstance(observation, dict) else {}
        input_grid = _grid(context, "input_grid")
        output_grid = _grid(context, "output_grid")
        input_cells = _nonzero_cells(input_grid)
        output_cells = _nonzero_cells(output_grid)
        input_positions = _positions_only(input_cells)
        output_positions = _positions_only(output_cells)
        input_colors = _color_set(input_grid)
        output_colors = _color_set(output_grid)
        input_count = _count_objects(context, "input_grid")
        output_count = _count_objects(context, "output_grid")
        features = {
            "active_concepts": sorted(_active_concepts(context)),
            "input_shape": _grid_shape(input_grid),
            "output_shape": _grid_shape(output_grid),
            "input_object_count": input_count,
            "output_object_count": output_count,
            "object_delta": output_count - input_count,
            "input_color_count": len(input_colors),
            "output_color_count": len(output_colors),
            "colors_preserved": input_colors == output_colors
            if input_colors or output_colors
            else None,
            "positions_preserved": input_positions == output_positions
            if input_positions or output_positions
            else None,
            "cell_count_delta": len(output_cells) - len(input_cells),
            "grid_shape_changed": _grid_shape(input_grid) != _grid_shape(
                output_grid
            ),
        }
        return features

    def _keyword_family(self, features):
        joined = " ".join(features.get("active_concepts", []))
        for family, keywords in self.FAMILY_KEYWORDS.items():
            if family in joined or any(keyword in joined for keyword in keywords):
                return family, 0.86, [f"active concept indicates {family}"]
        return None, 0.0, []

    def discover_transformation_family(self, observation=None):
        context = observation if isinstance(observation, dict) else {}
        explicit = context.get("transformation_family")
        if explicit:
            return {
                "value": _normalize(explicit),
                "confidence": 0.95,
                "reasons": ["explicit transformation family supplied"],
            }
        features = self.extract_context_features(context)
        keyword_family, keyword_confidence, reasons = self._keyword_family(
            features
        )
        if keyword_family:
            return {
                "value": keyword_family,
                "confidence": keyword_confidence,
                "reasons": reasons,
            }
        identity_behavior = _normalize(
            context.get(
                "identity_behavior",
                context.get("identity", context.get("identity_mode")),
            )
        )
        topology_behavior = _normalize(
            context.get(
                "topology_behavior",
                context.get("topology", context.get("topology_mode")),
            )
        )
        if (
            "object_identity_preservation" in features["active_concepts"]
            and (
                identity_behavior in {"identity_split", "object_split"}
                or topology_behavior in {
                    "topology_splitting",
                    "object_splitting",
                }
            )
        ):
            return {
                "value": "duplication",
                "confidence": 0.74,
                "reasons": [
                    "object identity concept observed under split context",
                    "identity split implies structural duplication context",
                ],
            }
        if "object_identity_preservation" in features["active_concepts"]:
            return {
                "value": "identity_preservation",
                "confidence": 0.82,
                "reasons": [
                    "object identity concept anchors identity context",
                    "no split or merge evidence requires structural context",
                ],
            }
        if (
            features["colors_preserved"] is False
            and features["positions_preserved"] is True
        ):
            return {
                "value": "recoloring",
                "confidence": 0.90,
                "reasons": [
                    "objects preserved",
                    "topology preserved",
                    "colors changed consistently",
                    "no geometric movement detected",
                ],
            }
        if (
            features["positions_preserved"] is False
            and features["colors_preserved"] is True
            and features["object_delta"] == 0
        ):
            return {
                "value": "translation",
                "confidence": 0.78,
                "reasons": [
                    "colors preserved",
                    "object count preserved",
                    "occupied positions changed",
                ],
            }
        if features["object_delta"] > 0:
            return {
                "value": "duplication",
                "confidence": 0.76,
                "reasons": ["output contains additional objects"],
            }
        if features["object_delta"] < 0:
            return {
                "value": "deletion",
                "confidence": 0.76,
                "reasons": ["output contains fewer objects"],
            }
        if features["cell_count_delta"] > 0:
            return {
                "value": "growth",
                "confidence": 0.72,
                "reasons": ["occupied area expanded"],
            }
        return {
            "value": "unknown",
            "confidence": 0.20,
            "reasons": ["insufficient transformation evidence"],
        }

    def discover_object_dynamics(self, observation=None):
        features = self.extract_context_features(observation)
        if features["object_delta"] > 0:
            return "object_created"
        if features["object_delta"] < 0:
            return "object_removed"
        if features["positions_preserved"] is False:
            return "object_moved"
        if features["cell_count_delta"] > 0:
            return "object_expanded"
        return "object_preserved"

    def discover_topology_behavior(self, observation=None):
        context = observation if isinstance(observation, dict) else {}
        explicit = context.get("topology_behavior", context.get("topology"))
        if explicit:
            return _normalize(explicit)
        features = self.extract_context_features(observation)
        if features["cell_count_delta"] > 0:
            return "topology_expanding"
        if features["object_delta"] > 0:
            return "topology_splitting"
        if features["object_delta"] < 0:
            return "topology_merging"
        if features["positions_preserved"] is False:
            return "topology_restructured"
        return "topology_preserved"

    def discover_color_behavior(self, observation=None):
        context = observation if isinstance(observation, dict) else {}
        explicit = context.get("color_behavior", context.get("color"))
        if explicit:
            return _normalize(explicit)
        features = self.extract_context_features(observation)
        family = self.discover_transformation_family(observation)["value"]
        if features["colors_preserved"] is True:
            return "color_preserved"
        if family == "symbolic_remapping":
            return "color_mapped"
        if family == "recoloring":
            return "color_changed"
        if features["output_color_count"] > features["input_color_count"]:
            return "color_expanding"
        return "color_reassigned"

    def discover_identity_behavior(self, observation=None):
        context = observation if isinstance(observation, dict) else {}
        explicit = context.get("identity_behavior", context.get("identity"))
        if explicit:
            return _normalize(explicit)
        features = self.extract_context_features(observation)
        if features["object_delta"] > 0:
            return "identity_split"
        if features["object_delta"] < 0:
            return "identity_merged"
        if self.discover_transformation_family(observation)["value"] == (
            "propagation"
        ):
            return "identity_propagated"
        if features["colors_preserved"] is False:
            return "identity_modified"
        return "identity_preserved"

    def generate_context_signature(self, observation=None):
        context = observation if isinstance(observation, dict) else {}
        family = self.discover_transformation_family(context)
        features = self.extract_context_features(context)
        return {
            "task_cluster": _normalize(
                context.get("task_cluster", family["value"])
            ),
            "transformation_family": family["value"],
            "object_count": str(features["output_object_count"]),
            "object_dynamics": self.discover_object_dynamics(context),
            "topology_behavior": self.discover_topology_behavior(context),
            "color_behavior": self.discover_color_behavior(context),
            "symmetry_behavior": _normalize(
                context.get("symmetry_behavior", "unknown")
            ),
            "size_behavior": (
                "size_expanded"
                if features["cell_count_delta"] > 0
                else "size_preserved"
            ),
            "identity_behavior": self.discover_identity_behavior(context),
            "propagation_behavior": (
                "propagation_detected"
                if family["value"] == "propagation"
                else "propagation_absent"
            ),
            "confidence": family["confidence"],
            "classification_reasons": family["reasons"],
        }

    def classify_context(self, observation=None):
        signature = self.generate_context_signature(observation)
        family = signature["transformation_family"]
        cluster_name = self._cluster_name_for_family(family)
        return {
            "context_name": family,
            "context_family": cluster_name,
            "confidence": signature["confidence"],
            "signature": signature,
            "why": signature["classification_reasons"],
        }

    def discover_context(self, observation=None):
        context = observation if isinstance(observation, dict) else {}
        classification = self.classify_context(context)
        task_id = context.get("task_id", context.get("task", "unknown"))
        descriptor = ContextDescriptor(
            context_id=f"context:{classification['context_name']}:{task_id}",
            context_name=classification["context_name"],
            confidence=classification["confidence"],
            context_family=classification["context_family"],
            originating_tasks=[task_id],
            evidence_count=1,
            features=classification["signature"],
        )
        self.discovered_contexts.append(descriptor)
        self.cluster_contexts([descriptor])
        return {
            "system": "context_discovery_engine",
            "task": task_id,
            "discovered_context": descriptor.serialize(),
            "context_signature": classification["signature"],
            "transformation_family":
            classification["signature"]["transformation_family"],
            "topology_behavior":
            classification["signature"]["topology_behavior"],
            "color_behavior":
            classification["signature"]["color_behavior"],
            "identity_behavior":
            classification["signature"]["identity_behavior"],
            "confidence": descriptor.confidence,
            "cluster": classification["context_family"],
            "explanation": descriptor.describe(),
        }

    def _cluster_name_for_family(self, family):
        for cluster_name, families in self.CLUSTER_FAMILIES.items():
            if family in families:
                return cluster_name
        return "Unknown Context Family"

    def cluster_contexts(self, contexts=None):
        contexts = list(contexts or self.discovered_contexts)
        for context in contexts:
            descriptor = (
                context
                if isinstance(context, ContextDescriptor)
                else ContextDescriptor(**context)
            )
            cluster_name = descriptor.context_family
            cluster_id = f"cluster:{cluster_name.lower().replace(' ', '_')}"
            cluster = self.clusters.setdefault(
                cluster_id,
                ContextCluster(
                    cluster_id=cluster_id,
                    cluster_name=cluster_name,
                ),
            )
            cluster.add_context(descriptor)
        return {
            "system": "context_discovery_engine",
            "clusters": [
                cluster.as_dict()
                for cluster in self.clusters.values()
            ],
        }

    def compute_context_similarity(self, first, second):
        first_signature = (
            first.get("features", first)
            if isinstance(first, dict)
            else first.features
        )
        second_signature = (
            second.get("features", second)
            if isinstance(second, dict)
            else second.features
        )
        keys = [
            "transformation_family",
            "object_dynamics",
            "topology_behavior",
            "color_behavior",
            "identity_behavior",
            "propagation_behavior",
        ]
        return clamp(
            sum(
                first_signature.get(key) == second_signature.get(key)
                for key in keys
            )
            / len(keys)
        )


def discover_transformation_family(observation=None):
    return ContextDiscoveryEngine().discover_transformation_family(observation)


def discover_object_dynamics(observation=None):
    return ContextDiscoveryEngine().discover_object_dynamics(observation)


def discover_topology_behavior(observation=None):
    return ContextDiscoveryEngine().discover_topology_behavior(observation)


def discover_color_behavior(observation=None):
    return ContextDiscoveryEngine().discover_color_behavior(observation)


def discover_identity_behavior(observation=None):
    return ContextDiscoveryEngine().discover_identity_behavior(observation)


def generate_context_signature(observation=None):
    return ContextDiscoveryEngine().generate_context_signature(observation)


def compute_context_similarity(first, second):
    return ContextDiscoveryEngine().compute_context_similarity(first, second)


__all__ = [
    "ContextCluster",
    "ContextDescriptor",
    "ContextDiscoveryEngine",
    "compute_context_similarity",
    "discover_color_behavior",
    "discover_identity_behavior",
    "discover_object_dynamics",
    "discover_topology_behavior",
    "discover_transformation_family",
    "generate_context_signature",
]
