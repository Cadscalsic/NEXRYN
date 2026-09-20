"""Unified adaptive execution governor foundation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import time
from typing import Any, Iterable, Mapping

from runtime.resource_governance.execution_plan import ExecutionPlan
from runtime.resource_governance.execution_policy import (
    ExecutionPolicy,
    ExecutionPolicyName,
)
from runtime.resource_governance.activation_guard import ActivationGuard
from runtime.resource_governance.budget_allocator import BudgetAllocator
from runtime.resource_governance.budget_enforcer import BudgetEnforcer
from runtime.resource_governance.budget_monitor import BudgetMonitor
from runtime.resource_governance.capability_activation_resolver import (
    CapabilityActivationResolver,
    CapabilityActivationRequest,
)
from runtime.resource_governance.cognitive_budget import (
    CognitiveBudget,
    ResourceRequest,
    ResourceRequestDecision,
)
from runtime.resource_governance.deescalation_controller import (
    DeescalationController,
    FinalizationStrategy,
)
from runtime.resource_governance.diminishing_return_detector import (
    DiminishingReturnDetector,
)
from runtime.resource_governance.dynamic_layer_activator import DynamicLayerActivator
from runtime.resource_governance.early_termination_controller import (
    EarlyTerminationController,
    TerminalState,
)
from runtime.resource_governance.escalation_controller import (
    EscalationController,
    RuntimeExecutionStrategy,
)
from runtime.resource_governance.execution_transition import ExecutionTransition
from runtime.resource_governance.governor_registry import GovernorRegistry
from runtime.resource_governance.layer_dependency_resolver import LayerDependencyResolver
from runtime.resource_governance.layer_state_registry import (
    LayerExecutionCategory,
    LayerMetadata,
    LayerState,
    LayerStateRegistry,
    normalize_layer_state,
)
from runtime.resource_governance.initial_execution_planner import (
    CAPABILITY_LAYER_MAP,
    InitialExecutionPlanner,
    InitialExecutionResourcePlan,
)
from runtime.resource_governance.task_profiler import TaskProfile, TaskProfiler
from runtime.resource_governance.runtime_signal_monitor import (
    RuntimeSignal,
    RuntimeSignalMonitor,
    RuntimeSignalType,
)
from runtime.resource_governance.resource_value_tracker import ResourceValueTracker
from runtime.resource_governance.deferred_maintenance_plan import (
    MaintenanceWorkItem,
    PostExecutionPlan,
)
from runtime.resource_governance.maintenance_classifier import MaintenanceClassification
from runtime.resource_governance.post_execution_governor import PostExecutionGovernor
from runtime.resource_governance.post_processing_budget import (
    PostProcessingBudget,
    PostProcessingDecision,
)
from runtime.resource_governance.runtime_closure import (
    ResultLifecycleState,
    RuntimeClosureRecord,
)
from runtime.resource_governance.terminal_state_guard import (
    CRITICAL_COMPLETION_WORK,
    TerminalRecord,
    TerminalStateGuard,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from runtime.capability_architecture.capability_contract import CapabilityContract
    from runtime.capability_architecture.layer_descriptor import LayerDescriptor


EXECUTABLE_STATES = {
    LayerState.REQUIRED,
    LayerState.ACTIVE,
}


@dataclass(frozen=True)
class ExecutionDecision:
    layer_name: str
    previous_state: LayerState
    new_state: LayerState
    execution_policy: ExecutionPolicyName
    reason: str
    timestamp: str

    def as_dict(self) -> dict[str, str]:
        return {
            "layer_name": self.layer_name,
            "previous_state": self.previous_state.value,
            "new_state": self.new_state.value,
            "execution_policy": self.execution_policy.value,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


class AdaptiveExecutionGovernor:
    def __init__(
        self,
        execution_policy: str | ExecutionPolicyName | ExecutionPolicy | None = None,
        registry: GovernorRegistry | None = None,
        register_defaults: bool = True,
    ):
        self.execution_policy = ExecutionPolicy.from_name(execution_policy)
        self.registry = registry or GovernorRegistry(LayerStateRegistry())
        self.state_registry = self.registry.state_registry
        self.task_profiler = TaskProfiler()
        self.initial_execution_planner = InitialExecutionPlanner()
        self.signal_monitor = RuntimeSignalMonitor()
        self.activation_guard = ActivationGuard()
        self.capability_resolver = CapabilityActivationResolver(CAPABILITY_LAYER_MAP)
        self.dependency_resolver = LayerDependencyResolver(self.registry)
        self.dynamic_layer_activator = DynamicLayerActivator(
            self.dependency_resolver,
            self.activation_guard,
        )
        self.escalation_controller = EscalationController()
        self.deescalation_controller = DeescalationController()
        self.diminishing_return_detector = DiminishingReturnDetector()
        self.early_termination_controller = EarlyTerminationController()
        self.terminal_state_guard = TerminalStateGuard()
        self.budget_allocator = BudgetAllocator()
        self.budget_monitor = BudgetMonitor()
        self.budget_enforcer = BudgetEnforcer()
        self.value_tracker = ResourceValueTracker()
        self.post_execution_governor = PostExecutionGovernor()
        self.post_execution_plan: PostExecutionPlan | None = None
        self.runtime_closure = RuntimeClosureRecord()
        from runtime.capability_architecture.capability_governor import CapabilityGovernor
        from runtime.capability_intelligence.capability_intelligence_engine import (
            CapabilityIntelligenceEngine,
        )

        self.capability_governor = CapabilityGovernor()
        self.capability_intelligence = CapabilityIntelligenceEngine(self.capability_governor)
        self.cognitive_budget: CognitiveBudget | None = None
        self.resource_request_history: list[ResourceRequestDecision] = []
        self.post_success_started_at: float | None = None
        self.transition_history: list[ExecutionTransition] = []
        self.initial_strategy = RuntimeExecutionStrategy.LIGHT_EXECUTION
        self.execution_decisions: list[ExecutionDecision] = []
        self.status = "OPERATIONAL"
        if register_defaults:
            self.registry.register_defaults()

    def register_layer(
        self,
        name: str,
        description: str = "",
        dependencies: Iterable[str] | None = None,
        owner: str = "runtime",
        default_state: str | LayerState = LayerState.REGISTERED,
        execution_category: str | LayerExecutionCategory = (
            LayerExecutionCategory.COGNITIVE_REASONING
        ),
        metadata: Mapping[str, Any] | None = None,
    ) -> LayerMetadata:
        return self.registry.register_layer(
            name=name,
            description=description,
            dependencies=dependencies,
            owner=owner,
            default_state=default_state,
            execution_category=execution_category,
            metadata=metadata,
        )

    def register_capability_layer(
        self,
        layer_descriptor: "LayerDescriptor",
        capability_contracts: list["CapabilityContract"],
    ) -> bool:
        layer_registered = self.capability_governor.register_layer(layer_descriptor)
        for contract in capability_contracts:
            self.capability_governor.register_capability(contract)
        return layer_registered

    def discover_capability(self, capability_name: str):
        return self.capability_governor.discovery.get_capability(capability_name)

    def recommend_capabilities_for_task(
        self,
        task: Any,
        policy: str | None = None,
    ) -> dict[str, Any]:
        profile = task if isinstance(task, TaskProfile) else self.profile_task(task)
        return self.capability_intelligence.recommend_for_task(
            profile,
            policy or self.execution_policy.name.value,
        )

    def recommend_policy_for_task(self, task: Any) -> dict[str, str]:
        profile = task if isinstance(task, TaskProfile) else self.profile_task(task)
        signature = self.capability_intelligence.task_signature_mapper.map_profile(profile)
        return self.capability_intelligence.policy_recommendation_engine.recommend(
            signature.task_family,
            profile.task_complexity,
        )

    def build_capability_intelligence_report(self, task: Any) -> dict[str, Any]:
        profile = task if isinstance(task, TaskProfile) else self.profile_task(task)
        recommendation = self.capability_intelligence.recommend_for_task(
            profile,
            self.execution_policy.name.value,
        )
        approved = [
            capability for capability in recommendation["recommended_capabilities"]
            if self.can_activate_capability(capability)
        ]
        status = "APPROVED" if len(approved) == len(recommendation["recommended_capabilities"]) else "PARTIAL"
        return self.capability_intelligence.build_report(
            profile,
            self.execution_policy.name.value,
            governor_approval_status=status,
        )

    def set_policy(
        self,
        execution_policy: str | ExecutionPolicyName | ExecutionPolicy,
    ) -> ExecutionPolicy:
        self.execution_policy = ExecutionPolicy.from_name(execution_policy)
        return self.execution_policy

    def transition_layer(
        self,
        layer_name: str,
        new_state: str | LayerState,
        reason: str = "governor_transition",
    ) -> LayerState:
        previous_state = self.get_layer_state(layer_name)
        normalized_state = normalize_layer_state(new_state)
        applied_state = self.state_registry.set_state(layer_name, normalized_state)
        self._record_decision(
            layer_name=str(layer_name),
            previous_state=previous_state,
            new_state=applied_state,
            reason=reason,
        )
        return applied_state

    def require_layer(self, layer_name: str, reason: str = "layer_required") -> LayerState:
        return self.transition_layer(layer_name, LayerState.REQUIRED, reason)

    def defer_layer(
        self,
        layer_name: str,
        reason: str = "policy_constraint",
    ) -> LayerState:
        return self.transition_layer(layer_name, LayerState.DEFERRED, reason)

    def block_layer(
        self,
        layer_name: str,
        reason: str = "governor_block",
    ) -> LayerState:
        return self.transition_layer(layer_name, LayerState.BLOCKED, reason)

    def complete_layer(
        self,
        layer_name: str,
        reason: str = "layer_completed",
        execution_id: str = "runtime_execution",
    ) -> LayerState:
        previous_state = self.get_layer_state(layer_name)
        state = self.transition_layer(layer_name, LayerState.COMPLETED, reason)
        self._record_transition(
            execution_id=execution_id,
            layer_name=layer_name,
            capability_name=layer_name,
            previous_state=previous_state,
            new_state=LayerState.COMPLETED,
            trigger_signal="COMPLETION_REQUEST",
            reason=reason,
            priority="LOW",
            dependencies_activated=(),
            approved=True,
            rejection_reason=None,
        )
        return state

    def fail_layer(
        self,
        layer_name: str,
        reason: str = "layer_failed",
        execution_id: str = "runtime_execution",
    ) -> LayerState:
        previous_state = self.get_layer_state(layer_name)
        state = self.transition_layer(layer_name, LayerState.FAILED, reason)
        self._record_transition(
            execution_id=execution_id,
            layer_name=layer_name,
            capability_name=layer_name,
            previous_state=previous_state,
            new_state=LayerState.FAILED,
            trigger_signal="FAILURE_REQUEST",
            reason=reason,
            priority="MEDIUM",
            dependencies_activated=(),
            approved=True,
            rejection_reason=None,
        )
        return state

    def can_execute(self, layer_name: str) -> bool:
        return self.get_layer_state(layer_name) in EXECUTABLE_STATES

    def get_layer_state(self, layer_name: str) -> LayerState:
        return self.state_registry.get_state(layer_name)

    def layer_states(self) -> dict[str, str]:
        return self.state_registry.states()

    def layer_metadata(self, layer_name: str) -> dict[str, Any]:
        return self.registry.get_metadata(layer_name)

    def create_execution_plan(self) -> ExecutionPlan:
        states = {
            layer_name: self.get_layer_state(layer_name)
            for layer_name in self.registry.list_layers()
        }
        return ExecutionPlan.from_states(states)

    def create_complete_execution_plan(self) -> ExecutionPlan:
        plan = self.create_execution_plan()
        for capability in self.capability_governor.capability_registry.all():
            plan.record_capability(
                capability.capability_name,
                capability.execution_phase.value,
                state=getattr(capability.lifecycle_state, "value", str(capability.lifecycle_state)),
                post_processing_category=capability.post_processing_category.value,
            )
        return plan

    def profile_task(self, task: Any) -> TaskProfile:
        return self.task_profiler.profile(task)

    def create_initial_resource_plan(
        self,
        task: Any,
    ) -> InitialExecutionResourcePlan:
        profile = self.profile_task(task)
        resource_plan = self.initial_execution_planner.plan(profile)
        self.initial_strategy = _runtime_strategy_from_initial(
            resource_plan.execution_strategy.value
        )
        self.escalation_controller.current_strategy = self.initial_strategy
        return resource_plan

    def build_task_resource_profile_report(self, task: Any) -> dict[str, Any]:
        resource_plan = self.create_initial_resource_plan(task)
        return self.initial_execution_planner.build_report(resource_plan)

    def render_task_resource_profile_report(self, task: Any) -> str:
        resource_plan = self.create_initial_resource_plan(task)
        return self.initial_execution_planner.render_report(resource_plan)

    def create_budget(
        self,
        task_profile: TaskProfile,
        execution_policy: ExecutionPolicy | ExecutionPolicyName | str | None = None,
        execution_id: str = "runtime_execution",
        task_id: str = "unknown_task",
    ) -> CognitiveBudget:
        policy = ExecutionPolicy.from_name(execution_policy or self.execution_policy)
        self.cognitive_budget = self.budget_allocator.allocate(
            task_profile,
            policy,
            execution_id=execution_id,
            task_id=task_id,
        )
        self.escalation_controller.max_escalation_count = self.cognitive_budget.max_escalations
        self.activation_guard.limits.max_escalation_count = self.cognitive_budget.max_escalations
        self.activation_guard.limits.max_activation_count_per_layer = max(
            1,
            self.cognitive_budget.max_layer_activations,
        )
        return self.cognitive_budget

    def request_resources(
        self,
        resource_request: ResourceRequest | dict[str, Any],
    ) -> ResourceRequestDecision:
        request = resource_request if isinstance(resource_request, ResourceRequest) else ResourceRequest(**resource_request)
        if self.cognitive_budget is None:
            profile = self.profile_task("")
            self.create_budget(profile)
        status = self.get_budget_status()
        decision = self.budget_enforcer.evaluate_request(
            self.cognitive_budget,
            request,
            self.execution_policy.name,
            terminal=self.terminal_state_guard.terminal,
            pressure=status["budget_pressure_state"],
        )
        if decision.approved_amount > 0:
            self.consume_budget(request.resource_type, decision.approved_amount)
        self.resource_request_history.append(decision)
        return decision

    def consume_budget(self, resource_type: str, amount: float) -> bool:
        if self.cognitive_budget is None:
            return False
        allowed = self.budget_enforcer.consume(self.cognitive_budget, resource_type, amount)
        if not allowed:
            self.enter_terminal_state(
                TerminalState.BEST_EFFORT_BUDGET_EXHAUSTED,
                f"{resource_type}_budget_exhausted",
            )
        return allowed

    def get_budget_status(self) -> dict[str, Any]:
        if self.cognitive_budget is None:
            return {
                "budget_used": {},
                "budget_remaining": {},
                "budget_usage_ratio": {},
                "budget_pressure_state": "NORMAL",
                "projected_exhaustion": [],
            }
        return self.budget_monitor.status(self.cognitive_budget)

    def evaluate_budget_pressure(self) -> str:
        return self.get_budget_status()["budget_pressure_state"]

    def evaluate_diminishing_returns(self, evidence: dict[str, Any] | None = None) -> str:
        return self.diminishing_return_detector.evaluate(dict(evidence or {})).value

    def record_layer_value(
        self,
        layer_name: str,
        evidence: dict[str, float] | None = None,
        resource_cost: float = 0.0,
    ) -> float:
        return self.value_tracker.record(layer_name, evidence, resource_cost).efficiency()

    def publish_signal(
        self,
        signal: RuntimeSignal | dict[str, Any],
    ) -> RuntimeSignal:
        runtime_signal = signal if isinstance(signal, RuntimeSignal) else RuntimeSignal.create(**signal)
        self.activation_guard.note_signal(runtime_signal.signal_type)
        self.signal_monitor.publish(runtime_signal)
        if runtime_signal.signal_type == RuntimeSignalType.EXACT_SUCCESS.value:
            self.activation_guard.mark_terminal_success()
            self.enter_terminal_state(TerminalState.EXACT_SUCCESS, "exact_success_confirmed")
            self.consume_signal(runtime_signal.signal_id, "terminal_success")
            return runtime_signal

        request = self.capability_resolver.resolve_signal(
            runtime_signal.signal_type,
            runtime_signal.payload,
        )
        transition = None
        if request is not None:
            transition = self._activate_capability_request(request, runtime_signal.execution_id)
        escalation = self.evaluate_escalation(runtime_signal)
        effects = []
        if transition is not None:
            effects.append("activation_approved" if transition.approved else f"activation_rejected::{transition.rejection_reason}")
        if escalation.escalated:
            effects.append(f"strategy_escalated::{escalation.new_strategy.value}")
        if runtime_signal.signal_type == RuntimeSignalType.ROUTING_OVERLOAD.value:
            self._suspend_low_priority_layer(runtime_signal)
            effects.append("routing_overload_suspension")
        if runtime_signal.signal_type == RuntimeSignalType.LAYER_NO_VALUE_PRODUCED.value:
            target_layer = runtime_signal.payload.get("layer_name") or runtime_signal.source_layer
            self.evaluate_diminishing_returns({"no_value": True})
            self.suspend_layer(target_layer, "no value produced", runtime_signal.execution_id)
            effects.append("layer_suspended_no_value")
        if runtime_signal.signal_type == RuntimeSignalType.LAYER_VALUE_PRODUCED.value:
            self.record_layer_value(
                runtime_signal.payload.get("layer_name") or runtime_signal.source_layer,
                runtime_signal.payload.get("value_evidence", {"unique_information_produced": 1.0}),
                resource_cost=float(runtime_signal.payload.get("resource_cost", 1.0)),
            )
        self.consume_signal(runtime_signal.signal_id, ",".join(effects) or "observed")
        return runtime_signal

    def consume_signal(self, signal_id: str, activation_effect: str | None = None):
        return self.signal_monitor.consume(signal_id, activation_effect)

    def request_capability(
        self,
        capability_name: str,
        reason: str = "capability_requested",
        execution_id: str = "manual_execution",
    ) -> ExecutionTransition:
        if not self.can_request_resources(capability_name):
            return self._record_transition(
                execution_id=execution_id,
                layer_name=capability_name,
                capability_name=capability_name,
                previous_state=self.get_layer_state(capability_name),
                new_state=self.get_layer_state(capability_name),
                trigger_signal="MANUAL_REQUEST",
                reason=reason,
                priority="MEDIUM",
                dependencies_activated=(),
                approved=False,
                rejection_reason="TERMINAL_STATE_REACHED",
            )
        request = self.capability_resolver.resolve_capability(capability_name, reason)
        return self._activate_capability_request(request, execution_id)

    def activate_layer(
        self,
        layer_name: str,
        trigger_signal: str = "MANUAL_REQUEST",
        reason: str = "execution_transition_requested",
        execution_id: str = "manual_execution",
    ) -> LayerState | ExecutionTransition:
        if not self.can_activate_layer(layer_name):
            return self._record_transition(
                execution_id=execution_id,
                layer_name=layer_name,
                capability_name=layer_name,
                previous_state=self.get_layer_state(layer_name),
                new_state=self.get_layer_state(layer_name),
                trigger_signal=trigger_signal,
                reason=reason,
                priority="MEDIUM",
                dependencies_activated=(),
                approved=False,
                rejection_reason="TERMINAL_STATE_REACHED",
            )
        if trigger_signal == "MANUAL_REQUEST" and execution_id == "manual_execution":
            return self.transition_layer(layer_name, LayerState.ACTIVE, reason)
        request = CapabilityActivationRequest(
            capability_name=layer_name,
            target_layer=layer_name,
            reason=reason,
            trigger_signal=trigger_signal,
        )
        return self._activate_capability_request(request, execution_id)

    def suspend_layer(
        self,
        layer_name: str,
        reason: str = "layer_suspended",
        execution_id: str = "runtime_execution",
    ) -> LayerState:
        previous_state = self.get_layer_state(layer_name)
        state = self.transition_layer(layer_name, LayerState.SUSPENDED, reason)
        self._record_transition(
            execution_id=execution_id,
            layer_name=layer_name,
            capability_name=layer_name,
            previous_state=previous_state,
            new_state=LayerState.SUSPENDED,
            trigger_signal="SUSPENSION_REQUEST",
            reason=reason,
            priority="LOW",
            dependencies_activated=(),
            approved=True,
            rejection_reason=None,
        )
        return state

    def evaluate_escalation(self, signal: RuntimeSignal | str | None = None):
        if self.cognitive_budget is not None and self.cognitive_budget.used("escalations") >= self.cognitive_budget.max_escalations:
            return self.escalation_controller.evaluate("")
        signal_type = signal.signal_type if isinstance(signal, RuntimeSignal) else str(signal or "")
        critical = isinstance(signal, RuntimeSignal) and signal.severity == "CRITICAL"
        decision = self.escalation_controller.evaluate(
            signal_type,
            policy=self.execution_policy.name,
            critical=critical,
        )
        if decision.escalated:
            self.consume_budget("escalations", 1)
        return decision

    def evaluate_deescalation(
        self,
        signal_type: str = "",
        diminishing_state: str | None = None,
    ):
        decision = self.deescalation_controller.evaluate(
            self.get_current_strategy(),
            signal_type=signal_type,
            diminishing_state=diminishing_state or self.diminishing_return_detector.current_state.value,
            terminal=self.terminal_state_guard.terminal,
        )
        if decision.deescalated:
            if decision.new_strategy == FinalizationStrategy.MINIMAL_FINALIZATION.value:
                self.enter_minimal_finalization()
            else:
                self.escalation_controller.current_strategy = RuntimeExecutionStrategy(decision.new_strategy)
        return decision

    def evaluate_early_termination(
        self,
        signal_type: str = "",
        partial_success: dict[str, Any] | None = None,
        external_stop: bool = False,
        critical_failure: bool = False,
    ):
        status = self.get_budget_status()
        budget = self.cognitive_budget
        decision = self.early_termination_controller.evaluate(
            signal_type=signal_type,
            budget_pressure=status["budget_pressure_state"],
            diminishing_state=self.diminishing_return_detector.current_state.value,
            retries_used=budget.used("retries") if budget else 0,
            max_retries=budget.max_retries if budget else 1,
            repairs_used=budget.used("repairs") if budget else 0,
            max_repairs=budget.max_repairs if budget else 1,
            partial_success=partial_success,
            external_stop=external_stop,
            critical_failure=critical_failure,
        )
        if decision.should_terminate:
            self.enter_terminal_state(decision.terminal_state, decision.reason)
        return decision

    def enter_terminal_state(
        self,
        state: TerminalState | str,
        reason: str,
        final_prediction_state: Any = None,
        final_confidence: float | None = None,
        best_candidate: Any = None,
        unresolved_residual: Any = None,
        deferred_work_requirements: list[str] | None = None,
        critical_persistence_requirements: list[str] | None = None,
    ) -> TerminalRecord:
        state_value = state.value if isinstance(state, TerminalState) else str(state)
        record = TerminalRecord(
            state=state_value,
            termination_reason=reason,
            final_prediction_state=final_prediction_state,
            final_confidence=final_confidence,
            remaining_budget=self.get_budget_status().get("budget_remaining", {}),
            best_candidate=best_candidate,
            unresolved_residual=unresolved_residual,
            deferred_work_requirements=list(deferred_work_requirements or []),
            critical_persistence_requirements=list(critical_persistence_requirements or []),
        )
        self.terminal_state_guard.enter_terminal(record)
        self.runtime_closure.task_result_status = state_value
        self.runtime_closure.transition(ResultLifecycleState.TERMINAL_STATE_REACHED)
        self.activation_guard.mark_terminal_success()
        self.enter_minimal_finalization()
        for layer_name, state_name in self.layer_states().items():
            if state_name == LayerState.ACTIVE.value and layer_name not in {"report_binding", "report_rendering"}:
                self.suspend_layer(layer_name, "terminal state reached")
        return record

    def enter_minimal_finalization(self) -> None:
        self.terminal_state_guard.enter_minimal_finalization()
        self.escalation_controller.current_strategy = RuntimeExecutionStrategy.LIGHT_EXECUTION
        self.post_success_started_at = self.post_success_started_at or time.monotonic()
        self.runtime_closure.transition(ResultLifecycleState.MINIMAL_FINALIZATION)

    def can_continue_execution(self) -> bool:
        if self.terminal_state_guard.terminal:
            return False
        if self.evaluate_budget_pressure() == "EXHAUSTED":
            return False
        return True

    def can_activate_layer(self, layer_name: str) -> bool:
        if not self.terminal_state_guard.allow("activate_layer"):
            return False
        if self.cognitive_budget is not None and self.cognitive_budget.remaining("layer_activations") <= 0:
            return False
        return True

    def can_activate_capability(self, capability_name: str) -> bool:
        contract = self.capability_governor.discovery.get_capability(capability_name)
        if contract is not None:
            return self.capability_governor.can_activate_capability(
                capability_name,
                self.execution_policy.name,
            )
        request = self.capability_resolver.resolve_capability(
            capability_name,
            "capability_authority_check",
        )
        return self.can_activate_layer(request.target_layer)

    def check_layer_execution_authority(
        self,
        layer_name: str,
        call_site: str = "unknown",
    ) -> bool:
        approved = self.can_execute(layer_name)
        detector = getattr(self, "bypass_detector", None)
        if detector is not None:
            detector.record_attempt(
                layer_name,
                approved,
                call_site=call_site,
                policy_context_present=True,
                execution_contract_present=hasattr(self, "execution_contract"),
            )
        return approved

    def can_request_resources(self, layer_name: str) -> bool:
        return self.terminal_state_guard.allow("request_resources")

    def allow_critical_completion_work(self, action: str) -> bool:
        return self.terminal_state_guard.allow(action, critical=action in CRITICAL_COMPLETION_WORK)

    def build_post_execution_plan(
        self,
        work_types: list[str] | None = None,
        triggers: list[str] | None = None,
        state_versions: dict[str, Any] | None = None,
        task_profile: TaskProfile | dict[str, Any] | None = None,
        execution_id: str | None = None,
        task_id: str | None = None,
    ) -> PostExecutionPlan:
        terminal = self.terminal_state_guard.terminal_record
        profile_dict = (
            task_profile.as_dict()
            if isinstance(task_profile, TaskProfile)
            else dict(task_profile or {})
        )
        self.post_execution_plan = self.post_execution_governor.build_plan(
            execution_id=execution_id or (self.cognitive_budget.execution_id if self.cognitive_budget else "runtime_execution"),
            task_id=task_id or (self.cognitive_budget.task_id if self.cognitive_budget else "unknown_task"),
            terminal_state=terminal.state if terminal else "RUNTIME_FAILURE",
            policy=self.execution_policy.name,
            task_profile=profile_dict,
            work_types=work_types,
            triggers=triggers,
            state_versions=state_versions,
        )
        self.runtime_closure.post_processing_status = "PLANNED"
        if self.post_execution_plan.deferred_work or self.post_execution_plan.change_triggered_work:
            self.runtime_closure.maintenance_status = "PENDING"
        return self.post_execution_plan

    def classify_post_execution_work(
        self,
        work_type: str,
        component_name: str = "",
    ) -> MaintenanceClassification:
        return self.post_execution_governor.classifier.classify(
            work_type,
            component_name=component_name,
            policy=self.execution_policy.name,
        )

    def register_deferred_work(
        self,
        work_item: MaintenanceWorkItem,
    ) -> MaintenanceWorkItem:
        return self.post_execution_governor.register_deferred(work_item)

    def execute_critical_finalization(self) -> list[MaintenanceWorkItem]:
        plan = self.post_execution_plan or self.build_post_execution_plan()
        completed = self.post_execution_governor.execute_critical(plan)
        self.enter_result_available_state()
        return completed

    def execute_bounded_finalization(
        self,
        elapsed: float = 0.0,
    ) -> list[MaintenanceWorkItem]:
        plan = self.post_execution_plan or self.build_post_execution_plan()
        completed = self.post_execution_governor.execute_bounded(plan, elapsed=elapsed)
        self.runtime_closure.post_processing_status = (
            "PARTIALLY_DEFERRED"
            if plan.deferred_work or any(item.status == "DEFERRED" for item in plan.bounded_sync_work)
            else "COMPLETED"
        )
        self.runtime_closure.maintenance_status = (
            "PENDING" if plan.deferred_work or plan.change_triggered_work else "COMPLETED"
        )
        if self.runtime_closure.result_available and self.runtime_closure.maintenance_status == "PENDING":
            self.runtime_closure.transition(ResultLifecycleState.POST_PROCESSING_PENDING)
        return completed

    def evaluate_change_triggers(
        self,
        triggers: list[str] | None = None,
        state_versions: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.post_execution_governor.trigger_resolver.evaluate(
            triggers,
            state_versions,
        )

    def select_report_projection(self) -> dict[str, Any]:
        terminal = self.terminal_state_guard.terminal_record
        return self.post_execution_governor.reporting_governor.select_projection(
            self.execution_policy.name,
            terminal.state if terminal else None,
        ).as_dict()

    def select_persistence_contract(
        self,
        state_changed: bool = False,
        shutdown_required: bool = False,
    ) -> dict[str, Any]:
        return self.post_execution_governor.persistence_governor.select_contract(
            self.execution_policy.name,
            state_changed=state_changed,
            shutdown_required=shutdown_required,
        ).as_dict()

    def create_post_processing_budget(self) -> PostProcessingBudget:
        self.post_execution_governor.post_processing_budget = PostProcessingBudget.for_policy(
            self.execution_policy.name
        )
        return self.post_execution_governor.post_processing_budget

    def evaluate_post_processing_capability(
        self,
        capability_id: str,
        category: str,
        state_changed: bool = False,
        diagnostic_requested: bool = False,
    ) -> PostProcessingDecision:
        normalized = str(category)
        budget = self.post_execution_governor.post_processing_budget or self.create_post_processing_budget()
        if normalized == "PROHIBITED_AFTER_TERMINAL" and self.terminal_state_guard.terminal:
            decision = PostProcessingDecision.REJECT_AFTER_TERMINAL
            reason = "terminal_state_restriction"
        elif normalized == "CRITICAL_SYNC":
            decision = PostProcessingDecision.RUN_CRITICAL_SYNC
            reason = "critical_completion_required"
        elif normalized == "BOUNDED_SYNC":
            decision = (
                PostProcessingDecision.RUN_BOUNDED_SYNC
                if budget.can_run_bounded()
                else PostProcessingDecision.DEFER
            )
            reason = "bounded_sync_budget_available" if decision == PostProcessingDecision.RUN_BOUNDED_SYNC else "bounded_sync_budget_exceeded"
        elif normalized == "CHANGE_TRIGGERED":
            decision = PostProcessingDecision.RUN_IF_CHANGED if state_changed else PostProcessingDecision.SKIP_UNCHANGED
            reason = "state_signature_changed" if state_changed else "state_signature_unchanged"
        elif normalized == "DIAGNOSTIC_ONLY":
            decision = (
                PostProcessingDecision.RUN_BOUNDED_SYNC
                if diagnostic_requested or self.execution_policy.name == ExecutionPolicyName.DIAGNOSTIC
                else PostProcessingDecision.SKIP_DIAGNOSTIC_ONLY
            )
            reason = "diagnostic_policy" if decision == PostProcessingDecision.RUN_BOUNDED_SYNC else "diagnostic_policy_required"
        else:
            decision = PostProcessingDecision.DEFER
            reason = "deferred_maintenance"
        budget.record_decision(capability_id, decision, reason)
        return decision

    def check_post_processing_authority(
        self,
        capability_name: str,
        category: str = "post_processing",
        call_site: str = "unknown",
    ) -> bool:
        approved = self.post_execution_plan is not None
        detector = getattr(self, "bypass_detector", None)
        if detector is not None:
            detector.record_post_processing_attempt(
                capability_name,
                approved,
                category=category,
                call_site=call_site,
            )
        return approved

    def enforce_serialization_budget(
        self,
        object_count: int,
        serialized_bytes: int,
        duration: float = 0.0,
        signature: str | None = None,
    ) -> bool:
        budget_bytes = 65_536
        max_duration = 0.1
        if self.post_execution_plan is not None:
            budget_bytes = int(self.post_execution_plan.synchronous_budget.get("serialization_budget_bytes", budget_bytes))
            max_duration = float(self.post_execution_plan.synchronous_budget.get("seconds", max_duration))
        return self.post_execution_governor.serialization_governor.enforce(
            object_count=object_count,
            serialized_bytes=serialized_bytes,
            duration=duration,
            max_serialized_bytes=budget_bytes,
            max_duration=max_duration,
            signature=signature,
        )

    def enter_result_available_state(self) -> str:
        plan = self.post_execution_plan or self.build_post_execution_plan()
        timestamp = self.post_execution_governor.enter_result_available(plan)
        self.runtime_closure.transition(ResultLifecycleState.RESULT_AVAILABLE)
        self.runtime_closure.post_processing_status = "PENDING"
        return timestamp

    def get_maintenance_status(self) -> dict[str, Any]:
        plan = self.post_execution_plan
        task_result_status = (
            self.terminal_state_guard.terminal_record.state
            if self.terminal_state_guard.terminal_record
            else "NOT_TERMINAL"
        )
        deferred_count = len(plan.deferred_work) if plan else 0
        skipped_policy = len([item for item in (plan.diagnostic_work if plan else []) if item.status == "SKIPPED_POLICY"])
        status = "PARTIALLY_DEFERRED" if deferred_count else "COMPLETED"
        return {
            "task_result_status": task_result_status,
            "post_processing_status": self.runtime_closure.post_processing_status,
            "maintenance_status": status,
            "deferred_work_count": deferred_count,
            "diagnostic_work_skipped": skipped_policy,
            "registry": self.post_execution_governor.registry.summary(),
            "ledger": self.post_execution_governor.ledger.summary(),
            "result_available_timestamp": self.post_execution_governor.result_available_timestamp,
        }

    def get_deferred_work_summary(self) -> dict[str, Any]:
        return self.post_execution_governor.registry.summary()

    def close_execution(self) -> str:
        plan = self.post_execution_plan or self.build_post_execution_plan()
        terminal = self.terminal_state_guard.terminal_record
        bypass = getattr(self, "bypass_detector", None)
        bypass_count = bypass.unauthorized_layer_execution_count if bypass is not None else 0
        policy_violations = len(self.post_execution_governor.serialization_governor.ledger.policy_violations or [])
        closure = self.runtime_closure.validate(
            terminal_state=terminal.state if terminal else None,
            critical_completed=bool(self.post_execution_governor.critical_completed),
            deferred_count=len(plan.deferred_work) + len([
                item for item in plan.change_triggered_work
                if item.status not in {"SKIPPED_UNCHANGED", "SKIPPED_POLICY", "COMPLETED"}
            ]),
            prohibited_count=len([
                item for item in plan.prohibited_work
                if item.status != "CANCELLED"
            ]),
            bypass_count=bypass_count,
            policy_violation_count=policy_violations,
            maintenance_failure_count=len(self.post_execution_governor.maintenance_failures),
        )
        return closure.value

    def get_current_strategy(self) -> str:
        return self.escalation_controller.current_strategy.value

    def get_transition_history(self) -> list[dict[str, Any]]:
        return [transition.as_dict() for transition in self.transition_history]

    def build_dynamic_activation_report(self, diagnostic: bool = False) -> dict[str, Any]:
        signals = self.signal_monitor.all_signals()
        transitions = self.transition_history
        approved = [item for item in transitions if item.approved]
        rejected = [item for item in transitions if not item.approved]
        suspended = [
            item for item in transitions
            if item.approved and item.new_state == LayerState.SUSPENDED.value
        ]
        report = {
            "DYNAMIC_RESOURCE_ACTIVATION_REPORT": True,
            "initial_execution_strategy": self.initial_strategy.value,
            "current_execution_strategy": self.get_current_strategy(),
            "runtime_signals_received": len(signals),
            "layers_activated_on_demand": [
                {"layer_name": item.layer_name, "reason": item.trigger_signal}
                for item in approved
                if item.new_state == LayerState.ACTIVE.value
            ],
            "dependencies_activated": sorted({
                dep for item in approved for dep in item.dependencies_activated
            }),
            "layers_suspended": [
                {"layer_name": item.layer_name, "reason": item.reason}
                for item in suspended
            ],
            "escalation_count": self.escalation_controller.escalation_count,
            "activation_rejections": [item.as_dict() for item in rejected],
            "governor_transition_count": len(transitions),
            "runtime_adaptation_status": self.status,
        }
        if diagnostic or self.execution_policy.name == ExecutionPolicyName.DIAGNOSTIC:
            report.update({
                "signal_ledger": [signal.as_dict() for signal in signals],
                "transition_ledger": [item.as_dict() for item in transitions],
                "activation_guard_events": list(self.activation_guard.guard_events),
                "escalation_decisions": [
                    item.as_dict() for item in self.escalation_controller.decisions
                ],
                "repeated_signal_statistics": dict(self.activation_guard.signal_counts),
                "activation_counts": dict(self.activation_guard.activation_counts),
            })
        return report

    def build_cognitive_resource_governance_report(self, diagnostic: bool = False) -> dict[str, Any]:
        budget = self.cognitive_budget
        status = self.get_budget_status()
        terminal_record = self.terminal_state_guard.terminal_record
        suspended = [
            item.layer_name for item in self.transition_history
            if item.approved and item.new_state == LayerState.SUSPENDED.value
        ]
        report = {
            "COGNITIVE_RESOURCE_GOVERNANCE_REPORT": True,
            "execution_policy": self.execution_policy.name.value,
            "initial_strategy": self.initial_strategy.value,
            "final_strategy": (
                FinalizationStrategy.MINIMAL_FINALIZATION.value
                if self.terminal_state_guard.minimal_finalization
                else self.get_current_strategy()
            ),
            "wall_time_budget": budget.max_wall_time_seconds if budget else None,
            "active_compute_budget": budget.max_active_compute_seconds if budget else None,
            "budget_usage": status["budget_used"],
            "budget_pressure": status["budget_pressure_state"],
            "escalations": self.escalation_controller.escalation_count,
            "deescalations": sum(1 for item in self.deescalation_controller.decisions if item.deescalated),
            "suspended_layers": suspended,
            "retry_count": status["budget_used"].get("retries", 0.0),
            "repair_count": status["budget_used"].get("repairs", 0.0),
            "candidate_count": status["budget_used"].get("candidates", 0.0),
            "diminishing_return_state": self.diminishing_return_detector.current_state.value,
            "terminal_state": terminal_record.state if terminal_record else None,
            "termination_reason": terminal_record.termination_reason if terminal_record else None,
            "post_success_duration": self._post_success_duration(),
            "governor_status": self.status,
            "observability_metrics": self._resource_observability_metrics(),
        }
        if diagnostic or self.execution_policy.name == ExecutionPolicyName.DIAGNOSTIC:
            report.update({
                "budget_ledger": list(self.budget_enforcer.ledger),
                "resource_requests": [item.as_dict() for item in self.resource_request_history],
                "per_layer_value_evidence": self.value_tracker.as_dict(),
                "diminishing_return_history": list(self.diminishing_return_detector.history),
                "deescalation_decisions": [item.as_dict() for item in self.deescalation_controller.decisions],
                "terminal_state_guard_rejections": list(self.terminal_state_guard.rejections),
            })
        return report

    def build_post_execution_governance_report(self, diagnostic: bool = False) -> dict[str, Any]:
        plan = self.post_execution_plan or self.build_post_execution_plan()
        maintenance = self.get_maintenance_status()
        serialization = self.post_execution_governor.serialization_governor.ledger.as_dict()
        post_budget = self.post_execution_governor.post_processing_budget or self.create_post_processing_budget()
        binding_contract = plan.reporting_contract
        report_metrics = self.post_execution_governor.reporting_governor.bind_projection(
            self.post_execution_governor.reporting_governor.select_projection(self.execution_policy.name, plan.terminal_state)
        ).as_dict()
        deferred_components = [item.component_name for item in plan.deferred_work]
        result_time = self.post_execution_governor.result_available_timestamp
        report = {
            "POST_EXECUTION_GOVERNANCE_REPORT": True,
            "terminal_state": plan.terminal_state,
            "result_available_time": result_time,
            "post_success_budget": plan.synchronous_budget.get("seconds"),
            "post_success_time_used": self._post_success_duration(),
            "critical_work_completed": len(self.post_execution_governor.critical_completed),
            "bounded_work_completed": len(self.post_execution_governor.bounded_completed),
            "deferred_work_count": len(plan.deferred_work),
            "change_triggered_work_count": len(plan.change_triggered_work),
            "diagnostic_work_skipped": maintenance["diagnostic_work_skipped"],
            "report_projection": binding_contract.get("projection_name"),
            "persistence_contract": plan.persistence_contract.get("contract_type"),
            "serialized_bytes": serialization["serialized_bytes"],
            "maintenance_status": maintenance["maintenance_status"],
            "deferred_components": deferred_components,
            "governor_status": self.status,
            "observability_metrics": {
                "post_execution_governance_active": True,
                "post_processing_budget_used": post_budget.used_sync_seconds,
                "post_processing_budget_exceeded": post_budget.exceeded(),
                "result_available_timestamp": result_time,
                "post_success_duration": self._post_success_duration(),
                "critical_work_count": len(plan.critical_sync_work),
                "bounded_work_count": len(plan.bounded_sync_work),
                "deferred_work_count": len(plan.deferred_work),
                "change_triggered_work_count": len(plan.change_triggered_work),
                "diagnostic_work_skipped": maintenance["diagnostic_work_skipped"],
                "maintenance_budget_used": self._post_success_duration(),
                "maintenance_budget_remaining": max(0.0, float(plan.synchronous_budget.get("seconds", 0.0)) - self._post_success_duration()),
                "report_projection": binding_contract.get("projection_name"),
                "report_binding_duration": report_metrics["binding_duration"],
                "report_nodes_visited": report_metrics["source_nodes_visited"],
                "deepcopy_duration": serialization["deepcopy_duration"],
                "serialization_duration": serialization["serialization_duration"],
                "serialized_bytes": serialization["serialized_bytes"],
                "persistence_duration": plan.persistence_contract.get("max_duration"),
                "fabric_integration_deferred": "knowledge_fabric_integration" in [item.work_type for item in plan.deferred_work],
                "semantic_memory_consolidation_deferred": "semantic_memory_consolidation" in [item.work_type for item in plan.deferred_work],
                "full_state_save_deferred": plan.persistence_contract.get("contract_type") in {"DEFERRED_STATE_SAVE", "FULL_STATE_SAVE"},
                "full_report_deferred": "full_canonical_report_construction" in [item.work_type for item in plan.deferred_work],
                "maintenance_status": maintenance["maintenance_status"],
            },
        }
        if diagnostic or self.execution_policy.name == ExecutionPolicyName.DIAGNOSTIC:
            report.update({
                "maintenance_work_ledger": plan.as_dict(),
                "work_classification_decisions": [item.trigger_reason for item in plan.critical_sync_work + plan.bounded_sync_work + plan.deferred_work + plan.change_triggered_work + plan.diagnostic_work + plan.prohibited_work],
                "trigger_evaluation": plan.state_change_signatures,
                "deferred_work_dependencies": [item.dependency_versions for item in plan.deferred_work],
                "serialization_ledger": serialization,
                "copy_ledger": {
                    "deepcopy_calls": serialization["deepcopy_calls"],
                    "deepcopy_objects": serialization["deepcopy_objects"],
                    "deepcopy_bytes": serialization["deepcopy_bytes"],
                },
                "report_projection_decisions": binding_contract,
                "persistence_decisions": plan.persistence_contract,
                "maintenance_failures": list(self.post_execution_governor.maintenance_failures),
                "idempotency_events": list(self.post_execution_governor.registry.idempotency_events),
                "state_signatures": plan.state_change_signatures,
                "post_success_guard_rejections": list(self.post_execution_governor.post_success_guard.rejections),
            })
        return report

    def build_adaptive_runtime_closure_report(self, diagnostic: bool = False) -> dict[str, Any]:
        plan = self.post_execution_plan or self.build_post_execution_plan()
        if self.post_execution_governor.result_available_timestamp is None:
            self.execute_critical_finalization()
        if self.runtime_closure.post_processing_status in {"PENDING", "PLANNED"}:
            self.execute_bounded_finalization()
        closure_state = self.close_execution()
        terminal = self.terminal_state_guard.terminal_record
        post_budget = self.post_execution_governor.post_processing_budget or self.create_post_processing_budget()
        maintenance = self.get_maintenance_status()
        bypass = getattr(self, "bypass_detector", None)
        bypass_dict = bypass.as_dict() if bypass is not None else {
            "governor_bypass_count": 0,
            "post_processing_bypass_count": 0,
            "maintenance_bypass_count": 0,
            "reporting_bypass_count": 0,
            "persistence_bypass_count": 0,
            "bypass_call_sites": [],
        }
        legacy = getattr(self, "legacy_mode_audit", None)
        legacy_count = legacy.legacy_branch_count if legacy is not None else 0
        capability_report = self.capability_governor.build_report()
        closure_maintenance_status = (
            "PENDING" if maintenance["maintenance_status"] == "PARTIALLY_DEFERRED"
            else maintenance["maintenance_status"]
        )
        report = {
            "ADAPTIVE_RUNTIME_CLOSURE_REPORT": True,
            "execution_policy": self.execution_policy.name.value,
            "governor_status": self.status,
            "capability_registry_status": capability_report["observability_metrics"]["registry_status"],
            "task_execution_status": maintenance["task_result_status"],
            "terminal_state": terminal.state if terminal else None,
            "result_availability": "AVAILABLE" if self.runtime_closure.result_available else "UNAVAILABLE",
            "post_processing_budget": post_budget.maximum_sync_seconds,
            "post_processing_used": post_budget.used_sync_seconds,
            "critical_work_completed": "COMPLETED" if self.post_execution_governor.critical_completed else "INCOMPLETE",
            "bounded_work_completed": len(self.post_execution_governor.bounded_completed),
            "deferred_work_count": len(plan.deferred_work),
            "change_triggered_work_count": len(plan.change_triggered_work),
            "diagnostic_work_skipped": maintenance["diagnostic_work_skipped"],
            "report_projection": plan.reporting_contract.get("projection_name"),
            "persistence_contract": plan.persistence_contract.get("contract_type"),
            "post_processing_status": maintenance["post_processing_status"],
            "maintenance_status": closure_maintenance_status,
            "governor_bypass_count": bypass_dict["governor_bypass_count"],
            "legacy_branch_count": legacy_count,
            "closure_state": closure_state,
            "runtime_lifecycle": self.runtime_closure.as_dict(),
            "observability_metrics": {
                "adaptive_runtime_closed": closure_state is not None,
                "result_available_before_maintenance": (
                    self.runtime_closure.result_available
                    and closure_maintenance_status == "PENDING"
                ),
                "post_processing_governance_active": True,
                "post_processing_budget_used": post_budget.used_sync_seconds,
                "post_processing_budget_exceeded": post_budget.exceeded(),
                "critical_sync_count": len(plan.critical_sync_work),
                "bounded_sync_count": len(plan.bounded_sync_work),
                "deferred_maintenance_count": len(plan.deferred_work),
                "change_triggered_count": len(plan.change_triggered_work),
                "diagnostic_skipped_count": maintenance["diagnostic_work_skipped"],
                "governor_bypass_count": bypass_dict["governor_bypass_count"],
                "legacy_branch_count": legacy_count,
                "knowledge_fabric_deferred": "knowledge_fabric_integration" in [item.work_type for item in plan.deferred_work],
                "semantic_memory_consolidation_deferred": "semantic_memory_consolidation" in [item.work_type for item in plan.deferred_work],
                "full_report_deferred": "full_canonical_report_construction" in [item.work_type for item in plan.deferred_work],
                "full_persistence_deferred": plan.persistence_contract.get("contract_type") in {"DEFERRED_STATE_SAVE", "FULL_STATE_SAVE"},
                "closure_state": closure_state,
            },
        }
        if diagnostic or self.execution_policy.name == ExecutionPolicyName.DIAGNOSTIC:
            report.update({
                "deferred_maintenance_ledger": self.post_execution_governor.ledger.as_dict(),
                "post_processing_decision_ledger": list(post_budget.decision_ledger),
                "bypass_detection": bypass_dict,
                "closure_validation_errors": list(self.runtime_closure.validation_errors),
            })
        return report

    def render_adaptive_runtime_closure_report(self) -> str:
        report = self.build_adaptive_runtime_closure_report()
        return "\n".join([
            "==================================================",
            "ADAPTIVE RUNTIME CLOSURE REPORT",
            "==================================================",
            "",
            "Execution Policy:",
            report["execution_policy"],
            "",
            "Governor:",
            report["governor_status"],
            "",
            "Terminal State:",
            str(report["terminal_state"]),
            "",
            "Result Availability:",
            report["result_availability"],
            "",
            "Post-Processing Budget:",
            f"{report['post_processing_budget']} s",
            "",
            "Post-Processing Used:",
            f"{round(report['post_processing_used'], 3)} s",
            "",
            "Critical Work:",
            report["critical_work_completed"],
            "",
            "Bounded Work:",
            str(report["bounded_work_completed"]),
            "",
            "Deferred Work:",
            str(report["deferred_work_count"]),
            "",
            "Report Projection:",
            str(report["report_projection"]),
            "",
            "Persistence Contract:",
            str(report["persistence_contract"]),
            "",
            "Post-Processing Status:",
            str(report["post_processing_status"]),
            "",
            "Maintenance Status:",
            str(report["maintenance_status"]),
            "",
            "Governor Bypasses:",
            str(report["governor_bypass_count"]),
            "",
            "Legacy Branches:",
            str(report["legacy_branch_count"]),
            "",
            "Closure State:",
            str(report["closure_state"]),
        ])

    def render_post_execution_governance_report(self) -> str:
        report = self.build_post_execution_governance_report()
        lines = [
            "==================================================",
            "POST-EXECUTION GOVERNANCE REPORT",
            "==================================================",
            "",
            "Terminal State:",
            str(report["terminal_state"]),
            "",
            "Result Available Time:",
            str(report["result_available_time"]),
            "",
            "Post-Success Budget:",
            f"{report['post_success_budget']} s",
            "",
            "Post-Success Time Used:",
            f"{round(report['post_success_time_used'], 3)} s",
            "",
            "Critical Work Completed:",
            str(report["critical_work_completed"]),
            "",
            "Bounded Work Completed:",
            str(report["bounded_work_completed"]),
            "",
            "Deferred Work:",
            str(report["deferred_work_count"]),
            "",
            "Report Projection:",
            str(report["report_projection"]),
            "",
            "Persistence Contract:",
            str(report["persistence_contract"]),
            "",
            "Deferred Components:",
        ]
        lines.extend([f"- {item}" for item in report["deferred_components"]] or ["- none"])
        lines.extend([
            "",
            "Maintenance Status:",
            report["maintenance_status"],
            "",
            "Governor Status:",
            report["governor_status"],
        ])
        return "\n".join(lines)

    def render_cognitive_resource_governance_report(self) -> str:
        report = self.build_cognitive_resource_governance_report()
        lines = [
            "==================================================",
            "COGNITIVE RESOURCE GOVERNANCE REPORT",
            "==================================================",
            "",
            "Execution Policy:",
            report["execution_policy"],
            "",
            "Initial Strategy:",
            report["initial_strategy"],
            "",
            "Final Strategy:",
            report["final_strategy"],
            "",
            "Wall-Time Budget:",
            f"{report['wall_time_budget']} s",
            "",
            "Wall-Time Used:",
            f"{round(report['budget_usage'].get('wall_time_seconds', 0.0), 3)} s",
            "",
            "Budget Pressure:",
            report["budget_pressure"],
            "",
            "Escalations:",
            str(report["escalations"]),
            "",
            "De-escalations:",
            str(report["deescalations"]),
            "",
            "Suspended Layers:",
        ]
        lines.extend([f"- {item}" for item in report["suspended_layers"]] or ["- none"])
        lines.extend([
            "",
            "Diminishing Return State:",
            report["diminishing_return_state"],
            "",
            "Terminal State:",
            str(report["terminal_state"]),
            "",
            "Post-Success Duration:",
            f"{round(report['post_success_duration'], 3)} s",
            "",
            "Governor Status:",
            report["governor_status"],
        ])
        return "\n".join(lines)

    def render_dynamic_activation_report(self) -> str:
        report = self.build_dynamic_activation_report()
        lines = [
            "==================================================",
            "DYNAMIC RESOURCE ACTIVATION REPORT",
            "==================================================",
            "",
            "Initial Strategy:",
            report["initial_execution_strategy"],
            "",
            "Current Strategy:",
            report["current_execution_strategy"],
            "",
            "Signals Received:",
            str(report["runtime_signals_received"]),
            "",
            "On-Demand Activations:",
        ]
        lines.extend([
            f"- {item['layer_name']}\n  reason: {item['reason']}"
            for item in report["layers_activated_on_demand"]
        ] or ["- none"])
        lines.extend([
            "",
            "Dependencies Activated:",
        ])
        lines.extend([f"- {item}" for item in report["dependencies_activated"]] or ["- none"])
        lines.extend([
            "",
            "Layers Suspended:",
        ])
        lines.extend([
            f"- {item['layer_name']}\n  reason: {item['reason']}"
            for item in report["layers_suspended"]
        ] or ["- none"])
        lines.extend([
            "",
            "Escalations:",
            str(report["escalation_count"]),
            "",
            "Runtime Adaptation Status:",
            report["runtime_adaptation_status"],
        ])
        return "\n".join(lines)

    def execution_policies(self) -> dict[str, Any]:
        return self.execution_policy.as_dict()

    def build_report(self) -> dict[str, Any]:
        plan = self.create_execution_plan()
        return {
            "ADAPTIVE_EXECUTION_GOVERNOR_REPORT": True,
            "execution_policy": self.execution_policy.name.value,
            "registered_layers": len(self.registry.list_layers()),
            "active_layers": len(plan.active_layers),
            "deferred_layers": len(plan.deferred_layers),
            "blocked_layers": len(plan.blocked_layers),
            "execution_decisions": [
                decision.as_dict()
                for decision in self.execution_decisions
            ],
            "governor_status": self.status,
            "execution_plan": plan.as_dict(),
        }

    def _activate_capability_request(
        self,
        request: CapabilityActivationRequest,
        execution_id: str,
    ) -> ExecutionTransition:
        if not self.can_activate_layer(request.target_layer):
            return self._record_transition(
                execution_id=execution_id,
                layer_name=request.target_layer,
                capability_name=request.capability_name,
                previous_state=self.get_layer_state(request.target_layer),
                new_state=self.get_layer_state(request.target_layer),
                trigger_signal=request.trigger_signal,
                reason=request.reason,
                priority=request.priority,
                dependencies_activated=(),
                approved=False,
                rejection_reason="TERMINAL_STATE_REACHED",
            )
        if self.registry.get_state(request.target_layer) == LayerState.NOT_REGISTERED:
            return self._record_transition(
                execution_id=execution_id,
                layer_name=request.target_layer,
                capability_name=request.capability_name,
                previous_state=LayerState.NOT_REGISTERED,
                new_state=LayerState.NOT_REGISTERED,
                trigger_signal=request.trigger_signal,
                reason=request.reason,
                priority=request.priority,
                dependencies_activated=(),
                approved=False,
                rejection_reason="LAYER_NOT_REGISTERED",
            )
        transition = self.dynamic_layer_activator.activate(self, request, execution_id)
        if transition.approved:
            self.consume_budget("layer_activations", 1)
        return transition

    def _record_transition(
        self,
        execution_id: str,
        layer_name: str,
        capability_name: str,
        previous_state: LayerState,
        new_state: LayerState,
        trigger_signal: str,
        reason: str,
        priority: str,
        dependencies_activated: tuple[str, ...],
        approved: bool,
        rejection_reason: str | None,
    ) -> ExecutionTransition:
        transition = ExecutionTransition.create(
            execution_id=execution_id,
            layer_name=layer_name,
            capability_name=capability_name,
            previous_state=previous_state.value,
            new_state=new_state.value,
            trigger_signal=trigger_signal,
            reason=reason,
            priority=priority,
            policy=self.execution_policy.name.value,
            dependencies_activated=dependencies_activated,
            approved=approved,
            rejection_reason=rejection_reason,
        )
        self.transition_history.append(transition)
        return transition

    def _suspend_low_priority_layer(self, signal: RuntimeSignal) -> None:
        for layer_name in ("color_mapping", "alternative_proposal_source", "candidate_arena"):
            if self.get_layer_state(layer_name) == LayerState.ACTIVE:
                self.suspend_layer(layer_name, "routing overload", signal.execution_id)
                return

    def _post_success_duration(self) -> float:
        if self.post_success_started_at is None:
            return 0.0
        return max(0.0, time.monotonic() - self.post_success_started_at)

    def _resource_observability_metrics(self) -> dict[str, Any]:
        terminal = self.terminal_state_guard.terminal_record
        no_value_suspended = [
            item.layer_name for item in self.transition_history
            if item.approved and item.new_state == LayerState.SUSPENDED.value and "no value" in item.reason
        ]
        return {
            "budget_enforcement_active": self.cognitive_budget is not None,
            "budget_violation_count": self.budget_enforcer.violation_count,
            "resource_request_count": len(self.resource_request_history),
            "resource_rejection_count": sum(1 for item in self.resource_request_history if item.decision.value.startswith("REJECTED")),
            "deescalation_count": sum(1 for item in self.deescalation_controller.decisions if item.deescalated),
            "early_termination_triggered": terminal is not None,
            "terminal_state": terminal.state if terminal else None,
            "post_success_duration": self._post_success_duration(),
            "layers_stopped_after_success": len(no_value_suspended),
            "no_value_layers_suspended": len(no_value_suspended),
            "retry_efficiency": self.value_tracker.efficiency("retry"),
            "repair_efficiency": self.value_tracker.efficiency("repair"),
            "candidate_efficiency": self.value_tracker.efficiency("candidate_arena"),
            "route_efficiency": self.value_tracker.efficiency("routing"),
        }

    def render_report(self) -> str:
        report = self.build_report()
        return "\n".join([
            "==================================================",
            "ADAPTIVE EXECUTION GOVERNOR REPORT",
            "==================================================",
            "",
            "Execution Policy:",
            "",
            report["execution_policy"],
            "",
            "Registered Layers:",
            "",
            str(report["registered_layers"]),
            "",
            "Active Layers:",
            "",
            str(report["active_layers"]),
            "",
            "Deferred Layers:",
            "",
            str(report["deferred_layers"]),
            "",
            "Blocked Layers:",
            "",
            str(report["blocked_layers"]),
            "",
            "Execution Decisions:",
            "",
            str(len(report["execution_decisions"])),
            "",
            "Governor Status:",
            "",
            report["governor_status"],
        ])

    def _record_decision(
        self,
        layer_name: str,
        previous_state: LayerState,
        new_state: LayerState,
        reason: str,
    ) -> None:
        self.execution_decisions.append(
            ExecutionDecision(
                layer_name=layer_name,
                previous_state=previous_state,
                new_state=new_state,
                execution_policy=self.execution_policy.name,
                reason=str(reason or "governor_transition"),
                timestamp=str(datetime.utcnow()),
            )
        )


adaptive_execution_governor = AdaptiveExecutionGovernor()


def _runtime_strategy_from_initial(strategy: str) -> RuntimeExecutionStrategy:
    if strategy == "LIGHT_EXECUTION":
        return RuntimeExecutionStrategy.LIGHT_EXECUTION
    if strategy == "BALANCED_EXECUTION":
        return RuntimeExecutionStrategy.BALANCED_EXECUTION
    if strategy == "DEEP_EXECUTION_REQUIRED":
        return RuntimeExecutionStrategy.DEEP_EXECUTION
    if strategy == "DIAGNOSTIC_EXECUTION":
        return RuntimeExecutionStrategy.DIAGNOSTIC_EXECUTION
    return RuntimeExecutionStrategy.BALANCED_EXECUTION


__all__ = [
    "AdaptiveExecutionGovernor",
    "EXECUTABLE_STATES",
    "ExecutionDecision",
    "adaptive_execution_governor",
]
