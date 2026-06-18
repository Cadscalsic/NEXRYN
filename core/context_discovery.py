from dataclasses import asdict, dataclass, field
from uuid import uuid4

from core.epistemic_models import clamp
from core.context.process_context_generation import (
    PROCESS_CONTEXT_STATUSES,
    PROCESS_CONTEXTS,
)
from core.process_context_generation import ProcessContextGenerationEngine
from core.process_abstraction import ProcessAbstractionLayer
from runtime.context.context_taxonomy_engine import ContextTaxonomyEngine


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
    if "object_identity_preservation" in concepts:
        concepts.add("identity_persistence")
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
    TRUTH_CONTEXT_SURFACES = {
        "shape_preservation": {
            "context_family": "Shape Context",
            "context_name": "shape_context",
            "surface": "shape_stability",
            "native_contexts": [
                "shape_stability",
                "local_shape_preservation",
                "boundary_geometry_preservation",
            ],
            "topology_behavior": "topology_preserved",
            "color_behavior": "color_preserved",
            "identity_behavior": "identity_preserved",
            "symmetry_behavior": "unknown",
        },
        "topology_preservation": {
            "context_family": "Topology Context",
            "context_name": "topology_context",
            "surface": "topology_stability",
            "native_contexts": [
                "topology_stability",
                "connectivity_preservation",
                "region_relation_preservation",
            ],
            "topology_behavior": "topology_preserved",
            "color_behavior": "color_preserved",
            "identity_behavior": "identity_preserved",
            "symmetry_behavior": "unknown",
        },
        "position_preservation": {
            "context_family": "Position Context",
            "context_name": "position_context",
            "surface": "position_stability",
            "native_contexts": [
                "position_stability",
                "coordinate_anchor_preservation",
                "relative_position_preservation",
            ],
            "topology_behavior": "topology_preserved",
            "color_behavior": "color_preserved",
            "identity_behavior": "identity_preserved",
            "symmetry_behavior": "unknown",
        },
        "color_preservation": {
            "context_family": "Color Context",
            "context_name": "color_context",
            "surface": "color_stability",
            "native_contexts": [
                "color_stability",
                "attribute_mapping_preservation",
                "no_color_reassignment",
            ],
            "topology_behavior": "topology_preserved",
            "color_behavior": "color_preserved",
            "identity_behavior": "identity_preserved",
            "symmetry_behavior": "unknown",
        },
        "symmetry_reasoning": {
            "context_family": "Symmetry Context",
            "context_name": "symmetry_context",
            "surface": "symmetry_relation",
            "native_contexts": [
                "symmetry_relation",
                "axis_consistency",
                "mirror_consistency",
            ],
            "topology_behavior": "topology_preserved",
            "color_behavior": "color_preserved",
            "identity_behavior": "identity_preserved",
            "symmetry_behavior": "symmetry_reasoned",
        },
        "symmetry_preservation": {
            "context_family": "Symmetry Context",
            "context_name": "symmetry_context",
            "surface": "symmetry_stability",
            "native_contexts": [
                "symmetry_stability",
                "axis_consistency",
                "mirror_consistency",
            ],
            "topology_behavior": "topology_preserved",
            "color_behavior": "color_preserved",
            "identity_behavior": "identity_preserved",
            "symmetry_behavior": "symmetry_preserved",
        },
        "identity_persistence": {
            "context_family": "Identity Persistence",
            "context_name": "identity_persistence",
            "surface": "identity_persistence",
            "native_contexts": [
                "identity_persistence",
                "object_persistence",
                "identity_continuity",
            ],
            "topology_behavior": "topology_preserved",
            "color_behavior": "color_reassignment_allowed",
            "identity_behavior": "identity_preserved",
            "symmetry_behavior": "unknown",
        },
        "identity_forking": {
            "context_family": "Identity Forking",
            "context_name": "identity_forking",
            "surface": "identity_forking",
            "native_contexts": [
                "identity_forking",
                "identity_split",
                "object_count_increase",
                "topology_splitting",
            ],
            "topology_behavior": "topology_splitting",
            "color_behavior": "color_preserved",
            "identity_behavior": "identity_split",
            "symmetry_behavior": "unknown",
        },
    }
    PROCESS_CONTEXT_SURFACES = ProcessContextGenerationEngine.discovery_surfaces()
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
        "replication": ["replication", "replicated", "replicating"],
        "deletion": ["delete", "remove"],
        "insertion": ["insert", "create", "add"],
        "propagation": ["propagate", "spread"],
        "topological_growth": [
            "topological_growth",
            "topology_growth",
            "topology_expansion",
            "fill_region",
        ],
        "directional_motion": [
            "directional_motion",
            "position_delta",
            "directional_displacement",
        ],
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
            "structural_transformation_context",
            "topology_change",
            "topology_expansion",
        },
        "Growth Context": {
            "growth",
            "topology_expansion",
            "region_expansion",
            "object_count_growth",
            "identity_preservation_under_growth",
        },
        "Topological Growth Context": {
            "topological_growth",
            "topology_splitting",
            "topological_expansion",
        },
        "Propagation Context": {
            "propagation",
            "directional_spread",
            "source_pattern_preservation",
            "signal_transfer",
        },
        "Directional Motion Context": {
            "directional_motion",
            "position_delta",
            "directional_displacement",
            "source_pattern_motion",
        },
        "Replication Context": {
            "replication",
            "object_creation",
            "identity_split",
            "structural_copying",
        },
        "Identity Preservation": {
            "identity_preservation",
            "identity_persistence",
        },
        "Identity Forking": {
            "identity_forking",
            "identity_split",
            "object_count_increase",
            "topology_splitting",
        },
        "Color Context": {
            "color_context",
            "color_preservation",
            "color_stability",
            "attribute_mapping_preservation",
            "no_color_reassignment",
        },
        "Position Context": {
            "position_context",
            "position_preservation",
            "position_stability",
            "coordinate_anchor_preservation",
            "relative_position_preservation",
        },
        "Shape Context": {
            "shape_context",
            "shape_preservation",
            "shape_stability",
            "local_shape_preservation",
            "boundary_geometry_preservation",
        },
        "Topology Context": {
            "topology_context",
            "topology_preservation",
            "topology_stability",
            "connectivity_preservation",
            "region_relation_preservation",
        },
        "Symmetry Context": {
            "symmetry_context",
            "symmetry_reasoning",
            "symmetry_preservation",
            "symmetry_relation",
            "symmetry_stability",
            "axis_consistency",
            "mirror_consistency",
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
        for family in self.PROCESS_CONTEXT_SURFACES:
            if family in features.get("active_concepts", []):
                return family, 0.90, [
                    f"active process concept indicates {family}",
                    "process-native context surface available",
                ]
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
            (
                "identity_forking" in features["active_concepts"]
            )
            and (
                identity_behavior in {"identity_split", "object_split"}
                or topology_behavior in {
                    "topology_splitting",
                    "object_splitting",
                }
            )
        ):
            return {
                "value": "replication",
                "confidence": 0.74,
                "reasons": [
                    "identity forking observed under split context",
                    "identity split implies replication context",
                ],
            }
        if (
            "identity_persistence" in features["active_concepts"]
        ):
            return {
                "value": "identity_preservation",
                "confidence": 0.82,
                "reasons": [
                    "identity persistence concept anchors identity context",
                    "no split or merge evidence requires structural context",
                ],
            }
        if (
            features["positions_preserved"] is False
            and features["colors_preserved"] is True
            and features["object_delta"] == 0
            and features["grid_shape_changed"] is False
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

    def discover_process_operator(self, observation=None):
        return self.discover_transformation_family(observation)

    def discover_semantic_context(self, observation=None):
        context = observation if isinstance(observation, dict) else {}
        features = self.extract_context_features(context)
        truth_surface = self._truth_surface_for_observation(context)
        if truth_surface:
            context_name = truth_surface.get(
                "context_name",
                _normalize(truth_surface["context_family"]),
            )
            return {
                "value": context_name,
                "confidence": 0.92,
                "reasons": [
                    f"active truth concept indicates {context_name}",
                    "truth-native semantic context surface available",
                ],
            }
        process_context = self._process_context_for_observation(context)
        if process_context:
            return {
                "value": process_context["context_name"],
                "confidence": max(
                    clamp(process_context.get("confidence", 0.0)),
                    0.90,
                ),
                "reasons": [
                    "math reasoning process context supplied",
                    f"process context status {process_context.get('status')}",
                ],
            }
        operator = self.discover_process_operator(context)
        process_surface = self.PROCESS_CONTEXT_SURFACES.get(operator["value"])
        if process_surface:
            context_name = process_surface["process_context"]
            return {
                "value": context_name,
                "confidence": max(operator["confidence"], 0.90),
                "reasons": [
                    f"process operator {operator['value']} maps to {context_name}",
                    "process abstraction context surface available",
                ],
            }
        taxonomy = ContextTaxonomyEngine().classify({
            **context,
            **self.generate_context_signature_without_taxonomy(context),
        })
        if taxonomy.get("known_context"):
            return {
                "value": taxonomy["context_name"],
                "confidence": taxonomy["context_confidence"],
                "reasons": [
                    "semantic taxonomy reclassified unknown context",
                    f"taxonomy family {taxonomy['context_family']}",
                ],
            }
        if operator["value"] == "translation":
            return {
                "value": "position_context",
                "confidence": operator["confidence"],
                "reasons": [
                    "translation operator carries position context evidence",
                ],
            }
        if operator["value"] in {"recoloring", "symbolic_remapping"}:
            return {
                "value": "color_context",
                "confidence": operator["confidence"],
                "reasons": [
                    f"{operator['value']} operator carries color context evidence",
                ],
            }
        if operator["value"] in {"rotation", "reflection"}:
            return {
                "value": "shape_context",
                "confidence": operator["confidence"],
                "reasons": [
                    f"{operator['value']} operator carries shape context evidence",
                ],
            }
        if operator["value"] in {"duplication", "deletion", "insertion"}:
            return {
                "value": "structural_transformation_context",
                "confidence": operator["confidence"],
                "reasons": [
                    f"{operator['value']} operator carries structural context evidence",
                ],
            }
        if operator["value"] == "identity_preservation":
            return {
                "value": "identity_preservation",
                "confidence": operator["confidence"],
                "reasons": [
                    "identity preservation operator anchors identity context",
                ],
            }
        return {
            "value": "unknown",
            "confidence": operator["confidence"],
            "reasons": ["insufficient semantic context evidence"],
        }

    def generate_context_signature_without_taxonomy(self, observation=None):
        context = observation if isinstance(observation, dict) else {}
        features = self.extract_context_features(context)
        return {
            "active_concepts": features.get("active_concepts", []),
            "topology_behavior": _normalize(
                context.get(
                    "topology_behavior",
                    "topology_preserved"
                    if features.get("cell_count_delta", 0) == 0
                    else "topology_restructured",
                )
            ),
            "color_behavior": _normalize(
                context.get(
                    "color_behavior",
                    "color_preserved"
                    if features.get("colors_preserved") is True
                    else "color_reassigned"
                    if features.get("colors_preserved") is False
                    else "unknown",
                )
            ),
            "identity_behavior": _normalize(
                context.get("identity_behavior", "identity_preserved")
            ),
            "size_behavior": _normalize(
                context.get(
                    "size_behavior",
                    "size_expanded"
                    if features.get("grid_shape_changed")
                    or features.get("cell_count_delta", 0) != 0
                    else "size_preserved",
                )
            ),
        }

    def discover_object_dynamics(self, observation=None):
        features = self.extract_context_features(observation)
        family = self.discover_process_operator(observation)["value"]
        process_surface = self.PROCESS_CONTEXT_SURFACES.get(family)
        if process_surface:
            return process_surface["object_dynamics"]
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
        truth_surface = self._truth_surface_for_observation(observation)
        if truth_surface:
            return truth_surface["topology_behavior"]
        explicit = context.get("topology_behavior", context.get("topology"))
        if explicit:
            return _normalize(explicit)
        features = self.extract_context_features(observation)
        family = self.discover_process_operator(observation)["value"]
        process_surface = self.PROCESS_CONTEXT_SURFACES.get(family)
        if process_surface:
            return process_surface["topology_behavior"]
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
        truth_surface = self._truth_surface_for_observation(observation)
        if truth_surface:
            return truth_surface["color_behavior"]
        explicit = context.get("color_behavior", context.get("color"))
        if explicit:
            return _normalize(explicit)
        features = self.extract_context_features(observation)
        family = self.discover_process_operator(observation)["value"]
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
        truth_surface = self._truth_surface_for_observation(observation)
        if truth_surface:
            return truth_surface["identity_behavior"]
        explicit = context.get("identity_behavior", context.get("identity"))
        if explicit:
            return _normalize(explicit)
        features = self.extract_context_features(observation)
        family = self.discover_process_operator(observation)["value"]
        process_surface = self.PROCESS_CONTEXT_SURFACES.get(family)
        if process_surface:
            return process_surface["identity_behavior"]
        if features["object_delta"] > 0:
            return "identity_split"
        if features["object_delta"] < 0:
            return "identity_merged"
        if self.discover_process_operator(observation)["value"] == (
            "propagation"
        ):
            return "identity_propagated"
        if features["colors_preserved"] is False:
            return "identity_modified"
        return "identity_preserved"

    def generate_context_signature(self, observation=None):
        context = observation if isinstance(observation, dict) else {}
        operator = self.discover_process_operator(context)
        semantic_context = self.discover_semantic_context(context)
        features = self.extract_context_features(context)
        process_surface = self.PROCESS_CONTEXT_SURFACES.get(operator["value"])
        process_context_report = (
            ProcessContextGenerationEngine().generate_context(
                operator["value"],
                evidence={
                    "operator_confidence": operator["confidence"],
                    "operator_reasons": operator["reasons"],
                },
            )
            if process_surface
            else {}
        )
        truth_surface = self._truth_surface_for_observation(context)
        process_native_contexts = (
            list(process_surface["native_contexts"])
            if process_surface
            else []
        )
        truth_native_contexts = (
            list(truth_surface["native_contexts"])
            if truth_surface
            else []
        )
        native_contexts = truth_native_contexts or process_native_contexts
        context_surface = (
            truth_surface["surface"]
            if truth_surface
            else process_surface["surface"]
            if process_surface
            else semantic_context["value"]
        )
        return {
            "task_cluster": _normalize(
                context.get("task_cluster", semantic_context["value"])
            ),
            "transformation_family": semantic_context["value"],
            "semantic_context": semantic_context["value"],
            "process_operator": operator["value"],
            "operator_confidence": operator["confidence"],
            "operator_reasons": operator["reasons"],
            "process_abstraction": (
                ProcessAbstractionLayer.get(operator["value"]).as_dict()
                if ProcessAbstractionLayer.get(operator["value"])
                else {}
            ),
            "process_abstraction_ready": bool(
                ProcessAbstractionLayer.get(operator["value"])
            ),
            "process_context_generation": process_context_report,
            "process_context_generated": bool(
                process_context_report.get("process_context_generated")
            ),
            "process_context_family": (
                process_surface["context_family"]
                if process_surface
                else "none"
            ),
            "truth_context_family": (
                truth_surface["context_family"]
                if truth_surface
                else "none"
            ),
            "process_context_surface": (
                process_surface["surface"] if process_surface else "none"
            ),
            "truth_context_surface": (
                truth_surface["surface"] if truth_surface else "none"
            ),
            "context_surface": context_surface,
            "process_native_contexts": process_native_contexts,
            "truth_native_contexts": truth_native_contexts,
            "native_contexts": native_contexts,
            "process_native_context_ready": bool(process_surface),
            "truth_native_context_ready": bool(truth_surface),
            "object_count": str(features["output_object_count"]),
            "object_dynamics": self.discover_object_dynamics(context),
            "topology_behavior": self.discover_topology_behavior(context),
            "color_behavior": self.discover_color_behavior(context),
            "symmetry_behavior": _normalize(
                context.get(
                    "symmetry_behavior",
                    truth_surface["symmetry_behavior"]
                    if truth_surface
                    else "unknown",
                )
            ),
            "size_behavior": (
                process_surface["size_behavior"]
                if process_surface
                else "size_expanded"
                if features["cell_count_delta"] > 0
                else "size_preserved"
            ),
            "identity_behavior": self.discover_identity_behavior(context),
            "propagation_behavior": (
                process_surface["propagation_behavior"]
                if process_surface
                else "propagation_absent"
            ),
            "confidence": semantic_context["confidence"],
            "classification_reasons": semantic_context["reasons"],
        }

    def classify_context(self, observation=None):
        signature = self.generate_context_signature(observation)
        family = signature["semantic_context"]
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
            "semantic_context":
            classification["signature"]["semantic_context"],
            "discovered_context_name": classification["context_name"],
            "process_operator":
            classification["signature"]["process_operator"],
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
        process_surface = self.PROCESS_CONTEXT_SURFACES.get(family)
        if process_surface:
            return process_surface["context_family"]
        for surface in self.PROCESS_CONTEXT_SURFACES.values():
            if family == surface.get("context_id"):
                return surface["context_family"]
        if family == "color_context":
            return "Color Context"
        if family == "symmetry_context":
            return "Symmetry Context"
        if family == "density_context":
            return "Density Context"
        if family == "scale_context":
            return "Scale Context"
        if family == "mapping_context":
            return "Mapping Context"
        if family == "position_context":
            return "Position Context"
        if family == "shape_context":
            return "Shape Context"
        if family == "topology_context":
            return "Topology Context"
        if family == "structural_transformation_context":
            return "Structural Transformation"
        for cluster_name, families in self.CLUSTER_FAMILIES.items():
            if family in families:
                return cluster_name
        return "Unknown Context Family"

    def _truth_surface_for_observation(self, observation=None):
        features = self.extract_context_features(observation)
        for concept, surface in self.TRUTH_CONTEXT_SURFACES.items():
            if concept in features.get("active_concepts", []):
                return surface
        return None

    def _process_context_for_observation(self, observation=None):
        context = observation if isinstance(observation, dict) else {}
        report = context.get("process_context_report", {})
        if not isinstance(report, dict):
            return None
        status = report.get("status")
        if status not in PROCESS_CONTEXT_STATUSES:
            return None
        context_name = _normalize(report.get("context_name"))
        source_concept = _normalize(
            report.get("source_concept", report.get("concept"))
        )
        active_concepts = set(self.extract_context_features(context).get("active_concepts", []))
        if source_concept not in PROCESS_CONTEXTS:
            return None
        if source_concept not in active_concepts:
            return None
        expected = f"{source_concept}_context"
        if context_name != expected:
            return None
        return report

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
