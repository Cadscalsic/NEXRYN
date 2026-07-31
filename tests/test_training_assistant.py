import json

from runtime.learning.training_assistant import TrainingAssistant


def task_files(count=12):
    return [
        f"task_{sequence:03d}.json"
        for sequence in range(1, count + 1)
    ]


def test_training_assistant_consumes_persisted_evidence_plan_and_selects_validation_task(
    tmp_path,
):
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        selection_mode="curriculum",
    )

    selected = assistant.select_batch(
        task_files(),
        pending_evidence_acquisition_plans=[
            {
                "plan_id": "evidence_plan_run_20260730_074151_a84f290c",
                "required_evidence_category": "CROSS_SOURCE_CONSENSUS",
                "required_evidence": "cross_source_consensus_evidence",
                "required_validation_task": (
                    "select_cross_source_tie_break_validation_task"
                ),
                "tie_break_strategy": "cross_source_consensus",
                "target_candidate": "semantic_program:replace_color",
                "target_operation": "replace_color",
                "expected_tie_break_impact": "HIGH",
                "governed_reentry_action": (
                    "reenter_arena_after_required_evidence_without_truth_grant"
                ),
                "authority": {
                    "truth": "NONE",
                    "trust": "NONE",
                    "graduation": "NONE",
                    "execution": "NONE",
                },
            }
        ],
    )

    alignment = selected["training_economy_alignment_report"]
    assert alignment["pending_evidence_plan_count"] == 1
    assert alignment["training_assistant_plan_available"] is True
    assert alignment["evidence_acquisition_plan_forwarded"] is True
    assert alignment["evidence_acquisition_plan_consumed"] is True
    assert alignment["training_assistant_consumed_plan"] is True
    assert alignment["consumption_state"] == "MATCHING_COMPLETED"
    assert alignment["curriculum_search_state"] == "COMPLETED"
    assert alignment["matching_validation_tasks"] > 0
    assert alignment["best_matching_task"] != "Not Available"
    assert alignment["evidence_acquisition_selected_task"] != "Not Available"
    assert alignment["selection_authority"] == "TRAINING_ASSISTANT"
    assert alignment["selection_state"] == "WAITING_EXECUTION"
    assert alignment["waiting_execution"] is True
    assert alignment["generation_invoked"] is False
    assert alignment["decision_orchestration_state"] == (
        "VALIDATION_TASK_SELECTED_AWAITING_EXECUTION"
    )


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


def test_training_assistant_selects_elite_only_for_v1_curriculum(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    tasks = {}
    for sequence in range(1, 5):
        task_file = f"elite_cognitive_task_{sequence:02d}.json"
        tasks[task_file] = {
            "nexryn_metadata": {
                "curriculum": "nexryn_elite_training_curriculum_v1",
                "operationalization_phase_curriculum": True,
                "elite_cognitive_task": True,
                "target_concepts": ["translation", "preserve_topology"],
                "target_domains": ["Spatial", "Topology", "Identity"],
                "deficiency_targets": ["domain_operationalization_gaps"],
                "required_operational_capabilities": [
                    "capability_composition",
                ],
            },
        }
    tasks["task_001.json"] = {
        "nexryn_metadata": {
            "target_concepts": ["old_task"],
        },
    }
    for task_file, payload in tasks.items():
        (tasks_directory / task_file).write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        batch_size=3,
        selection_mode="curriculum",
    )
    selected = assistant.select_batch(
        list(tasks),
        task_directory=tasks_directory,
    )

    assert selected["elite_only_policy_active"] is True
    assert selected["selected_task_count"] == 3
    assert selected["selected_task_files"] == selected["selected_elite_task_files"]
    assert "task_001.json" not in selected["selected_task_files"]
    assert selected["elite_selection_report"]["policy"] == (
        "elite_tasks_only_operationalization_phase"
    )


def test_training_assistant_aligns_elite_selection_with_operational_economy(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    tasks = {
        "elite_cognitive_task_01.json": ["color_noise"],
        "elite_cognitive_task_02.json": ["growth_probe"],
        "elite_cognitive_task_03.json": ["translate", "preserve_topology"],
        "elite_cognitive_task_04.json": ["shape_probe"],
    }
    for task_file, concepts in tasks.items():
        (tasks_directory / task_file).write_text(
            json.dumps({
                "nexryn_metadata": {
                    "curriculum": "nexryn_elite_training_curriculum_v1",
                    "operationalization_phase_curriculum": True,
                    "elite_cognitive_task": True,
                    "target_concepts": concepts,
                    "target_domains": ["Spatial", "Topology", "Color"],
                    "deficiency_targets": ["validation_gap"],
                    "required_operational_capabilities": concepts,
                    "required_evidence": (
                        ["exact_or_governed_validation_success"]
                        if "translate" in concepts else []
                    ),
                    "task_properties": (
                        ["unambiguous_directional_translation_ground_truth"]
                        if "translate" in concepts else []
                    ),
                    "composite_capabilities": [
                        "Topology Preserving Translation"
                    ] if "translate" in concepts else [],
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
        task_directory=tasks_directory,
        operational_economy_report={
            "operational_economy_health": 0.55,
            "capability_economy_crisis_state": "CAPABILITY_ECONOMY_PRESSURE",
            "operational_economy_bottleneck": "compiled_programs->validated_programs",
            "capability_investment_priorities": [
                {"operation": "translate", "capability_investment_score": 0.9},
                {
                    "operation": "preserve_topology",
                    "capability_investment_score": 0.85,
                },
            ],
            "operational_capability_clusters": [
                {
                    "cluster_name": "Topology Preserving Translation",
                    "member_capabilities": [
                        "translate",
                        "preserve_topology",
                        "preserve_colors",
                    ],
                    "missing_capabilities": [],
                    "cluster_readiness": 1.0,
                    "required_grounding": [
                        {
                            "operation": "translate",
                            "domain": "Spatial",
                            "required_evidence": (
                                "exact_or_governed_validation_success"
                            ),
                            "required_task_property": (
                                "unambiguous_directional_translation_ground_truth"
                            ),
                            "cluster_name": "Topology Preserving Translation",
                        },
                        {
                            "operation": "preserve_topology",
                            "domain": "Topology",
                            "required_evidence": (
                                "exact_or_governed_validation_success"
                            ),
                            "required_task_property": (
                                "topology_preserving_transformation_ground_truth"
                            ),
                            "cluster_name": "Topology Preserving Translation",
                        },
                    ],
                }
            ],
            "operational_economy_roadmap": [
                {
                    "priority": "knowledge_crystallization",
                    "target": "compiled_programs->validated_programs",
                    "action": "prioritize_validation_and_graduation_evidence",
                }
            ],
        },
    )

    assert selected["selected_task_files"][0] == "elite_cognitive_task_03.json"
    assert selected["training_economy_alignment_report"]["alignment_state"] == (
        "ECONOMY_ALIGNED_TRAINING"
    )
    assert selected["training_economy_alignment_report"][
        "training_economy_alignment_score"
    ] > 0
    assert "capability_economy_investment_alignment" in selected[
        "elite_selection_report"
    ]["priority_reasons"]
    assert selected["training_diversity_report"][
        "training_economy_alignment_state"
    ] == "ECONOMY_ALIGNED_TRAINING"
    assert selected["training_economy_alignment_report"][
        "grounding_economy_alignment"
    ] == "GROUNDING_ECONOMY_ALIGNED"
    assert selected["training_economy_alignment_report"][
        "selected_grounding_aligned_tasks"
    ] == ["elite_cognitive_task_03.json"]
    assert "unambiguous_directional_translation_ground_truth" in selected[
        "training_economy_alignment_report"
    ]["matched_grounding_targets"]
    assert selected["training_economy_alignment_report"][
        "grounding_alignment_trace"
    ][0]["evidence_collection_attempted"] is True
    assert selected["training_diversity_report"][
        "grounding_economy_alignment"
    ] == "GROUNDING_ECONOMY_ALIGNED"


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


def test_training_assistant_prioritizes_governed_validation_evidence_signal(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    for task_file, metadata in {
        "elite_cognitive_task_01.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["translation"],
            "required_operational_capabilities": ["translate"],
        },
        "elite_cognitive_task_02.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["translation"],
            "required_evidence": ["exact_or_governed_validation_success"],
            "task_properties": ["exact_or_governed_validation_ground_truth"],
        },
        "normal_001.json": {"target_concepts": ["identity_preservation"]},
        "normal_002.json": {"target_concepts": ["path_finding"]},
    }.items():
        (tasks_directory / task_file).write_text(
            json.dumps({"train": [], "test": [], "nexryn_metadata": metadata}),
            encoding="utf-8",
        )
    economy_report = {
        "governed_validation_bottleneck_state": (
            "GOVERNED_VALIDATION_INFRASTRUCTURE_BOTTLENECK"
        ),
        "governed_validation_action": (
            "select_governed_validation_evidence_tasks"
        ),
        "governed_validation_required_evidence": (
            "exact_or_governed_validation_success"
        ),
    }
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
        ],
        task_directory=tasks_directory,
        operational_economy_report=economy_report,
    )

    assert selected["selected_elite_task_files"] == [
        "elite_cognitive_task_02.json",
    ]
    alignment = selected["training_economy_alignment_report"]
    assert alignment["governed_validation_bottleneck_state"] == (
        "GOVERNED_VALIDATION_INFRASTRUCTURE_BOTTLENECK"
    )
    report = selected["elite_selection_report"]
    assert "governed_validation_evidence_alignment" in report[
        "priority_reasons"
    ]
    assert any(
        match["match_type"] == "governed_validation_required_evidence"
        for row in report["elite_task_priorities"]
        for match in row.get("training_economy_matches", [])
        if row["task_file"] == "elite_cognitive_task_02.json"
    )


def test_training_assistant_uses_validation_academy_opportunity_matching(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    survival_path = tmp_path / "operational_capability_survival.json"
    academy_path = tmp_path / "elite_validation_academy_v1.json"
    survival_path.write_text(
        json.dumps({
            "operational_capability:growth:duplicate_object:growth": {
                "capability_id": "operational_capability:growth:duplicate_object:growth",
                "operation": "duplicate_object",
                "domain": "Growth",
                "lifecycle_state": "SURVIVING_CAPABILITY",
                "next_required_evidence": "exact_or_governed_validation_success",
                "best_accuracy": 1.0,
                "average_accuracy": 0.56,
                "distinct_task_count": 35,
                "arena_simulated_count": 61,
                "arena_quality_count": 35,
                "validation_attempts": 10,
            },
        }),
        encoding="utf-8",
    )
    academy_path.write_text(
        json.dumps({
            "academy": "nexryn_elite_validation_academy_v1",
            "tasks": [
                {
                    "task_id": "elite_validation_task_27",
                    "elite_group": "Capability Graduation Tasks",
                    "target_capability": "duplicate_object",
                    "target_cluster": "Symbolic Object Replication",
                    "target_domain": "Growth",
                    "required_task_property": (
                        "paired_symbolic_object_replication_ground_truth"
                    ),
                    "required_validation_evidence": (
                        "exact_or_governed_validation_success"
                    ),
                    "promotion_weight": 0.98,
                }
            ],
        }),
        encoding="utf-8",
    )
    for task_file, metadata in {
        "elite_cognitive_task_01.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["growth"],
            "required_operational_capabilities": ["duplicate_object"],
        },
        "elite_cognitive_task_02.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["growth", "symbolic_object_replication"],
            "required_operational_capabilities": ["duplicate_object"],
            "required_task_property": (
                "paired_symbolic_object_replication_ground_truth"
            ),
            "required_evidence": ["exact_or_governed_validation_success"],
            "target_cluster": "Symbolic Object Replication",
            "target_capability": "duplicate_object",
        },
        "normal_001.json": {"target_concepts": ["identity_preservation"]},
    }.items():
        (tasks_directory / task_file).write_text(
            json.dumps({"train": [], "test": [], "nexryn_metadata": metadata}),
            encoding="utf-8",
        )
    economy_report = {
        "governed_validation_bottleneck_state": (
            "GOVERNED_VALIDATION_INFRASTRUCTURE_BOTTLENECK"
        ),
        "governed_validation_required_evidence": (
            "exact_or_governed_validation_success"
        ),
        "grounding_requirement_rows": [
            {
                "operation": "duplicate_object",
                "required_task_property": (
                    "paired_symbolic_object_replication_ground_truth"
                ),
            }
        ],
    }
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        survival_store_path=survival_path,
        validation_academy_path=academy_path,
        batch_size=2,
        selection_mode="curriculum",
    )

    selected = assistant.select_batch(
        [
            "elite_cognitive_task_01.json",
            "elite_cognitive_task_02.json",
            "normal_001.json",
        ],
        task_directory=tasks_directory,
        operational_economy_report=economy_report,
    )

    assert selected["selected_elite_task_files"] == [
        "elite_cognitive_task_02.json",
    ]
    report = selected["elite_selection_report"]
    assert "elite_validation_task_selection_intelligence" in report[
        "priority_reasons"
    ]
    assert "capability_directed_validation" in report["priority_reasons"]
    match = report["validation_academy_matches"][0]
    assert match["academy_task_id"] == "elite_validation_task_27"
    assert match["target_capability"] == "duplicate_object"
    assert match["required_task_property"] == (
        "paired_symbolic_object_replication_ground_truth"
    )
    alignment = selected["training_economy_alignment_report"]
    assert alignment["validation_academy_alignment"] == (
        "VALIDATION_ACADEMY_ALIGNED"
    )
    assert alignment["validation_academy_alignment_trace"][0][
        "academy_task_id"
    ] == "elite_validation_task_27"


def test_training_assistant_searches_advanced_validation_academy_before_generation(
    tmp_path,
):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    academy_path = tmp_path / "elite_validation_academy_v1.json"
    academy_path.write_text(
        json.dumps({
            "academy": "nexryn_elite_validation_academy_v1",
            "tasks": [
                {
                    "task_id": "elite_validation_task_31",
                    "elite_group": "Advanced Multi-Concept Validation Tasks",
                    "target_capability": "localized_replace_color",
                    "target_cluster": "Color Transformation Capability",
                    "target_domain": "Color",
                    "required_task_property": (
                        "localized_color_remap_cross_source_consensus"
                    ),
                    "required_validation_evidence": (
                        "cross_source_consensus_evidence"
                    ),
                    "promotion_weight": 0.94,
                }
            ],
        }),
        encoding="utf-8",
    )
    for task_file, metadata in {
        "elite_cognitive_task_01.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["general_validation"],
            "required_evidence": ["independent_validation_evidence"],
        },
        "elite_cognitive_task_02.json": {
            "elite_cognitive_task": True,
            "target_concepts": [
                "replace_color",
                "localized_replace_color",
                "cross_source_consensus",
            ],
            "required_evidence": ["cross_source_consensus_evidence"],
            "task_properties": [
                "select_cross_source_tie_break_validation_task",
                "localized_color_remap_cross_source_consensus",
            ],
            "target_capability": "localized_replace_color",
            "target_cluster": "Color Transformation Capability",
        },
    }.items():
        (tasks_directory / task_file).write_text(
            json.dumps({"train": [], "test": [], "nexryn_metadata": metadata}),
            encoding="utf-8",
        )
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        validation_academy_path=academy_path,
        evidence_generation_path=tmp_path / "generated_curriculum",
        batch_size=1,
        selection_mode="curriculum",
    )

    selected = assistant.select_batch(
        ["elite_cognitive_task_01.json", "elite_cognitive_task_02.json"],
        task_directory=tasks_directory,
        operational_economy_report={
            "evidence_acquisition_state": "EVIDENCE_ACQUISITION_PLAN_READY",
            "evidence_acquisition_required_evidence": (
                "cross_source_consensus_evidence"
            ),
            "evidence_acquisition_required_category": "CROSS_SOURCE_CONSENSUS",
            "evidence_acquisition_validation_task": (
                "select_cross_source_tie_break_validation_task"
            ),
            "evidence_acquisition_tie_break_strategy": "cross_source_consensus",
            "evidence_acquisition_target_operation": "replace_color",
        },
    )

    assert selected["selected_task_files"] == ["elite_cognitive_task_02.json"]
    alignment = selected["training_economy_alignment_report"]
    assert alignment["decision_orchestration_state"] == (
        "PLAN_CONSUMED_AND_TASK_SCHEDULED"
    )
    assert alignment["validation_academy_alignment"] == (
        "VALIDATION_ACADEMY_ALIGNED"
    )
    assert alignment["validation_academy_alignment_trace"][0][
        "academy_task_id"
    ] == "elite_validation_task_31"
    generation = selected["evidence_generation_report"]
    assert generation["generation_required"] is False
    assert generation["existing_tasks_found"] is True
    assert generation["generated_tasks"] == 0


def test_training_assistant_uses_evidence_responsibility_for_task_selection(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    for task_file, metadata in {
        "elite_cognitive_task_01.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["general_validation"],
            "required_evidence": ["independent_validation_evidence"],
        },
        "elite_cognitive_task_02.json": {
            "elite_cognitive_task": True,
            "target_concepts": [
                "object_grounding",
                "validation_evidence_grounding",
            ],
            "required_evidence": ["grounded_target_object_evidence"],
            "task_properties": ["select_object_grounded_validation_task"],
            "responsibility_targets": ["OBJECT_GROUNDING_LAYER"],
        },
    }.items():
        (tasks_directory / task_file).write_text(
            json.dumps({"train": [], "test": [], "nexryn_metadata": metadata}),
            encoding="utf-8",
        )
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        batch_size=1,
        selection_mode="curriculum",
    )

    selected = assistant.select_batch(
        ["elite_cognitive_task_01.json", "elite_cognitive_task_02.json"],
        task_directory=tasks_directory,
        operational_economy_report={
            "knowledge_operationalization_choke_point": (
                "validation_evidence_grounding"
            ),
            "knowledge_operationalization_choke_action": (
                "select_object_grounded_validation_task"
            ),
            "knowledge_operationalization_evidence_responsibility": (
                "OBJECT_GROUNDING_LAYER"
            ),
            "knowledge_operationalization_required_evidence": (
                "grounded_target_object_evidence"
            ),
        },
    )

    assert selected["selected_task_files"] == ["elite_cognitive_task_02.json"]
    alignment = selected["training_economy_alignment_report"]
    assert alignment["evidence_driven_task_selection_state"] == (
        "ALIGNED_TASK_SELECTED"
    )
    assert alignment["evidence_remediation_attempted"] is True
    assert alignment["evidence_remediation_task"] == "elite_cognitive_task_02.json"
    assert alignment["evidence_remediation_deficit"] == (
        "grounded_target_object_evidence"
    )
    assert alignment["evidence_remediation_responsible_area"] == (
        "OBJECT_GROUNDING_LAYER"
    )
    assert alignment["remediation_outcome"] == "REMEDIATION_ATTEMPT_QUEUED"
    report = selected["elite_selection_report"]
    assert "evidence_responsibility_alignment" in report["priority_reasons"]
    assert any(
        match["match_type"] == "evidence_responsibility"
        and match["target"] == "object_grounding_layer"
        for row in report["elite_task_priorities"]
        for match in row.get("training_economy_matches", [])
        if row["task_file"] == "elite_cognitive_task_02.json"
    )


def test_training_assistant_consumes_evidence_acquisition_plan(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    for task_file, metadata in {
        "elite_cognitive_task_01.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["general_validation"],
            "required_evidence": ["independent_validation_evidence"],
        },
        "elite_cognitive_task_02.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["replace_color", "source_consensus"],
            "required_evidence": ["cross_source_consensus_evidence"],
            "task_properties": ["select_cross_source_tie_break_validation_task"],
        },
    }.items():
        (tasks_directory / task_file).write_text(
            json.dumps({"train": [], "test": [], "nexryn_metadata": metadata}),
            encoding="utf-8",
        )
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        batch_size=1,
        selection_mode="curriculum",
    )

    selected = assistant.select_batch(
        ["elite_cognitive_task_01.json", "elite_cognitive_task_02.json"],
        task_directory=tasks_directory,
        operational_economy_report={
            "evidence_acquisition_state": "EVIDENCE_ACQUISITION_PLAN_READY",
            "evidence_acquisition_required_evidence": (
                "cross_source_consensus_evidence"
            ),
            "evidence_acquisition_required_category": "CROSS_SOURCE_CONSENSUS",
            "evidence_acquisition_validation_task": (
                "select_cross_source_tie_break_validation_task"
            ),
            "evidence_acquisition_tie_break_strategy": "cross_source_consensus",
            "evidence_acquisition_target_operation": "replace_color",
            "evidence_acquisition_expected_tie_break_impact": "HIGH",
        },
    )

    assert selected["selected_task_files"] == ["elite_cognitive_task_02.json"]
    alignment = selected["training_economy_alignment_report"]
    assert alignment["decision_orchestration_state"] == (
        "PLAN_CONSUMED_AND_TASK_SCHEDULED"
    )
    assert alignment["evidence_acquisition_plan_forwarded"] is True
    assert alignment["evidence_acquisition_plan_consumed"] is True
    assert alignment["evidence_acquisition_task_scheduled"] is True
    assert alignment["evidence_acquisition_selected_task"] == (
        "elite_cognitive_task_02.json"
    )
    assert alignment["evidence_acquisition_validation_task"] == (
        "select_cross_source_tie_break_validation_task"
    )
    assert alignment["evidence_acquisition_alignment_trace"][0][
        "tie_break_strategy"
    ] == "cross_source_consensus"


def test_training_assistant_generates_validation_task_when_plan_has_no_match(
    tmp_path,
):
    tasks_directory = tmp_path / "training"
    generated_directory = tmp_path / "generated_curriculum"
    tasks_directory.mkdir()
    (tasks_directory / "task_general.json").write_text(
        json.dumps({
            "train": [],
            "test": [],
            "nexryn_metadata": {
                "target_concepts": ["general_validation"],
                "required_evidence": ["independent_validation_evidence"],
            },
        }),
        encoding="utf-8",
    )
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        batch_size=1,
        selection_mode="curriculum",
        evidence_generation_path=generated_directory,
    )

    selected = assistant.select_batch(
        ["task_general.json"],
        task_directory=tasks_directory,
        operational_economy_report={
            "evidence_acquisition_state": "EVIDENCE_ACQUISITION_PLAN_READY",
            "evidence_acquisition_required_evidence": (
                "cross_source_consensus_evidence"
            ),
            "evidence_acquisition_required_category": "CROSS_SOURCE_CONSENSUS",
            "evidence_acquisition_validation_task": (
                "select_cross_source_tie_break_validation_task"
            ),
            "evidence_acquisition_tie_break_strategy": "cross_source_consensus",
            "evidence_acquisition_target_operation": "replace_color",
            "evidence_acquisition_expected_tie_break_impact": "HIGH",
            "evidence_acquisition_target_candidate": (
                "semantic_program:replace_color"
            ),
        },
    )

    generated_task = selected["selected_task_files"][0]
    assert str(generated_task).startswith(str(generated_directory))
    assert generated_directory.exists()
    alignment = selected["training_economy_alignment_report"]
    assert alignment["decision_orchestration_state"] == (
        "PLAN_CONSUMED_AND_TASK_SCHEDULED"
    )
    assert alignment["evidence_acquisition_plan_forwarded"] is True
    assert alignment["evidence_acquisition_task_scheduled"] is True
    assert alignment["evidence_acquisition_selected_task"] == generated_task
    assert alignment["evidence_acquisition_alignment_trace"][0][
        "generated_validation_opportunity"
    ] is True

    generation = selected["evidence_generation_report"]
    assert generation["generation_required"] is True
    assert generation["generation_status"] == "GENERATED_VALIDATION_OPPORTUNITY"
    assert generation["training_assistant_queue_updated"] is True
    assert generation["future_execution_ready"] is True
    assert generation["evidence_produced"] is False
    assert generation["truth_authority"] == "NONE"
    assert generation["trust_authority"] == "NONE"
    assert generation["graduation_authority"] == "NONE"


def test_training_assistant_tracks_evidence_remediation_across_runs(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    for task_file, metadata in {
        "elite_cognitive_task_01.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["object_grounding"],
            "required_evidence": ["grounded_target_object_evidence"],
            "task_properties": ["select_object_grounded_validation_task"],
            "responsibility_targets": ["OBJECT_GROUNDING_LAYER"],
        },
        "elite_cognitive_task_02.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["general_validation"],
        },
    }.items():
        (tasks_directory / task_file).write_text(
            json.dumps({"train": [], "test": [], "nexryn_metadata": metadata}),
            encoding="utf-8",
        )
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        batch_size=1,
        selection_mode="curriculum",
    )

    first = assistant.select_batch(
        ["elite_cognitive_task_01.json", "elite_cognitive_task_02.json"],
        task_directory=tasks_directory,
        operational_economy_report={
            "knowledge_operationalization_choke_cause": (
                "missing_object_grounding"
            ),
            "knowledge_operationalization_choke_action": (
                "select_object_grounded_validation_task"
            ),
            "knowledge_operationalization_evidence_responsibility": (
                "OBJECT_GROUNDING_LAYER"
            ),
            "knowledge_operationalization_required_evidence": (
                "grounded_target_object_evidence"
            ),
        },
    )
    assert first["training_economy_alignment_report"]["remediation_outcome"] == (
        "REMEDIATION_ATTEMPT_QUEUED"
    )
    assistant.complete_cycle(successful_tasks=1)

    second = assistant.select_batch(
        ["elite_cognitive_task_01.json", "elite_cognitive_task_02.json"],
        task_directory=tasks_directory,
        operational_economy_report={
            "knowledge_operationalization_choke_point": "evidence_sufficiency",
            "knowledge_operationalization_choke_cause": "evidence_sufficient",
        },
    )

    alignment = second["training_economy_alignment_report"]
    assert alignment["evidence_remediation_progress_state"] == (
        "EVIDENCE_DEFICIT_CLEARED"
    )
    assert alignment["previous_remediation_task"] == "elite_cognitive_task_01.json"
    assert alignment["previous_evidence_deficit"] == (
        "grounded_target_object_evidence"
    )
    assert alignment["current_evidence_deficit"] is None
    assert alignment["required_evidence_produced"] is True
    assert alignment["remediation_outcome"] == "REMEDIATION_IMPROVED"


def test_training_assistant_prioritizes_composition_and_source_diversity(tmp_path):
    tasks_directory = tmp_path / "training"
    tasks_directory.mkdir()
    for task_file, metadata in {
        "elite_cognitive_task_01.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["color_validation"],
        },
        "elite_cognitive_task_02.json": {
            "elite_cognitive_task": True,
            "target_concepts": ["pattern_completion", "adaptive_reuse"],
            "composition_opportunity_targets": [
                "Pattern Completion Intelligence",
            ],
            "missing_composite_capabilities": ["pattern_completion"],
            "candidate_source_targets": ["adaptive_reuse"],
            "source_diversity_targets": ["adaptive_reuse"],
        },
    }.items():
        (tasks_directory / task_file).write_text(
            json.dumps({"train": [], "test": [], "nexryn_metadata": metadata}),
            encoding="utf-8",
        )
    assistant = TrainingAssistant(
        state_path=tmp_path / "training_assistant_state.json",
        selection_memory_path=tmp_path / "task_selection_memory.json",
        batch_size=1,
        selection_mode="curriculum",
    )

    selected = assistant.select_batch(
        ["elite_cognitive_task_01.json", "elite_cognitive_task_02.json"],
        task_directory=tasks_directory,
        operational_economy_report={
            "arena_source_diversity_state": "LOW_SOURCE_DIVERSITY",
            "arena_source_diversity_action": "SOURCE_DIVERSITY_SPRINT_REQUIRED",
            "missing_candidate_sources": ["adaptive_reuse"],
            "candidate_source_materialization_rows": [
                {
                    "source": "adaptive_reuse",
                    "source_materialization_state": (
                        "NO_EXECUTABLE_CANDIDATE"
                    ),
                }
            ],
            "capability_composition_opportunities": [
                {
                    "composite_name": "Pattern Completion Intelligence",
                    "required_capabilities": [
                        "pattern_completion",
                        "translate",
                    ],
                    "missing_capabilities": ["pattern_completion"],
                    "composition_state": "PARTIAL_COMPOSITION",
                }
            ],
        },
    )

    assert selected["selected_task_files"] == ["elite_cognitive_task_02.json"]
    alignment = selected["training_economy_alignment_report"]
    assert alignment["composition_opportunity_alignment"] == (
        "COMPOSITION_OPPORTUNITY_ALIGNED"
    )
    assert alignment["arena_source_diversity_alignment"] == (
        "SOURCE_DIVERSITY_ALIGNED"
    )
    assert alignment["selected_composition_aligned_tasks"] == [
        "elite_cognitive_task_02.json"
    ]
    assert alignment["selected_source_diversity_aligned_tasks"] == [
        "elite_cognitive_task_02.json"
    ]
    assert "composition_opportunity_alignment" in selected[
        "elite_selection_report"
    ]["priority_reasons"]
    assert "arena_source_diversity_alignment" in selected[
        "elite_selection_report"
    ]["priority_reasons"]
