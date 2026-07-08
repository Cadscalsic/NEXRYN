import numpy as np

from core.solver import ARCSolver
from runtime.cognitive_pipeline import (
    CognitiveContext,
    CognitivePipelineOrchestrator,
    build_cognitive_pipeline_report,
)
from runtime.cognitive_pipeline.stages import DEFAULT_COGNITIVE_STAGE_IDS


class Grid:
    def __init__(self, grid):
        self.grid = np.array(grid)


def test_arc_solver_runs_through_cognitive_pipeline_without_behavior_change():
    solver = ARCSolver(
        Grid([[1, 0], [1, 0]]),
        [{"rule": "color_changes", "removed_colors": [1], "added_colors": [5]}],
    )

    predicted = solver.solve()

    assert predicted.tolist() == [[5, 0], [5, 0]]
    assert solver.cognitive_pipeline_report["COGNITIVE_PIPELINE_REPORT"] is True
    assert [
        event["stage_id"]
        for event in solver.cognitive_context.stage_events
    ] == list(DEFAULT_COGNITIVE_STAGE_IDS)
    for event in solver.cognitive_context.stage_events:
        assert event["stage_id"]
        assert event["stage_name"]
        assert "execution_start" in event
        assert "execution_end" in event
        assert "duration" in event
        assert "cpu_cost" in event
        assert "memory_cost" in event
        assert "confidence" in event
        assert "generated_concepts" in event
        assert "consumed_concepts" in event
        assert "dependencies" in event
        assert "produced_knowledge" in event
        assert event["execution_status"] == "completed"


def test_cognitive_pipeline_report_includes_metrics_and_bottlenecks():
    context = CognitiveContext(
        input_grid=[[1, 0], [1, 0]],
        rules=[{"rule": "color_changes", "removed_colors": [1], "added_colors": [5]}],
        output_grid=[[5, 0], [5, 0]],
    )
    context = CognitivePipelineOrchestrator().execute(context)

    report = build_cognitive_pipeline_report(contexts=[context])

    assert report["COGNITIVE_PIPELINE_REPORT"] is True
    assert len(report["pipeline_graph"]["nodes"]) == len(DEFAULT_COGNITIVE_STAGE_IDS)
    assert report["pipeline_statistics"]["pipeline_depth"] == len(DEFAULT_COGNITIVE_STAGE_IDS)
    assert report["pipeline_statistics"]["pipeline_width"] == 1
    assert report["concept_evolution"]
    assert report["hypothesis_evolution"]
    assert report["transformation_evolution"]
    assert report["program_evolution"]
    assert report["validation_statistics"]["validation_successes"] == 1
    assert report["pipeline_bottlenecks"]["slowest_stage"]["stage_id"]
    assert report["optimization_candidates"]["highest_reuse_opportunity"]["stage_id"]
