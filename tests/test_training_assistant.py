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


def test_training_assistant_selects_one_elite_and_two_normal_tasks(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    for task_file, metadata in {
        "elite_cognitive_task_01.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["topological_reasoning"],
            "deficiency_targets": ["candidate_generation_gap"],
        },
        "elite_cognitive_task_02.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["color_transformation"],
            "deficiency_targets": ["color_pressure"],
        },
        "normal_001.json": {"target_concepts": ["spatial_reasoning"]},
        "normal_002.json": {"target_concepts": ["path_finding"]},
        "normal_003.json": {"target_concepts": ["object_counting"]},
    }.items():
        (tasks_directory / task_file).write_text(
            json.dumps({"train": [], "test": [], "nexryn_metadata": metadata}),
            encoding="utf-8",
        )

    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        batch_size=3,
        selection_mode="curriculum",
    )
    selected = assistant.select_batch(
        [
            "elite_cognitive_task_01.json",
            "elite_cognitive_task_02.json",
            "normal_001.json",
            "normal_002.json",
            "normal_003.json",
        ],
        concept_counts={"topological_reasoning": 1},
        task_directory=tasks_directory,
        core_knowledge=[{"concept": "replace_color"}],
    )

    assert selected["selected_task_count"] == 3
    assert len(selected["selected_elite_task_files"]) == 1
    assert selected["selected_elite_task_files"] == [
        "elite_cognitive_task_01.json",
    ]
    assert len([
        task_file
        for task_file in selected["selected_task_files"]
        if not task_file.startswith("elite_cognitive_task_")
    ]) == 2
    assert selected["elite_selection_report"]["policy"] == (
        "exactly_one_elite_task_per_cycle"
    )


def test_training_assistant_uses_survival_store_for_elite_reappearance(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    survival_path = tmp_path / "operational_capability_survival.json"
    survival_path.write_text(
        json.dumps({
            "operational_capability:topology:preserve_topology:topological_reasoning": {
                "capability_id": "operational_capability:topology:preserve_topology:topological_reasoning",
                "operation": "preserve_topology",
                "domain": "Topology",
                "semantic_intent": "topological_reasoning",
                "lifecycle_state": "INCUBATING_VALIDATION_GAP",
                "next_required_evidence": "independent_task_reappearance",
                "best_accuracy": 0.84,
                "distinct_task_count": 1,
                "arena_simulated_count": 1,
                "validation_attempts": 1,
            }
        }),
        encoding="utf-8",
    )
    for task_file, metadata in {
        "elite_cognitive_task_01.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["color_transformation"],
            "deficiency_targets": ["color_pressure"],
        },
        "elite_cognitive_task_02.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["topological_reasoning", "identity_preservation"],
            "deficiency_targets": ["validation_gap"],
        },
        "normal_001.json": {"target_concepts": ["spatial_reasoning"]},
        "normal_002.json": {"target_concepts": ["path_finding"]},
    }.items():
        (tasks_directory / task_file).write_text(
            json.dumps({"train": [], "test": [], "nexryn_metadata": metadata}),
            encoding="utf-8",
        )

    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        survival_store_path=survival_path,
        batch_size=3,
        selection_mode="curriculum",
    )

    selected = assistant.select_batch(
        [
            "elite_cognitive_task_01.json",
            "elite_cognitive_task_02.json",
            "normal_001.json",
            "normal_002.json",
        ],
        concept_counts={
            "color_transformation": 20,
            "topological_reasoning": 20,
            "identity_preservation": 20,
        },
        task_directory=tasks_directory,
    )

    assert selected["selected_elite_task_files"] == [
        "elite_cognitive_task_02.json",
    ]
    assert "survival_store_independent_reappearance_probe" in (
        selected["elite_selection_report"]["priority_reasons"]
    )
    assert selected["elite_selection_report"][
        "survival_reappearance_matches"
    ][0]["operation"] == "preserve_topology"


def test_training_assistant_prioritizes_elite_domain_citizenship_gaps(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    survival_path = tmp_path / "operational_capability_survival.json"
    survival_path.write_text(
        json.dumps({
            "operational_capability:color:replace_color:color_mapping": {
                "capability_id": "operational_capability:color:replace_color:color_mapping",
                "operation": "replace_color",
                "domain": "Color",
                "lifecycle_state": "OPERATIONAL_CITIZEN",
            },
            "operational_capability:spatial:translate:spatial_reasoning": {
                "capability_id": "operational_capability:spatial:translate:spatial_reasoning",
                "operation": "translate",
                "domain": "Spatial",
                "semantic_intent": "spatial_reasoning",
                "lifecycle_state": "INCUBATING_VALIDATION_GAP",
                "next_required_evidence": "repeatable_validation_across_independent_task",
                "best_accuracy": 0.88,
                "distinct_task_count": 2,
                "arena_simulated_count": 2,
                "validation_attempts": 2,
            },
        }),
        encoding="utf-8",
    )
    for task_file, metadata in {
        "elite_cognitive_task_01.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["color_transformation"],
            "deficiency_targets": ["color_pressure"],
        },
        "elite_cognitive_task_02.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["spatial_reasoning", "translation"],
            "deficiency_targets": ["domain_operationalization_gap"],
        },
        "normal_001.json": {"target_concepts": ["identity_preservation"]},
        "normal_002.json": {"target_concepts": ["path_finding"]},
    }.items():
        (tasks_directory / task_file).write_text(
            json.dumps({"train": [], "test": [], "nexryn_metadata": metadata}),
            encoding="utf-8",
        )

    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        survival_store_path=survival_path,
        batch_size=3,
        selection_mode="curriculum",
    )

    selected = assistant.select_batch(
        [
            "elite_cognitive_task_01.json",
            "elite_cognitive_task_02.json",
            "normal_001.json",
            "normal_002.json",
        ],
        concept_counts={
            "color_transformation": 20,
            "spatial_reasoning": 20,
            "translation": 20,
        },
        task_directory=tasks_directory,
    )

    assert selected["selected_elite_task_files"] == [
        "elite_cognitive_task_02.json",
    ]
    assert "domain_citizenship_gap_probe" in (
        selected["elite_selection_report"]["priority_reasons"]
    )
    assert selected["elite_selection_report"]["domain_citizenship_matches"][0][
        "domain"
    ] == "Spatial"


def test_training_assistant_targets_declining_capability_recovery(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    survival_path = tmp_path / "operational_capability_survival.json"
    survival_path.write_text(
        json.dumps({
            "operational_capability:spatial:preserve_grid:object_identity_preservation": {
                "capability_id": "operational_capability:spatial:preserve_grid:object_identity_preservation",
                "operation": "preserve_grid",
                "domain": "Spatial",
                "semantic_intent": "object_identity_preservation",
                "lifecycle_state": "SURVIVING_CAPABILITY",
                "next_required_evidence": "stability_recovery_evidence",
                "best_accuracy": 0.9722,
                "average_accuracy": 0.7763,
                "improvement_trend": "DECLINING",
                "distinct_task_count": 6,
                "arena_simulated_count": 6,
                "validation_attempts": 6,
            }
        }),
        encoding="utf-8",
    )
    for task_file, metadata in {
        "elite_cognitive_task_01.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["color_transformation"],
        },
        "elite_cognitive_task_02.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["spatial_reasoning", "identity_preservation"],
            "required_operational_capabilities": ["preserve_grid"],
        },
        "normal_001.json": {"target_concepts": ["identity_preservation"]},
        "normal_002.json": {"target_concepts": ["path_finding"]},
    }.items():
        (tasks_directory / task_file).write_text(
            json.dumps({"train": [], "test": [], "nexryn_metadata": metadata}),
            encoding="utf-8",
        )

    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        survival_store_path=survival_path,
        batch_size=3,
        selection_mode="curriculum",
    )

    selected = assistant.select_batch(
        [
            "elite_cognitive_task_01.json",
            "elite_cognitive_task_02.json",
            "normal_001.json",
            "normal_002.json",
        ],
        concept_counts={
            "color_transformation": 20,
            "spatial_reasoning": 20,
            "identity_preservation": 20,
        },
        task_directory=tasks_directory,
    )

    assert selected["selected_elite_task_files"] == [
        "elite_cognitive_task_02.json",
    ]
    assert selected["elite_selection_report"][
        "survival_reappearance_matches"
    ][0]["next_required_evidence"] == "stability_recovery_evidence"


def test_training_assistant_targets_crystallization_ready_capabilities(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    survival_path = tmp_path / "operational_capability_survival.json"
    survival_path.write_text(
        json.dumps({
            "operational_capability:spatial:preserve_grid:object_identity_preservation": {
                "capability_id": "operational_capability:spatial:preserve_grid:object_identity_preservation",
                "operation": "preserve_grid",
                "domain": "Spatial",
                "semantic_intent": "object_identity_preservation",
                "lifecycle_state": "INCUBATING_VALIDATION_GAP",
                "next_required_evidence": "repeatable_validation_across_independent_task",
                "best_accuracy": 0.9722,
                "average_accuracy": 0.8841,
                "improvement_trend": "STABLE",
                "distinct_task_count": 4,
                "arena_simulated_count": 4,
                "arena_quality_count": 4,
                "validation_attempts": 4,
            }
        }),
        encoding="utf-8",
    )
    for task_file, metadata in {
        "elite_cognitive_task_01.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["color_transformation"],
        },
        "elite_cognitive_task_02.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["spatial_reasoning", "identity_preservation"],
            "required_operational_capabilities": ["preserve_grid"],
        },
        "normal_001.json": {"target_concepts": ["identity_preservation"]},
        "normal_002.json": {"target_concepts": ["path_finding"]},
    }.items():
        (tasks_directory / task_file).write_text(
            json.dumps({"train": [], "test": [], "nexryn_metadata": metadata}),
            encoding="utf-8",
        )

    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        survival_store_path=survival_path,
        batch_size=3,
        selection_mode="curriculum",
    )

    selected = assistant.select_batch(
        [
            "elite_cognitive_task_01.json",
            "elite_cognitive_task_02.json",
            "normal_001.json",
            "normal_002.json",
        ],
        concept_counts={
            "color_transformation": 20,
            "spatial_reasoning": 20,
            "identity_preservation": 20,
        },
        task_directory=tasks_directory,
    )

    assert selected["selected_elite_task_files"] == [
        "elite_cognitive_task_02.json",
    ]
    assert "capability_crystallization_probe" in (
        selected["elite_selection_report"]["priority_reasons"]
    )
    match = selected["elite_selection_report"][
        "survival_reappearance_matches"
    ][0]
    assert match["operation"] == "preserve_grid"
    assert match["crystallization_candidate"] is True


def test_training_assistant_enters_population_evolution_sprint(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    survival_path = tmp_path / "operational_capability_survival.json"
    survival_path.write_text(
        json.dumps({
            "operational_capability:color:replace_color:color_mapping": {
                "capability_id": "operational_capability:color:replace_color:color_mapping",
                "operation": "replace_color",
                "domain": "Color",
                "lifecycle_state": "OPERATIONAL_CITIZEN",
                "operational_experience_count": 19,
            },
            "operational_capability:growth:duplicate_object:growth": {
                "capability_id": "operational_capability:growth:duplicate_object:growth",
                "operation": "duplicate_object",
                "domain": "Growth",
                "lifecycle_state": "OPERATIONAL_CITIZEN",
                "operational_experience_count": 7,
            },
            "operational_capability:spatial:translate:spatial_reasoning": {
                "capability_id": "operational_capability:spatial:translate:spatial_reasoning",
                "operation": "translate",
                "domain": "Spatial",
                "semantic_intent": "spatial_reasoning",
                "lifecycle_state": "SURVIVING_CAPABILITY",
                "next_required_evidence": "repeatable_validation_across_independent_task",
                "best_accuracy": 0.9444,
                "average_accuracy": 0.7647,
                "improvement_trend": "STABLE",
                "distinct_task_count": 15,
                "arena_simulated_count": 15,
                "arena_quality_count": 15,
                "validation_attempts": 10,
            },
        }),
        encoding="utf-8",
    )
    for task_file, metadata in {
        "elite_cognitive_task_01.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["color_transformation"],
            "required_operational_capabilities": ["replace_color"],
        },
        "elite_cognitive_task_02.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["spatial_reasoning", "translation"],
            "required_operational_capabilities": ["translate"],
        },
        "normal_001.json": {"target_concepts": ["identity_preservation"]},
        "normal_002.json": {"target_concepts": ["path_finding"]},
    }.items():
        (tasks_directory / task_file).write_text(
            json.dumps({"train": [], "test": [], "nexryn_metadata": metadata}),
            encoding="utf-8",
        )

    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        survival_store_path=survival_path,
        batch_size=3,
        selection_mode="curriculum",
    )

    selected = assistant.select_batch(
        [
            "elite_cognitive_task_01.json",
            "elite_cognitive_task_02.json",
            "normal_001.json",
            "normal_002.json",
        ],
        concept_counts={
            "color_transformation": 20,
            "spatial_reasoning": 20,
            "translation": 20,
        },
        task_directory=tasks_directory,
    )

    report = selected["elite_selection_report"]
    assert selected["selected_elite_task_files"] == [
        "elite_cognitive_task_02.json",
    ]
    assert report["capability_population_evolution_policy"]["policy_state"] == (
        "SEVERE_POPULATION_EVOLUTION_SPRINT"
    )
    assert report["capability_population_evolution_policy"][
        "operational_experience_count"
    ] == 41
    assert report["capability_population_evolution_policy"][
        "governance_action"
    ] == "graduation_sprint_required"
    assert "translate" in report["capability_population_evolution_policy"][
        "graduation_target_operations"
    ]
    assert "translate" in report["capability_population_evolution_policy"][
        "target_operations"
    ]
    assert "capability_population_evolution_sprint" in report[
        "priority_reasons"
    ]
    assert "capability_graduation_sprint_required" in report[
        "priority_reasons"
    ]
    assert report["survival_reappearance_matches"][0][
        "population_evolution_target"
    ] is True


def test_training_assistant_targets_exact_evidence_gap_not_generic_reappearance(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    survival_path = tmp_path / "operational_capability_survival.json"
    survival_path.write_text(
        json.dumps({
            "operational_capability:spatial:translate:spatial_reasoning": {
                "capability_id": "operational_capability:spatial:translate:spatial_reasoning",
                "operation": "translate",
                "domain": "Spatial",
                "semantic_intent": "spatial_reasoning",
                "lifecycle_state": "SURVIVING_CAPABILITY",
                "next_required_evidence": "exact_or_governed_validation_success",
                "best_accuracy": 0.9444,
                "average_accuracy": 0.7668,
                "improvement_trend": "DECLINING_MINOR",
                "distinct_task_count": 16,
                "arena_simulated_count": 16,
                "arena_quality_count": 15,
                "validation_attempts": 10,
            },
            "operational_capability:color:replace_color:color_mapping": {
                "capability_id": "operational_capability:color:replace_color:color_mapping",
                "operation": "replace_color",
                "domain": "Color",
                "lifecycle_state": "OPERATIONAL_CITIZEN",
                "operational_experience_count": 19,
            },
        }),
        encoding="utf-8",
    )
    for task_file, metadata in {
        "elite_cognitive_task_01.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["spatial_reasoning", "translation"],
            "required_operational_capabilities": ["translate"],
        },
        "elite_cognitive_task_02.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["spatial_reasoning", "translation"],
            "required_operational_capabilities": ["translate"],
            "required_evidence": ["exact_or_governed_validation_success"],
            "task_properties": [
                "unambiguous_directional_translation_ground_truth",
                "exact_validation",
            ],
            "transformation_contract": "directional_translation",
            "primary_operation": "translate",
        },
        "normal_001.json": {"target_concepts": ["identity_preservation"]},
        "normal_002.json": {"target_concepts": ["path_finding"]},
    }.items():
        (tasks_directory / task_file).write_text(
            json.dumps({"train": [], "test": [], "nexryn_metadata": metadata}),
            encoding="utf-8",
        )

    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        survival_store_path=survival_path,
        batch_size=3,
        selection_mode="curriculum",
    )

    selected = assistant.select_batch(
        [
            "elite_cognitive_task_01.json",
            "elite_cognitive_task_02.json",
            "normal_001.json",
            "normal_002.json",
        ],
        concept_counts={
            "spatial_reasoning": 20,
            "translation": 20,
        },
        task_directory=tasks_directory,
    )

    report = selected["elite_selection_report"]
    assert selected["selected_elite_task_files"] == [
        "elite_cognitive_task_02.json",
    ]
    assert "evidence_gap_aligned_maturation_probe" in report[
        "priority_reasons"
    ]
    assert "maturation_no_progress_repair_probe" in report[
        "priority_reasons"
    ]
    match = report["survival_reappearance_matches"][0]
    assert match["operation"] == "translate"
    assert match["next_required_evidence"] == "exact_or_governed_validation_success"
    assert match["required_task_property"] == (
        "unambiguous_directional_translation_ground_truth"
    )
    assert match["evidence_gap_aligned"] is True
    assert match["maturation_no_progress"] is True
