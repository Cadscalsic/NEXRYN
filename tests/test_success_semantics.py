from runtime.evaluation.success_semantics import SuccessSemanticsEngine
from runtime.meta.meta_controller import MetaControllerEngine
from runtime.motivation import MotivationSystem
from runtime.reflection.failure_analyzer import FailureAnalyzer


def trusted_residual_context():
    return {
        "predicted_output": [[0, 8], [0, 0]],
        "output_grid": [[0, 8], [0, 2]],
        "world_model_gate_report": {
            "execution_authorized": True,
            "gate_state": "LOCALIZATION_CONFIRMED_EXECUTION",
            "acceptance_state": "EXECUTION_ACCEPTED",
        },
        "execution_integrity_report": {
            "integrity_preserved": True,
        },
        "transformation_localization": {
            "localization_ready": True,
            "localization_confidence": 0.9775,
            "localized_program": [
                {"op": "replace_color", "from": 2, "to": 8}
            ],
        },
        "identity_governance_state": "IDENTITY_GOVERNANCE_STABLE",
        "identity_confidence": 1.0,
        "stable_truth": True,
        "causal_consistency": 1.0,
        "residual_difference_count": 1,
    }


def test_success_semantics_accepts_trusted_residual_execution():
    engine = SuccessSemanticsEngine()
    evaluation, report = engine.apply(
        {
            "accuracy": 0.9796,
            "difference_count": 1,
            "success": False,
            "exact_success": False,
            "partial_success": True,
            "success_state": "PARTIAL_SUCCESS",
        },
        trusted_residual_context(),
    )

    assert evaluation["success_state"] == "SUCCESS_WITH_RESIDUALS"
    assert evaluation["failure_detected"] is False
    assert evaluation["partial_success"] is False
    assert evaluation["episode_completed"] is True
    assert evaluation["retry_allowed"] is False
    assert evaluation["shutdown_mode"] == "fast"
    assert (
        evaluation["termination_reason"]
        == "HIGH_CONFIDENCE_RESIDUAL_ACCEPTANCE"
    )
    assert report["residual_analysis"]["residual_difference_count"] == 1
    assert report["residual_analysis"]["blocks_runtime_termination"] is False


def test_success_with_residuals_does_not_enter_failure_history():
    evaluation, _ = SuccessSemanticsEngine().apply(
        {
            "accuracy": 0.9796,
            "difference_count": 1,
            "success": False,
            "exact_success": False,
            "partial_success": True,
        },
        trusted_residual_context(),
    )
    analyzer = FailureAnalyzer()
    analysis = analyzer.analyze_failure({}, evaluation)

    assert analysis["failure_detected"] is False
    assert analysis["failure_causes"] == []


def test_meta_stops_after_success_with_residuals():
    context = trusted_residual_context()
    context["evaluation_result"] = {
        "success_state": "SUCCESS_WITH_RESIDUALS",
        "accuracy": 0.9796,
        "difference_count": 1,
        "failure_detected": False,
        "episode_completed": True,
    }

    decision = MetaControllerEngine().decide(context)

    assert decision.action == "STOP_AFTER_SUCCESS"
    assert decision.shutdown_mode == "fast"
    assert decision.enable_self_improvement is False
    assert decision.enable_strategy_evolution is False


def test_learning_progress_is_terminal_runtime_shutdown():
    context = trusted_residual_context()
    context["world_model_gate_report"] = {"execution_authorized": False}
    context["transformation_localization"] = {
        "localization_ready": True,
        "localization_confidence": 0.748,
        "localized_program": [{"op": "duplicate_object"}],
    }
    context["dependency_evidence"] = [{"target": "identity_replication"}]

    evaluation, report = SuccessSemanticsEngine().apply(
        {
            "accuracy": 0.84,
            "difference_count": 2,
            "success": False,
            "exact_success": False,
        },
        context,
    )

    assert evaluation["success_state"] == "LEARNING_PROGRESS"
    assert evaluation["termination_reason"] == "NEW_KNOWLEDGE_SIGNAL_RECORDED"
    assert evaluation["failure_detected"] is False
    assert evaluation["episode_completed"] is True
    assert evaluation["retry_allowed"] is False
    assert evaluation["shutdown_mode"] == "fast"
    assert report["background_task_control"]["disabled_tasks"]["self_improvement"] is True

    context["evaluation_result"] = evaluation
    decision = MetaControllerEngine().decide(context)

    assert decision.action == "STOP_AFTER_SUCCESS"
    assert decision.shutdown_mode == "fast"
    assert decision.max_reasoning_depth == 0


def test_motivation_rewards_success_with_residuals_without_penalty():
    context = trusted_residual_context()
    context["evaluation_result"] = {
        "success_state": "SUCCESS_WITH_RESIDUALS",
        "accuracy": 0.9796,
        "difference_count": 1,
        "failure_detected": False,
        "episode_completed": True,
    }

    report = MotivationSystem().evaluate(context)["MOTIVATION_REPORT"]

    assert report["outcome_class"] == "success_with_residuals"
    assert report["reward_score"] >= 0.80
    assert report["penalty_score"] == 0.0


def test_success_semantics_audit_report_shape():
    audit = SuccessSemanticsEngine().build_audit_report()
    required = {
        "module",
        "success_criteria",
        "failure_criteria",
        "exact_success_dependencies",
        "shutdown_dependencies",
        "retry_triggers",
        "learning_triggers",
    }

    assert audit["system"] == "SUCCESS_SEMANTICS_AUDIT_REPORT"
    assert audit["modules"]
    for module in audit["modules"]:
        assert required <= set(module)
