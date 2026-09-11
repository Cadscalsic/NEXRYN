import pytest

from runtime.adaptive_reuse.adaptive_reuse_layer import AdaptiveReuseLayer
from runtime.cache import CacheManager
from runtime.capabilities.cognitive_capability_orchestrator import (
    CognitiveCapabilityOrchestrator,
)
from runtime.governance.locked_truth_fastpath import LockedTruthFastPath
from runtime.knowledge.cognitive_knowledge_integration_layer import (
    CognitiveKnowledgeIntegrationLayer,
    CognitiveKnowledgeMemory,
)
from runtime.truth.current_truth_admission import CurrentTruthAdmissionGate
from runtime.truth.truth_current_authority_lifecycle import (
    TruthCurrentAuthorityLifecycleEngine,
    TruthLifecycleStatus,
)
from runtime.truth.truth_reuse_engine import TruthReuseEngine
from runtime.cognition.adaptive_reuse_engine import AdaptiveReuseEngine


def _engine(tmp_path):
    return TruthCurrentAuthorityLifecycleEngine(tmp_path)


def _active(engine, truth_id="truth:T1", claim_id="claim:T1"):
    state = engine.create_active_truth(
        truth_id=truth_id,
        claim_id=claim_id,
        support=engine.truth_support_dependency_graph(
            source_identities=["source:A"],
            sufficient=True,
        ),
        confidence=0.99,
    )
    engine.persist_current_state(state)
    return state


def _gate(engine):
    return CurrentTruthAdmissionGate(engine)


def _locked_report(state, **overrides):
    report = {
        **state,
        "final_commit_state": "LOCKED_TRUTH_PRESERVED",
        "decision": "TRUTH_COMMITTED",
        "identity_runtime_state": "IDENTITY_RUNTIME_STABLE",
        "identity_runtime_ready": True,
        "contextual_truth_supported": True,
        "effective_contradiction": 0.01,
        "contradiction_threshold": 0.2,
        "recovery_state": "STABLE_SEMANTIC_SPINE",
        "remaining_recovery_cycles": 0,
        "failed_identity_governance_gates": [],
        "failed_gates": [],
        "contradiction_review_required": False,
    }
    report.update(overrides)
    return report


def test_current_truth_admission_active_control(tmp_path):
    engine = _engine(tmp_path)
    state = _active(engine)

    admission = _gate(engine).admit_current_truth(
        state,
        consumer_scope="test",
    )

    assert admission.admitted is True
    assert admission.admission_state == "CURRENT_TRUTH_ADMITTED"
    assert admission.current_status == TruthLifecycleStatus.ACTIVE.value
    assert admission.authority_source == engine.authority


@pytest.mark.parametrize(
    ("status_builder", "expected_reason"),
    [
        (
            lambda engine, state: engine.current_state_from_decision(
                state,
                engine.open_review(
                    state,
                    review_trigger="GOVERNANCE_REVIEW_REQUIRED",
                ),
            ),
            "DENIED_TRUTH_UNDER_REVIEW",
        ),
        (
            lambda engine, state: _invalidated(engine, state),
            "DENIED_TRUTH_INVALIDATED",
        ),
        (
            lambda engine, state: _revalidation_required(engine, state),
            "DENIED_TRUTH_REVALIDATION_REQUIRED",
        ),
        (
            lambda engine, state: _superseded(engine, state),
            "DENIED_TRUTH_SUPERSEDED",
        ),
    ],
)
def test_current_truth_admission_denies_non_current_statuses(
    tmp_path,
    status_builder,
    expected_reason,
):
    engine = _engine(tmp_path)
    active = _active(engine)
    state = status_builder(engine, active)
    engine.persist_current_state(state)

    admission = _gate(engine).admit_current_truth(state, consumer_scope="test")

    assert admission.admitted is False
    assert admission.admission_reason == expected_reason


def test_historical_active_replay_and_stale_decision_are_denied(tmp_path):
    engine = _engine(tmp_path)
    active = _active(engine)
    old_artifact = dict(active)
    review = engine.open_review(
        active,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
    )
    under_review = engine.current_state_from_decision(active, review)
    engine.persist_current_state(under_review, lifecycle_decision=review)

    replay = _gate(engine).admit_current_truth(old_artifact, consumer_scope="test")

    assert replay.admitted is False
    assert replay.admission_reason == "DENIED_STALE_TRUTH_DECISION"
    with pytest.raises(ValueError, match="out_of_order_truth_decision_rejected"):
        engine.current_state_from_decision(under_review, review)


def test_copied_corrupt_cross_truth_and_cross_claim_are_denied(tmp_path):
    engine = _engine(tmp_path)
    active = _active(engine)
    other = _active(engine, truth_id="truth:T2", claim_id="claim:T2")
    gate = _gate(engine)

    copied = {**active, "truth_id": "truth:COPY"}
    corrupt = {**active, "fingerprint": "corrupt"}

    assert gate.admit_current_truth(copied).admission_reason == (
        "DENIED_TRUTH_CURRENT_AUTHORITY_UNVERIFIED"
    )
    assert gate.admit_current_truth(corrupt).admission_reason == (
        "DENIED_TRUTH_FINGERPRINT_INVALID"
    )
    assert gate.admit_current_truth(
        {**active, "current_truth_decision_id": other["current_truth_decision_id"]}
    ).admission_reason == "DENIED_STALE_TRUTH_DECISION"
    assert gate.admit_current_truth(
        active,
        expected_claim_id="claim:other",
    ).admission_reason == "DENIED_TRUTH_IDENTITY_MISMATCH"


def test_adaptive_reuse_filters_noncurrent_truth_and_preserves_history(tmp_path):
    engine = _engine(tmp_path)
    active = {**_active(engine, "truth:T1", "claim:T1"), "concept": "alpha"}
    invalidated_state = _invalidated(engine, _active(engine, "truth:T2", "claim:T2"))
    engine.persist_current_state(invalidated_state)
    invalidated = {**invalidated_state, "concept": "alpha", "status": "ACTIVE"}
    legacy = {
        "truth_id": "truth:legacy",
        "concept": "alpha",
        "status": "ACTIVE",
        "truth_confidence": 0.99,
    }
    layer = AdaptiveReuseLayer(truth_admission_gate=_gate(engine))
    layer._read_json = lambda path: {"truths": [active, invalidated, legacy]}

    report = layer.evaluate({"concept": "alpha", "task": "alpha truth"})

    assert report["truth_hits"] == 1
    assert report["current_truth_input_count"] == 1
    assert report["excluded_noncurrent_truth_count"] == 2
    assert report["reused_assets"]["truth"]["truth_id"] == "truth:T1"


def test_truth_reuse_filters_noncurrent_truths(tmp_path):
    engine = _engine(tmp_path)
    active = {**_active(engine), "concept": "alpha", "truth_confidence": 0.99}
    invalidated_state = _invalidated(engine, _active(engine, "truth:T2", "claim:T2"))
    engine.persist_current_state(invalidated_state)
    invalidated = {
        **invalidated_state,
        "concept": "alpha",
        "truth_confidence": 0.99,
    }

    result = TruthReuseEngine(admission_gate=_gate(engine)).reuse_truth(
        {"concept": "alpha"},
        truths=[invalidated, active],
        min_relevance=0.6,
    )

    assert result["truth_reused"] is True
    assert result["reused_truth"]["truth_id"] == active["truth_id"]
    assert result["excluded_noncurrent_truth_count"] == 1


def test_locked_truth_fastpath_requires_current_truth(tmp_path):
    engine = _engine(tmp_path)
    active = _active(engine)
    fastpath = LockedTruthFastPath(admission_gate=_gate(engine))

    admitted = fastpath.evaluate("alpha", {"truth_commit_report": _locked_report(active)})
    denied = fastpath.evaluate(
        "alpha",
        {
            "truth_commit_report": _locked_report(
                {
                    "truth_id": "truth:legacy",
                    "truth_state": "LOCKED_TRUTH_PRESERVED",
                }
            )
        },
    )

    assert admitted["fastpath_active"] is True
    assert denied["fastpath_active"] is False
    assert denied["reason"] == "DENIED_TRUTH_CURRENT_AUTHORITY_UNVERIFIED"


def test_ckil_and_capability_ingestion_require_current_truth(tmp_path):
    engine = _engine(tmp_path)
    active = {**_active(engine), "confidence": 0.9}
    invalidated_state = _invalidated(engine, _active(engine, "truth:T2", "claim:T2"))
    engine.persist_current_state(invalidated_state)
    invalidated = {**invalidated_state, "confidence": 0.9}
    gate = _gate(engine)

    ckil = CognitiveKnowledgeIntegrationLayer(
        memory=CognitiveKnowledgeMemory(tmp_path / "ckil.json"),
        truth_admission_gate=gate,
    )
    ckil_report = ckil.build_report(
        truth_report={"validated_truths": [invalidated, active]},
        persist=False,
    )
    capability = CognitiveCapabilityOrchestrator(truth_admission_gate=gate)
    capability_report = capability.build_report(
        runtime_context={"truth_commitments": [invalidated, active]},
        reports={},
    )

    truth_objects = [
        item for item in ckil_report["knowledge_objects"]
        if item["knowledge_type"] == "truth"
    ]
    assert [item["knowledge_id"] for item in truth_objects] == [active["truth_id"]]
    assert [item["truth_id"] for item in capability_report["shared_truths"]] == [
        active["truth_id"]
    ]


def test_missing_identity_and_missing_current_decision_are_denied(tmp_path):
    engine = _engine(tmp_path)
    active = _active(engine)
    gate = _gate(engine)

    assert gate.admit_current_truth({"truth_id": ""}).admission_reason == (
        "DENIED_TRUTH_IDENTITY_MISSING"
    )
    assert gate.admit_current_truth(
        {key: value for key, value in active.items() if key != "current_truth_decision_id"}
    ).admission_reason == "DENIED_TRUTH_DECISION_MISSING"


def test_adaptive_reuse_engine_truth_cache_replay_is_gated(tmp_path):
    engine = _engine(tmp_path / "truth")
    active = {
        **_active(engine),
        "concept": "alpha",
        "decision": "TRUTH_COMMITTED",
        "final_commit_state": "LOCKED_TRUTH_PRESERVED",
    }
    invalidated_state = _invalidated(
        engine,
        _active(engine, "truth:T2", "claim:T2"),
    )
    engine.persist_current_state(invalidated_state)
    invalidated = {
        **invalidated_state,
        "concept": "alpha",
        "decision": "TRUTH_COMMITTED",
        "final_commit_state": "LOCKED_TRUTH_PRESERVED",
    }
    manager = CacheManager(cache_dir=tmp_path / "cache", auto_migrate=False)
    manager.put("truth", key=manager.key("truth", concept="alpha"), value=invalidated)
    reuse = AdaptiveReuseEngine(
        cache_manager=manager,
        truth_admission_gate=_gate(engine),
    )

    denied_report = reuse.evaluate_reuse({
        "concept": "alpha",
        "identity_runtime_state": "IDENTITY_RUNTIME_STABLE",
        "identity_runtime_ready": True,
        "semantic_drift": 0.0,
        "effective_contradiction": 0.0,
        "context_compatibility": 1.0,
        "dependency_compatibility": 1.0,
        "world_model_compatibility": 1.0,
        "truth_integrity_preserved": True,
        "failed_gates": [],
        "failed_identity_governance_gates": [],
        "contradiction_review_required": False,
    })
    admitted_report = reuse.evaluate_reuse({
        "concept": "alpha",
        "identity_runtime_state": "IDENTITY_RUNTIME_STABLE",
        "identity_runtime_ready": True,
        "semantic_drift": 0.0,
        "effective_contradiction": 0.0,
        "context_compatibility": 1.0,
        "dependency_compatibility": 1.0,
        "world_model_compatibility": 1.0,
        "truth_integrity_preserved": True,
        "failed_gates": [],
        "failed_identity_governance_gates": [],
        "contradiction_review_required": False,
        "truth_commitments": [active],
    })

    assert denied_report["truth_hits"] == 0
    assert "truth" not in denied_report["reused_assets"]
    assert admitted_report["truth_hits"] == 1
    assert admitted_report["reused_assets"]["truth"]["truth_id"] == active["truth_id"]


def _invalidated(engine, active):
    review = engine.open_review(
        active,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
    )
    under_review = engine.current_state_from_decision(active, review)
    invalidation = engine.invalidate_truth(
        under_review,
        reason="test_invalidation",
    )
    return engine.current_state_from_decision(under_review, invalidation)


def _revalidation_required(engine, active):
    review = engine.open_review(
        active,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
    )
    under_review = engine.current_state_from_decision(active, review)
    decision = engine.reassess_under_review(
        under_review,
        current_support={"current_support_sufficient": False},
        decision_result="REVALIDATION_REQUIRED",
    )
    return engine.current_state_from_decision(under_review, decision)


def _superseded(engine, active):
    decision, _replacement = engine.supersede_truth(
        active,
        replacement_truth_id=f"{active['truth_id']}:replacement",
        replacement_claim_id=f"{active['claim_id']}:replacement",
        reason="test_supersession",
    )
    return engine.current_state_from_decision(active, decision)
