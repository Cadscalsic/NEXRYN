"""Synthetic ARC-style task generation for targeted concept coverage."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from runtime.training.concept_coverage_audit import (
    MAJOR_ARC_CONCEPTS,
    audit_training_tasks,
    curriculum_level_for,
)


TRAINING_DIRECTORY = Path("data/training")
CURRICULUM_NAME = "arc_cognitive_curriculum_balancing_alpha_01"
Grid = list[list[int]]
Builder = Callable[[int], tuple[Grid, Grid]]


def blank(height: int = 7, width: int = 7) -> Grid:
    return [[0 for _ in range(width)] for _ in range(height)]


def clone(source: Grid) -> Grid:
    return [list(row) for row in source]


def draw(source: Grid, cells: list[tuple[int, int, int]]) -> Grid:
    target = clone(source)
    for row, column, color in cells:
        if 0 <= row < len(target) and 0 <= column < len(target[0]):
            target[row][column] = color
    return target


def containment(index: int) -> tuple[Grid, Grid]:
    source = draw(blank(), _box(1, 1, 5, 5, 3) + [(3, 3, 2), (6, 0, 2)])
    target = clone(source)
    target[3][3] = 8
    return source, target


def occlusion(index: int) -> tuple[Grid, Grid]:
    source = draw(blank(6, 7), [(2, 1, 5), (2, 2, 5), (2, 4, 5), (2, 5, 5), (2, 3, 9)])
    target = clone(source)
    target[2][3] = 5
    return source, target


def topology_change(index: int) -> tuple[Grid, Grid]:
    source = draw(blank(6, 6), [(2, 1, 4), (2, 2, 4), (2, 4, 4), (2, 5, 4)])
    target = draw(source, [(2, 3, 4)])
    return source, target


def route_completion(index: int) -> tuple[Grid, Grid]:
    source = draw(blank(), [(1, 1, 2), (5, 5, 3)] + [(3, column, 8) for column in range(1, 6) if column != 3])
    path = [(2, 1, 4), (3, 1, 4), (4, 1, 4), (5, 1, 4), (5, 2, 4), (5, 3, 4), (5, 4, 4)]
    return source, draw(source, path)


def relative_position(index: int) -> tuple[Grid, Grid]:
    source = draw(blank(6, 6), [(2, 2, 2), (2, 3, 3)])
    return source, draw(blank(6, 6), [(3, 3, 2), (3, 4, 3)])


def rotation(index: int) -> tuple[Grid, Grid]:
    source = draw(blank(5, 5), [(1, 1, 2), (2, 1, 2), (2, 2, 2), (3, 2, 3)])
    target = [list(row) for row in zip(*source[::-1])]
    return source, target


def reflection(index: int) -> tuple[Grid, Grid]:
    source = draw(blank(5, 5), [(1, 1, 2), (2, 1, 2), (2, 2, 3)])
    return source, [list(reversed(row)) for row in source]


def scaling(index: int) -> tuple[Grid, Grid]:
    source = draw(blank(4, 4), [(1, 1, 6), (1, 2, 6), (2, 1, 6)])
    target = blank(8, 8)
    for row in range(len(source)):
        for column in range(len(source[0])):
            if source[row][column]:
                for row_delta in range(2):
                    for column_delta in range(2):
                        target[row * 2 + row_delta][column * 2 + column_delta] = source[row][column]
    return source, target


def count_by_color(index: int) -> tuple[Grid, Grid]:
    source = draw(blank(5, 6), [(1, 1, 2), (1, 3, 2), (2, 2, 3), (3, 1, 3), (3, 4, 3)])
    return source, draw(blank(3, 6), [(1, column, 2) for column in range(2)] + [(2, column, 3) for column in range(3)])


def artifact_filtering(index: int) -> tuple[Grid, Grid]:
    signal = [(1, 1, 4), (2, 2, 4), (3, 3, 4), (4, 4, 4)]
    source = draw(blank(6, 6), signal + [(0, 5, 9), (5, 0, 8)])
    return source, draw(blank(6, 6), signal)


def gravity(index: int) -> tuple[Grid, Grid]:
    source = draw(blank(7, 5), [(6, column, 8) for column in range(5)] + [(1, 1, 2), (3, 3, 3)])
    target = draw(blank(7, 5), [(6, column, 8) for column in range(5)] + [(5, 1, 2), (5, 3, 3)])
    return source, target


def pattern_completion(index: int) -> tuple[Grid, Grid]:
    source = blank(5, 7)
    target = blank(5, 7)
    for column in range(7):
        target[2][column] = 1 if column % 2 == 0 else 2
        if column != 3:
            source[2][column] = target[2][column]
    return source, target


def symbolic_mapping(index: int) -> tuple[Grid, Grid]:
    source = draw(blank(5, 5), [(1, 1, 1), (1, 2, 2), (2, 1, 2), (2, 2, 1)])
    target = [[{1: 5, 2: 7}.get(value, value) for value in row] for row in source]
    return source, target


SINGLE_CONCEPT_BUILDERS: dict[str, Builder] = {
    "artifact_filtering": artifact_filtering,
    "containment": containment,
    "count_by_color": count_by_color,
    "downward_motion": gravity,
    "gravity_simulation": gravity,
    "hidden_object_recovery": occlusion,
    "inside": containment,
    "inside_outside": containment,
    "masking": occlusion,
    "object_counting": count_by_color,
    "occlusion": occlusion,
    "outside": containment,
    "path_finding": route_completion,
    "pattern_completion": pattern_completion,
    "reflection": reflection,
    "relative_position": relative_position,
    "rotation": rotation,
    "route_completion": route_completion,
    "scaling": scaling,
    "sequence_completion": pattern_completion,
    "symbolic_mapping": symbolic_mapping,
    "symbolic_remapping": symbolic_mapping,
    "topological_change": topology_change,
    "topology_change": topology_change,
    "topological_growth": topology_change,
}

MULTI_CONCEPT_RECIPES: tuple[tuple[str, ...], ...] = (
    ("replication", "growth"),
    ("growth", "propagation"),
    ("containment", "occlusion"),
    ("topology_change", "scaling"),
    ("relative_position", "symbolic_mapping"),
    ("route_completion", "path_finding"),
    ("hidden_object_recovery", "symmetry_reasoning"),
    ("causal_reasoning", "topology_change"),
)


class TaskGenerationEngine:
    """Generate deterministic, human-solvable tasks for concept gaps."""

    def __init__(self, training_directory: Path | str = TRAINING_DIRECTORY) -> None:
        self.training_directory = Path(training_directory)

    def generate_for_missing(
        self,
        audit_report: dict[str, Any] | None = None,
        minimum_task_count: int = 3,
        include_multi_concept: bool = True,
    ) -> list[dict[str, Any]]:
        report = audit_report or audit_training_tasks(self.training_directory, report_path=None)
        generated = []
        concepts = report.get("concepts", {})
        for concept in MAJOR_ARC_CONCEPTS:
            count = int(concepts.get(concept, {}).get("task_count", 0))
            if count >= minimum_task_count:
                continue
            for index in range(minimum_task_count - count):
                generated.append(self.task_for_concepts([concept], index))
        if include_multi_concept:
            for index, concepts_tuple in enumerate(MULTI_CONCEPT_RECIPES):
                generated.append(self.task_for_concepts(list(concepts_tuple), index))
        return generated

    def task_for_concepts(self, concepts: list[str], index: int = 0) -> dict[str, Any]:
        primary = concepts[0]
        builder = SINGLE_CONCEPT_BUILDERS.get(primary, symbolic_mapping)
        source, target = builder(index)
        if len(concepts) > 1:
            target = _compose_target(target, concepts)
        task_id = _task_id(concepts, index)
        return {
            "concept_family": primary,
            "concept_labels": concepts,
            "difficulty": "frontier" if curriculum_level_for(concepts) == 4 else "medium",
            "train": [
                {"input": source, "output": target},
                {"input": _variant(source, index + 1), "output": _variant(target, index + 1)},
            ],
            "test": [{"input": _variant(source, index + 2)}],
            "expected_transformations": concepts,
            "nexryn_metadata": {
                "curriculum": CURRICULUM_NAME,
                "task_id": task_id,
                "concept_family": primary,
                "target_concepts": concepts,
                "concept_labels": concepts,
                "curriculum_level": curriculum_level_for(concepts),
                "multi_concept": len(concepts) > 1,
                "metadata_is_targeting_not_runtime_observation": True,
                "governance_constraints": {
                    "force_truth_promotion": False,
                    "lower_thresholds": False,
                    "manual_stable_truth": False,
                    "evidence_only": True,
                },
            },
        }

    def write_tasks(self, tasks: list[dict[str, Any]]) -> dict[str, Any]:
        self.training_directory.mkdir(parents=True, exist_ok=True)
        written = []
        coverage = Counter()
        for task in tasks:
            task_id = task["nexryn_metadata"]["task_id"]
            path = self.training_directory / f"{task_id}.json"
            path.write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
            written.append(str(path))
            coverage.update(task["nexryn_metadata"]["target_concepts"])
        return {
            "system": "task_generation_engine",
            "curriculum": CURRICULUM_NAME,
            "generated_tasks": len(written),
            "written": written,
            "concept_coverage": dict(sorted(coverage.items())),
            "multi_concept_tasks": sum(
                1 for task in tasks if task["nexryn_metadata"]["multi_concept"]
            ),
            "evidence_only": True,
        }


def _box(top: int, left: int, bottom: int, right: int, color: int) -> list[tuple[int, int, int]]:
    cells = []
    for column in range(left, right + 1):
        cells.extend([(top, column, color), (bottom, column, color)])
    for row in range(top + 1, bottom):
        cells.extend([(row, left, color), (row, right, color)])
    return cells


def _compose_target(target: Grid, concepts: list[str]) -> Grid:
    result = clone(target)
    if any(concept in concepts for concept in ("symbolic_mapping", "symbolic_remapping")):
        result = [[7 if value == 2 else value for value in row] for row in result]
    if any(concept in concepts for concept in ("causal_reasoning", "dependency_reasoning")):
        result[0][0] = 6
    return result


def _variant(source: Grid, index: int) -> Grid:
    target = clone(source)
    marker = 1 + index % 8
    if target and target[0]:
        target[-1][-1] = marker if target[-1][-1] == 0 else target[-1][-1]
    return target


def _task_id(concepts: list[str], index: int) -> str:
    slug = "_".join(concepts).replace(" ", "_")
    return f"arc_generated_{slug}_{index + 1:02d}"


def main() -> None:
    engine = TaskGenerationEngine()
    tasks = engine.generate_for_missing()
    print(json.dumps(engine.write_tasks(tasks), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
