from copy import deepcopy

from core.causal import DependencyEvidenceEngine


KEY = "color_preservation::depends_on::color_behavior"


def evidence(**overrides):
    payload = {
        "task_id": "task_047.json",
        "concept": "color_preservation",
        "dependency": "color_behavior",
        "dependency_type": "contextual_dependency",
        "context": "duplication",
        "supported": True,
        "contradicted": False,
        "confidence": 0.81,
        "transfer_success": True,
        "contradiction_score": 0.12,
        "timestamp": "2026-06-07T00:00:00",
    }
    payload.update(overrides)
    return payload


def test_evidence_recording_does_not_mutate_input():
    engine = DependencyEvidenceEngine()
    payload = evidence()
    original = deepcopy(payload)

    report = engine.record_evidence(KEY, payload)

    assert payload == original
    assert report["support_count"] == 1
    assert report["contradiction_count"] == 0
    assert report["contexts_seen"] == ["duplication"]
    assert report["tasks_seen"] == ["task_047.json"]
    assert report["status"] == "PROVISIONAL"


def test_duplicate_context_and_task_handling():
    engine = DependencyEvidenceEngine()

    engine.record_evidence(KEY, evidence())
    engine.record_evidence(KEY, evidence(confidence=0.82))
    report = engine.analyze_dependency(KEY)

    assert report["support_count"] == 2
    assert report["contexts_seen"] == ["duplication"]
    assert report["tasks_seen"] == ["task_047.json"]


def test_support_transfer_stability_and_contradiction_scores():
    engine = DependencyEvidenceEngine()
    record = engine.get_or_create_record(KEY)
    engine.update_record(record, evidence(confidence=0.8))
    engine.update_record(record, evidence(
        task_id="task_048.json",
        context="translation",
        confidence=0.82,
    ))

    assert engine.compute_support_score(record) > 0.6
    assert engine.compute_transfer_score(record) == 1.0
    assert engine.compute_stability_score(record) > 0.95
    assert engine.compute_contradiction_risk(record) == 0.0
    assert engine.compute_dependency_confidence(record) > 0.7


def test_confidence_classification_validated():
    engine = DependencyEvidenceEngine()

    for index in range(3):
        engine.record_evidence(
            KEY,
            evidence(
                task_id=f"task_{index}.json",
                context=f"context_{index}",
                confidence=0.9,
            ),
        )

    report = engine.analyze_dependency(KEY)

    assert report["status"] == "VALIDATED"
    assert report["recommended_action"] == "USE_FOR_TRUTH_SUPPORT"


def test_ledger_export_import():
    engine = DependencyEvidenceEngine()
    engine.record_evidence(KEY, evidence())
    ledger = engine.export_ledger()

    imported = DependencyEvidenceEngine()
    count = imported.import_ledger(ledger)

    assert count == 1
    assert imported.analyze_dependency(KEY)["support_count"] == 1
    assert imported.context_history[KEY] == ["duplication"]


def test_empty_record_behavior():
    engine = DependencyEvidenceEngine()

    report = engine.analyze_dependency(
        "shape_preservation::depends_on::structural_integrity"
    )

    assert report["support_count"] == 0
    assert report["dependency_confidence"] == 0.375
    assert report["status"] == "BLOCKED"
    assert report["recommended_action"] == "BLOCK_DEPENDENCY"


def test_promoted_dependency_behavior():
    engine = DependencyEvidenceEngine()

    for index in range(5):
        engine.record_evidence(
            KEY,
            evidence(
                task_id=f"task_{index}.json",
                context=f"context_{index}",
                confidence=0.92,
            ),
        )

    report = engine.analyze_dependency(KEY)

    assert report["status"] == "PROMOTED"
    assert report["recommended_action"] == "PROMOTE_DEPENDENCY"
    assert report["dependency_confidence"] >= 0.85


def test_blocked_dependency_behavior():
    engine = DependencyEvidenceEngine()

    for index in range(3):
        engine.record_evidence(
            KEY,
            evidence(
                task_id=f"task_{index}.json",
                supported=False,
                contradicted=True,
                transfer_success=False,
                contradiction_score=0.8,
                confidence=0.2,
            ),
        )

    report = engine.analyze_dependency(KEY)

    assert report["status"] == "BLOCKED"
    assert report["contradiction_risk"] >= 0.6
    assert report["recommended_action"] == "BLOCK_DEPENDENCY"


def test_analyze_many_returns_reports():
    engine = DependencyEvidenceEngine()
    engine.record_evidence(KEY, evidence())

    reports = engine.analyze_many([
        KEY,
        "topology_preservation::depends_on::topology_behavior",
    ])

    assert len(reports) == 2
    assert reports[0]["dependency_key"] == KEY
