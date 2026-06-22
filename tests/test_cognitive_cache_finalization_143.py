from runtime.planning.cache_invalidation_engine import (
    CacheInvalidationEngine,
)
from runtime.planning.cognitive_cache_manager import (
    CognitiveCacheManager,
    CacheEntry,
)
from runtime.planning.runtime_finalization_optimizer import (
    RuntimeFinalizationOptimizer,
)
from runtime.pipeline import AdaptiveCognitivePipeline


def test_concept_cache_entry_reuses_stable_artifacts():

    cache = CognitiveCacheManager(persistence_enabled=False)
    version = cache.concept_version_hash("evidence", "dependency", "context")
    key = cache.concept_key(
        concept_name="LOCKED_TRUTH_PRESERVED",
        evidence_hash="evidence",
        dependency_hash="dependency",
        context_hash="context",
        runtime_version="test",
    )

    cache.store_concept(
        key,
        dependency_chain=["truth", "stable"],
        explanation_path=[{"step": "preserved"}],
        truth_commit_result={"truth": "preserved"},
    )

    cached = cache.lookup_concept(key)
    partial = cache.partial_lookup(
        key,
        ["dependency_chain", "truth_commit_result"],
    )

    assert isinstance(cached, CacheEntry)
    assert len(version) == 64
    assert cached.dependency_chain == ["truth", "stable"]
    assert partial == {
        "dependency_chain": ["truth", "stable"],
        "truth_commit_result": {"truth": "preserved"},
    }
    assert cache.build_report()["reused_concepts"] == [
        "LOCKED_TRUTH_PRESERVED"
    ]


def test_cache_invalidation_is_selective_and_ignores_telemetry():

    invalidation = CacheInvalidationEngine()

    unchanged = invalidation.should_invalidate(
        {
            "evidence_hash": "e",
            "dependency_hash": "d",
            "context_hash": "c",
            "governance_threshold_hash": "g",
            "runtime_version": "v",
            "telemetry_enabled": False,
        },
        {
            "evidence_hash": "e",
            "dependency_hash": "d",
            "context_hash": "c",
            "governance_threshold_hash": "g",
            "runtime_version": "v",
            "telemetry_enabled": True,
        },
    )
    changed = invalidation.should_invalidate(
        {"evidence_hash": "old"},
        {"evidence_hash": "new"},
    )

    assert unchanged["should_invalidate"] is False
    assert changed["should_invalidate"] is True
    assert "evidence_hash_changed" in changed["reasons"]


def test_concept_cache_persists_to_disk(tmp_path):

    cache_path = tmp_path / "concept_cache.json"
    cache = CognitiveCacheManager(cache_path=cache_path)
    key = cache.concept_key(
        concept_name="COLOR_MAPPING_STABLE",
        evidence_hash="e",
        dependency_hash="d",
        context_hash="c",
        runtime_version="test",
    )
    cache.store_concept(
        key,
        dependency_chain=["color", "mapping"],
    )
    cache.save()

    restored = CognitiveCacheManager(cache_path=cache_path)
    cached = restored.lookup_concept(key)

    assert cache_path.exists()
    assert isinstance(cached, CacheEntry)
    assert cached.dependency_chain == ["color", "mapping"]
    assert restored.build_report()["cache_persistence_enabled"] is True
    assert restored.build_report()["cache_entry_count"] == 1
    assert restored.build_report()["cache_hits"] == 1


def test_cache_refuses_global_invalidation_by_default():

    cache = CognitiveCacheManager(persistence_enabled=False)
    key = cache.concept_key("A", "e", "d", "c", runtime_version="test")
    cache.store_concept(key, dependency_chain=["A"])

    assert cache.invalidate() == 0
    assert cache.lookup_concept(key) is not None


def test_governance_reuses_cached_locked_truth_without_reexecution():

    pipeline = AdaptiveCognitivePipeline()
    pipeline.cognitive_cache_manager = CognitiveCacheManager(
        persistence_enabled=False
    )
    pipeline.prepare_task_run()
    pipeline._dependency_reasoning_concepts = lambda _context: [
        "color_mapping"
    ]
    runtime_context = {
        "evidence_saturated": True,
        "identity_runtime_continuity": 0.97,
        "context_strength": 0.93,
        "dependency_chain_coverage": 0.95,
        "dependency_explanation_quality": 0.94,
        "dependency_coherence_average": 0.88,
        "semantic_abstractions": [{"concept": "color_mapping"}],
    }
    pipeline.runtime.bulk_update_context(runtime_context)
    metadata = pipeline._cache_metadata(runtime_context)
    cache_key = pipeline._governance_cache_key(
        "color_mapping",
        metadata,
    )
    pipeline.cognitive_cache_manager.store_concept(
        cache_key,
        truth_commit_result={
            **runtime_context,
            "final_commit_state": "LOCKED_TRUTH_PRESERVED",
            "governance_report": {"status": "cached"},
        },
    )

    def fail_governance(_context):
        raise AssertionError("governance should be skipped")

    pipeline.runtime_governor.govern = fail_governance

    pipeline.run_governance_cycle()
    context = pipeline.runtime.get_context()

    assert context["governance_reuse_skipped"] is True
    assert context["governance_cache_report"]["cache_state"] == "hit"
    assert pipeline.performance_report()["cache_hits"] == 1


def test_truth_commit_cleanup_removes_stale_dependency_reason():

    pipeline = AdaptiveCognitivePipeline()
    context = {
        "evidence_saturated": True,
        "dependency_chain_coverage": 0.95,
        "dependency_explanation_quality": 0.94,
        "dependency_coherence_average": 0.88,
        "truth_commit": {
            "reasons": [
                "dependency coherence requires more evidence",
                "identity continuity accepted",
            ],
        },
    }

    cleaned = pipeline._cleanup_truth_commit_reasons(context)

    assert cleaned["truth_commit"]["reasons"] == [
        "identity continuity accepted"
    ]


def test_runtime_finalization_optimizer_selects_fast_for_stable_fast_mode():

    class Budget:
        mode = "fast"

    optimizer = RuntimeFinalizationOptimizer()

    mode = optimizer.choose_mode(
        reasoning_budget=Budget(),
        invalidated_concepts=[],
    )
    report = optimizer.fast_report(
        reused_concepts=["STABLE_SEMANTIC_SPINE"],
        started_at=None,
    )

    assert mode == "fast"
    assert report["finalization_mode"] == "fast"
    assert "stable_truth_revalidation" in report["skipped_operations"]
    assert report["reused_concepts"] == ["STABLE_SEMANTIC_SPINE"]


def test_runtime_finalization_optimizer_uses_deep_when_invalidated():

    class Budget:
        mode = "fast"

    optimizer = RuntimeFinalizationOptimizer()

    assert optimizer.choose_mode(
        reasoning_budget=Budget(),
        invalidated_concepts=["IDENTITY_RUNTIME_STABLE"],
    ) == "deep"


def test_fast_finalization_tolerates_missing_world_governance_report():

    pipeline = AdaptiveCognitivePipeline()
    pipeline.prepare_task_run()

    context = pipeline.finalize_runtime_fast()

    assert context["finalization_report"]["runtime_state"] == "completed"
    assert context["runtime_finalization_report"]["finalization_mode"] == "fast"
    assert (
        pipeline.runtime.context["world_governance_report"][
            "finalization_state"
        ]
        == "skipped"
    )
