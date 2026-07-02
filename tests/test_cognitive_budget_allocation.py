from runtime.planning.cognitive_budget_engine import (
    CognitiveBudgetEngine,
)
from runtime.planning.cognitive_cost_estimator import (
    CognitiveCostEstimator,
)
from runtime.planning.task_complexity_analyzer import (
    TaskComplexityAnalyzer,
)
from runtime.planning.tool_selection_engine import (
    ToolSelectionEngine,
)
from runtime.state.runtime_state import RuntimeState


def _profile_and_cost(task):

    analyzer = TaskComplexityAnalyzer()
    estimator = CognitiveCostEstimator()
    profile = analyzer.analyze(task)
    cost = estimator.estimate(profile)
    profile.estimated_cost = cost.total_cost
    return profile, cost


def test_low_complexity_task_selects_fast_budget():

    profile, cost = _profile_and_cost({
        "input_grid": [[0, 1], [0, 0]],
        "output_grid": [[0, 2], [0, 0]],
    })

    budget = CognitiveBudgetEngine().allocate(profile, cost)

    assert budget.mode == "fast"
    assert budget.max_hypotheses == 2
    assert budget.max_reasoning_depth == 2
    assert budget.max_dependency_depth == 4
    assert budget.telemetry_enabled is False
    assert budget.process_semantics_enabled is False


def test_high_complexity_task_selects_deep_budget():

    profile, cost = _profile_and_cost({
        "input_grid": [
            [1, 0, 2, 0],
            [0, 3, 0, 4],
            [5, 0, 6, 0],
        ],
        "output_grid": [
            [0, 2, 0, 1],
            [4, 0, 3, 0],
            [0, 6, 0, 5],
        ],
        "process_note": "temporal sequence dependency chain",
    })

    budget = CognitiveBudgetEngine().allocate(profile, cost)

    assert budget.mode == "deep"
    assert budget.max_hypotheses == 10
    assert budget.process_semantics_enabled is True
    assert budget.explanation_enabled is True
    assert budget.temporal_reasoning_enabled is False


def test_tool_selection_preserves_safety_floor_in_fast_mode():

    profile, cost = _profile_and_cost({
        "input_grid": [[0, 1], [0, 0]],
        "output_grid": [[0, 2], [0, 0]],
    })
    budget = CognitiveBudgetEngine().allocate(profile, cost)
    selection = ToolSelectionEngine().select(profile, budget)

    assert "identity_governance" in selection.enabled_tools
    assert "truth_governance" in selection.enabled_tools
    assert "contradiction_checks" in selection.enabled_tools
    assert "causal_validation" in selection.enabled_tools
    assert "process_semantics" in selection.disabled_tools
    assert "temporal_reasoning" in selection.disabled_tools


def test_tool_selection_enables_spatial_reasoning_from_task_identity():

    profile, cost = _profile_and_cost({
        "task_id": "arc_concept_path_finding_13.json",
        "target_concepts": ["path_finding"],
        "input_grid": [[0, 1], [0, 0]],
        "output_grid": [[0, 1], [0, 0]],
    })
    budget = CognitiveBudgetEngine().allocate(profile, cost)
    selection = ToolSelectionEngine().select(profile, budget)

    assert profile.task_id == "arc_concept_path_finding_13.json"
    assert profile.target_concepts == ["path_finding"]
    assert "spatial_reasoning" in selection.enabled_tools
    assert selection.selection_reason["spatial_reasoning"] == (
        "task identity or target concepts indicate spatial reasoning"
    )


def test_tool_selection_enables_spatial_reasoning_for_topology_tasks():

    profile, cost = _profile_and_cost({
        "task_id": "arc_generated_component_merging_03.json",
        "target_concepts": ["component_merging", "topology_change"],
        "input_grid": [[1, 0, 1]],
        "output_grid": [[1, 1, 1]],
    })
    budget = CognitiveBudgetEngine().allocate(profile, cost)
    selection = ToolSelectionEngine().select(profile, budget)

    assert "spatial_reasoning" in selection.enabled_tools


def test_task_identity_promotes_object_counting_concepts():

    profile, cost = _profile_and_cost({
        "task_id": "arc_concept_object_counting_03.json",
        "input_grid": [[1, 0], [0, 2]],
        "output_grid": [[1, 2], [0, 0]],
    })
    selection = ToolSelectionEngine().select(
        profile,
        CognitiveBudgetEngine().allocate(profile, cost),
    )

    assert "object_counting" in profile.target_concepts
    assert "cardinality" in profile.target_concepts
    assert "numerical_reasoning" in profile.target_concepts
    assert "set_reasoning" in profile.target_concepts
    assert "dependency_reasoning" in profile.required_capabilities
    assert "dependency_reasoning" in selection.enabled_tools


def test_runtime_state_applies_budget_and_tool_selection():

    profile, cost = _profile_and_cost({
        "input_grid": [[0, 1], [0, 0]],
        "output_grid": [[0, 2], [0, 0]],
    })
    budget = CognitiveBudgetEngine().allocate(profile, cost)
    selection = ToolSelectionEngine().select(profile, budget)
    state = RuntimeState()

    state.apply_reasoning_budget(budget)
    state.apply_tool_selection(selection)

    assert state.get_budget_value("max_hypotheses") == 2
    assert state.is_tool_enabled("identity_governance")
    assert not state.is_tool_enabled("process_semantics")


def test_dependency_tool_selection_creates_runtime_request():

    profile, cost = _profile_and_cost({
        "input_grid": [
            [1, 0, 2],
            [0, 3, 0],
        ],
        "output_grid": [
            [2, 0, 1],
            [0, 3, 0],
        ],
        "process_note": "dependency chain required",
    })
    budget = CognitiveBudgetEngine().allocate(profile, cost)
    selection = ToolSelectionEngine().select(profile, budget)
    state = RuntimeState()

    state.apply_tool_selection(selection)

    request = state.context["runtime_tool_requests"]["dependency_reasoning"]
    lifecycle = state.context["dependency_lifecycle_report"]
    assert request["request_state"] == "REQUESTED"
    assert lifecycle["dependency_activation_state"] == "REQUESTED"
