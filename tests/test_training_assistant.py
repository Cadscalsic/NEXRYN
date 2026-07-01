import json

from runtime.learning.training_assistant import TrainingAssistant


def task_files(count=12):
    return [
        f"task_{sequence:03d}.json"
        for sequence in range(1, count + 1)
    ]


def test_training_assistant_selects_three_tasks_and_resumes_active_batch(
    tmp_path,
):
    state_path = tmp_path / "training_assistant_state.json"
    memory_path = tmp_path / "task_selection_memory.json"
    first = TrainingAssistant(
        state_path=state_path,
        selection_memory_path=memory_path,
        selection_mode="curriculum",
    )
    selected = first.select_batch(task_files())

    resumed = TrainingAssistant(
        state_path=state_path,
        selection_memory_path=memory_path,
        selection_mode="curriculum",
    ).select_batch(
        task_files(),
        selection_mode="curriculum",
    )

    assert selected["selected_task_files"] == [
        "task_001.json",
        "task_002.json",
        "task_003.json",
    ]
    assert selected["resumed_active_batch"] is False
    assert resumed["selected_task_files"] == selected["selected_task_files"]
    assert resumed["resumed_active_batch"] is True


def test_training_assistant_advances_after_completed_cycle(tmp_path):
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        selection_mode="curriculum",
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
        "task_004.json",
        "task_005.json",
        "task_006.json",
    ]


def test_training_assistant_wraps_at_end_of_task_list(tmp_path):
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        selection_mode="curriculum",
    )
    tasks = task_files(12)

    assistant.select_batch(tasks)
    assistant.complete_cycle()
    assistant.select_batch(tasks)
    assistant.complete_cycle()
    assistant.select_batch(tasks)
    assistant.complete_cycle()
    assistant.select_batch(tasks)
    assistant.complete_cycle()
    selected = assistant.select_batch(tasks)

    assert selected["selected_task_files"] == [
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
        selection_memory_path=tmp_path / "task_selection_memory.json",
        batch_size=2,
        selection_mode="curriculum",
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
        "knowledge_expansion_prioritized_batch"
    )
    assert selected["selected_task_files"] == [
        "task_003.json",
        "task_002.json",
    ]
    assert selected["prioritized_concepts"] == [
        "density_modulation",
        "topological_change",
    ]
    assert (
        selected["training_diversity_report"]["knowledge_expansion_score"]
        > 0.0
    )


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
        selection_memory_path=tmp_path / "task_selection_memory.json",
        batch_size=1,
        selection_mode="curriculum",
    )

    selected = assistant.select_batch(
        ["task_001.json", "task_002.json"],
        concept_counts={"topological_change": 1},
        task_directory=tasks_directory,
        observed_task_ids=["data/training/task_001.json"],
    )

    assert selected["selected_task_files"] == ["task_002.json"]


def test_training_assistant_deprioritizes_recent_core_knowledge(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    tasks = {
        "task_001.json": ["shape_preservation"],
        "task_002.json": ["occlusion"],
    }
    for task_file, concepts in tasks.items():
        (tasks_directory / task_file).write_text(
            json.dumps({
                "nexryn_metadata": {
                    "target_concepts": concepts,
                },
            }),
            encoding="utf-8",
        )
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        batch_size=1,
        selection_mode="curriculum",
    )
    assistant.state["history"] = [
        {
            "cycle": 1,
            "task_files": ["task_001.json"],
            "concepts": ["shape_preservation"],
        }
    ]

    selected = assistant.select_batch(
        list(tasks),
        concept_counts={"shape_preservation": 40, "occlusion": 0},
        concept_states={"shape_preservation": "CORE_KNOWLEDGE"},
        task_directory=tasks_directory,
        core_knowledge=[
            {
                "concept": "shape_preservation",
                "graduation_level": "CORE_KNOWLEDGE",
                "mastery_score": 0.96,
                "training_dominance_penalty": 0.75,
            }
        ],
    )

    assert selected["selected_task_files"] == ["task_002.json"]
    assert selected["selected_concepts"] == ["occlusion"]
    assert selected["training_diversity_report"][
        "cooldown_filtered_concepts"
    ] == ["shape_preservation"]


def test_training_assistant_weighted_random_avoids_previous_batch_overlap(
    tmp_path,
):
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        batch_size=3,
        random_seed=11,
    )
    tasks = task_files(30)

    first = assistant.select_batch(tasks)
    second = assistant.select_batch(tasks, random_seed=12)

    assert first["training_mode"] == "weighted_random"
    assert len(set(first["selected_task_files"])) == 3
    assert (
        set(first["selected_task_files"])
        & set(second["selected_task_files"])
    ) == set()
    assert second["selection_diversity_report"][
        "previous_batch_overlap_count"
    ] == 0
    assert second["selection_diversity_report"]["unseen_tasks_selected"] > 0


def test_training_assistant_persists_task_selection_memory(tmp_path):
    memory_path = tmp_path / "task_selection_memory.json"
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=memory_path,
        batch_size=2,
        random_seed=7,
    )

    selected = assistant.select_batch(task_files(12))
    memory = json.loads(memory_path.read_text(encoding="utf-8"))

    assert memory["previous_batch"] == selected["selected_task_files"]
    assert memory["run_counter"] == 1
    for task_file in selected["selected_task_files"]:
        assert memory["tasks"][task_file]["times_selected"] == 1
        assert memory["tasks"][task_file]["last_run_id"]
