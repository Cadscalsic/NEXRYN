from runtime.search import (
    ACSCMemory,
    AdaptiveCognitiveSuperCoolingEngine,
)


def _route(route_id, confidence, utility, cost, risk, future, state="SUPPORTED"):
    return {
        "route_id": route_id,
        "current_state": state,
        "proposed_state": state,
        "current_confidence": confidence,
        "current_utility": utility,
        "future_value": future,
        "expected_future_utility": future,
        "expected_information_gain": future * 0.5,
        "search_budget_consumed": cost,
        "risk_score": risk,
        "concept_coverage": confidence * 0.5,
        "program_coverage": utility * 0.5,
        "truth_support": confidence,
        "memory_support": 0.3,
        "generalization_score": future,
        "novelty": 0.5,
        "compression_score": 0.4,
        "expected_recovery_value": future,
        "reactivation_potential": future,
        "priority_score": utility,
        "supporting_concepts": [f"concept:{route_id}"],
        "supporting_programs": [f"program:{route_id}"],
        "quality": {
            "confidence_score": confidence,
            "utility_score": utility,
            "evidence_score": confidence,
            "search_cost": cost,
            "failure_risk": risk,
            "concept_coverage": confidence * 0.5,
            "program_coverage": utility * 0.5,
            "generalization_potential": future,
            "novelty_score": 0.5,
            "compression_score": 0.4,
        },
        "evidence": [{"source": "test", "strength": confidence}],
        "decision_history": [{"decision": "Expand"}],
    }


def _route_report():
    routes = {
        "hot": _route("hot", 0.92, 0.88, 0.12, 0.1, 0.86),
        "cool": _route("cool", 0.2, 0.18, 0.85, 0.82, 0.16),
        "reactivate": _route(
            "reactivate",
            0.45,
            0.46,
            0.35,
            0.28,
            0.72,
            state="SUSPENDED",
        ),
    }
    return {
        "COGNITIVE_ROUTE_INTELLIGENCE_REPORT": True,
        "cognitive_routes": routes,
        "route_graph": {"nodes": [], "edges": []},
    }


def test_acsc_allocates_resources_and_decisions(tmp_path):
    engine = AdaptiveCognitiveSuperCoolingEngine(
        memory=ACSCMemory(tmp_path / "acsc_memory.json"),
    )

    report = engine.build_report(
        cognitive_route_intelligence_report=_route_report(),
        adaptive_search_intelligence_report={"chosen_strategy": {"strategy": "Hybrid Strategy"}},
        concept_formation_report={"concept_count": 3},
        program_synthesis_report={"generated_programs": 2},
        performance_report={"total_runtime_seconds": 1.0},
    )

    assert report["ACSC_REPORT"] is True
    assert report["thermal_graph"]["nodes"]
    assert report["resource_allocation_timeline"]
    assert report["resource_redistribution"]["measurable"] is True
    assert report["acsc_analytics"]["resource_savings"] >= 0

    for route in report["route_thermal_states"].values():
        assert route["thermal_state"]
        assert route["thermal_score"] >= 0
        assert route["allocated_resources"]
        assert route["resource_history"]
        assert route["cooling_decision"]["action"]

    assert any(
        item["action"] in {"Cool Route", "Suspend Route", "Terminate Route", "Decrease Budget"}
        for item in report["cooling_decisions"]
    )
    assert any(
        item["action"] in {"Increase Budget", "Warm Route", "Reactivate Route"}
        for item in report["reactivation_decisions"]
    )


def test_acsc_memory_persists_thermal_history(tmp_path):
    memory = ACSCMemory(tmp_path / "acsc_memory.json")
    engine = AdaptiveCognitiveSuperCoolingEngine(memory=memory)

    first = engine.build_report(cognitive_route_intelligence_report=_route_report())
    second = engine.build_report(cognitive_route_intelligence_report=_route_report())

    assert first["thermal_memory_update"]["persistent_thermal_memory"] is True
    assert second["thermal_memory"]["budget_history_count"] >= 3
    assert memory.path.exists()
