"""Operational economy and knowledge crystallization diagnostics.

This module accounts for knowledge attrition and operational investment return
inside the existing operationalization pipeline. It does not add layers,
capability types, domains, or governance rules.
"""

from __future__ import annotations

from typing import Any, Mapping


class OperationalEconomyAnalysis:
    """Measure lifecycle efficiency from generated knowledge to citizens."""

    def analyze(
        self,
        *,
        generated_concepts: int = 0,
        generated_programs: int = 0,
        candidate_count: int = 0,
        arena_candidate_count: int = 0,
        compiled_programs: int = 0,
        validated_programs: int = 0,
        materialized_operational_capabilities: int = 0,
        operational_citizen_count: int = 0,
        expected_operational_capability_count: int = 0,
        known_operational_capability_count: int = 0,
        operational_experience_count: int = 0,
        candidate_attrition_summary: Mapping[str, Any] | None = None,
        capability_ecology_report: Mapping[str, Any] | None = None,
        capability_population_evolution_lag: float | None = None,
        generated_to_citizen_pressure_ratio: float | None = None,
        crystallization_candidate_count: int = 0,
        high_value_knowledge_items: int = 0,
        medium_value_knowledge_items: int = 0,
        low_value_knowledge_items: int = 0,
    ) -> dict[str, Any]:
        attrition = (
            candidate_attrition_summary
            if isinstance(candidate_attrition_summary, Mapping)
            else {}
        )
        ecology = capability_ecology_report if isinstance(capability_ecology_report, Mapping) else {}
        lifecycle = [
            ("generated_concepts", self._int(generated_concepts)),
            ("generated_programs", self._int(generated_programs)),
            ("candidate_count", self._int(candidate_count)),
            ("arena_candidate_count", self._int(arena_candidate_count)),
            ("compiled_programs", self._int(compiled_programs)),
            ("validated_programs", self._int(validated_programs)),
            (
                "materialized_operational_capabilities",
                self._int(materialized_operational_capabilities),
            ),
            ("operational_citizens", self._int(operational_citizen_count)),
        ]
        attrition_rows = self._attrition_rows(lifecycle)
        conversion_rates = {
            "concept_to_program": self._ratio(generated_programs, generated_concepts),
            "program_to_candidate": self._ratio(candidate_count, generated_programs),
            "candidate_to_arena": self._ratio(arena_candidate_count, candidate_count),
            "arena_to_compiled": self._ratio(compiled_programs, arena_candidate_count),
            "compiled_to_validated": self._ratio(validated_programs, compiled_programs),
            "validated_to_materialized": self._ratio(
                materialized_operational_capabilities,
                validated_programs,
            ),
            "materialized_to_citizen": self._ratio(
                operational_citizen_count,
                materialized_operational_capabilities,
            ),
            "concept_to_citizen": self._ratio(
                operational_citizen_count,
                generated_concepts,
            ),
        }
        knowledge_investment_units = (
            self._int(high_value_knowledge_items) * 3
            + self._int(medium_value_knowledge_items) * 2
            + self._int(low_value_knowledge_items)
        )
        total_generated_units = max(self._int(generated_concepts), 1)
        invested_units = max(knowledge_investment_units, total_generated_units)
        realized_units = (
            self._int(operational_citizen_count) * 5
            + self._int(materialized_operational_capabilities) * 4
            + self._int(validated_programs) * 3
            + self._int(compiled_programs) * 2
        )
        operational_investment_return = self._ratio(realized_units, invested_units)
        attrition_loss_score = self._average(
            row["loss_rate"] for row in attrition_rows
        )
        lifecycle_efficiency = self._average(conversion_rates.values())
        population_gap = max(
            self._int(expected_operational_capability_count)
            - self._int(known_operational_capability_count),
            0,
        )
        population_growth_pressure = self._ratio(
            population_gap,
            max(self._int(expected_operational_capability_count), 1),
        )
        crystallization_efficiency = (
            self._bounded_ratio(operational_citizen_count, crystallization_candidate_count)
            if self._int(crystallization_candidate_count) > 0
            else None
        )
        composite_candidates = ecology.get("composite_capability_candidates") or []
        composite_candidates = (
            composite_candidates if isinstance(composite_candidates, list) else []
        )
        operational_clusters = self._operational_clusters(composite_candidates)
        cluster_readiness = self._average(
            row.get("cluster_readiness") for row in operational_clusters
        )
        economy_health = self._average(
            [
                lifecycle_efficiency,
                min(operational_investment_return, 1.0),
                crystallization_efficiency,
                1.0 - population_growth_pressure,
                cluster_readiness,
            ]
        )
        crisis_score = self._average(
            [
                attrition_loss_score,
                population_growth_pressure,
                float(capability_population_evolution_lag or 0.0),
                1.0 - min(operational_investment_return, 1.0),
            ]
        )

        return {
            "system": "operational_economy_analysis",
            "operational_economy_health": economy_health,
            "knowledge_attrition_health": round(1.0 - attrition_loss_score, 4),
            "knowledge_attrition_loss_score": attrition_loss_score,
            "knowledge_attrition_state": self._state(
                attrition_loss_score,
                high="SEVERE_KNOWLEDGE_ATTRITION",
                medium="KNOWLEDGE_ATTRITION_PRESSURE",
                low="ATTRITION_WITHIN_EXPECTED_BOUNDS",
            ),
            "operational_investment_return": operational_investment_return,
            "operational_investment_return_state": self._state(
                1.0 - min(operational_investment_return, 1.0),
                high="LOW_OPERATIONAL_RETURN",
                medium="PARTIAL_OPERATIONAL_RETURN",
                low="HEALTHY_OPERATIONAL_RETURN",
            ),
            "knowledge_crystallization_efficiency": crystallization_efficiency,
            "knowledge_crystallization_pressure": self._ratio(
                crystallization_candidate_count,
                max(operational_citizen_count, 1),
            ),
            "operational_population_growth_pressure": population_growth_pressure,
            "capability_economy_crisis_score": crisis_score,
            "capability_economy_crisis_state": self._state(
                crisis_score,
                high="CAPABILITY_ECONOMY_CRISIS",
                medium="CAPABILITY_ECONOMY_PRESSURE",
                low="CAPABILITY_ECONOMY_STABLE",
            ),
            "capability_lifecycle_efficiency": lifecycle_efficiency,
            "knowledge_to_citizen_efficiency": conversion_rates["concept_to_citizen"],
            "candidate_attrition_cost": self._int(
                attrition.get("rejected_before_arena")
            ),
            "candidate_attrition_cost_state": (
                "CANDIDATE_LOSS_REQUIRES_REVIEW"
                if self._int(attrition.get("rejected_before_arena")) > 0
                else "NO_CANDIDATE_ATTRITION_COST"
            ),
            "knowledge_attrition_lifecycle": attrition_rows,
            "operational_lifecycle_conversion_rates": conversion_rates,
            "operational_economy_bottleneck": self._bottleneck(attrition_rows),
            "operational_economy_roadmap": self._roadmap(
                attrition_rows=attrition_rows,
                conversion_rates=conversion_rates,
                population_growth_pressure=population_growth_pressure,
                crystallization_efficiency=crystallization_efficiency,
                operational_investment_return=operational_investment_return,
            ),
            "operational_capability_clusters": operational_clusters,
            "operational_cluster_readiness": cluster_readiness,
            "operational_cluster_count": len(operational_clusters),
            "generated_to_citizen_pressure_ratio": generated_to_citizen_pressure_ratio,
            "operational_experience_count": self._int(operational_experience_count),
        }

    def _attrition_rows(self, lifecycle: list[tuple[str, int]]) -> list[dict[str, Any]]:
        rows = []
        for (source_name, source_count), (target_name, target_count) in zip(
            lifecycle,
            lifecycle[1:],
        ):
            conversion = self._ratio(target_count, source_count)
            loss = max(source_count - target_count, 0)
            loss_rate = round(1.0 - conversion, 4) if source_count else 0.0
            rows.append(
                {
                    "from_stage": source_name,
                    "to_stage": target_name,
                    "input_count": source_count,
                    "output_count": target_count,
                    "lost_count": loss,
                    "conversion_rate": conversion,
                    "loss_rate": loss_rate,
                    "attrition_state": self._state(
                        loss_rate,
                        high="SEVERE_ATTRITION",
                        medium="ATTRITION_PRESSURE",
                        low="CONTROLLED_ATTRITION",
                    ),
                }
            )
        return rows

    def _operational_clusters(
        self,
        composite_candidates: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        clusters = []
        for row in composite_candidates:
            if not isinstance(row, Mapping):
                continue
            readiness = float(row.get("composition_readiness") or 0.0)
            if readiness < 0.5:
                continue
            clusters.append(
                {
                    "cluster_name": row.get("composite_name"),
                    "member_capabilities": row.get("required_capabilities") or [],
                    "present_capabilities": row.get("present_capabilities") or [],
                    "missing_capabilities": row.get("missing_capabilities") or [],
                    "participating_domains": row.get("participating_domains") or [],
                    "cluster_readiness": readiness,
                    "cluster_state": (
                        "OPERATIONAL_CLUSTER_READY"
                        if readiness >= 1.0
                        else "PARTIAL_OPERATIONAL_CLUSTER"
                    ),
                }
            )
        clusters.sort(key=lambda item: (-item["cluster_readiness"], item["cluster_name"]))
        return clusters

    def _roadmap(
        self,
        *,
        attrition_rows: list[Mapping[str, Any]],
        conversion_rates: Mapping[str, float],
        population_growth_pressure: float,
        crystallization_efficiency: float,
        operational_investment_return: float,
    ) -> list[dict[str, Any]]:
        recommendations = []
        bottleneck = self._bottleneck(attrition_rows)
        if bottleneck != "none":
            recommendations.append(
                {
                    "priority": "knowledge_attrition",
                    "target": bottleneck,
                    "action": f"reduce_loss_between:{bottleneck}",
                }
            )
        if population_growth_pressure >= 0.5:
            recommendations.append(
                {
                    "priority": "operational_population_growth",
                    "target": "capability_population_evolution",
                    "action": "increase_citizen_conversion_without_new_layers",
                }
            )
        if crystallization_efficiency is None or crystallization_efficiency <= 0.25:
            recommendations.append(
                {
                    "priority": "knowledge_crystallization",
                    "target": "crystallization_candidate_to_citizen",
                    "action": "prioritize_validation_and_graduation_evidence",
                }
            )
        if operational_investment_return <= 0.35:
            recommendations.append(
                {
                    "priority": "operational_investment_return",
                    "target": "low_return_pipeline_stages",
                    "action": "measure_cost_of_rejected_candidates",
                }
            )
        if conversion_rates.get("arena_to_compiled", 1.0) <= 0.35:
            recommendations.append(
                {
                    "priority": "compiler_conversion",
                    "target": "arena_to_compiled",
                    "action": "focus_compiler_package_and_primitive_support",
                }
            )
        return recommendations[:7]

    def _bottleneck(self, attrition_rows: list[Mapping[str, Any]]) -> str:
        if not attrition_rows:
            return "none"
        row = sorted(
            attrition_rows,
            key=lambda item: (
                -float(item.get("loss_rate") or 0.0),
                str(item.get("from_stage")),
            ),
        )[0]
        if float(row.get("loss_rate") or 0.0) <= 0:
            return "none"
        return f"{row.get('from_stage')}->{row.get('to_stage')}"

    def _state(self, value: float, *, high: str, medium: str, low: str) -> str:
        if value >= 0.60:
            return high
        if value >= 0.30:
            return medium
        return low

    def _ratio(self, numerator: Any, denominator: Any) -> float:
        try:
            den = float(denominator)
            if den == 0:
                return 0.0
            return round(float(numerator or 0.0) / den, 4)
        except (TypeError, ValueError):
            return 0.0

    def _bounded_ratio(self, numerator: Any, denominator: Any) -> float:
        return min(max(self._ratio(numerator, denominator), 0.0), 1.0)

    def _average(self, values: Any) -> float:
        valid = [
            float(value)
            for value in values
            if isinstance(value, (int, float))
        ]
        return round(sum(valid) / len(valid), 4) if valid else 0.0

    def _int(self, value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0


operational_economy_analysis = OperationalEconomyAnalysis()


__all__ = [
    "OperationalEconomyAnalysis",
    "operational_economy_analysis",
]
