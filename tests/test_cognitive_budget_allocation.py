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
