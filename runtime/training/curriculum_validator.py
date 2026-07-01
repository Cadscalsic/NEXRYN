"""Validate balance and diversity of the ARC training curriculum."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from runtime.training.concept_coverage_audit import (
    TARGET_FAMILY_DISTRIBUTION,
    audit_training_tasks,
)


TRAINING_DIRECTORY = Path("data/training")


class CurriculumValidator:
    system_name = "curriculum_validator"

    def validate(
        self,
        training_directory: Path | str = TRAINING_DIRECTORY,
        audit_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        report = dict(
            audit_report
            or audit_training_tasks(training_directory, report_path=None)
        )
        tasks = list(report.get("tasks", []))
        concepts = dict(report.get("concepts", {}))
        total_tasks = int(report.get("total_tasks", len(tasks)))
        covered = list(report.get("covered_concepts", []))
        missing = list(report.get("missing_concepts", []))
        family_distribution = dict(report.get("family_distribution", {}))

        generated_tasks = [
            task for task in tasks
            if "arc_generated_" in str(task.get("task_id", ""))
            or "arc_concept_" in str(task.get("task_id", ""))
        ]
        frontier_concepts = [
            concept for concept, item in concepts.items()
            if item.get("family") == "frontier" and item.get("task_count", 0)
        ]
        multi_concept_tasks = [
            task for task in tasks if task.get("multi_concept")
        ]
        scores = {
            "concept_diversity_score": _ratio(len(covered), max(len(concepts), 1)),
            "task_diversity_score": _ratio(
                len({tuple(task.get("all_concepts", [])) for task in tasks}),
                max(total_tasks, 1),
            ),
            "concept_coverage_score": _ratio(len(covered), max(len(concepts), 1)),
            "frontier_concept_score": _ratio(
                len(frontier_concepts),
                max(
                    sum(1 for item in concepts.values() if item.get("family") == "frontier"),
                    1,
                ),
            ),
            "curriculum_balance_score": _balance_score(family_distribution),
            "missing_concept_score": 1.0 - _ratio(len(missing), max(len(concepts), 1)),
            "redundancy_score": _redundancy_score(concepts, total_tasks),
        }
        coverage_report = {
            "total_tasks": total_tasks,
            "generated_tasks": len(generated_tasks),
            "concept_count": len(concepts),
            "covered_concepts": sorted(covered),
            "missing_concepts": sorted(missing),
            "coverage_percentage": report.get("coverage_percentage", 0.0),
            "frontier_concepts": sorted(frontier_concepts),
            "topology_tasks": _concept_task_total(concepts, "topolog"),
            "containment_tasks": _concept_task_total(concepts, "containment"),
            "occlusion_tasks": _concept_task_total(concepts, "occlusion"),
            "path_reasoning_tasks": _concept_task_total(concepts, "path")
            + _concept_task_total(concepts, "route"),
            "scaling_tasks": _concept_task_total(concepts, "scaling"),
            "multi_concept_tasks": len(multi_concept_tasks),
            "curriculum_balance_score": scores["curriculum_balance_score"],
        }
        return {
            "system": self.system_name,
            **scores,
            "family_distribution": family_distribution,
            "target_family_distribution": TARGET_FAMILY_DISTRIBUTION,
            "curriculum_coverage_report": coverage_report,
        }


def validate_curriculum(
    training_directory: Path | str = TRAINING_DIRECTORY,
    audit_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return CurriculumValidator().validate(training_directory, audit_report)


def _concept_task_total(concepts: Mapping[str, Mapping[str, Any]], fragment: str) -> int:
    return sum(
        int(item.get("task_count", 0))
        for concept, item in concepts.items()
        if fragment in concept
    )


def _balance_score(distribution: Mapping[str, Any]) -> float:
    drift = 0.0
    for family, target in TARGET_FAMILY_DISTRIBUTION.items():
        try:
            observed = float(distribution.get(family, 0.0))
        except (TypeError, ValueError):
            observed = 0.0
        drift += abs(observed - target)
    return round(max(0.0, 1.0 - drift / 2.0), 4)


def _redundancy_score(concepts: Mapping[str, Mapping[str, Any]], total_tasks: int) -> float:
    if not concepts or not total_tasks:
        return 0.0
    max_share = max(
        int(item.get("task_count", 0)) / total_tasks
        for item in concepts.values()
    )
    return round(max(0.0, 1.0 - max_share), 4)


def _ratio(value: int | float, total: int | float) -> float:
    return round(float(value) / float(total), 4) if total else 0.0


def main() -> None:
    print(json.dumps(validate_curriculum(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

