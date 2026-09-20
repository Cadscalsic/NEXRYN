"""Autonomous cognitive direction and purpose-guided recommendations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from runtime.world_governance.cognitive_compass import cognitive_compass
from runtime.world_governance.constitutional_identity import protect_core
from runtime.world_governance.long_term_objectives import (
    DEFAULT_LONG_TERM_OBJECTIVES,
    LongTermObjectives,
)
from runtime.world_governance.objective_tracker import objective_tracker
from runtime.world_governance.priority_allocator import priority_allocator
from runtime.world_governance.purpose_engine import purpose_engine
from runtime.world_governance.tradeoff_manager import tradeoff_manager
from runtime.world_governance.trajectory_estimator import trajectory_estimator
from runtime.world_governance.world_governance_reporter import (
    world_governance_reporter,
)
from runtime.world_governance.world_kernel import world_governance_kernel


ALLOWED_DIRECTIONS: tuple[str, ...] = (
    "EXPAND",
    "STABILIZE",
    "FREEZE",
    "DIVERSIFY",
    "OPTIMIZE",
    "EXPLORE",
)


@dataclass
class CognitiveDirectionDecision:
    direction: str
    target_domains: list[str]
    purpose_alignment: float
    expected_value: float
    estimated_cost: float
    identity_risk: float
    truth_risk: float
    recommendation: str
    explanation: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CognitiveDirectionEngine:
    def __init__(
        self,
        objectives: LongTermObjectives | None = None,
        kernel=world_governance_kernel,
    ):
        self.objectives = objectives or DEFAULT_LONG_TERM_OBJECTIVES
        self.kernel = kernel
        self.compass = cognitive_compass
        self.purpose_engine = purpose_engine
        self.objective_tracker = objective_tracker
        self.trajectory_estimator = trajectory_estimator
        self.priority_allocator = priority_allocator
        self.tradeoff_manager = tradeoff_manager

    def evaluate(
        self,
        runtime_context: Mapping[str, Any] | None = None,
        objectives: LongTermObjectives | None = None,
    ) -> dict[str, Any]:
        context = dict(runtime_context or {})
        active_objectives = objectives or self.objectives
        compass_state = self.compass.assess(context, active_objectives)
        tracker_report = self.objective_tracker.track(
            context,
            compass_state.objective_distance,
        )
        target_domains = self._target_domains(
            compass_state.objective_distance,
            context,
        )
        selected_direction = self._select_direction(
            target_domains,
            context,
            tracker_report,
        )
        trajectory = self.trajectory_estimator.estimate(
            selected_direction,
            target_domains,
            context,
            compass_state.objective_distance,
        )
        purpose_values = dict(compass_state.current_cognitive_state)
        purpose_values.update({
            "identity_risk": context.get("identity_risk", trajectory["identity_impact"]),
            "truth_risk": context.get("truth_risk", 0.0),
            "governance_risk": context.get("governance_risk", 0.0),
        })
        purpose_alignment = self.purpose_engine.purpose_alignment(purpose_values)
        resource_allocation = self.priority_allocator.allocate(
            target_domains,
            context,
            context.get("available_resources"),
        )
        tradeoffs = self.tradeoff_manager.analyze(context, selected_direction)
        expected_value = self._expected_value(
            trajectory,
            purpose_alignment,
            compass_state.objective_distance,
        )
        identity_risk = max(
            self._number(context.get("identity_risk")),
            trajectory["identity_impact"],
        )
        truth_risk = self._number(context.get("truth_risk"))

        recommendation = self._recommendation(
            selected_direction,
            purpose_alignment,
            expected_value,
            trajectory["estimated_cost"],
            identity_risk,
            truth_risk,
            context,
        )
        explanation = self.purpose_engine.why_this_evolution_path_matters({
            "direction": selected_direction,
            "expected_value": round(expected_value, 4),
            "target": ", ".join(target_domains),
        })

        decision = CognitiveDirectionDecision(
            selected_direction,
            target_domains,
            purpose_alignment,
            expected_value,
            trajectory["estimated_cost"],
            identity_risk,
            truth_risk,
            recommendation,
            explanation,
        )
        kernel_decision = None
        if protect_core(context)["allowed"]:
            kernel_decision = self.kernel.evaluate_evolution_permission({
                "candidate_name": f"direction::{selected_direction}",
                "candidate_type": "evolution_direction",
                "generalization": compass_state.objective_distance.get("generalization", 0.0),
                "process_understanding": compass_state.objective_distance.get("process_understanding", 0.0),
                "strategy_reuse": compass_state.objective_distance.get("strategy_reuse", 0.0),
                "runtime_efficiency": compass_state.objective_distance.get("runtime_efficiency", 0.0),
                "identity_risk": identity_risk,
                "truth_risk": truth_risk,
                "governance_risk": self._number(context.get("governance_risk")),
            })

        report = {
            "AUTONOMOUS_DIRECTION_REPORT": {
                "current_state": compass_state.current_cognitive_state,
                "desired_state": compass_state.desired_cognitive_state,
                "objective_distances": compass_state.objective_distance,
                "selected_direction": selected_direction,
                "target_domains": target_domains,
                "resource_allocation": resource_allocation,
                "expected_value": expected_value,
                "estimated_cost": trajectory["estimated_cost"],
                "purpose_alignment": purpose_alignment,
                "tradeoffs": tradeoffs,
                "trajectory_confidence": compass_state.trajectory_confidence,
            },
            "direction_decision": decision.as_dict(),
            "trajectory_estimate": trajectory,
            "objective_tracker": tracker_report,
            "kernel_decision": (
                kernel_decision.as_dict()
                if hasattr(kernel_decision, "as_dict")
                else kernel_decision
            ),
        }
        world_governance_reporter.record_autonomous_direction_report(report)
        return report

    def _target_domains(
        self,
        distances: Mapping[str, float],
        context: Mapping[str, Any],
    ) -> list[str]:
        frozen = set(context.get("frozen_concepts", []) or [])
        saturated = set(context.get("saturated_domains", []) or [])
        locked = set(context.get("locked_truths", []) or [])
        blocked = frozen | saturated | locked
        ranked = sorted(
            ((domain, value) for domain, value in distances.items() if domain not in blocked),
            key=lambda item: item[1],
            reverse=True,
        )
        targets = [domain for domain, value in ranked if value > 0.05][:3]
        return targets or [domain for domain, _ in ranked[:1]] or ["memory_efficiency"]

    def _select_direction(
        self,
        target_domains: list[str],
        context: Mapping[str, Any],
        tracker_report: Mapping[str, Any],
    ) -> str:
        saturated = set(context.get("saturated_domains", []) or [])
        if target_domains and all(domain in saturated for domain in target_domains):
            return "FREEZE"
        if tracker_report.get("stagnation"):
            return "EXPLORE"
        if "strategy_reuse" in target_domains or self._number(context.get("strategy_reuse_rate")) < self._number(context.get("target_strategy_reuse", 0.65)):
            return "OPTIMIZE"
        if "cognitive_diversity" in target_domains or self._number(context.get("diversity_score")) < 0.45:
            return "DIVERSIFY"
        if "runtime_efficiency" in target_domains or "memory_efficiency" in target_domains:
            return "STABILIZE"
        return "EXPAND"

    def _expected_value(
        self,
        trajectory: Mapping[str, float],
        purpose_alignment: float,
        distances: Mapping[str, float],
    ) -> float:
        avg_gap = sum(float(value) for value in distances.values()) / max(1, len(distances))
        value = (
            trajectory["expected_progress"] * 0.45
            + purpose_alignment * 0.35
            + avg_gap * 0.20
            - trajectory["estimated_cost"] * 0.15
        )
        return min(1.0, max(0.0, value))

    def _recommendation(
        self,
        direction: str,
        purpose_alignment: float,
        expected_value: float,
        estimated_cost: float,
        identity_risk: float,
        truth_risk: float,
        context: Mapping[str, Any],
    ) -> str:
        if not protect_core(context)["allowed"]:
            return "BLOCKED_BY_CONSTITUTION"
        if identity_risk >= 0.65 or truth_risk >= 0.65:
            return "REQUIRE_REVIEW"
        if direction == "FREEZE":
            return "KEEP_STABLE"
        if purpose_alignment >= 0.55 and expected_value >= 0.30 and estimated_cost <= 0.75:
            return "PRIORITIZE"
        if purpose_alignment >= 0.40 and expected_value >= 0.20:
            return "PRIORITIZE_WITH_LIMITS"
        return "DEFER"

    def _number(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


cognitive_direction_engine = CognitiveDirectionEngine()


__all__ = [
    "ALLOWED_DIRECTIONS",
    "CognitiveDirectionDecision",
    "CognitiveDirectionEngine",
    "cognitive_direction_engine",
]
