# ============================================
# NEXRYN BUDGET POLICY
# ============================================

from dataclasses import dataclass, field


@dataclass
class ReasoningBudget:

    mode: str

    max_hypotheses: int

    max_reasoning_depth: int

    max_dependency_depth: int

    max_active_routes: int

    max_contexts: int

    telemetry_enabled: bool

    explanation_enabled: bool

    process_semantics_enabled: bool

    temporal_reasoning_enabled: bool

    full_governance_enabled: bool

    report_level: str

    execution_profile: str = "adaptive"

    cognitive_pipeline: str = "adaptive"

    notes: list[str] = field(default_factory=list)


class BudgetPolicy:

    def fast(self):

        return ReasoningBudget(
            mode="fast",
            execution_profile="fast",
            cognitive_pipeline="adaptive",
            max_hypotheses=2,
            max_reasoning_depth=2,
            max_dependency_depth=4,
            max_active_routes=3,
            max_contexts=4,
            telemetry_enabled=False,
            explanation_enabled=False,
            process_semantics_enabled=False,
            temporal_reasoning_enabled=False,
            full_governance_enabled=False,
            report_level="minimal",
            notes=[
                "fast_policy_selected",
                "minimum_safety_governance_preserved",
            ],
        )

    def adaptive(self):

        return ReasoningBudget(
            mode="adaptive",
            execution_profile="adaptive",
            cognitive_pipeline="adaptive",
            max_hypotheses=4,
            max_reasoning_depth=4,
            max_dependency_depth=6,
            max_active_routes=4,
            max_contexts=8,
            telemetry_enabled=True,
            explanation_enabled=True,
            process_semantics_enabled=True,
            temporal_reasoning_enabled=False,
            full_governance_enabled=False,
            report_level="normal",
            notes=[
                "adaptive_policy_selected",
                "minimum_safety_governance_preserved",
            ],
        )

    def deep(self):

        return ReasoningBudget(
            mode="deep",
            execution_profile="deep",
            cognitive_pipeline="adaptive",
            max_hypotheses=10,
            max_reasoning_depth=8,
            max_dependency_depth=12,
            max_active_routes=10,
            max_contexts=12,
            telemetry_enabled=True,
            explanation_enabled=True,
            process_semantics_enabled=True,
            temporal_reasoning_enabled=False,
            full_governance_enabled=True,
            report_level="full",
            notes=[
                "deep_policy_selected",
                "minimum_safety_governance_preserved",
            ],
        )

    def for_mode(self, mode):

        mode = str(mode or "adaptive").lower()

        if mode == "fast":
            return self.fast()

        if mode in {"deep", "full"}:
            return self.deep()

        return self.adaptive()

    def from_execution_profile(self, profile):

        return ReasoningBudget(
            mode=profile.name,
            execution_profile=profile.name,
            cognitive_pipeline=profile.pipeline_name,
            max_hypotheses=profile.max_hypotheses,
            max_reasoning_depth=profile.reasoning_depth,
            max_dependency_depth=profile.dependency_depth,
            max_active_routes=profile.search_budget,
            max_contexts=profile.max_contexts,
            telemetry_enabled=profile.telemetry_enabled,
            explanation_enabled=profile.explanation_enabled,
            process_semantics_enabled=profile.process_semantics_enabled,
            temporal_reasoning_enabled=profile.temporal_reasoning_enabled,
            full_governance_enabled=profile.full_governance_enabled,
            report_level=profile.report_level,
            notes=[
                f"{profile.name}_profile_selected",
                "unified_adaptive_pipeline",
                "minimum_safety_governance_preserved",
            ],
        )


budget_policy = BudgetPolicy()
