"""Elite cognitive curriculum for capability-driven operational training.

These tasks are evidence probes, not truth promotions.  They intentionally
combine several domains so failures can expose missing execution packages,
validation paths, and cross-domain collaborations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable


TRAINING_DIRECTORY = Path("data/training")
CURRICULUM_NAME = "nexryn_elite_cognitive_training_phase_01"
TASK_PREFIX = "elite_cognitive_task"

Grid = list[list[int]]
Transform = Callable[[Grid, int], Grid]


def blank(height: int = 12, width: int = 12) -> Grid:
    return [[0 for _ in range(width)] for _ in range(height)]


def clone(source: Grid) -> Grid:
    return [list(row) for row in source]


def draw(source: Grid, cells: list[tuple[int, int, int]]) -> Grid:
    target = clone(source)
    height = len(target)
    width = len(target[0])
    for row, column, value in cells:
        if 0 <= row < height and 0 <= column < width:
            target[row][column] = value
    return target


def points(source: Grid, colors: set[int] | None = None) -> list[tuple[int, int, int]]:
    found = []
    for row_index, row in enumerate(source):
        for column_index, value in enumerate(row):
            if value and (colors is None or value in colors):
                found.append((row_index, column_index, value))
    return found


def translate(source: Grid, row_delta: int, column_delta: int) -> Grid:
    return draw(blank(len(source), len(source[0])), [
        (row + row_delta, column + column_delta, value)
        for row, column, value in points(source)
    ])


def mirror_horizontal(source: Grid) -> Grid:
    width = len(source[0])
    return draw(blank(len(source), width), [
        (row, width - column - 1, value)
        for row, column, value in points(source)
    ])


def halo_growth(source: Grid, index: int) -> Grid:
    target = clone(source)
    growth_color = 4 + index % 4
    for row, column, value in points(source, {1, 2, 3}):
        for row_delta, column_delta in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            target = draw(target, [(row + row_delta, column + column_delta, growth_color)])
        target[row][column] = value
    return target


def preserve_tunnels(source: Grid, index: int) -> Grid:
    target = clone(source)
    for row in range(2, len(source) - 2):
        target[row][5] = 6
    for row, column, value in points(source, {2, 3}):
        target[row][column] = value
    target[2 + index % 3][5] = 0
    return target


def dependency_bridge(source: Grid, index: int) -> Grid:
    target = clone(source)
    anchors = points(source, {2, 3, 4})
    rows = [row for row, _, _ in anchors]
    columns = [column for _, column, _ in anchors]
    if rows and columns:
        mid_row = sorted(rows)[len(rows) // 2]
        for column in range(min(columns), max(columns) + 1):
            if target[mid_row][column] == 0:
                target[mid_row][column] = 7
    return target


def relation_markers(source: Grid, index: int) -> Grid:
    target = clone(source)
    colored = points(source, {1, 2, 3, 4, 5})
    for row, column, value in colored:
        marker = 8 if (row + column + index) % 2 == 0 else 9
        target = draw(target, [(row + 1, column, marker)])
        target[row][column] = value
    return target


def reflected_growth_translation(source: Grid, index: int) -> Grid:
    grown = halo_growth(source, index)
    reflected = mirror_horizontal(grown)
    return translate(reflected, 1 if index % 2 == 0 else -1, 0)


def multi_stage_program(source: Grid, index: int) -> Grid:
    return dependency_bridge(reflected_growth_translation(source, index), index)


def unknown_weave(source: Grid, index: int) -> Grid:
    target = clone(source)
    for row, column, value in points(source):
        target[row][column] = ((value + row + column + index) % 9) + 1
        if (row + column) % 3 == 0:
            target = draw(target, [(column % len(source), row % len(source[0]), value)])
    return target


def temporal_evolution(source: Grid, index: int) -> Grid:
    target = clone(source)
    for row, column, value in points(source, {1, 2, 3, 4}):
        target = draw(target, [(row + value % 3, column + index % 2, value)])
    return halo_growth(target, index)


def counterfactual_trace(source: Grid, index: int) -> Grid:
    target = dependency_bridge(source, index)
    for row, column, value in points(source, {8}):
        target[row][column] = 0
        target = draw(target, [(row, column + 1, 5), (row + 1, column, 5)])
    return target


def causal_cascade(source: Grid, index: int) -> Grid:
    target = clone(source)
    for row, column, value in points(source, {2, 4, 6}):
        for step in range(1, 4):
            target = draw(target, [(row + step, column + step, value + 1)])
    return target


def dynamic_world(source: Grid, index: int) -> Grid:
    return causal_cascade(counterfactual_trace(source, index), index)


def conflict_resolution(source: Grid, index: int) -> Grid:
    target = multi_stage_program(source, index)
    for row, column, value in points(target):
        if value in {4, 7} and row % 2 == column % 2:
            target[row][column] = 5
    return target


def grand_boss(source: Grid, index: int) -> Grid:
    target = dynamic_world(multi_stage_program(source, index), index)
    for row in range(1, len(target) - 1):
        if target[row][1] == 0:
            target[row][1] = 6
        if target[row][-2] == 0:
            target[row][-2] = 7
    for column in range(2, len(target[0]) - 2):
        if column % 2 == index % 2:
            target[1][column] = 8
            target[-2][column] = 9
    return target


TRANSFORMS: dict[str, Transform] = {
    "halo_growth": halo_growth,
    "preserve_tunnels": preserve_tunnels,
    "dependency_bridge": dependency_bridge,
    "relation_markers": relation_markers,
    "reflected_growth_translation": reflected_growth_translation,
    "multi_stage_program": multi_stage_program,
    "unknown_weave": unknown_weave,
    "temporal_evolution": temporal_evolution,
    "counterfactual_trace": counterfactual_trace,
    "causal_cascade": causal_cascade,
    "dynamic_world": dynamic_world,
    "conflict_resolution": conflict_resolution,
    "grand_boss": grand_boss,
}


TASK_SPECS = [
    ("Spatial + Growth + Color Reasoning", "cross_domain_reasoning", "halo_growth", ["spatial_reasoning", "growth", "color_transformation"]),
    ("Topology + Identity Preservation Reasoning", "cross_domain_reasoning", "preserve_tunnels", ["topological_reasoning", "identity_preservation", "containment"]),
    ("Multi Object Dependency Reasoning", "cross_domain_reasoning", "dependency_bridge", ["multi_object_dependency", "causal_dependency", "spatial_reasoning"]),
    ("Object Relationship Discovery Task", "cross_domain_reasoning", "relation_markers", ["object_relationship_discovery", "relative_position", "identity_preservation"]),
    ("Bridge Creation Capability Composition", "capability_composition", "dependency_bridge", ["bridge_creation", "path_finding", "topological_growth"]),
    ("Growth + Reflection + Translation Composition", "capability_composition", "reflected_growth_translation", ["growth", "reflection", "translation", "composition"]),
    ("Multi Stage Program Composition", "capability_composition", "multi_stage_program", ["program_composition", "compiler_runtime_activation", "validation_pipeline"]),
    ("Operational Capability Composition Challenge", "capability_composition", "conflict_resolution", ["capability_composition", "candidate_arena", "cross_domain_collaboration"]),
    ("Unknown Transformation Discovery", "novel_capability_discovery", "unknown_weave", ["unknown_transformation", "novel_capability_discovery", "exploration"]),
    ("Unknown Execution Package Discovery", "novel_capability_discovery", "multi_stage_program", ["unknown_execution_package", "compiler_runtime_activation", "program_generation"]),
    ("Novel Pattern Completion", "novel_capability_discovery", "unknown_weave", ["novel_pattern_completion", "symbolic_remapping", "operationalization"]),
    ("Emergent Behavior Discovery", "novel_capability_discovery", "causal_cascade", ["emergent_behavior", "causal_reasoning", "world_modeling"]),
    ("Temporal Object Evolution", "world_modeling", "temporal_evolution", ["temporal_dependency", "object_evolution", "world_model"]),
    ("Counterfactual Reasoning", "world_modeling", "counterfactual_trace", ["counterfactual_reasoning", "causal_reasoning", "validation_gap"]),
    ("Cause Effect Discovery", "world_modeling", "causal_cascade", ["cause_effect_discovery", "causal_chain", "dependency_reasoning"]),
    ("Dynamic World State Simulation", "world_modeling", "dynamic_world", ["dynamic_world_state", "simulation", "resource_allocation"]),
    ("Multi Domain Collaborative Reasoning", "collaborative_intelligence", "multi_stage_program", ["multi_domain_collaboration", "growth", "topology", "identity"]),
    ("Cognitive Conflict Resolution", "collaborative_intelligence", "conflict_resolution", ["cognitive_conflict_resolution", "validation_efficiency", "candidate_arena"]),
    ("Multiple Valid Solution Strategies", "collaborative_intelligence", "dynamic_world", ["multiple_solution_strategies", "execution_path_diversity", "knowledge_investment"]),
    ("THE GRAND COGNITIVE BOSS TASK", "grand_boss", "grand_boss", ["growth", "spatial_reasoning", "topological_reasoning", "identity_preservation", "transformation", "world_model", "capability_composition", "knowledge_investment", "operational_capability_discovery", "candidate_arena", "compiler_runtime_activation", "validation_pipeline"]),
]


def base_scene(index: int, size: int = 12) -> Grid:
    source = blank(size, size)
    cells = [
        (1 + index % 3, 1, 1),
        (2, 2 + index % 4, 2),
        (3, 7, 3),
        (5, 3, 4),
        (6, 8, 5),
        (8, 2 + index % 2, 6),
        (8, 8, 7),
        (4 + index % 3, 5, 8),
    ]
    if index >= 19:
        cells.extend([
            (1, 9, 2), (2, 5, 3), (3, 3, 4), (4, 9, 5),
            (5, 1, 6), (6, 6, 7), (7, 10, 8), (9, 4, 9),
        ])
    return draw(source, cells)


def task_for(sequence: int, spec: tuple[str, str, str, list[str]]) -> dict:
    title, category, transform_name, concepts = spec
    transform = TRANSFORMS[transform_name]
    first_input = base_scene(sequence)
    second_input = base_scene(sequence + 4)
    test_input = base_scene(sequence + 8)
    task_id = f"{TASK_PREFIX}_{sequence:02d}"
    return {
        "train": [
            {"input": first_input, "output": transform(first_input, sequence)},
            {"input": second_input, "output": transform(second_input, sequence + 4)},
        ],
        "test": [{"input": test_input}],
        "expected_transformations": [
            "compose_capabilities",
            "infer_operational_path",
            transform_name,
        ],
        "negative_controls": [
            {
                "input": first_input,
                "output": translate(first_input, 0, 1),
                "reason": "simple_translation_is_insufficient",
            }
        ],
        "nexryn_metadata": {
            "curriculum": CURRICULUM_NAME,
            "task_id": task_id,
            "task_title": title,
            "elite_cognitive_task": True,
            "elite_category": category,
            "target_concepts": concepts,
            "target_domains": sorted(set(concept.split("_")[0] for concept in concepts)),
            "deficiency_targets": [
                "operational_knowledge_waste",
                "low_operational_yield",
                "capability_population_evolution_lag",
                "validation_gaps",
                "domain_operationalization_gaps",
                "slow_capability_acquisition",
                "historical_exploitation_bias",
            ],
            "required_operational_capabilities": [
                "candidate_generation",
                "program_generation",
                "capability_composition",
                "compiler_runtime_activation",
                "world_model_validation",
                "cross_domain_collaboration",
            ],
            "multiple_valid_solution_strategies": True,
            "failure_is_training_signal": True,
            "success_policy": "capability_acquisition_over_exact_accuracy",
            "forbidden_simple_solution_classes": [
                "replace_color",
                "duplicate_object",
                "single_basic_transformation",
            ],
            "governance_constraints": {
                "force_truth_promotion": False,
                "lower_thresholds": False,
                "manual_stable_truth": False,
                "evidence_only": True,
            },
        },
    }


def build_curriculum() -> list[dict]:
    return [
        task_for(sequence, spec)
        for sequence, spec in enumerate(TASK_SPECS, start=1)
    ]


def write_curriculum(training_directory: Path = TRAINING_DIRECTORY) -> dict:
    training_directory.mkdir(parents=True, exist_ok=True)
    written = []
    for task in build_curriculum():
        task_id = task["nexryn_metadata"]["task_id"]
        path = training_directory / f"{task_id}.json"
        path.write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
        written.append(str(path))
    return {
        "system": "elite_cognitive_curriculum_generator",
        "curriculum": CURRICULUM_NAME,
        "task_count": len(written),
        "training_directory": str(training_directory),
        "written": written,
        "evidence_only": True,
    }


def main() -> None:
    print(json.dumps(write_curriculum(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
