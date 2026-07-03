from runtime.metrics.canonical_metric_registry import CanonicalMetricRegistry
from runtime.metrics.metric_validation_engine import MetricValidationEngine
from runtime.metrics.runtime_event_tracker import RuntimeEventTracker
from runtime.metrics.unified_metric_store import UnifiedMetricStore
from runtime.observability.runtime_observability_layer import RuntimeObservabilityLayer
from runtime.reporting.compact_report_builder import CompactReportBuilder


def _observability():
    registry = CanonicalMetricRegistry()
    store = UnifiedMetricStore(registry=registry)
    validator = MetricValidationEngine(store=store)
    return RuntimeObservabilityLayer(
        store=store,
        registry=registry,
        validator=validator,
    )


def test_registry_defines_canonical_metric_owners():
    registry = CanonicalMetricRegistry()
    audit = registry.metric_source_audit({
        "introspection": {"reasoning_depth": 4},
        "performance": {"reasoning_depth": 0},
    })

    assert registry.owner_for("reasoning_depth") == "reasoning_engine"
    assert registry.owner_for("strategy_hits") == "strategy_memory"
    assert audit["METRIC_SOURCE_AUDIT"] is True
    assert set(audit["metrics"]["reasoning_depth"]["producer"]) == {
        "introspection",
        "performance",
    }


def test_unified_store_reconciles_conflicting_reasoning_depth_by_policy():
    observability = _observability()
    observability.ingest_report(
        {"reasoning_depth": 4, "active_routes": 8},
        producer="introspection_report",
        source="introspection",
    )
    observability.ingest_report(
        {"reasoning_depth": 0, "active_routes": 0},
        producer="performance_report",
        source="performance",
    )
    report = observability.build_reconciliation_report()

    assert observability.get_metric("reasoning_depth") == 4
    assert observability.get_metric("active_routes") == 8
    assert report["METRIC_RECONCILIATION_REPORT"]["metrics_conflicts"] >= 2
    assert report["METRIC_RECONCILIATION_WARNING"] is True


def test_observability_unifies_reuse_hits_for_dashboard_consumers():
    observability = _observability()
    observability.ingest_report(
        {"strategy_hits": 15, "truth_hits": 15, "context_hits": 5},
        producer="performance_layer",
        source="performance",
    )
    observability.ingest_report(
        {"strategy_hits": 0, "truth_hits": 0, "context_hits": 0},
        producer="dashboard",
        source="dashboard",
    )
    canonical = observability.get_metrics([
        "strategy_hits",
        "truth_hits",
        "context_hits",
    ])

    assert canonical == {
        "strategy_hits": 15,
        "truth_hits": 15,
        "context_hits": 5,
    }


def test_runtime_event_tracker_derives_metrics_from_events():
    registry = CanonicalMetricRegistry()
    store = UnifiedMetricStore(registry=registry)
    tracker = RuntimeEventTracker(store=store)

    tracker.track(
        "dependency_execution",
        value=3,
        producer="dependency_runtime",
        source="dependency_executor",
    )
    tracker.track(
        "prediction_generation",
        value=0.94,
        producer="evaluation_runtime",
        source="evaluation",
    )

    assert store.get_metric("dependency_chains_executed") == 3
    assert store.get_metric("prediction_accuracy") == 0.94
    assert tracker.build_report()["event_count"] == 2


def test_compact_performance_report_surfaces_metric_reconciliation():
    reconciliation = {
        "metrics_registered": 16,
        "metrics_validated": 3,
        "metrics_conflicts": 1,
        "metrics_repaired": 1,
        "consistency_score": 0.9,
        "observability_health": "healthy",
    }

    compact = CompactReportBuilder().compact_performance_report({
        "system": "runtime_reasoning_budget",
        "canonical_metrics": {"reasoning_depth": 4},
        "METRIC_RECONCILIATION_REPORT": reconciliation,
        "METRIC_RECONCILIATION_WARNING": True,
    })

    assert compact["canonical_metrics"]["reasoning_depth"] == 4
    assert compact["METRIC_RECONCILIATION_REPORT"]["metrics_repaired"] == 1
    assert compact["METRIC_RECONCILIATION_WARNING"] is True
