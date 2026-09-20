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
CURRICULUM_NAME = "nexryn_elite_training_curriculum_v1"
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
    {
        "title": "Identity Bridge Operationalization",
        "tier": "Tier 1",
        "category": "operationalization",
        "transform": "dependency_bridge",
        "domains": ["Identity", "Topology", "Spatial"],
        "concepts": ["identity_preservation", "bridge_creation", "spatial_reasoning", "topological_reasoning"],
        "composite": ["Object Identity Preservation", "Bridge Creation", "Spatial Reasoning"],
        "graduation": ["preserve_grid", "preserve_topology"],
        "expansion": ["Identity", "Topology"],
    },
    {
        "title": "Color Topology Stabilization",
        "tier": "Tier 1",
        "category": "operationalization",
        "transform": "preserve_tunnels",
        "domains": ["Color", "Topology", "Identity"],
        "concepts": ["preserve_colors", "preserve_topology", "containment", "identity_preservation"],
        "composite": ["Topology Preservation", "Color Preservation", "Identity Preservation"],
        "graduation": ["preserve_colors", "preserve_topology"],
        "expansion": ["Topology", "Identity"],
    },
    {
        "title": "Transformation Package Probe",
        "tier": "Tier 1",
        "category": "operationalization",
        "transform": "unknown_weave",
        "domains": ["Transformation", "Color", "Geometry"],
        "concepts": ["symbolic_remapping", "color_transformation", "geometric_reasoning", "transformation_sequence"],
        "composite": ["Color Transformation", "Geometry Tracking", "Transformation Sequence"],
        "graduation": ["replace_color"],
        "expansion": ["Transformation", "Geometry"],
    },
    {
        "title": "Growth Density Operational Probe",
        "tier": "Tier 1",
        "category": "operationalization",
        "transform": "halo_growth",
        "domains": ["Growth", "Spatial", "Color"],
        "concepts": ["growth", "density_modulation", "spatial_reasoning", "color_transformation"],
        "composite": ["Growth Detection", "Density Modulation", "Color Transformation"],
        "graduation": ["duplicate_object", "preserve_colors"],
        "expansion": ["Growth"],
    },
    {
        "title": "Spatial Geometry Candidate Entry",
        "tier": "Tier 1",
        "category": "operationalization",
        "transform": "relation_markers",
        "domains": ["Spatial", "Geometry", "Identity"],
        "concepts": ["relative_position", "geometric_reasoning", "object_relationship_discovery", "identity_preservation"],
        "composite": ["Spatial Relation", "Geometry Recognition", "Object Identity Tracking"],
        "graduation": ["preserve_shape", "preserve_grid"],
        "expansion": ["Geometry", "Identity"],
    },
    {
        "title": "Translate Governed Validation",
        "tier": "Tier 2",
        "category": "capability_graduation",
        "transform": "reflected_growth_translation",
        "domains": ["Spatial", "Transformation", "Identity", "Color"],
        "concepts": ["translation", "directional_translation", "exact_or_governed_validation_success", "identity_preservation"],
        "composite": ["Translation", "Identity Preservation", "Color Preservation"],
        "graduation": ["translate"],
        "expansion": ["Spatial", "Identity"],
    },
    {
        "title": "Preserve Topology Cross Domain Validation",
        "tier": "Tier 2",
        "category": "capability_graduation",
        "transform": "preserve_tunnels",
        "domains": ["Topology", "Spatial", "Identity", "Growth"],
        "concepts": ["topological_reasoning", "preserve_topology", "stability_recovery_probe", "cross_domain_validation"],
        "composite": ["Topology Preservation", "Spatial Alignment", "Growth Filtering"],
        "graduation": ["preserve_topology"],
        "expansion": ["Topology"],
    },
    {
        "title": "Duplicate Object Population Diversification",
        "tier": "Tier 2",
        "category": "capability_graduation",
        "transform": "halo_growth",
        "domains": ["Growth", "Spatial", "Color", "Transformation"],
        "concepts": ["duplicate_object", "growth", "population_diversification", "independent_task_validation"],
        "composite": ["Duplicate Object", "Growth Detection", "Spatial Placement"],
        "graduation": ["duplicate_object"],
        "expansion": ["Growth", "Transformation"],
    },
    {
        "title": "Preserve Grid Identity Graduation",
        "tier": "Tier 2",
        "category": "capability_graduation",
        "transform": "relation_markers",
        "domains": ["Identity", "Spatial", "Geometry"],
        "concepts": ["preserve_grid", "identity_preservation", "object_relationship_discovery", "exact_validation"],
        "composite": ["Preserve Grid", "Object Identity Tracking", "Spatial Relation"],
        "graduation": ["preserve_grid"],
        "expansion": ["Identity", "Geometry"],
    },
    {
        "title": "Preserve Colors Transformation Graduation",
        "tier": "Tier 2",
        "category": "capability_graduation",
        "transform": "conflict_resolution",
        "domains": ["Color", "Transformation", "Topology"],
        "concepts": ["preserve_colors", "color_transformation", "validation_pipeline", "cross_domain_validation"],
        "composite": ["Color Preservation", "Conflict Resolution", "Topology Preservation"],
        "graduation": ["preserve_colors", "replace_color"],
        "expansion": ["Transformation"],
    },
    {
        "title": "Pattern Completion Translation Topology",
        "tier": "Tier 3",
        "category": "composite_capability",
        "transform": "multi_stage_program",
        "domains": ["Transformation", "Spatial", "Topology", "Color"],
        "concepts": ["pattern_completion", "translation", "preserve_topology", "color_transformation"],
        "composite": ["Pattern Completion", "Translation", "Topology Preservation", "Color Transformation"],
        "graduation": ["translate", "preserve_topology"],
        "expansion": ["Transformation", "Topology"],
    },
    {
        "title": "Bridge Growth Identity Composition",
        "tier": "Tier 3",
        "category": "composite_capability",
        "transform": "dependency_bridge",
        "domains": ["Topology", "Spatial", "Identity", "Growth"],
        "concepts": ["bridge_creation", "growth", "identity_preservation", "spatial_reasoning"],
        "composite": ["Bridge Creation", "Growth Detection", "Object Identity Preservation"],
        "graduation": ["duplicate_object", "preserve_grid"],
        "expansion": ["Identity", "Topology"],
    },
    {
        "title": "Rotation Reflection Density Composite",
        "tier": "Tier 3",
        "category": "composite_capability",
        "transform": "unknown_weave",
        "domains": ["Geometry", "Transformation", "Growth", "Spatial"],
        "concepts": ["rotation", "reflection", "density_modulation", "pattern_completion"],
        "composite": ["Rotation", "Reflection", "Pattern Completion", "Density Modulation"],
        "graduation": ["preserve_shape"],
        "expansion": ["Geometry", "Transformation"],
    },
    {
        "title": "Adaptive Reuse Program Transfer",
        "tier": "Tier 3",
        "category": "composite_capability",
        "transform": "dynamic_world",
        "domains": ["Transformation", "Color", "Spatial", "Identity"],
        "concepts": ["historical_pattern_reuse", "program_reuse", "capability_transfer", "identity_preservation"],
        "composite": ["Program Reuse", "Capability Transfer", "Object Identity Tracking"],
        "graduation": ["translate", "replace_color"],
        "expansion": ["Identity", "Transformation"],
    },
    {
        "title": "Topology Color Pattern Completion",
        "tier": "Tier 3",
        "category": "composite_capability",
        "transform": "conflict_resolution",
        "domains": ["Topology", "Color", "Transformation", "Spatial"],
        "concepts": ["pattern_completion", "preserve_topology", "symbolic_remapping", "spatial_reasoning"],
        "composite": ["Pattern Completion", "Topology Preservation", "Symbolic Remapping"],
        "graduation": ["preserve_topology", "replace_color"],
        "expansion": ["Topology", "Transformation"],
    },
    {
        "title": "World Model Reuse Gauntlet",
        "tier": "Tier 4",
        "category": "elite_multi_domain",
        "transform": "dynamic_world",
        "domains": ["Growth", "Topology", "Spatial", "Transformation", "Identity"],
        "concepts": ["world_model", "adaptive_reuse", "causal_reasoning", "capability_collaboration"],
        "composite": ["Object Falling Simulation", "Bridge Creation", "Object Identity Tracking"],
        "graduation": ["translate", "duplicate_object", "preserve_grid"],
        "expansion": ["Identity", "Topology", "Transformation"],
    },
    {
        "title": "Composite Domain Civilization Probe",
        "tier": "Tier 4",
        "category": "elite_multi_domain",
        "transform": "grand_boss",
        "domains": ["Color", "Transformation", "Topology", "Spatial", "Identity", "Growth"],
        "concepts": ["multi_domain_collaboration", "capability_composition", "operational_population", "domain_expansion"],
        "composite": ["Color Transformation", "Bridge Creation", "Growth Detection", "Identity Preservation"],
        "graduation": ["translate", "preserve_topology", "preserve_colors"],
        "expansion": ["Identity", "Topology", "Transformation"],
    },
    {
        "title": "Geometry Transformation Boss",
        "tier": "Tier 4",
        "category": "elite_multi_domain",
        "transform": "unknown_weave",
        "domains": ["Geometry", "Transformation", "Spatial", "Color", "Topology"],
        "concepts": ["geometric_reasoning", "unknown_transformation", "pattern_completion", "topological_reasoning"],
        "composite": ["Geometry Tracking", "Unknown Transformation", "Pattern Completion"],
        "graduation": ["preserve_shape", "replace_color"],
        "expansion": ["Geometry", "Transformation", "Topology"],
    },
    {
        "title": "Operational Population Diversification Boss",
        "tier": "Tier 4",
        "category": "elite_multi_domain",
        "transform": "conflict_resolution",
        "domains": ["Identity", "Growth", "Topology", "Spatial", "Transformation"],
        "concepts": ["population_diversification", "capability_graduation", "adaptive_reuse", "cross_domain_validation"],
        "composite": ["Capability Graduation", "Adaptive Reuse", "Domain Collaboration"],
        "graduation": ["translate", "duplicate_object", "preserve_grid", "preserve_topology"],
        "expansion": ["Identity", "Topology", "Growth"],
    },
    {
        "title": "THE ELITE MULTI DOMAIN BOSS TASK",
        "tier": "Tier 4",
        "category": "elite_multi_domain",
        "transform": "grand_boss",
        "domains": ["Color", "Transformation", "Topology", "Spatial", "Identity", "Growth"],
        "concepts": ["growth", "spatial_reasoning", "topological_reasoning", "identity_preservation", "transformation", "world_model", "capability_composition", "knowledge_investment", "operational_capability_discovery", "candidate_arena", "compiler_runtime_activation", "validation_pipeline"],
        "composite": ["Pattern Completion", "Translation", "Bridge Creation", "Topology Preservation", "Color Transformation", "Growth Detection"],
        "graduation": ["translate", "preserve_topology", "preserve_colors", "preserve_grid", "duplicate_object"],
        "expansion": ["Identity", "Topology", "Transformation", "Growth"],
    },
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


def task_for(sequence: int, spec: dict) -> dict:
    title = spec["title"]
    category = spec["category"]
    transform_name = spec["transform"]
    concepts = list(spec["concepts"])
    domains = list(spec["domains"])
    composite = list(spec["composite"])
    graduation = list(spec["graduation"])
    expansion = list(spec["expansion"])
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
            "multi_step_reasoning",
            "multi_domain_reasoning",
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
            "curriculum_version": "Elite Training Curriculum V1",
            "task_id": task_id,
            "task_title": title,
            "elite_cognitive_task": True,
            "operationalization_phase_curriculum": True,
            "elite_category": category,
            "curriculum_tier": spec["tier"],
            "elite_task_difficulty": "very_high",
            "target_concepts": concepts,
            "target_domains": domains,
            "domain_count": len(domains),
            "minimum_domain_count": 3,
            "maximum_domain_count": 6,
            "multi_domain_reasoning": True,
            "multi_step_reasoning": True,
            "program_composition_required": True,
            "transformation_sequence_required": True,
            "operational_capability_composition_required": True,
            "novel_abstraction_required": True,
            "independent_validation_opportunities": [
                "exact_validation",
                "governed_validation",
                "independent_task_validation",
                "cross_domain_validation",
            ],
            "composite_capabilities": composite,
            "capability_graduation_targets": graduation,
            "domain_expansion_targets": expansion,
            "adaptive_reuse_opportunities": [
                "historical_pattern_reuse",
                "capability_transfer",
                "program_reuse",
                "cognitive_reuse",
            ],
            "curriculum_diagnostics_tags": [
                "capability_graduation",
                "domain_expansion",
                "composite_capability",
                "adaptive_reuse",
                "compiler_infrastructure",
                "operationalization",
            ],
            "deficiency_targets": [
                "operational_knowledge_waste",
                "low_operational_yield",
                "capability_population_evolution_lag",
                "validation_gaps",
                "domain_operationalization_gaps",
                "slow_capability_acquisition",
                "historical_exploitation_bias",
                "domain_population_imbalance",
                "adaptive_reuse_cognitive_only",
            ],
            "required_operational_capabilities": [
                "candidate_generation",
                "program_generation",
                "capability_composition",
                "compiler_runtime_activation",
                "world_model_validation",
                "cross_domain_collaboration",
                "capability_graduation",
                "domain_operationalization",
                "adaptive_reuse",
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
