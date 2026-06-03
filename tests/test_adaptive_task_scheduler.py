import json
from pathlib import Path

from runtime.adaptive_task_scheduler import AdaptiveTaskScheduler


def write_task_metadata(directory, task_file, metadata):
    (directory / task_file).write_text(
        json.dumps({
            "nexryn_metadata": metadata,
        }),
        encoding="utf-8",
    )


def test_adaptive_task_scheduler_prioritizes_rare_target_concepts(tmp_path):
    task_directory = tmp_path / "training"
    task_directory.mkdir()
    write_task_metadata(
        task_directory,
        "task_001.json",
        {
            "curriculum": "phase_7_prelude_batch_01",
            "target_concepts": ["shape_preservation"],
        },
    )
    write_task_metadata(
        task_directory,
        "task_005.json",
        {
            "curriculum": "phase_7_targeted_batch_02",
            "target_concepts": ["topological_change"],
        },
    )
    scheduler = AdaptiveTaskScheduler()

    queue = scheduler.build_task_queue(
        ["task_001.json", "task_005.json"],
        concept_counts={
            "shape_preservation": 39,
            "topological_change": 1,
        },
        task_directory=task_directory,
    )

    assert queue[0]["task"] == "task_005.json"
    assert queue[0]["rarity_score"] > queue[1]["rarity_score"]


def test_adaptive_task_scheduler_falls_back_to_complexity_without_metadata():
    scheduler = AdaptiveTaskScheduler()
    queue = scheduler.build_task_queue([
        "task_001.json",
        "task_003.json",
        "task_010.json",
    ])

    assert [item["task"] for item in queue] == [
        "task_001.json",
        "task_003.json",
        "task_010.json",
    ]
