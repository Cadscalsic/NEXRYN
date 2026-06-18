from collections import Counter

from data.curriculum.arc_concept_curriculum import (
    CONCEPT_FAMILIES,
    TASKS_PER_FAMILY,
    build_curriculum,
)


def test_arc_concept_curriculum_generates_required_families():
    tasks = build_curriculum()
    families = {task["concept_family"] for task in tasks}

    assert families == set(CONCEPT_FAMILIES)
    assert len(tasks) == len(CONCEPT_FAMILIES) * TASKS_PER_FAMILY


def test_arc_concept_curriculum_tasks_are_evidence_only_arc_payloads():
    task = build_curriculum(tasks_per_family=1)[0]

    assert set(task) >= {
        "concept_family",
        "concept_labels",
        "difficulty",
        "train",
        "test",
        "expected_transformations",
        "negative_controls",
        "nexryn_metadata",
    }
    assert len(task["train"]) == 2
    assert len(task["test"]) == 1
    assert task["negative_controls"]
    assert task["nexryn_metadata"]["target_concepts"] == task["concept_labels"]
    assert task["nexryn_metadata"]["governance_constraints"] == {
        "force_truth_promotion": False,
        "lower_thresholds": False,
        "manual_stable_truth": False,
        "evidence_only": True,
    }


def test_arc_concept_curriculum_covers_missing_concepts():
    coverage = Counter(
        label
        for task in build_curriculum()
        for label in task["concept_labels"]
    )

    for concept in [
        "object_counting",
        "spatial_reasoning",
        "pattern_completion",
        "color_mapping",
        "color_transformation",
        "gravity_simulation",
        "rotation",
        "reflection",
        "scaling",
        "occlusion",
        "masking",
        "inside_outside",
        "path_finding",
        "noise_removal",
    ]:
        assert coverage[concept] >= TASKS_PER_FAMILY
