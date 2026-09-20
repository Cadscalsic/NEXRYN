from runtime.reporting.output_governor import OutputGovernor


def test_runtime_dashboard_limits_selected_tasks_and_uses_schema():
    governor = OutputGovernor()
    dashboard = governor.runtime_dashboard(
        {
            "system": "training_report",
            "tasks_selected": 5,
            "tasks_executed": [
                "task_001.json",
                "task_002.json",
                "task_003.json",
                "task_004.json",
            ],
            "successful_tasks": 2,
            "failed_tasks": 1,
            "incomplete_tasks": 1,
            "multi_task_results": [
                {"task": "task_001.json", "status": "completed"},
                {"task": "task_002.json", "status": "failed", "error": "boom"},
            ],
            "concept_memory": {
                "replication": {
                    "promotion_stage": "TRUTH_CANDIDATE",
                    "promotion_score": 0.91,
                    "used_task_count": 12,
                    "task_history": ["old"] * 12,
                },
            },
        },
        level="normal",
    )

    assert set(
        [
            "system",
            "report_state",
            "status",
            "timestamp",
            "summary",
            "metrics",
            "warnings",
            "failures",
            "recommendations",
        ]
    ).issubset(dashboard)
    assert dashboard["summary"]["selected_tasks"] == [
        "task_001.json",
        "task_002.json",
        "task_003.json",
        "... 1 additional entries hidden",
    ]
    assert dashboard["summary"]["concepts"][0]["history_count"] == 12
    assert "history" not in dashboard


def test_govern_value_hides_archives_until_audit():
    governor = OutputGovernor()
    report = {
        "context_archives": [{"context": index} for index in range(4)],
    }

    normal = governor.govern_value(report, level="normal")
    audit = governor.govern_value(report, level="audit")

    assert normal == {"context_archives_count": 4}
    assert audit == report


def test_runtime_dashboard_uses_performance_report_as_reuse_authority():
    governor = OutputGovernor()
    dashboard = governor.runtime_dashboard(
        {
            "reuse_rate": 0.0,
            "strategy_hits": 0,
            "truth_hits": 0,
            "context_hits": 0,
            "knowledge_reuse_report": {
                "reuse_rate": 0.0,
                "strategy_hits": 0,
                "truth_hits": 0,
                "context_hits": 0,
            },
            "performance_report": {
                "cache_hits": 0,
                "cache_misses": 6,
                "reuse_rate": 0.5667,
                "strategy_hits": 15,
                "truth_hits": 15,
                "context_hits": 5,
                "adaptive_reuse_engine": {
                    "reuse_rate": 0.5667,
                    "strategy_hits": 15,
                    "truth_hits": 15,
                    "context_hits": 5,
                    "estimated_compute_saved": 3.2,
                },
            },
        },
        level="normal",
    )

    metrics = dashboard["metrics"]
    assert metrics["reuse_rate"] == 0.5667
    assert metrics["strategy_hits"] == 15
    assert metrics["truth_hits"] == 15
    assert metrics["context_hits"] == 5
    assert metrics["estimated_compute_saved"] == 3.2


def test_runtime_dashboard_counts_context_types_from_registry():
    governor = OutputGovernor()
    dashboard = governor.runtime_dashboard(
        {
            "semantic_context_reports": {
                f"semantic_{index}": {"context_type": "SEMANTIC_CONTEXT"}
                for index in range(15)
            },
            "context_registry_report": {
                "contexts": [
                    {
                        "context_id": "semantic:growth",
                        "concept": "growth",
                        "context_type": "SEMANTIC_CONTEXT",
                        "confidence": 0.9,
                    },
                    {
                        "context_id": "process:growth",
                        "concept": "growth",
                        "context_type": "PROCESS_CONTEXT",
                        "confidence": 0.9,
                    },
                    {
                        "context_id": "causal:growth",
                        "concept": "growth",
                        "context_type": "CAUSAL_CONTEXT",
                        "confidence": 0.8,
                    },
                    {
                        "context_id": "world:growth",
                        "concept": "growth",
                        "context_type": "WORLD_CONTEXT",
                        "confidence": 0.8,
                    },
                ],
            },
        },
        level="normal",
    )

    metrics = dashboard["metrics"]
    assert metrics["context_count"] == 15
    assert metrics["semantic_context_count"] == 1
    assert metrics["process_context_count"] == 1
    assert metrics["causal_context_count"] == 1
    assert metrics["world_context_count"] == 1
