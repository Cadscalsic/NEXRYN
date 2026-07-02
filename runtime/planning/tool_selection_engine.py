# ============================================
# NEXRYN TOOL SELECTION ENGINE
# ============================================

from dataclasses import dataclass


@dataclass
class ToolSelection:

    enabled_tools: list[str]

    disabled_tools: list[str]

    selection_reason: dict


class ToolSelectionEngine:

    TOOL_CATEGORIES = [
        "object_tracking",
        "color_mapping",
        "spatial_reasoning",
        "dependency_reasoning",
        "process_semantics",
        "identity_governance",
        "truth_governance",
        "causal_validation",
        "temporal_reasoning",
        "telemetry",
        "explanation_generation",
        "strategy_evolution",
    ]

    SAFETY_TOOLS = [
        "identity_governance",
        "truth_governance",
        "contradiction_checks",
        "causal_validation",
    ]

    def select(
        self,
        task_profile,
        reasoning_budget,
    ):

        enabled = set(self.SAFETY_TOOLS)
        reasons = {
            "safety_floor":
            "identity, truth, contradiction, and causal checks remain enabled",
        }

        if task_profile.object_count > 0:
            enabled.add("object_tracking")
            reasons["object_tracking"] = "task contains detected objects"

        if task_profile.transformation_count > 0:
            enabled.add("color_mapping")
            reasons["color_mapping"] = "task contains transformations"

        if task_profile.spatial_complexity >= 0.15:
            enabled.add("spatial_reasoning")
            reasons["spatial_reasoning"] = "spatial complexity above baseline"

        task_identity = " ".join(
            str(getattr(task_profile, key, "") or "")
            for key in (
                "task_id",
                "task_path",
                "task_file",
                "concept_family",
                "task_family",
            )
        ).lower()
        concept_signals = []
        for key in (
            "target_concepts",
            "suspected_concepts",
            "required_capabilities",
        ):
            value = getattr(task_profile, key, [])
            if isinstance(value, (list, tuple, set)):
                concept_signals.extend(value)
            elif value:
                concept_signals.append(value)
        concept_text = " ".join(
            str(concept)
            for concept in concept_signals
            if concept
        ).lower()
        if any(
            marker in f"{task_identity} {concept_text}"
            for marker in (
                "spatial",
                "relative_position",
                "left_of",
                "right_of",
                "above",
                "below",
                "inside",
                "outside",
                "containment",
                "path_finding",
                "route_completion",
                "component_merging",
                "component_splitting",
                "topology_change",
                "topological",
                "connectivity",
            )
        ):
            enabled.add("spatial_reasoning")
            reasons["spatial_reasoning"] = (
                "task identity or target concepts indicate spatial reasoning"
            )

        if (
            reasoning_budget.max_dependency_depth > 0
            and (
                task_profile.process_complexity >= 0.30
                or task_profile.transformation_count >= 3
                or task_profile.complexity in {"medium", "high"}
            )
        ):
            enabled.add("dependency_reasoning")
            reasons["dependency_reasoning"] = "dependency budget allocated"

        if reasoning_budget.process_semantics_enabled:
            enabled.add("process_semantics")
            reasons["process_semantics"] = "process complexity requires it"

        if reasoning_budget.temporal_reasoning_enabled:
            enabled.add("temporal_reasoning")
            reasons["temporal_reasoning"] = "temporal reasoning requested"

        if reasoning_budget.telemetry_enabled:
            enabled.add("telemetry")
            reasons["telemetry"] = "budget telemetry is enabled"

        if reasoning_budget.explanation_enabled:
            enabled.add("explanation_generation")
            reasons["explanation_generation"] = "budget explanations enabled"

        if reasoning_budget.full_governance_enabled:
            enabled.add("strategy_evolution")
            reasons["strategy_evolution"] = "deep mode diagnostic coverage"

        disabled = [
            tool
            for tool in self.TOOL_CATEGORIES
            if tool not in enabled
        ]

        return ToolSelection(
            enabled_tools=sorted(enabled),
            disabled_tools=disabled,
            selection_reason=reasons,
        )

    def build_report(self, selection):

        return {
            "enabled_tools": selection.enabled_tools,
            "disabled_tools": selection.disabled_tools,
            "selection_reason": selection.selection_reason,
        }


tool_selection_engine = ToolSelectionEngine()
