import pytest

from runtime.execution.execution_planner import ExecutionPlanner
from runtime.goals.current_goal_authority import GoalCurrentAuthorityEngine
from runtime.intent.current_intent_authority import (
    INTENT_SOURCES,
    IntentCurrentAuthorityEngine,
    IntentLifecycleStatus,
)
from runtime.knowledge import KnowledgeCurrentAuthorityEngine, KnowledgeLifecycleStatus
from runtime.knowledge.current_knowledge_admission import CurrentKnowledgeAdmissionGate
from runtime.truth.current_truth_admission import CurrentTruthAdmissionGate
from runtime.truth.truth_current_authority_lifecycle import (
    TruthCurrentAuthorityLifecycleEngine,
)


def _truth_engine(tmp_path):
    return TruthCurrentAuthorityLifecycleEngine(tmp_path / "truth")


def _active_truth(engine, truth_id="truth:intent", claim_id="intent:purpose"):
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
    state = dict(state)
    state["support_type"] = "truth"
    return state


def _knowledge_engine(tmp_path, truth_engine):
    return KnowledgeCurrentAuthorityEngine(
        tmp_path / "knowledge",
        truth_admission_gate=CurrentTruthAdmissionGate(truth_engine),
    )


def _active_knowledge(tmp_path, claim_id="intent:purpose", suffix="1"):
    truth_engine = _truth_engine(tmp_path / suffix)
    engine = _knowledge_engine(tmp_path / suffix, truth_engine)
    subject = engine.create_subject(
        subject_type="intent_support",
        claim_id=claim_id,
        scope="strategic",
        context_class="intent",
        domain="arc",
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
    state = dict(state)
    state["support_type"] = "knowledge"
    return engine, state


def _transition_knowledge(engine, state):
    clean = dict(state)
    clean.pop("support_type", None)
    review = engine.current_state_from_decision(
        clean,
        engine.open_review(clean, review_trigger="GOVERNANCE_REVIEW_REQUIRED"),
    )
    decision = engine.invalidate_knowledge(review, reason="intent_test")
    changed = engine.current_state_from_decision(review, decision)
    engine.persist_current_state(changed, lifecycle_decision=decision)
    changed = dict(changed)
    changed["support_type"] = "knowledge"
    return changed


def _engine(tmp_path, knowledge_engine=None, truth_engine=None, goal_engine=None):
    return IntentCurrentAuthorityEngine(
        tmp_path / "intent",
        knowledge_admission_gate=CurrentKnowledgeAdmissionGate(knowledge_engine)
        if knowledge_engine is not None
        else CurrentKnowledgeAdmissionGate(),
        truth_admission_gate=CurrentTruthAdmissionGate(truth_engine)
        if truth_engine is not None
        else CurrentTruthAdmissionGate(),
        goal_authority_engine=goal_engine or GoalCurrentAuthorityEngine(tmp_path / "goal"),
    )


def _subject(engine, purpose="intent:purpose", suffix=""):
    return engine.create_subject(
        intent_type="strategic_direction" + suffix,
        purpose=purpose,
        directional_target="increase_reliable_arc_solving",
        scope="strategic",
        domain="arc",
        context_class="adaptive",
        constraint_domain="runtime_governance",
        authority_origin="USER_DIRECTED",
    )


def _proposal(engine, subject, *support, source="USER_DIRECTED", priority_score=None, constraints=None):
    return engine.create_proposal(
        subject,
        source=source,
        support_refs=list(support),
        constraint_refs=constraints
        if constraints is not None
        else [{"constraint_type": "GOVERNANCE_CONSTRAINT", "owner": "governance"}],
        governance_refs=[{"governance_event_id": "gov:intent"}],
        provenance={"origin": "unit_test", "user_request_id": "req:intent"},
        proposal_context={"run_id": "run_a", "task_id": "task_a"},
        priority_score=priority_score,
    )


def _active_intent(engine, subject, proposal, *, min_current_knowledge=0, min_current_truth=0):
    assessment = engine.assess_proposal(
        proposal,
        subject,
        min_current_knowledge=min_current_knowledge,
        min_current_truth=min_current_truth,
    )
    decision = engine.commit_intent(subject, proposal, assessment)
    state = engine.current_state_from_decision({}, decision)
    engine.persist_current_state(
        state,
        lifecycle_decision=decision,
        proposal=proposal.to_dict(),
        assessment=assessment.to_dict(),
    )
    return assessment, decision, state


def test_lawful_intent_authority_positive_control_is_isolated(tmp_path):
    knowledge_engine, knowledge = _active_knowledge(tmp_path)
    engine = _engine(tmp_path, knowledge_engine=knowledge_engine)
    subject = _subject(engine)
    proposal = _proposal(engine, subject, knowledge)
    assessment, decision, state = _active_intent(
        engine,
        subject,
        proposal,
        min_current_knowledge=1,
    )

    assert proposal.authority == "NONE"
    assert assessment.intent_authority_predicate_satisfied is True
    assert decision["authority"] == "INTENT_CURRENT_AUTHORITY"
    assert state["lifecycle_status"] == IntentLifecycleStatus.ACTIVE.value
    assert state["goal_authority"] == "NONE"
    assert state["planning_authority"] == "NONE"
    assert state["action_authority"] == "NONE"
    assert state["budget_authority"] == "NONE"
    assert state["execution_authority"] == "NONE"
    assert state["truth_authority"] == "NONE"
    assert state["knowledge_authority"] == "NONE"
    assert state["capability_authority"] == "NONE"


def test_intent_identity_is_semantic_and_stable_across_runs_support_and_goal_realizations(tmp_path):
    engine = _engine(tmp_path)
    first = _subject(engine)
    second = _subject(engine)
    different = _subject(engine, purpose="intent:preserve_energy")

    assert first.intent_id == second.intent_id
    assert first.to_dict()["identity_excludes_run_id"] is True
    assert first.to_dict()["identity_excludes_task_id"] is True
    assert first.to_dict()["identity_excludes_goal_id"] is True
    assert first.intent_id != different.intent_id


def test_intent_to_goal_produces_proposal_only(tmp_path):
    goal_engine = GoalCurrentAuthorityEngine(tmp_path / "goal")
    engine = _engine(tmp_path, goal_engine=goal_engine)
    subject = _subject(engine)
    proposal = _proposal(engine, subject)
    _, _, active = _active_intent(engine, subject, proposal)

    goal_proposal = engine.propose_goal_from_intent(
        active,
        goal_type="solve_task",
        objective="goal:arc_task",
        target_state="validated_prediction",
    )

    assert goal_proposal["authority"] == "NONE"
    assert goal_proposal["goal_authority"] == "NONE"
    assert goal_proposal["source_intent_id"] == active["intent_id"]
    assert goal_engine.is_goal_current(goal_proposal)["is_current_goal"] is False


def test_goal_can_only_create_intent_proposal_not_active_intent(tmp_path):
    engine = _engine(tmp_path)
    goal = {
        "goal_id": "goal:revealed",
        "current_goal_decision_id": "goal_decision:1",
        "goal_subject": {"scope": "strategic", "domain": "arc"},
    }
    proposal = engine.create_goal_derived_intent_proposal(
        goal,
        intent_type="strategic_direction",
        purpose="intent:revealed_purpose",
    )

    assert proposal.source == "GOAL_DERIVED"
    assert proposal.authority == "NONE"
    assert engine.is_intent_current(proposal.to_dict())["is_current_intent"] is False


def test_noncurrent_knowledge_cannot_support_intent_authority(tmp_path):
    knowledge_engine, knowledge = _active_knowledge(tmp_path)
    invalidated = _transition_knowledge(knowledge_engine, knowledge)
    engine = _engine(tmp_path, knowledge_engine=knowledge_engine)
    subject = _subject(engine)
    proposal = _proposal(engine, subject, invalidated)
    assessment = engine.assess_proposal(
        proposal,
        subject,
        min_current_knowledge=1,
    )

    assert assessment.intent_authority_predicate_satisfied is False
    assert "NONCURRENT_KNOWLEDGE_SUPPORT_REJECTED" in assessment.failures
    with pytest.raises(ValueError):
        engine.commit_intent(subject, proposal, assessment)


def test_priority_negotiation_and_hierarchy_do_not_grant_authority(tmp_path):
    engine = _engine(tmp_path)
    parent_subject = _subject(engine, purpose="intent:parent")
    parent = _proposal(engine, parent_subject, priority_score=1.0)
    child_subject = engine.create_subject(
        intent_type="strategic_direction_child",
        purpose="intent:child",
        directional_target="child_target",
        scope="strategic",
        parent_intent_id=parent_subject.intent_id,
    )
    child = _proposal(engine, child_subject, priority_score=1.0)
    negotiation = engine.negotiate_intents(
        [parent.to_dict(), child.to_dict()],
        recommendation="COEXIST",
    )

    assert parent.authority == "NONE"
    assert child.authority == "NONE"
    assert negotiation["authority"] == "NONE"
    assert engine.is_intent_current(parent.to_dict())["is_current_intent"] is False
    assert engine.is_intent_current(child.to_dict())["is_current_intent"] is False


def test_self_improvement_and_constraint_self_relaxation_fail_closed(tmp_path):
    engine = _engine(tmp_path)
    subject = _subject(engine)
    self_improvement = engine.create_proposal(
        subject,
        source="SELF_IMPROVEMENT_PROPOSED",
        provenance={"origin": "self_improvement_loop"},
    )
    self_assessment = engine.assess_proposal(self_improvement, subject)
    relaxed = _proposal(
        engine,
        subject,
        constraints=[
            {
                "constraint_type": "GOVERNANCE_CONSTRAINT",
                "changed_by": "INTENT_SELF",
                "self_relaxation": True,
            },
            {
                "constraint_type": "USER_CONSTRAINT",
                "rewritten_by": "INTENT",
            },
        ],
    )
    relaxed_assessment = engine.assess_proposal(relaxed, subject)

    assert "SELF_IMPROVEMENT_INTENT_REQUIRES_EXTERNAL_GOVERNANCE" in self_assessment.failures
    assert self_assessment.intent_authority_predicate_satisfied is False
    assert "INTENT_CONSTRAINT_SELF_RELAXATION_REJECTED" in relaxed_assessment.failures
    assert "USER_CONSTRAINT_REWRITE_REJECTED" in relaxed_assessment.failures


def test_lifecycle_review_revalidation_satisfaction_abandonment_and_supersession(tmp_path):
    engine = _engine(tmp_path)
    subject = _subject(engine)
    proposal = _proposal(engine, subject)
    assessment, _, active = _active_intent(engine, subject, proposal)
    review = engine.current_state_from_decision(
        active,
        engine.open_review(active, trigger="GOVERNANCE_CHANGED"),
    )
    restored = engine.current_state_from_decision(
        review,
        engine.reassess_under_review(
            review,
            assessment=assessment,
            decision_result=IntentLifecycleStatus.ACTIVE.value,
        ),
    )
    satisfied = engine.current_state_from_decision(
        restored,
        engine.satisfy_intent(
            restored,
            satisfaction_evidence={"completion_criteria_id": "done:1"},
        ),
    )
    active2 = _active_intent(engine, subject, proposal)[2]
    abandoned = engine.current_state_from_decision(
        active2,
        engine.abandon_intent(active2, reason="user_cancelled"),
    )
    replacement_subject = _subject(engine, purpose="intent:replacement", suffix="_v2")
    replacement_proposal = _proposal(engine, replacement_subject)
    replacement_assessment = engine.assess_proposal(
        replacement_proposal,
        replacement_subject,
    )
    old_super, new_decision = engine.supersede_intent(
        active2,
        replacement_subject=replacement_subject,
        replacement_proposal=replacement_proposal,
        replacement_assessment=replacement_assessment,
        reason="strategic_replacement",
    )
    superseded = engine.current_state_from_decision(active2, old_super)
    replacement = engine.current_state_from_decision({}, new_decision)

    assert review["lifecycle_status"] == IntentLifecycleStatus.UNDER_REVIEW.value
    assert restored["lifecycle_status"] == IntentLifecycleStatus.ACTIVE.value
    assert satisfied["lifecycle_status"] == IntentLifecycleStatus.SATISFIED.value
    assert abandoned["lifecycle_status"] == IntentLifecycleStatus.ABANDONED.value
    assert superseded["lifecycle_status"] == IntentLifecycleStatus.SUPERSEDED.value
    assert replacement["lifecycle_status"] == IntentLifecycleStatus.ACTIVE.value


def test_support_loss_opens_review_without_direct_invalidation(tmp_path):
    knowledge_engine, knowledge = _active_knowledge(tmp_path)
    engine = _engine(tmp_path, knowledge_engine=knowledge_engine)
    subject = _subject(engine)
    proposal = _proposal(engine, subject, knowledge)
    _, _, active = _active_intent(engine, subject, proposal, min_current_knowledge=1)

    signal = engine.support_change_review_signal(active, trigger="SUPPORT_CHANGED")
    review = engine.current_state_from_decision(
        active,
        engine.open_review(
            active,
            trigger="SUPPORT_CHANGED",
            affected_dependencies=active["support_refs"],
        ),
    )

    assert signal["authority"] == "NONE"
    assert signal["direct_intent_mutation"] is False
    assert review["lifecycle_status"] == IntentLifecycleStatus.UNDER_REVIEW.value


def test_persistence_stale_replay_cross_intent_and_cross_scope_controls(tmp_path):
    engine = _engine(tmp_path)
    subject = _subject(engine)
    proposal = _proposal(engine, subject)
    _, decision, active = _active_intent(engine, subject, proposal)
    review = engine.current_state_from_decision(
        active,
        engine.open_review(active, trigger="GOVERNANCE_CHANGED"),
    )
    invalidated = engine.current_state_from_decision(
        review,
        engine.invalidate_intent(review, reason="support_removed"),
    )
    engine.persist_current_state(invalidated)
    other_subject = _subject(engine, purpose="intent:other")
    other_proposal = _proposal(engine, other_subject)
    other_assessment = engine.assess_proposal(other_proposal, other_subject)
    other_decision = engine.commit_intent(other_subject, other_proposal, other_assessment)
    different_scope = engine.create_subject(
        intent_type="strategic_direction",
        purpose="intent:purpose",
        scope="global",
    )

    assert engine.is_intent_current(active)["is_current_intent"] is False
    assert engine.is_intent_current(active)["reason"] == "CURRENT_INTENT_NOT_ACTIVE"
    with pytest.raises(ValueError):
        engine.current_state_from_decision(invalidated, active)
    with pytest.raises(ValueError):
        engine.current_state_from_decision(active, other_decision)
    with pytest.raises(ValueError):
        engine.current_state_from_decision(active, decision)
    assert subject.intent_id != different_scope.intent_id


def test_merge_split_memory_telemetry_and_epistemic_isolation_are_non_authority(tmp_path):
    engine = _engine(tmp_path)
    first = _subject(engine, purpose="intent:first")
    second = _subject(engine, purpose="intent:second", suffix="_second")
    first_state = _active_intent(engine, first, _proposal(engine, first))[2]
    second_state = _active_intent(engine, second, _proposal(engine, second))[2]
    merge = engine.merge_proposal([first_state, second_state], reason="similar_purpose")
    split = engine.split_proposal(first_state, child_purposes=["a", "b"])
    graph = engine.intent_dependency_graph(first_state)

    assert first_state["intent_id"] != second_state["intent_id"]
    assert merge["authority"] == "NONE"
    assert merge["direct_replacement"] is False
    assert split["authority"] == "NONE"
    assert split["children_active"] is False
    assert graph["dependency_graph_authority"] == "NONE"
    assert first_state["truth_authority"] == "NONE"
    assert first_state["knowledge_authority"] == "NONE"
    assert INTENT_SOURCES >= {"USER_DIRECTED", "GOAL_DERIVED", "SELF_IMPROVEMENT_PROPOSED"}


def test_execution_planner_projects_intent_boundary_without_activation(tmp_path):
    plan = ExecutionPlanner().build_authoritative_run_plan(
        run_id="run_intent_boundary",
        task_files=["task_a.json"],
        selected_mode="adaptive",
        cognitive_pipeline="adaptive",
        declared_budget={
            "max_active_routes": 6,
            "max_reasoning_depth": 2,
            "max_dependency_depth": 2,
        },
        intent_state_dir=tmp_path / "intent_boundary",
    )

    assert plan["canonical_intent_authority_owner"] == "intent_current_authority_engine"
    assert plan["intent_authority_count"] == 1
    assert plan["natural_intent_authority_applicability"] == "APPLICABLE"
    assert plan["natural_intent_proposal_count"] == 1
    assert plan["natural_intent_assessment_count"] == 1
    assert plan["natural_intent_authority_invocation_count"] == 1
    assert plan["natural_active_intent_count"] == 1
    assert plan["intent_active_authority"] == "INTENT_CURRENT_AUTHORITY"
    assert plan["intent_cognitive_consumption"] is False
    assert plan["goal_authority_count"] == 1
    assert plan["planning_authority_count"] == 1
