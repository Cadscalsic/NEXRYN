from runtime.truth.truth_metric_synchronization_engine import (
    TruthMetricSynchronizationEngine,
)


def test_truth_metric_synchronization_builds_canonical_state():
    engine = TruthMetricSynchronizationEngine()
    report = engine.synchronize(
        execution_instances=[
            {
                "runtime_id": "truth_runtime",
                "execution_id": "truth-1",
                "execution_end": "2026-07-14T10:00:00+00:00",
                "duration_seconds": 0.25,
                "completion_status": "COMPLETED",
                "truth_candidates": 3,
                "validated_truth": 2,
                "promoted_truth": 1,
                "committed_truth": 1,
                "rejected_truth": 1,
                "truth_confidence": 0.74,
                "truth_validation_count": 2,
            }
        ],
        parent_aggregation={"generated_truth_candidates": 3},
        execution_report={"generated_truth_candidates": 3},
        diagnostics={"truth_candidates": 3},
    )

    state = report["canonical_truth_state"]

    assert report["TRUTH_METRIC_SYNCHRONIZATION_REPORT"] is True
    assert report["truth_metric_status"] == "SYNCHRONIZED"
    assert state["truth_candidates"] == 3
    assert state["validated_truth"] == 2
    assert state["committed_truth"] == 1
    assert state["truth_confidence"] == 0.74
    assert report["truth_metric_validation"]["validation_success"] is True
    assert report["truth_metric_consistency"]["single_canonical_source"] is True


def test_truth_metric_synchronization_detects_conflicting_counts():
    report = TruthMetricSynchronizationEngine().synchronize(
        execution_instances=[
            {
                "runtime_id": "truth_runtime",
                "execution_id": "truth-1",
                "execution_end": "2026-07-14T10:00:00+00:00",
                "duration_seconds": 0.25,
                "completion_status": "COMPLETED",
                "generated_truth_candidates": 4,
            }
        ],
        parent_aggregation={"generated_truth_candidates": 2},
        execution_report={"generated_truth_candidates": 4},
    )

    assert report["truth_metric_status"] == "CONFLICTS_DETECTED"
    assert report["truth_metric_validation"]["validation_success"] is False
    assert report["truth_metric_validation"]["parent_conflicts"]
    assert report["truth_metric_consistency"]["parent_aggregation_synchronized"] is False
