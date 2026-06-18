"""Targeted ARC-style micro-curriculum for underrepresented concepts.

The generator only creates evidence tasks. It does not alter lifecycle state,
truth thresholds, registry entries, or governance outcomes.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Callable


TRAINING_DIRECTORY = Path("data/training")
CURRICULUM_NAME = "arc_concept_coverage_expansion_alpha_01"
TASK_PREFIX = "arc_concept"
TASKS_PER_FAMILY = 15


CONCEPT_FAMILIES = {
    "object_counting": ["object_counting", "object_count_increase", "count_by_color"],
    "spatial_reasoning": ["spatial_reasoning", "relative_position", "position_change"],
    "color_mapping": ["color_mapping", "color_transformation"],
    "rotation_reflection": ["rotation", "reflection", "rotation_reflection"],
    "pattern_completion": ["pattern_completion", "sequence_completion"],
    "inside_outside": ["inside_outside", "containment"],
    "noise_removal": ["noise_removal", "artifact_filtering"],
    "occlusion_masking": ["occlusion", "masking", "hidden_object_recovery"],
    "scaling": ["scaling", "size_transformation"],
    "path_finding": ["path_finding", "route_completion"],
    "gravity_simulation": ["gravity_simulation", "downward_motion"],
}


EXPECTED_TRANSFORMATIONS = {
    "object_counting": ["count_objects", "encode_count"],
    "spatial_reasoning": ["translate_object", "preserve_relative_position"],
    "color_mapping": ["map_colors", "preserve_structure"],
    "rotation_reflection": ["rotate_or_reflect", "preserve_shape_identity"],
    "pattern_completion": ["complete_repeating_pattern"],
    "inside_outside": ["classify_containment", "recolor_inner_region"],
    "noise_removal": ["remove_noise", "preserve_signal"],
    "occlusion_masking": ["recover_masked_shape", "ignore_occluder"],
    "scaling": ["scale_shape", "preserve_topology"],
    "path_finding": ["connect_start_to_goal", "avoid_obstacles"],
    "gravity_simulation": ["drop_objects_downward", "respect_barriers"],
}


Grid = list[list[int]]
InputBuilder = Callable[[int], Grid]
OutputBuilder = Callable[[Grid, int], Grid]


def grid(*rows: tuple[int, ...]) -> Grid:
    return [list(row) for row in rows]


def blank(height: int = 7, width: int = 7) -> Grid:
    return [[0 for _ in range(width)] for _ in range(height)]


def clone(source: Grid) -> Grid:
    return [list(row) for row in source]


def points(source: Grid, colors: set[int] | None = None) -> list[tuple[int, int, int]]:
    found = []
    for row_index, row in enumerate(source):
        for column_index, value in enumerate(row):
            if value and (colors is None or value in colors):
                found.append((row_index, column_index, value))
    return found


def draw(source: Grid, cells: list[tuple[int, int, int]]) -> Grid:
    target = clone(source)
    height = len(target)
    width = len(target[0])
    for row, column, value in cells:
        if 0 <= row < height and 0 <= column < width:
            target[row][column] = value
    return target


def recolor(source: Grid, mapping: dict[int, int]) -> Grid:
    return [[mapping.get(value, value) for value in row] for row in source]


def shift(source: Grid, row_delta: int, column_delta: int) -> Grid:
    target = blank(len(source), len(source[0]))
    for row, column, value in points(source):
        draw(target, [(row + row_delta, column + column_delta, value)])
    return target


def rotate_clockwise(source: Grid) -> Grid:
    return [list(row) for row in zip(*source[::-1])]


def rotate_180(source: Grid) -> Grid:
    return rotate_clockwise(rotate_clockwise(source))


def reflect_horizontal(source: Grid) -> Grid:
    return [list(reversed(row)) for row in source]


def reflect_vertical(source: Grid) -> Grid:
    return list(reversed(clone(source)))


def object_counting_input(index: int) -> Grid:
    source = blank(5, 5)
    count = index % 4 + 1
    cells = [(1, column + 1, 2) for column in range(count)]
    if index % 3 == 0:
        cells.append((3, 3, 3))
    return draw(source, cells)


def object_counting_output(source: Grid, index: int) -> Grid:
    count = len(points(source, {2}))
    return draw(blank(5, 5), [(2, column, 4) for column in range(count)])


def spatial_input(index: int) -> Grid:
    row = 1 + index % 3
    column = 1 + (index // 3) % 3
    return draw(blank(6, 6), [(row, column, 2), (row, column + 1, 3)])


def spatial_output(source: Grid, index: int) -> Grid:
    return shift(source, 1 if index % 2 == 0 else -1, 1)


def color_input(index: int) -> Grid:
    return draw(
        blank(5, 5),
        [(1, 1, 1), (1, 2, 2), (2, 1, 2), (2, 2, 1), (3, 3, 3 + index % 2)],
    )


def color_output(source: Grid, index: int) -> Grid:
    return recolor(source, {1: 4 + index % 3, 2: 7, 3: 8, 4: 9})


def rotation_input(index: int) -> Grid:
    return draw(blank(5, 5), [(1, 1, 2), (2, 1, 2), (2, 2, 2), (3, 2, 3)])


def rotation_output(source: Grid, index: int) -> Grid:
    operations = [rotate_clockwise, reflect_horizontal, reflect_vertical, rotate_180]
    return operations[index % len(operations)](source)


def pattern_input(index: int) -> Grid:
    source = blank(5, 7)
    for column in range(6):
        if column == 3 + index % 2:
            continue
        source[2][column] = 1 if column % 2 == 0 else 2
    return source


def pattern_output(source: Grid, index: int) -> Grid:
    target = clone(source)
    for column in range(len(target[0])):
        target[2][column] = 1 if column % 2 == 0 else 2
    return target


def inside_outside_input(index: int) -> Grid:
    source = blank(7, 7)
    border = []
    for column in range(1, 6):
        border.extend([(1, column, 3), (5, column, 3)])
    for row in range(2, 5):
        border.extend([(row, 1, 3), (row, 5, 3)])
    inside = (3, 3, 2)
    outside = (0 if index % 2 else 6, 6 if index % 2 else 0, 2)
    return draw(source, border + [inside, outside])


def inside_outside_output(source: Grid, index: int) -> Grid:
    target = clone(source)
    target[3][3] = 8
    return target


def noise_input(index: int) -> Grid:
    signal = [(1, 1, 4), (2, 2, 4), (3, 3, 4), (4, 4, 4)]
    noise = [(0, index % 5, 9), (5, (index + 2) % 5, 8)]
    return draw(blank(6, 6), signal + noise)


def noise_output(source: Grid, index: int) -> Grid:
    return [[value if value == 4 else 0 for value in row] for row in source]


def occlusion_input(index: int) -> Grid:
    source = draw(blank(6, 6), [(2, 1, 5), (2, 2, 5), (2, 4, 5), (2, 5, 5)])
    source[2][3] = 9
    if index % 2:
        source[3][3] = 9
    return source


def occlusion_output(source: Grid, index: int) -> Grid:
    target = clone(source)
    target[2][3] = 5
    if index % 2:
        target[3][3] = 0
    return target


def scaling_input(index: int) -> Grid:
    return draw(blank(6, 6), [(1, 1, 6), (1, 2, 6), (2, 1, 6), (2, 2, 6)])


def scaling_output(source: Grid, index: int) -> Grid:
    target = blank(6, 6)
    scale = 2 if index % 3 else 1
    for row, column, value in points(source):
        for row_delta in range(scale):
            for column_delta in range(scale):
                target_row = row * scale - 1 + row_delta
                target_column = column * scale - 1 + column_delta
                if 0 <= target_row < len(target) and 0 <= target_column < len(target[0]):
                    target[target_row][target_column] = value
    return target


def path_input(index: int) -> Grid:
    source = blank(7, 7)
    obstacles = [(3, column, 8) for column in range(1, 6) if column != 3]
    return draw(source, [(1, 1, 2), (5, 5, 3)] + obstacles)


def path_output(source: Grid, index: int) -> Grid:
    path = [(1, 1, 2), (2, 1, 4), (3, 1, 4), (4, 1, 4), (5, 1, 4),
            (5, 2, 4), (5, 3, 4), (5, 4, 4), (5, 5, 3)]
    return draw(source, path)


def gravity_input(index: int) -> Grid:
    source = blank(7, 5)
    floor = [(6, column, 8) for column in range(5)]
    block_row = 1 + index % 3
    return draw(source, floor + [(block_row, 1, 2), (block_row + 1, 3, 3)])


def gravity_output(source: Grid, index: int) -> Grid:
    target = blank(7, 5)
    for column in range(5):
        target[6][column] = 8
    column_values: dict[int, list[int]] = {}
    for _, column, value in points(source, {2, 3, 4, 5, 6, 7}):
        column_values.setdefault(column, []).append(value)
    for column, values in column_values.items():
        row = 5
        for value in values:
            target[row][column] = value
            row -= 1
    return target


BUILDERS: dict[str, tuple[InputBuilder, OutputBuilder]] = {
    "object_counting": (object_counting_input, object_counting_output),
    "spatial_reasoning": (spatial_input, spatial_output),
    "color_mapping": (color_input, color_output),
    "rotation_reflection": (rotation_input, rotation_output),
    "pattern_completion": (pattern_input, pattern_output),
    "inside_outside": (inside_outside_input, inside_outside_output),
    "noise_removal": (noise_input, noise_output),
    "occlusion_masking": (occlusion_input, occlusion_output),
    "scaling": (scaling_input, scaling_output),
    "path_finding": (path_input, path_output),
    "gravity_simulation": (gravity_input, gravity_output),
}


def negative_control(source: Grid, family: str, index: int) -> dict:
    wrong_output = recolor(source, {1: 9, 2: 9, 3: 9})
    if family in {"rotation_reflection", "spatial_reasoning"}:
        wrong_output = source
    if family in {"noise_removal", "occlusion_masking"}:
        wrong_output = shift(source, 0, 1)
    return {
        "input": source,
        "output": wrong_output,
        "reason": f"counterexample_for_{family}",
    }


def task_for(family: str, index: int) -> dict:
    input_builder, output_builder = BUILDERS[family]
    first_input = input_builder(index)
    second_input = input_builder(index + 5)
    test_input = input_builder(index + 10)
    labels = CONCEPT_FAMILIES[family]
    difficulty = "easy" if index < 5 else "medium" if index < 10 else "mixed"
    task_id = f"{TASK_PREFIX}_{family}_{index + 1:02d}"
    return {
        "concept_family": family,
        "concept_labels": labels,
        "difficulty": difficulty,
        "train": [
            {"input": first_input, "output": output_builder(first_input, index)},
            {"input": second_input, "output": output_builder(second_input, index + 5)},
        ],
        "test": [{"input": test_input}],
        "expected_transformations": EXPECTED_TRANSFORMATIONS[family],
        "negative_controls": [negative_control(first_input, family, index)],
        "nexryn_metadata": {
            "curriculum": CURRICULUM_NAME,
            "task_id": task_id,
            "concept_family": family,
            "target_concepts": labels,
            "concept_labels": labels,
            "difficulty": difficulty,
            "expected_transformations": EXPECTED_TRANSFORMATIONS[family],
            "positive_examples": 2,
            "counterexample_examples": 1,
            "metadata_is_targeting_not_runtime_observation": True,
            "governance_constraints": {
                "force_truth_promotion": False,
                "lower_thresholds": False,
                "manual_stable_truth": False,
                "evidence_only": True,
            },
        },
    }


def build_curriculum(tasks_per_family: int = TASKS_PER_FAMILY) -> list[dict]:
    tasks = []
    for family in CONCEPT_FAMILIES:
        for index in range(tasks_per_family):
            tasks.append(task_for(family, index))
    return tasks


def write_curriculum(
    training_directory: Path = TRAINING_DIRECTORY,
    tasks_per_family: int = TASKS_PER_FAMILY,
) -> dict:
    training_directory.mkdir(parents=True, exist_ok=True)
    tasks = build_curriculum(tasks_per_family=tasks_per_family)
    written = []
    coverage = Counter()
    for task in tasks:
        task_id = task["nexryn_metadata"]["task_id"]
        path = training_directory / f"{task_id}.json"
        path.write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
        written.append(str(path))
        coverage.update(task["concept_labels"])
    return {
        "system": "arc_concept_curriculum_generator",
        "curriculum": CURRICULUM_NAME,
        "task_count": len(written),
        "tasks_per_family": tasks_per_family,
        "concept_families": sorted(CONCEPT_FAMILIES),
        "concept_coverage": dict(sorted(coverage.items())),
        "training_directory": str(training_directory),
        "written": written,
        "evidence_only": True,
        "truth_promotion_forced": False,
        "thresholds_lowered": False,
        "stable_truths_marked": False,
    }


def main() -> None:
    print(json.dumps(write_curriculum(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
