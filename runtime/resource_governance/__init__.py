"""Adaptive execution governor foundation."""

from runtime.resource_governance.adaptive_execution_governor import (
    AdaptiveExecutionGovernor,
    ExecutionDecision,
    adaptive_execution_governor,
)
from runtime.resource_governance.execution_plan import ExecutionPlan
from runtime.resource_governance.execution_policy import (
    DEFAULT_EXECUTION_POLICIES,
    ExecutionPolicy,
    ExecutionPolicyName,
)
from runtime.resource_governance.execution_contract import (
    ExecutionContract,
    LEGACY_MODE_ALIASES,
    SUPPORTED_POLICY_ALIASES,
    resolve_policy,
)
from runtime.resource_governance.complexity_estimator import (
    ComplexityEstimate,
    ComplexityEstimator,
    ComplexityLevel,
)
from runtime.resource_governance.capability_requirement_resolver import (
    CapabilityRequirement,
    CapabilityRequirementResolver,
)
from runtime.resource_governance.activation_guard import (
    ActivationGuard,
    ActivationGuardDecision,
    ActivationGuardLimits,
    ActivationRejectionReason,
)
from runtime.resource_governance.budget_allocator import BudgetAllocator
from runtime.resource_governance.budget_enforcer import BudgetEnforcer
from runtime.resource_governance.budget_monitor import BudgetMonitor, BudgetThresholds
from runtime.resource_governance.capability_activation_resolver import (
    CapabilityActivationRequest,
    CapabilityActivationResolver,
    CapabilityActivationRule,
)
from runtime.resource_governance.cognitive_budget import (
    BudgetPressureState,
    CognitiveBudget,
    ResourceRequest,
    ResourceRequestDecision,
    ResourceRequestDecisionType,
)
from runtime.resource_governance.deescalation_controller import (
    DeescalationController,
    DeescalationDecision,
    FinalizationStrategy,
)
from runtime.resource_governance.diminishing_return_detector import (
    DiminishingReturnDetector,
    DiminishingReturnState,
)
from runtime.resource_governance.early_termination_controller import (
    EarlyTerminationController,
    TerminalState,
    TerminationDecision,
)
from runtime.resource_governance.deferred_maintenance_plan import (
    MaintenanceWorkItem,
    MaintenanceWorkStatus,
    PostExecutionPlan,
)
from runtime.resource_governance.deferred_maintenance_ledger import DeferredMaintenanceLedger
from runtime.resource_governance.deferred_work_registry import DeferredWorkRegistry
from runtime.resource_governance.escalation_controller import (
    EscalationController,
    EscalationDecision,
    RuntimeExecutionStrategy,
)
from runtime.resource_governance.execution_transition import ExecutionTransition
from runtime.resource_governance.governor_registry import (
    DEFAULT_LAYER_DEFINITIONS,
    GovernorRegistry,
)
from runtime.resource_governance.governor_authority import (
    GovernorBypassDetector,
    LegacyModeAudit,
)
from runtime.resource_governance.initial_execution_planner import (
    ExecutionStrategy,
    InitialExecutionPlanner,
    InitialExecutionResourcePlan,
)
from runtime.resource_governance.layer_state_registry import (
    LayerExecutionCategory,
    LayerMetadata,
    LayerState,
    LayerStateRegistry,
)
from runtime.resource_governance.maintenance_budget import MaintenanceBudget
from runtime.resource_governance.maintenance_classifier import (
    MaintenanceClassification,
    MaintenanceClassifier,
    MaintenanceTriggerType,
    MaintenanceWorkCategory,
)
from runtime.resource_governance.maintenance_trigger_resolver import (
    MaintenanceTriggerResolver,
)
from runtime.resource_governance.persistence_governor import (
    PersistenceContract,
    PersistenceContractType,
    PersistenceGovernor,
)
from runtime.resource_governance.post_execution_governor import (
    DEFAULT_POST_EXECUTION_WORK,
    PostExecutionGovernor,
)
from runtime.resource_governance.post_processing_budget import (
    PostProcessingBudget,
    PostProcessingDecision,
)
from runtime.resource_governance.post_success_guard import (
    PostSuccessGuard,
    PostSuccessRejectionReason,
)
from runtime.resource_governance.reporting_governor import (
    ReportBindingMetrics,
    ReportProjection,
    ReportProjectionContract,
    ReportingGovernor,
)
from runtime.resource_governance.resource_plan_builder import (
    ResourceCostLevel,
    ResourcePlan,
    ResourcePlanBuilder,
)
from runtime.resource_governance.resource_value_tracker import (
    LayerValueRecord,
    ResourceValueTracker,
)
from runtime.resource_governance.runtime_signal_monitor import (
    RuntimeSignal,
    RuntimeSignalMonitor,
    RuntimeSignalSeverity,
    RuntimeSignalType,
)
from runtime.resource_governance.runtime_closure import (
    ClosureState,
    ResultLifecycleState,
    RuntimeClosureRecord,
)
from runtime.resource_governance.serialization_governor import (
    SerializationGovernor,
    SerializationLedger,
)
from runtime.resource_governance.task_profiler import TaskProfile, TaskProfiler
from runtime.resource_governance.terminal_state_guard import (
    CRITICAL_COMPLETION_WORK,
    TerminalRecord,
    TerminalStateGuard,
)
from runtime.resource_governance.unified_adaptive_runtime import (
    UnifiedRuntimeResult,
    build_unified_adaptive_runtime_report,
    render_unified_adaptive_runtime_report,
    run_with_governor,
)


__all__ = [
    "AdaptiveExecutionGovernor",
    "ActivationGuard",
    "ActivationGuardDecision",
    "ActivationGuardLimits",
    "ActivationRejectionReason",
    "BudgetAllocator",
    "BudgetEnforcer",
    "BudgetMonitor",
    "BudgetPressureState",
    "BudgetThresholds",
    "CapabilityActivationRequest",
    "CapabilityActivationResolver",
    "CapabilityActivationRule",
    "CapabilityRequirement",
    "CapabilityRequirementResolver",
    "ComplexityEstimate",
    "ComplexityEstimator",
    "ComplexityLevel",
    "CognitiveBudget",
    "CRITICAL_COMPLETION_WORK",
    "DEFAULT_EXECUTION_POLICIES",
    "DEFAULT_LAYER_DEFINITIONS",
    "DEFAULT_POST_EXECUTION_WORK",
    "DeescalationController",
    "DeescalationDecision",
    "DiminishingReturnDetector",
    "DiminishingReturnState",
    "DeferredWorkRegistry",
    "DeferredMaintenanceLedger",
    "EarlyTerminationController",
    "ExecutionDecision",
    "ExecutionPlan",
    "ExecutionPolicy",
    "ExecutionPolicyName",
    "ExecutionContract",
    "ExecutionTransition",
    "ExecutionStrategy",
    "EscalationController",
    "EscalationDecision",
    "FinalizationStrategy",
    "GovernorRegistry",
    "GovernorBypassDetector",
    "InitialExecutionPlanner",
    "InitialExecutionResourcePlan",
    "LayerExecutionCategory",
    "LayerMetadata",
    "LayerState",
    "LayerStateRegistry",
    "LayerValueRecord",
    "LEGACY_MODE_ALIASES",
    "LegacyModeAudit",
    "MaintenanceBudget",
    "MaintenanceClassification",
    "MaintenanceClassifier",
    "MaintenanceTriggerResolver",
    "MaintenanceTriggerType",
    "MaintenanceWorkCategory",
    "MaintenanceWorkItem",
    "MaintenanceWorkStatus",
    "PersistenceContract",
    "PersistenceContractType",
    "PersistenceGovernor",
    "PostExecutionGovernor",
    "PostExecutionPlan",
    "PostProcessingBudget",
    "PostProcessingDecision",
    "PostSuccessGuard",
    "PostSuccessRejectionReason",
    "ReportBindingMetrics",
    "ReportProjection",
    "ReportProjectionContract",
    "ReportingGovernor",
    "ResourceCostLevel",
    "ResourcePlan",
    "ResourcePlanBuilder",
    "ResourceRequest",
    "ResourceRequestDecision",
    "ResourceRequestDecisionType",
    "ResourceValueTracker",
    "RuntimeExecutionStrategy",
    "RuntimeClosureRecord",
    "ResultLifecycleState",
    "ClosureState",
    "RuntimeSignal",
    "RuntimeSignalMonitor",
    "RuntimeSignalSeverity",
    "RuntimeSignalType",
    "SerializationGovernor",
    "SerializationLedger",
    "SUPPORTED_POLICY_ALIASES",
    "TaskProfile",
    "TaskProfiler",
    "TerminalRecord",
    "TerminalState",
    "TerminalStateGuard",
    "TerminationDecision",
    "UnifiedRuntimeResult",
    "adaptive_execution_governor",
    "build_unified_adaptive_runtime_report",
    "render_unified_adaptive_runtime_report",
    "resolve_policy",
    "run_with_governor",
]
