import numpy as np

from runtime.pipeline.legacy_pipeline import AdaptiveCognitivePipeline
from runtime.reflection.failure_analyzer import FailureAnalyzer
from runtime.reflection.introspection_engine import IntrospectionEngine
from runtime.stages.evaluation import evaluation_stage


def test_evaluation_stage_marks_missing_prediction_incomplete():
    context = {
        "output_grid": np.zeros((2, 2), dtype=int),
        "cognitive_cycle": {"task_id": "task_missing_prediction"},
    }

    result = evaluation_stage(context)

    assert result["evaluation_complete"] is False
    assert result["pipeline_incomplete"] is True
    assert result["prediction_not_produced"] is True
    assert result["success_state"] == "PREDICTION_NOT_PRODUCED"
    assert result["task_status"] == "TASK_INCOMPLETE"
    assert result["evaluation_result"]["reason"] == "missing_predicted_output"
    assert result["program_memory_report"]["program_saved"] is False


def test_evaluation_stage_still_evaluates_exact_success():
    context = {
        "predicted_output": np.zeros((2, 2), dtype=int),
        "output_grid": np.zeros((2, 2), dtype=int),
        "cognitive_cycle": {"task_id": "task_exact_success"},
    }

    result = evaluation_stage(context)

    assert result["evaluation_complete"] is True
    assert result["evaluation_result"]["accuracy"] == 1.0
    assert result["evaluation_result"]["exact_success"] is True
    assert result["success_state"] in {"SUCCESS", "EXACT_SUCCESS"}


class GridStub:
    def __init__(self, grid):
        self.grid = np.array(grid)


def test_legacy_pipeline_produces_identity_baseline_before_evaluation():
    pipeline = AdaptiveCognitivePipeline.__new__(AdaptiveCognitivePipeline)
    context = {
        "input_grid": GridStub([[1, 0], [0, 2]]),
        "inference_stage_report": {"status": "skipped"},
        "transformation_stage_report": {"status": "skipped"},
    }

    result = pipeline._ensure_prediction_before_evaluation(context)

    assert np.array_equal(result["predicted_output"], context["input_grid"].grid)
    assert result["prediction_fallback_used"] is True
    assert result["prediction_pipeline_report"]["status"] == (
        "fallback_prediction_produced"
    )
    assert result["prediction_pipeline_report"][
        "pipeline_disconnect_detected"
    ] is True


def test_introspection_attributes_contextual_transformation_concepts():
    report = IntrospectionEngine().analyze_cycle(
        {"semantics": {"concept_count": 0}},
        {
            "accuracy": 0.9444,
            "success": False,
            "partial_success": False,
        },
        {
            "input_summary": {
                "object_count": 2,
                "density": 0.055,
                "colors": [0, 2, 3],
                "horizontal_symmetry": False,
                "vertical_symmetry": False,
            },
            "output_summary": {
                "object_count": 0,
                "density": 0.0,
                "colors": [0],
                "horizontal_symmetry": True,
                "vertical_symmetry": True,
            },
        },
    )

    concepts = set(report["attributed_concepts"])

    assert report["semantic_concept_count"] >= 5
    assert "object_removal" in concepts
    assert "density_reduction" in concepts
    assert "color_elimination" in concepts
    assert "symmetry_creation" in concepts
    assert "transformation_sequence" in concepts
    assert report["semantic_attribution_source"] == (
        "contextual_transformation_evidence"
    )


def test_introspection_attributes_path_finding_from_task_signal():
    report = IntrospectionEngine().analyze_cycle(
        {"semantics": {"concept_count": 0}},
        {"accuracy": 0.92, "success": False},
        {
            "task_id": "arc_concept_path_finding_13.json",
            "target_concepts": ["path_finding"],
            "input_summary": {"object_count": 1},
            "output_summary": {"object_count": 1},
        },
    )

    concepts = set(report["attributed_concepts"])

    assert "path_finding" in concepts
    assert "route_completion" in concepts
    assert "reachability" in concepts
    assert "path_construction" in concepts
    assert report["semantic_concept_count"] >= 3
    assert "spatial_delta" in report["semantic_attribution_evidence"]
    assert (
        report["semantic_attribution_evidence"]["spatial_delta"]["evidence"][
            "path_signature"
        ]["reachability_delta"]
        == "reachable_path_added"
    )


def test_introspection_attributes_rotation_from_grid_geometry():
    report = IntrospectionEngine().analyze_cycle(
        {"semantics": {"concept_count": 0}},
        {"accuracy": 0.92, "success": False},
        {
            "task_id": "arc_concept_rotation_reflection_11.json",
            "input_grid": [
                [1, 0],
                [2, 2],
            ],
            "output_grid": [
                [2, 1],
                [2, 0],
            ],
            "input_summary": {
                "object_count": 1,
                "density": 0.75,
                "colors": [0, 1, 2],
            },
            "output_summary": {
                "object_count": 1,
                "density": 0.75,
                "colors": [0, 1, 2],
            },
        },
    )

    concepts = set(report["attributed_concepts"])
    spatial_evidence = report["semantic_attribution_evidence"]["spatial_delta"]

    assert "rotation" in concepts
    assert "orientation_change" in concepts
    assert report["semantic_concept_count"] >= 2
    assert (
        spatial_evidence["evidence"]["geometry_signature"][
            "rotation_signature"
        ]
        == "clockwise_90"
    )


def test_introspection_attributes_inside_outside_from_nested_task_signal():
    report = IntrospectionEngine().analyze_cycle(
        {"semantics": {"concept_count": 0}},
        {"accuracy": 0.90, "success": False},
        {
            "cognitive_cycle": {
                "task_id": "arc_concept_inside_outside_10.json",
                "target_concepts": ["inside_outside"],
            },
            "input_summary": {"object_count": 2},
            "output_summary": {"object_count": 2},
        },
    )

    concepts = set(report["attributed_concepts"])

    assert "inside_outside" in concepts
    assert "containment" in concepts
    assert "relative_position" in concepts
    assert "spatial_delta" in report["semantic_attribution_evidence"]


def test_introspection_attributes_component_merging_from_topology_delta():
    report = IntrospectionEngine().analyze_cycle(
        {"semantics": {"concept_count": 0}},
        {"accuracy": 0.90, "success": False},
        {
            "task_id": "arc_generated_component_merging_03.json",
            "input_grid": [
                [1, 0, 1],
                [0, 0, 0],
                [0, 0, 0],
            ],
            "output_grid": [
                [1, 1, 1],
                [0, 0, 0],
                [0, 0, 0],
            ],
            "input_summary": {
                "object_count": 2,
                "density": 2 / 9,
                "colors": [0, 1],
            },
            "output_summary": {
                "object_count": 1,
                "density": 3 / 9,
                "colors": [0, 1],
            },
        },
    )

    concepts = set(report["attributed_concepts"])
    spatial_evidence = report["semantic_attribution_evidence"]["spatial_delta"]

    assert "component_merging" in concepts
    assert "connectivity_change" in concepts
    assert "topology_change" in concepts
    assert (
        spatial_evidence["evidence"]["topology_signature"][
            "component_merge_delta"
        ]
        == 1
    )


def test_introspection_attributes_hole_removal_from_topology_signal():
    report = IntrospectionEngine().analyze_cycle(
        {"semantics": {"concept_count": 0}},
        {"accuracy": 0.90, "success": False},
        {
            "task_id": "arc_generated_hole_removal_03.json",
            "target_concepts": ["hole_removal"],
            "input_grid": [
                [1, 1, 1],
                [1, 0, 1],
                [1, 1, 1],
            ],
            "output_grid": [
                [1, 1, 1],
                [1, 1, 1],
                [1, 1, 1],
            ],
            "input_summary": {"object_count": 1, "density": 8 / 9},
            "output_summary": {"object_count": 1, "density": 1.0},
        },
    )

    concepts = set(report["attributed_concepts"])
    spatial_evidence = report["semantic_attribution_evidence"]["spatial_delta"]

    assert "hole_removal" in concepts
    assert "topology_repair" in concepts
    assert "connectivity_restoration" in concepts
    assert "topology_change" in concepts
    assert spatial_evidence["evidence"]["topology_signature"]["hole_delta"] == -1


def test_introspection_attributes_bridge_creation_from_task_signal():
    report = IntrospectionEngine().analyze_cycle(
        {"semantics": {"concept_count": 0}},
        {"accuracy": 0.91, "success": False},
        {
            "task_id": "arc_generated_bridge_creation_02.json",
            "target_concepts": ["bridge_creation"],
            "input_summary": {"object_count": 2, "density": 0.20},
            "output_summary": {"object_count": 1, "density": 0.28},
        },
    )

    concepts = set(report["attributed_concepts"])

    assert "bridge_creation" in concepts
    assert "component_connection" in concepts
    assert "connectivity_change" in concepts
    assert "topology_change" in concepts
    assert "spatial_delta" in report["semantic_attribution_evidence"]


def test_introspection_attributes_pattern_completion_from_task_signal():
    report = IntrospectionEngine().analyze_cycle(
        {"semantics": {"concept_count": 0}},
        {"accuracy": 0.9429, "success": False},
        {
            "task_id": "arc_concept_pattern_completion_11.json",
            "target_concepts": ["pattern_completion"],
            "input_summary": {
                "object_count": 3,
                "density": 0.20,
                "horizontal_symmetry": False,
                "vertical_symmetry": False,
            },
            "output_summary": {
                "object_count": 5,
                "density": 0.28,
                "horizontal_symmetry": True,
                "vertical_symmetry": False,
            },
            "predicted_output": [[0, 1], [1, 1]],
            "evaluation_result": {"accuracy": 0.9429},
            "residual_analysis": {"residual_difference_count": 2},
        },
    )

    concepts = set(report["attributed_concepts"])

    assert "pattern_completion" in concepts
    assert "pattern_extension" in concepts
    assert "missing_pattern_recovery" in concepts
    assert "symmetry_guided_completion" in concepts
    assert report["reasoning_depth"] > 0
    assert report["execution_nodes"] > 0
    assert report["pipeline_activity"]["active_stages"]


def test_failure_analysis_uses_introspection_activity_metrics():
    analysis = FailureAnalyzer().analyze_failure(
        {"reasoning": {}, "semantics": {}, "routing": {}, "execution": {}},
        {
            "accuracy": 0.8571,
            "success": False,
            "success_state": "FAILURE",
        },
        {
            "reasoning_depth": 6,
            "semantic_concept_count": 4,
            "active_routes": 3,
            "execution_nodes": 2,
            "pipeline_activity": {
                "active_stages": [
                    "pattern_analysis",
                    "rule_analysis",
                    "predicted_output",
                    "residual_analysis",
                ],
            },
        },
    )

    assert analysis["reasoning_depth"] == 6
    assert analysis["semantic_density"] == 4
    assert analysis["route_count"] == 3
    assert analysis["execution_nodes"] == 2
    assert analysis["pipeline_activity"]["active_stages"]
