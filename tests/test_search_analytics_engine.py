from runtime.search.search_analytics_engine import SearchAnalyticsEngine


def _routes():
    return [
        {
            "route_id": "route:a",
            "current_state": "VALIDATED",
            "current_confidence": 0.9,
            "evidence_score": 0.84,
            "expected_information_gain": 0.4,
            "estimated_computational_cost": 0.18,
            "priority": 0.9,
            "depth": 2,
            "branch_width": 2,
            "visited_concepts": ["color", "shape"],
            "visited_transformations": ["replace_color"],
            "visited_programs": ["program:a"],
            "visited_constraints": ["preserve_shape"],
            "validation_status": "validated",
            "decision": "Validate",
            "decision_explanation": "validated route",
        },
        {
            "route_id": "route:b",
            "current_state": "PRUNED",
            "current_confidence": 0.22,
            "evidence_score": 0.2,
            "expected_information_gain": 0.1,
            "estimated_computational_cost": 0.42,
            "priority": 0.25,
            "depth": 3,
            "branch_width": 3,
            "visited_concepts": ["color", "color"],
            "visited_transformations": ["mirror"],
            "visited_programs": [],
            "visited_constraints": [],
            "validation_status": "failed",
            "decision": "Discard",
        },
    ]


def test_search_analytics_engine_computes_explainable_route_metrics():
    report = SearchAnalyticsEngine().build_report(routes=_routes())

    assert report["SEARCH_ANALYTICS_REPORT"] is True
    assert report["search_analytics_authority"] is True
    assert report["routes_analyzed"] == 2
    assert report["overall_search_quality"] > 0.0
    assert report["search_efficiency"] > 0.0
    assert report["search_coverage"] > 0.0
    assert report["search_entropy"] > 0.0
    assert report["average_route_quality"] > 0.0
    assert report["best_route"]["route_id"] == "route:a"
    assert report["worst_route"]["route_id"] == "route:b"
    assert report["route_distribution"]["by_state"]["VALIDATED"] == 1
    assert report["analytics_generation_success"] is True

    route = report["route_analysis"][0]
    assert {
        "route_id",
        "route_length",
        "route_cost",
        "route_quality",
        "route_success",
        "route_confidence",
        "route_reason",
        "route_dependencies",
        "route_reuse",
    }.issubset(route)


def test_search_analytics_engine_reports_failure_without_routes():
    report = SearchAnalyticsEngine().build_report(routes=[])

    assert report["analytics_generation_success"] is False
    assert report["analytics_generation_failures"] == ["no_search_routes"]
