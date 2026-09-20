from runtime.capability_architecture import (
    ActivationContract,
    ActivationType,
    CapabilityCategory,
    CapabilityContract,
    CapabilityValidator,
    ExecutionPhase,
    HealthContract,
    InputContract,
    OutputContract,
    PostProcessingCategory,
)
from runtime.capability_architecture.health_contract import CapabilityHealthStatus
from runtime.capability_intelligence import (
    CapabilityRecommendationState,
    CapabilityUsageStatistics,
)
from runtime.resource_governance import (
    AdaptiveExecutionGovernor,
    ClosureState,
    ExecutionContract,
    ExecutionPolicyName,
    GovernorBypassDetector,
    MaintenanceWorkItem,
    MaintenanceWorkStatus,
    PostProcessingBudget,
    PostProcessingDecision,
    run_with_governor,
)


def _post_capability(name: str, category: PostProcessingCategory) -> CapabilityContract:
    return CapabilityContract(
        capability_id=name,
        capability_name=name,
        capability_version="1",
        owning_layer=f"{name}_layer",
        category=CapabilityCategory.MAINTENANCE,
        execution_phase=ExecutionPhase.POST_PROCESSING,
        post_processing_category=category,
        synchronous_allowed=category in {
            PostProcessingCategory.CRITICAL_SYNC,
            PostProcessingCategory.BOUNDED_SYNC,
        },
        maximum_synchronous_duration=0.05 if category in {
            PostProcessingCategory.CRITICAL_SYNC,
            PostProcessingCategory.BOUNDED_SYNC,
        } else 0.0,
        critical_completion_required=category == PostProcessingCategory.CRITICAL_SYNC,
        blocks_result_availability=category == PostProcessingCategory.CRITICAL_SYNC,
        safe_to_skip=category != PostProcessingCategory.CRITICAL_SYNC,
        input_contract=InputContract(optional_inputs=("terminal_state",)),
        output_contract=OutputContract(produced_outputs=("maintenance_record",)),
        activation_contract=ActivationContract(activation_type=ActivationType.POST_EXECUTION_ONLY),
        health_contract=HealthContract(health_status=CapabilityHealthStatus.HEALTHY),
    )


def test_capability_contract_requires_explicit_post_processing_limits():
    valid = CapabilityValidator().validate(
        _post_capability("minimal_result_preservation", PostProcessingCategory.CRITICAL_SYNC)
    )
    invalid = _post_capability("bad_sync", PostProcessingCategory.BOUNDED_SYNC)
    invalid.maximum_synchronous_duration = 0.0

    assert valid.valid is True
    assert CapabilityValidator().validate(invalid).errors == (
        "SYNCHRONOUS_CAPABILITY_REQUIRES_DURATION_LIMIT",
    )


def test_complete_execution_plan_contains_post_processing_sections():
    governor = AdaptiveExecutionGovernor()
    capability = _post_capability("knowledge_fabric_integration", PostProcessingCategory.DEFERRED)
    governor.capability_governor.register_capability(capability)

    plan = governor.create_complete_execution_plan()

    assert "knowledge_fabric_integration" in plan.deferred_maintenance


def test_post_processing_budget_is_separate_and_enforced():
    budget = PostProcessingBudget.for_policy(ExecutionPolicyName.LOW_LATENCY)

    assert budget.consume_bounded("compact_report", duration=budget.maximum_sync_seconds + 0.01) is False
    assert budget.decision_ledger[-1]["decision"] == PostProcessingDecision.DEFER.value


def test_result_available_before_deferred_maintenance():
    result = run_with_governor("simple color remapping", policy="balanced")
    closure = result.unified_report["adaptive_runtime_closure"]

    assert closure["terminal_state"] == "EXACT_SUCCESS"
    assert closure["result_availability"] == "AVAILABLE"
    assert closure["maintenance_status"] == "PENDING"
    assert closure["observability_metrics"]["result_available_before_maintenance"] is True


def test_exact_success_closes_with_deferred_maintenance():
    result = run_with_governor("simple color remapping", policy="balanced")

    assert result.unified_report["closure_state"] == ClosureState.CLOSED_WITH_DEFERRED_MAINTENANCE.value
    assert result.unified_report["adaptive_runtime_closure"]["deferred_work_count"] > 0


def test_unchanged_change_triggered_work_is_skipped_not_run():
    governor = AdaptiveExecutionGovernor()
    governor.enter_terminal_state("EXACT_SUCCESS", "test")
    plan = governor.build_post_execution_plan(
        work_types=["domain_constitution_validation"],
        state_versions={"domain": "v1"},
    )

    assert plan.change_triggered_work[0].status == MaintenanceWorkStatus.SKIPPED_UNCHANGED.value
    assert governor.post_execution_governor.decision_counts[PostProcessingDecision.SKIP_UNCHANGED.value] == 1


def test_direct_post_processing_without_plan_counts_as_bypass():
    governor = AdaptiveExecutionGovernor()
    governor.bypass_detector = GovernorBypassDetector()

    assert governor.check_post_processing_authority("full_report_binding", "reporting", "test") is False
    assert governor.bypass_detector.reporting_bypass_count == 1
    assert governor.bypass_detector.unauthorized_layer_execution_count == 1


def test_legacy_alias_uses_same_closure_system():
    result = run_with_governor("simple color remapping", legacy_mode="fast")

    assert result.execution_contract.resolved_policy == ExecutionPolicyName.LOW_LATENCY
    assert result.unified_report["legacy_branches_used"] == 0
    assert result.unified_report["adaptive_runtime_closure"]["legacy_branch_count"] == 0


def test_deferred_maintenance_ledger_is_idempotent_and_recoverable():
    governor = AdaptiveExecutionGovernor()
    item = MaintenanceWorkItem.create(
        execution_id="e1",
        work_type="semantic_memory_consolidation",
        component_name="semantic_memory",
        work_category="DEFERRED",
        trigger_reason="test",
        input_signature="same",
    )
    first = governor.post_execution_governor.ledger.register(item)
    second = governor.post_execution_governor.ledger.register(item)
    governor.post_execution_governor.ledger.mark_failed(first.work_id, "temporary", retryable=True)

    assert first is second
    assert governor.post_execution_governor.ledger.recover_retryable()[0].status == "READY"


def test_capability_intelligence_tracks_post_processing_metrics():
    stats = CapabilityUsageStatistics()
    record = stats.record_usage(
        "knowledge_fabric_integration",
        deferred=True,
        post_processing_metrics={
            "post_processing_cost": 4.0,
            "maintenance_value": 9.0,
            "state_change_frequency": 1,
        },
    )

    assert record.post_processing_cost == 4.0
    assert record.maintenance_value == 9.0
    assert record.state_change_frequency == 1
    assert CapabilityRecommendationState.MAINTENANCE_DEFERRED.value == "MAINTENANCE_DEFERRED"


def test_closure_report_renderer_contains_final_section():
    governor = AdaptiveExecutionGovernor()
    governor.execution_contract = ExecutionContract.create(policy="balanced")
    governor.enter_terminal_state("EXACT_SUCCESS", "test")
    governor.build_post_execution_plan()

    rendered = governor.render_adaptive_runtime_closure_report()

    assert "ADAPTIVE RUNTIME CLOSURE REPORT" in rendered
    assert "Closure State:" in rendered
