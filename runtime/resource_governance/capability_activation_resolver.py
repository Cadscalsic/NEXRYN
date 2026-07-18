"""Resolve runtime signals to capability activation requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class CapabilityActivationRule:
    trigger_signal: str
    required_capability: str
    target_layer: str
    activation_reason: str
    activation_priority: str = "MEDIUM"
    policy_constraints: tuple[str, ...] = ()
    dependency_requirements: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "trigger_signal": self.trigger_signal,
            "required_capability": self.required_capability,
            "target_layer": self.target_layer,
            "activation_reason": self.activation_reason,
            "activation_priority": self.activation_priority,
            "policy_constraints": list(self.policy_constraints),
            "dependency_requirements": list(self.dependency_requirements),
        }


@dataclass(frozen=True)
class CapabilityActivationRequest:
    capability_name: str
    target_layer: str
    reason: str
    priority: str = "MEDIUM"
    trigger_signal: str = "MANUAL_REQUEST"
    policy_constraints: tuple[str, ...] = ()
    dependency_requirements: tuple[str, ...] = ()
    fallback_capability: str | None = None


DEFAULT_SIGNAL_RULES = (
    CapabilityActivationRule("TOPOLOGY_CHANGE_DETECTED", "topology_reasoning", "topology_reasoning", "component merge evidence requires topology analysis", "HIGH", dependency_requirements=("object_tracking", "spatial_reasoning")),
    CapabilityActivationRule("HOLE_CHANGE_DETECTED", "topology_reasoning", "topology_reasoning", "hole evidence requires topology analysis", "HIGH", dependency_requirements=("object_tracking", "spatial_reasoning")),
    CapabilityActivationRule("SPATIAL_RELATION_DETECTED", "spatial_reasoning", "spatial_reasoning", "spatial relation evidence requires spatial analysis", "MEDIUM", dependency_requirements=("object_tracking",)),
    CapabilityActivationRule("ROTATION_SIGNAL_DETECTED", "rotation_execution", "rotation_execution", "rotation signal requires rotation execution support", "MEDIUM", dependency_requirements=("semantic_compilation",)),
    CapabilityActivationRule("REFLECTION_SIGNAL_DETECTED", "reflection_execution", "reflection_execution", "reflection signal requires reflection execution support", "MEDIUM", dependency_requirements=("semantic_compilation",)),
    CapabilityActivationRule("SCALING_SIGNAL_DETECTED", "scaling_execution", "scaling_execution", "scaling signal requires scaling execution support", "MEDIUM", dependency_requirements=("semantic_compilation",)),
    CapabilityActivationRule("PATH_SIGNAL_DETECTED", "path_reasoning", "path_reasoning", "path evidence requires path reasoning support", "MEDIUM", dependency_requirements=("object_tracking", "spatial_reasoning")),
    CapabilityActivationRule("GRAVITY_SIGNAL_DETECTED", "gravity_reasoning", "gravity_reasoning", "gravity evidence requires physics reasoning", "HIGH", dependency_requirements=("object_tracking", "spatial_reasoning")),
    CapabilityActivationRule("COLOR_MAPPING_SIGNAL_DETECTED", "color_mapping", "color_mapping", "color mapping evidence requires mapping support", "LOW"),
    CapabilityActivationRule("COMPILER_REJECTED", "program_generation", "program_generation", "compiler rejection requires program generation fallback", "HIGH", dependency_requirements=("semantic_compilation",)),
    CapabilityActivationRule("LOCALIZED_RESIDUAL", "localized_repair", "localized_repair", "localized residual requires bounded repair", "HIGH", dependency_requirements=("object_tracking",)),
    CapabilityActivationRule("CONTRADICTION_DETECTED", "contradiction_resolution", "contradiction_resolution", "contradiction requires deeper validation", "HIGH", dependency_requirements=("dependency_reasoning",)),
    CapabilityActivationRule("SINGLE_SOURCE_DOMINANCE", "alternative_proposal_source", "alternative_proposal_source", "single source dominance requires an alternative proposal source", "MEDIUM"),
    CapabilityActivationRule("DEPENDENCY_GAP_DETECTED", "dependency_reasoning", "dependency_reasoning", "dependency gap requires dependency reasoning", "HIGH"),
)


class CapabilityActivationResolver:
    def __init__(self, capability_layer_map: Mapping[str, str] | None = None):
        self.capability_layer_map = dict(capability_layer_map or {})
        self.rules = {rule.trigger_signal: rule for rule in DEFAULT_SIGNAL_RULES}

    def resolve_signal(self, signal_type: str, payload: Mapping[str, Any] | None = None) -> CapabilityActivationRequest | None:
        rule = self.rules.get(str(signal_type))
        if rule is None:
            return None
        payload = dict(payload or {})
        target_layer = payload.get("target_layer") or self.capability_layer_map.get(rule.required_capability) or rule.target_layer
        if str(signal_type) == "COMPILER_REJECTED" and payload.get("reason") == "no_executable_semantic_intents":
            target_layer = self.capability_layer_map.get("program_generation", "program_generation")
        return CapabilityActivationRequest(
            capability_name=rule.required_capability,
            target_layer=str(target_layer),
            reason=rule.activation_reason,
            priority=rule.activation_priority,
            trigger_signal=rule.trigger_signal,
            policy_constraints=rule.policy_constraints,
            dependency_requirements=rule.dependency_requirements,
            fallback_capability=payload.get("fallback_capability"),
        )

    def resolve_capability(self, capability_name: str, reason: str = "capability_requested") -> CapabilityActivationRequest:
        target_layer = self.capability_layer_map.get(str(capability_name), str(capability_name))
        return CapabilityActivationRequest(
            capability_name=str(capability_name),
            target_layer=target_layer,
            reason=reason,
            priority="MEDIUM",
            trigger_signal="MANUAL_REQUEST",
        )


__all__ = [
    "CapabilityActivationRequest",
    "CapabilityActivationResolver",
    "CapabilityActivationRule",
    "DEFAULT_SIGNAL_RULES",
]
