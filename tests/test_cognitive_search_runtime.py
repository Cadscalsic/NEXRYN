from runtime.search import (
    CognitiveSearchRuntime,
    SEARCH_RUNTIME_LIFECYCLE,
    build_cognitive_search_report,
)


def _sample_results():
    return [
        {
            "task": "runtime_task",
            "result": {
                "search_result": {
                    "paths": [
                        {
                            "path_type": "single",
                            "score": 0.9,
                            "hypotheses": [
                                {
                                    "type": "replace_color",
                                    "primitive": "replace_color",
                                    "confidence": 0.9,
                                    "explanatory_power": 0.88,
                                }
                            ],
                        },
                        {
                            "path_type": "combined",
                            "score": 0.4,
                            "hypotheses": [
                                {"type": "mirror", "primitive": "mirror", "confidence": 0.3},
                                {"type": "rotate", "primitive": "rotate", "confidence": 0.2},
                            ],
                        },
                    ]
                },
                "synthesized_program": {"step_count": 1},
                "evaluation_result": {"success": True},
            },
        }
    ]


def test_cognitive_search_report_embeds_first_class_search_runtime():
    report = build_cognitive_search_report(
        all_results=_sample_results(),
        performance_report={"search_time_seconds": 0.05},
        persist_memory=False,
    )

    runtime = report["search_runtime"]

    assert report["COGNITIVE_SEARCH_RUNTIME_REPORT"] is True
    assert runtime["COGNITIVE_SEARCH_RUNTIME_REPORT"] is True
    assert runtime["runtime_id"] == "search_runtime"
    assert runtime["metrics"]["search_routes"] == 2
    assert runtime["metrics"]["routes_created"] == 2
    assert runtime["metrics"]["overall_search_quality"] > 0.0
    assert runtime["metrics"]["search_efficiency"] > 0.0
    assert runtime["metrics"]["search_coverage"] > 0.0
    assert runtime["metrics"]["search_entropy"] > 0.0
    assert runtime["metrics"]["average_route_quality"] > 0.0
    assert runtime["metrics"]["analytics_generation_success"] is True
    assert "route_cooling" in runtime["lifecycle"]
    assert "route_reactivation" in runtime["lifecycle"]
    assert runtime["acsc_route_targets"]
    assert runtime["coverage"]["route_cooling_ready"] is True


def test_search_runtime_can_be_built_from_existing_search_report():
    search_report = {
        "route_statistics": {"routes_created": 1, "routes_active": 1},
        "search_space_graph": {
            "nodes": [{"id": "r1", "type": "SearchRoute", "state": "EXPLORING"}],
            "edges": [],
        },
        "route_ranking": [{"route_id": "r1", "current_state": "EXPLORING"}],
    }

    runtime = CognitiveSearchRuntime().build_report(search_report=search_report)

    assert runtime["lifecycle"] == SEARCH_RUNTIME_LIFECYCLE
    assert runtime["metrics"]["search_routes"] == 1
    assert runtime["metrics"]["overall_search_quality"] > 0.0
    assert runtime["graph"]["nodes"][0]["id"] == "r1"
    assert runtime["status"] == "OPERATIONAL"
