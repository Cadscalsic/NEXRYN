"""Immutable cognitive purpose explanations for NEXRYN."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from runtime.world_governance.constitutional_identity import protect_core


META_PURPOSES: tuple[str, ...] = (
    "maximize_trustworthy_cognition",
    "maximize_adaptive_generalization",
    "maximize_efficient_reuse",
    "maximize_process_understanding",
    "maximize_contextual_understanding",
    "minimize_unnecessary_cognition",
    "preserve_identity_continuity",
    "preserve_truth_integrity",
    "support_human_development",
)

PURPOSE_DESCRIPTIONS = MappingProxyType({
    "maximize_trustworthy_cognition": "Cognition should remain reliable, governed, and evidence-aware.",
    "maximize_adaptive_generalization": "Learning should transfer beyond a narrow task instance.",
    "maximize_efficient_reuse": "Useful knowledge should be reused before expensive rediscovery.",
    "maximize_process_understanding": "NEXRYN should understand processes, not only outcomes.",
    "maximize_contextual_understanding": "Cognition should adapt to context without losing identity.",
    "minimize_unnecessary_cognition": "Reasoning should avoid waste when safe reuse is available.",
    "preserve_identity_continuity": "Evolution must not fracture NEXRYN's identity.",
    "preserve_truth_integrity": "Purpose cannot bypass truth governance or locked truth integrity.",
    "support_human_development": "Long-term cognition remains directed toward helping human users.",
})


class PurposeEngine:
    def purposes(self) -> tuple[str, ...]:
        return META_PURPOSES

    def why_this_goal_exists(self, goal: str) -> str:
        normalized = str(goal or "").strip().lower()
        return PURPOSE_DESCRIPTIONS.get(
            normalized,
            "This goal exists only if it supports trustworthy, generalizable, identity-safe cognition.",
        )

    def why_this_evolution_path_matters(
        self,
        path: Mapping[str, Any] | str,
    ) -> str:
        if isinstance(path, Mapping):
            target = path.get("direction") or path.get("selected_direction") or path.get("target") or "this path"
            value = path.get("expected_value", 0.0)
            return (
                f"{target} matters because it is expected to create long-term value "
                f"({value}) while remaining inside constitutional boundaries."
            )
        return (
            f"{path} matters when it improves generalization, reuse, process understanding, "
            "or trustworthy cognition without weakening identity."
        )

    def why_this_investment_is_prioritized(
        self,
        investment: Mapping[str, Any] | str,
    ) -> str:
        if isinstance(investment, Mapping):
            target = investment.get("target") or investment.get("domain") or "this investment"
            reason = investment.get("reason") or "it advances long-term objectives"
            return f"{target} is prioritized because {reason}."
        return f"{investment} is prioritized when it advances purpose more than it consumes resources."

    def purpose_alignment(
        self,
        values: Mapping[str, Any],
    ) -> float:
        if not protect_core(values)["allowed"]:
            return 0.0
        positive = [
            "generalization",
            "process_understanding",
            "strategy_reuse",
            "context_reuse",
            "memory_efficiency",
            "runtime_efficiency",
            "causal_reasoning",
            "cognitive_diversity",
            "trust_score",
        ]
        score = sum(self._number(values.get(key)) for key in positive) / len(positive)
        risk = max(
            self._number(values.get("identity_risk")),
            self._number(values.get("truth_risk")),
            self._number(values.get("governance_risk")),
        )
        return min(1.0, max(0.0, score * 0.75 + (1.0 - risk) * 0.25))

    def _number(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


purpose_engine = PurposeEngine()


__all__ = [
    "META_PURPOSES",
    "PURPOSE_DESCRIPTIONS",
    "PurposeEngine",
    "purpose_engine",
]
