from runtime.planning.cognitive_cost_estimator import (
    CognitiveCostEstimator,
)
from runtime.planning.runtime_profile_manager import (
    RuntimeProfileManager,
)
from runtime.planning.task_complexity_analyzer import (
    TaskComplexityAnalyzer,
)


def test_low_complexity_color_remap_is_observational_profile():

    analyzer = TaskComplexityAnalyzer()
    estimator = CognitiveCostEstimator()
    manager = RuntimeProfileManager()

    task = {
        "input_grid": [
            [0, 0, 0],
            [0, 1, 0],
            [0, 0, 0],
        ],
        "output_grid": [
            [0, 0, 0],
            [0, 2, 0],
            [0, 0, 0],
        ],
    }

    profile = analyzer.analyze(task)
    cost = estimator.estimate(profile)
    profile.estimated_cost = cost.total_cost
    observation = manager.record(
        profile,
        cost,
        task_signature=analyzer.last_task_signature,
    )

    assert profile.complexity == "low"
    assert profile.object_count == 1
    assert profile.transformation_count == 2
    assert 0.0 <= cost.total_cost <= 1.0
    assert observation["task_complexity"] == "low"
    assert observation["actual_runtime_seconds"] is None


def test_high_complexity_detects_temporal_process_indicators():

    analyzer = TaskComplexityAnalyzer()

    profile = analyzer.analyze({
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

    assert profile.complexity == "high"
    assert profile.temporal_complexity > 0.0
    assert profile.process_complexity >= 0.60


def test_reports_expose_required_fields():

    analyzer = TaskComplexityAnalyzer()
    estimator = CognitiveCostEstimator()
    profile = analyzer.analyze({
        "input_grid": [[0, 1], [0, 0]],
        "output_grid": [[0, 2], [0, 0]],
    })
    cost = estimator.estimate(profile)
    profile.estimated_cost = cost.total_cost

    task_report = analyzer.build_report(profile)
    cost_report = estimator.build_report(cost)

    assert set(task_report) == {
        "task_signature",
        "complexity",
        "object_count",
        "transformation_count",
        "spatial_complexity",
        "process_complexity",
        "temporal_complexity",
        "estimated_cost",
    }
    assert set(cost_report) == {
        "object_cost",
        "relation_cost",
        "dependency_cost",
        "governance_cost",
        "explanation_cost",
        "total_cost",
    }
