from runtime.reporting.report_budget_manager import ReportBudgetManager


def test_report_budget_manager_flags_over_budget_report_cost():
    manager = ReportBudgetManager(max_runtime_fraction=0.05)

    report = manager.evaluate(
        report_seconds=8.0,
        total_runtime_seconds=100.0,
        report={
            "compact_report": {
                "final_context_size_estimate_before": 1000,
                "final_context_size_estimate_after": 250,
            }
        },
    )

    assert report["report_budget_exceeded"] is True
    assert report["report_compression_required"] is True
    assert report["report_budget_seconds"] == 5.0
    assert report["report_compression_ratio"] == 0.75
