from runtime.resource_governance import (
    AdaptiveExecutionGovernor,
    ExecutionPolicyName,
    MaintenanceWorkItem,
    MaintenanceWorkCategory,
    PersistenceContractType,
    ReportProjection,
    RuntimeSignal,
    RuntimeSignalType,
    TerminalState,
)


LEGACY_POLICY_MAP = {
    "fast": ExecutionPolicyName.LOW_LATENCY,
    "adaptive": ExecutionPolicyName.BALANCED,
    "deep": ExecutionPolicyName.MAX_ACCURACY,
    "research": ExecutionPolicyName.RESEARCH,
    "diagnostic": ExecutionPolicyName.DIAGNOSTIC,
}


def terminal_governor(policy=ExecutionPolicyName.BALANCED):
    governor = AdaptiveExecutionGovernor(execution_policy=policy)
    profile = governor.profile_task("simple color remapping")
    governor.create_budget(profile, execution_id="exec-1", task_id="task-1")
    governor.enter_terminal_state(TerminalState.EXACT_SUCCESS, "exact_success_confirmed")
    return governor


def test_post_execution_work_classification():
    governor = terminal_governor()

    critical = governor.classify_post_execution_work("preserve_final_prediction")
    deferred = governor.classify_post_execution_work("knowledge_fabric_integration")
    diagnostic = governor.classify_post_execution_work("complete_signal_ledger")
    prohibited = governor.classify_post_execution_work("candidate_expansion")

    assert critical.category == MaintenanceWorkCategory.CRITICAL_SYNC
    assert deferred.category == MaintenanceWorkCategory.DEFERRED
    assert diagnostic.category == MaintenanceWorkCategory.DIAGNOSTIC_ONLY
    assert prohibited.category == MaintenanceWorkCategory.PROHIBITED_AFTER_TERMINAL


def test_critical_sync_execution_makes_result_available():
    governor = terminal_governor()
    governor.build_post_execution_plan()

    completed = governor.execute_critical_finalization()
    status = governor.get_maintenance_status()

    assert len(completed) >= 5
    assert status["task_result_status"] == "EXACT_SUCCESS"
    assert status["result_available_timestamp"] is not None


def test_bounded_sync_timeout_defers_remaining_work():
    governor = terminal_governor()
    plan = governor.build_post_execution_plan(work_types=["compact_execution_summary"])

    completed = governor.execute_bounded_finalization(elapsed=plan.synchronous_budget["seconds"] + 1)

    assert completed == []
    assert governor.get_deferred_work_summary()["pending_count"] >= 1
    assert governor.post_execution_governor.post_success_guard.rejections[-1]["reason"] == "POST_SUCCESS_BUDGET_EXCEEDED"


def test_deferred_work_registration_idempotency_and_duplicate_merging():
    governor = terminal_governor()
    item = MaintenanceWorkItem.create(
        execution_id="exec-1",
        work_type="knowledge_fabric_integration",
        component_name="knowledge_fabric",
        work_category="DEFERRED",
        trigger_reason="heavy_or_noncritical_maintenance",
        input_signature="fabric-v1",
    )

    first = governor.register_deferred_work(item)
    second = governor.register_deferred_work(item)

    assert first.work_id == second.work_id
    assert governor.get_deferred_work_summary()["total_count"] == 1
    assert governor.get_deferred_work_summary()["idempotency_events"]


def test_change_triggered_work_skips_unchanged_and_runs_on_change():
    governor = terminal_governor()
    unchanged = governor.build_post_execution_plan(
        work_types=["domain_constitution_validation"],
        triggers=["EXECUTION_COMPLETED"],
        state_versions={"cognitive_domain_registry": 1},
    )
    changed = governor.build_post_execution_plan(
        work_types=["domain_constitution_validation"],
        triggers=["DOMAIN_REGISTRY_CHANGED"],
        state_versions={"cognitive_domain_registry": 2},
    )

    assert unchanged.change_triggered_work[0].status == "SKIPPED_UNCHANGED"
    assert changed.change_triggered_work[0].status == "PLANNED"


def test_diagnostic_only_work_gating_by_policy():
    balanced = terminal_governor(ExecutionPolicyName.BALANCED)
    diagnostic = terminal_governor(ExecutionPolicyName.DIAGNOSTIC)

    balanced_plan = balanced.build_post_execution_plan(work_types=["complete_signal_ledger"])
    diagnostic_plan = diagnostic.build_post_execution_plan(work_types=["complete_signal_ledger"])

    assert balanced_plan.diagnostic_work[0].status == "SKIPPED_POLICY"
    assert diagnostic_plan.diagnostic_work[0].status == "PLANNED"


def test_prohibited_post_terminal_work_is_cancelled():
    governor = terminal_governor()

    plan = governor.build_post_execution_plan(work_types=["retry", "candidate_expansion"])

    assert len(plan.prohibited_work) == 2
    assert all(item.status == "CANCELLED" for item in plan.prohibited_work)


def test_policy_specific_post_success_contracts():
    low = terminal_governor(ExecutionPolicyName.LOW_LATENCY).build_post_execution_plan()
    balanced = terminal_governor(ExecutionPolicyName.BALANCED).build_post_execution_plan()
    accuracy = terminal_governor(ExecutionPolicyName.MAX_ACCURACY).build_post_execution_plan()
    research = terminal_governor(ExecutionPolicyName.RESEARCH).build_post_execution_plan()
    diagnostic = terminal_governor(ExecutionPolicyName.DIAGNOSTIC).build_post_execution_plan()

    assert low.reporting_contract["projection_name"] == ReportProjection.MINIMAL_RESULT.value
    assert balanced.reporting_contract["projection_name"] == ReportProjection.COMPACT_OPERATIONAL.value
    assert accuracy.reporting_contract["projection_name"] == ReportProjection.STANDARD.value
    assert research.reporting_contract["projection_name"] == ReportProjection.RESEARCH.value
    assert diagnostic.reporting_contract["projection_name"] == ReportProjection.DIAGNOSTIC.value


def test_exact_success_uses_minimal_finalization_and_defers_heavy_work():
    governor = terminal_governor()

    plan = governor.build_post_execution_plan()

    assert governor.terminal_state_guard.minimal_finalization is True
    assert "knowledge_fabric_integration" in [item.work_type for item in plan.deferred_work]
    assert "semantic_memory_consolidation" in [item.work_type for item in plan.deferred_work]


def test_recoverable_failure_preserves_deferred_repair_information():
    governor = AdaptiveExecutionGovernor()
    governor.enter_terminal_state(
        TerminalState.BEST_EFFORT_BUDGET_EXHAUSTED,
        "budget_exhausted",
        deferred_work_requirements=["localized_repair_replay"],
    )

    record = governor.terminal_state_guard.terminal_record

    assert record.deferred_work_requirements == ["localized_repair_replay"]


def test_maintenance_failure_does_not_invalidate_solved_task():
    governor = terminal_governor()
    governor.post_execution_governor.maintenance_failures.append({
        "component": "knowledge_fabric",
        "reason": "optional_integration_failed",
    })
    governor.build_post_execution_plan()

    status = governor.get_maintenance_status()

    assert status["task_result_status"] == "EXACT_SUCCESS"
    assert status["maintenance_status"] == "PARTIALLY_DEFERRED"


def test_state_signature_change_detection():
    governor = terminal_governor()
    first = governor.evaluate_change_triggers(state_versions={"semantic_memory": 1})
    second = governor.evaluate_change_triggers(state_versions={"semantic_memory": 2})

    assert first["signatures"]["semantic_memory"] != second["signatures"]["semantic_memory"]
    assert second["changes"]["semantic_memory"] is True


def test_minimal_report_avoids_full_registry_traversal_and_binding_is_bounded():
    governor = terminal_governor(ExecutionPolicyName.LOW_LATENCY)
    contract = governor.select_report_projection()
    metrics = governor.post_execution_governor.reporting_governor.bind_projection(
        governor.post_execution_governor.reporting_governor.select_projection(ExecutionPolicyName.LOW_LATENCY),
        available_sections={"task_id": "task-1", "terminal_state": "EXACT_SUCCESS"},
    )

    assert contract["projection_name"] == "MINIMAL_RESULT"
    assert "knowledge_fabric" in contract["deferred_sections"]
    assert metrics.source_nodes_visited <= len(contract["required_sections"])
    assert metrics.binding_duration <= contract["max_construction_time"]


def test_persistence_contracts_checkpoint_delta_and_full_save_gating():
    governor = terminal_governor(ExecutionPolicyName.LOW_LATENCY)
    critical = governor.select_persistence_contract(state_changed=False)
    balanced = terminal_governor(ExecutionPolicyName.BALANCED).select_persistence_contract(state_changed=True)
    research = terminal_governor(ExecutionPolicyName.RESEARCH).select_persistence_contract(state_changed=True, shutdown_required=True)

    assert critical["contract_type"] == PersistenceContractType.CRITICAL_CHECKPOINT.value
    assert balanced["contract_type"] == PersistenceContractType.DELTA_CHECKPOINT.value
    assert research["contract_type"] == PersistenceContractType.FULL_STATE_SAVE.value
    assert research["synchronous"] is False


def test_serialization_limits_timeout_and_duplicate_avoidance():
    governor = terminal_governor()
    governor.build_post_execution_plan()

    ok = governor.enforce_serialization_budget(10, 1000, duration=0.01, signature="x")
    duplicate = governor.enforce_serialization_budget(10, 1000, duration=0.01, signature="x")
    too_large = governor.enforce_serialization_budget(10, 10_000_000, duration=0.01, signature="y")
    too_slow = governor.enforce_serialization_budget(10, 1000, duration=10.0, signature="z")

    ledger = governor.post_execution_governor.serialization_governor.ledger
    assert ok is True
    assert duplicate is True
    assert too_large is False
    assert too_slow is False
    assert ledger.duplicate_serialization_avoided == 1
    assert ledger.deferred_serialization_count == 2


def test_deepcopy_policy_enforcement():
    governor = terminal_governor(ExecutionPolicyName.BALANCED)
    diagnostic = terminal_governor(ExecutionPolicyName.DIAGNOSTIC)

    blocked = governor.post_execution_governor.serialization_governor.record_deepcopy(
        1000,
        1_000_000,
        0.5,
        governor.execution_policy.name,
    )
    allowed = diagnostic.post_execution_governor.serialization_governor.record_deepcopy(
        1000,
        1_000_000,
        0.5,
        diagnostic.execution_policy.name,
    )

    assert blocked is False
    assert allowed is True


def test_knowledge_fabric_semantic_memory_domain_and_program_governance():
    governor = terminal_governor()
    plan = governor.build_post_execution_plan(
        work_types=[
            "knowledge_fabric_integration",
            "semantic_memory_consolidation",
            "domain_constitution_validation",
            "program_ecosystem_aggregation",
        ],
        triggers=["PROGRAM_REGISTRY_CHANGED"],
        state_versions={"program_registry": 3},
    )

    assert "knowledge_fabric_integration" in [item.work_type for item in plan.deferred_work]
    assert "semantic_memory_consolidation" in [item.work_type for item in plan.deferred_work]
    domain_item = [item for item in plan.change_triggered_work if item.work_type == "domain_constitution_validation"][0]
    program_item = [item for item in plan.change_triggered_work if item.work_type == "program_ecosystem_aggregation"][0]
    assert domain_item.status == "SKIPPED_UNCHANGED"
    assert program_item.status == "PLANNED"


def test_post_execution_governance_report_and_diagnostics():
    governor = terminal_governor()
    governor.build_post_execution_plan()
    governor.execute_critical_finalization()
    governor.execute_bounded_finalization()

    report = governor.build_post_execution_governance_report(diagnostic=True)
    rendered = governor.render_post_execution_governance_report()

    assert report["POST_EXECUTION_GOVERNANCE_REPORT"] is True
    assert report["terminal_state"] == "EXACT_SUCCESS"
    assert report["deferred_work_count"] >= 1
    assert report["maintenance_status"] == "PARTIALLY_DEFERRED"
    assert "maintenance_work_ledger" in report
    assert "POST-EXECUTION GOVERNANCE REPORT" in rendered


def test_legacy_modes_route_to_governor_contracts():
    projections = {}
    for mode, policy in LEGACY_POLICY_MAP.items():
        governor = terminal_governor(policy)
        projections[mode] = governor.build_post_execution_plan().reporting_contract["projection_name"]

    assert projections["fast"] == "MINIMAL_RESULT"
    assert projections["adaptive"] == "COMPACT_OPERATIONAL"
    assert projections["deep"] == "STANDARD"
    assert projections["research"] == "RESEARCH"
    assert projections["diagnostic"] == "DIAGNOSTIC"
