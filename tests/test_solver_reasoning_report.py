from runtime import solver_intelligence_report, solver_reasoning_report


def test_solver_reasoning_report_explains_solver_decisions():
    context = {
        "input_grid": [[1]],
        "output_grid": [[2]],
        "input_object_summaries": [{"id": "obj_1"}],
        "output_object_summaries": [{"id": "obj_1"}],
        "patterns": [{"pattern": "colors_added", "value": [2]}],
        "rules": [{"rule": "color_changes", "removed_colors": [1]}],
        "semantic_abstractions": ["symbolic_remapping"],
        "hypotheses": [{"type": "replace_color", "confidence": 0.92}],
        "ranked_hypotheses": [
            {
                "type": "replace_color",
                "primitive": "replace_color",
                "confidence": 0.92,
                "geometric_grounding": {"operator": "replace_color"},
            },
            {
                "type": "expand_pattern",
                "primitive": "expand_pattern",
                "confidence": 0.41,
            },
        ],
        "winner_hypothesis": {
            "type": "replace_color",
            "primitive": "replace_color",
            "confidence": 0.92,
        },
        "synthesized_program": {"step_count": 1},
        "predicted_output": [[2]],
        "transformation_report": {
            "execution_trace": [
                {
                    "operation": "replace_color",
                    "status": "executed",
                    "confidence": 0.92,
                }
            ]
        },
        "evaluation_result": {
            "accuracy": 1.0,
            "success": True,
            "success_state": "SUCCESS",
        },
        "tool_selection_report": {
            "enabled_tools": ["color_mapping", "causal_validation"],
            "selection_reason": {
                "color_mapping": "task contains transformations",
                "causal_validation": "safety floor enabled",
            },
        },
        "inference_stage_report": {
            "status": "completed",
            "timestamp": "2026-07-08 00:00:00",
        },
        "evaluation_stage_report": {
            "status": "completed",
            "timestamp": "2026-07-08 00:00:01",
        },
        "performance_report": {
            "module_timings": [
                {"module": "inference", "seconds": 0.2},
                {"module": "evaluation", "seconds": 0.05},
            ]
        },
    }
    all_results = [{"task": "task_reasoning", "result": context}]
    solver_graph = solver_intelligence_report.build_report(
        all_results=all_results,
        performance_report={"reasoning_time_seconds": 0.2},
    )

    report = solver_reasoning_report.build_report(
        all_results=all_results,
        solver_intelligence_report=solver_graph,
        performance_report={"reasoning_time_seconds": 0.2},
    )

    assert report["SOLVER_REASONING_REPORT"] is True
    assert report["reasoning_graph"]["reuses_solver_execution_graph"] is True
    assert report["reasoning_graph"]["node_count"] > 0
    assert report["reasoning_graph"]["edge_count"] > 0
    assert report["hypothesis_statistics"]["generated_hypotheses"] == 2
    assert report["hypothesis_statistics"]["rejected_hypotheses"] == 1
    assert report["confidence_evolution"][0]["why_confidence_changed"]
    assert report["capability_decisions"]
    assert report["program_decisions"][0]["programs_rejected"] == 1
    assert report["root_decision_analysis"]["root_decision"]
    assert report["success_explanation"]["successful_task_count"] == 1
    assert report["failure_explanation"]["failed_task_count"] == 0
    assert report["reasoning_knowledge"]["stored_as_cognitive_assets"] is True

