from runtime.reuse.knowledge_reuse_engine import KnowledgeReuseEngine


def test_reuse_before_regenerate_uses_stored_context_and_program_caches():
    engine = KnowledgeReuseEngine()
    engine._context_cache = [
        {
            "context_id": "replication_context",
            "concept": "replication",
            "confidence": 0.92,
        }
    ]
    engine._program_cache = [
        {
            "program_id": "program-1",
            "concept": "replication",
            "confidence": 0.96,
            "program": {
                "program_steps": [
                    {"operator": "duplicate_object"},
                ],
            },
            "validation_state": "validated",
            "integrity_verified": True,
        }
    ]

    report = engine.reuse_before_regenerate({"concept": "replication"})

    assert report["reused_context"]["context_id"] == "replication_context"
    assert report["reused_program"]["program_id"] == "program-1"
    assert report["context_hits"] == 1
    assert report["program_hits"] == 1
    assert report["context_misses"] == 0
    assert report["program_misses"] == 0
    assert report["knowledge_reused"] is True


def test_reuse_before_regenerate_records_context_and_program_misses():
    engine = KnowledgeReuseEngine()
    engine._context_cache = []
    engine._program_cache = []

    report = engine.reuse_before_regenerate({"concept": "replication"})

    assert report["reused_context"] == {}
    assert report["reused_program"] == {}
    assert report["context_hits"] == 0
    assert report["program_hits"] == 0
    assert report["context_misses"] == 1
    assert report["program_misses"] == 1
