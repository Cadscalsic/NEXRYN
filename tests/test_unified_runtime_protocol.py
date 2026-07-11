from runtime.cognitive_runtime import build_cognitive_runtime_report
from runtime.protocol import (
    ProtocolNegotiator,
    RuntimeLifecycleValidator,
    UnifiedRuntimeProtocol,
    build_unified_runtime_protocol_report,
)


def test_cognitive_runtime_report_emits_unified_runtime_protocol_report():
    report = build_cognitive_runtime_report(
        performance_report={
            "reasoning_time_seconds": 0.2,
            "search_time_seconds": 0.1,
            "truth_time_seconds": 0.1,
            "memory_time_seconds": 0.05,
            "evaluation_time_seconds": 0.03,
        },
        runtime_lifecycle_report={"executions": []},
        runtime_observability_report={"observability_score": 1.0},
        cognitive_search_report={
            "COGNITIVE_SEARCH_REPORT": True,
            "route_statistics": {
                "routes_created": 2,
                "search_cost": 0.2,
                "search_efficiency": 0.9,
            },
            "search_space_graph": {"nodes": [{"id": "route:a"}], "edges": []},
            "search_timeline": [{"route_id": "route:a"}],
        },
        truth_report={"truth_candidates": [{"id": "truth:a"}]},
        memory_report={"entries_stored": 1},
        evaluation_report={"success": True, "accuracy": 1.0},
    )

    protocol = report["unified_runtime_protocol"]

    assert report["UNIFIED_RUNTIME_PROTOCOL_REPORT"] is True
    assert protocol["UNIFIED_RUNTIME_PROTOCOL_REPORT"] is True
    assert protocol["protocol_compliance"]["fully_compliant"] is True
    assert protocol["protocol_compliance"]["compliance_percentage"] == 100.0
    assert "search_runtime" in protocol["runtime_discovery"]
    search = protocol["runtime_reports"]["search_runtime"]["descriptor"]
    assert search["protocol_version"] == "1.0.0"
    assert search["capabilities"] == ["Adaptive Search"]
    assert search["resource_usage"]["search_cost"] == 0.2
    assert set(search["required_inputs"]) == {
        "required_artifacts",
        "required_context",
        "required_dependencies",
        "required_evidence",
        "required_knowledge",
        "required_memory",
        "required_runtime_services",
    }
    assert set(search["expected_outputs"]) == {
        "produced_artifacts",
        "published_artifacts",
        "generated_metrics",
        "generated_evidence",
        "generated_context",
        "generated_knowledge",
        "generated_truth",
        "generated_memory",
    }


def test_protocol_discovery_and_negotiation_are_semantic_and_versioned():
    report = build_unified_runtime_protocol_report({
        "producer_runtime": {
            "runtime_name": "Producer Runtime",
            "execution_id": "producer:1",
            "capabilities": ["Evidence Construction"],
            "expected_outputs": {
                "produced_artifacts": ["EVIDENCE"],
                "published_artifacts": ["EVIDENCE"],
                "generated_metrics": [],
                "generated_evidence": ["EVIDENCE"],
                "generated_context": [],
                "generated_knowledge": [],
                "generated_truth": [],
                "generated_memory": [],
            },
        },
        "consumer_runtime": {
            "runtime_name": "Consumer Runtime",
            "execution_id": "consumer:1",
            "capabilities": ["Truth Validation"],
            "required_inputs": {
                "required_artifacts": ["EVIDENCE"],
                "required_context": [],
                "required_dependencies": [],
                "required_evidence": ["EVIDENCE"],
                "required_knowledge": [],
                "required_memory": [],
                "required_runtime_services": [],
            },
        },
    })
    producer = report["runtime_reports"]["producer_runtime"]["descriptor"]
    consumer = report["runtime_reports"]["consumer_runtime"]["descriptor"]

    negotiation = ProtocolNegotiator().negotiate(producer, consumer)

    assert report["runtime_discovery"]["producer_runtime"]["identity"]["protocol"] == "1.0.0"
    assert negotiation["compatible"] is True
    assert negotiation["communication_status"] == "READY"
    assert negotiation["supported_artifact_types"] == ["EVIDENCE"]


def test_protocol_rejects_illegal_lifecycle_transitions():
    validator = RuntimeLifecycleValidator()

    assert validator.validate(["CREATED", "INITIALIZED", "READY"])["valid"] is True
    invalid = validator.validate(["CREATED", "RUNNING"])
    assert invalid["valid"] is False
    assert invalid["violations"] == [
        {
            "from": "CREATED",
            "to": "RUNNING",
            "violation": "illegal_runtime_state_transition",
        }
    ]


def test_self_validation_reports_missing_interfaces_for_non_normalized_payload():
    protocol = UnifiedRuntimeProtocol()

    validation = protocol.validate_descriptor({"runtime_id": "raw_runtime"})

    assert validation["compliant"] is False
    assert "runtime_name" in validation["missing_interfaces"]
