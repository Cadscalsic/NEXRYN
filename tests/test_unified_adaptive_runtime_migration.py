import pytest

from runtime.resource_governance import (
    AdaptiveExecutionGovernor,
    ExecutionContract,
    ExecutionPolicyName,
    GovernorBypassDetector,
    LEGACY_MODE_ALIASES,
    RuntimeSignal,
    RuntimeSignalType,
    run_with_governor,
    render_unified_adaptive_runtime_report,
    resolve_policy,
)


def test_policy_resolution_and_default_policy():
    explicit = resolve_policy("max-accuracy")
    default = resolve_policy()

    assert explicit["resolved_policy"] == ExecutionPolicyName.MAX_ACCURACY
    assert default["resolved_policy"] == ExecutionPolicyName.BALANCED


def test_auto_policy_resolution_is_explicit_and_bounded():
    governor = AdaptiveExecutionGovernor()
    low_profile = governor.profile_task("simple color remapping")
    complex_profile = governor.profile_task("ambiguous topology graph dependency unknown concept")

    low = ExecutionContract.create(policy="AUTO", task_profile=low_profile)
    complex_contract = ExecutionContract.create(policy="AUTO", task_profile=complex_profile)

    assert low.requested_policy == "AUTO"
    assert low.resolved_policy in {ExecutionPolicyName.LOW_LATENCY, ExecutionPolicyName.BALANCED}
    assert complex_contract.resolved_policy in {
        ExecutionPolicyName.BALANCED,
        ExecutionPolicyName.MAX_ACCURACY,
    }
    assert low.resolution_reason == "auto_policy_resolution"


def test_legacy_alias_mapping_and_deprecation_warning():
    for alias, policy in LEGACY_MODE_ALIASES.items():
        contract = ExecutionContract.create(legacy_mode=alias)
        assert contract.resolved_policy == policy
        assert contract.legacy_alias == alias
        assert "deprecated" in contract.alias_warning


def test_unknown_legacy_alias_is_rejected_clearly():
    with pytest.raises(ValueError) as exc:
        ExecutionContract.create(legacy_mode="turbo")

    assert "Supported aliases" in str(exc.value)


def test_policy_resolution_failure_falls_back_to_balanced():
    contract = ExecutionContract.create(policy="not-a-policy")

    assert contract.resolved_policy == ExecutionPolicyName.BALANCED
    assert contract.resolution_reason == "policy_resolution_failed_fallback_balanced"


def test_one_canonical_execution_entry_point_for_policy_and_alias():
    policy_result = run_with_governor({"task_id": "t1", "description": "simple color remapping"}, policy="balanced")
    alias_result = run_with_governor({"task_id": "t2", "description": "simple color remapping"}, legacy_mode="adaptive")

    assert policy_result.task_result["execution_path"] == "unified_adaptive_runtime"
    assert alias_result.task_result["execution_path"] == "unified_adaptive_runtime"
    assert alias_result.execution_contract.resolved_policy == ExecutionPolicyName.BALANCED
    assert alias_result.warnings


def test_no_separate_fast_adaptive_or_deep_pipeline():
    fast = run_with_governor("simple color remapping", legacy_mode="fast")
    adaptive = run_with_governor("simple color remapping", legacy_mode="adaptive")
    deep = run_with_governor("simple color remapping", legacy_mode="deep")

    assert fast.task_result["execution_path"] == adaptive.task_result["execution_path"] == deep.task_result["execution_path"]
    assert fast.unified_report["legacy_branches_used"] == 0
    assert adaptive.unified_report["legacy_branches_used"] == 0
    assert deep.unified_report["legacy_branches_used"] == 0


def test_unified_terminal_state_and_post_execution_handling():
    result = run_with_governor("simple color remapping", policy="balanced")

    assert result.terminal_state == "EXACT_SUCCESS"
    assert result.post_execution_contract["terminal_state"] == "EXACT_SUCCESS"
    assert result.unified_report["post_execution_contract"] == "BOUNDED_AND_DEFERRED"


def test_unified_report_metadata_and_rendering():
    result = run_with_governor("simple color remapping", legacy_mode="adaptive")
    rendered = render_unified_adaptive_runtime_report(result.unified_report)

    assert result.unified_report["UNIFIED_ADAPTIVE_RUNTIME_REPORT"] is True
    assert result.unified_report["requested_policy"] == "adaptive"
    assert result.unified_report["resolved_policy"] == "BALANCED"
    assert result.unified_report["legacy_alias"] == "adaptive"
    assert result.unified_report["governor_status"] == "OPERATIONAL"
    assert "UNIFIED ADAPTIVE RUNTIME REPORT" in rendered


def test_unified_persistence_contracts_for_training_and_diagnostic():
    training = run_with_governor("training task", policy="training")
    diagnostic = run_with_governor("diagnostic task", policy="diagnostic")

    assert training.execution_contract.resolved_policy == ExecutionPolicyName.TRAINING
    assert training.post_execution_contract["persistence_contract"]["contract_type"] == "DELTA_CHECKPOINT"
    assert diagnostic.execution_contract.resolved_policy == ExecutionPolicyName.DIAGNOSTIC
    assert diagnostic.post_execution_contract["reporting_contract"]["projection_name"] == "DIAGNOSTIC"


def test_training_execution_uses_same_adaptive_runtime():
    result = run_with_governor("training curriculum update", policy="training")

    assert result.task_result["execution_path"] == "unified_adaptive_runtime"
    assert result.execution_contract.maintenance_permissions["allow_learning_updates"] is True
    assert result.unified_report["legacy_branches_used"] == 0


def test_diagnostic_execution_uses_same_adaptive_runtime():
    result = run_with_governor("diagnose runtime behavior", policy="diagnostic")

    assert result.task_result["execution_path"] == "unified_adaptive_runtime"
    assert result.execution_contract.diagnostic_permissions["allow_diagnostic_overhead"] is True
    assert result.unified_report["legacy_branches_used"] == 0


def test_tool_selection_is_advisory_in_unified_report():
    result = run_with_governor("simple color remapping", policy="balanced")

    tools = result.unified_report["tool_selection"]
    assert set(tools) == {
        "recommended_tools",
        "governor_approved_tools",
        "activated_tools",
        "rejected_tools",
        "deferred_tools",
    }


def test_governor_approval_required_and_bypass_detection():
    result = run_with_governor("simple color remapping", policy="balanced")
    governor = result.governor

    approved = governor.check_layer_execution_authority("topology_reasoning", "test_call_site")

    assert approved is False
    assert governor.bypass_detector.unauthorized_layer_execution_count == 1
    assert governor.bypass_detector.unauthorized_layers == ["topology_reasoning"]


def test_authorized_layer_execution_does_not_count_as_bypass():
    governor = AdaptiveExecutionGovernor()
    governor.bypass_detector = GovernorBypassDetector()
    governor.execution_contract = ExecutionContract.create(policy="balanced")
    governor.activate_layer("object_tracking")

    assert governor.check_layer_execution_authority("object_tracking") is True
    assert governor.bypass_detector.unauthorized_layer_execution_count == 0


def test_configuration_migration_contract_fields():
    contract = ExecutionContract.create(policy="low-latency")

    assert contract.reporting_requirements["reporting_projection"] == "MINIMAL_RESULT"
    assert contract.persistence_requirements["persistence_requirement"] == "CRITICAL_CHECKPOINT"
    assert contract.termination_preferences["immediate_exact_success"] is True


def test_dashboard_policy_metadata_prefers_policy_over_mode():
    result = run_with_governor("simple color remapping", legacy_mode="deep")
    metadata = result.unified_report["observability_metrics"]

    assert metadata["resolved_policy"] == "MAX_ACCURACY"
    assert metadata["legacy_alias_used"] is True
    assert "mode" not in result.execution_contract.reporting_requirements


def test_exact_success_recoverable_failure_and_budget_exhaustion_parity_paths():
    exact = run_with_governor("simple color remapping", policy="balanced")
    recoverable = run_with_governor(
        "repair task",
        policy="balanced",
        executor=lambda task, governor: {"success": False, "prediction": "best-effort"},
    )
    exhausted = run_with_governor(
        "budget task",
        policy="balanced",
        executor=lambda task, governor: (
            governor.consume_budget("candidates", governor.cognitive_budget.max_candidates + 1)
            or {"success": False, "prediction": "budget-best"}
        ),
    )

    assert exact.terminal_state == "EXACT_SUCCESS"
    assert recoverable.terminal_state in {"BEST_EFFORT_BUDGET_EXHAUSTED", "UNRECOVERABLE_FAILURE", "REPAIR_EXHAUSTED"}
    assert exhausted.terminal_state == "BEST_EFFORT_BUDGET_EXHAUSTED"
    assert exact.task_result["execution_path"] == recoverable.task_result["execution_path"] == exhausted.task_result["execution_path"]


def test_repair_and_candidate_selection_parity_use_same_executor_contract():
    def executor(task, governor):
        governor.publish_signal(RuntimeSignal.create(
            execution_id=governor.execution_contract.contract_id,
            task_id="task",
            signal_type=RuntimeSignalType.LOCALIZED_RESIDUAL,
            source_layer="test",
        ))
        return {"success": True, "prediction": "candidate-a", "selected_candidate": "candidate-a"}

    result = run_with_governor("localized repair task", policy="max-accuracy", executor=executor)

    assert result.task_result["selected_candidate"] == "candidate-a"
    assert result.unified_report["dynamic_layer_activations"] >= 1
    assert result.task_result["execution_path"] == "unified_adaptive_runtime"


def test_full_mode_parity_suite_runs_through_one_runtime():
    tasks = [
        "simple color remapping",
        "rotation and scaling transformation",
        "spatial relation task",
        "topology graph task",
        "multi step dependency task",
        "semantic compilation task",
        "candidate competition task",
        "training execution task",
        "diagnostic failure path task",
    ]
    policies = ["low-latency", "balanced", "max-accuracy", "research", "diagnostic", "training"]

    results = [run_with_governor(task, policy=policies[index % len(policies)]) for index, task in enumerate(tasks)]

    assert all(item.task_result["execution_path"] == "unified_adaptive_runtime" for item in results)
    assert all(item.unified_report["legacy_branches_used"] == 0 for item in results)
    assert all(item.unified_report["unauthorized_bypasses"] == 0 for item in results)


def test_legacy_branch_and_bypass_counts_reach_zero_for_unified_path():
    result = run_with_governor("simple color remapping", policy="balanced")
    metrics = result.unified_report["observability_metrics"]

    assert metrics["legacy_branch_count"] == 0
    assert metrics["mode_specific_branch_count"] == 0
    assert metrics["governor_bypass_count"] == 0
    assert result.unified_report["migration_status"] == "UNIFIED_RUNTIME_ACTIVE"
