from pathlib import Path

from runtime.search import CognitiveSearchManager, SearchMemory, build_cognitive_search_report


def _sample_results():
    return [
        {
            "task": "demo_task",
            "result": {
                "search_result": {
                    "paths": [
                        {
                            "path_type": "single",
                            "score": 0.92,
                            "hypotheses": [
                                {
                                    "type": "replace_color",
                                    "primitive": "replace_color",
                                    "confidence": 0.93,
                                    "explanatory_power": 0.9,
                                    "residual_reduction": 0.95,
                                    "semantic_class": "transformation",
                                }
                            ],
                        },
                        {
                            "path_type": "combined",
                            "score": 0.31,
                            "hypotheses": [
                                {
                                    "type": "expand_pattern",
                                    "primitive": "expand_pattern",
                                    "confidence": 0.28,
                                    "explanatory_power": 0.2,
                                },
                                {
                                    "type": "mirror",
                                    "primitive": "mirror",
                                    "confidence": 0.22,
                                    "explanatory_power": 0.1,
                                },
                            ],
                        },
                    ],
                    "best_path": {"path_type": "single", "score": 0.92},
                    "path_count": 2,
                },
                "synthesized_program": {"step_count": 1},
                "evaluation_result": {"success": True, "success_state": "SUCCESS"},
            },
        }
    ]


def test_cognitive_search_manager_builds_route_graph_and_policy_decisions(tmp_path):
    manager = CognitiveSearchManager(
        memory=SearchMemory(Path(tmp_path) / "search_memory.json"),
    )

    report = manager.build_report(
        all_results=_sample_results(),
        cognitive_pipeline_report={"COGNITIVE_PIPELINE_REPORT": True},
        solver_reasoning_report={"SOLVER_REASONING_REPORT": True},
        performance_report={"reasoning_time_seconds": 0.2},
    )

    assert report["COGNITIVE_SEARCH_REPORT"] is True
    assert report["route_statistics"]["routes_created"] == 2
    assert report["route_statistics"]["routes_active"] >= 1
    assert report["search_space_graph"]["nodes"]
    assert report["search_space_graph"]["edges"]
    assert report["route_ranking"][0]["route_id"]
    assert report["winning_route"]["why_it_won"]
    assert report["SEARCH_ANALYTICS_REPORT"]["SEARCH_ANALYTICS_REPORT"] is True
    assert (
        report["SEARCH_EXPLORATION_QUALITY_REPORT"][
            "SEARCH_EXPLORATION_QUALITY_REPORT"
        ]
        is True
    )
    assert report["overall_search_quality"] > 0.0
    assert report["overall_exploration_quality"] > 0.0
    assert report["exploration_entropy"] > 0.0
    assert report["preferred_search_strategy"]
    assert report["search_efficiency"] > 0.0
    assert report["search_coverage"] > 0.0
    assert report["search_entropy"] > 0.0
    assert report["average_route_quality"] > 0.0
    assert report["best_route"]["route_id"]
    assert report["worst_route"]["route_id"]
    assert report["route_distribution"]
    assert report["analytics_generation_success"] is True
    assert report["search_memory"]["persistent_search_memory"] is True


def test_cognitive_search_report_exposes_phase_9_metrics_without_solving():
    report = build_cognitive_search_report(
        all_results=_sample_results(),
        cognitive_pipeline_report={"COGNITIVE_PIPELINE_REPORT": True},
        solver_reasoning_report={"SOLVER_REASONING_REPORT": True},
        performance_report={"execution_time": 1.0},
        persist_memory=False,
    )

    assert report["COGNITIVE_SEARCH_REPORT"] is True
    assert "search_space_size" in report["route_statistics"]
    assert "search_entropy" in report["route_statistics"]
    assert "search_efficiency" in report["route_statistics"]
    assert report["route_statistics"]["overall_search_quality"] > 0.0
    assert report["route_statistics"]["search_coverage"] > 0.0
    assert report["route_statistics"]["search_cost"] > 0.0
    assert "pruning_decisions" in report
    assert "merge_history" in report
    assert "split_history" in report
    assert "reactivation_history" in report
    assert "knowledge_learned" in report
    assert report["runtime_alignment"]["does_not_solve_tasks"] is True
    assert report["runtime_alignment"]["solver_logic_modified"] is False
    assert "SEARCH_EXPLORATION_QUALITY_REPORT" in report
    assert report["productive_routes"]
    assert "preferred_search_strategy" in report
