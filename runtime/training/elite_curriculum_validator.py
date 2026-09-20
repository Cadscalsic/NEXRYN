"""Diagnostics for the Elite Training Curriculum V1.

The validator reads task metadata only. It does not promote truths, change
training architecture, or alter runtime decision policies.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping


TRAINING_DIRECTORY = Path("data/training")
ELITE_CURRICULUM_NAME = "nexryn_elite_training_curriculum_v1"
ELITE_VALIDATION_ACADEMY_NAME = "nexryn_elite_validation_academy_v1"
ELITE_VALIDATION_ACADEMY_PATH = Path(
    "data/curriculum/elite_validation_academy_v1.json"
)
REQUIRED_DOMAINS = {
    "Color",
    "Transformation",
    "Topology",
    "Spatial",
    "Identity",
    "Growth",
    "Geometry",
}
REQUIRED_GRADUATION_TARGETS = {
    "translate",
    "preserve_topology",
    "preserve_colors",
    "preserve_grid",
    "duplicate_object",
}
REQUIRED_DIAGNOSTIC_TAGS = {
    "capability_graduation",
    "domain_expansion",
    "composite_capability",
    "adaptive_reuse",
    "compiler_infrastructure",
    "operationalization",
}
REQUIRED_TIERS = {
    "Tier 1": "Operationalization Tasks",
    "Tier 2": "Capability Graduation Tasks",
    "Tier 3": "Composite Capability Tasks",
    "Tier 4": "Elite Multi-Domain Tasks",
}
REQUIRED_VALIDATION_GROUPS = {
    "Capability Validation Tasks": 10,
    "Composite Capability Validation Tasks": 5,
    "Cross Domain Validation Tasks": 5,
    "Trust Formation Tasks": 5,
    "Capability Graduation Tasks": 5,
    "Advanced Multi-Concept Validation Tasks": 20,
}
ELITE_VALIDATION_ACADEMY_TASK_COUNT = sum(REQUIRED_VALIDATION_GROUPS.values())
REQUIRED_VALIDATION_FIELDS = {
    "task_id",
    "task_name",
    "elite_group",
    "target_capability",
    "target_cluster",
    "target_domain",
    "required_ground_truth",
    "required_validation_evidence",
    "required_task_property",
    "validation_objective",
    "trust_objective",
    "graduation_objective",
    "difficulty_level",
    "promotion_weight",
    "cross_domain_requirement",
    "operationalization_objective",
    "expected_capability_promotion",
    "expected_governed_validation_effect",
    "expected_capability_trust_effect",
    "expected_graduation_effect",
}
ADVANCED_VALIDATION_FIELDS = {
    "target_cognitive_domains",
    "primary_evidence_category",
    "secondary_evidence_categories",
    "required_grounding",
    "expected_validation_contract",
    "capability_targets",
    "cross_domain_participation",
    "reasoning_complexity",
    "operational_reuse_potential",
    "prerequisite_capabilities",
    "validation_difficulty",
    "graduation_relevance",
}


class EliteCurriculumValidator:
    system_name = "elite_curriculum_validator"

    def validate(
        self,
        training_directory: Path | str = TRAINING_DIRECTORY,
    ) -> dict[str, Any]:
        directory = Path(training_directory)
        tasks = []
        for path in sorted(directory.glob("elite_cognitive_task_*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            metadata = payload.get("nexryn_metadata")
            if not isinstance(metadata, Mapping):
                continue
            if metadata.get("curriculum") != ELITE_CURRICULUM_NAME:
                continue
            tasks.append({
                "task_file": path.name,
                "metadata": dict(metadata),
                "train_count": len(payload.get("train") or []),
                "test_count": len(payload.get("test") or []),
            })
        tier_counts = Counter(
            task["metadata"].get("curriculum_tier")
            for task in tasks
        )
        domains = Counter()
        graduation = Counter()
        tags = Counter()
        composite_task_count = 0
        adaptive_task_count = 0
        invalid_tasks = []
        task_rows = []
        for task in tasks:
            metadata = task["metadata"]
            task_domains = [
                str(item)
                for item in metadata.get("target_domains", [])
                if item
            ]
            task_graduation = [
                str(item)
                for item in metadata.get("capability_graduation_targets", [])
                if item
            ]
            task_tags = [
                str(item)
                for item in metadata.get("curriculum_diagnostics_tags", [])
                if item
            ]
            composite = [
                str(item)
                for item in metadata.get("composite_capabilities", [])
                if item
            ]
            adaptive = [
                str(item)
                for item in metadata.get("adaptive_reuse_opportunities", [])
                if item
            ]
            domains.update(task_domains)
            graduation.update(task_graduation)
            tags.update(task_tags)
            if composite:
                composite_task_count += 1
            if adaptive:
                adaptive_task_count += 1
            failures = []
            if len(task_domains) < 3 or len(task_domains) > 6:
                failures.append("domain_count_out_of_bounds")
            if not metadata.get("multi_step_reasoning"):
                failures.append("missing_multi_step_reasoning")
            if not metadata.get("program_composition_required"):
                failures.append("missing_program_composition")
            if not composite:
                failures.append("missing_composite_capabilities")
            if not adaptive:
                failures.append("missing_adaptive_reuse_opportunity")
            if task["train_count"] < 2 or task["test_count"] < 1:
                failures.append("insufficient_independent_validation_surface")
            if failures:
                invalid_tasks.append({
                    "task_file": task["task_file"],
                    "failures": failures,
                })
            task_rows.append({
                "task_file": task["task_file"],
                "tier": metadata.get("curriculum_tier"),
                "elite_task_difficulty": metadata.get("elite_task_difficulty"),
                "domain_count": len(task_domains),
                "target_domains": task_domains,
                "graduation_targets": task_graduation,
                "composite_capabilities": composite,
                "adaptive_reuse_opportunities": adaptive,
                "training_value_score": self._task_value_score(
                    domain_count=len(task_domains),
                    graduation_count=len(task_graduation),
                    composite_count=len(composite),
                    adaptive_count=len(adaptive),
                    tag_count=len(task_tags),
                    invalid=bool(failures),
                ),
            })
        task_count = len(tasks)
        tier_health = _ratio(
            sum(1 for tier in REQUIRED_TIERS if tier_counts.get(tier) == 5),
            len(REQUIRED_TIERS),
        )
        domain_coverage = _ratio(
            len(REQUIRED_DOMAINS & set(domains)),
            len(REQUIRED_DOMAINS),
        )
        graduation_coverage = _ratio(
            len(REQUIRED_GRADUATION_TARGETS & set(graduation)),
            len(REQUIRED_GRADUATION_TARGETS),
        )
        tag_coverage = _ratio(
            len(REQUIRED_DIAGNOSTIC_TAGS & set(tags)),
            len(REQUIRED_DIAGNOSTIC_TAGS),
        )
        composite_coverage = _ratio(composite_task_count, task_count)
        adaptive_coverage = _ratio(adaptive_task_count, task_count)
        operationalization_coverage = _ratio(
            tags.get("operationalization", 0),
            task_count,
        )
        utilization = _ratio(task_count, 20)
        diversity = round(
            (
                domain_coverage
                + tag_coverage
                + _ratio(len(tier_counts), len(REQUIRED_TIERS))
            )
            / 3,
            4,
        )
        training_value = _average(row["training_value_score"] for row in task_rows)
        health = round(
            (
                tier_health
                + domain_coverage
                + graduation_coverage
                + composite_coverage
                + adaptive_coverage
                + operationalization_coverage
                + diversity
                + utilization
                + (1.0 - _ratio(len(invalid_tasks), max(task_count, 1)))
            )
            / 9,
            4,
        )
        return {
            "system": self.system_name,
            "curriculum": ELITE_CURRICULUM_NAME,
            "elite_task_count": task_count,
            "elite_curriculum_health": health,
            "elite_task_difficulty": "very_high" if task_count else "not_available",
            "capability_graduation_coverage": graduation_coverage,
            "domain_expansion_coverage": domain_coverage,
            "composite_capability_coverage": composite_coverage,
            "adaptive_reuse_coverage": adaptive_coverage,
            "operationalization_coverage": operationalization_coverage,
            "curriculum_diversity_score": diversity,
            "elite_task_utilization": utilization,
            "training_value_score": training_value,
            "tier_distribution": dict(sorted(tier_counts.items())),
            "domain_distribution": dict(sorted(domains.items())),
            "graduation_target_distribution": dict(sorted(graduation.items())),
            "diagnostic_tag_distribution": dict(sorted(tags.items())),
            "invalid_elite_tasks": invalid_tasks,
            "elite_task_rows": task_rows,
            "elite_curriculum_readiness": (
                "READY"
                if health >= 0.90 and task_count == 20 and not invalid_tasks
                else "PARTIAL"
                if task_count
                else "MISSING"
            ),
        }

    def _task_value_score(
        self,
        *,
        domain_count: int,
        graduation_count: int,
        composite_count: int,
        adaptive_count: int,
        tag_count: int,
        invalid: bool,
    ) -> float:
        score = (
            _ratio(domain_count, 6) * 0.25
            + _ratio(graduation_count, 3) * 0.20
            + _ratio(composite_count, 4) * 0.20
            + _ratio(adaptive_count, 4) * 0.15
            + _ratio(tag_count, len(REQUIRED_DIAGNOSTIC_TAGS)) * 0.20
        )
        if invalid:
            score *= 0.5
        return round(min(1.0, score), 4)


def validate_elite_curriculum(
    training_directory: Path | str = TRAINING_DIRECTORY,
) -> dict[str, Any]:
    return EliteCurriculumValidator().validate(training_directory)


def validate_elite_validation_academy(
    academy_path: Path | str = ELITE_VALIDATION_ACADEMY_PATH,
) -> dict[str, Any]:
    path = Path(academy_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "system": "elite_validation_academy_validator",
            "academy": ELITE_VALIDATION_ACADEMY_NAME,
            "academy_task_count": 0,
            "academy_readiness": "MISSING",
            "invalid_validation_tasks": [{
                "task_file": str(path),
                "failures": ["academy_file_unreadable"],
            }],
        }
    tasks = payload.get("tasks") or []
    tasks = tasks if isinstance(tasks, list) else []
    group_counts = Counter(
        str(task.get("elite_group"))
        for task in tasks
        if isinstance(task, Mapping)
    )
    required_properties = Counter()
    target_capabilities = Counter()
    target_clusters = Counter()
    invalid_tasks = []
    for index, task in enumerate(tasks, start=1):
        if not isinstance(task, Mapping):
            invalid_tasks.append({
                "task_id": f"task:{index}",
                "failures": ["task_not_mapping"],
            })
            continue
        failures = []
        missing_fields = [
            field for field in sorted(REQUIRED_VALIDATION_FIELDS)
            if task.get(field) in (None, "", [])
        ]
        if missing_fields:
            failures.append(
                "missing_required_fields:" + ",".join(missing_fields)
            )
        if not isinstance(task.get("cross_domain_requirement"), list):
            failures.append("cross_domain_requirement_not_list")
        elif len(task.get("cross_domain_requirement") or []) < 2:
            failures.append("insufficient_cross_domain_requirement")
        if task.get("elite_group") == "Advanced Multi-Concept Validation Tasks":
            missing_advanced_fields = [
                field for field in sorted(ADVANCED_VALIDATION_FIELDS)
                if task.get(field) in (None, "", [])
            ]
            if missing_advanced_fields:
                failures.append(
                    "missing_advanced_fields:"
                    + ",".join(missing_advanced_fields)
                )
            for field in (
                "target_cognitive_domains",
                "secondary_evidence_categories",
                "required_grounding",
                "capability_targets",
                "cross_domain_participation",
                "prerequisite_capabilities",
            ):
                if not isinstance(task.get(field), list):
                    failures.append(f"{field}_not_list")
            if task.get("truth_authority") != "NONE":
                failures.append("truth_authority_not_none")
            if task.get("trust_authority") != "NONE":
                failures.append("trust_authority_not_none")
            if task.get("graduation_authority") != "NONE":
                failures.append("graduation_authority_not_none")
        weight = task.get("promotion_weight")
        if not isinstance(weight, int | float) or not 0.0 <= float(weight) <= 1.0:
            failures.append("promotion_weight_out_of_bounds")
        required_properties[str(task.get("required_task_property"))] += 1
        target_capabilities[str(task.get("target_capability"))] += 1
        target_clusters[str(task.get("target_cluster"))] += 1
        if failures:
            invalid_tasks.append({
                "task_id": task.get("task_id") or f"task:{index}",
                "failures": failures,
            })
    distribution_ok = all(
        group_counts.get(group, 0) == expected
        for group, expected in REQUIRED_VALIDATION_GROUPS.items()
    )
    fields_ok = not invalid_tasks
    task_count_ok = len(tasks) == ELITE_VALIDATION_ACADEMY_TASK_COUNT
    property_coverage = _ratio(len([
        key for key in required_properties
        if key and key != "None"
    ]), 8)
    cluster_coverage = _ratio(len([
        key for key in target_clusters
        if key and key != "None"
    ]), 6)
    health = round(
        (
            (1.0 if payload.get("academy") == ELITE_VALIDATION_ACADEMY_NAME else 0.0)
            + (1.0 if task_count_ok else 0.0)
            + (1.0 if distribution_ok else 0.0)
            + (1.0 if fields_ok else 0.0)
            + min(property_coverage, 1.0)
            + min(cluster_coverage, 1.0)
        )
        / 6,
        4,
    )
    return {
        "system": "elite_validation_academy_validator",
        "academy": payload.get("academy") or ELITE_VALIDATION_ACADEMY_NAME,
        "academy_version": payload.get("academy_version"),
        "academy_task_count": len(tasks),
        "academy_health": health,
        "academy_readiness": (
            "READY"
            if health >= 0.95
            and task_count_ok
            and distribution_ok
            and fields_ok
            else "PARTIAL"
            if tasks
            else "MISSING"
        ),
        "group_distribution": dict(sorted(group_counts.items())),
        "required_task_property_distribution": dict(
            sorted(required_properties.items())
        ),
        "target_capability_distribution": dict(sorted(target_capabilities.items())),
        "target_cluster_distribution": dict(sorted(target_clusters.items())),
        "invalid_validation_tasks": invalid_tasks,
    }


def _ratio(value: int | float, total: int | float) -> float:
    return round(float(value) / float(total), 4) if total else 0.0


def _average(values: Any) -> float:
    rows = [
        float(value)
        for value in values
        if isinstance(value, (int, float))
    ]
    if not rows:
        return 0.0
    return round(sum(rows) / len(rows), 4)


__all__ = [
    "ELITE_CURRICULUM_NAME",
    "ELITE_VALIDATION_ACADEMY_NAME",
    "EliteCurriculumValidator",
    "validate_elite_curriculum",
    "validate_elite_validation_academy",
]
