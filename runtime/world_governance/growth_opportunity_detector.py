"""Detect long-term cognitive growth opportunities."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass
class GrowthOpportunity:
    target: str
    target_type: str
    opportunity_type: str
    expected_value: float
    maturity: float
    risk: float
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class GrowthOpportunityDetector:
    def detect(
        self,
        runtime_context: Mapping[str, Any] | None = None,
        potential_worlds_report: Mapping[str, Any] | None = None,
    ) -> list[GrowthOpportunity]:
        context = dict(runtime_context or {})
        potential = self._potential_report(context, potential_worlds_report)
        opportunities: list[GrowthOpportunity] = []

        if potential:
            candidate_name = str(potential.get("candidate_name") or "unnamed_candidate")
            expected_value = self._number(potential.get("world_score"))
            risk = max(
                self._number(potential.get("identity_risk")),
                self._number(potential.get("truth_risk")),
                self._number(potential.get("governance_risk")),
            )
            if expected_value > 0.0 and risk < 0.75:
                opportunities.append(GrowthOpportunity(
                    candidate_name,
                    str(potential.get("candidate_type") or "candidate"),
                    "high_value_candidate_world",
                    expected_value,
                    self._number(context.get("candidate_maturity")),
                    risk,
                    "potential_world_has_positive_long_term_value",
                ))

        for concept in self._items(context.get("concepts")):
            value = self._number(concept.get("value", concept.get("expected_value")))
            maturity = self._number(concept.get("maturity"))
            risk = self._risk(concept)
            if value >= 0.55 and maturity <= 0.45 and risk < 0.60:
                opportunities.append(GrowthOpportunity(
                    str(concept.get("name") or "unnamed_concept"),
                    "concept",
                    "high_value_concept_low_maturity",
                    value,
                    maturity,
                    risk,
                    "concept_has_value_but_needs_expansion",
                ))

        for strategy in self._items(context.get("strategies")):
            reuse_count = min(1.0, max(0.0, self._raw_number(strategy.get("reuse_count")) / 10.0))
            success = self._number(strategy.get("success_rate"))
            risk = self._risk(strategy)
            value = min(1.0, reuse_count * 0.5 + success * 0.5)
            if reuse_count >= 0.3 and success >= 0.65 and risk < 0.60:
                opportunities.append(GrowthOpportunity(
                    str(strategy.get("name") or "unnamed_strategy"),
                    "strategy",
                    "frequently_reused_strategy",
                    value,
                    self._number(strategy.get("maturity", success)),
                    risk,
                    "strategy_is_reused_often_and_worth_refinement",
                ))

        for gap in self._items(context.get("conceptual_coverage_gaps")):
            opportunities.append(GrowthOpportunity(
                str(gap.get("name") or gap.get("domain") or "coverage_gap"),
                "concept",
                "missing_conceptual_coverage",
                self._number(gap.get("severity", 0.5)),
                0.0,
                self._risk(gap),
                "missing_coverage_limits_generalization",
            ))

        for failure in self._items(context.get("failure_patterns")):
            opportunities.append(GrowthOpportunity(
                str(failure.get("name") or failure.get("pattern") or "failure_pattern"),
                "process",
                "repeated_failure_pattern",
                self._number(failure.get("frequency", 0.5)),
                0.0,
                self._risk(failure),
                "repeated_failure_pattern_requires_guided_learning",
            ))

        if self._number(context.get("expensive_reasoning_loop_rate")) >= 0.4:
            opportunities.append(GrowthOpportunity(
                "reasoning_loop_optimization",
                "performance",
                "expensive_reasoning_loops",
                self._number(context.get("expensive_reasoning_loop_rate")),
                0.2,
                0.2,
                "reasoning_cost_is_high_without_sufficient_reuse",
            ))

        for domain in self._items(context.get("underrepresented_contexts")):
            opportunities.append(GrowthOpportunity(
                str(domain.get("name") or domain.get("context") or "underrepresented_context"),
                "context",
                "underrepresented_context",
                self._number(domain.get("importance", 0.5)),
                self._number(domain.get("maturity")),
                self._risk(domain),
                "context_is_underrepresented_and_may_improve_transfer",
            ))

        return sorted(
            opportunities,
            key=lambda item: (item.expected_value - item.risk, item.expected_value),
            reverse=True,
        )

    def _potential_report(
        self,
        context: Mapping[str, Any],
        report: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        source = dict(report or context.get("POTENTIAL_WORLDS_REPORT") or {})
        if "POTENTIAL_WORLDS_REPORT" in source:
            return dict(source.get("POTENTIAL_WORLDS_REPORT") or {})
        return source

    def _items(self, value: Any) -> list[dict[str, Any]]:
        if isinstance(value, Mapping):
            return [dict(item, name=name) if isinstance(item, Mapping) else {"name": name, "value": item}
                    for name, item in value.items()]
        if isinstance(value, list):
            return [dict(item) for item in value if isinstance(item, Mapping)]
        return []

    def _risk(self, item: Mapping[str, Any]) -> float:
        return max(
            self._number(item.get("identity_risk")),
            self._number(item.get("truth_risk")),
            self._number(item.get("governance_risk")),
            self._number(item.get("risk")),
        )

    def _number(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0

    def _raw_number(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


growth_opportunity_detector = GrowthOpportunityDetector()


__all__ = [
    "GrowthOpportunity",
    "GrowthOpportunityDetector",
    "growth_opportunity_detector",
]
