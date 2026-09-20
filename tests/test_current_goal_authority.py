import pytest

from core.goals.goal_conflict_resolver import GoalConflictResolver
from core.goals.goal_priority import GoalPriorityEngine
from runtime.execution.execution_planner import ExecutionPlanner
from runtime.goals.current_goal_authority import (
    GOAL_SOURCES,
    GoalCurrentAuthorityEngine,
    GoalLifecycleStatus,
)
from runtime.knowledge import KnowledgeCurrentAuthorityEngine, KnowledgeLifecycleStatus
from runtime.knowledge.current_knowledge_admission import CurrentKnowledgeAdmissionGate
from runtime.planning.current_plan_authority import PlanningCurrentAuthorityEngine
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


def _active_knowledge(tmp_path, claim_id="goal:solve_arc", suffix="1"):
    truth_engine = _truth_engine(tmp_path / suffix)
    engine = _knowledge_engine(tmp_path / suffix, truth_engine)
    subject = engine.create_subject(
        subject_type="goal_support",
        claim_id=claim_id,
        scope="arc",
        context_class="goal",
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
    if status == KnowledgeLifecycleStatus.INVALIDATED.value:
        decision = engine.invalidate_knowledge(review, reason="goal_test")
        changed = engine.current_state_from_decision(review, decision)
        engine.persist_current_state(changed, lifecycle_decision=decision)
        return changed
    raise AssertionError(status)


def _goal_engine(tmp_path, knowledge_engine=None):
    gate = (
        CurrentKnowledgeAdmissionGate(knowledge_engine)
        if knowledge_engine is not None
        else CurrentKnowledgeAdmissionGate()
    )
    return GoalCurrentAuthorityEngine(
        tmp_path / "goal",
        knowledge_admission_gate=gate,
    )


def _subject(engine, objective="goal:solve_arc", suffix=""):
    return engine.create_subject(
        goal_type="solve_task" + suffix,
        objective=objective,
        target_state="validated_prediction",
        scope="arc",
        domain="grid",
        context_class="adaptive",
        constraint_domain="runtime_governance",
    )


def _proposal(engine, subject, *support, source="USER_DIRECTED", priority_score=None):
    support_refs = [
        {**dict(row), "support_type": dict(row).get("support_type", "knowledge")}
        for row in support
    ]
    return engine.create_proposal(
        subject,
        source=source,
        support_refs=support_refs,
        constraint_refs=[{"constraint_type": "runtime_governance"}],
        provenance={"origin": "unit_test", "user_request_id": "req:goal"},
        proposal_context={"run_id": "run_a", "task_id": "task_a"},
        priority_score=priority_score,
    )


def _active_goal(engine, subject, proposal, *, min_relevant_knowledge=0):
    assessment = engine.assess_proposal(
        proposal,
        subject,
        min_relevant_knowledge=min_relevant_knowledge,
    )
    decision = engine.commit_goal(subject, proposal, assessment)
    state = engine.current_state_from_decision({}, decision)
    engine.persist_current_state(
        state,
        lifecycle_decision=decision,
        proposal=proposal.to_dict(),
        assessment=assessment.to_dict(),
    )
    return assessment, decision, state


def test_lawful_goal_authority_positive_control_is_isolated(tmp_path):
    knowledge_engine, knowledge = _active_knowledge(tmp_path)
    engine = _goal_engine(tmp_path, knowledge_engine)
    subject = _subject(engine)
    proposal = _proposal(engine, subject, knowledge)
    assessment, decision, state = _active_goal(
        engine,
        subject,
        proposal,
        min_relevant_knowledge=1,
    )

    assert proposal.authority == "NONE"
    assert assessment.goal_authority_predicate_satisfied is True
    assert decision["authority"] == "GOAL_CURRENT_AUTHORITY"
    assert state["lifecycle_status"] == GoalLifecycleStatus.ACTIVE.value
    assert state["planning_authority"] == "NONE"
    assert state["action_authority"] == "NONE"
    assert state["budget_authority"] == "NONE"
    assert state["execution_authority"] == "NONE"
    assert state["truth_authority"] == "NONE"
    assert state["knowledge_authority"] == "NONE"
    assert state["capability_authority"] == "NONE"


def test_goal_identity_is_semantic_and_not_run_or_task_scoped_by_default(tmp_path):
    engine = _goal_engine(tmp_path)
    a = _subject(engine)
    b = _subject(engine)
    c = _subject(engine, objective="goal:improve_efficiency")

    assert a.goal_id == b.goal_id
    assert a.to_dict()["identity_excludes_run_id"] is True
    assert a.to_dict()["identity_excludes_task_id"] is True
    assert a.goal_id != c.goal_id


def test_goal_proposal_priority_and_conflict_do_not_grant_authority(tmp_path):
    engine = _goal_engine(tmp_path)
    subject = _subject(engine)
    proposal = _proposal(engine, subject, priority_score=1.0)
    priority = GoalPriorityEngine().score_goal(
        {
            "goal_id": proposal.goal_id,
            "goal_type": "solve_task",
            "level": "core",
            "priority": 1.0,
            "persistence": 1.0,
            "urgency": 1.0,
        }
    )
    conflict = GoalConflictResolver().resolve(
        [{"goal_id": proposal.goal_id, "goal_type": "solve_task", "status": "active"}]
    )

    assert priority == 1.0
    assert conflict["blocked_goal_ids"] == []
    assert proposal.authority == "NONE"
    assert engine.is_goal_current(proposal.to_dict())["is_current_goal"] is False


def test_noncurrent_knowledge_cannot_support_goal_authority(tmp_path):
    knowledge_engine, knowledge = _active_knowledge(tmp_path)
    invalidated = _transition_knowledge(
        knowledge_engine,
        knowledge,
        KnowledgeLifecycleStatus.INVALIDATED.value,
    )
    engine = _goal_engine(tmp_path, knowledge_engine)
    subject = _subject(engine)
    proposal = _proposal(engine, subject, invalidated)
    assessment = engine.assess_proposal(
        proposal,
        subject,
        min_relevant_knowledge=1,
    )

    assert assessment.goal_authority_predicate_satisfied is False
    assert "NONCURRENT_KNOWLEDGE_SUPPORT_REJECTED" in assessment.failures
    with pytest.raises(ValueError):
        engine.commit_goal(subject, proposal, assessment)


def test_unrelated_current_knowledge_is_not_goal_admissible(tmp_path):
    knowledge_engine, knowledge = _active_knowledge(
        tmp_path,
        claim_id="goal:other",
    )
    engine = _goal_engine(tmp_path, knowledge_engine)
    subject = _subject(engine, objective="goal:solve_arc")
    proposal = _proposal(engine, subject, knowledge)
    assessment = engine.assess_proposal(
        proposal,
        subject,
        min_relevant_knowledge=1,
    )

    assert assessment.current_knowledge_refs
    assert assessment.goal_authority_predicate_satisfied is False
    assert "IRRELEVANT_KNOWLEDGE_SUPPORT_REJECTED" in assessment.failures


def test_support_loss_opens_review_without_direct_goal_mutation(tmp_path):
    knowledge_engine, knowledge = _active_knowledge(tmp_path)
    engine = _goal_engine(tmp_path, knowledge_engine)
    subject = _subject(engine)
    proposal = _proposal(engine, subject, knowledge)
    _, _, active = _active_goal(engine, subject, proposal, min_relevant_knowledge=1)

    signal = engine.support_change_review_signal(
        active,
        trigger="SUPPORTING_KNOWLEDGE_CHANGED",
    )
    review = engine.current_state_from_decision(
        active,
        engine.open_review(
            active,
            trigger="SUPPORTING_KNOWLEDGE_CHANGED",
            affected_dependencies=active["support_refs"],
        ),
    )

    assert signal["authority"] == "NONE"
    assert signal["direct_goal_mutation"] is False
    assert review["lifecycle_status"] == GoalLifecycleStatus.UNDER_REVIEW.value


def test_revalidation_satisfaction_abandonment_and_supersession_are_authoritative(tmp_path):
    engine = _goal_engine(tmp_path)
    subject = _subject(engine)
    proposal = _proposal(engine, subject)
    assessment, _, active = _active_goal(engine, subject, proposal)
    review = engine.current_state_from_decision(
        active,
        engine.open_review(active, trigger="GOVERNANCE_REVIEW_REQUIRED"),
    )
    restored = engine.current_state_from_decision(
        review,
        engine.reassess_under_review(
            review,
            assessment=assessment,
            decision_result=GoalLifecycleStatus.ACTIVE.value,
        ),
    )
    satisfied = engine.current_state_from_decision(
        restored,
        engine.satisfy_goal(
            restored,
            target_state_evidence={"target_state_evidence_id": "e:1"},
        ),
    )

    active2 = _active_goal(engine, subject, proposal)[2]
    abandoned = engine.current_state_from_decision(
        active2,
        engine.abandon_goal(active2, reason="user_cancelled"),
    )
    replacement_subject = _subject(engine, objective="goal:solve_arc_better", suffix="_v2")
    replacement_proposal = _proposal(engine, replacement_subject)
    replacement_assessment = engine.assess_proposal(
        replacement_proposal,
        replacement_subject,
    )
    old_super, new_decision = engine.supersede_goal(
        active2,
        replacement_subject=replacement_subject,
        replacement_proposal=replacement_proposal,
        replacement_assessment=replacement_assessment,
        reason="strategic_replacement",
    )
    superseded = engine.current_state_from_decision(active2, old_super)
    replacement = engine.current_state_from_decision({}, new_decision)

    assert restored["lifecycle_status"] == GoalLifecycleStatus.ACTIVE.value
    assert satisfied["lifecycle_status"] == GoalLifecycleStatus.SATISFIED.value
    assert abandoned["lifecycle_status"] == GoalLifecycleStatus.ABANDONED.value
    assert superseded["lifecycle_status"] == GoalLifecycleStatus.SUPERSEDED.value
    assert replacement["lifecycle_status"] == GoalLifecycleStatus.ACTIVE.value


def test_persistence_and_stale_replay_controls(tmp_path):
    engine = _goal_engine(tmp_path)
    subject = _subject(engine)
    proposal = _proposal(engine, subject)
    _, _, active = _active_goal(engine, subject, proposal)
    review = engine.current_state_from_decision(
        active,
        engine.open_review(active, trigger="GOVERNANCE_REVIEW_REQUIRED"),
    )
    invalidated = engine.current_state_from_decision(
        review,
        engine.invalidate_goal(review, reason="support_removed"),
    )
    engine.persist_current_state(invalidated)

    assert engine.is_goal_current(active)["is_current_goal"] is False
    assert engine.is_goal_current(active)["reason"] == "CURRENT_GOAL_NOT_ACTIVE"
    with pytest.raises(ValueError):
        engine.current_state_from_decision(invalidated, active)


def test_cross_goal_cross_objective_and_cross_scope_attacks_fail(tmp_path):
    engine = _goal_engine(tmp_path)
    subject_a = _subject(engine, objective="goal:a")
    subject_b = _subject(engine, objective="goal:b")
    subject_scope = engine.create_subject(
        goal_type="solve_task",
        objective="goal:a",
        scope="other_scope",
    )
    proposal_a = _proposal(engine, subject_a)
    assessment_a, decision_a, active_a = _active_goal(engine, subject_a, proposal_a)
    proposal_b = _proposal(engine, subject_b)
    assessment_b = engine.assess_proposal(proposal_b, subject_b)

    with pytest.raises(ValueError):
        engine.commit_goal(subject_b, proposal_a, assessment_a)
    with pytest.raises(ValueError):
        engine.current_state_from_decision(active_a, decision_a)
    assert subject_a.goal_id != subject_b.goal_id
    assert subject_a.goal_id != subject_scope.goal_id
    assert assessment_b.goal_authority_predicate_satisfied is True


def test_planner_plan_and_self_improvement_cannot_self_authorize_goals(tmp_path):
    engine = _goal_engine(tmp_path)
    subject = _subject(engine)
    self_improvement = engine.create_proposal(
        subject,
        source="SELF_IMPROVEMENT_PROPOSED",
        provenance={"origin": "training_loop"},
    )
    assessment = engine.assess_proposal(self_improvement, subject)
    assert assessment.goal_authority_predicate_satisfied is False
    assert "SELF_IMPROVEMENT_GOAL_REQUIRES_EXTERNAL_GOVERNANCE" in assessment.failures

    planner_proposal = engine.create_proposal(
        subject,
        source="PLANNING_DERIVED",
        planning_refs=[
            {
                "plan_id": "plan:active",
                "planning_authority": "PLANNING_CURRENT_AUTHORITY",
            }
        ],
        provenance={"origin": "planner", "planning_decision_id": "pd:1"},
    )
    assert planner_proposal.authority == "NONE"
    assert engine.is_goal_current(planner_proposal.to_dict())["is_current_goal"] is False

    plan_engine = PlanningCurrentAuthorityEngine(tmp_path / "planning")
    plan_subject = plan_engine.create_subject(objective_refs=[subject.goal_id])
    plan_candidate = plan_engine.create_candidate(
        plan_subject,
        goal_refs=[planner_proposal.to_dict()],
        source_planner="unit_planner",
    )
    plan_assessment = plan_engine.assess_candidate(plan_candidate, plan_subject)
    plan_decision = plan_engine.commit_plan(
        plan_subject,
        plan_candidate,
        plan_assessment,
    )
    plan_state = plan_engine.current_state_from_decision({}, plan_decision)
    assert plan_state["lifecycle_status"] == "ACTIVE"
    assert engine.is_goal_current(planner_proposal.to_dict())["is_current_goal"] is False


def test_multiple_active_goals_share_one_authority_without_identity_merge(tmp_path):
    engine = _goal_engine(tmp_path)
    first = _subject(engine, objective="goal:first")
    second = _subject(engine, objective="goal:second", suffix="_second")
    first_state = _active_goal(engine, first, _proposal(engine, first))[2]
    second_state = _active_goal(engine, second, _proposal(engine, second))[2]
    engine.persist_current_state(first_state)
    engine.persist_current_state(second_state)

    assert first_state["goal_id"] != second_state["goal_id"]
    assert engine.is_goal_current(first_state)["is_current_goal"] is True
    assert engine.is_goal_current(second_state)["is_current_goal"] is True
    assert GOAL_SOURCES >= {"USER_DIRECTED", "PLANNING_DERIVED", "SELF_IMPROVEMENT_PROPOSED"}


def test_execution_planner_projects_goal_boundary_without_activation():
    plan = ExecutionPlanner().build_authoritative_run_plan(
        run_id="run_goal_boundary",
        task_files=["task_a.json"],
        selected_mode="adaptive",
        cognitive_pipeline="adaptive",
        declared_budget={
            "max_active_routes": 6,
            "max_reasoning_depth": 2,
            "max_dependency_depth": 2,
        },
    )

    assert plan["canonical_goal_authority_owner"] == "goal_current_authority_engine"
    assert plan["goal_authority_count"] == 1
    assert plan["natural_goal_authority_applicability"] == "NOT_APPLICABLE"
    assert plan["current_goal_ids"] == []
    assert plan["goal_active_authority"] == "NONE"
    assert plan["planning_authority_count"] == 1
