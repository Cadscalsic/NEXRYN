import json

from runtime.training.curriculum_manager import CurriculumManager


def write_task(directory, task_file, concepts):
    (directory / task_file).write_text(
        json.dumps({
            "nexryn_metadata": {
                "target_concepts": concepts,
            },
        }),
        encoding="utf-8",
    )


def test_curriculum_manager_scores_scarcity_and_lifecycle_state(tmp_path):
    write_task(tmp_path, "stable.json", ["shape_preservation"])
    write_task(tmp_path, "discovering.json", ["topological_change"])
    write_task(tmp_path, "boundary.json", ["density_modulation"])

    report = CurriculumManager().rank_tasks(
        ["stable.json", "boundary.json", "discovering.json"],
        concept_counts={
            "shape_preservation": 39,
            "topological_change": 1,
            "density_modulation": 2,
        },
        concept_states={
            "shape_preservation": "STABLE_TRUTH",
            "topological_change": "DISCOVERING",
            "density_modulation": "BOUNDARY_REFINEMENT",
        },
        task_directory=tmp_path,
    )

    assert report["ranked_task_files"] == [
        "discovering.json",
        "boundary.json",
        "stable.json",
    ]
    priorities = {
        item["task_file"]: item["priority"]
        for item in report["task_priorities"]
    }
    assert priorities == {
        "discovering.json": 310,
        "boundary.json": 285,
        "stable.json": 0,
    }
    discovering = report["task_priorities"][0]["concept_priorities"][0]
    assert discovering["target_count"] == 20
    assert discovering["coverage_gap"] == 19
    assert discovering["coverage_ratio"] == 0.05


def test_curriculum_manager_prefers_unobserved_tasks_for_rare_concepts(
    tmp_path,
):
    write_task(tmp_path, "observed.json", ["topological_change"])
    write_task(tmp_path, "novel.json", ["topological_change"])

    report = CurriculumManager().rank_tasks(
        ["observed.json", "novel.json"],
        concept_counts={"topological_change": 1},
        task_directory=tmp_path,
        observed_task_ids=["data/training/observed.json"],
    )

    assert report["ranked_task_files"] == [
        "novel.json",
        "observed.json",
    ]
    assert report["task_priorities"][0]["unobserved_task"] is True


def test_curriculum_manager_represents_each_deficient_target_in_batch(
    tmp_path,
):
    write_task(
        tmp_path,
        "topology.json",
        ["topological_change", "topological_reasoning"],
    )
    write_task(tmp_path, "density.json", ["density_modulation"])
    manager = CurriculumManager()
    report = manager.rank_tasks(
        ["topology.json", "density.json"],
        concept_counts={
            "topological_change": 1,
            "topological_reasoning": 2,
            "density_modulation": 2,
        },
        task_directory=tmp_path,
    )

    assert manager.select_batch_tasks(report, batch_size=2) == [
        "topology.json",
        "density.json",
    ]


def test_curriculum_manager_falls_back_to_family_related_tasks(
    tmp_path,
):
    write_task(tmp_path, "grow_topology.json", ["grow_topology"])
    write_task(tmp_path, "color_maintenance.json", ["color_preservation"])
    manager = CurriculumManager()
    report = manager.rank_tasks(
        ["grow_topology.json", "color_maintenance.json"],
        concept_counts={"topological_change": 1},
        task_directory=tmp_path,
    )

    assert report["training_mode"] == (
        "concept_imbalance_prioritized_batch"
    )
    assert report["ranked_task_files"][0] == "grow_topology.json"
    assert manager.select_batch_tasks(report, batch_size=1) == [
        "grow_topology.json",
    ]


def test_preservation_concept_diverts_from_family_transform():
    manager = CurriculumManager()

    bias = manager._preservation_bias_for(
        "color_preservation",
        {
            "color_preservation": 3,
            "color_transform": 1,
        },
        {"color_transform"},
    )

    assert bias["priority"] == manager.PRESERVATION_FAMILY_DIVERSION_PENALTY
    assert bias["reasons"] == [
        "preservation_concept_diverts_from_family_transform",
    ]


def test_preservation_compound_bias_is_skipped_without_available_family_transform():
    manager = CurriculumManager()

    bias = manager._preservation_bias_for(
        "color_preservation",
        {
            "color_preservation": 39,
            "color_transform": 0,
        },
        {"color_preservation"},
    )

    assert bias["priority"] == 0
    assert bias["reasons"] == []
