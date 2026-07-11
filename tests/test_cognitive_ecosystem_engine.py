from runtime.ecosystem import CognitiveEcosystemEngine


def _engine(tmp_path):
    return CognitiveEcosystemEngine(tmp_path / "ecosystem_states.json")


def _runtime_report():
    return {
        "COGNITIVE_RUNTIME_REPORT": True,
        "runtime_registry": {
            "reasoning_runtime": {"runtime_id": "reasoning_runtime", "coverage": 0.9},
            "search_runtime": {"runtime_id": "search_runtime", "coverage": 0.75},
            "evidence_builder_runtime": {"runtime_id": "evidence_builder_runtime", "coverage": 0.9},
            "truth_runtime": {"runtime_id": "truth_runtime", "coverage": 0.82},
            "memory_runtime": {"runtime_id": "memory_runtime", "coverage": 0.7},
            "world_governance_runtime": {"runtime_id": "world_governance_runtime", "coverage": 0.88},
        },
        "runtime_metrics": {
            "reasoning_runtime": {
                "produced_artifact_count": 3,
                "consumed_artifact_count": 2,
            },
            "search_runtime": {
                "produced_artifact_count": 9,
                "consumed_artifact_count": 5,
                "cognitive_pressure": 0.86,
            },
            "evidence_builder_runtime": {
                "produced_artifact_count": 4,
                "consumed_artifact_count": 4,
            },
            "truth_runtime": {
                "produced_artifact_count": 2,
                "consumed_artifact_count": 5,
            },
            "memory_runtime": {
                "produced_artifact_count": 1,
                "consumed_artifact_count": 4,
            },
            "world_governance_runtime": {
                "produced_artifact_count": 2,
                "consumed_artifact_count": 6,
            },
        },
        "runtime_telemetry": {
            "reasoning_runtime": {"duration_seconds": 0.04},
            "search_runtime": {"duration_seconds": 0.65},
            "evidence_builder_runtime": {"duration_seconds": 0.08},
            "truth_runtime": {"duration_seconds": 0.1},
            "memory_runtime": {"duration_seconds": 0.12},
            "world_governance_runtime": {"duration_seconds": 0.06},
        },
        "runtime_graph": {
            "nodes": [
                {"id": "reasoning_runtime"},
                {"id": "search_runtime"},
                {"id": "evidence_builder_runtime"},
                {"id": "truth_runtime"},
                {"id": "memory_runtime"},
            ],
            "edges": [
                {"from": "reasoning_runtime", "to": "search_runtime"},
                {"from": "search_runtime", "to": "evidence_builder_runtime"},
                {"from": "evidence_builder_runtime", "to": "truth_runtime"},
                {"from": "truth_runtime", "to": "memory_runtime"},
            ],
        },
    }


def _observability_report():
    return {
        "COGNITIVE_OBSERVABILITY_REPORT": True,
        "runtime_reports": {
            "reasoning_runtime": {"health_score": 0.84, "observability_level": 5},
            "search_runtime": {"health_score": 0.42, "observability_level": 4, "warnings": ["route_pressure_high"]},
            "evidence_builder_runtime": {"health_score": 0.83, "observability_level": 5},
            "truth_runtime": {"health_score": 0.78, "observability_level": 5},
            "memory_runtime": {"health_score": 0.58, "observability_level": 4},
            "world_governance_runtime": {"health_score": 0.86, "observability_level": 5},
        },
        "runtime_health": {
            "reasoning_runtime": {"observability_score": 0.9, "execution_success": True, "artifact_consistency": 1.0},
            "search_runtime": {"observability_score": 0.7, "execution_success": True, "artifact_consistency": 0.45},
            "evidence_builder_runtime": {"observability_score": 0.9, "execution_success": True, "artifact_consistency": 1.0},
            "truth_runtime": {"observability_score": 0.86, "execution_success": True, "artifact_consistency": 1.0},
            "memory_runtime": {"observability_score": 0.7, "execution_success": True, "artifact_consistency": 0.8},
            "world_governance_runtime": {"observability_score": 0.9, "execution_success": True, "artifact_consistency": 1.0},
        },
        "artifact_flow_observability": {
            "reasoning_runtime": {
                "produced_artifacts": ["concept:a"],
                "consumed_artifacts": [],
                "published_artifacts": {"concept:a": "CONCEPT"},
                "missing_required": [],
                "rejected_artifacts": [],
            },
            "search_runtime": {
                "produced_artifacts": ["route:a"],
                "consumed_artifacts": ["concept:a"],
                "published_artifacts": {"route:a": "ROUTE"},
                "missing_required": ["program_store"],
                "rejected_artifacts": ["route:failed"],
            },
            "evidence_builder_runtime": {
                "produced_artifacts": ["evidence:a"],
                "consumed_artifacts": ["route:a"],
                "published_artifacts": {"evidence:a": "EVIDENCE"},
                "missing_required": [],
                "rejected_artifacts": [],
            },
            "truth_runtime": {
                "produced_artifacts": ["truth:a"],
                "consumed_artifacts": ["evidence:a"],
                "published_artifacts": {"truth:a": "TRUTH"},
                "missing_required": [],
                "rejected_artifacts": [],
            },
            "memory_runtime": {
                "produced_artifacts": ["memory:a"],
                "consumed_artifacts": ["truth:a"],
                "published_artifacts": {"memory:a": "MEMORY"},
                "missing_required": [],
                "rejected_artifacts": [],
            },
            "world_governance_runtime": {
                "produced_artifacts": ["intent:a"],
                "consumed_artifacts": ["memory:a"],
                "published_artifacts": {"intent:a": "INTENT"},
                "missing_required": [],
                "rejected_artifacts": [],
            },
        },
        "cognitive_timeline": [
            {"runtime_id": "reasoning_runtime"},
            {"runtime_id": "search_runtime"},
            {"runtime_id": "evidence_builder_runtime"},
            {"runtime_id": "truth_runtime"},
            {"runtime_id": "memory_runtime"},
            {"runtime_id": "world_governance_runtime"},
        ],
        "observability_gap_detection": {
            "missing_snapshots": [],
            "missing_metrics": ["search_runtime"],
            "missing_telemetry": [],
            "missing_artifact_reports": [],
            "missing_lifecycle_events": [],
        },
    }


def test_ecosystem_engine_computes_homeostatic_runtime_ecology(tmp_path):
    engine = _engine(tmp_path)

    report = engine.build_report(
        runtime_report=_runtime_report(),
        observability_report=_observability_report(),
        governance_report={"runtime_budgets": {"search_runtime": {"budget": 0.8}}},
        policy_report={"selected_policy": {"policy_id": "pressure_policy"}},
        decision_report={"selected_decision": {"decision_id": "decision:rebalance"}},
        situation_report={"current_goal": "stabilize ecosystem"},
        analytics_report={"overall_cognitive_intelligence_score": 0.76},
        acsc_report={"thermal_decisions": [{"runtime_id": "search_runtime"}]},
        experience_report={"experience": {"semantic_domains": ["Geometry"]}},
        world_model_report={"ecosystem_states": []},
        dna_report={"traits": {}},
    )

    search = report["runtime_ecology"]["search_runtime"]

    assert report["COGNITIVE_ECOSYSTEM_REPORT"] is True
    assert report["global_health"] > 0
    assert search["health"] < search["pressure"]
    assert search["energy"] < 0.6
    assert search["risk"] > 0.5
    assert "search_runtime" in report["health_distribution"]
    assert report["influence_graph"]["edges"]
    assert report["dependency_health"]["weak_dependencies"]
    assert report["collaboration_matrix"]["search_runtime"]
    assert report["resource_flow"]["flows"]
    assert any(item["runtime_id"] == "search_runtime" for item in report["bottlenecks"])
    assert report["cascade_analysis"]["cascading_failures_predicted"] is True
    assert any(item["runtime_id"] == "search_runtime" for item in report["recovery_actions"])
    assert report["predicted_risks"]
    assert report["adaptive_recommendations"]
    assert report["global_stability"] > 0
    assert report["homeostasis_score"] > 0
    assert report["workload_balancing"]["load_distribution"]
    assert report["runtime_collaboration"]["collaboration_quality"] > 0
    assert report["predictive_ecology"]["future_pressure"]
    assert report["self_organization"]["dynamic_priority_adjustment"]["search_runtime"] in {
        "increase_priority",
        "decrease_priority",
        "maintain_priority",
    }
    assert report["ecological_memory"]["persistence"]["stored"] is True
    assert report["world_governance_integration"]["governs_ecosystem_instead_of_isolated_runtimes"] is True
    assert report["acsc_integration"]["cooling_uses_health_pressure_influence_risk_energy"] is True
    assert report["policy_engine_integration"]["policies_regulate_ecosystem_balance"] is True
    assert report["decision_intelligence_integration"]["decision_intelligence_reasons_over_ecosystem_state"] is True
    assert report["situation_awareness_integration"]["situation_includes_ecosystem_state"] is True
    assert report["world_model_integration"]["world_model_stores_ecosystem_states"] is True
    assert report["dna_integration"]["dna_evolves_from_ecosystem_behavior"] is True
    assert report["meta_cognition"]["evaluates_ecosystem_health"] is True
    assert report["runtime_alignment"]["duplicates_world_governance"] is False
    assert report["runtime_alignment"]["duplicates_acsc"] is False


def test_ecosystem_memory_accumulates_ecological_states(tmp_path):
    engine = _engine(tmp_path)

    first = engine.build_report(
        runtime_report=_runtime_report(),
        observability_report=_observability_report(),
    )
    second = engine.build_report(
        runtime_report=_runtime_report(),
        observability_report=_observability_report(),
    )

    assert first["ecological_memory"]["persistence"]["state_count"] == 1
    assert second["ecological_memory"]["persistence"]["state_count"] == 2
    assert second["ecological_memory"]["state"]["runtime_count"] >= 6
