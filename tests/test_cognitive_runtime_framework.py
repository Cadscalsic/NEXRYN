from runtime.cognitive_runtime import build_cognitive_runtime_report
from runtime.observability.runtime_observability_layer import RuntimeObservabilityLayer


def test_cognitive_runtime_report_registers_cognitive_owners():
    report = build_cognitive_runtime_report(
        performance_report={
            "reasoning_time_seconds": 0.2,
            "truth_time_seconds": 0.1,
            "memory_time_seconds": 0.05,
            "evaluation_time_seconds": 0.03,
        },
        runtime_lifecycle_report={"executions": []},
        runtime_observability_report={"observability_score": 0.72},
        cognitive_search_report={
            "COGNITIVE_SEARCH_REPORT": True,
            "route_statistics": {"routes_created": 3},
            "search_space_graph": {"nodes": [{"id": "r1"}], "edges": []},
            "search_timeline": [{"route_id": "r1"}],
        },
        solver_reasoning_report={"SOLVER_REASONING_REPORT": True},
        truth_report={"truth_candidates": [{"id": "t1"}]},
        memory_report={"entries_stored": 4},
        evaluation_report={"success": True, "accuracy": 1.0},
    )

    assert report["COGNITIVE_RUNTIME_REPORT"] is True
    assert set(report["runtime_registry"]) == {
        "reasoning_runtime",
        "search_runtime",
        "truth_runtime",
        "memory_runtime",
        "evaluation_runtime",
    }
    assert report["metric_ownership"]["reasoning_time_seconds"]["owner"] == "reasoning_runtime"
    assert report["metric_ownership"]["search_time_seconds"]["owner"] == "search_runtime"
    assert report["runtime_metrics"]["reasoning_runtime"]["search_routes"] == 3
    assert report["runtime_metrics"]["search_runtime"]["search_routes"] == 3
    assert report["metric_ownership"]["truth_time_seconds"]["owner"] == "truth_runtime"
    assert report["status_semantics"]["overall"] == "SUCCESS_WITH_LIMITED_OBSERVABILITY"
    assert report["acsc_readiness"]["can_cool_search_runtime"] is True
    assert report["acsc_readiness"]["can_cool_search_routes"] is True
    assert report["acsc_readiness"]["cooling_target"] == "cognitive_runtime_and_search_routes"


def test_observability_gaps_are_reinterpreted_as_limited_observability():
    report = RuntimeObservabilityLayer().build_runtime_observability_report(
        performance_report={"module_timings": []},
        runtime_attribution_report={"total_runtime": 1.0},
    )

    assert report["failure"] == "OBSERVABILITY_GAPS_DETECTED"
    assert report["status_semantics"]["execution"] == "SUCCESS"
    assert report["overall_status"] == "SUCCESS_WITH_LIMITED_OBSERVABILITY"
