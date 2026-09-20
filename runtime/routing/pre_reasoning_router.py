from __future__ import annotations

from typing import Any

from runtime.reasoning.dependency_activation_policy import (
    should_activate_context_generation,
    should_activate_dependency_memory,
    should_activate_dependency_reasoning,
    should_activate_process_dependencies,
    should_activate_truth_promotion,
)
from runtime.routing.task_profile import build_task_profile


ALL_LAYERS = [
    "task_loader",
    "grid_analysis",
    "object_detection",
    "pattern_rule",
    "inference",
    "transformation_solver",
    "evaluation",
    "dependency_reasoning",
    "process_semantic_synthesis",
    "context_discovery",
    "context_hierarchy",
    "semantic_context",
    "causal_validation",
    "truth_candidate",
    "truth_commit",
    "deep_governance",
    "adaptive_reuse",
    "world_model",
    "self_improvement",
    "meta_cognition",
    "reporting",
    "adaptive_memory_update",
]

BASE_REQUIRED_LAYERS = [
    "task_loader",
    "grid_analysis",
    "pattern_rule",
    "inference",
    "transformation_solver",
    "evaluation",
    "reporting",
]


class PreReasoningRouter:
    system_name = "pre_reasoning_router"

    def __init__(self):
        self.history: list[dict[str, Any]] = []
        self.reset()

    def reset(self) -> None:
        self.history = []
        self.metrics = {
            "pre_reasoning_router_enabled": True,
            "task_profiles_generated": 0,
            "selective_execution_enabled": True,
            "layers_enabled_count": 0,
            "layers_disabled_count": 0,
            "layers_deferred_count": 0,
            "full_stack_avoided": False,
            "estimated_layers_skipped": 0,
            "estimated_runtime_saved": 0.0,
            "skipped_reports_count": 0,
            "premature_reports_prevented": 0,
            "dependency_activation_attempted": False,
            "dependency_activation_successful": False,
            "dependency_activation_blocked": False,
        }

    def analyze_task(self, task, context=None) -> dict[str, Any]:
        profile = build_task_profile(task, context)
        self.metrics["task_profiles_generated"] += 1
        return profile

    def select_layers(self, task_profile, context=None) -> dict[str, Any]:
        context = context if isinstance(context, dict) else {}
        task_profile = task_profile if isinstance(task_profile, dict) else {}
        mode = str(
            context.get("requested_mode")
            or context.get("mode")
            or _budget_mode(context)
            or "adaptive"
        ).lower()
        if mode not in {"fast", "adaptive", "deep"}:
            mode = "adaptive"

        safety_overrides = self._safety_overrides(task_profile, context)
        dependency_policy = should_activate_dependency_reasoning(
            task_profile,
            context,
        )
        process_policy = should_activate_process_dependencies(
            task_profile,
            context,
        )
        memory_policy = should_activate_dependency_memory(
            task_profile,
            context,
        )
        context_policy = should_activate_context_generation(
            task_profile,
            context,
        )
        truth_policy = should_activate_truth_promotion(
            task_profile,
            context,
        )
        required = set(BASE_REQUIRED_LAYERS)
        optional = {
            "adaptive_memory_update",
            "adaptive_reuse",
            "meta_cognition",
            "self_improvement",
        }
        deferred = {"adaptive_memory_update"}

        if task_profile.get("requires_object_detection"):
            required.add("object_detection")
        if task_profile.get("requires_world_model"):
            required.add("world_model")
        if task_profile.get("requires_spatial_reasoning"):
            optional.add("dependency_reasoning")
        if task_profile.get("requires_context_discovery"):
            required.update({
                "dependency_reasoning",
                "process_semantic_synthesis",
                "context_discovery",
                "semantic_context",
            })
        if task_profile.get("requires_topology_reasoning"):
            required.add("dependency_reasoning")
        if (
            task_profile.get("requires_symmetry_reasoning")
            or task_profile.get("requires_counting")
            or task_profile.get("requires_growth_reasoning")
        ):
            required.add("dependency_reasoning")
        if dependency_policy["activate"]:
            required.update({
                "dependency_reasoning",
                "process_semantic_synthesis",
            })
            deferred.discard("dependency_reasoning")
        if context_policy["activate"]:
            required.update({
                "context_discovery",
                "semantic_context",
            })
            deferred.discard("context_discovery")
            deferred.discard("semantic_context")
        if task_profile.get("requires_truth_promotion"):
            required.update({"truth_candidate", "truth_commit"})
        if task_profile.get("requires_governance"):
            required.add("deep_governance")
        if task_profile.get("requires_cache_lookup"):
            optional.add("adaptive_reuse")

        if mode == "fast":
            optional.discard("self_improvement")
            optional.discard("meta_cognition")
            deferred.update({
                "context_hierarchy",
                "truth_candidate",
                "truth_commit",
                "deep_governance",
                "self_improvement",
            })
        elif mode == "adaptive":
            optional.update({"meta_cognition", "adaptive_reuse"})
            if (
                task_profile.get("confidence", 1.0) < 0.70
                or context.get("new_concept_detected") is True
            ):
                required.update({
                    "dependency_reasoning",
                    "context_discovery",
                    "semantic_context",
                })
        else:
            diagnostic_layers = {
                "deep_governance",
                "self_improvement",
                "adaptive_memory_update",
                "world_model",
                "truth_commit",
            }
            optional.difference_update(diagnostic_layers)
            optional.update({
                "adaptive_reuse",
                "causal_validation",
                "context_hierarchy",
                "meta_cognition",
            })
            if (
                task_profile.get("confidence", 1.0) < 0.82
                or dependency_policy["activate"]
                or context_policy["activate"]
            ):
                required.update({
                    "dependency_reasoning",
                    "process_semantic_synthesis",
                    "causal_validation",
                })
            audit_sections = set(context.get("audit_sections_requested", []) or [])
            if "truth" in audit_sections:
                optional.update({"truth_candidate", "truth_commit"})
            if "dependencies" in audit_sections:
                required.update({"dependency_reasoning", "process_semantic_synthesis"})
            if "lineage" in audit_sections:
                optional.add("context_hierarchy")
            if "cache" in audit_sections:
                optional.add("adaptive_memory_update")
            if "concepts" in audit_sections:
                optional.add("self_improvement")
            deferred.update(diagnostic_layers - required - optional)

        if context.get("new_concept_detected") is True:
            required.add("dependency_reasoning")
        if context.get("evidence_saturated") is True and task_profile.get("requires_context_discovery"):
            optional.add("truth_candidate")
        if truth_policy["activate"]:
            optional.add("truth_candidate")

        if safety_overrides:
            required.update({
                "causal_validation",
                "deep_governance",
                "meta_cognition",
            })
            deferred.discard("deep_governance")

        enabled = set(required)
        if mode == "deep":
            enabled.update(layer for layer in optional if layer not in deferred)
        elif mode == "adaptive":
            enabled.update(layer for layer in optional if layer not in deferred)
        elif safety_overrides:
            enabled.update({"meta_cognition"})

        disabled = [
            layer
            for layer in ALL_LAYERS
            if layer not in enabled and layer not in deferred
        ]
        skip_reasons = {
            layer: "not_required_by_task_profile"
            for layer in disabled
        }
        skip_reasons.update({
            layer: "deferred_by_selective_execution"
            for layer in deferred
            if layer not in enabled
        })
        dependency_activation_successful = "dependency_reasoning" in enabled
        dependency_activation_blocked = (
            dependency_policy["activate"]
            and not dependency_activation_successful
        )
        escalation_level = self._escalation_level(
            enabled,
            task_profile,
            dependency_policy,
            context_policy,
            truth_policy,
        )
        decision_reason = dependency_policy["reason"]
        router_decision_trace = {
            "detected_family": task_profile.get("task_family", "unknown_complex"),
            "detected_capabilities":
            list(task_profile.get("required_capabilities", [])),
            "suspected_concepts":
            list(task_profile.get("suspected_concepts", [])),
            "enabled_layers": sorted(enabled),
            "disabled_layers": sorted(disabled),
            "deferred_layers": sorted(
                layer for layer in deferred if layer not in enabled
            ),
            "dependency_reasoning_enabled":
            dependency_activation_successful,
            "process_dependencies_enabled":
            process_policy["activate"] and dependency_activation_successful,
            "dependency_memory_enabled":
            memory_policy["activate"] and dependency_activation_successful,
            "context_discovery_enabled":
            "context_discovery" in enabled,
            "truth_candidate_enabled":
            "truth_candidate" in enabled,
            "truth_commit_enabled":
            "truth_commit" in enabled,
            "router_confidence": task_profile.get("confidence", 0.0),
            "decision_reason": decision_reason,
            "dependency_activation_reason": dependency_policy["reason"],
            "context_activation_reason": context_policy["reason"],
            "truth_activation_reason": truth_policy["reason"],
            "matched_dependency_signals":
            dependency_policy.get("matched_signals", []),
            "matched_dependency_capabilities":
            dependency_policy.get("matched_capabilities", []),
            "escalation_level": escalation_level,
        }

        plan = {
            "system": self.system_name,
            "report_state": "final",
            "task_family": task_profile.get("task_family", "unknown_complex"),
            "enabled_layers": sorted(enabled),
            "disabled_layers": sorted(disabled),
            "deferred_layers": sorted(layer for layer in deferred if layer not in enabled),
            "required_layers": sorted(required),
            "optional_layers": sorted(optional),
            "skip_reasons": skip_reasons,
            "safety_overrides": safety_overrides,
            "dependency_reasoning_enabled":
            router_decision_trace["dependency_reasoning_enabled"],
            "context_discovery_enabled":
            router_decision_trace["context_discovery_enabled"],
            "truth_candidate_enabled":
            router_decision_trace["truth_candidate_enabled"],
            "truth_commit_enabled":
            router_decision_trace["truth_commit_enabled"],
            "router_confidence": task_profile.get("confidence", 0.0),
            "decision_reason": decision_reason,
            "dependency_activation_policy": dependency_policy,
            "process_dependency_activation_policy": process_policy,
            "dependency_memory_activation_policy": memory_policy,
            "context_generation_activation_policy": context_policy,
            "truth_promotion_activation_policy": truth_policy,
            "dependency_activation_attempted":
            dependency_policy["activate"],
            "dependency_activation_successful":
            dependency_activation_successful,
            "dependency_activation_blocked":
            dependency_activation_blocked,
            "dependency_activation_reason":
            dependency_policy["reason"],
            "router_decision_trace": router_decision_trace,
            "escalation_level": escalation_level,
            "execution_mode": "selective_deep" if mode == "deep" else "selective",
            "mode": mode,
            "confidence": task_profile.get("confidence", 0.0),
        }
        self.metrics.update({
            "layers_enabled_count": len(plan["enabled_layers"]),
            "layers_disabled_count": len(plan["disabled_layers"]),
            "layers_deferred_count": len(plan["deferred_layers"]),
            "full_stack_avoided": bool(plan["disabled_layers"] or plan["deferred_layers"]),
            "estimated_layers_skipped": len(plan["disabled_layers"]) + len(plan["deferred_layers"]),
            "estimated_runtime_saved": round(
                (len(plan["disabled_layers"]) + len(plan["deferred_layers"])) * 0.12,
                4,
            ),
            "premature_reports_prevented": len([
                layer for layer in plan["disabled_layers"]
                if layer in {"truth_candidate", "truth_commit", "context_hierarchy", "semantic_context"}
            ]),
            "dependency_activation_attempted":
            dependency_policy["activate"],
            "dependency_activation_successful":
            dependency_activation_successful,
            "dependency_activation_blocked":
            dependency_activation_blocked,
        })
        return plan

    def should_run(self, layer_name, task_profile=None, context=None) -> bool:
        context = context if isinstance(context, dict) else {}
        plan = context.get("pre_reasoning_execution_plan") or context.get("execution_plan")
        if not isinstance(plan, dict):
            if task_profile is None:
                return True
            plan = self.select_layers(task_profile, context)
        layer_name = self._canonical_layer_name(layer_name)
        if layer_name in set(plan.get("enabled_layers", [])):
            return True
        return False

    def build_execution_plan(self, task_profile, context=None) -> dict[str, Any]:
        plan = self.select_layers(task_profile, context)
        self.history.append(plan)
        return plan

    def skipped_report(self, layer_name, plan=None, reason=None) -> dict[str, Any]:
        layer_name = self._canonical_layer_name(layer_name)
        plan = plan if isinstance(plan, dict) else {}
        skip_reason = (
            reason
            or plan.get("skip_reasons", {}).get(layer_name)
            or "not_required_by_task_profile"
        )
        self.metrics["skipped_reports_count"] += 1
        return {
            "system": layer_name,
            "report_state": "skipped",
            "skipped": True,
            "skip_reason": skip_reason,
            "activation_rule":
            plan.get("dependency_activation_reason")
            or plan.get("decision_reason")
            or "not_required_by_task_profile",
            "recommended_next_step":
            "inspect_router_decision_trace_and_required_capabilities",
            "router": self.system_name,
        }

    def report(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "report_state": "final",
            **self.metrics,
            "last_execution_plan": self.history[-1] if self.history else {},
        }

    def _safety_overrides(self, task_profile, context):
        overrides = []
        risk_keys = {
            "safety_risk_detected": "safety_risk",
            "identity_risk_detected": "identity_risk",
            "contradiction_review_required": "contradiction_review",
            "governance_required": "governance_required",
        }
        for key, reason in risk_keys.items():
            if context.get(key) is True:
                overrides.append(reason)
        if task_profile.get("requires_governance"):
            overrides.append("task_profile_governance_required")
        return sorted(set(overrides))

    def _canonical_layer_name(self, layer_name):
        aliases = {
            "transformation": "transformation_solver",
            "program_synthesis": "transformation_solver",
            "reasoning": "inference",
            "governance": "deep_governance",
            "process_semantics": "process_semantic_synthesis",
            "world_modeling": "world_model",
        }
        return aliases.get(str(layer_name), str(layer_name))

    def _escalation_level(
        self,
        enabled,
        task_profile,
        dependency_policy,
        context_policy,
        truth_policy,
    ):
        if truth_policy.get("activate") and "truth_candidate" in enabled:
            return "LEVEL_6"
        if context_policy.get("activate") and "context_discovery" in enabled:
            return "LEVEL_5"
        if dependency_policy.get("activate") and "dependency_reasoning" in enabled:
            return "LEVEL_4"
        if (
            task_profile.get("requires_spatial_reasoning")
            or task_profile.get("requires_symmetry_reasoning")
        ):
            return "LEVEL_3"
        if (
            task_profile.get("requires_topology_reasoning")
            or task_profile.get("requires_growth_reasoning")
        ):
            return "LEVEL_2"
        return "LEVEL_1"


def _budget_mode(context):
    budget = context.get("current_reasoning_budget")
    if budget is None:
        return None
    if isinstance(budget, dict):
        return budget.get("mode")
    return getattr(budget, "mode", None)


pre_reasoning_router = PreReasoningRouter()


__all__ = [
    "ALL_LAYERS",
    "PreReasoningRouter",
    "pre_reasoning_router",
]
