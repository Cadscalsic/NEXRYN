from runtime.profiling import performance_reporter, telemetry


def test_performance_reporter_emits_required_sections():
    telemetry.clear()
    telemetry.configure(enabled=True)
    telemetry.record("stage", "reasoning_cycle", 1.25)

    report = performance_reporter.build_report(
        runtime_context={
            "reasoning_report": {
                "reasoning_depth": 4,
                "active_routes": 2,
            },
            "evaluation_result": {
                "accuracy": 0.8,
                "exact_success": True,
            },
            "COGNITIVE_REUSE_REPORT": {
                "strategy_hits": 1,
                "program_hits": 0,
                "context_hits": 1,
                "truth_hits": 1,
            },
        },
        performance_report={
            "total_runtime_seconds": 10.0,
            "cache_hits": 3,
            "cache_misses": 1,
            "module_timings": [
                {"module": "governance_cycle", "seconds": 3.0},
                {"module": "reasoning_cycle", "seconds": 2.0},
                {"module": "finalize_runtime", "seconds": 0.5},
            ],
        },
        profile_level="detailed",
    )

    assert report["runtime_summary"]["total_runtime_seconds"] == 10.0
    assert report["TOP_EXPENSIVE_MODULES"][0]["module"] == "governance_cycle"
    assert "COGNITIVE_EFFICIENCY_SCORE" in report
    assert "STRATEGY_REUSE_RATE" in report
    assert "POST_COMPLETION_LATENCY" in report
    assert report["memory_efficiency"]["cache_hit_rate"] == 0.75
    assert report["telemetry"]["enabled"] is True
    assert report["telemetry_events"]


def test_telemetry_is_disableable_and_lightweight():
    telemetry.clear()
    telemetry.configure(enabled=False)
    telemetry.record("runtime", "ignored", 1)

    assert telemetry.report()["event_count"] == 0

    telemetry.configure(enabled=True)
    telemetry.record("runtime", "captured", 1)

    assert telemetry.report()["event_count"] == 1
