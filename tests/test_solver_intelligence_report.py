from runtime import solver_intelligence_report


def test_solver_intelligence_report_builds_execution_graph():
    context = {
        "input_grid": [[1]],
        "output_grid": [[2]],
        "input_object_summaries": [{"id": "obj_1"}],
        "output_object_summaries": [{"id": "obj_2"}],
        "patterns": [{"type": "color"}],
        "rules": [{"rule": "color_changes"}],
        "hypotheses": [{"type": "replace_color", "confidence": 0.9}],
        "ranked_hypotheses": [
            {"type": "replace_color", "confidence": 0.9},
            {"type": "expand_pattern", "confidence": 0.4},
        ],
        "winner_hypothesis": {"type": "replace_color", "confidence": 0.9},
        "synthesized_program": {"step_count": 1},
        "predicted_output": [[2]],
        "transformation_confidence": 0.9,
        "transformation_report": {
            "execution_trace": [
                {
                    "operation": "replace_color",
                    "status": "executed",
                    "confidence": 0.9,
                }
            ]
        },
        "evaluation_result": {"accuracy": 1.0, "success": True},
        "grid_analysis_stage_report": {"status": "completed", "timestamp": "t0"},
        "object_detection_stage_report": {
            "status": "completed",
            "timestamp": "t1",
        },
        "pattern_rule_stage_report": {"status": "completed", "timestamp": "t2"},
        "inference_stage_report": {"status": "completed", "timestamp": "t3"},
        "transformation_stage_report": {
            "status": "completed",
            "timestamp": "t4",
        },
        "evaluation_stage_report": {"status": "completed", "timestamp": "t5"},
        "performance_report": {
            "module_timings": [
                {"module": "inference", "seconds": 0.12},
                {"module": "evaluation", "seconds": 0.03},
            ]
        },
    }

    report = solver_intelligence_report.build_report(
        all_results=[{"task": "task_a", "result": context}],
        performance_report={"reasoning_time_seconds": 0.12},
        cognitive_capability_report={
            "capabilities_executed": [
                {"capability": "color_mapping", "confidence": 0.8}
            ]
        },
    )

    assert report["SOLVER_INTELLIGENCE_REPORT"] is True
    assert report["execution_graph"]["node_count"] == 16
    assert report["execution_graph"]["edge_count"] == 15
    assert report["stage_statistics"]["Hypothesis Generation"][
        "hypotheses_generated"
    ] == 1
    assert report["transformation_statistics"]["attempt_count"] == 1
    assert report["program_statistics"]["programs_ranked"] == 2
    assert report["program_statistics"]["programs_rejected"] == 1
    assert report["capability_activations"][0]["capability"] == "color_mapping"
    assert report["bottleneck_analysis"]["slowest_stage"] is not None
    assert report["optimization_candidates"]

