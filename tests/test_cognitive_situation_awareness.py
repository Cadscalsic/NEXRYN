from runtime.world_governance import (
    CognitiveSituationAwarenessEngine,
    WorldKernel,
)


def sample_artifacts():
    return {
        "WORLD_GOVERNANCE_EXECUTIVE_REPORT": {
            "Execution Intent": {
                "goal": "solve_spatial_transform",
                "execution_profile": "deep",
                "task_analysis": {
                    "difficulty": 0.7,
                    "novelty": 0.6,
                    "priority": 0.9,
                },
            },
            "Activated Runtimes": [
                {"runtime_id": "concept_runtime"},
                {"runtime_id": "adaptive_search"},
                {"runtime_id": "evidence_builder"},
                {"runtime_id": "truth_runtime"},
            ],
            "Runtime Budgets": {
                "global_budget": {
                    "search_budget": 6,
                    "reasoning_budget": 6,
                    "memory_budget": 256,
                    "truth_budget": 5,
                    "execution_time": 12,
                    "acsc_budget": 0.8,
                }
            },
            "Execution Deviations": {
                "execution_progress": 0.65,
                "resource_consumption": 0.4,
                "confidence_evolution": [0.68, 0.74],
                "evidence_growth": 4,
                "truth_growth": 2,
                "knowledge_density": 0.7,
            },
            "Memory Decisions": {"memory_update_allowed": False},
            "Truth Decisions": [],
            "Knowledge Decisions": [],
        },
        "COGNITIVE_POLICY_REPORT": {
            "Policy Confidence": 0.78,
            "Task Profile": {"priority": 0.9},
            "Selected Policy": {
                "policy": {"policy_id": "novel_task_policy"}
            },
            "Runtime Schedule": {
                "mandatory_runtimes": [
                    "concept_runtime",
                    "adaptive_search",
                    "evidence_builder",
                    "truth_runtime",
                ]
            },
        },
        "COGNITIVE_DECISION_INTELLIGENCE_REPORT": {
            "Selected Decision": {
                "Decision": {"Decision ID": "decision_1"},
                "Decision Utility": 0.72,
            },
            "Decision Confidence": {"Decision Confidence": 0.76},
            "Risk Analysis": {"Execution Risk": 0.3},
        },
        "COGNITIVE_INTELLIGENCE_ANALYTICS_REPORT": {
            "Cognitive KPIs": {
                "Search Intelligence": 0.7,
                "Concept Intelligence": 0.62,
                "Evidence Intelligence": 0.75,
                "Truth Intelligence": 0.65,
                "Memory Intelligence": 0.35,
                "Knowledge Intelligence": 0.72,
                "Governance Intelligence": 0.7,
                "Execution Intelligence": 0.68,
            },
            "Evidence Health": {"Evidence Utility": 0.75},
            "Truth Health": {"Promotion Rate": 0.4, "Truth Candidates": 2},
            "Knowledge Health": {"Knowledge Stability": 0.7},
            "Memory Health": {"Memory Quality": 0.35},
            "Recommended Actions": [
                {
                    "action": "continue truth validation before memory promotion",
                    "domain": "truth",
                    "evidence": "truth still stabilizing",
                }
            ],
        },
        "observed_transformations": ["move_object"],
        "candidate_transformations": ["recolor_object"],
        "concept_count": 43,
        "program_count": 20,
    }


def test_csae_constructs_unified_situation():
    engine = CognitiveSituationAwarenessEngine()

    report = engine.construct_situation(sample_artifacts())

    situation_report = report["COGNITIVE_SITUATION_REPORT"]
    situation = situation_report["Situation"]

    assert situation["Current Goal"] == "solve_spatial_transform"
    assert situation["Execution Profile"] == "deep"
    assert situation_report["Situation Graph"]["graph_type"] == "cognitive_situation_graph"
    assert situation_report["Objects"]["concept_count"] == 43
    assert situation_report["Policies"]["selected_policy"] == "novel_task_policy"
    assert situation_report["Decisions"]["selected_decision"] == "decision_1"
    assert situation["Overall Situation Quality"] > 0


def test_csae_models_uncertainty_risk_and_resources():
    engine = CognitiveSituationAwarenessEngine()

    report = engine.construct_situation(sample_artifacts())
    situation_report = report["COGNITIVE_SITUATION_REPORT"]

    assert "Incomplete Evidence" in situation_report["Uncertainty"]
    assert "Overall Situation Risk" in situation_report["Risk"]
    assert situation_report["Resources"]["Search Budget"] == 6
    assert situation_report["Confidence"]["Overall Situation Confidence"] > 0
    assert situation_report["Situation Explainability"]["What is happening?"]


def test_csae_tracks_history_and_comparison():
    engine = CognitiveSituationAwarenessEngine()
    first = engine.construct_situation(sample_artifacts())
    updated = sample_artifacts()
    updated["WORLD_GOVERNANCE_EXECUTIVE_REPORT"]["Execution Deviations"][
        "execution_progress"
    ] = 0.9

    second = engine.construct_situation(updated)

    assert first["COGNITIVE_SITUATION_REPORT"]["Situation Evolution"][
        "Current Evolution State"
    ] == "birth"
    comparison = second["COGNITIVE_SITUATION_REPORT"]["Situation Comparison"]
    assert comparison["Similarity"] > 0
    assert comparison["Goal Advancement"] == 0.9
    assert len(second["COGNITIVE_SITUATION_REPORT"]["Situation Timeline"]) == 2


def test_csae_predicts_next_situation_and_integrations():
    engine = CognitiveSituationAwarenessEngine()

    report = engine.construct_situation(sample_artifacts())
    situation_report = report["COGNITIVE_SITUATION_REPORT"]

    assert "Likely Next Situation" in situation_report["Expected Next Situation"]
    assert situation_report["World Model Integration"][
        "situation_based_world_model"
    ] is True
    assert situation_report["Memory Integration"][
        "store_complete_cognitive_episode"
    ] is True
    assert situation_report["DNA Integration"][
        "dna_evolves_from_situational_experience"
    ] is True


def test_world_kernel_exposes_cognitive_situation_report():
    kernel = WorldKernel()

    report = kernel.construct_cognitive_situation(sample_artifacts())
    world_report = kernel.build_report()

    assert report["COGNITIVE_SITUATION_REPORT"]["Situation"]
    assert world_report["COGNITIVE_SITUATION_REPORT"]["Situation"]


def test_governed_cycle_generates_unified_situation():
    kernel = WorldKernel()

    report = kernel.govern_cognitive_cycle(
        {
            "goal": "situation_cycle",
            "difficulty": 0.65,
            "novelty": 0.55,
            "risk_level": 0.3,
        },
        runtime_events=[
            {
                "runtime_id": "evidence_builder",
                "confidence": 0.72,
                "progress": 0.75,
                "evidence_growth": 4,
                "truth_growth": 2,
                "knowledge_density": 0.7,
                "resource_consumption": 0.4,
            }
        ],
        execution_result={"success": True},
    )

    situation_report = report["COGNITIVE_SITUATION_REPORT"]

    assert situation_report["Situation"]["Current Goal"] == "situation_cycle"
    assert situation_report["Situation Summary"].startswith("Current Situation:")
    assert situation_report["Overall Situation Quality"] > 0
