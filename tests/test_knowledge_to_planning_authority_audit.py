from pathlib import Path

from core.goals.goal_manager import GoalManager
from runtime.execution.execution_planner import ExecutionPlanner
from runtime.knowledge import (
    CurrentKnowledgeAdmissionGate,
    KnowledgeCurrentAuthorityEngine,
    KnowledgeLifecycleStatus,
)
from runtime.knowledge_optimization.strategy_reuse_engine import (
    KnowledgeStrategyReuseEngine,
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
    candidate = engine.create_candidate(
        subject,
        {
            "supporting_truths": [truth],
            "source_identities": ["source:a"],
            "valid_provenance": True,
        },
    )
    assessment = engine.assess_candidate(candidate, subject)
    decision = engine.commit_knowledge(subject, candidate, assessment)
    state = engine.current_state_from_decision({}, decision)
    engine.persist_current_state(state, lifecycle_decision=decision)
    return engine, state


def _invalidate(engine, state):
    review_decision = engine.open_review(
        state,
        review_trigger="GOVERNANCE_REVIEW_REQUIRED",
    )
    review_state = engine.current_state_from_decision(state, review_decision)
    invalidation = engine.invalidate_knowledge(
        review_state,
        reason="planning_boundary_audit",
    )
    invalidated = engine.current_state_from_decision(review_state, invalidation)
    engine.persist_current_state(invalidated, lifecycle_decision=invalidation)
    return invalidated


def test_current_knowledge_admission_does_not_create_authoritative_run_plan(tmp_path):
    engine, state = _active_knowledge(tmp_path)
    admission = CurrentKnowledgeAdmissionGate(engine).admit_current_knowledge(state)
    assert admission.admitted is True

    plan = ExecutionPlanner().build_authoritative_run_plan(
        run_id="run_planning_boundary",
        task_files=["task_a.json"],
        selected_mode="adaptive",
        declared_budget={
            "max_active_routes": 6,
            "max_reasoning_depth": 2,
            "max_dependency_depth": 2,
        },
    )

    assert plan["planning_authority"] == "AUTHORITATIVE"
    assert plan["plan_origin"] == "main_adaptive_pre_execution_planner"
    assert "knowledge_id" not in plan
    assert "current_knowledge_decision_id" not in plan
    assert "current_knowledge_admission" not in plan


def test_authoritative_plan_consumption_does_not_invoke_execution_when_not_validly_consumable():
    planner = ExecutionPlanner()
    plan = planner.build_authoritative_run_plan(
        run_id="run_plan_no_execution",
        task_files=["task_a.json"],
        selected_mode="adaptive",
        declared_budget={
            "max_active_routes": 6,
            "max_reasoning_depth": 2,
            "max_dependency_depth": 2,
        },
    )
    consumed = planner.consume_finalized_plan(plan, {"run_id": "run_plan_no_execution"})

    assert consumed["orchestrator_consumption_state"] in {
        "CANONICAL_PLAN_CONSUMED",
        "BLOCKED_BY_STALE_PLAN",
    }
    assert consumed.get("execution_invoked", False) is False
    assert consumed["invocation_record_count"] == 0


def test_cross_run_plan_replay_is_blocked_by_plan_identity():
    planner = ExecutionPlanner()
    plan = planner.build_authoritative_run_plan(
        run_id="run_a",
        task_files=["task_a.json"],
        selected_mode="adaptive",
        declared_budget={"max_active_routes": 6, "max_reasoning_depth": 2},
    )
    consumed = planner.consume_finalized_plan(plan, {"run_id": "run_b"})

    assert consumed["orchestrator_consumption_state"] == "BLOCKED_BY_PLAN_IDENTITY"
    assert consumed["failure_reason"] == "CROSS_RUN_PLAN_CONTAMINATION"
    assert consumed["invocation_record_count"] == 0


def test_knowledge_derived_strategy_is_denied_after_source_invalidation(tmp_path):
    engine, active = _active_knowledge(tmp_path)
    invalidated = _invalidate(engine, active)
    strategy = {
        "source_knowledge_id": invalidated["knowledge_id"],
        "source_knowledge_subject_id": invalidated["subject_id"],
        "source_knowledge_decision_id": invalidated["current_knowledge_decision_id"],
        "source_knowledge_fingerprint": invalidated.get("current_state_fingerprint"),
        "shape_similarity": 1.0,
        "context_similarity": 1.0,
        "strategy_confidence": 1.0,
    }

    report = KnowledgeStrategyReuseEngine(
        knowledge_admission_gate=CurrentKnowledgeAdmissionGate(engine),
    ).find_reusable_strategy(
        query={"strategy_memory": strategy},
        memories={"strategy_memory": [strategy]},
    )

    assert report["reuse_existing_strategy"] is False
    assert report["excluded_noncurrent_knowledge_count"] == 1
    assert report["selected_source"] == "reasoning"


def test_existing_goal_manager_has_no_knowledge_dependency_or_lifecycle_decision(tmp_path):
    engine, state = _active_knowledge(tmp_path)
    admission = CurrentKnowledgeAdmissionGate(engine).admit_current_knowledge(state)
    assert admission.admitted is True

    report = GoalManager().run_cycle(
        {
            "task_path": "task_a.json",
            "current_knowledge_inputs": [state],
        }
    )
    dominant = report["dominant_goal"]

    assert dominant["goal_id"] in {"core:preserve_identity", "core:reduce_entropy"}
    assert "source_knowledge_id" not in dominant
    assert "current_knowledge_decision_id" not in dominant
    assert "goal_lifecycle_decision_id" not in dominant


def test_planning_modules_do_not_import_current_knowledge_admission():
    audited_files = [
        Path("runtime/planning/planning_engine.py"),
        Path("runtime/planning/autonomous_runtime_planner.py"),
        Path("runtime/planning/autonomous_cognitive_planner.py"),
        Path("runtime/execution/execution_planner.py"),
        Path("core/goals/goal_manager.py"),
        Path("core/goals/goal_priority.py"),
        Path("core/goals/goal_conflict_resolver.py"),
        Path("runtime/goals/persistent_goal_manager.py"),
        Path("runtime/goals/goal_arbitration.py"),
        Path("runtime/goals/goal_hierarchy_manager.py"),
    ]

    for path in audited_files:
        text = path.read_text(encoding="utf-8")
        assert "CurrentKnowledgeAdmissionGate" not in text
        assert "current_knowledge_admission" not in text
