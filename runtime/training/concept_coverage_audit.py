"""Concept coverage audit for ARC-style training tasks.

The audit is intentionally evidence-neutral: task metadata and lightweight grid
heuristics describe curriculum exposure, not truth promotion or mastery.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


TRAINING_DIRECTORY = Path("data/training")
REPORT_PATH = Path("concept_coverage_report.json")

CONCEPT_FAMILIES: dict[str, set[str]] = {
    "foundational": {
        "color_mapping",
        "color_transformation",
        "count_by_color",
        "shape_preservation",
        "object_counting",
        "object_count_increase",
        "object_tracking",
        "relative_position",
        "object_identity_preservation",
        "topology_preservation",
    },
    "intermediate": {
        "replication",
        "growth",
        "propagation",
        "density_modulation",
        "density_preservation",
        "scaling",
        "size_transformation",
        "rotation",
        "reflection",
        "rotation_reflection",
        "symbolic_mapping",
        "symbolic_remapping",
    },
    "advanced": {
        "containment",
        "inside_outside",
        "occlusion",
        "hidden_object_recovery",
        "topology_change",
        "topological_change",
        "topological_growth",
        "route_completion",
        "path_finding",
        "masking",
        "artifact_filtering",
        "noise_removal",
        "position_change",
        "topological_reasoning",
    },
    "frontier": {
        "multi_step_reasoning",
        "hierarchical_reasoning",
        "causal_reasoning",
        "causal_chains",
        "dependency_reasoning",
        "contextual_reasoning",
        "context_reasoning",
        "constraint_reasoning",
        "multi_concept_composition",
        "multi_object_reasoning",
        "visual_reconstruction",
    },
}

CONCEPT_CATEGORIES: dict[str, set[str]] = {
    "transformation_concepts": {
        "color_mapping",
        "color_transformation",
        "symbolic_mapping",
        "symbolic_remapping",
        "rotation",
        "reflection",
        "rotation_reflection",
        "scaling",
        "replication",
        "growth",
        "propagation",
        "gravity_simulation",
        "downward_motion",
        "pattern_completion",
        "sequence_completion",
    },
    "spatial_concepts": {
        "left_of",
        "right_of",
        "above",
        "below",
        "between",
        "adjacent",
        "nearest",
        "farthest",
        "inside",
        "outside",
        "inside_outside",
        "containment",
        "relative_position",
        "spatial_reasoning",
        "relative_movement",
        "path_finding",
        "route_completion",
        "obstacle_avoidance",
        "reachability",
    },
    "topological_concepts": {
        "topology_preservation",
        "topology_change",
        "topological_change",
        "topological_growth",
        "connected_components",
        "component_splitting",
        "component_merging",
        "hole_creation",
        "hole_removal",
        "bridge_creation",
        "bridge_destruction",
        "connectivity_preservation",
    },
    "symbolic_concepts": {
        "symbolic_mapping",
        "symbolic_remapping",
        "color_mapping",
        "count_by_color",
        "object_counting",
        "masking",
    },
    "causal_concepts": {
        "causal_reasoning",
        "causal_chains",
        "dependency_reasoning",
        "constraint_reasoning",
        "gravity_simulation",
        "downward_motion",
        "contextual_reasoning",
        "hierarchical_reasoning",
    },
}

MAJOR_ARC_CONCEPTS: tuple[str, ...] = tuple(sorted(set().union(
    *CONCEPT_FAMILIES.values(),
    *CONCEPT_CATEGORIES.values(),
    {
        "count_by_color",
        "hidden_object_recovery",
        "multi_object_reasoning",
        "object_counting",
        "pattern_completion",
        "sequence_completion",
        "shape_preservation",
        "visual_reconstruction",
    },
)))

MINIMUM_CONCEPT_EXPOSURE = 3
TARGET_FAMILY_DISTRIBUTION = {
    "foundational": 0.25,
    "intermediate": 0.35,
    "advanced": 0.25,
    "frontier": 0.15,
}


def audit_training_tasks(
    training_directory: Path | str = TRAINING_DIRECTORY,
    report_path: Path | str | None = REPORT_PATH,
) -> dict[str, Any]:
    """Analyze every JSON task and optionally write concept_coverage_report."""

    task_paths = sorted(Path(training_directory).glob("*.json"))
    task_reports = [_task_report(path) for path in task_paths]
    concept_to_tasks: dict[str, set[str]] = defaultdict(set)
    primary_counts: Counter[str] = Counter()

    for report in task_reports:
        task_id = report["task_id"]
        for concept in report["all_concepts"]:
            concept_to_tasks[concept].add(task_id)
        for concept in report["primary_concepts"]:
            primary_counts[concept] += 1

    total_tasks = len(task_reports)
    concept_reports = {}
    for concept in sorted(set(MAJOR_ARC_CONCEPTS) | set(concept_to_tasks)):
        task_ids = sorted(concept_to_tasks.get(concept, set()))
        task_count = len(task_ids)
        concept_reports[concept] = {
            "concept_name": concept,
            "task_count": task_count,
            "task_ids": task_ids,
            "coverage_score": _ratio(task_count, MINIMUM_CONCEPT_EXPOSURE),
            "discovery_frequency": _frequency(task_count, total_tasks),
            "truth_commit_frequency": 0.0,
            "graduation_frequency": 0.0,
            "primary_task_count": primary_counts.get(concept, 0),
            "family": concept_family(concept),
            "missing": task_count == 0,
            "rare": 0 < task_count < MINIMUM_CONCEPT_EXPOSURE,
        }

    covered = [concept for concept, item in concept_reports.items() if item["task_count"]]
    missing = [concept for concept, item in concept_reports.items() if item["missing"]]
    rare = [concept for concept, item in concept_reports.items() if item["rare"]]
    family_counts = _family_counts(task_reports)
    report = {
        "system": "concept_coverage_audit",
        "training_directory": str(training_directory),
        "total_tasks": total_tasks,
        "concept_count": len(concept_reports),
        "covered_concepts": sorted(covered),
        "missing_concepts": sorted(missing),
        "rare_concepts": sorted(rare),
        "coverage_percentage": _frequency(len(covered), len(concept_reports)),
        "target_family_distribution": TARGET_FAMILY_DISTRIBUTION,
        "family_task_counts": family_counts,
        "family_distribution": _family_distribution(family_counts),
        "concepts": concept_reports,
        "tasks": task_reports,
        "metadata_is_targeting_not_runtime_observation": True,
    }
    if report_path is not None:
        Path(report_path).write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return report


def concept_family(concept: str) -> str:
    for family, concepts in CONCEPT_FAMILIES.items():
        if concept in concepts:
            return family
    return "unclassified"


def categorize_concepts(concepts: Iterable[str]) -> dict[str, list[str]]:
    concept_set = {str(concept) for concept in concepts if concept}
    return {
        category: sorted(concept_set & members)
        for category, members in CONCEPT_CATEGORIES.items()
    }


def task_concepts(task: Mapping[str, Any]) -> list[str]:
    concepts: list[str] = []
    metadata = task.get("nexryn_metadata", {})
    for source in (
        metadata.get("target_concepts", []) if isinstance(metadata, Mapping) else [],
        metadata.get("concept_labels", []) if isinstance(metadata, Mapping) else [],
        task.get("target_concepts", []),
        task.get("concept_labels", []),
    ):
        if isinstance(source, str):
            concepts.append(source)
        else:
            concepts.extend(str(item) for item in source or [] if item)
    concepts.extend(_infer_grid_concepts(task))
    return list(dict.fromkeys(concepts))


def _task_report(path: Path) -> dict[str, Any]:
    try:
        task = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        task = {}
    metadata = task.get("nexryn_metadata", {})
    concepts = task_concepts(task)
    primary = concepts[:1] or ["unclassified"]
    secondary = concepts[1:]
    categories = categorize_concepts(concepts)
    return {
        "task_id": str(
            (
                metadata.get("task_id")
                if isinstance(metadata, Mapping)
                and metadata.get("task_id") is not None
                else ""
            )
        ) or path.stem,
        "task_file": str(path),
        "primary_concepts": primary,
        "secondary_concepts": secondary,
        "all_concepts": concepts,
        "transformation_concepts": categories["transformation_concepts"],
        "spatial_concepts": categories["spatial_concepts"],
        "topological_concepts": categories["topological_concepts"],
        "symbolic_concepts": categories["symbolic_concepts"],
        "causal_concepts": categories["causal_concepts"],
        "curriculum_level": curriculum_level_for(concepts),
        "multi_concept": len(concepts) > 1,
    }


def curriculum_level_for(concepts: Iterable[str]) -> int:
    families = {concept_family(concept) for concept in concepts}
    if "frontier" in families:
        return 4
    if "advanced" in families:
        return 3
    if "intermediate" in families:
        return 2
    return 1


def _infer_grid_concepts(task: Mapping[str, Any]) -> list[str]:
    inferred: set[str] = set()
    pairs = [
        item
        for item in task.get("train", [])
        if isinstance(item, Mapping) and "input" in item and "output" in item
    ]
    for pair in pairs:
        source = pair["input"]
        target = pair["output"]
        if not (_is_grid(source) and _is_grid(target)):
            continue
        source_cells = _nonzero_count(source)
        target_cells = _nonzero_count(target)
        if source_cells == target_cells and source != target:
            inferred.add("shape_preservation")
        if target_cells > source_cells:
            inferred.add("growth")
        if _colors(source) != _colors(target):
            inferred.add("color_transformation")
        if len(source) != len(target) or len(source[0]) != len(target[0]):
            inferred.add("scaling")
    return sorted(inferred)


def _is_grid(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(row, list) and row for row in value)
    )


def _nonzero_count(grid: list[list[int]]) -> int:
    return sum(1 for row in grid for value in row if value)


def _colors(grid: list[list[int]]) -> set[int]:
    return {int(value) for row in grid for value in row if value}


def _family_counts(task_reports: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counts = {family: 0 for family in TARGET_FAMILY_DISTRIBUTION}
    for report in task_reports:
        families = {
            concept_family(concept)
            for concept in report.get("all_concepts", [])
            if concept_family(concept) in counts
        }
        for family in families:
            counts[family] += 1
    return counts


def _family_distribution(counts: Mapping[str, int]) -> dict[str, float]:
    total = max(sum(counts.values()), 1)
    return {family: round(count / total, 4) for family, count in counts.items()}


def _frequency(count: int, total: int) -> float:
    return round(count / total, 4) if total else 0.0


def _ratio(count: int, target: int) -> float:
    return round(min(count / max(target, 1), 1.0), 4)


def main() -> None:
    print(json.dumps(audit_training_tasks(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
