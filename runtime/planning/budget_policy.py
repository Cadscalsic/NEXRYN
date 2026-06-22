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

    notes: list[str] = field(default_factory=list)


class BudgetPolicy:

    def fast(self):

        return ReasoningBudget(
            mode="fast",
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

        if mode == "deep":
            return self.deep()

        return self.adaptive()


budget_policy = BudgetPolicy()
