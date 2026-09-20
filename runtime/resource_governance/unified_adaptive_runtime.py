"""Canonical unified adaptive runtime entry point."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from runtime.resource_governance.adaptive_execution_governor import AdaptiveExecutionGovernor
from runtime.resource_governance.execution_contract import ExecutionContract
from runtime.resource_governance.execution_policy import ExecutionPolicyName
from runtime.resource_governance.governor_authority import GovernorBypassDetector, LegacyModeAudit
from runtime.resource_governance.runtime_signal_monitor import RuntimeSignal, RuntimeSignalType


@dataclass
class UnifiedRuntimeResult:
    task_result: dict[str, Any]
    execution_contract: ExecutionContract
    governor: AdaptiveExecutionGovernor
    task_profile: dict[str, Any]
    initial_plan: dict[str, Any]
    budget_summary: dict[str, Any]
    terminal_state: str
    post_execution_contract: dict[str, Any]
    unified_report: dict[str, Any]
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_result": dict(self.task_result),
            "execution_contract": self.execution_contract.as_dict(),
            "task_profile": dict(self.task_profile),
            "initial_plan": dict(self.initial_plan),
            "budget_summary": dict(self.budget_summary),
            "terminal_state": self.terminal_state,
            "post_execution_contract": dict(self.post_execution_contract),
            "unified_report": dict(self.unified_report),
            "warnings": list(self.warnings),
        }


def run_with_governor(
    task: Any,
    execution_contract: ExecutionContract | None = None,
    policy: str | ExecutionPolicyName | None = None,
    legacy_mode: str | None = None,
    executor: Callable[[Any, AdaptiveExecutionGovernor], dict[str, Any]] | None = None,
) -> UnifiedRuntimeResult:
    warnings: list[str] = []
    try:
        provisional_profile = AdaptiveExecutionGovernor().profile_task(task)
        contract = execution_contract or ExecutionContract.create(
            policy=policy,
            legacy_mode=legacy_mode,
            task_profile=provisional_profile,
        )
    except ValueError:
        raise
    except Exception as exc:
        warnings.append(f"GOVERNOR_INITIALIZATION_FAILED: {exc}")
        contract = ExecutionContract.create(policy=ExecutionPolicyName.BALANCED)

    if contract.alias_warning:
        warnings.append(contract.alias_warning)

    governor = AdaptiveExecutionGovernor(execution_policy=contract.resolved_policy)
    governor.execution_contract = contract
    governor.bypass_detector = GovernorBypassDetector()
    governor.legacy_mode_audit = LegacyModeAudit()
    profile = governor.profile_task(task)
    initial = governor.create_initial_resource_plan(task)
    budget = governor.create_budget(
        profile,
        execution_policy=contract.resolved_policy,
        execution_id=contract.contract_id,
        task_id=_task_id(task),
    )

    if executor is None:
        task_result = _default_task_result(task, contract)
    else:
        task_result = executor(task, governor)
        task_result.setdefault("policy", contract.resolved_policy.value)
        task_result.setdefault("execution_path", "unified_adaptive_runtime")
    terminal_signal = RuntimeSignal.create(
        execution_id=contract.contract_id,
        task_id=_task_id(task),
        signal_type=(
            RuntimeSignalType.EXACT_SUCCESS
            if task_result.get("success", True)
            else RuntimeSignalType.RECOVERABLE_FAILURE
        ),
        source_layer="unified_adaptive_runtime",
        payload={"final_prediction": task_result.get("prediction")},
    )
    governor.publish_signal(terminal_signal)
    if not governor.terminal_state_guard.terminal:
        governor.evaluate_early_termination(
            signal_type="EXACT_SUCCESS" if task_result.get("success", True) else "UNRECOVERABLE_FAILURE"
        )
    governor.build_post_execution_plan(task_profile=profile)
    governor.execute_critical_finalization()
    governor.execute_bounded_finalization()

    report = build_unified_adaptive_runtime_report(governor, contract)
    return UnifiedRuntimeResult(
        task_result=task_result,
        execution_contract=contract,
        governor=governor,
        task_profile=profile.as_dict(),
        initial_plan=initial.as_dict(),
        budget_summary=budget.as_dict(),
        terminal_state=governor.terminal_state_guard.terminal_record.state,
        post_execution_contract=governor.post_execution_plan.as_dict(),
        unified_report=report,
        warnings=warnings,
    )


def build_unified_adaptive_runtime_report(
    governor: AdaptiveExecutionGovernor,
    contract: ExecutionContract,
) -> dict[str, Any]:
    dynamic = governor.build_dynamic_activation_report()
    post = governor.build_post_execution_governance_report()
    closure = governor.build_adaptive_runtime_closure_report()
    bypass = getattr(governor, "bypass_detector", GovernorBypassDetector()).as_dict()
    audit = getattr(governor, "legacy_mode_audit", LegacyModeAudit()).as_dict()
    report = {
        "UNIFIED_ADAPTIVE_RUNTIME_REPORT": True,
        "requested_policy": contract.requested_policy,
        "resolved_policy": contract.resolved_policy.value,
        "legacy_alias": contract.legacy_alias,
        "execution_contract_status": "VALID",
        "governor_status": governor.status,
        "initial_strategy": governor.initial_strategy.value,
        "final_strategy": (
            "MINIMAL_FINALIZATION"
            if governor.terminal_state_guard.minimal_finalization
            else governor.get_current_strategy()
        ),
        "policy_transitions": [],
        "dynamic_layer_activations": len(dynamic["layers_activated_on_demand"]),
        "deescalations": sum(1 for item in governor.deescalation_controller.decisions if item.deescalated),
        "terminal_state": governor.terminal_state_guard.terminal_record.state if governor.terminal_state_guard.terminal_record else None,
        "post_execution_contract": _post_contract_name(post),
        "deferred_work_count": post["deferred_work_count"],
        "result_availability": closure["result_availability"],
        "post_processing_status": closure["post_processing_status"],
        "maintenance_status": closure["maintenance_status"],
        "closure_state": closure["closure_state"],
        "legacy_branches_used": audit["legacy_branch_count"],
        "unauthorized_bypasses": bypass["unauthorized_layer_execution_count"],
        "migration_status": "UNIFIED_RUNTIME_ACTIVE",
        "observability_metrics": {
            "unified_runtime_active": True,
            "execution_contract_valid": True,
            "requested_policy": contract.requested_policy,
            "resolved_policy": contract.resolved_policy.value,
            "legacy_alias_used": contract.legacy_alias is not None,
            "legacy_branch_count": audit["legacy_branch_count"],
            "governor_bypass_count": bypass["unauthorized_layer_execution_count"],
            "mode_specific_branch_count": audit["mode_specific_branch_count"],
            "dynamic_strategy_transition_count": governor.escalation_controller.escalation_count + sum(1 for item in governor.deescalation_controller.decisions if item.deescalated),
            "policy_violation_count": len(governor.post_execution_governor.serialization_governor.ledger.policy_violations or []),
            "post_execution_contract_used": _post_contract_name(post),
            "result_available_time": post["result_available_time"],
            "adaptive_runtime_closed": closure["observability_metrics"]["adaptive_runtime_closed"],
            "result_available_before_maintenance": closure["observability_metrics"]["result_available_before_maintenance"],
            "post_processing_budget_used": closure["observability_metrics"]["post_processing_budget_used"],
            "post_processing_budget_exceeded": closure["observability_metrics"]["post_processing_budget_exceeded"],
            "closure_state": closure["closure_state"],
            "migration_status": "UNIFIED_RUNTIME_ACTIVE",
        },
        "tool_selection": {
            "recommended_tools": [],
            "governor_approved_tools": [],
            "activated_tools": [],
            "rejected_tools": [],
            "deferred_tools": [],
        },
        "bypass_detection": bypass,
        "adaptive_runtime_closure": closure,
    }
    return report


def render_unified_adaptive_runtime_report(report: dict[str, Any]) -> str:
    return "\n".join([
        "==================================================",
        "UNIFIED ADAPTIVE RUNTIME REPORT",
        "==================================================",
        "",
        "Requested Policy:",
        str(report["requested_policy"]),
        "",
        "Resolved Policy:",
        str(report["resolved_policy"]),
        "",
        "Legacy Alias:",
        str(report["legacy_alias"]),
        "",
        "Governor Status:",
        str(report["governor_status"]),
        "",
        "Initial Strategy:",
        str(report["initial_strategy"]),
        "",
        "Final Strategy:",
        str(report["final_strategy"]),
        "",
        "Dynamic Activations:",
        str(report["dynamic_layer_activations"]),
        "",
        "De-escalations:",
        str(report["deescalations"]),
        "",
        "Terminal State:",
        str(report["terminal_state"]),
        "",
        "Post-Execution Contract:",
        str(report["post_execution_contract"]),
        "",
        "Legacy Branches Used:",
        str(report["legacy_branches_used"]),
        "",
        "Unauthorized Bypasses:",
        str(report["unauthorized_bypasses"]),
        "",
        "Migration Status:",
        str(report["migration_status"]),
    ])


def _default_task_result(task: Any, contract: ExecutionContract) -> dict[str, Any]:
    return {
        "success": True,
        "prediction": task.get("output_grid") if isinstance(task, dict) and task.get("output_grid") is not None else task,
        "policy": contract.resolved_policy.value,
        "execution_path": "unified_adaptive_runtime",
    }


def _task_id(task: Any) -> str:
    if isinstance(task, dict) and task.get("task_id"):
        return str(task["task_id"])
    return "task"


def _post_contract_name(post_report: dict[str, Any]) -> str:
    if post_report.get("deferred_work_count", 0):
        return "BOUNDED_AND_DEFERRED"
    return "CRITICAL_ONLY"


__all__ = [
    "UnifiedRuntimeResult",
    "build_unified_adaptive_runtime_report",
    "render_unified_adaptive_runtime_report",
    "run_with_governor",
]
