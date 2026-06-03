import json

from runtime.learning.training_assistant import TrainingAssistant


def task_files(count=12):
    return [
        f"task_{sequence:03d}.json"
        for sequence in range(1, count + 1)
    ]


def test_training_assistant_selects_five_tasks_and_resumes_active_batch(
    tmp_path,
):
    state_path = tmp_path / "training_assistant_state.json"
    first = TrainingAssistant(state_path=state_path)
    selected = first.select_batch(task_files())

    resumed = TrainingAssistant(state_path=state_path).select_batch(
        task_files()
    )

    assert selected["selected_task_files"] == [
        "task_001.json",
        "task_002.json",
        "task_003.json",
        "task_004.json",
        "task_005.json",
    ]
    assert selected["resumed_active_batch"] is False
    assert resumed["selected_task_files"] == selected["selected_task_files"]
    assert resumed["resumed_active_batch"] is True


def test_training_assistant_advances_after_completed_cycle(tmp_path):
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json"
    )
    assistant.select_batch(task_files())
    completion = assistant.complete_cycle(
        successful_tasks=4,
        failed_tasks=1,
    )
    selected = assistant.select_batch(task_files())

    assert completion["cycle_completion_state"] == (
        "TRAINING_BATCH_COMPLETED"
    )
    assert completion["completed_cycles"] == 1
    assert selected["selected_task_files"] == [
        "task_006.json",
        "task_007.json",
        "task_008.json",
        "task_009.json",
        "task_010.json",
    ]


def test_training_assistant_wraps_at_end_of_task_list(tmp_path):
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json"
    )
    tasks = task_files(12)

    assistant.select_batch(tasks)
    assistant.complete_cycle()
    assistant.select_batch(tasks)
    assistant.complete_cycle()
    selected = assistant.select_batch(tasks)

    assert selected["selected_task_files"] == [
        "task_011.json",
        "task_012.json",
        "task_001.json",
        "task_002.json",
        "task_003.json",
    ]


def test_training_assistant_prioritizes_rare_concept_tasks(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    tasks = {
        "task_001.json": ["shape_preservation"],
        "task_002.json": ["topological_change"],
        "task_003.json": ["density_modulation"],
    }
    for task_file, concepts in tasks.items():
        (tasks_directory / task_file).write_text(
            json.dumps({
                "nexryn_metadata": {
                    "curriculum": "phase_7_targeted_batch_02",
                    "target_concepts": concepts,
                },
            }),
            encoding="utf-8",
        )
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        batch_size=2,
    )

    selected = assistant.select_batch(
        list(tasks),
        concept_counts={
            "shape_preservation": 39,
            "topological_change": 1,
        },
        concept_states={
            "shape_preservation": "STABLE_TRUTH",
            "topological_change": "BOUNDARY_REFINEMENT",
            "density_modulation": "DISCOVERING",
        },
        task_directory=tasks_directory,
    )

    assert selected["training_mode"] == (
        "concept_imbalance_prioritized_batch"
    )
    assert selected["selected_task_files"] == [
        "task_003.json",
        "task_002.json",
    ]
    assert selected["prioritized_concepts"] == [
        "density_modulation",
        "topological_change",
    ]


def test_training_assistant_prioritizes_unobserved_rare_concept_task(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    for task_file in ["task_001.json", "task_002.json"]:
        (tasks_directory / task_file).write_text(
            json.dumps({
                "nexryn_metadata": {
                    "target_concepts": ["topological_change"],
                },
            }),
            encoding="utf-8",
        )
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        batch_size=1,
    )

    selected = assistant.select_batch(
        ["task_001.json", "task_002.json"],
        concept_counts={"topological_change": 1},
        task_directory=tasks_directory,
        observed_task_ids=["data/training/task_001.json"],
    )

    assert selected["selected_task_files"] == ["task_002.json"]
