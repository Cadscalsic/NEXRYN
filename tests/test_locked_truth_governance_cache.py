from runtime.governance.cache import GovernanceCache
from runtime.learning.saturation_detector import saturation_detector


def test_governance_cache_reuses_stable_locked_truth(tmp_path):
    cache = GovernanceCache(
        cache_path=tmp_path / "governance_cache.json",
    )
    runtime_context = {
        "process_dependency_chains": {
            "growth": {"chain": ["seed", "expand"]},
        },
        "semantic_context": {
            "concept": "growth",
        },
        "identity_runtime_state": "IDENTITY_RUNTIME_STABLE",
        "identity_runtime_continuity": 0.95,
        "contradiction_review_required": False,
        "contradiction_gap": 0.0,
    }
    truth_record = {
        "concept": "growth",
        "final_commit_state": "LOCKED_TRUTH_PRESERVED",
        "claim": "growth preserves verified continuity",
    }

    cache.store(
        "growth",
        runtime_context,
        truth_record,
        "LOCKED_TRUTH_PRESERVED",
        0.95,
        0.99,
    )

    snapshot, reason = cache.lookup(
        "growth",
        runtime_context,
        truth_record,
    )

    assert snapshot is not None
    assert reason == "stable_verified_continuity"
    assert cache.build_report()["cache_hits"] == 1


def test_learning_saturation_freezes_concept():
    report = saturation_detector.evaluate(
        "growth",
        {
            "evidence_saturated": True,
            "dependency_chain_coverage": 0.9908,
            "contradiction_gap": 0.0,
            "transfer_reliability": 0.9,
            "recovery_streak": 2,
        },
    )

    assert report["learning_state"] == "LEARNING_SATURATED"
    assert report["recommended_next_step"] == "freeze_concept"
    assert report["enable_adaptive_training"] is False
