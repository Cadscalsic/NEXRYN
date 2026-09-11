from runtime.cache import CacheManager
from runtime.cognition.adaptive_reuse_engine import AdaptiveReuseEngine
from runtime.knowledge import (
    CognitiveKnowledgeIntegrationLayer,
    CognitiveKnowledgeMemory,
    CurrentKnowledgeAdmissionGate,
    KnowledgeCurrentAuthorityEngine,
    KnowledgeLifecycleStatus,
)
from runtime.knowledge_optimization.knowledge_reuse_gate import KnowledgeReuseGate
from runtime.knowledge_optimization.strategy_reuse_engine import (
    KnowledgeStrategyReuseEngine,
)
from runtime.truth.current_truth_admission import CurrentTruthAdmissionGate
from runtime.truth.truth_current_authority_lifecycle import (
    TruthCurrentAuthorityLifecycleEngine,
)


def _runtime_context(**overrides):
    context = {
        "concept": "claim:k",
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
    }
    context.update(overrides)
    return context


def _truth_engine(tmp_path):
    return TruthCurrentAuthorityLifecycleEngine(tmp_path / "truth")


def _knowledge_engine(tmp_path, truth_engine):
    return KnowledgeCurrentAuthorityEngine(
        tmp_path / "knowledge",
        truth_admission_gate=CurrentTruthAdmissionGate(truth_engine),
    )


def _active_truth(engine, truth_id="truth:T1", claim_id="claim:k"):
    state = engine.create_active_truth(
        truth_id=truth_id,
        claim_id=claim_id,
        support=engine.truth_support_dependency_graph(
            source_identities=["source:a"],
            sufficient=True,
        ),
        confidence=0.99,
    )
    engine.persist_current_state(state)
    return state


def _active_knowledge(tmp_path):
    truth_engine = _truth_engine(tmp_path)
    engine = _knowledge_engine(tmp_path, truth_engine)
    subject = engine.create_subject(
        subject_type="claim",
        claim_id="claim:k",
        scope="arc",
        context_class="transformation",
        domain="grid",
    )
    truth = _active_truth(truth_engine)
    support = {
        "supporting_truths": [truth],
        "source_identities": ["source:a"],
        "valid_provenance": True,
    }
    candidate = engine.create_candidate(subject, support)
    assessment = engine.assess_candidate(candidate, subject)
    decision = engine.commit_knowledge(subject, candidate, assessment)
    state = engine.current_state_from_decision({}, decision)
    engine.persist_current_state(state, lifecycle_decision=decision)
    return engine, subject, state


def _transition(engine, state, status):
    if status == KnowledgeLifecycleStatus.UNDER_REVIEW.value:
        return engine.current_state_from_decision(
            state,
            engine.open_review(state, review_trigger="GOVERNANCE_REVIEW_REQUIRED"),
        )
    review = engine.current_state_from_decision(
        state,
        engine.open_review(state, review_trigger="GOVERNANCE_REVIEW_REQUIRED"),
    )
    if status == KnowledgeLifecycleStatus.INVALIDATED.value:
        return engine.current_state_from_decision(
            review,
            engine.invalidate_knowledge(review, reason="audit_invalidation"),
        )
    if status == KnowledgeLifecycleStatus.REVALIDATION_REQUIRED.value:
        return engine.current_state_from_decision(
            review,
            engine.reassess_under_review(
                review,
                assessment={**review["knowledge_assessment"], "commitment_predicate_satisfied": False},
                decision_result="REVALIDATION_REQUIRED",
            ),
        )
    if status == KnowledgeLifecycleStatus.SUPERSEDED.value:
        replacement_subject = engine.create_subject(
            subject_type="claim",
            claim_id="claim:replacement",
            scope="arc",
            context_class="transformation",
            domain="grid",
        )
        replacement_candidate = engine.create_candidate(
            replacement_subject,
            {"source_identities": ["source:a"], "valid_provenance": True},
        )
        replacement_assessment = {
            "knowledge_id": replacement_subject.knowledge_id,
            "subject_id": replacement_subject.subject_id,
            "commitment_predicate_satisfied": True,
            "current_truth_ids": [],
            "current_epistemic_assessment_ids": [],
            "current_evidence_ids": [],
        }
        supersession, _ = engine.supersede_knowledge(
            state,
            replacement_subject=replacement_subject,
            replacement_candidate=replacement_candidate,
            replacement_assessment=replacement_assessment,
            reason="audit_supersession",
        )
        return engine.current_state_from_decision(state, supersession)
    raise AssertionError(status)


def test_current_knowledge_authority_controls_non_current_statuses(tmp_path):
    for status in (
        KnowledgeLifecycleStatus.UNDER_REVIEW.value,
        KnowledgeLifecycleStatus.INVALIDATED.value,
        KnowledgeLifecycleStatus.SUPERSEDED.value,
        KnowledgeLifecycleStatus.REVALIDATION_REQUIRED.value,
    ):
        engine, subject, active = _active_knowledge(tmp_path / status)
        state = _transition(engine, active, status)
        engine.persist_current_state(state)

        assert engine.get_current_knowledge_state(subject.knowledge_id)[
            "lifecycle_status"
        ] == status
        assert engine.is_knowledge_current(subject.knowledge_id) is False


def test_historical_active_replay_and_stale_decision_do_not_restore_currentness(tmp_path):
    engine, subject, active = _active_knowledge(tmp_path)
    historical_active = dict(active)
    invalidated = _transition(engine, active, KnowledgeLifecycleStatus.INVALIDATED.value)
    engine.persist_current_state(invalidated)

    assert engine.is_knowledge_current(subject.knowledge_id) is False
    assert historical_active["lifecycle_status"] == KnowledgeLifecycleStatus.ACTIVE.value
    assert engine.get_current_knowledge_state(subject.knowledge_id)[
        "current_knowledge_decision_id"
    ] == invalidated["current_knowledge_decision_id"]


def test_adaptive_reuse_learned_heuristic_cache_uses_current_knowledge_gate(tmp_path):
    authority, subject, active = _active_knowledge(tmp_path / "authority")
    manager = CacheManager(cache_dir=tmp_path / "cache", auto_migrate=False)
    key = manager.key("knowledge", concept="claim:k", variant="stale")
    manager.put(
        "knowledge",
        key=key,
        value={
            "knowledge_id": "knowledge_stale",
            "concept": "claim:k",
            "lifecycle_status": "INVALIDATED",
            "current_knowledge_decision_id": "stale_decision",
            "confidence": 0.99,
        },
    )
    active_key = manager.key("knowledge", concept=active["claim_id"])
    manager.put("knowledge", key=active_key, value={**active, "concept": "claim:k"})
    engine = AdaptiveReuseEngine(
        cache_manager=manager,
        knowledge_admission_gate=CurrentKnowledgeAdmissionGate(authority),
    )

    report = engine.evaluate_reuse(_runtime_context())

    assert report["learned_heuristic_hits"] == 1
    assert report["reused_assets"]["learned_heuristic"]["knowledge_id"] == (
        subject.knowledge_id
    )
    assert report["reused_assets"]["learned_heuristic"][
        "current_knowledge_admission"
    ]["admitted"] is True
    assert report["excluded_noncurrent_knowledge_count"] == 1


def test_knowledge_reuse_gate_does_not_grant_downstream_authority():
    report = KnowledgeReuseGate().evaluate(
        {"reusable_strategy_exists": True},
        {"reuse_existing_strategy": True},
    )

    assert report["skip_deep_reasoning"] is True
    assert "current_knowledge_admission" not in report


def test_strategy_reuse_engine_excludes_stale_knowledge_derived_strategy(tmp_path):
    authority, subject, active = _active_knowledge(tmp_path / "authority")
    stale_strategy = {
        "strategy_id": "strategy_from_stale_knowledge",
        "knowledge_id": "knowledge_stale",
        "lifecycle_status": "INVALIDATED",
        "shape_similarity": 1.0,
        "context_similarity": 1.0,
        "strategy_confidence": 1.0,
    }
    current_strategy = {
        "strategy_id": "strategy_from_current_knowledge",
        "knowledge_id": subject.knowledge_id,
        "subject_id": subject.subject_id,
        "current_knowledge_decision_id": active["current_knowledge_decision_id"],
        "current_state_fingerprint": active["fingerprint"],
        "concept": "claim:k",
        "shape_similarity": 1.0,
        "context_similarity": 1.0,
        "strategy_confidence": 1.0,
    }

    report = KnowledgeStrategyReuseEngine(
        knowledge_admission_gate=CurrentKnowledgeAdmissionGate(authority),
    ).find_reusable_strategy(
        {"concept": "claim:k"},
        {"strategy_memory": [stale_strategy, current_strategy]},
    )

    assert report["reuse_existing_strategy"] is True
    assert report["strategy_candidate"]["knowledge_id"] == subject.knowledge_id
    assert report["strategy_candidate"]["current_knowledge_admission"][
        "admitted"
    ] is True


def test_knowledge_reuse_engine_excludes_noncurrent_knowledge_before_ranking(tmp_path):
    from runtime.reuse.knowledge_reuse_engine import KnowledgeReuseEngine

    authority, subject, active = _active_knowledge(tmp_path / "authority")
    engine = KnowledgeReuseEngine(
        knowledge_admission_gate=CurrentKnowledgeAdmissionGate(authority)
    )
    report = engine.reuse_before_regenerate(
        {"concept": "claim:k"},
        contexts=[
            {
                "context_id": "stale_context",
                "knowledge_id": "knowledge_stale",
                "concept": "claim:k",
                "confidence": 1.0,
            },
            {
                "context_id": "current_context",
                "knowledge_id": subject.knowledge_id,
                "subject_id": subject.subject_id,
                "current_knowledge_decision_id": active[
                    "current_knowledge_decision_id"
                ],
                "current_state_fingerprint": active["fingerprint"],
                "concept": "claim:k",
                "confidence": 0.5,
            },
        ],
    )

    assert report["reused_context"]["context_id"] == "current_context"
    assert report["current_knowledge_input_count"] == 1
    assert report["excluded_noncurrent_knowledge_count"] == 1


def test_ckil_separates_current_and_historical_knowledge_inputs(tmp_path):
    authority, subject, active = _active_knowledge(tmp_path / "authority")
    ckil = CognitiveKnowledgeIntegrationLayer(
        memory=CognitiveKnowledgeMemory(tmp_path / "ckil.json"),
        knowledge_admission_gate=CurrentKnowledgeAdmissionGate(authority),
    )

    report = ckil.build_report(
        memory_report={
            "knowledge_inputs": [
                {
                    "knowledge_id": "knowledge_stale",
                    "current_knowledge_decision_id": "stale",
                    "lifecycle_status": "INVALIDATED",
                },
                {**active, "concept": "claim:k"},
            ]
        },
        persist=False,
    )

    assert report["current_knowledge_input_count"] == 1
    assert report["excluded_noncurrent_knowledge_count"] == 1
    assert report["CURRENT_KNOWLEDGE_INPUTS"][0]["knowledge_id"] == (
        subject.knowledge_id
    )


def test_mixed_currentness_collection_expected_set_is_active_only(tmp_path):
    engine, subject, active = _active_knowledge(tmp_path / "active")
    states = [active]
    for status in (
        KnowledgeLifecycleStatus.INVALIDATED.value,
        KnowledgeLifecycleStatus.UNDER_REVIEW.value,
        KnowledgeLifecycleStatus.SUPERSEDED.value,
        KnowledgeLifecycleStatus.REVALIDATION_REQUIRED.value,
    ):
        other_engine, _, other_active = _active_knowledge(tmp_path / status)
        states.append(_transition(other_engine, other_active, status))

    resolved = engine.get_current_knowledge_state(subject.knowledge_id)
    current = [
        resolved
        for state in states
        if state["knowledge_id"] == subject.knowledge_id
        and resolved is not None
        and resolved["current_knowledge_decision_id"]
        == state["current_knowledge_decision_id"]
        and engine.is_knowledge_current(state["knowledge_id"])
    ]

    assert [item["lifecycle_status"] for item in current] == [
        KnowledgeLifecycleStatus.ACTIVE.value
    ]


def test_fail_closed_inputs_for_current_authority(tmp_path):
    engine, subject, active = _active_knowledge(tmp_path)
    corrupt = dict(active)
    corrupt["fingerprint"] = "corrupt"
    missing_pointer = KnowledgeCurrentAuthorityEngine(tmp_path / "missing")

    assert missing_pointer.get_current_knowledge_state(subject.knowledge_id) is None
    assert engine._fingerprint_valid(corrupt) is False


def test_current_knowledge_does_not_grant_downstream_authority(tmp_path):
    _, _, active = _active_knowledge(tmp_path)

    assert active["planning_authority"] == "NONE"
    assert active["self_improvement_authority"] == "NONE"
    assert active["capability_authority"] == "NONE"
    assert active["runtime_authority"] == "NONE"
    assert active["budget_authority"] == "NONE"
    assert active["execution_authority"] == "NONE"
