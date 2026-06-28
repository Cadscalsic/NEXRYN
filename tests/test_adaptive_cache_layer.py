import json

from runtime.cache import CacheManager
from runtime.cache.cache_serializer import CacheSerializer


def _stable_context(**overrides):
    context = {
        "identity_runtime_state": "IDENTITY_RUNTIME_STABLE",
        "identity_runtime_ready": True,
        "semantic_drift": 0.01,
        "effective_contradiction": 0.01,
        "context_compatibility": 0.95,
        "truth_integrity_preserved": True,
        "failed_gates": [],
        "failed_identity_governance_gates": [],
        "contradiction_review_required": False,
        "ontology_violation": False,
    }
    context.update(overrides)
    return context


def test_cache_loading(tmp_path):
    manager = CacheManager(cache_dir=tmp_path, auto_migrate=False)
    key = manager.key("knowledge", concept="growth")
    manager.put("knowledge", key=key, value={"concept": "growth"})
    manager.flush()

    restored = CacheManager(cache_dir=tmp_path, auto_migrate=False)

    assert restored.get("knowledge", key=key, context=_stable_context()) == {
        "concept": "growth"
    }


def test_cache_migration(tmp_path):
    legacy = tmp_path / "concept_cache.json"
    legacy.write_text(
        json.dumps({
            "entries": [
                {
                    "entry_type": "concept",
                    "key": {
                        "concept_name": "color",
                        "evidence_hash": "e",
                        "dependency_hash": "d",
                        "context_hash": "c",
                        "runtime_version": "r",
                    },
                    "value": {
                        "cache_key": {
                            "concept_name": "color",
                            "evidence_hash": "e",
                            "dependency_hash": "d",
                            "context_hash": "c",
                            "runtime_version": "r",
                        },
                        "dependency_chain": ["color", "identity"],
                        "explanation_path": ["color->identity"],
                        "truth_commit_result": {
                            "decision": "TRUTH_COMMITTED",
                            "final_commit_state": "LOCKED_TRUTH_PRESERVED",
                        },
                        "process_semantic_model": {"context": "validated"},
                    },
                }
            ]
        }),
        encoding="utf-8",
    )

    manager = CacheManager(cache_dir=tmp_path, auto_migrate=True)

    assert manager.migration_completed is True
    assert (tmp_path / "truth_cache.json").exists()
    assert (tmp_path / "dependency_snapshot_cache.json").exists()
    assert (tmp_path / ".adaptive_cache_migrated").exists()


def test_cache_manager_init_does_not_migrate_legacy_cache_by_default(tmp_path):
    legacy = tmp_path / "concept_cache.json"
    legacy.write_text(json.dumps({"entries": []}), encoding="utf-8")

    manager = CacheManager(cache_dir=tmp_path)

    assert manager.legacy_cache_detected is True
    assert manager.legacy_cache_migration_skipped is True
    assert manager.cache_boot_loaded is False
    assert manager.cache_boot_skipped is True
    assert not (tmp_path / ".adaptive_cache_migrated").exists()


def test_cache_manager_init_does_not_read_large_cache_files(tmp_path):
    cache_file = tmp_path / "knowledge_cache.json"
    cache_file.write_text(
        json.dumps({"entries": {"heavy": {"value": {"x": 1}}}}),
        encoding="utf-8",
    )

    manager = CacheManager(cache_dir=tmp_path)

    assert manager.caches["knowledge"].loaded is False


def test_cache_invalidation(tmp_path):
    manager = CacheManager(cache_dir=tmp_path, auto_migrate=False)
    key = manager.key("knowledge", concept="growth")
    manager.put("knowledge", key=key, value={"concept": "growth"})

    value = manager.get(
        "knowledge",
        key=key,
        context=_stable_context(identity_runtime_state="IDENTITY_RUNTIME_UNSTABLE"),
    )

    assert value is None
    assert manager.report()["invalidated_entries"] == 1


def test_truth_reuse(tmp_path):
    manager = CacheManager(cache_dir=tmp_path, auto_migrate=False)
    key = manager.key("truth", concept="color", truth_signature="t")
    manager.put(
        "truth",
        key=key,
        value={
            "decision": "TRUTH_COMMITTED",
            "final_commit_state": "LOCKED_TRUTH_PRESERVED",
        },
    )

    assert manager.get("truth", key=key, context=_stable_context()) is not None
    assert manager.report()["truth_hits"] == 1


def test_strategy_reuse(tmp_path):
    manager = CacheManager(cache_dir=tmp_path, auto_migrate=False)
    key = manager.key("strategy", concept="dup", strategy_signature="s")
    manager.put("strategy", key=key, value={"validated": True})

    assert manager.get("strategy", key=key, context=_stable_context()) == {
        "validated": True
    }


def test_program_reuse(tmp_path):
    manager = CacheManager(cache_dir=tmp_path, auto_migrate=False)
    key = manager.key("program", concept="dup", program_signature="p")
    manager.put("program", key=key, value={"steps": [{"op": "copy"}]})

    assert manager.get("program", key=key, context=_stable_context())[
        "steps"
    ][0]["op"] == "copy"


def test_dependency_snapshot_reuse(tmp_path):
    manager = CacheManager(cache_dir=tmp_path, auto_migrate=False)
    key = manager.key("dependency_snapshot", concept="color")
    manager.put(
        "dependency_snapshot",
        key=key,
        value={
            "concept": "color",
            "snapshot_state": "ACTIVE",
            "truth_state": "LOCKED_TRUTH_PRESERVED",
            "dependency_chain_depth": 2,
            "dependency_chain_coverage": 0.95,
            "dependency_coherence": 0.9,
            "links_loaded": 2,
            "links_used": 2,
            "explanation_path_summary": ["a", "b"],
            "dependency_signature": "d",
            "identity_runtime_state": "IDENTITY_RUNTIME_STABLE",
            "contextual_truth_supported": True,
            "reuse_count": 0,
        },
    )

    assert manager.get(
        "dependency_snapshot",
        key=key,
        context=_stable_context(),
    )["dependency_coherence"] == 0.9


def test_context_world_model_and_semantic_reuse(tmp_path):
    manager = CacheManager(cache_dir=tmp_path, auto_migrate=False)
    for cache_type in ["context", "world_model", "semantic"]:
        key = manager.key(cache_type, concept="color")
        manager.put(cache_type, key=key, value={"cache_type": cache_type})
        assert manager.get(cache_type, key=key, context=_stable_context())[
            "cache_type"
        ] == cache_type


def test_cache_compaction(tmp_path):
    manager = CacheManager(cache_dir=tmp_path, auto_migrate=False)
    key = manager.key("knowledge", concept="heavy")
    manager.put(
        "knowledge",
        key=key,
        value={
            "concept": "heavy",
            "simulation_trace": list(range(100)),
            "input_grid": [[1] * 10] * 10,
        },
    )

    report = manager.compact()

    assert report["system"] == "adaptive_cache_compaction"
    assert report["compaction_ratio"] <= 1.0


def test_cache_serializer_summarizes_counterfactual_candidates():
    serializer = CacheSerializer()
    compact = serializer.compact({
        "counterfactual_candidates": [
            {
                "direction": "up",
                "prediction_accuracy": 0.51,
                "predicted_grid": [[1]],
            },
            {
                "direction": "down",
                "prediction_accuracy": 0.84,
                "operation": "duplicate_object",
                "predicted_grid": [[1], [1]],
            },
        ]
    })

    assert "counterfactual_candidates" not in compact
    assert compact["counterfactual_candidates_summary"] == {
        "candidate_count": 2,
        "best_accuracy": 0.84,
        "best_direction": "down",
        "best_operation": "duplicate_object",
    }
    assert serializer.report()["heavy_objects_removed"] == 1


def test_legacy_compatibility_migrates_only_once(tmp_path):
    (tmp_path / "concept_cache.json").write_text(
        json.dumps({"entries": []}),
        encoding="utf-8",
    )
    first = CacheManager(cache_dir=tmp_path, auto_migrate=True)
    second = CacheManager(cache_dir=tmp_path, auto_migrate=True)

    assert first.migration_completed is True
    assert second.migrate_legacy_once()["migration_skipped"] is True
