from runtime.cache import CacheManager
from runtime.cognition import AdaptiveReuseEngine
from runtime.profiling.metric_bridge import runtime_metric_bridge


def _stable_context(**overrides):
    context = {
        "identity_runtime_state": "IDENTITY_RUNTIME_STABLE",
        "identity_runtime_ready": True,
        "semantic_drift": 0.01,
        "effective_contradiction": 0.01,
        "context_compatibility": 0.95,
        "dependency_compatibility": 0.95,
        "world_model_compatibility": 0.95,
        "truth_integrity_preserved": True,
        "failed_gates": [],
        "failed_identity_governance_gates": [],
        "contradiction_review_required": False,
    }
    context.update(overrides)
    return context


def test_adaptive_reuse_engine_reuses_locked_truth_and_snapshot(tmp_path):
    manager = CacheManager(cache_dir=tmp_path, auto_migrate=False)
    snapshot_key = manager.key("dependency_snapshot", concept="color")
    manager.put(
        "dependency_snapshot",
        key=snapshot_key,
        value={
            "concept": "color",
            "snapshot_state": "ACTIVE",
            "truth_state": "LOCKED_TRUTH_PRESERVED",
            "dependency_chain_depth": 2,
            "dependency_chain_coverage": 0.95,
            "dependency_coherence": 0.95,
            "explanation_path_summary": ["color", "mapping"],
            "identity_runtime_state": "IDENTITY_RUNTIME_STABLE",
            "identity_runtime_ready": True,
            "contextual_truth_supported": True,
        },
    )
    engine = AdaptiveReuseEngine(cache_manager=manager)

    report = engine.evaluate_reuse({
        **_stable_context(concept="color"),
        "truth_commitments": [
            {
                "concept": "color",
                "decision": "TRUTH_COMMITTED",
                "final_commit_state": "LOCKED_TRUTH_PRESERVED",
            }
        ],
    })

    assert report["truth_hits"] == 1
    assert report["dependency_snapshot_hits"] == 1
    assert report["reuse_rate"] > 0
    assert report["dependency_reasoning_skipped"] is True


def test_adaptive_reuse_engine_recomputes_when_governance_uncertain(tmp_path):
    manager = CacheManager(cache_dir=tmp_path, auto_migrate=False)
    engine = AdaptiveReuseEngine(cache_manager=manager)

    report = engine.evaluate_reuse(
        _stable_context(contradiction_review_required=True)
    )

    assert report["eligible"] is False
    assert report["cache_hits"] == 0
    assert report["cache_misses"] >= 1


def test_adaptive_reuse_engine_treats_none_numeric_context_as_default(tmp_path):
    manager = CacheManager(cache_dir=tmp_path, auto_migrate=False)
    engine = AdaptiveReuseEngine(cache_manager=manager)

    report = engine.evaluate_reuse(
        _stable_context(
            semantic_drift=None,
            effective_contradiction=None,
            context_compatibility=None,
            dependency_compatibility=None,
            world_model_compatibility=None,
        )
    )

    assert report["eligible"] is True
    assert report["eligibility_reason"] == "eligible"


def test_metric_bridge_synchronizes_required_timing_fields():
    report = runtime_metric_bridge.synchronize(
        {"total_runtime_seconds": 2.0},
        module_timings=[
            {"module": "runtime_boot", "seconds": 0.2},
            {"module": "dependency_reasoning", "seconds": 0.4},
            {"module": "governance_cycle", "seconds": 0.3},
            {"module": "finalize_runtime", "seconds": 0.1},
        ],
    )

    assert report["active_compute_time_seconds"] == 1.0
    assert report["startup_time_seconds"] == 0.2
    assert report["dependency_reasoning_time_seconds"] == 0.4
    assert report["governance_time_seconds"] == 0.3
    assert report["finalization_time_seconds"] == 0.1
    assert report["idle_time_seconds"] == 1.0
