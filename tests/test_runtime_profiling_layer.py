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
            "hypotheses": [
                {"concept": "growth"},
                {"concept": "replication"},
            ],
            "counterfactuals": [
                {"concept": "growth"},
            ],
            "COGNITIVE_REUSE_REPORT": {
                "strategy_hits": 1,
                "program_hits": 0,
                "context_hits": 1,
                "truth_hits": 1,
            },
            "counterfactual_reuse_report": {
                "counterfactual_hits": 1,
                "counterfactual_misses": 0,
                "counterfactual_success": 1,
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
    assert report["cognitive_efficiency"]["hypothesis_count"] == 2
    assert report["cognitive_efficiency"]["counterfactual_count"] == 1
    assert report["memory_efficiency"]["cache_hit_rate"] == 0.75
    assert report["memory_efficiency"]["counterfactual_reuse_rate"] == 1.0
    assert report["memory_efficiency"]["counterfactual_success_rate"] == 1.0
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


def test_performance_reporter_scores_truth_generated_hypotheses():
    report = performance_reporter.build_report(
        runtime_context={
            "hypotheses": [
                {"concept": "growth"},
                {"concept": "replication"},
            ],
            "counterfactuals": [
                {"concept": "growth"},
                {"concept": "replication"},
            ],
            "hypothesis_generation_report": {
                "accepted_hypothesis_count": 2,
            },
        },
        performance_report={
            "total_runtime_seconds": 4.0,
            "dependency_chains_executed": 1,
            "dependency_chain_depth": 1,
            "module_timings": [],
        },
    )

    assert report["cognitive_efficiency"]["hypothesis_count"] == 2
    assert report["cognitive_efficiency"]["counterfactual_count"] == 2
    assert report["COGNITIVE_EFFICIENCY_SCORE"] > 0.0
