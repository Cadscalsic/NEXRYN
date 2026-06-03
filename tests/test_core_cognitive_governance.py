from core.goals.goal_manager import GoalManager
from core.metacognition.executive import MetaCognitiveExecutive
from core.self_model.self_state import RecursiveSelfModel


def test_meta_cognitive_executive_budgets_and_reflects():

    executive = MetaCognitiveExecutive()

    context = {
        "runtime_entropy": 0.8868,
        "identity_anchor_core_report": {
            "identity_drift_before": 0.50,
        },
        "recursive_pressure_governor_report": {
            "raw_reasoning_depth": 12,
        },
        "recursive_paths": [
            "a",
            "a",
            "b",
        ],
    }

    report = executive.run_cycle(
        context
    )

    assert report["executive_state"] == "thermal_guarded"

    assert (
        "reduce_exploration"
        in report["strategic_reflection"]["strategic_actions"]
    )

    assert (
        "stabilize_identity"
        in report["strategic_reflection"]["strategic_actions"]
    )

    assert (
        report["cognitive_budgeting"]["exploration"]
        <
        report["cognitive_budgeting"]["attention"]
    )


def test_goal_manager_builds_layers_and_resolves_conflicts():

    manager = GoalManager()

    context = {
        "runtime_entropy": 0.8868,
        "task_path": "data/training/example.json",
    }

    report = manager.run_cycle(
        context
    )

    layers = report["layers"]

    assert len(layers["core_goals"]) >= 3

    assert len(layers["strategic_goals"]) >= 1

    assert len(layers["task_goals"]) == 1

    assert report["dominant_goal"]["level"] == "core"

    assert report["long_term_coherence"] is True


def test_recursive_self_model_maps_capabilities_and_limits():

    model = RecursiveSelfModel()

    context = {
        "runtime_entropy": 0.8868,
        "cognitive_thermodynamics_report": {
            "thermodynamic_state": "hot_but_regulated",
            "semantic_heat_dissipation": {
                "cognitive_equilibrium": 0.42,
            },
        },
        "distributed_cognitive_execution_report": {},
        "distributed_semantic_execution_fabric_report": {},
        "controlled_safe_novelty_report": {},
        "adaptive_semantic_control_report": {},
        "recursive_pressure_governor_report": {
            "pressure_state": "capped",
        },
    }

    report = model.run_cycle(
        context
    )

    assert (
        "thermodynamic_regulation"
        in report["self_representation"]["capable_of"]
    )

    assert (
        "semantic_overheating"
        in report["self_representation"]["uncertain_about"]
    )

    assert (
        "recursive_depth_overrun"
        in report["self_representation"]["known_failure_patterns"]
    )

    assert (
        report["confidence_model"]["uncertainty"]
        > 0
    )
