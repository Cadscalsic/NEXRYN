from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from typing import Any


TASK_FAMILIES = {
    "color_mapping",
    "object_duplication",
    "object_movement",
    "shape_preservation",
    "topology_preservation",
    "symmetry",
    "rotation_reflection",
    "scaling",
    "counting",
    "inside_outside",
    "gravity_simulation",
    "pattern_completion",
    "symbolic_remapping",
    "unknown_complex",
}


@dataclass
class RuntimeTaskProfile:
    task_id: str
    task_family: str
    required_capabilities: list[str] = field(default_factory=list)
    suspected_concepts: list[str] = field(default_factory=list)
    grid_complexity: float = 0.0
    object_count: int = 0
    color_count: int = 0
    spatial_complexity: float = 0.0
    requires_object_detection: bool = False
    requires_spatial_reasoning: bool = False
    requires_color_mapping: bool = False
    requires_topology_reasoning: bool = False
    requires_symmetry_reasoning: bool = False
    requires_counting: bool = False
    requires_growth_reasoning: bool = False
    requires_gravity_reasoning: bool = False
    requires_context_discovery: bool = False
    requires_truth_promotion: bool = False
    requires_governance: bool = False
    requires_cache_lookup: bool = True
    requires_world_model: bool = False
    confidence: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_task_profile(task: dict[str, Any] | None, context: dict[str, Any] | None = None) -> dict[str, Any]:
    task = task if isinstance(task, dict) else {}
    context = context if isinstance(context, dict) else {}
    merged = {**task, **context}
    input_grid = _grid(
        merged.get("input_grid")
        or _nested_get(merged, "train_example", "input")
        or _nested_get(merged, "input")
    )
    output_grid = _grid(
        merged.get("output_grid")
        or _nested_get(merged, "train_example", "output")
        or _nested_get(merged, "output")
    )
    input_colors = _colors(input_grid)
    output_colors = _colors(output_grid)
    color_count = len(input_colors | output_colors)
    object_count = max(_object_count(input_grid), _object_count(output_grid))
    grid_complexity = _grid_complexity(input_grid, output_grid)
    spatial_complexity = _spatial_complexity(input_grid, output_grid)
    task_family, confidence, suspected = _detect_family(
        input_grid,
        output_grid,
        input_colors,
        output_colors,
        object_count,
        spatial_complexity,
    )
    explicit_signals = _explicit_structural_signals(merged)
    suspected = list(dict.fromkeys([*suspected, *explicit_signals]))
    capabilities = list(dict.fromkeys([
        *_capabilities_for(task_family),
        *_capabilities_for_signals(explicit_signals),
    ]))
    if explicit_signals and task_family == "color_mapping":
        confidence = min(confidence, 0.69)
    profile = RuntimeTaskProfile(
        task_id=str(
            merged.get("task_id")
            or merged.get("task_path")
            or _stable_hash({"input": input_grid, "output": output_grid})[:16]
        ),
        task_family=task_family,
        required_capabilities=capabilities,
        suspected_concepts=suspected,
        grid_complexity=grid_complexity,
        object_count=object_count,
        color_count=color_count,
        spatial_complexity=spatial_complexity,
        requires_object_detection=object_count > 0,
        requires_spatial_reasoning=task_family in {
            "object_movement",
            "rotation_reflection",
            "scaling",
            "inside_outside",
            "gravity_simulation",
            "topology_preservation",
            "unknown_complex",
        } or spatial_complexity >= 0.18 or bool(
            set(explicit_signals)
            & {
                "topology",
                "topological",
                "symmetry",
                "reflection",
                "rotation",
                "inside_outside",
                "structural transformation",
            }
        ),
        requires_color_mapping=task_family in {"color_mapping", "symbolic_remapping"},
        requires_topology_reasoning=task_family in {
            "topology_preservation",
            "inside_outside",
            "object_duplication",
            "unknown_complex",
        } or bool(
            set(explicit_signals)
            & {
                "topology",
                "topological",
                "topology_preservation",
                "topology preservation",
                "topological_growth",
                "topological growth",
            }
        ),
        requires_symmetry_reasoning=(
            task_family in {"symmetry", "rotation_reflection"}
            or bool(
                set(explicit_signals)
                & {
                    "symmetry",
                    "symmetry_preservation",
                    "symmetry preservation",
                    "reflection",
                    "rotation",
                }
            )
        ),
        requires_counting=(
            task_family in {"counting", "object_duplication"}
            or "counting" in explicit_signals
        ),
        requires_growth_reasoning=(
            task_family in {"object_duplication", "scaling", "pattern_completion"}
            or bool(set(explicit_signals) & {"growth", "topological_growth"})
        ),
        requires_gravity_reasoning=task_family == "gravity_simulation",
        requires_context_discovery=(
            task_family == "unknown_complex"
            or confidence < 0.55
            or bool(
                set(explicit_signals)
                & {
                    "propagation",
                    "causality",
                    "causal",
                    "dependency",
                    "dependencies",
                    "context-sensitive transformations",
                    "context sensitive transformations",
                    "symbolic_remapping",
                    "symbolic remapping",
                }
            )
        ),
        requires_truth_promotion=False,
        requires_governance=task_family == "unknown_complex" or confidence < 0.45,
        requires_cache_lookup=True,
        requires_world_model=task_family in {
            "object_movement",
            "gravity_simulation",
            "pattern_completion",
            "unknown_complex",
        },
        confidence=confidence,
    )
    return profile.as_dict()


def _capabilities_for(task_family: str) -> list[str]:
    mapping = {
        "color_mapping": ["color_analysis", "transformation_solver", "evaluation"],
        "object_duplication": ["object_detection", "counting", "topology_reasoning"],
        "object_movement": ["object_detection", "spatial_reasoning", "world_model"],
        "shape_preservation": ["object_detection", "shape_analysis"],
        "topology_preservation": ["object_detection", "topology_reasoning"],
        "symmetry": ["spatial_reasoning", "symmetry_reasoning"],
        "rotation_reflection": ["spatial_reasoning", "symmetry_reasoning"],
        "scaling": ["spatial_reasoning", "growth_reasoning"],
        "counting": ["object_detection", "counting"],
        "inside_outside": ["object_detection", "spatial_reasoning", "topology_reasoning"],
        "gravity_simulation": ["object_detection", "gravity_reasoning", "world_model"],
        "pattern_completion": ["pattern_reasoning", "world_model"],
        "symbolic_remapping": ["color_analysis", "symbolic_reasoning"],
        "unknown_complex": ["object_detection", "spatial_reasoning", "dependency_reasoning", "context_discovery"],
    }
    return mapping.get(task_family, mapping["unknown_complex"])


def _capabilities_for_signals(signals: list[str]) -> list[str]:
    capabilities = []
    signal_text = " ".join(signals)
    if any(value in signal_text for value in ["topology", "topological"]):
        capabilities.extend(["topology_reasoning", "dependency_reasoning"])
    if "symmetry" in signal_text or "reflection" in signal_text or "rotation" in signal_text:
        capabilities.extend(["symmetry_reasoning", "dependency_reasoning"])
    if "growth" in signal_text or "scaling" in signal_text:
        capabilities.extend(["growth_reasoning", "dependency_reasoning"])
    if "counting" in signal_text:
        capabilities.extend(["counting", "dependency_reasoning"])
    if "symbolic" in signal_text:
        capabilities.extend(["symbolic_reasoning", "context_discovery"])
    if any(value in signal_text for value in ["causal", "propagation", "dependency", "relation"]):
        capabilities.extend(["dependency_reasoning", "context_discovery"])
    if "shape" in signal_text or "object interaction" in signal_text:
        capabilities.extend(["object_detection", "shape_analysis", "dependency_reasoning"])
    return capabilities


def _explicit_structural_signals(merged: dict[str, Any]) -> list[str]:
    signals = []
    fields = [
        "task_family",
        "concept",
        "task_description",
        "prompt",
        "claim",
    ]
    values = [merged.get(field) for field in fields]
    for key in (
        "required_capabilities",
        "suspected_concepts",
        "semantic_abstractions",
        "prioritized_concepts",
    ):
        value = merged.get(key)
        if isinstance(value, list):
            values.extend(value)
    text = " ".join(str(value or "").lower() for value in values)
    candidates = [
        "topology",
        "topological",
        "symmetry",
        "reflection",
        "rotation",
        "object interaction",
        "propagation",
        "causality",
        "causal",
        "counting",
        "growth",
        "scaling",
        "inside_outside",
        "structural transformation",
        "shape_preservation",
        "shape preservation",
        "topology_preservation",
        "topology preservation",
        "symmetry_preservation",
        "symmetry preservation",
        "symbolic_remapping",
        "symbolic remapping",
        "multi-object relations",
        "context-sensitive transformations",
        "dependency",
        "dependencies",
        "relation",
        "relations",
        "topological_growth",
        "topological growth",
    ]
    for candidate in candidates:
        if candidate in text:
            signals.append(candidate)
    return list(dict.fromkeys(signals))


def _detect_family(input_grid, output_grid, input_colors, output_colors, object_count, spatial_complexity):
    if not input_grid or not output_grid:
        return "unknown_complex", 0.35, ["unknown_task"]
    if _same_shape(input_grid, output_grid) and input_colors != output_colors and _nonzero_positions(input_grid) == _nonzero_positions(output_grid):
        return "color_mapping", 0.88, ["color_mapping", "symbolic_remapping"]
    if _same_shape(input_grid, output_grid) and len(output_colors - input_colors) == 1 and len(input_colors - output_colors) == 1:
        return "symbolic_remapping", 0.78, ["symbolic_remapping", "color_transformation"]
    in_cells = _nonzero_count(input_grid)
    out_cells = _nonzero_count(output_grid)
    if out_cells > in_cells and object_count <= 3:
        return "object_duplication", 0.72, ["replication", "growth", "counting"]
    if _same_multiset_nonzero(input_grid, output_grid) and _nonzero_positions(input_grid) != _nonzero_positions(output_grid):
        return "object_movement", 0.74, ["position_change", "object_motion"]
    if _same_shape(input_grid, output_grid) and in_cells == out_cells and spatial_complexity < 0.08:
        return "shape_preservation", 0.68, ["shape_preservation"]
    if _has_symmetry(output_grid):
        return "symmetry", 0.66, ["symmetry"]
    if _shape_scale_changed(input_grid, output_grid):
        return "scaling", 0.62, ["scaling"]
    if out_cells != in_cells and object_count > 3:
        return "counting", 0.58, ["object_counting", "count_by_color"]
    if _bottom_weighted(output_grid) and not _bottom_weighted(input_grid):
        return "gravity_simulation", 0.63, ["gravity_simulation", "downward_motion"]
    if spatial_complexity >= 0.35:
        return "pattern_completion", 0.55, ["pattern_completion", "spatial_reasoning"]
    return "unknown_complex", 0.42, ["unknown_complex"]


def _nested_get(value, *keys):
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _grid(value):
    if not isinstance(value, list):
        return []
    return [list(row) for row in value if isinstance(row, list)]


def _colors(grid):
    return {
        cell
        for row in grid
        for cell in row
        if isinstance(cell, int)
    }


def _nonzero_count(grid):
    return sum(1 for row in grid for cell in row if cell != 0)


def _nonzero_positions(grid):
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, cell in enumerate(row)
        if cell != 0
    }


def _same_shape(left, right):
    return len(left) == len(right) and all(len(a) == len(b) for a, b in zip(left, right))


def _same_multiset_nonzero(left, right):
    left_values = sorted(cell for row in left for cell in row if cell != 0)
    right_values = sorted(cell for row in right for cell in row if cell != 0)
    return left_values == right_values and bool(left_values)


def _shape_scale_changed(left, right):
    return bool(left and right) and (
        len(left) != len(right)
        or max((len(row) for row in left), default=0) != max((len(row) for row in right), default=0)
    )


def _has_symmetry(grid):
    if not grid:
        return False
    horizontal = grid == list(reversed(grid))
    vertical = all(row == list(reversed(row)) for row in grid)
    return horizontal or vertical


def _bottom_weighted(grid):
    if not grid:
        return False
    midpoint = len(grid) // 2
    top = sum(1 for row in grid[:midpoint] for cell in row if cell != 0)
    bottom = sum(1 for row in grid[midpoint:] for cell in row if cell != 0)
    return bottom > top


def _object_count(grid):
    seen = set()
    count = 0
    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell == 0 or (r, c) in seen:
                continue
            count += 1
            stack = [(r, c)]
            seen.add((r, c))
            while stack:
                cr, cc = stack.pop()
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if (
                        0 <= nr < len(grid)
                        and 0 <= nc < len(grid[nr])
                        and (nr, nc) not in seen
                        and grid[nr][nc] == cell
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return count


def _grid_complexity(input_grid, output_grid):
    cells = sum(len(row) for row in input_grid) + sum(len(row) for row in output_grid)
    colors = len(_colors(input_grid) | _colors(output_grid))
    return round(min(1.0, cells / 200.0 + colors / 20.0), 4)


def _spatial_complexity(input_grid, output_grid):
    if not input_grid or not output_grid or not _same_shape(input_grid, output_grid):
        return 0.45
    total = max(1, sum(len(row) for row in input_grid))
    changed = 0
    for r, row in enumerate(input_grid):
        for c, cell in enumerate(row):
            if output_grid[r][c] != cell:
                changed += 1
    return round(changed / total, 4)


def _stable_hash(value):
    try:
        encoded = json.dumps(value, sort_keys=True, default=str)
    except TypeError:
        encoded = str(value)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


__all__ = [
    "RuntimeTaskProfile",
    "TASK_FAMILIES",
    "build_task_profile",
]
