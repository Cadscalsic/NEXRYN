import json

from runtime.learning.training_assistant import TrainingAssistant


def _assistant(tmp_path, batch_size=1):
    return TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        batch_size=batch_size,
        selection_mode="curriculum",
    )


def _write_elite_task(directory, task_file, concepts, capabilities=None):
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "nexryn_metadata": {
            "curriculum": "nexryn_elite_training_curriculum_v1",
            "operationalization_phase_curriculum": True,
            "elite_cognitive_task": True,
            "target_concepts": list(concepts),
            "target_domains": ["Spatial", "Topology"],
            "deficiency_targets": ["validation_gap"],
            "required_operational_capabilities": list(
                capabilities or concepts
            ),
        },
    }
    (directory / task_file).write_text(json.dumps(payload), encoding="utf-8")


def _task_names(count):
    return [
        f"elite_cognitive_task_{index:02d}.json"
        for index in range(1, count + 1)
    ]


def test_adaptive_elite_selector_damps_saturated_recent_repeat(tmp_path):
    tasks_directory = tmp_path / "training"
    saturated, useful, novelty_only = _task_names(3)
    _write_elite_task(
        tasks_directory,
        saturated,
        [f"saturated_capability_{index}" for index in range(15)],
    )
    _write_elite_task(
        tasks_directory,
        useful,
        [f"useful_information_gain_{index}" for index in range(8)],
    )
    _write_elite_task(tasks_directory, novelty_only, ["novelty_only"])

    assistant = _assistant(tmp_path)
    assistant.selection_memory = {
        **assistant.selection_memory,
        "run_counter": 31,
        "previous_batch": [saturated],
        "tasks": {
            saturated: {
                "task_id": saturated,
                "times_selected": 31,
                "recent_selection_count": 31,
            },
        },
        "recent_runs": [
            {"run_id": f"run_{index}", "task_ids": [saturated]}
            for index in range(31)
        ],
    }

    selected = assistant.select_batch(
        [saturated, useful, novelty_only],
        task_directory=tasks_directory,
    )
    priorities = selected["elite_selection_report"]["elite_task_priorities"]
    saturated_row = next(row for row in priorities if row["task_file"] == saturated)

    assert selected["selected_task_files"] == [useful]
    assert saturated_row["exposure_penalty"] > 0
    assert saturated_row["recency_penalty"] > 0
    assert saturated_row["final_selection_score"] < saturated_row["base_priority"]


def test_adaptive_elite_selector_keeps_repeated_high_value_task_eligible(tmp_path):
    tasks_directory = tmp_path / "training"
    repeated, shallow = _task_names(2)
    _write_elite_task(
        tasks_directory,
        repeated,
        [f"high_value_probe_{index}" for index in range(28)],
    )
    _write_elite_task(tasks_directory, shallow, ["shallow_novel_probe"])

    assistant = _assistant(tmp_path)
    assistant.selection_memory = {
        **assistant.selection_memory,
        "previous_batch": [repeated],
        "tasks": {
            repeated: {
                "task_id": repeated,
                "times_selected": 4,
                "recent_selection_count": 2,
            },
        },
        "recent_runs": [
            {"run_id": "run_1", "task_ids": [repeated]},
        ],
    }

    selected = assistant.select_batch(
        [repeated, shallow],
        task_directory=tasks_directory,
    )
    repeated_row = next(
        row
        for row in selected["elite_selection_report"]["elite_task_priorities"]
        if row["task_file"] == repeated
    )

    assert selected["selected_task_files"] == [repeated]
    assert "repeated_task_retained_when_value_exceeds_penalty" in repeated_row[
        "priority_reasons"
    ]


def test_adaptive_elite_selector_exposes_required_score_breakdown(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks = _task_names(3)
    for index, task_file in enumerate(tasks, start=1):
        _write_elite_task(
            tasks_directory,
            task_file,
            [f"capability_{index}", f"coverage_{index}"],
        )

    selected = _assistant(tmp_path, batch_size=2).select_batch(
        tasks,
        task_directory=tasks_directory,
    )
    report = selected["elite_selection_report"]

    assert report["adaptive_task_selection_contract"][
        "selector_decision_owner"
    ] == "TrainingAssistant"
    for row in report["elite_task_priorities"]:
        for field in (
            "base_priority",
            "exposure_penalty",
            "recency_penalty",
            "novelty_bonus",
            "information_gain_bonus",
            "coverage_bonus",
            "remediation_adjustment",
            "final_selection_score",
            "selection_rank",
            "tie_breaking_policy",
        ):
            assert field in row
        assert row["adaptive_selection_score"]["authority"] == "TrainingAssistant"
        assert row["adaptive_selection_score"][
            "dataset_expansion_authority"
        ] == "NONE"


def test_adaptive_elite_selector_tie_break_prefers_lower_exposure(tmp_path):
    tasks_directory = tmp_path / "training"
    recent, fresh = _task_names(2)
    _write_elite_task(tasks_directory, recent, ["shared_tie_probe"])
    _write_elite_task(tasks_directory, fresh, ["shared_tie_probe"])

    assistant = _assistant(tmp_path)
    assistant.selection_memory = {
        **assistant.selection_memory,
        "tasks": {
            recent: {
                "task_id": recent,
                "times_selected": 1,
                "recent_selection_count": 1,
            },
            fresh: {
                "task_id": fresh,
                "times_selected": 0,
                "recent_selection_count": 0,
            },
        },
    }

    selected = assistant.select_batch(
        [recent, fresh],
        concept_counts={"shared_tie_probe": 5},
        task_directory=tasks_directory,
    )

    assert selected["selected_task_files"] == [fresh]
