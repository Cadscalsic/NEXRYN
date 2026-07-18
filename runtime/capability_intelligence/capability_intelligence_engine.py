"""Top-level capability intelligence system."""

from __future__ import annotations

from typing import Any

from runtime.capability_intelligence.adaptive_capability_learning_engine import (
    AdaptiveCapabilityLearningEngine,
)
from runtime.capability_intelligence.capability_cooperation_engine import (
    CapabilityCooperationEngine,
)
from runtime.capability_intelligence.capability_cost_intelligence import (
    CapabilityCostIntelligence,
)
from runtime.capability_intelligence.capability_cost_predictor import CapabilityCostPredictor
from runtime.capability_intelligence.capability_effectiveness_tracker import (
    CapabilityEffectivenessTracker,
)
from runtime.capability_intelligence.capability_recommendation_engine import (
    CapabilityRecommendationEngine,
    CapabilityRecommendationState,
)
from runtime.capability_intelligence.capability_retirement_detector import (
    CapabilityRetirementDetector,
)
from runtime.capability_intelligence.capability_usage_statistics import (
    CapabilityUsageStatistics,
)
from runtime.capability_intelligence.policy_recommendation_engine import (
    PolicyRecommendationEngine,
)
from runtime.capability_intelligence.strategy_descriptor import StrategyDescriptor
from runtime.capability_intelligence.strategy_memory_engine import StrategyMemoryEngine
from runtime.capability_intelligence.strategy_registry import StrategyRegistry
from runtime.capability_intelligence.task_family_memory import TaskFamilyMemory
from runtime.capability_intelligence.task_signature_mapper import TaskSignatureMapper


class CapabilityIntelligenceEngine:
    def __init__(self, capability_governor=None):
        self.capability_governor = capability_governor
        self.usage_statistics = CapabilityUsageStatistics()
        self.effectiveness_tracker = CapabilityEffectivenessTracker()
        self.cost_intelligence = CapabilityCostIntelligence()
        self.cooperation_engine = CapabilityCooperationEngine()
        self.strategy_memory = StrategyMemoryEngine()
        self.strategy_registry = StrategyRegistry()
        self.task_family_memory = TaskFamilyMemory()
        self.task_signature_mapper = TaskSignatureMapper()
        self.policy_recommendation_engine = PolicyRecommendationEngine()
        self.retirement_detector = CapabilityRetirementDetector()
        self.cost_predictor = CapabilityCostPredictor(
            self.cost_intelligence,
            self.effectiveness_tracker,
        )
        self.recommendation_engine = CapabilityRecommendationEngine()
        self.learning_engine = AdaptiveCapabilityLearningEngine(
            self.usage_statistics,
            self.effectiveness_tracker,
            self.cost_intelligence,
            self.cooperation_engine,
            self.strategy_memory,
            self.task_family_memory,
        )
        self.strategy_lookup_count = 0
        self.policy_recommendation_count = 0

    def register_strategy(self, strategy: StrategyDescriptor) -> StrategyDescriptor:
        return self.strategy_registry.register(strategy)

    def recommend_for_task(
        self,
        task_profile: Any,
        policy: str = "BALANCED",
    ) -> dict[str, Any]:
        signature = self.task_signature_mapper.map_profile(task_profile)
        self.strategy_lookup_count += 1
        strategies = self.strategy_memory.lookup(signature.task_family, policy)
        historical_strategy_count = len(strategies)
        registry_strategies = self.strategy_registry.by_task_family(signature.task_family)
        expected = set(getattr(task_profile, "expected_capabilities", set()) or set())
        optional = set(getattr(task_profile, "potential_capabilities", set()) or set())
        candidates = sorted(expected.union(optional))
        if self.capability_governor is not None and self.capability_governor.capability_registry.all():
            candidates = sorted({
                item.capability_name for item in self.capability_governor.capability_registry.all()
            }.intersection(set(candidates)) or set(candidates))
            allowed = {
                item.capability_name
                for item in self.capability_governor.capability_registry.all()
                if item.allows_policy(policy)
            }
        else:
            allowed = set(candidates)
        cost_predictions = {
            name: self.cost_predictor.predict(name)
            for name in candidates
        }
        effectiveness = {
            name: self.effectiveness_tracker.score(name)
            for name in candidates
        }
        recommendations = self.recommendation_engine.recommend(
            candidates,
            expected,
            optional,
            effectiveness,
            cost_predictions,
            policy_allowed=allowed,
        )
        self.policy_recommendation_count += 1
        policy_rec = self.policy_recommendation_engine.recommend(
            signature.task_family,
            getattr(task_profile, "task_complexity", "LOW"),
        )
        return {
            "task_signature": signature.as_dict(),
            "task_family": signature.task_family,
            "historical_strategy_count": historical_strategy_count,
            "registry_strategy_count": len(registry_strategies),
            "recommendations": [item.as_dict() for item in recommendations],
            "recommended_capabilities": [
                item.capability_name for item in recommendations
                if item.recommendation == CapabilityRecommendationState.RECOMMENDED
            ],
            "optional_capabilities": [
                item.capability_name for item in recommendations
                if item.recommendation == CapabilityRecommendationState.OPTIONAL
            ],
            "avoided_capabilities": [
                item.capability_name for item in recommendations
                if item.recommendation == CapabilityRecommendationState.AVOID
            ],
            "unknown_capabilities": [
                item.capability_name for item in recommendations
                if item.recommendation == CapabilityRecommendationState.UNKNOWN
            ],
            "policy_recommendation": policy_rec,
            "capability_priorities": {
                item.capability_name: item.priority for item in recommendations
            },
            "cost_predictions": cost_predictions,
            "strategy_recommendation": (
                strategies[0].as_dict()
                if strategies
                else (registry_strategies[0].as_dict() if registry_strategies else None)
            ),
        }

    def learn_from_execution(self, **kwargs: Any):
        return self.learning_engine.learn_from_execution(**kwargs)

    def build_report(self, task_profile: Any, policy: str = "BALANCED", governor_approval_status: str = "UNKNOWN") -> dict[str, Any]:
        recommendation = self.recommend_for_task(task_profile, policy)
        cooperation = [item.as_dict() for item in self.cooperation_engine.best_pairs()]
        cost_summary = self.cost_intelligence.as_dict()
        report = {
            "CAPABILITY_INTELLIGENCE_REPORT": True,
            "task_family": recommendation["task_family"],
            "historical_strategy_count": recommendation["historical_strategy_count"],
            "recommended_capabilities": recommendation["recommended_capabilities"],
            "optional_capabilities": recommendation["optional_capabilities"],
            "avoided_capabilities": recommendation["avoided_capabilities"],
            "policy_recommendation": recommendation["policy_recommendation"]["recommended_policy"],
            "capability_priorities": recommendation["capability_priorities"],
            "capability_cooperation_summary": cooperation,
            "strategy_recommendation": recommendation["strategy_recommendation"],
            "capability_cost_summary": cost_summary,
            "governor_approval_status": governor_approval_status,
            "observability_metrics": {
                "capability_recommendation_count": len(recommendation["recommendations"]),
                "strategy_lookup_count": self.strategy_lookup_count,
                "task_family_count": len(self.task_family_memory.records),
                "historical_strategy_count": self.strategy_memory.count(),
                "capability_priority_count": len(recommendation["capability_priorities"]),
                "capability_cost_predictions": len(recommendation["cost_predictions"]),
                "policy_recommendations": self.policy_recommendation_count,
                "capability_effectiveness_metrics": self.effectiveness_tracker.as_dict(),
                "resource_efficiency_metrics": self.cost_intelligence.as_dict(),
                "strategy_effectiveness_metrics": [item.as_dict() for item in self.strategy_memory.records],
            },
        }
        return report

    def render_report(self, task_profile: Any, policy: str = "BALANCED") -> str:
        report = self.build_report(task_profile, policy)
        lines = [
            "==================================================",
            "CAPABILITY INTELLIGENCE REPORT",
            "==================================================",
            "",
            "Task Family:",
            report["task_family"],
            "",
            "Historical Strategy Count:",
            str(report["historical_strategy_count"]),
            "",
            "Recommended Capabilities:",
        ]
        lines.extend([f"- {item}" for item in report["recommended_capabilities"]] or ["- none"])
        lines.extend(["", "Optional:"])
        lines.extend([f"- {item}" for item in report["optional_capabilities"]] or ["- none"])
        lines.extend(["", "Avoid:"])
        lines.extend([f"- {item}" for item in report["avoided_capabilities"]] or ["- none"])
        lines.extend([
            "",
            "Recommended Policy:",
            report["policy_recommendation"],
            "",
            "Governor Approval:",
            report["governor_approval_status"],
        ])
        return "\n".join(lines)


__all__ = ["CapabilityIntelligenceEngine"]
