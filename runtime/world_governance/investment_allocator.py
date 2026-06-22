"""Allocate cognitive investment toward safe long-term value."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from runtime.world_governance.constitutional_identity import protect_core
from runtime.world_governance.evolution_objectives import (
    DEFAULT_EVOLUTION_OBJECTIVES,
    EvolutionObjectives,
)
from runtime.world_governance.growth_opportunity_detector import GrowthOpportunity


ALLOWED_EVOLUTION_ACTIONS: tuple[str, ...] = (
    "EXPAND",
    "STABILIZE",
    "FREEZE",
    "DIVERSIFY",
    "QUARANTINE",
    "DEPRECATE",
)


@dataclass
class EvolutionDecision:
    target: str
    target_type: str
    action: str
    investment_score: float
    expected_value: float
    resource_budget: float
    diversity_impact: float
    identity_risk: float
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class InvestmentAllocator:
    def __init__(
        self,
        objectives: EvolutionObjectives | None = None,
    ):
        self.objectives = objectives or DEFAULT_EVOLUTION_OBJECTIVES

    def allocate(
        self,
        opportunities: list[GrowthOpportunity],
        runtime_context: Mapping[str, Any] | None = None,
        diversity_report: Mapping[str, Any] | None = None,
    ) -> list[EvolutionDecision]:
        context = dict(runtime_context or {})
        diversity = dict(diversity_report or {})
        total_budget = self._budget(context)
        decisions: list[EvolutionDecision] = []

        for opportunity in opportunities:
            decision = self._decision_for(opportunity, context, diversity)
            decisions.append(decision)

        positive = [
            item for item in decisions
            if item.action in {"EXPAND", "DIVERSIFY", "STABILIZE"}
        ]
        total_score = sum(max(0.0, item.investment_score) for item in positive) or 1.0

        allocated: list[EvolutionDecision] = []
        for decision in decisions:
            if decision.action in {"EXPAND", "DIVERSIFY", "STABILIZE"}:
                share = max(0.0, decision.investment_score) / total_score
                budget = min(total_budget, total_budget * share)
            else:
                budget = 0.0
            allocated.append(EvolutionDecision(
                decision.target,
                decision.target_type,
                decision.action,
                decision.investment_score,
                decision.expected_value,
                budget,
                decision.diversity_impact,
                decision.identity_risk,
                decision.reason,
            ))

        return sorted(
            allocated,
            key=lambda item: (item.resource_budget, item.investment_score),
            reverse=True,
        )

    def _decision_for(
        self,
        opportunity: GrowthOpportunity,
        context: Mapping[str, Any],
        diversity: Mapping[str, Any],
    ) -> EvolutionDecision:
        protection = protect_core({
            "target": opportunity.target,
            "target_type": opportunity.target_type,
        })
        saturated = opportunity.target in set(context.get("saturated_concepts", []) or [])
        locked = opportunity.target in set(context.get("locked_truths", []) or [])
        high_risk = opportunity.risk >= 0.70 or protection["protected_core_touched"]
        diversity_impact = self._diversity_impact(opportunity, diversity)
        investment_score = self._investment_score(opportunity, diversity_impact)

        if locked:
            action = "FREEZE"
            reason = "locked_truths_are_not_investment_targets"
            investment_score = 0.0
        elif saturated:
            action = "FREEZE"
            reason = "saturated_concept_should_remain_stable"
            investment_score = 0.0
        elif high_risk:
            action = "QUARANTINE"
            reason = "high_risk_mutation_not_eligible_for_investment"
            investment_score = 0.0
        elif opportunity.expected_value < 0.20:
            action = "DEPRECATE"
            reason = "low_value_candidate_should_not_receive_budget"
            investment_score = 0.0
        elif opportunity.opportunity_type in {
            "underrepresented_context",
            "missing_conceptual_coverage",
        }:
            action = "DIVERSIFY"
            reason = "target_improves_contextual_or_conceptual_coverage"
        elif opportunity.opportunity_type == "expensive_reasoning_loops":
            action = "STABILIZE"
            reason = "investment_should_reduce_reasoning_cost"
        elif opportunity.opportunity_type == "frequently_reused_strategy":
            action = "STABILIZE"
            reason = "reused_strategy_deserves_refinement_and_stability"
        else:
            action = "EXPAND"
            reason = "target_has_safe_long_term_cognitive_value"

        return EvolutionDecision(
            opportunity.target,
            opportunity.target_type,
            action,
            investment_score,
            opportunity.expected_value,
            0.0,
            diversity_impact,
            opportunity.risk,
            reason,
        )

    def _investment_score(
        self,
        opportunity: GrowthOpportunity,
        diversity_impact: float,
    ) -> float:
        objective_values = {
            "reasoning_accuracy": opportunity.expected_value,
            "generalization": opportunity.expected_value,
            "strategy_reuse": opportunity.expected_value if opportunity.target_type == "strategy" else 0.0,
            "memory_efficiency": opportunity.expected_value if opportunity.target_type in {"memory", "performance"} else 0.0,
            "contextual_understanding": opportunity.expected_value if opportunity.target_type == "context" else 0.0,
            "cognitive_diversity": max(0.0, diversity_impact),
            "runtime_efficiency": opportunity.expected_value if opportunity.target_type == "performance" else 0.0,
        }
        value = self.objectives.score(objective_values)
        maturity_gap = 1.0 - opportunity.maturity
        risk_penalty = opportunity.risk * 0.5
        return min(1.0, max(0.0, value * (0.7 + maturity_gap * 0.3) - risk_penalty))

    def _diversity_impact(
        self,
        opportunity: GrowthOpportunity,
        diversity: Mapping[str, Any],
    ) -> float:
        interventions = set(diversity.get("interventions", []) or [])
        if opportunity.opportunity_type in {
            "underrepresented_context",
            "missing_conceptual_coverage",
        }:
            return 0.6
        if "prevent_strategy_domination" in interventions and opportunity.target_type == "strategy":
            return 0.3
        if opportunity.opportunity_type == "frequently_reused_strategy":
            return -0.1
        return 0.1

    def _budget(self, context: Mapping[str, Any]) -> float:
        try:
            return min(1.0, max(0.0, float(context.get("cognitive_investment_budget", 1.0))))
        except (TypeError, ValueError):
            return 1.0


investment_allocator = InvestmentAllocator()


__all__ = [
    "ALLOWED_EVOLUTION_ACTIONS",
    "EvolutionDecision",
    "InvestmentAllocator",
    "investment_allocator",
]
