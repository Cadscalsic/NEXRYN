from runtime.world_governance import WorldKernel


def test_every_cycle_begins_with_execution_intent_and_report():
    kernel = WorldKernel()

    report = kernel.govern_cognitive_cycle(
        {
            "goal": "solve_novel_dependency_task",
            "difficulty": 0.8,
            "novelty": 0.75,
            "risk_level": 0.55,
            "required_confidence": 0.9,
        },
        runtime_events=[
            {
                "runtime_id": "adaptive_search",
                "confidence": 0.42,
                "progress": 0.4,
                "evidence_growth": 2,
                "resource_consumption": 0.35,
            }
        ],
    )

    executive = report["WORLD_GOVERNANCE_EXECUTIVE_REPORT"]

    assert executive["Execution Intent"]["goal"] == "solve_novel_dependency_task"
    assert executive["Execution Intent"]["execution_profile"] == "deep"
    assert executive["Execution Graph"]["graph_type"] == "task_dependent_runtime_dependency_graph"
    assert executive["Runtime Budgets"]["global_budget"]["reasoning_budget"] > 0
    assert executive["Thermal Decisions"]["acsc_controlled_by"] == "world_governance"
    assert executive["Adaptive Replanning Events"]["replanning_required"] is True
    assert executive["Final Executive Assessment"]["cycle_governed"] is True


def test_runtime_activation_is_authorized_by_governance():
    kernel = WorldKernel()
    intent = kernel.build_execution_intent({
        "goal": "simple_color_transform",
        "difficulty": 0.1,
        "risk_level": 0.1,
    })
    graph = kernel.construct_execution_graph(intent)
    budgets = kernel.allocate_runtime_budgets(intent, graph)

    activation = kernel.authorize_runtime_activation(graph, budgets)

    assert activation["activated_runtimes"]
    assert all(
        runtime["activated_by"] == "world_governance"
        for runtime in activation["activated_runtimes"]
    )
    assert {
        runtime["runtime_id"]
        for runtime in activation["activated_runtimes"]
    } == {"concept_runtime", "program_runtime", "evaluation_runtime"}


def test_artifact_transition_governance_rejects_illegal_moves():
    kernel = WorldKernel()

    decision = kernel.govern_artifact_transition(
        {
            "artifact_id": "artifact_1",
            "state": "created",
            "owner": "evidence_builder",
        },
        "committed",
    )

    assert decision["transition_allowed"] is False
    assert decision["decision"] == "REJECT_ILLEGAL_TRANSITION"
    assert decision["ownership_enforced"] is True


def test_truth_world_model_and_dna_promotion_are_governed():
    kernel = WorldKernel()

    truth = kernel.govern_truth_promotion({
        "truth_id": "truth_1",
        "confidence": 0.91,
        "evidence_score": 0.83,
        "contradiction_score": 0.02,
    })
    world_model = kernel.govern_world_model_update({
        "knowledge_id": "knowledge_1",
        "committed": True,
        "contradictory": False,
    })
    dna = kernel.govern_dna_evolution({
        "signal_id": "dna_signal_1",
        "source": "temporary_reasoning",
        "stability": 1.0,
    })

    assert truth["promotion_allowed"] is True
    assert truth["decision"] == "VALIDATE_TRUTH_PROMOTION"
    assert world_model["update_allowed"] is True
    assert world_model["decision"] == "ALLOW_WORLD_MODEL_UPDATE"
    assert dna["dna_evolution_allowed"] is False
    assert dna["temporary_reasoning_rejected"] is True


def test_kernel_build_report_exposes_latest_executive_report():
    kernel = WorldKernel()
    kernel.govern_cognitive_cycle({
        "goal": "reportable_cycle",
        "difficulty": 0.4,
    })

    report = kernel.build_report()

    assert "WORLD_GOVERNANCE_EXECUTIVE_REPORT" in report
    assert report["WORLD_GOVERNANCE_EXECUTIVE_REPORT"]["Execution Intent"][
        "goal"
    ] == "reportable_cycle"


def test_executive_brain_actively_steers_cognition():
    kernel = WorldKernel()

    report = kernel.govern_cognitive_cycle(
        {
            "goal": "solve_geometry_dependency_task",
            "task": "geometry object transformation with dependency reasoning",
            "difficulty": 0.7,
            "novelty": 0.8,
            "risk_level": 0.45,
            "similarity_to_previous_tasks": 0.72,
        },
        runtime_events=[
            {
                "runtime_id": "adaptive_search",
                "confidence": 0.34,
                "progress": 0.35,
                "importance": 0.9,
                "novelty": 0.8,
                "pressure": 0.4,
                "resource_consumption": 0.35,
                "evidence_growth": 1,
            },
            {
                "runtime_id": "truth_runtime",
                "confidence": 0.48,
                "progress": 0.2,
                "importance": 0.7,
                "pressure": 0.6,
                "truth_growth": 0,
            },
        ],
        execution_result={"success": True, "stable": True},
    )

    executive = report["EXECUTIVE_COGNITIVE_REPORT"]
    world_executive = report["WORLD_GOVERNANCE_EXECUTIVE_REPORT"]

    assert executive["governance_authority"] == "Executive World Governance"
    assert executive["active_cognition"] is True
    assert executive["Attention Allocation"]["attention_is_finite"] is True
    assert executive["Goal Hierarchy"]["primary_goal"] == "solve_geometry_dependency_task"
    assert executive["Runtime Priorities"]["priorities_evolve_continuously"] is True
    assert executive["Interrupt Decisions"]["interrupts_enabled"] is True
    assert executive["Experience Reuse"]["reuse_query_performed"] is True
    assert executive["Mental Models Activated"]["selected_mental_model"]["name"] in {
        "Spatial Mental Model",
        "Causal Mental Model",
    }
    assert executive["Strategic Decisions"]["truth_promotion_requires_executive_approval"] is True
    assert "Prediction Results" in executive
    assert "EXECUTIVE_COGNITIVE_REPORT" in world_executive
