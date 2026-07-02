from runtime.telemetry import (
    RuntimeTelemetryValidator,
    metric_authority_registry,
)


def test_dependency_state_contradiction_is_detected():
    report = RuntimeTelemetryValidator().validate({
        "dependency_activation_state": "COMPLETED",
        "dependency_chains_executed": 0,
        "dependency_chain_depth": 0,
        "dependency_chain_coverage": 0.0,
        "dependency_time": 0.0,
    })

    assert {
        item["code"]
        for item in report["contradictions"]
    } == {"DEPENDENCY_STATE_CONTRADICTION"}
    assert report["dependency_integrity_score"] < 1.0


def test_metric_authority_reconciles_reuse_from_adaptive_reuse_engine():
    report = metric_authority_registry.reconcile(
        {
            "reuse_rate": 0.0,
            "strategy_hits": 0,
            "truth_hits": 0,
            "context_hits": 0,
        },
        {
            "adaptive_cache_manager": {
                "reuse_rate": 0.0,
                "strategy_hits": 0,
                "truth_hits": 0,
                "context_hits": 0,
            },
            "adaptive_reuse_engine": {
                "reuse_rate": 0.5667,
                "strategy_hits": 15,
                "truth_hits": 15,
                "context_hits": 5,
            },
        },
    )

    assert report["reuse_rate"] == 0.5667
    assert report["strategy_hits"] == 15
    assert report["truth_hits"] == 15
    assert report["context_hits"] == 5
    assert report["metric_authority_conflicts"]
    assert report["METRIC_SOURCE_MAP"]["reuse_rate"]["producer"] == (
        "adaptive_reuse_engine"
    )


def test_public_reuse_rate_matches_reuse_authority():
    report = RuntimeTelemetryValidator().validate({
        "reuse_rate": 0.5667,
        "reuse_metric_authority": {
            "reuse_rate": 0.5667,
        },
        "cache_metric_authority": {
            "reuse_rate": 0.0,
        },
    })

    assert report["contradictions"] == []
    assert report["reuse_integrity_score"] == 1.0
