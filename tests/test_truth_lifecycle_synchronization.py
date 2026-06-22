from runtime.governance.cache import GovernanceCache
from runtime.learning.saturation_controller import LearningSaturationController
from runtime.truth import TruthLifecycleSynchronizer


def locked_truth_context():
    return {
        "concept": "growth",
        "final_commit_state": "LOCKED_TRUTH_PRESERVED",
        "identity_runtime_state": "IDENTITY_RUNTIME_STABLE",
        "recovery_state": "STABLE_SEMANTIC_SPINE",
        "contextual_truth_supported": True,
        "contradiction_review_required": False,
        "evidence_saturated": True,
        "dependency_chain_coverage": 0.9908,
        "dependency_explanation_quality": 0.9731,
        "recommended_next_step": "continue_adaptive_training",
        "why": [
            "contradiction requires review",
            "dependency coherence requires more evidence",
            "identity continuity accepted",
        ],
        "how_we_know": [],
        "transfer_reliability": 0.9,
        "recovery_streak": 2,
        "contradiction_gap": 0.0,
    }


def test_truth_lifecycle_synchronizer_freezes_locked_truth():
    report = LearningSaturationController().evaluate(
        "growth",
        locked_truth_context(),
    )
    synchronized = TruthLifecycleSynchronizer().synchronize(
        concept_name="growth",
        runtime_context=locked_truth_context(),
        learning_report=report,
    )

    assert synchronized["recommended_next_step"] == "freeze_concept"
    assert synchronized["truth_validation_mode"] == "CACHE_REUSE"
    assert synchronized["learning_state"] == "LEARNING_SATURATED"
    assert "contradiction requires review" not in synchronized["why"]
    assert "dependency coherence requires more evidence" not in synchronized["why"]
    assert synchronized["TRUTH_LIFECYCLE_REPORT"]["removed_obsolete_reasons"] == [
        "contradiction requires review",
        "dependency coherence requires more evidence",
    ]


def test_governance_cache_report_exposes_cache_reuse_mode(tmp_path):
    cache = GovernanceCache(
        cache_path=tmp_path / "governance_cache.json",
    )
    context = locked_truth_context()
    truth_record = {
        "concept": "growth",
        "final_commit_state": "LOCKED_TRUTH_PRESERVED",
        "claim": "growth is stable",
    }
    cache.store(
        "growth",
        context,
        truth_record,
        "LOCKED_TRUTH_PRESERVED",
        1.0,
        0.99,
    )

    snapshot, reason = cache.lookup("growth", context, truth_record)
    report = cache.build_report()

    assert snapshot is not None
    assert reason == "stable_verified_continuity"
    assert report["cache_hit_rate"] == 1.0
    assert report["truth_validation_mode"] == "CACHE_REUSE"
