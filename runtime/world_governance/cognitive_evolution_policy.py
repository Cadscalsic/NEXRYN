"""Strategic cognitive evolution policy for NEXRYN."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.world_governance.cognitive_diversity_manager import (
    cognitive_diversity_manager,
)
from runtime.world_governance.evolution_objectives import (
    DEFAULT_EVOLUTION_OBJECTIVES,
    EvolutionObjectives,
)
from runtime.world_governance.growth_opportunity_detector import (
    growth_opportunity_detector,
)
from runtime.world_governance.investment_allocator import (
    investment_allocator,
)
from runtime.world_governance.stagnation_detector import stagnation_detector
from runtime.world_governance.world_governance_reporter import (
    world_governance_reporter,
)


class CognitiveEvolutionPolicyEngine:
    def __init__(
        self,
        objectives: EvolutionObjectives | None = None,
    ):
        self.objectives = objectives or DEFAULT_EVOLUTION_OBJECTIVES
        self.growth_detector = growth_opportunity_detector
        self.diversity_manager = cognitive_diversity_manager
        self.stagnation_detector = stagnation_detector
        self.investment_allocator = investment_allocator

    def evaluate(
        self,
        runtime_context: Mapping[str, Any] | None = None,
        potential_worlds_report: Mapping[str, Any] | None = None,
        objectives: EvolutionObjectives | None = None,
    ) -> dict[str, Any]:
        context = dict(runtime_context or {})
        active_objectives = objectives or self.objectives
        if objectives is not None:
            self.investment_allocator.objectives = active_objectives

        opportunities = self.growth_detector.detect(
            context,
            potential_worlds_report,
        )
        diversity_report = self.diversity_manager.evaluate(context)
        stagnation = self.stagnation_detector.assess(context)
        allocations = self.investment_allocator.allocate(
            opportunities,
            context,
            diversity_report,
        )

        frozen = [
            decision.target
            for decision in allocations
            if decision.action == "FREEZE"
        ]
        expansion_targets = [
            decision.target
            for decision in allocations
            if decision.action in {"EXPAND", "DIVERSIFY", "STABILIZE"}
            and decision.resource_budget > 0.0
        ]
        budget_used = sum(decision.resource_budget for decision in allocations)
        budget_available = self._budget(context)

        report = {
            "COGNITIVE_EVOLUTION_REPORT": {
                "growth_opportunities": [
                    item.as_dict()
                    for item in opportunities
                ],
                "investment_allocations": [
                    item.as_dict()
                    for item in allocations
                ],
                "diversity_score": diversity_report.get("diversity_score", 0.0),
                "stagnation_level": stagnation.stagnation_level,
                "frozen_concepts": frozen,
                "expansion_targets": expansion_targets,
                "resource_budget_usage": {
                    "used": budget_used,
                    "available": budget_available,
                    "remaining": max(0.0, budget_available - budget_used),
                },
            },
            "evolution_objectives": active_objectives.normalized().as_dict(),
            "diversity_report": diversity_report,
            "stagnation_assessment": stagnation.as_dict(),
        }
        world_governance_reporter.record_cognitive_evolution_report(report)
        return report

    def _budget(self, context: Mapping[str, Any]) -> float:
        try:
            return min(1.0, max(0.0, float(context.get("cognitive_investment_budget", 1.0))))
        except (TypeError, ValueError):
            return 1.0


cognitive_evolution_policy_engine = CognitiveEvolutionPolicyEngine()


__all__ = [
    "CognitiveEvolutionPolicyEngine",
    "cognitive_evolution_policy_engine",
]
