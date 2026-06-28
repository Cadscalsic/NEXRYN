from __future__ import annotations

import re
from typing import Any


DEPENDENCY_ACTIVATION_SIGNALS = {
    "topology",
    "topological",
    "symmetry",
    "reflection",
    "rotation",
    "object interaction",
    "propagation",
    "causality",
    "causal",
    "counting",
    "growth",
    "scaling",
    "inside_outside",
    "inside outside",
    "structural transformation",
    "shape preservation",
    "shape_preservation",
    "topology preservation",
    "topology_preservation",
    "symmetry preservation",
    "symmetry_preservation",
    "symbolic remapping",
    "symbolic_remapping",
    "multi-object relations",
    "multi object relations",
    "context-sensitive transformations",
    "context sensitive transformations",
    "dependency",
    "dependencies",
    "relation",
    "relations",
    "process chain",
    "multi-step transformation",
    "topological growth",
    "topological_growth",
}

DEPENDENCY_CAPABILITIES = {
    "dependency_reasoning",
    "topology_reasoning",
    "symmetry_reasoning",
    "spatial_reasoning",
    "growth_reasoning",
    "gravity_reasoning",
    "counting",
    "symbolic_reasoning",
    "object_detection",
    "shape_analysis",
}


def should_activate_dependency_reasoning(
    task_profile: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    task_profile = task_profile if isinstance(task_profile, dict) else {}
    context = context if isinstance(context, dict) else {}
    matched = _matched_signals(task_profile, context)
    matched_capabilities = sorted(
        set(task_profile.get("required_capabilities", []))
        & DEPENDENCY_CAPABILITIES
    )
    confidence = _confidence(task_profile)

    if matched:
        return _decision(
            True,
            "mandatory_structural_dependency_signal",
            matched,
            matched_capabilities,
            confidence,
        )
    if matched_capabilities and not _simple_color_only(task_profile):
        return _decision(
            True,
            "required_capability_demands_dependency_reasoning",
            matched,
            matched_capabilities,
            confidence,
        )
    if confidence < 0.70:
        return _decision(
            True,
            "low_router_confidence_escalates_reasoning",
            matched,
            matched_capabilities,
            confidence,
        )
    if context.get("new_concept_detected") is True:
        return _decision(
            True,
            "new_concept_requires_dependency_recovery",
            matched,
            matched_capabilities,
            confidence,
        )
    return _decision(
        False,
        "no_structural_dependency_signal_detected",
        matched,
        matched_capabilities,
        confidence,
    )


def should_activate_process_dependencies(
    task_profile: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decision = should_activate_dependency_reasoning(task_profile, context)
    return {
        **decision,
        "policy": "process_dependency_activation",
    }


def should_activate_dependency_memory(
    task_profile: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decision = should_activate_dependency_reasoning(task_profile, context)
    return {
        **decision,
        "policy": "dependency_memory_activation",
    }


def should_activate_context_generation(
    task_profile: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dependency_decision = should_activate_dependency_reasoning(
        task_profile,
        context,
    )
    if dependency_decision["activate"]:
        return {
            **dependency_decision,
            "policy": "context_generation_activation",
            "reason": "dependency_reasoning_makes_context_generation_eligible",
        }
    return {
        **dependency_decision,
        "policy": "context_generation_activation",
    }


def should_activate_truth_promotion(
    task_profile: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = context if isinstance(context, dict) else {}
    context_count = int(context.get("context_count", 0) or 0)
    coverage = float(context.get("dependency_chain_coverage", 0.0) or 0.0)
    dependency_decision = should_activate_dependency_reasoning(
        task_profile,
        context,
    )
    if context_count > 0 and coverage > 0.0:
        return {
            **dependency_decision,
            "activate": True,
            "policy": "truth_promotion_activation",
            "reason": "contexts_and_dependency_evidence_available",
            "context_count": context_count,
            "dependency_chain_coverage": coverage,
        }
    return {
        **dependency_decision,
        "activate": dependency_decision["activate"],
        "policy": "truth_promotion_activation",
        "context_count": context_count,
        "dependency_chain_coverage": coverage,
    }


def explain_dependency_link_usage(report: dict[str, Any] | None) -> dict[str, Any]:
    report = report if isinstance(report, dict) else {}
    loaded = int(report.get("process_dependency_links_loaded", 0) or 0)
    used = int(report.get("process_dependency_links_used", 0) or 0)
    skipped = max(loaded - used, 0)
    if loaded <= 0:
        reason = "no_process_dependency_links_loaded"
    elif used > 0:
        reason = None
    elif report.get("cache_hit"):
        reason = "dependency_snapshot_reused_without_link_traversal"
    elif report.get("dependency_chain_depth", 0) <= 0:
        reason = "no_matching_dependency_chain_for_selected_concept"
    else:
        reason = "dependency_links_loaded_but_not_consumed"
    return {
        "process_dependency_links_loaded": loaded,
        "process_dependency_links_used": used,
        "dependency_links_skipped": skipped,
        "dependency_skip_reason": reason,
        "dependency_activation_attempted": loaded > 0,
        "dependency_activation_successful": used > 0,
        "dependency_activation_blocked": loaded > 0 and used == 0,
    }


def skipped_layer_report(
    layer_name: str,
    reason: str,
    activation_rule: str,
) -> dict[str, Any]:
    return {
        "system": str(layer_name),
        "report_state": "skipped",
        "skipped": True,
        "skip_reason": reason,
        "activation_rule": activation_rule,
        "recommended_next_step":
        "inspect_router_decision_trace_and_required_capabilities",
    }


def _decision(
    activate: bool,
    reason: str,
    matched_signals: list[str],
    matched_capabilities: list[str],
    confidence: float,
) -> dict[str, Any]:
    return {
        "activate": activate,
        "reason": reason,
        "activation_rule": reason,
        "matched_signals": matched_signals,
        "matched_capabilities": matched_capabilities,
        "router_confidence": confidence,
    }


def _simple_color_only(task_profile: dict[str, Any]) -> bool:
    return (
        task_profile.get("task_family") == "color_mapping"
        and set(task_profile.get("required_capabilities", []))
        <= {"color_analysis", "transformation_solver", "evaluation"}
    )


def _confidence(task_profile: dict[str, Any]) -> float:
    try:
        return float(task_profile.get("confidence", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _matched_signals(
    task_profile: dict[str, Any],
    context: dict[str, Any],
) -> list[str]:
    text = _search_text(task_profile, context)
    matched = []
    for signal in sorted(DEPENDENCY_ACTIVATION_SIGNALS):
        pattern = re.escape(signal).replace("\\ ", r"[\s_]+")
        if re.search(rf"(?<![a-z0-9]){pattern}(?![a-z0-9])", text):
            matched.append(signal)
    return matched


def _search_text(
    task_profile: dict[str, Any],
    context: dict[str, Any],
) -> str:
    values = [
        task_profile.get("task_family"),
        *task_profile.get("required_capabilities", []),
        *task_profile.get("suspected_concepts", []),
        context.get("task_family"),
        context.get("concept"),
        context.get("task_description"),
        context.get("prompt"),
        context.get("claim"),
    ]
    for key in (
        "required_capabilities",
        "suspected_concepts",
        "semantic_abstractions",
        "prioritized_concepts",
    ):
        value = context.get(key)
        if isinstance(value, list):
            values.extend(value)
    return " ".join(str(value or "").lower() for value in values)


__all__ = [
    "DEPENDENCY_ACTIVATION_SIGNALS",
    "should_activate_dependency_reasoning",
    "should_activate_process_dependencies",
    "should_activate_dependency_memory",
    "should_activate_context_generation",
    "should_activate_truth_promotion",
    "explain_dependency_link_usage",
    "skipped_layer_report",
]
