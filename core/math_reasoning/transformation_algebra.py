"""Passive symbolic transformation algebra for ARC-style objects."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.math_reasoning.graph_relations import GraphRelationsEngine
from core.math_reasoning.set_operations import SetOperationsEngine
from core.math_reasoning.spatial_relations import SpatialRelationsEngine, normalize_object


Operator = dict[str, Any]


SUPPORTED_OPERATORS = {
    "identity",
    "translate",
    "rotate_90",
    "rotate_180",
    "rotate_270",
    "flip_horizontal",
    "flip_vertical",
    "mirror",
    "scale",
    "recolor",
    "duplicate",
    "crop",
    "expand",
    "contract",
    "erase",
    "fill",
    "move",
    "compose",
}


TRANSFORMATION_TYPES = {
    "translation",
    "rotation",
    "reflection",
    "scaling",
    "propagation",
    "replication",
    "topology_expansion",
    "growth",
    "topological_growth",
    "identity",
}


class TransformationAlgebraEngine:
    """Represent ARC transformations as composable symbolic operators."""

    system_name = "transformation_algebra_engine"

    def normalize_operator(self, operator: Any) -> Operator:
        if isinstance(operator, str):
            operator = {"operator": operator}
        source = operator.get("source") if isinstance(operator, Mapping) else None
        target = operator.get("target") if isinstance(operator, Mapping) else None
        name = str(operator.get("operator", "identity")) if isinstance(operator, Mapping) else "identity"
        if name not in SUPPORTED_OPERATORS:
            name = "identity"
        parameters = dict(operator.get("parameters", {})) if isinstance(operator, Mapping) else {}
        normalized: Operator = {
            "operator": name,
            "parameters": _normalize_parameters(parameters),
            "source": source,
            "target": target,
            "confidence": round(float(operator.get("confidence", 1.0)), 4) if isinstance(operator, Mapping) else 1.0,
        }
        if name == "compose":
            sequence = operator.get("sequence", []) if isinstance(operator, Mapping) else []
            normalized["sequence"] = [self.normalize_operator(item) for item in sequence]
        return normalized

    def apply_operator(self, object_item: Mapping[str, Any] | None, operator: Mapping[str, Any]) -> dict[str, Any] | None:
        op = self.normalize_operator(operator)
        if op["operator"] == "erase":
            return None
        if object_item is None:
            return None
        obj = normalize_object(object_item)
        name = op["operator"]
        params = op["parameters"]
        if name == "compose":
            current: dict[str, Any] | None = obj
            for item in op.get("sequence", []):
                current = self.apply_operator(current, item)
                if current is None:
                    return None
            return current
        if name in {"identity", "duplicate"}:
            return dict(obj)
        if name in {"translate", "move"}:
            return self._translate_object(obj, float(params.get("delta_row", 0)), float(params.get("delta_col", 0)))
        if name == "recolor":
            result = dict(obj)
            result["color"] = params.get("to_color", obj.get("color"))
            return normalize_object(result)
        if name in {"rotate_90", "rotate_180", "rotate_270"}:
            turns = {"rotate_90": 1, "rotate_180": 2, "rotate_270": 3}[name]
            return self._transform_cells(obj, lambda row, col: _rotate_cell(row, col, turns))
        if name in {"flip_horizontal", "mirror"}:
            return self._transform_cells(obj, lambda row, col: (row, -col))
        if name == "flip_vertical":
            return self._transform_cells(obj, lambda row, col: (-row, col))
        if name == "scale":
            factor = int(params.get("factor", 1))
            return self._scale_object(obj, factor)
        return dict(obj)

    def infer_operator(
        self,
        input_object: Mapping[str, Any] | None,
        output_object: Mapping[str, Any] | None,
    ) -> Operator:
        if input_object is None and output_object is None:
            return self.normalize_operator({"operator": "identity"})
        if input_object is not None and output_object is None:
            source = input_object.get("id")
            return self.normalize_operator({"operator": "erase", "source": source, "target": None})
        if input_object is None and output_object is not None:
            target = output_object.get("id")
            return self.normalize_operator({"operator": "duplicate", "source": None, "target": target})

        source = normalize_object(input_object or {})
        target = normalize_object(output_object or {})
        base = {"source": source["id"], "target": target["id"], "confidence": 1.0}
        source_shape = _normalized_shape(source["cells"])
        target_shape = _normalized_shape(target["cells"])
        same_shape = source_shape == target_shape
        same_position = source["center"] == target["center"]
        same_color = source.get("color") == target.get("color")

        if same_shape and same_position and same_color:
            return self.normalize_operator({"operator": "identity", **base})
        if same_shape and not same_position:
            vector = SpatialRelationsEngine().compute_direction_vector(source, target)
            return self.normalize_operator(
                {
                    "operator": "translate",
                    "parameters": {
                        "delta_row": vector["delta_row"],
                        "delta_col": vector["delta_col"],
                    },
                    **base,
                }
            )
        if same_shape and same_position and not same_color:
            return self.normalize_operator(
                {
                    "operator": "recolor",
                    "parameters": {
                        "from_color": source.get("color"),
                        "to_color": target.get("color"),
                    },
                    **base,
                }
            )

        shape_operator = self._infer_shape_operator(source, target)
        if shape_operator:
            shape_operator.update(base)
            if not same_color:
                return self.compose(
                    shape_operator,
                    {
                        "operator": "recolor",
                        "parameters": {
                            "from_color": source.get("color"),
                            "to_color": target.get("color"),
                        },
                        **base,
                    },
                )
            return self.normalize_operator(shape_operator)

        if target.get("area", 0) > source.get("area", 0):
            return self.normalize_operator({"operator": "expand", **base})
        if target.get("area", 0) < source.get("area", 0):
            return self.normalize_operator({"operator": "contract", **base})
        return self.normalize_operator({"operator": "move", **base})

    def compose(self, operator_a: Mapping[str, Any], operator_b: Mapping[str, Any]) -> Operator:
        first = self.normalize_operator(operator_a)
        second = self.normalize_operator(operator_b)
        if first["operator"] == "identity":
            return second
        if second["operator"] == "identity":
            return first
        sequence = []
        sequence.extend(first.get("sequence", [first]) if first["operator"] == "compose" else [first])
        sequence.extend(second.get("sequence", [second]) if second["operator"] == "compose" else [second])
        return self.normalize_operator(
            {
                "operator": "compose",
                "sequence": sequence,
                "source": first.get("source"),
                "target": second.get("target"),
                "confidence": min(first.get("confidence", 1.0), second.get("confidence", 1.0)),
            }
        )

    def invert(self, operator: Mapping[str, Any]) -> Operator:
        op = self.normalize_operator(operator)
        name = op["operator"]
        params = op["parameters"]
        if name == "translate":
            return self.normalize_operator(
                {
                    **op,
                    "parameters": {
                        "delta_row": -float(params.get("delta_row", 0)),
                        "delta_col": -float(params.get("delta_col", 0)),
                    },
                }
            )
        if name == "move":
            return self.normalize_operator({**op, "operator": "move"})
        if name == "recolor":
            return self.normalize_operator(
                {
                    **op,
                    "parameters": {
                        "from_color": params.get("to_color"),
                        "to_color": params.get("from_color"),
                    },
                }
            )
        inverse_names = {
            "identity": "identity",
            "rotate_90": "rotate_270",
            "rotate_180": "rotate_180",
            "rotate_270": "rotate_90",
            "flip_horizontal": "flip_horizontal",
            "flip_vertical": "flip_vertical",
            "mirror": "mirror",
            "duplicate": "erase",
            "erase": "duplicate",
            "expand": "contract",
            "contract": "expand",
            "fill": "erase",
            "crop": "expand",
        }
        if name == "compose":
            return self.normalize_operator(
                {
                    "operator": "compose",
                    "sequence": [self.invert(item) for item in reversed(op.get("sequence", []))],
                    "source": op.get("target"),
                    "target": op.get("source"),
                    "confidence": op.get("confidence", 1.0),
                }
            )
        return self.normalize_operator({**op, "operator": inverse_names.get(name, "identity")})

    def operators_equivalent(self, operator_a: Mapping[str, Any], operator_b: Mapping[str, Any]) -> bool:
        return self.operator_signature(operator_a) == self.operator_signature(operator_b)

    def operator_signature(self, operator: Mapping[str, Any]) -> dict[str, Any]:
        op = self.normalize_operator(operator)
        signature = {
            "operator": op["operator"],
            "parameters": op["parameters"],
        }
        if op["operator"] == "compose":
            signature["sequence"] = [self.operator_signature(item) for item in op.get("sequence", [])]
        return signature

    def transformation_signature(
        self,
        input_objects: Iterable[Mapping[str, Any]],
        output_objects: Iterable[Mapping[str, Any]],
    ) -> dict[str, Any]:
        input_list = [normalize_object(obj, fallback_id=f"input_{index + 1}") for index, obj in enumerate(input_objects)]
        output_list = [normalize_object(obj, fallback_id=f"output_{index + 1}") for index, obj in enumerate(output_objects)]
        operators = self._infer_object_operators(input_list, output_list)
        operator_types = sorted({op["operator"] for op in operators})
        algebra = self.classify_transformation(
            {
                "operator_types": operator_types,
                "position_change": any(
                    not self._operator_preserves_position(op)
                    for op in operators
                ),
                "object_count_constant": len(input_list) == len(output_list),
                "object_count_increase": len(output_list) > len(input_list),
                "source_pattern_preserved": False,
                "identity_persistence": len(input_list) == len(output_list),
                "identity_forking": len(output_list) > len(input_list),
                "topology_expansion": any(
                    op["operator"] in {"expand", "duplicate", "scale"}
                    for op in operators
                ),
            }
        )
        return {
            "system": self.system_name,
            "transformation_count": len(operators),
            "operators": operators,
            "transformation_algebra": algebra,
            "transformation_signature": {
                "operator_types": operator_types,
                "has_composition": any(op["operator"] == "compose" for op in operators),
                "preserves_shape": all(self._operator_preserves_shape(op) for op in operators),
                "preserves_position": all(self._operator_preserves_position(op) for op in operators),
                "preserves_color": all(self._operator_preserves_color(op) for op in operators),
                "changes_object_count": len(input_list) != len(output_list),
                "transformation_types": algebra["transformation_types"],
                "primary_transformation_type": algebra["primary_transformation_type"],
                "invariants": algebra["invariants"],
                "algebraic_signature": algebra["algebraic_signature"],
            },
        }

    def classify_transformation(
        self,
        evidence: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        evidence = evidence if isinstance(evidence, Mapping) else {}
        operator_types = {
            str(item)
            for item in evidence.get("operator_types", [])
            if item
        }
        signals = {
            "position_change": _truthy(evidence, "position_change")
            or bool(operator_types & {"translate", "move"}),
            "object_count_constant": _truthy(evidence, "object_count_constant"),
            "object_count_increase": _truthy(evidence, "object_count_increase")
            or _truthy(evidence, "object_count_change")
            or bool(operator_types & {"duplicate"}),
            "source_pattern_preserved": _truthy(
                evidence,
                "source_pattern_preserved",
            ),
            "identity_persistence": _truthy(evidence, "identity_persistence")
            or _truthy(evidence, "identity_continuity"),
            "identity_forking": _truthy(evidence, "identity_forking")
            or _truthy(evidence, "identity_split")
            or bool(operator_types & {"duplicate"}),
            "topology_expansion": _truthy(evidence, "topology_expansion")
            or bool(operator_types & {"expand", "scale"}),
        }
        concept = str(evidence.get("concept", "")).strip().lower()
        types = self._classify_types(operator_types, signals, concept=concept)
        invariants = self._infer_invariants(operator_types, signals, types)
        algebraic_signature = self._algebraic_signature(types, invariants, signals)
        return {
            "system": self.system_name,
            "transformation_algebra_generated": bool(types),
            "transformation_types": types,
            "primary_transformation_type": types[0] if types else "unknown",
            "invariants": invariants,
            "algebraic_signature": algebraic_signature,
            "signals": signals,
            "operator_types": sorted(operator_types),
            "concept": concept,
            "identity_scope_leakage_detected": (
                invariants["preserves_identity"]
                and invariants["forks_identity"]
            ),
        }

    def compare_transformations(
        self,
        transformation_a: Mapping[str, Any],
        transformation_b: Mapping[str, Any],
    ) -> dict[str, Any]:
        sig_a = self.operator_signature(transformation_a)
        sig_b = self.operator_signature(transformation_b)
        params_a = sig_a.get("parameters", {})
        params_b = sig_b.get("parameters", {})
        return {
            "system": self.system_name,
            "operator_a": sig_a,
            "operator_b": sig_b,
            "equivalent": sig_a == sig_b,
            "same_operator_type": sig_a["operator"] == sig_b["operator"],
            "parameter_changes": {
                key: {"from": params_a.get(key), "to": params_b.get(key)}
                for key in sorted(set(params_a) | set(params_b))
                if params_a.get(key) != params_b.get(key)
            },
            "conflict": self._operators_conflict(sig_a, sig_b),
        }

    def explain_transformation(self, operator: Mapping[str, Any]) -> dict[str, Any]:
        op = self.normalize_operator(operator)
        name = op["operator"]
        params = op["parameters"]
        descriptions = {
            "identity": "Object is preserved without spatial, color, or shape change.",
            "translate": f"Object shifts by row {params.get('delta_row', 0)} and column {params.get('delta_col', 0)}.",
            "recolor": f"Object color changes from {params.get('from_color')} to {params.get('to_color')}.",
            "rotate_90": "Object shape rotates 90 degrees clockwise.",
            "rotate_180": "Object shape rotates 180 degrees.",
            "rotate_270": "Object shape rotates 270 degrees clockwise.",
            "flip_horizontal": "Object shape flips horizontally.",
            "flip_vertical": "Object shape flips vertically.",
            "mirror": "Object shape is mirrored horizontally.",
            "duplicate": "Object is copied or newly introduced from a source pattern.",
            "erase": "Object is removed.",
            "expand": "Object gains cells or area.",
            "contract": "Object loses cells or area.",
            "compose": "Multiple operators are applied in sequence.",
        }
        return {
            "system": self.system_name,
            "operator": name,
            "parameters": params,
            "explanation": descriptions.get(name, f"Operator {name} is applied."),
            "preserves_shape": self._operator_preserves_shape(op),
            "preserves_position": self._operator_preserves_position(op),
            "preserves_color": self._operator_preserves_color(op),
        }

    def explain_transformation_sequence(self, operators: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        sequence = [self.normalize_operator(operator) for operator in operators]
        return {
            "system": self.system_name,
            "sequence_length": len(sequence),
            "operators": sequence,
            "explanations": [self.explain_transformation(operator) for operator in sequence],
            "composition": self.normalize_operator({"operator": "compose", "sequence": sequence}) if sequence else self.normalize_operator("identity"),
        }

    def analyze_pipeline_sets(self, input_objects: Iterable[Mapping[str, Any]], output_objects: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        spatial = SpatialRelationsEngine().analyze(input_objects)
        graph = GraphRelationsEngine().build_graph(input_objects, spatial)
        object_set = SetOperationsEngine().analyze_from_graph(graph)
        transformation = self.transformation_signature(input_objects, output_objects)
        return {
            "system": self.system_name,
            "spatial_signature": spatial["spatial_signature"],
            "graph_signature": graph["graph_signature"],
            "object_set_signature": object_set,
            "transformation_signature": transformation["transformation_signature"],
        }

    def _infer_object_operators(self, input_objects: list[dict[str, Any]], output_objects: list[dict[str, Any]]) -> list[Operator]:
        operators = []
        used_outputs: set[int] = set()
        for input_obj in input_objects:
            best_index = self._best_output_match(input_obj, output_objects, used_outputs)
            if best_index is None:
                operators.append(self.infer_operator(input_obj, None))
                continue
            used_outputs.add(best_index)
            operators.append(self.infer_operator(input_obj, output_objects[best_index]))
        for index, output_obj in enumerate(output_objects):
            if index not in used_outputs:
                operators.append(self.infer_operator(None, output_obj))
        return operators

    def _best_output_match(self, input_obj: Mapping[str, Any], output_objects: list[dict[str, Any]], used_outputs: set[int]) -> int | None:
        best_index = None
        best_score = -1
        input_shape = _normalized_shape(input_obj.get("cells", []))
        for index, output_obj in enumerate(output_objects):
            if index in used_outputs:
                continue
            score = 0
            if input_obj.get("id") == output_obj.get("id"):
                score += 5
            if input_obj.get("color") == output_obj.get("color"):
                score += 2
            if input_shape == _normalized_shape(output_obj.get("cells", [])):
                score += 3
            if input_obj.get("area") == output_obj.get("area"):
                score += 1
            if score > best_score:
                best_score = score
                best_index = index
        return best_index if best_score > 0 else None

    def _infer_shape_operator(self, source: Mapping[str, Any], target: Mapping[str, Any]) -> Operator | None:
        source_shape = _normalized_shape(source["cells"])
        target_shape = _normalized_shape(target["cells"])
        candidates = {
            "rotate_90": _normalize_cells([_rotate_cell(row, col, 1) for row, col in source_shape]),
            "rotate_180": _normalize_cells([_rotate_cell(row, col, 2) for row, col in source_shape]),
            "rotate_270": _normalize_cells([_rotate_cell(row, col, 3) for row, col in source_shape]),
            "flip_horizontal": _normalize_cells([(row, -col) for row, col in source_shape]),
            "flip_vertical": _normalize_cells([(-row, col) for row, col in source_shape]),
            "mirror": _normalize_cells([(row, -col) for row, col in source_shape]),
        }
        for name, candidate_shape in candidates.items():
            if candidate_shape == target_shape:
                return {"operator": name}
        return None

    def _translate_object(self, obj: Mapping[str, Any], delta_row: float, delta_col: float) -> dict[str, Any]:
        result = dict(obj)
        result["cells"] = [
            (int(row + delta_row), int(col + delta_col))
            for row, col in obj.get("cells", [])
        ]
        return normalize_object(result)

    def _transform_cells(self, obj: Mapping[str, Any], transform: Any) -> dict[str, Any]:
        result = dict(obj)
        result["cells"] = _normalize_cells([transform(row, col) for row, col in _normalized_shape(obj.get("cells", []))])
        return normalize_object(result)

    def _scale_object(self, obj: Mapping[str, Any], factor: int) -> dict[str, Any]:
        if factor <= 1:
            return dict(obj)
        scaled = []
        for row, col in _normalized_shape(obj.get("cells", [])):
            for d_row in range(factor):
                for d_col in range(factor):
                    scaled.append((row * factor + d_row, col * factor + d_col))
        result = dict(obj)
        result["cells"] = scaled
        return normalize_object(result)

    def _operator_preserves_shape(self, operator: Mapping[str, Any]) -> bool:
        op = self.normalize_operator(operator)
        if op["operator"] == "compose":
            return all(self._operator_preserves_shape(item) for item in op.get("sequence", []))
        return op["operator"] in {
            "identity",
            "translate",
            "move",
            "recolor",
            "rotate_90",
            "rotate_180",
            "rotate_270",
            "flip_horizontal",
            "flip_vertical",
            "mirror",
            "duplicate",
        }

    def _operator_preserves_position(self, operator: Mapping[str, Any]) -> bool:
        op = self.normalize_operator(operator)
        if op["operator"] == "compose":
            return all(self._operator_preserves_position(item) for item in op.get("sequence", []))
        return op["operator"] not in {
            "translate",
            "move",
            "rotate_90",
            "rotate_180",
            "rotate_270",
            "flip_horizontal",
            "flip_vertical",
            "mirror",
            "duplicate",
            "erase",
        }

    def _operator_preserves_color(self, operator: Mapping[str, Any]) -> bool:
        op = self.normalize_operator(operator)
        if op["operator"] == "compose":
            return all(self._operator_preserves_color(item) for item in op.get("sequence", []))
        return op["operator"] != "recolor"

    def _operators_conflict(self, operator_a: Mapping[str, Any], operator_b: Mapping[str, Any]) -> bool:
        if operator_a["operator"] != operator_b["operator"]:
            return False
        return operator_a.get("parameters", {}) != operator_b.get("parameters", {})

    def _classify_types(
        self,
        operator_types: set[str],
        signals: Mapping[str, bool],
        concept: str = "",
    ) -> list[str]:
        types = []
        if (
            concept == "replication"
            and signals.get("object_count_increase")
            and signals.get("identity_forking")
        ):
            types.append("replication")
        if concept == "propagation" and signals.get("source_pattern_preserved"):
            types.append("propagation")
        if concept == "growth" and signals.get("topology_expansion"):
            types.append("growth")
        if concept == "topological_growth" and signals.get("topology_expansion"):
            types.append("topological_growth")
        if operator_types & {"rotate_90", "rotate_180", "rotate_270"}:
            types.append("rotation")
        if operator_types & {"flip_horizontal", "flip_vertical", "mirror"}:
            types.append("reflection")
        if operator_types & {"scale"}:
            types.append("scaling")
        if signals.get("topology_expansion") and signals.get("identity_forking"):
            types.append("topological_growth")
        elif signals.get("topology_expansion") and signals.get("identity_persistence"):
            types.append("growth")
        elif signals.get("topology_expansion"):
            types.append("topology_expansion")
        if signals.get("position_change") and signals.get("source_pattern_preserved"):
            types.append("propagation")
        elif signals.get("position_change") and signals.get("object_count_constant"):
            types.append("translation")
        if signals.get("object_count_increase") and signals.get("identity_forking"):
            types.append("replication")
        if not types and operator_types <= {"identity"}:
            types.append("identity")
        return _dedupe(types)

    def _infer_invariants(
        self,
        operator_types: set[str],
        signals: Mapping[str, bool],
        types: Iterable[str],
    ) -> dict[str, bool]:
        type_set = set(types)
        forks_identity = bool(
            signals.get("identity_forking")
            or "replication" in type_set
            or "topological_growth" in type_set
        )
        modifies_topology = bool(
            signals.get("topology_expansion")
            or type_set & {"growth", "topological_growth", "topology_expansion"}
        )
        preserves_identity = bool(
            signals.get("identity_persistence")
            and not forks_identity
        )
        preserves_topology = not modifies_topology
        preserves_shape = bool(
            signals.get("source_pattern_preserved")
            or operator_types
            <= {
                "identity",
                "translate",
                "move",
                "recolor",
                "duplicate",
            }
        )
        preserves_position = not bool(
            signals.get("position_change")
            or operator_types
            & {
                "translate",
                "move",
                "rotate_90",
                "rotate_180",
                "rotate_270",
                "flip_horizontal",
                "flip_vertical",
                "mirror",
                "duplicate",
                "erase",
            }
        )
        return {
            "preserves_identity": preserves_identity,
            "forks_identity": forks_identity,
            "preserves_topology": preserves_topology,
            "modifies_topology": modifies_topology,
            "preserves_shape": preserves_shape,
            "preserves_position": preserves_position,
        }

    def _algebraic_signature(
        self,
        types: Iterable[str],
        invariants: Mapping[str, bool],
        signals: Mapping[str, bool],
    ) -> str:
        type_part = "+".join(types) if types else "unknown"
        invariant_part = "+".join(
            key
            for key in [
                "preserves_identity",
                "forks_identity",
                "preserves_topology",
                "modifies_topology",
                "preserves_shape",
                "preserves_position",
            ]
            if invariants.get(key)
        )
        signal_part = "+".join(
            key
            for key in sorted(signals)
            if signals.get(key)
        )
        return f"{type_part}|{invariant_part}|{signal_part}"


def _normalize_parameters(parameters: Mapping[str, Any]) -> dict[str, Any]:
    normalized = {}
    for key, value in sorted(parameters.items()):
        if isinstance(value, float) and value.is_integer():
            normalized[str(key)] = int(value)
        else:
            normalized[str(key)] = value
    return normalized


def _truthy(evidence: Mapping[str, Any], key: str) -> bool:
    value = evidence.get(key)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", key}
    return bool(value)


def _dedupe(values: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _normalized_shape(cells: Iterable[Any]) -> tuple[tuple[int, int], ...]:
    normalized = []
    for cell in cells or []:
        if len(cell) >= 2:
            normalized.append((int(cell[0]), int(cell[1])))
    if not normalized:
        return ()
    min_row = min(row for row, _ in normalized)
    min_col = min(col for _, col in normalized)
    return tuple(sorted((row - min_row, col - min_col) for row, col in normalized))


def _normalize_cells(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cell_list = list(cells)
    if not cell_list:
        return ()
    min_row = min(row for row, _ in cell_list)
    min_col = min(col for _, col in cell_list)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cell_list))


def _rotate_cell(row: int, col: int, turns: int) -> tuple[int, int]:
    result = (row, col)
    for _ in range(turns % 4):
        result = (result[1], -result[0])
    return result


__all__ = ["TransformationAlgebraEngine"]
