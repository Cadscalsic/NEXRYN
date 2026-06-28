from runtime.governance.dependency_snapshot_cache import (
    DependencySnapshotCache,
)


def _dependency_report(**overrides):
    report = {
        "dependency_chain_depth": 7,
        "dependency_chain_coverage": 0.96,
        "dependency_coherence": 0.88,
        "process_dependency_links_loaded": 109,
        "process_dependency_links_used": 108,
        "explanation_path": [
            {"target": "perception"},
            {"target": "identity"},
            {"target": "context"},
        ],
        "typed_dependency_relations": [{"full": "graph"}],
        "full_dependency_graph": {"large": "payload"},
        "task_lists": ["do-not-store"],
    }
    report.update(overrides)
    return report


def _truth_report(**overrides):
    report = {
        "final_commit_state": "LOCKED_TRUTH_PRESERVED",
        "identity_runtime_state": "IDENTITY_RUNTIME_STABLE",
        "contextual_truth_supported": True,
    }
    report.update(overrides)
    return report


def _stable_context(**overrides):
    context = {
        "final_commit_state": "LOCKED_TRUTH_PRESERVED",
        "identity_runtime_state": "IDENTITY_RUNTIME_STABLE",
        "contextual_truth_supported": True,
        "contradiction_review_required": False,
        "failed_gates": [],
        "failed_identity_governance_gates": [],
        "missing_dependencies": [],
    }
    context.update(overrides)
    return context


def test_stores_snapshot_for_locked_truth():
    cache = DependencySnapshotCache()
    snapshot = cache.build_snapshot(
        "color_preservation",
        _dependency_report(),
        _truth_report(),
    )
    result = cache.store_snapshot("color_preservation", snapshot)

    assert result["stored"] is True
    assert snapshot["truth_state"] == "LOCKED_TRUTH_PRESERVED"
    assert cache.report()["dependency_snapshot_store_count"] == 1


def test_reuses_snapshot_when_stable():
    cache = DependencySnapshotCache()
    snapshot = cache.build_snapshot(
        "color_preservation",
        _dependency_report(),
        _truth_report(),
    )
    cache.store_snapshot("color_preservation", snapshot)

    report = cache.get_snapshot(
        "color_preservation",
        _stable_context(),
    )

    assert report["dependency_snapshot_reused"] is True
    assert report["dependency_reasoning_skipped"] is True
    assert report["process_dependency_links_loaded"] == 109


def test_rejects_snapshot_on_contradiction_review():
    cache = DependencySnapshotCache()
    snapshot = cache.build_snapshot(
        "color_preservation",
        _dependency_report(),
        _truth_report(),
    )
    cache.store_snapshot("color_preservation", snapshot)

    report = cache.get_snapshot(
        "color_preservation",
        _stable_context(contradiction_review_required=True),
    )

    assert report["dependency_snapshot_reused"] is False


def test_rejects_snapshot_when_identity_unstable():
    cache = DependencySnapshotCache()
    snapshot = cache.build_snapshot(
        "color_preservation",
        _dependency_report(),
        _truth_report(identity_runtime_state="IDENTITY_RUNTIME_PROVISIONAL"),
    )
    cache.store_snapshot("color_preservation", snapshot)

    report = cache.get_snapshot(
        "color_preservation",
        _stable_context(),
    )

    assert report["dependency_snapshot_reused"] is False


def test_rejects_snapshot_when_dependency_coverage_too_low():
    cache = DependencySnapshotCache()
    snapshot = cache.build_snapshot(
        "color_preservation",
        _dependency_report(dependency_chain_coverage=0.72),
        _truth_report(),
    )
    cache.store_snapshot("color_preservation", snapshot)

    report = cache.get_snapshot(
        "color_preservation",
        _stable_context(),
    )

    assert report["dependency_snapshot_reused"] is False


def test_snapshot_is_compact_without_full_graph():
    cache = DependencySnapshotCache()
    snapshot = cache.build_snapshot(
        "color_preservation",
        _dependency_report(),
        _truth_report(),
    )

    assert "typed_dependency_relations" not in snapshot
    assert "full_dependency_graph" not in snapshot
    assert "task_lists" not in snapshot
    assert snapshot["explanation_path_summary"] == [
        "perception",
        "identity",
        "context",
    ]
