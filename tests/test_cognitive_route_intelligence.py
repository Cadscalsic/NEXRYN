from pathlib import Path

from runtime.search.cognitive_route_intelligence import (
    CognitiveRouteIntelligenceEngine,
    RouteIntelligenceMemory,
)
from runtime.search.cognitive_search_manager import SearchRoute


def _engine(tmp_path, persist=False):
    return CognitiveRouteIntelligenceEngine(
        memory=RouteIntelligenceMemory(
            Path(tmp_path) / "route_intelligence_memory.json"
        ),
        persist_memory=persist,
    )


def _routes():
    parent = SearchRoute(
        route_id="task:route:0",
        creation_trigger="single",
        current_state="SUPPORTED",
        current_confidence=0.82,
        evidence_score=0.76,
        expected_information_gain=0.42,
        estimated_computational_cost=0.18,
        priority=0.9,
        depth=1,
        branch_width=1,
        visited_concepts=["spatial_relation", "truth"],
        visited_transformations=["mirror"],
        visited_programs=["program:mirror"],
        visited_constraints=["dependency:axis"],
        validation_status="validated",
        hypotheses=[{"type": "mirror", "explanatory_power": 0.8}],
        scores={
            "novelty_score": 0.5,
            "generalization_potential": 0.78,
            "search_cost": 0.18,
            "expected_remaining_cost": 0.05,
            "reuse_score": 0.4,
        },
    )
    child = SearchRoute(
        route_id="task:route:1",
        parent_route=parent.route_id,
        creation_trigger="combined",
        current_state="EXPLORING",
        current_confidence=0.35,
        evidence_score=0.3,
        expected_information_gain=0.55,
        estimated_computational_cost=0.45,
        priority=0.5,
        depth=2,
        branch_width=2,
        visited_concepts=["spatial_relation", "pattern"],
        visited_transformations=["mirror", "expand"],
        validation_status="unknown",
        hypotheses=[
            {"type": "mirror", "semantic_support": 0.4},
            {"type": "expand", "semantic_support": 0.3},
        ],
        scores={
            "novelty_score": 0.7,
            "generalization_potential": 0.5,
            "search_cost": 0.45,
            "expected_remaining_cost": 0.3,
        },
    )
    return [parent, child]


def test_every_route_exposes_quality_history_relationships_and_future_potential(tmp_path):
    routes = _routes()
    report = _engine(tmp_path).build_report(
        routes,
        search_policy_report={"selected_strategy": "Spatial-First"},
        performance_report={"execution_time": 1.0},
    )

    assert report["COGNITIVE_ROUTE_INTELLIGENCE_REPORT"] is True
    assert set(report["cognitive_routes"]) == {route.route_id for route in routes}
    route = report["cognitive_routes"]["task:route:0"]
    assert route["quality"]["confidence_score"] == 0.82
    assert "failure_risk" in route["quality"]
    assert route["expected_future_utility"] > 0
    assert route["future_value"] > 0
    assert route["thermal_readiness_score"] >= 0
    assert route["decision_history"]
    assert route["concept_coverage"] >= 0
    assert route["program_coverage"] >= 0
    assert "truth_support" in route
    assert "memory_support" in route
    assert route["history"]["observations"] == 0
    assert route["decision_justification"]
    assert route["snapshots"]
    assert route["current_policy"] == "Spatial-First"
    assert route["child_routes"] == ["task:route:1"]
    assert report["route_graph"]["edges"]
    assert report["route_graph"]["relationship_types"]
    assert report["route_ranking"]
    assert report["route_statistics"]["route_entropy"] >= 0
    assert "average_utility" in report["route_statistics"]
    assert "optimization_opportunities" in report
    assert report["dominant_route"]["route_id"]
    assert report["highest_risk_route"]["route_id"]
    assert report["runtime_alignment"]["duplicate_route_objects_created"] is False


def test_route_decisions_and_transitions_are_explainable(tmp_path):
    report = _engine(tmp_path).build_report(
        _routes(),
        performance_report={"execution_time": 1.0},
    )

    validated = report["cognitive_routes"]["task:route:0"]
    combined = report["cognitive_routes"]["task:route:1"]
    assert validated["decision"] == "Validate"
    assert validated["proposed_state"] == "VALIDATED"
    assert "VALIDATED" in validated["lifecycle"]
    assert combined["decision"] == "Merge"
    assert combined["proposed_state"] == "MERGED"
    assert any(
        snapshot["snapshot_type"] == "route_merged"
        for snapshot in combined["snapshots"]
    )
    assert combined["explainability"]["why_it_merged"] != "Route was not merged."


def test_route_intelligence_memory_persists_ranked_outcomes(tmp_path):
    engine = _engine(tmp_path, persist=True)
    report = engine.build_report(
        _routes(),
        performance_report={"execution_time": 1.0},
    )

    memory = report["route_intelligence_memory"]
    assert memory["persistent_route_intelligence_memory"] is True
    assert memory["entries_stored"] == 2
    assert memory["best_routes"]
    assert memory["most_innovative_routes"]

    second = engine.build_report(
        _routes(),
        performance_report={"execution_time": 1.0},
    )
    history = second["cognitive_routes"]["task:route:0"]["history"]
    assert history["observations"] == 1
    assert history["historical_success"] == 1


def test_route_intelligence_reuses_adaptive_concept_and_program_reports(tmp_path):
    route_payload = {
        "route_id": "serialized:route:0",
        "creation_trigger": "serialized_runtime",
        "current_state": "SUPPORTED",
        "current_confidence": 0.55,
        "evidence_score": 0.5,
        "expected_information_gain": 0.4,
        "estimated_computational_cost": 0.3,
        "scores": {
            "generalization_potential": 0.6,
            "search_cost": 0.3,
            "expected_remaining_cost": 0.2,
        },
        "hypotheses": [{"type": "serialized", "semantic_support": 0.5}],
    }

    report = _engine(tmp_path).build_report(
        [route_payload],
        adaptive_search_intelligence_report={
            "route_decisions": [
                {
                    "route_id": "serialized:route:0",
                    "decision": "Expand",
                    "explanation": "adaptive evidence",
                }
            ]
        },
        concept_formation_report={
            "concept_count": 2,
            "top_concepts": [{"concept_id": "concept:a"}],
        },
        program_synthesis_report={
            "generated_programs": 2,
            "winning_programs": [{"program_id": "program:a"}],
        },
        truth_report={"truth_candidates": []},
        memory_report={"reuse": True},
        performance_report={"execution_time": 1.0},
    )

    route = report["cognitive_routes"]["serialized:route:0"]
    assert route["creation_evidence"]["adaptive_search_decision"]["decision"] == "Expand"
    assert route["supporting_concepts"] == ["concept:a"]
    assert route["supporting_programs"] == ["program:a"]
    assert route["supporting_truths"]
    assert route["supporting_memory"]
    assert route["thermal_readiness"]["explanation"]
    assert report["runtime_alignment"]["adaptive_search_intelligence_reused"] is True
