from runtime.profiling.performance_reporter import PerformanceReporter
from runtime.performance.runtime_attribution_engine import runtime_attribution_engine
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


def test_performance_reporter_never_reports_total_below_active_compute():
    report = PerformanceReporter().build_report(
        performance_report={
            "total_runtime_seconds": 18.0,
            "idle_time_seconds": 18.0,
            "slowest_modules": [
                {"module": "stage_cycle", "seconds": 19.0},
            ],
        },
        profile_level="minimal",
    )

    runtime = report["runtime_summary"]
    stage = report["stage_metrics"][0]

    assert runtime["total_runtime_seconds"] == 19.0
    assert runtime["active_compute_time_seconds"] == 19.0
    assert runtime["idle_time_seconds"] == 0.0
    assert stage["percentage_of_runtime"] == 1.0


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


def test_runtime_attribution_does_not_relabel_cached_executor_time_as_dependency():
    report = runtime_attribution_engine.build_report(
        total_runtime=10.0,
        performance_report={
            "startup_time_seconds": 1.0,
            "task_execution_time_seconds": 2.0,
            "context_count": 5,
            "dependency_chains_executed": 2,
            "dependency_executor_cache_hits": 4,
            "dependency_executor_cache_misses": 2,
        },
    )

    breakdown = report["runtime_breakdown"]

    assert breakdown["dependency_time"] == 0.0
    assert breakdown["context_time"] == 0.0
    assert breakdown["reasoning_time"] == 0.0
    assert breakdown["untracked_runtime"] == 7.0
    assert report["untracked_runtime"] == 7.0


def test_runtime_attribution_does_not_relabel_candidate_runtime_as_truth():
    report = runtime_attribution_engine.build_report(
        total_runtime=20.0,
        performance_report={
            "startup_time_seconds": 1.0,
            "truth_candidate_count": 5,
            "slowest_modules": [
                {"module": "stage_cycle", "seconds": 6.0},
            ],
        },
    )

    breakdown = report["runtime_breakdown"]

    assert breakdown["truth_time"] == 0.0
    assert breakdown["task_execution_time"] == 6.0
    assert breakdown["reasoning_time"] == 0.0
    assert breakdown["untracked_runtime"] == 13.0
    assert report["untracked_runtime"] == 13.0
