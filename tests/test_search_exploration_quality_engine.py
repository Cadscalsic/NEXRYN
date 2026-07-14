from runtime.search.search_exploration_quality_engine import (
    SearchExplorationQualityEngine,
)


def _routes():
    return [
        {
            "route_id": "route:a",
            "current_state": "VALIDATED",
            "current_confidence": 0.91,
            "evidence_score": 0.86,
            "expected_information_gain": 0.65,
            "estimated_computational_cost": 0.20,
            "priority": 0.92,
            "depth": 3,
            "branch_width": 3,
            "visited_concepts": ["color", "shape", "object"],
            "visited_transformations": ["replace_color", "preserve_shape"],
            "visited_programs": ["program:color"],
            "visited_constraints": ["truth_alignment_required"],
            "validation_status": "validated",
            "decision": "Validate",
            "creation_trigger": "concept_graph",
        },
        {
            "route_id": "route:b",
            "current_state": "PRUNED",
            "current_confidence": 0.18,
            "evidence_score": 0.16,
            "expected_information_gain": 0.10,
            "estimated_computational_cost": 0.45,
            "priority": 0.22,
            "depth": 2,
            "branch_width": 2,
            "visited_concepts": ["noise", "artifact"],
            "visited_transformations": ["mirror"],
            "visited_programs": [],
            "visited_constraints": ["constraint:x"],
            "validation_status": "failed",
            "decision": "Discard",
            "creation_trigger": "hypothesis_branch",
        },
        {
            "route_id": "route:c",
            "current_state": "SUPPORTED",
            "current_confidence": 0.74,
            "evidence_score": 0.71,
            "expected_information_gain": 0.50,
            "estimated_computational_cost": 0.25,
            "priority": 0.68,
            "depth": 3,
            "branch_width": 4,
            "visited_concepts": ["spatial", "object"],
            "visited_transformations": ["translate"],
            "visited_programs": ["program:spatial"],
            "visited_constraints": ["concept_alignment_required"],
            "validation_status": "supported",
            "decision": "Expand",
            "creation_trigger": "route_split",
        },
        {
            "route_id": "route:d",
            "current_state": "SUPPORTED",
            "current_confidence": 0.70,
            "evidence_score": 0.68,
            "expected_information_gain": 0.48,
            "estimated_computational_cost": 0.27,
            "priority": 0.66,
            "depth": 3,
            "branch_width": 4,
            "visited_concepts": ["spatial", "object"],
            "visited_transformations": ["translate"],
            "visited_programs": ["program:spatial"],
            "visited_constraints": ["concept_alignment_required"],
            "validation_status": "supported",
            "decision": "Expand",
            "creation_trigger": "route_split",
        },
    ]


def test_entropy_computation_reflects_route_distribution():
    report = SearchExplorationQualityEngine().build_report(routes=_routes())

    assert report["SEARCH_EXPLORATION_QUALITY_REPORT"] is True
    assert report["exploration_entropy"] > 0.0
    assert report["exploration_entropy"] <= 1.0


def test_coverage_computation_counts_unique_exploration_content():
    report = SearchExplorationQualityEngine().build_report(routes=_routes())

    assert report["exploration_coverage"] > 0.0
    assert report["exploration_coverage"] < 1.0
    assert report["search_graph"]["node_count"] >= len(_routes())


def test_redundancy_detection_ratios_and_repeated_paths():
    report = SearchExplorationQualityEngine().build_report(routes=_routes())
    redundancy = report["redundancy_analysis"]

    assert redundancy["redundancy_ratio"] > 0.0
    assert redundancy["reuse_ratio"] > 0.0
    assert redundancy["unique_route_ratio"] < 1.0
    assert redundancy["repeated_reasoning_paths"]


def test_dead_end_unique_and_novel_route_identification():
    report = SearchExplorationQualityEngine().build_report(routes=_routes())

    assert report["dead_end_routes"] == ["route:b"]
    assert "route:a" in report["productive_routes"]
    assert "route:a" in report["unique_routes"]
    assert "route:b" in report["novel_routes"]


def test_strategy_classification_balanced_and_aggressive():
    balanced = SearchExplorationQualityEngine().build_report(routes=_routes())
    aggressive_routes = [
        {
            **route,
            "branch_width": 6,
            "priority": 0.25 + index * 0.2,
            "creation_trigger": f"branch:{index}",
        }
        for index, route in enumerate(_routes())
    ]
    aggressive = SearchExplorationQualityEngine().build_report(
        routes=aggressive_routes,
    )

    assert balanced["preferred_search_strategy"] == "balanced_exploration"
    assert aggressive["preferred_search_strategy"] == "aggressive_exploration"
    assert aggressive["strategy_analysis"]["excessive_branching"] is True


def test_quality_score_consistency_and_route_fields():
    report = SearchExplorationQualityEngine().build_report(routes=_routes())

    assert 0.0 <= report["overall_exploration_quality"] <= 1.0
    assert 0.0 <= report["exploration_efficiency"] <= 1.0
    assert 0.0 <= report["exploration_novelty"] <= 1.0
    route = report["path_quality"][0]
    assert {
        "route_id",
        "route_depth",
        "route_cost",
        "route_quality",
        "route_productivity",
        "route_novelty",
        "route_reuse",
        "route_confidence",
        "route_success_probability",
    }.issubset(route)


def test_reproducibility_is_deterministic():
    engine = SearchExplorationQualityEngine()
    first = engine.build_report(routes=list(reversed(_routes())))
    second = engine.build_report(routes=_routes())

    assert first["reproducibility_signature"] == second["reproducibility_signature"]
    assert first["overall_exploration_quality"] == second["overall_exploration_quality"]


def test_engine_can_analyze_completed_search_report():
    search_report = {
        "route_ranking": _routes(),
        "search_space_graph": {
            "nodes": [{"id": "route:a", "type": "SearchRoute"}],
            "edges": [{"from": "route:a", "to": "concept:color", "type": "visits"}],
        },
    }

    report = SearchExplorationQualityEngine().build_report(
        search_report=search_report,
    )

    assert report["routes_analyzed"] == 4
    assert report["search_graph"]["edge_count"] == 1
    assert report["learning_output"]["productive_search_patterns"]
