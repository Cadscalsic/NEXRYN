"""Mechanistic reasoning between semantic concepts and executable transforms."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Mapping

import numpy as np

from runtime.reasoning.transformation_theory_engine import transformation_theory_engine


class MechanisticReasoningEngine:
    """Convert attributed ARC concepts into causal mechanism graphs."""

    system_name = "mechanistic_reasoning_engine"

    MECHANISM_LIBRARY = {
        "gravity": {
            "family": "physics",
            "candidate_mechanisms": [
                "support_detection",
                "unsupported_object_detection",
                "downward_trajectory_simulation",
                "collision_resolution",
                "rest_state_detection",
                "topology_update",
            ],
            "reference_frames": ["grid_down_axis", "support_surface", "object_cells"],
            "operations": ["translate", "connect_components"],
        },
        "rotation": {
            "family": "orientation",
            "candidate_mechanisms": [
                "rotation_angle_inference",
                "rotation_center_selection",
                "orientation_update",
                "color_preservation",
                "topology_preservation",
            ],
            "reference_frames": ["grid_center", "object_centroid", "bounding_box_center"],
            "operations": ["rotate"],
        },
        "object_counting": {
            "family": "quantity",
            "candidate_mechanisms": [
                "object_grouping",
                "cardinality_extraction",
                "quantity_rule_selection",
                "quantity_preservation_check",
                "quantity_transformation",
            ],
            "reference_frames": ["object_components", "color_groups", "set_membership"],
            "operations": ["duplicate", "remove_object", "select_object"],
        },
        "density": {
            "family": "object_expansion",
            "candidate_mechanisms": [
                "source_object_selection",
                "expansion_mode_selection",
                "symmetry_axis_selection",
                "density_modulation",
                "topology_update",
            ],
            "reference_frames": ["object_centroid", "symmetry_axis", "local_neighborhood"],
            "operations": ["duplicate", "expand", "grow", "fill_region"],
        },
        "color_mapping": {
            "family": "symbolic",
            "candidate_mechanisms": [
                "symbol_class_detection",
                "mapping_rule_inference",
                "color_substitution",
                "shape_preservation",
                "position_preservation",
            ],
            "reference_frames": ["color_class", "symbol_class", "object_identity"],
            "operations": ["recolor"],
        },
    }

    CONCEPT_ALIASES = {
        "gravity": "gravity",
        "gravity_simulation": "gravity",
        "falling": "gravity",
        "support": "gravity",
        "collision": "gravity",
        "rest_state": "gravity",
        "downward_motion": "gravity",
        "rotation": "rotation",
        "reflection": "rotation",
        "rotation_reflection": "rotation",
        "orientation_change": "rotation",
        "object_counting": "object_counting",
        "cardinality": "object_counting",
        "quantity_preservation": "object_counting",
        "quantity_transformation": "object_counting",
        "numerical_reasoning": "object_counting",
        "set_reasoning": "object_counting",
        "density_increase": "density",
        "symmetry_creation": "density",
        "object_creation": "density",
        "symmetry_break": "density",
        "symbolic_remapping": "color_mapping",
        "color_mapping": "color_mapping",
    }

    def reason(
        self,
        *,
        concepts: list[str] | None = None,
        input_grid: Any = None,
        output_grid: Any = None,
        runtime_context: Mapping[str, Any] | None = None,
        transformation_theory_report: Mapping[str, Any] | None = None,
        transformation_explanation_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        concepts = list(dict.fromkeys(str(item) for item in concepts or []))
        theory_report = (
            transformation_theory_report
            if isinstance(transformation_theory_report, Mapping)
            else transformation_theory_engine.build_theory(concepts, runtime_context)
        )
        families = self._families(concepts)
        explanation = (
            transformation_explanation_report
            if isinstance(transformation_explanation_report, Mapping)
            else {}
        )
        selected_explanation = explanation.get("selected_explanation", {})
        if isinstance(selected_explanation, Mapping):
            for family in selected_explanation.get("mechanism_families", []) or []:
                if family in self.MECHANISM_LIBRARY and family not in families:
                    families.append(family)
        mechanisms = [
            self._mechanism_graph(
                family,
                concepts,
                input_grid,
                output_grid,
                theory_report,
                explanation,
            )
            for family in families
        ]
        executable = [item for item in mechanisms if item.get("execution_readiness", 0.0) > 0.0]
        return {
            "system": self.system_name,
            "MECHANISTIC_REASONING_REPORT": True,
            "input_concepts": concepts,
            "transformation_explanation_report": explanation,
            "transformation_theory_report": theory_report,
            "mechanism_count": len(mechanisms),
            "mechanism_families": families,
            "mechanism_graphs": mechanisms,
            "executable_mechanism_graphs": executable,
            "mechanistic_readiness": round(
                sum(item.get("execution_readiness", 0.0) for item in mechanisms)
                / max(len(mechanisms), 1),
                4,
            ),
            "unknown_sequence_resolved": bool(executable),
            "timestamp": str(datetime.utcnow()),
        }

    def _families(self, concepts):
        families = []
        for concept in concepts:
            family = self.CONCEPT_ALIASES.get(concept)
            if family and family not in families:
                families.append(family)
        return families

    def _mechanism_graph(
        self,
        family,
        concepts,
        input_grid,
        output_grid,
        theory_report,
        explanation_report,
    ):
        spec = self.MECHANISM_LIBRARY[family]
        theory = self._theory_for_family(family, theory_report)
        explanation = self._explanation_for_family(family, explanation_report)
        evidence = self._evidence(family, input_grid, output_grid)
        operations = self._operations(family, evidence)
        if theory:
            allowed = set(theory.get("canonical_operations", []) or [])
            operations = [operation for operation in operations if operation in allowed] or operations
        nodes = []
        edges = []
        for index, mechanism in enumerate(spec["candidate_mechanisms"]):
            nodes.append({
                "id": f"{family}:{mechanism}",
                "mechanism": mechanism,
                "status": "candidate",
                "evidence": evidence.get(mechanism, {}),
            })
            if index:
                edges.append({
                    "from": nodes[index - 1]["id"],
                    "to": nodes[index]["id"],
                    "relation": "mechanism_sequence",
                })
        readiness = self._readiness(family, evidence, operations)
        return {
            "family": family,
            "mechanism_type": spec["family"],
            "transformation_theory": theory,
            "transformation_explanation": explanation,
            "macro_concept": explanation.get("macro_concept") if explanation else None,
            "transformation_class": theory.get("transformation_class") if theory else None,
            "transformation_subtype": theory.get("subtype") if theory else None,
            "theory_constraints": theory.get("constraints", []) if theory else [],
            "theory_dependencies": theory.get("dependencies", []) if theory else [],
            "source_concepts": [
                concept for concept in concepts if self.CONCEPT_ALIASES.get(concept) == family
            ],
            "candidate_mechanisms": list(spec["candidate_mechanisms"]),
            "reference_frames": list(spec["reference_frames"]),
            "candidate_operations": operations,
            "nodes": nodes,
            "edges": edges,
            "causal_validation": {
                "validated": readiness >= 0.70,
                "score": readiness,
                "evidence_keys": sorted(evidence.keys()),
            },
            "execution_readiness": readiness,
        }

    def _theory_for_family(self, family, theory_report):
        family_to_class = {
            "gravity": "PHYSICS_TRANSFORMATION",
            "rotation": "SPATIAL_TRANSFORMATION",
            "object_counting": "QUANTITY_TRANSFORMATION",
            "density": "OBJECT_EXPANSION",
            "color_mapping": "SYMBOLIC_TRANSFORMATION",
        }
        expected = family_to_class.get(family)
        for theory in theory_report.get("transformation_theories", []) or []:
            if isinstance(theory, Mapping) and theory.get("transformation_class") == expected:
                return dict(theory)
        return {}

    def _explanation_for_family(self, family, explanation_report):
        selected = explanation_report.get("selected_explanation", {})
        if not isinstance(selected, Mapping):
            return {}
        families = selected.get("mechanism_families", []) or []
        return dict(selected) if family in families else {}

    def _operations(self, family, evidence):
        if family == "gravity":
            fall = evidence.get("downward_trajectory_simulation", {}).get("fall_distance", 0)
            return ["translate"] if fall else ["translate", "connect_components"]
        if family == "rotation":
            if evidence.get("rotation_angle_inference", {}).get("degrees"):
                return ["rotate"]
            return ["rotate", "mirror_horizontal", "mirror_vertical"]
        if family == "object_counting":
            delta = evidence.get("quantity_transformation", {}).get("count_delta", 0)
            if delta > 0:
                return ["duplicate"]
            if delta < 0:
                return ["remove_object"]
            return ["select_object"]
        if family == "density":
            return ["duplicate", "expand"]
        if family == "color_mapping":
            return ["recolor"]
        return []

    def _readiness(self, family, evidence, operations):
        if not operations:
            return 0.0
        if family == "gravity":
            score = 0.45
            if evidence.get("unsupported_object_detection", {}).get("unsupported_count", 0) > 0:
                score += 0.20
            if evidence.get("downward_trajectory_simulation", {}).get("fall_distance", 0) > 0:
                score += 0.25
            return round(min(score, 1.0), 4)
        if family == "rotation":
            return 0.90 if evidence.get("rotation_angle_inference", {}).get("degrees") else 0.55
        if family == "object_counting":
            score = 0.50
            if evidence.get("cardinality_extraction", {}).get("input_object_count", 0) > 0:
                score += 0.18
            if evidence.get("quantity_transformation", {}).get("count_delta", 0) != 0:
                score += 0.18
            return round(min(score, 1.0), 4)
        if family == "density":
            score = 0.58
            if evidence.get("density_modulation", {}).get("density_delta", 0.0) > 0:
                score += 0.20
            if evidence.get("symmetry_axis_selection", {}).get("symmetry_candidate"):
                score += 0.10
            return round(min(score, 1.0), 4)
        if family == "color_mapping":
            return 0.78 if evidence.get("mapping_rule_inference", {}).get("mapping_detected") else 0.55
        return 0.0

    def _evidence(self, family, input_grid, output_grid):
        source = self._array(input_grid)
        target = self._array(output_grid)
        if family == "gravity":
            return self._gravity_evidence(source, target)
        if family == "rotation":
            return self._rotation_evidence(source, target)
        if family == "object_counting":
            return self._counting_evidence(source, target)
        if family == "density":
            return self._density_evidence(source, target)
        if family == "color_mapping":
            return self._color_mapping_evidence(source, target)
        return {}

    def _gravity_evidence(self, source, target):
        fall_distance = self._vertical_shift(source, target)
        unsupported = 0
        if source.size:
            rows = source.shape[0]
            for row, col in np.argwhere(source != 0):
                if int(row) + 1 < rows and source[int(row) + 1, int(col)] == 0:
                    unsupported += 1
        return {
            "support_detection": {"axis": "down", "support_frame": "grid_boundary_or_nonzero_cell"},
            "unsupported_object_detection": {"unsupported_count": int(unsupported)},
            "downward_trajectory_simulation": {"fall_distance": int(max(fall_distance, 0))},
            "collision_resolution": {"collision_policy": "stop_at_support_or_boundary"},
            "rest_state_detection": {"rest_state": "support_or_boundary"},
            "topology_update": {"component_policy": "preserve_or_merge_on_contact"},
        }

    def _rotation_evidence(self, source, target):
        degrees = None
        if source.size and target.size:
            for candidate in (90, 180, 270):
                if np.array_equal(np.rot90(source, k=candidate // 90), target):
                    degrees = candidate
                    break
        return {
            "rotation_angle_inference": {"degrees": degrees},
            "rotation_center_selection": {"center": "grid_center"},
            "orientation_update": {"direction": "counter_clockwise"},
            "color_preservation": {"preserve_colors": True},
            "topology_preservation": {"preserve_topology": True},
        }

    def _counting_evidence(self, source, target):
        input_count = self._component_count(source)
        output_count = self._component_count(target)
        delta = output_count - input_count
        colors = self._color_counts(target)
        return {
            "object_grouping": {"grouping": "connected_components"},
            "cardinality_extraction": {
                "input_object_count": input_count,
                "output_object_count": output_count,
            },
            "quantity_rule_selection": {"rule": "count_delta" if delta else "count_preservation"},
            "quantity_preservation_check": {"preserved": delta == 0},
            "quantity_transformation": {
                "count_delta": delta,
                "dominant_output_color": colors.most_common(1)[0][0] if colors else None,
            },
        }

    def _density_evidence(self, source, target):
        source_count = int(np.sum(source != 0)) if source.size else 0
        target_count = int(np.sum(target != 0)) if target.size else 0
        source_density = source_count / max(source.size, 1) if source.size else 0.0
        target_density = target_count / max(target.size, 1) if target.size else 0.0
        return {
            "source_object_selection": {"source_nonzero_count": source_count},
            "expansion_mode_selection": {"mode": "duplicate_or_expand"},
            "symmetry_axis_selection": {"symmetry_candidate": self._has_symmetry(target)},
            "density_modulation": {"density_delta": round(target_density - source_density, 4)},
            "topology_update": {"target_nonzero_count": target_count},
        }

    def _color_mapping_evidence(self, source, target):
        mapping_detected = False
        mapping = {}
        if source.size and target.size and source.shape == target.shape:
            for value in sorted(set(int(item) for item in source.flatten()) - {0}):
                target_values = {
                    int(target[tuple(cell)])
                    for cell in np.argwhere(source == value)
                }
                if len(target_values) == 1:
                    mapped = next(iter(target_values))
                    if mapped != value:
                        mapping[str(value)] = mapped
            mapping_detected = bool(mapping)
        return {
            "symbol_class_detection": {"source_symbols": sorted(mapping.keys())},
            "mapping_rule_inference": {"mapping_detected": mapping_detected, "mapping": mapping},
            "color_substitution": {"mapping": mapping},
            "shape_preservation": {"preserve_shape": bool(source.size and target.size and source.shape == target.shape)},
            "position_preservation": {"preserve_position": True},
        }

    def _has_symmetry(self, array):
        if not array.size:
            return False
        return bool(np.array_equal(array, np.fliplr(array)) or np.array_equal(array, np.flipud(array)))

    def _vertical_shift(self, source, target):
        if not source.size or not target.size:
            return 0
        source_cells = np.argwhere(source != 0)
        target_cells = np.argwhere(target != 0)
        if len(source_cells) == 0 or len(source_cells) != len(target_cells):
            return 0
        source_colors = sorted(int(source[tuple(cell)]) for cell in source_cells)
        target_colors = sorted(int(target[tuple(cell)]) for cell in target_cells)
        if source_colors != target_colors:
            return 0
        return int(round(float(target_cells[:, 0].mean() - source_cells[:, 0].mean())))

    def _component_count(self, array):
        if not array.size:
            return 0
        visited = set()
        count = 0
        rows, cols = array.shape[:2]
        for row in range(rows):
            for col in range(cols):
                if array[row, col] == 0 or (row, col) in visited:
                    continue
                count += 1
                color = array[row, col]
                stack = [(row, col)]
                while stack:
                    r, c = stack.pop()
                    if (r, c) in visited or r < 0 or r >= rows or c < 0 or c >= cols:
                        continue
                    if array[r, c] != color:
                        continue
                    visited.add((r, c))
                    stack.extend([(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)])
        return count

    def _color_counts(self, array):
        if not array.size:
            return Counter()
        return Counter(int(value) for value in array.flatten() if int(value) != 0)

    def _array(self, grid):
        if grid is None:
            return np.array([])
        if hasattr(grid, "grid"):
            return np.array(grid.grid)
        return np.array(grid)


mechanistic_reasoning_engine = MechanisticReasoningEngine()


__all__ = [
    "MechanisticReasoningEngine",
    "mechanistic_reasoning_engine",
]
