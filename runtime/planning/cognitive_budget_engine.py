# ============================================
# NEXRYN COGNITIVE BUDGET ENGINE
# ============================================

from runtime.planning.budget_policy import (
    BudgetPolicy,
    ReasoningBudget,
)
from runtime.planning.execution_profile import build_execution_profile
from runtime.meta.supervisor import meta_supervisor


class CognitiveBudgetEngine:

    def __init__(self, policy=None):

        self.policy = policy or BudgetPolicy()

    def allocate(
        self,
        task_profile,
        cognitive_cost,
        requested_mode=None,
    ):

        if not meta_supervisor.is_action_allowed("reasoning"):
            budget = self.policy.fast()
            budget.max_reasoning_depth = 0
            budget.max_active_routes = 0
            budget.max_hypotheses = 0
            budget.process_semantics_enabled = False
            budget.notes.append("blocked_by_meta_supervisor")
            return budget

        mode = self._select_mode(
            task_profile,
            cognitive_cost,
            requested_mode,
        )
        execution_profile = build_execution_profile(mode)

        if mode == "fast":
            budget = self.policy.fast()
        elif mode in {"deep", "full"}:
            budget = self.policy.from_execution_profile(execution_profile)
        else:
            budget = self._adaptive_budget(
                task_profile,
                cognitive_cost,
                execution_profile=execution_profile,
            )

        budget.notes.append(
            f"complexity={task_profile.complexity}"
        )
        budget.notes.append(
            f"estimated_cost={cognitive_cost.total_cost}"
        )

        return self._apply_safety_floor(budget)

    def build_report(self, budget):

        return {
            "selected_mode": budget.mode,
            "execution_profile": budget.execution_profile,
            "cognitive_pipeline": budget.cognitive_pipeline,
            "max_hypotheses": budget.max_hypotheses,
            "max_reasoning_depth": budget.max_reasoning_depth,
            "max_dependency_depth": budget.max_dependency_depth,
            "max_active_routes": budget.max_active_routes,
            "telemetry_enabled": budget.telemetry_enabled,
            "explanation_enabled": budget.explanation_enabled,
            "process_semantics_enabled": budget.process_semantics_enabled,
            "report_level": budget.report_level,
        }

    def reduce_telemetry_if_saturated(
        self,
        budget,
        runtime_context,
    ):

        runtime_context = runtime_context if isinstance(runtime_context, dict) else {}
        evidence_saturated = runtime_context.get("evidence_saturated") is True
        coverage = self._clamp(
            runtime_context.get("dependency_chain_coverage", 0.0)
        )
        quality = self._clamp(
            runtime_context.get("dependency_explanation_quality", 0.0)
        )
        should_reduce = (
            evidence_saturated
            and coverage > 0.95
            and quality > 0.95
        )
        if budget is None:
            return {
                "telemetry_reduced": False,
                "telemetry_enabled": runtime_context.get(
                    "telemetry_enabled",
                    True,
                ),
                "evidence_saturated": evidence_saturated,
                "dependency_chain_coverage": coverage,
                "dependency_explanation_quality": quality,
                "reduction_skipped": "reasoning_budget_unavailable",
            }
        if should_reduce:
            budget.telemetry_enabled = False
            budget.report_level = "summary"
            if "telemetry_reduced_after_saturation" not in budget.notes:
                budget.notes.append("telemetry_reduced_after_saturation")
        return {
            "telemetry_reduced": should_reduce,
            "telemetry_enabled": budget.telemetry_enabled,
            "evidence_saturated": evidence_saturated,
            "dependency_chain_coverage": coverage,
            "dependency_explanation_quality": quality,
        }

    def as_legacy_pipeline_budget(self, budget):

        return {
            "mode": budget.mode,
            "execution_profile": budget.execution_profile,
            "cognitive_pipeline": budget.cognitive_pipeline,
            "pipeline_name": budget.cognitive_pipeline,
            "max_chain_depth": budget.max_dependency_depth,
            "max_concepts": budget.max_hypotheses,
            "telemetry_enabled": budget.telemetry_enabled,
            "cache_dependencies": False,
            "report_level": budget.report_level,
            "max_hypotheses": budget.max_hypotheses,
            "max_reasoning_depth": budget.max_reasoning_depth,
            "max_dependency_depth": budget.max_dependency_depth,
            "max_active_routes": budget.max_active_routes,
            "max_contexts": budget.max_contexts,
            "explanation_enabled": budget.explanation_enabled,
            "process_semantics_enabled":
            budget.process_semantics_enabled,
            "temporal_reasoning_enabled":
            budget.temporal_reasoning_enabled,
            "full_governance_enabled": budget.full_governance_enabled,
        }

    def _select_mode(
        self,
        task_profile,
        cognitive_cost,
        requested_mode,
    ):

        requested_mode = str(requested_mode or "").lower()
        if requested_mode in {"fast", "adaptive", "deep", "full"}:
            return requested_mode

        if task_profile.complexity == "low":
            return "fast"

        if task_profile.complexity == "high":
            return "deep"

        if cognitive_cost.total_cost >= 0.70:
            return "deep"

        return "adaptive"

    def _adaptive_budget(
        self,
        task_profile,
        cognitive_cost,
        execution_profile=None,
    ):

        cost = self._clamp(cognitive_cost.total_cost)
        uncertainty = self._clamp(task_profile.uncertainty)
        process = self._clamp(task_profile.process_complexity)

        max_hypotheses = self._range_value(3, 6, cost)
        max_reasoning_depth = self._range_value(
            2,
            6,
            max(cost, uncertainty),
        )
        max_dependency_depth = self._range_value(
            4,
            8,
            max(cost, process),
        )
        max_active_routes = self._range_value(3, 6, cost)

        execution_profile = execution_profile or build_execution_profile(
            "adaptive"
        )

        return ReasoningBudget(
            mode=execution_profile.name,
            execution_profile=execution_profile.name,
            cognitive_pipeline=execution_profile.pipeline_name,
            max_hypotheses=max_hypotheses,
            max_reasoning_depth=max_reasoning_depth,
            max_dependency_depth=max_dependency_depth,
            max_active_routes=max_active_routes,
            max_contexts=self._range_value(6, 10, cost),
            telemetry_enabled=cost >= 0.30 or uncertainty >= 0.45,
            explanation_enabled=(
                cost >= 0.40
                or uncertainty >= 0.45
                or task_profile.process_complexity >= 0.30
            ),
            process_semantics_enabled=(
                task_profile.process_complexity >= 0.30
                or task_profile.transformation_count >= 3
            ),
            temporal_reasoning_enabled=False,
            full_governance_enabled=False,
            report_level=execution_profile.report_level,
            notes=[
                "adaptive_policy_derived_from_task_profile",
                "unified_adaptive_pipeline",
                "minimum_safety_governance_preserved",
            ],
        )

    def _apply_safety_floor(self, budget):

        budget.max_dependency_depth = max(
            1,
            budget.max_dependency_depth,
        )
        budget.max_reasoning_depth = max(
            1,
            budget.max_reasoning_depth,
        )
        budget.max_hypotheses = max(
            1,
            budget.max_hypotheses,
        )
        budget.temporal_reasoning_enabled = False

        return budget

    @staticmethod
    def _range_value(low, high, score):

        score = max(0.0, min(1.0, float(score)))
        return int(round(low + (high - low) * score))

    @staticmethod
    def _clamp(value):

        return max(0.0, min(1.0, float(value)))


cognitive_budget_engine = CognitiveBudgetEngine()
