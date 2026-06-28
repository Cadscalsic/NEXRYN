from runtime.profiling.performance_reporter import PerformanceReporter
from runtime.reporting.compact_report_builder import CompactReportBuilder


def test_performance_reporter_uses_runtime_metric_bridge_fields():
    report = PerformanceReporter().build_report(
        runtime_context={
            "evaluation_result": {
                "exact_success": True,
                "accuracy": 1.0,
            },
        },
        performance_report={
            "total_runtime_seconds": 10.0,
            "active_compute_time_seconds": 7.5,
            "concepts_processed": 5,
            "semantic_concept_count": 5,
            "dependency_chains_executed": 4,
            "dependency_chain_depth": 3,
            "cache_hits": 2,
            "cache_misses": 1,
            "strategy_hits": 1,
            "strategy_misses": 1,
            "context_hits": 1,
            "context_misses": 0,
            "program_hits": 0,
            "program_misses": 1,
            "truth_hits": 1,
            "truth_misses": 0,
            "module_timings": [
                {"module": "dependency_reasoning", "seconds": 2.0},
                {"module": "governance_cycle", "seconds": 5.5},
            ],
        },
        profile_level="minimal",
    )

    runtime = report["runtime_summary"]
    cognition = report["cognitive_efficiency"]
    memory = report["memory_efficiency"]

    assert runtime["active_compute_time_seconds"] == 7.5
    assert runtime["idle_time_seconds"] == 2.5
    assert cognition["semantic_concept_count"] == 5
    assert cognition["reasoning_depth"] == 3
    assert cognition["active_routes"] == 4
    assert memory["strategy_hits"] == 1
    assert memory["context_hits"] == 1
    assert memory["truth_hits"] == 1
    assert memory["reuse_rate"] > 0.0


def test_compact_performance_report_preserves_pipeline_metrics():
    compact = CompactReportBuilder().compact_performance_report({
        "system": "runtime_reasoning_budget",
        "total_runtime_seconds": 10.0,
        "concepts_processed": 5,
        "semantic_concept_count": 5,
        "context_count": 29,
        "dependency_chains_executed": 4,
        "dependency_chain_depth": 3,
        "dependency_chain_coverage": 0.95,
        "active_compute_time_seconds": 7.5,
        "unattributed_runtime_seconds": 2.5,
        "strategy_hits": 1,
        "context_hits": 1,
        "program_hits": 0,
        "truth_hits": 1,
        "metric_source_warnings": [],
    })

    assert compact["concepts_processed"] == 5
    assert compact["semantic_concept_count"] == 5
    assert compact["context_count"] == 29
    assert compact["dependency_chain_depth"] == 3
    assert compact["dependency_chain_coverage"] == 0.95
    assert compact["unattributed_runtime_seconds"] == 2.5
    assert compact["truth_hits"] == 1
