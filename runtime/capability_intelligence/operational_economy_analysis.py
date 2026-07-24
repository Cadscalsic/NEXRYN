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
        operational_grounding_failure_count: int = 0,
        operational_grounding_failure_rate: float | None = None,
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
        cluster_operationalization = self._cluster_operationalization(
            operational_clusters=operational_clusters,
            materialized_operational_capabilities=materialized_operational_capabilities,
            operational_citizen_count=operational_citizen_count,
        )
        operationalization_choke = self._operationalization_choke_point(
            conversion_rates=conversion_rates,
            candidate_count=candidate_count,
            arena_candidate_count=arena_candidate_count,
            compiled_programs=compiled_programs,
            validated_programs=validated_programs,
            operational_grounding_failure_count=operational_grounding_failure_count,
            operational_grounding_failure_rate=operational_grounding_failure_rate,
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
            **operationalization_choke,
            "operational_economy_bottleneck": self._bottleneck(attrition_rows),
            "operational_economy_roadmap": self._roadmap(
                attrition_rows=attrition_rows,
                conversion_rates=conversion_rates,
                population_growth_pressure=population_growth_pressure,
                crystallization_efficiency=crystallization_efficiency,
                operational_investment_return=operational_investment_return,
                cluster_operationalization_state=cluster_operationalization[
                    "cluster_operationalization_state"
                ],
            ),
            "operational_capability_clusters": operational_clusters,
            "operational_cluster_readiness": cluster_readiness,
            "operational_cluster_count": len(operational_clusters),
            **cluster_operationalization,
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

    def _operationalization_choke_point(
        self,
        *,
        conversion_rates: Mapping[str, Any],
        candidate_count: int,
        arena_candidate_count: int,
        compiled_programs: int,
        validated_programs: int,
        operational_grounding_failure_count: int,
        operational_grounding_failure_rate: float | None,
    ) -> dict[str, Any]:
        stages = [
            (
                "candidate_to_arena",
                "candidate_count",
                self._int(candidate_count),
                "arena_candidate_count",
                self._int(arena_candidate_count),
                "candidate_admission",
            ),
            (
                "arena_to_compiled",
                "arena_candidate_count",
                self._int(arena_candidate_count),
                "compiled_programs",
                self._int(compiled_programs),
                (
                    "operational_grounding"
                    if float(operational_grounding_failure_rate or 0.0) >= 0.5
                    else "compiler_execution_or_support"
                ),
            ),
            (
                "compiled_to_validated",
                "compiled_programs",
                self._int(compiled_programs),
                "validated_programs",
                self._int(validated_programs),
                "validation_infrastructure",
            ),
        ]
        rows = []
        for stage, input_name, input_count, output_name, output_count, cause in stages:
            conversion = self._ratio(output_count, input_count)
            lost_count = max(input_count - output_count, 0)
            loss_rate = round(1.0 - conversion, 4) if input_count else 0.0
            rows.append(
                {
                    "stage": stage,
                    "input_stage": input_name,
                    "input_count": input_count,
                    "output_stage": output_name,
                    "output_count": output_count,
                    "lost_count": lost_count,
                    "conversion_rate": conversion,
                    "loss_rate": loss_rate,
                    "likely_cause": cause,
                    "action": self._operationalization_action(cause),
                }
            )
        primary = sorted(
            rows,
            key=lambda row: (
                -int(row.get("lost_count") or 0),
                -float(row.get("loss_rate") or 0.0),
                str(row.get("stage")),
            ),
        )[0]
        loss_pressure = self._bounded_ratio(
            sum(int(row.get("lost_count") or 0) for row in rows),
            max(self._int(candidate_count), 1),
        )
        return {
            "knowledge_operationalization_path": rows,
            "knowledge_operationalization_choke_point": primary["stage"],
            "knowledge_operationalization_choke_cause": primary["likely_cause"],
            "knowledge_operationalization_choke_action": primary["action"],
            "knowledge_operationalization_loss_count": sum(
                int(row.get("lost_count") or 0) for row in rows
            ),
            "knowledge_operationalization_loss_pressure": loss_pressure,
            "knowledge_operationalization_state": self._state(
                loss_pressure,
                high="SEVERE_KNOWLEDGE_OPERATIONALIZATION_CHOKE",
                medium="KNOWLEDGE_OPERATIONALIZATION_PRESSURE",
                low="KNOWLEDGE_OPERATIONALIZATION_CONTROLLED",
            ),
            "operational_grounding_failure_count": self._int(
                operational_grounding_failure_count
            ),
            "operational_grounding_failure_rate": operational_grounding_failure_rate,
        }

    def _operationalization_action(self, cause: str) -> str:
        if cause == "operational_grounding":
            return "select_grounding_aligned_validation_tasks"
        if cause == "validation_infrastructure":
            return "expand_validation_evidence_capture"
        if cause == "candidate_admission":
            return "improve_candidate_arena_admission"
        return "inspect_compiler_execution_contracts"

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
                    "required_grounding": self._cluster_required_grounding(row),
                    "cluster_state": (
                        "OPERATIONAL_CLUSTER_READY"
                        if readiness >= 1.0
                        else "PARTIAL_OPERATIONAL_CLUSTER"
                    ),
                }
            )
        clusters.sort(key=lambda item: (-item["cluster_readiness"], item["cluster_name"]))
        return clusters

    def _cluster_required_grounding(
        self,
        row: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        capabilities = row.get("required_capabilities") or []
        domains = row.get("participating_domains") or []
        cluster_name = str(row.get("composite_name") or "unknown_cluster")
        grounding_rows = []
        capability_list = capabilities if isinstance(capabilities, list) else []
        for capability in capability_list:
            operation = str(capability)
            grounding_rows.append(
                {
                    "cluster_name": cluster_name,
                    "operation": operation,
                    "domain": self._domain_for_operation(operation, domains),
                    "required_evidence": "exact_or_governed_validation_success",
                    "required_task_property": self._required_grounding_task_property(
                        operation
                    ),
                    "grounding_stage": "cluster_operationalization_grounding",
                    "action": "select_grounding_aligned_task",
                }
            )
        return grounding_rows

    def _domain_for_operation(self, operation: str, domains: Any) -> str:
        normalized = str(operation or "")
        if "topology" in normalized:
            return "Topology"
        if normalized in {"translate", "move_object", "preserve_grid"}:
            return "Spatial"
        if normalized in {"preserve_shape", "preserve_size", "duplicate_object"}:
            return "Identity"
        if "color" in normalized:
            return "Color"
        if isinstance(domains, list) and domains:
            return str(domains[0])
        return "Transformation"

    def _required_grounding_task_property(self, operation: str) -> str:
        operation = str(operation or "")
        if operation in {"translate", "move_object"}:
            return "unambiguous_directional_translation_ground_truth"
        if operation in {"preserve_topology", "topological_reasoning"}:
            return "topology_preserving_transformation_ground_truth"
        if operation in {"preserve_grid", "preserve_shape", "preserve_size"}:
            return "paired_identity_preservation_ground_truth"
        if operation in {"duplicate_object", "replicate_object"}:
            return "paired_symbolic_object_replication_ground_truth"
        if operation in {"replace_color", "preserve_colors"}:
            return "color_invariance_under_transformation"
        return "paired_source_target_grid_ground_truth"

    def _cluster_operationalization(
        self,
        *,
        operational_clusters: list[Mapping[str, Any]],
        materialized_operational_capabilities: int,
        operational_citizen_count: int,
    ) -> dict[str, Any]:
        ready_clusters = [
            row
            for row in operational_clusters
            if float(row.get("cluster_readiness") or 0.0) >= 1.0
        ]
        ready_count = len(ready_clusters)
        cluster_count = len(operational_clusters)
        materialized_count = self._int(materialized_operational_capabilities)
        citizen_count = self._int(operational_citizen_count)
        if ready_count == 0:
            state = "NO_READY_OPERATIONAL_CLUSTERS"
            action = "CONTINUE_COMPOSITE_EVIDENCE_ACCUMULATION"
        elif materialized_count == 0 and citizen_count == 0:
            state = "READY_CLUSTERS_BLOCKED_BY_OPERATIONALIZATION"
            action = "CLUSTER_OPERATIONALIZATION_REQUIRED"
        elif materialized_count == 0:
            state = "READY_CLUSTERS_AWAITING_MATERIALIZATION"
            action = "TARGET_CLUSTER_VALIDATION_AND_GROUNDING"
        else:
            state = "CLUSTER_OPERATIONALIZATION_ACTIVE"
            action = "MONITOR_CLUSTER_TO_CITIZEN_CONVERSION"
        return {
            "ready_operational_cluster_count": ready_count,
            "cluster_operationalization_candidate_count": ready_count,
            "cluster_to_materialization_gap": max(ready_count - materialized_count, 0),
            "cluster_to_citizen_gap": max(ready_count - citizen_count, 0),
            "cluster_operationalization_state": state,
            "cluster_operationalization_action": action,
            "cluster_operationalization_pressure": self._bounded_ratio(
                max(ready_count - materialized_count, 0),
                max(cluster_count, 1),
            ),
        }

    def _roadmap(
        self,
        *,
        attrition_rows: list[Mapping[str, Any]],
        conversion_rates: Mapping[str, float],
        population_growth_pressure: float,
        crystallization_efficiency: float,
        operational_investment_return: float,
        cluster_operationalization_state: str,
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
        if cluster_operationalization_state in {
            "READY_CLUSTERS_BLOCKED_BY_OPERATIONALIZATION",
            "READY_CLUSTERS_AWAITING_MATERIALIZATION",
        }:
            recommendations.append(
                {
                    "priority": "cluster_operationalization",
                    "target": "ready_operational_capability_clusters",
                    "action": "convert_ready_clusters_into_grounded_validation_targets",
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
