import pytest

from runtime.execution.execution_planner import ExecutionPlanner
from runtime.knowledge import KnowledgeCurrentAuthorityEngine, KnowledgeLifecycleStatus
from runtime.knowledge.current_knowledge_admission import CurrentKnowledgeAdmissionGate
from runtime.planning.current_plan_authority import (
    PlanLifecycleStatus,
    PlanningCurrentAuthorityEngine,
)
from runtime.truth.current_truth_admission import CurrentTruthAdmissionGate
from runtime.truth.truth_current_authority_lifecycle import (
    TruthCurrentAuthorityLifecycleEngine,
)


def _truth_engine(tmp_path):
    return TruthCurrentAuthorityLifecycleEngine(tmp_path / "truth")


def _knowledge_engine(tmp_path, truth_engine):
    return KnowledgeCurrentAuthorityEngine(
        tmp_path / "knowledge",
        truth_admission_gate=CurrentTruthAdmissionGate(truth_engine),
    )


def _active_truth(engine, truth_id, claim_id):
    state = engine.create_active_truth(
        truth_id=truth_id,
        claim_id=claim_id,
        support=engine.truth_support_dependency_graph(
            source_identities=[f"source:{truth_id}"],
            sufficient=True,
        ),
        confidence=0.99,
    )
    engine.persist_current_state(state)
    return state


def _active_knowledge(tmp_path, claim_id="claim:k", suffix="1"):
    truth_engine = _truth_engine(tmp_path / suffix)
    engine = _knowledge_engine(tmp_path / suffix, truth_engine)
    subject = engine.create_subject(
        subject_type="claim",
        claim_id=claim_id,
        scope="arc",
        context_class="planning",
        domain="grid",
    )
    truth = _active_truth(truth_engine, f"truth:{suffix}", claim_id)
    candidate = engine.create_candidate(
        subject,
        {
            "supporting_truths": [truth],
            "source_identities": [f"source:{suffix}"],
            "valid_provenance": True,
        },
    )
    assessment = engine.assess_candidate(candidate, subject)
    decision = engine.commit_knowledge(subject, candidate, assessment)
    state = engine.current_state_from_decision({}, decision)
    engine.persist_current_state(state, lifecycle_decision=decision)
    return engine, state


def _transition_knowledge(engine, state, status):
    review = engine.current_state_from_decision(
        state,
        engine.open_review(state, review_trigger="GOVERNANCE_REVIEW_REQUIRED"),
    )
    if status == KnowledgeLifecycleStatus.UNDER_REVIEW.value:
        engine.persist_current_state(review)
        return review
    if status == KnowledgeLifecycleStatus.INVALIDATED.value:
        decision = engine.invalidate_knowledge(review, reason="planning_test")
        changed = engine.current_state_from_decision(review, decision)
        engine.persist_current_state(changed, lifecycle_decision=decision)
        return changed
    if status == KnowledgeLifecycleStatus.REVALIDATION_REQUIRED.value:
        decision = engine.reassess_under_review(
            review,
            assessment={
                **review["knowledge_assessment"],
                "commitment_predicate_satisfied": False,
            },
            decision_result="REVALIDATION_REQUIRED",
        )
        changed = engine.current_state_from_decision(review, decision)
        engine.persist_current_state(changed, lifecycle_decision=decision)
        return changed
    raise AssertionError(status)


def _planning_engine(tmp_path, knowledge_engine):
    return PlanningCurrentAuthorityEngine(
        tmp_path / "planning",
        knowledge_admission_gate=CurrentKnowledgeAdmissionGate(knowledge_engine),
    )


def _subject(engine, objective="claim:k"):
    return engine.create_subject(
        objective_refs=[objective],
        planning_scope="arc",
        domain="grid",
        context_class="planning",
        constraint_domain="runtime_budget",
    )


def _candidate(engine, subject, *knowledge, source="unit_planner", operations=None):
    return engine.create_candidate(
        subject,
        supporting_knowledge_refs=list(knowledge),
        proposed_operations=operations or [{"operation": "inspect_grid"}],
        source_planner=source,
        plan_instance_context={"run_id": "run_plan_test"},
    )


def _active_plan(engine, subject, candidate, *, min_relevant_knowledge=1):
    assessment = engine.assess_candidate(
        candidate,
        subject,
        min_relevant_knowledge=min_relevant_knowledge,
    )
    decision = engine.commit_plan(subject, candidate, assessment)
    state = engine.current_state_from_decision({}, decision)
    engine.persist_current_state(state, lifecycle_decision=decision)
    return assessment, decision, state


def test_positive_current_knowledge_plan_grants_plan_authority_only(tmp_path):
    knowledge_engine, knowledge = _active_knowledge(tmp_path)
    engine = _planning_engine(tmp_path, knowledge_engine)
    subject = _subject(engine)
    candidate = _candidate(engine, subject, knowledge)
    assessment, decision, state = _active_plan(engine, subject, candidate)

    assert candidate.authority == "NONE"
    assert assessment.plan_authority_predicate_satisfied is True
    assert decision["granted_status"] == PlanLifecycleStatus.ACTIVE.value
    assert state["lifecycle_status"] == PlanLifecycleStatus.ACTIVE.value
    assert state["action_authority"] == "NONE"
    assert state["budget_authority"] == "NONE"
    assert state["execution_authority"] == "NONE"
    assert state["supporting_knowledge_refs"][0]["knowledge_id"] == knowledge["knowledge_id"]


def test_invalidated_knowledge_cannot_support_new_plan_authority(tmp_path):
    knowledge_engine, knowledge = _active_knowledge(tmp_path)
    invalidated = _transition_knowledge(
        knowledge_engine,
        knowledge,
        KnowledgeLifecycleStatus.INVALIDATED.value,
    )
    engine = _planning_engine(tmp_path, knowledge_engine)
    subject = _subject(engine)
    candidate = _candidate(engine, subject, invalidated)
    assessment = engine.assess_candidate(
        candidate,
        subject,
        min_relevant_knowledge=1,
    )

    assert assessment.plan_authority_predicate_satisfied is False
    assert "NONCURRENT_KNOWLEDGE_SUPPORT_REJECTED" in assessment.failures
    with pytest.raises(ValueError):
        engine.commit_plan(subject, candidate, assessment)


def test_unrelated_current_knowledge_is_not_planning_admissible(tmp_path):
    knowledge_engine, knowledge = _active_knowledge(
        tmp_path,
        claim_id="claim:unrelated",
    )
    engine = _planning_engine(tmp_path, knowledge_engine)
    subject = _subject(engine, objective="claim:k")
    candidate = _candidate(engine, subject, knowledge)
    assessment = engine.assess_candidate(
        candidate,
        subject,
        min_relevant_knowledge=1,
    )

    assert assessment.current_knowledge_refs
    assert assessment.plan_authority_predicate_satisfied is False
    assert "IRRELEVANT_KNOWLEDGE_SUPPORT_REJECTED" in assessment.failures


def test_support_loss_opens_review_without_direct_invalidation(tmp_path):
    knowledge_engine, knowledge = _active_knowledge(tmp_path)
    engine = _planning_engine(tmp_path, knowledge_engine)
    subject = _subject(engine)
    candidate = _candidate(engine, subject, knowledge)
    _, _, active = _active_plan(engine, subject, candidate)

    signal = engine.support_change_review_signal(
        active,
        trigger="SUPPORTING_KNOWLEDGE_UNDER_REVIEW",
    )
    review_decision = engine.open_review(
        active,
        trigger="SUPPORTING_KNOWLEDGE_UNDER_REVIEW",
        affected_dependencies=active["supporting_knowledge_refs"],
    )
    under_review = engine.current_state_from_decision(active, review_decision)

    assert signal["authority"] == "NONE"
    assert signal["direct_plan_mutation"] is False
    assert under_review["lifecycle_status"] == PlanLifecycleStatus.UNDER_REVIEW.value


def test_partial_support_loss_can_revalidate_with_fresh_decision(tmp_path):
    knowledge_engine, k1 = _active_knowledge(tmp_path, "claim:k", "k1")
    k2 = dict(k1)
    engine = _planning_engine(tmp_path, knowledge_engine)
    subject = _subject(engine)
    candidate = _candidate(engine, subject, k1, k2)
    _, _, active = _active_plan(engine, subject, candidate, min_relevant_knowledge=2)

    review = engine.current_state_from_decision(
        active,
        engine.open_review(
            active,
            trigger="SUPPORTING_KNOWLEDGE_INVALIDATED",
            affected_dependencies=[k2],
        ),
    )
    fresh_candidate = _candidate(engine, subject, k1)
    fresh_assessment = engine.assess_candidate(
        fresh_candidate,
        subject,
        min_relevant_knowledge=1,
    )
    revalidation = engine.reassess_under_review(
        review,
        assessment=fresh_assessment,
        decision_result=PlanLifecycleStatus.ACTIVE.value,
    )
    restored = engine.current_state_from_decision(review, revalidation)

    assert restored["lifecycle_status"] == PlanLifecycleStatus.ACTIVE.value
    assert restored["current_planning_decision_id"] != active["current_planning_decision_id"]


def test_complete_support_loss_can_invalidate_and_preserve_history(tmp_path):
    knowledge_engine, knowledge = _active_knowledge(tmp_path)
    engine = _planning_engine(tmp_path, knowledge_engine)
    subject = _subject(engine)
    candidate = _candidate(engine, subject, knowledge)
    _, _, active = _active_plan(engine, subject, candidate)
    review = engine.current_state_from_decision(
        active,
        engine.open_review(active, trigger="SUPPORTING_KNOWLEDGE_INVALIDATED"),
    )
    failed = engine.assess_candidate(
        _candidate(engine, subject),
        subject,
        min_relevant_knowledge=1,
    )
    revalidation_required = engine.current_state_from_decision(
        review,
        engine.reassess_under_review(review, assessment=failed),
    )
    invalidated = engine.current_state_from_decision(
        revalidation_required,
        engine.invalidate_plan(
            revalidation_required,
            reason="complete_support_loss",
            support_evaluation=failed.to_dict(),
        ),
    )

    assert invalidated["lifecycle_status"] == PlanLifecycleStatus.INVALIDATED.value
    assert invalidated["history"]


def test_supersession_is_explicit_and_does_not_use_recency(tmp_path):
    knowledge_engine, knowledge = _active_knowledge(tmp_path)
    engine = _planning_engine(tmp_path, knowledge_engine)
    subject = _subject(engine)
    _, _, active = _active_plan(engine, subject, _candidate(engine, subject, knowledge))
    replacement_candidate = _candidate(
        engine,
        subject,
        knowledge,
        operations=[{"operation": "inspect_grid_v2"}],
    )
    replacement_assessment = engine.assess_candidate(
        replacement_candidate,
        subject,
        min_relevant_knowledge=1,
    )
    supersession, replacement = engine.supersede_plan(
        active,
        replacement_subject=subject,
        replacement_candidate=replacement_candidate,
        replacement_assessment=replacement_assessment,
        reason="better_governed_realization",
    )

    old = engine.current_state_from_decision(active, supersession)
    new = engine.current_state_from_decision({}, replacement)
    assert old["lifecycle_status"] == PlanLifecycleStatus.SUPERSEDED.value
    assert new["lifecycle_status"] == PlanLifecycleStatus.ACTIVE.value
    assert replacement["supersedes_plan_id"] == active["plan_id"]


def test_persisted_active_replay_and_stale_decision_are_rejected(tmp_path):
    knowledge_engine, knowledge = _active_knowledge(tmp_path)
    engine = _planning_engine(tmp_path, knowledge_engine)
    subject = _subject(engine)
    _, _, active = _active_plan(engine, subject, _candidate(engine, subject, knowledge))
    replay = dict(active)
    invalidated = engine.current_state_from_decision(
        active,
        engine.invalidate_plan(active, reason="test_invalidation"),
    )
    engine.persist_current_state(invalidated)

    assert engine.is_plan_current(replay)["is_current_plan"] is False
    assert engine.is_plan_current(replay)["reason"] == "CURRENT_PLAN_NOT_ACTIVE"
    with pytest.raises(ValueError):
        engine.current_state_from_decision(invalidated, {
            **replay,
            "authority": engine.authority,
            "planning_decision_id": replay["current_planning_decision_id"],
            "decision_fingerprint": replay["planning_decision_fingerprint"],
            "granted_status": PlanLifecycleStatus.ACTIVE.value,
        })


def test_cross_plan_and_cross_objective_decisions_are_rejected(tmp_path):
    knowledge_engine, knowledge = _active_knowledge(tmp_path)
    engine = _planning_engine(tmp_path, knowledge_engine)
    subject_a = _subject(engine, "claim:k")
    subject_b = _subject(engine, "claim:other")
    _, decision_a, active_a = _active_plan(
        engine,
        subject_a,
        _candidate(engine, subject_a, knowledge),
    )
    candidate_b = _candidate(engine, subject_b)
    assessment_b = engine.assess_candidate(candidate_b, subject_b)
    decision_b = engine.commit_plan(subject_b, candidate_b, assessment_b)

    with pytest.raises(ValueError):
        engine.current_state_from_decision(active_a, decision_b)
    assert decision_a["plan_id"] != decision_b["plan_id"]


def test_executionplanner_materializes_run_plan_as_current_plan_without_execution_authority():
    plan = ExecutionPlanner().build_authoritative_run_plan(
        run_id="run_planning_authority",
        task_files=["task_a.json"],
        selected_mode="adaptive",
        declared_budget={
            "max_active_routes": 6,
            "max_reasoning_depth": 2,
            "max_dependency_depth": 2,
        },
    )

    assert plan["canonical_planning_authority_owner"] == "planning_current_authority_engine"
    assert plan["planning_authority_count"] == 1
    assert plan["plan_lifecycle_status"] == PlanLifecycleStatus.ACTIVE.value
    assert plan["plan_candidate"]["authority"] == "NONE"
    assert plan["planning_decision"]["authority"] == "PLANNING_CURRENT_AUTHORITY"
    assert plan["action_authority"] == "NONE"
    assert plan["budget_authority"] == "NONE"
    assert plan["execution_authority"] == "NONE"
    assert plan["knowledge_authority_changed"] is False
    assert plan["truth_authority_changed"] is False
