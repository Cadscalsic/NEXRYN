from copy import deepcopy

from runtime.reporting.compact_report_builder import CompactReportBuilder


class FakeArray:
    shape = (2, 3)
    dtype = "int64"

    def tolist(self):
        return [[1, 2, 3], [4, 5, 6]]

    def __eq__(self, other):
        return isinstance(other, FakeArray)


def _heavy_context():
    return {
        "episode_completed": True,
        "shutdown_mode": "fast",
        "evaluation_result": {
            "exact_success": True,
            "accuracy": 1.0,
            "winning_primitive": "duplicate_object",
        },
        "performance_report": {
            "total_runtime_seconds": 2.5,
            "cache_hits": 3,
            "cache_misses": 1,
            "slowest_modules": [
                {"module": "governance_cycle", "seconds": 1.0},
            ],
        },
        "prediction_report": {
            "prediction_accuracy": 1.0,
            "success": True,
            "predicted_grid": [[1, 2], [3, 4]],
        },
        "LOCALIZATION_REPORT": {
            "localization_ready": True,
            "execution_ready": True,
        },
        "graph_reasoning": {
            "dependency_evidence": [1, 2, 3, 4],
            "dependency_evidence_count": 4,
        },
        "counterfactual_candidates": [
            {
                "direction": "left",
                "prediction_accuracy": 0.42,
                "predicted_grid": [[1, 0]],
            },
            {
                "direction": "down",
                "prediction_report": {"prediction_accuracy": 0.84},
                "operation": "duplicate_object",
                "predicted_grid": [[1, 0], [1, 0]],
            },
        ],
        "large_list": list(range(20)),
        "array_payload": FakeArray(),
    }


def test_removes_heavy_keys_in_minimal_mode():
    builder = CompactReportBuilder()
    compact = builder.compact_context(_heavy_context(), level="minimal")

    assert "LOCALIZATION_REPORT" not in compact
    assert "graph_reasoning" not in compact
    assert "prediction_report" in compact
    assert compact["compact_report"]["heavy_keys_removed"] >= 1


def test_preserves_essential_success_fields():
    compact = CompactReportBuilder().compact_context(
        _heavy_context(),
        level="minimal",
    )

    assert compact["episode_completed"] is True
    assert compact["evaluation_result"]["exact_success"] is True
    assert compact["evaluation_result"]["accuracy"] == 1.0
    assert compact["performance_report"]["cache_hits"] == 3


def test_summarizes_numpy_like_arrays():
    compact = CompactReportBuilder().compact_context(
        _heavy_context(),
        level="normal",
    )

    assert compact["array_payload"]["array_summary"] is True
    assert compact["array_payload"]["shape"] == [2, 3]
    assert compact["array_payload"]["dtype"] == "int64"


def test_caps_list_length():
    compact = CompactReportBuilder().compact_context(
        _heavy_context(),
        level="normal",
    )

    assert len(compact["large_list"]) == 11
    assert compact["large_list"][-1]["truncated"] is True


def test_full_reports_are_capped_without_mutating_input():
    builder = CompactReportBuilder()
    context = _heavy_context()
    original = deepcopy(context)

    compact = builder.compact_context(context, level="full")

    assert context == original
    assert compact is not context
    assert "LOCALIZATION_REPORT_summary" in compact
    assert "LOCALIZATION_REPORT" in context
    assert len(compact["large_list"]) <= 21


def test_purges_heavy_objects_after_exact_success():
    builder = CompactReportBuilder()
    purged = builder.purge_heavy_objects(_heavy_context())

    assert "LOCALIZATION_REPORT" not in purged
    assert "graph_reasoning" not in purged
    assert purged["performance_report"]["cache_hits"] == 3
    assert purged["LOCALIZATION_REPORT_summary"]["localization_ready"] is True


def test_compact_performance_report_preserves_search_exploration_quality():
    compact = CompactReportBuilder().compact_performance_report({
        "COGNITIVE_SEARCH_REPORT": {
            "COGNITIVE_SEARCH_REPORT": True,
            "overall_search_quality": 0.73,
            "search_efficiency": 0.81,
            "search_coverage": 0.67,
            "search_entropy": 0.88,
            "overall_exploration_quality": 0.69,
            "exploration_entropy": 0.84,
            "exploration_diversity": 0.72,
            "exploration_redundancy": 0.25,
            "exploration_depth": 3.0,
            "exploration_breadth": 4.0,
            "exploration_efficiency": 0.58,
            "exploration_novelty": 0.75,
            "productive_routes": ["route:a"],
            "dead_end_routes": ["route:b"],
            "reused_routes": ["route:c"],
            "unique_routes": ["route:a", "route:b"],
            "preferred_search_strategy": "balanced_exploration",
            "route_ranking": [{"route_id": "route:a"}],
            "search_space_graph": {
                "nodes": [{"id": "route:a"}],
                "edges": [{"from": "route:a", "to": "concept:color"}],
            },
            "SEARCH_EXPLORATION_QUALITY_REPORT": {
                "SEARCH_EXPLORATION_QUALITY_REPORT": True,
                "quality_components": {"coverage": 0.67},
            },
        },
    })

    search = compact["COGNITIVE_SEARCH_REPORT"]
    assert search["COGNITIVE_SEARCH_REPORT"] is True
    assert search["overall_exploration_quality"] == 0.69
    assert search["exploration_entropy"] == 0.84
    assert search["productive_routes"] == ["route:a"]
    assert search["preferred_search_strategy"] == "balanced_exploration"
    assert search["search_graph"]["node_count"] == 1


def test_compact_performance_report_preserves_causal_quality():
    compact = CompactReportBuilder().compact_performance_report({
        "CAUSAL_CONTEXT_REPORT": {
            "CAUSAL_CONTEXT_REPORT": True,
            "causal_context_count": 2,
            "causal_relation_count": 2,
            "average_confidence": 0.77,
            "generated_causal_links": 2,
            "validated_causal_links": 1,
            "canonical_causal_links": 1,
            "causal_quality": 0.74,
            "average_causal_confidence": 0.76,
            "mechanism_completeness": 0.8,
            "generalization_quality": 0.7,
            "prediction_accuracy": 0.82,
            "contradicted_relationships": ["causal:x"],
            "weak_relationships": ["causal:y"],
            "CAUSAL_KNOWLEDGE_QUALITY_REPORT": {
                "CAUSAL_KNOWLEDGE_QUALITY_REPORT": True,
                "maturity_states": {"CANONICAL": 1},
            },
        },
    })

    causal = compact["CAUSAL_CONTEXT_REPORT"]
    assert causal["CAUSAL_CONTEXT_REPORT"] is True
    assert causal["generated_causal_links"] == 2
    assert causal["canonical_causal_links"] == 1
    assert causal["causal_quality"] == 0.74
    assert causal["mechanism_completeness"] == 0.8
    assert causal["contradicted_relationships"] == ["causal:x"]


def test_compacts_concept_lifecycle_report_with_budget_marker():
    report = {
        "system": "concept_maturity_tracker",
        "states": ["DISCOVERING", "TRUTH_CANDIDATE"],
        "concepts": [{
            "concept": "replication",
            "state": "TRUTH_CANDIDATE",
            "used_task_count": 42,
            "task_ids": ["task_001.json"] * 42,
            "promotion_score": 0.93,
            "promotion_stage": "TRUTH_CANDIDATE",
            "candidate_ready": True,
            "blocked_metrics": [],
            "context_artifacts": {"large": "payload"},
            "truth_candidate_promotion": {
                "promotion_dependency_score": 0.94,
                "dependency_chain_depth": 5,
                "dependency_chain_coverage": 1.0,
                "dependency_promotion_blockers": [],
            },
        }],
        "promotion_report": [{
            "concept": "replication",
            "promotion_score": 0.93,
        }],
        "context_count": 3,
        "truth_candidate_count": 1,
        "state_counts": {"TRUTH_CANDIDATE": 1},
    }

    compact = CompactReportBuilder().compact_concept_lifecycle_report(
        report,
        report_budget_seconds=2.0,
        elapsed_seconds=3.5,
    )

    concept = compact["concepts"][0]
    assert compact["concept_lifecycle_compressed"] is True
    assert compact["report_budget_exceeded"] is True
    assert compact["report_truncated_reason"] == (
        "concept_lifecycle_report_budget"
    )
    assert compact["context_count"] == 3
    assert concept["concept_name"] == "replication"
    assert concept["current_stage"] == "TRUTH_CANDIDATE"
    assert concept["observation_count"] == 42
    assert "task_ids" not in concept
    assert "context_artifacts" not in concept
    assert concept["promotion_dependency_score"] == 0.94


def test_summarizes_counterfactual_candidates():
    compact = CompactReportBuilder().compact_context(
        _heavy_context(),
        level="normal",
    )

    assert "counterfactual_candidates" not in compact
    assert compact["counterfactual_candidates_summary"] == {
        "candidate_count": 2,
        "best_accuracy": 0.84,
        "best_direction": "down",
        "best_operation": "duplicate_object",
    }


def test_minimal_report_excludes_heavy_runtime_keys():
    compact = CompactReportBuilder().compact_context(
        {
            "success": True,
            "predicted_grid": [[1, 2]],
            "counterfactual_candidates": [{"predicted_grid": [[1]]}],
            "graph_reasoning": {"nodes": list(range(20))},
            "object_tracker": {"objects": list(range(20))},
            "dependency_evidence": [{"evidence": "heavy"}],
            "localization_reports": [{"region": "heavy"}],
            "object_motion_report": {"path": [1, 2, 3]},
        },
        level="minimal",
    )

    serialized = str(compact)
    for heavy_key in [
        "predicted_grid",
        "counterfactual_candidates",
        "graph_reasoning",
        "object_tracker",
        "dependency_evidence",
        "localization_reports",
        "object_motion_report",
    ]:
        assert heavy_key not in serialized


def test_summarizes_historical_task_lists():
    compact = CompactReportBuilder().compact_context(
        {
            "observed_tasks": [
                f"task_{index:03}.json"
                for index in range(1, 126)
            ],
            "source_files": [
                f"source_{index:03}.json"
                for index in range(1, 21)
            ],
        },
        level="normal",
    )

    assert "observed_tasks" not in compact
    assert compact["observation_count"] == 125
    assert compact["source_files_count"] == 20
    assert "recent_tasks" not in compact
    assert "recent_sources" not in compact


def test_audit_report_can_include_historical_task_lists():
    compact = CompactReportBuilder().compact_context(
        {
            "observed_tasks": [
                f"task_{index:03}.json"
                for index in range(1, 5)
            ],
        },
        level="audit",
    )

    assert compact["observed_tasks_count"] == 4
    assert compact["observed_tasks"] == [
        "task_001.json",
        "task_002.json",
        "task_003.json",
        "task_004.json",
    ]


def test_normal_report_summarizes_grids_traces_and_nested_runtime_objects():
    compact = CompactReportBuilder().compact_context(
        {
            "prediction_report": {
                "success": True,
                "predicted_grid": [[1, 2], [3, 4]],
            },
            "world_model": {
                "simulation_trace": [
                    {"operation": "translate", "predicted_grid": [[1]]}
                    for _ in range(30)
                ],
            },
            "runtime_context": {
                "predicted_grid": [[1, 2]],
                "simulation_trace": list(range(100)),
                "nested": {"large": list(range(100))},
            },
        },
        level="normal",
    )

    serialized = str(compact)

    assert "predicted_grid': [[" not in serialized
    assert "simulation_trace': [" not in serialized
    assert compact["prediction_report"]["predicted_grid_summary"] == {
        "summary": "grid_summarized",
        "rows": 2,
        "columns": 2,
        "cell_count": 4,
    }
    assert compact["world_model"]["simulation_trace_summary"][
        "item_count"
    ] == 30
    assert compact["runtime_context_summary"]["key_count"] == 3
    assert compact["compact_report"]["heavy_keys_removed"] >= 3
