"""Dynamic layer activation through governor-owned components."""

from __future__ import annotations

from dataclasses import dataclass

from runtime.resource_governance.activation_guard import ActivationGuard
from runtime.resource_governance.capability_activation_resolver import CapabilityActivationRequest
from runtime.resource_governance.execution_transition import ExecutionTransition
from runtime.resource_governance.layer_dependency_resolver import LayerDependencyResolver
from runtime.resource_governance.layer_state_registry import LayerState


@dataclass
class DynamicLayerActivator:
    dependency_resolver: LayerDependencyResolver
    activation_guard: ActivationGuard

    def activate(
        self,
        governor,
        request: CapabilityActivationRequest,
        execution_id: str,
    ) -> ExecutionTransition:
        layer_name = request.target_layer
        dependency_resolution = self.dependency_resolver.resolve(
            layer_name,
            request.dependency_requirements,
        )
        previous_state = governor.get_layer_state(layer_name)
        guard_decision = self.activation_guard.approve_activation(
            execution_id=execution_id,
            layer_name=layer_name,
            previous_state=previous_state,
            signal_type=request.trigger_signal,
            policy=governor.execution_policy.name,
            transition_count=len(governor.transition_history),
            dependency_cycle=dependency_resolution.cycle_detected,
            dependency_missing=bool(dependency_resolution.missing_dependencies),
            policy_constraints=request.policy_constraints,
        )
        if not guard_decision.approved:
            return governor._record_transition(
                execution_id=execution_id,
                layer_name=layer_name,
                capability_name=request.capability_name,
                previous_state=previous_state,
                new_state=previous_state,
                trigger_signal=request.trigger_signal,
                reason=request.reason,
                priority=request.priority,
                dependencies_activated=(),
                approved=False,
                rejection_reason=guard_decision.rejection_reason,
            )

        dependencies_activated: list[str] = []
        for dependency in dependency_resolution.activation_order:
            dep_state = governor.get_layer_state(dependency)
            if dep_state not in {LayerState.ACTIVE, LayerState.REQUIRED}:
                governor.transition_layer(
                    dependency,
                    LayerState.ACTIVE,
                    reason=f"dependency_for::{layer_name}",
                )
                dependencies_activated.append(dependency)

        governor.transition_layer(
            layer_name,
            LayerState.ACTIVE,
            reason=request.reason,
        )
        self.activation_guard.record_activation(layer_name, request.trigger_signal)
        return governor._record_transition(
            execution_id=execution_id,
            layer_name=layer_name,
            capability_name=request.capability_name,
            previous_state=previous_state,
            new_state=LayerState.ACTIVE,
            trigger_signal=request.trigger_signal,
            reason=request.reason,
            priority=request.priority,
            dependencies_activated=tuple(dependencies_activated),
            approved=True,
            rejection_reason=None,
        )


__all__ = ["DynamicLayerActivator"]
