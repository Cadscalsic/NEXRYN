"""Operational domain diagnostics for the operationalization phase.

This module measures how existing cognitive domains move toward operational
citizenship. It does not add domains, layers, capability types, or governance
rules.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Any, Mapping


DOMAIN_COLLABORATION_SPECS = (
    {
        "composition_name": "Object Falling Simulation",
        "participating_domains": ("Growth", "Topology", "Spatial", "Transformation"),
        "required_capabilities": (
            "growth",
            "topology",
            "spatial_position",
            "transformation",
        ),
    },
    {
        "composition_name": "Bridge Creation Capability",
        "participating_domains": ("Topology", "Spatial", "Identity"),
        "required_capabilities": (
            "topology",
            "spatial_position",
            "identity_preservation",
        ),
    },
    {
        "composition_name": "Pattern Completion Capability",
        "participating_domains": ("Transformation", "Color", "Spatial", "Pattern"),
        "required_capabilities": (
            "transformation",
            "color_mapping",
            "spatial_position",
            "pattern_completion",
        ),
    },
    {
        "composition_name": "Color Transformation Capability",
        "participating_domains": ("Transformation", "Color"),
        "required_capabilities": ("transformation", "color_mapping"),
    },
    {
        "composition_name": "Object Identity Tracking",
        "participating_domains": ("Spatial", "Identity"),
        "required_capabilities": ("spatial_position", "identity_preservation"),
    },
)


class OperationalDomainInfrastructure:
    """Analyze operational domain population, gaps, and collaboration."""

    def analyze(
        self,
        *,
        domain_architecture: Mapping[str, Any] | None = None,
        operational_distribution: Mapping[str, Any] | None = None,
        survival_rows: list[Mapping[str, Any]] | None = None,
        graduation_diagnostics: list[Mapping[str, Any]] | None = None,
        target_domain_count: int | None = None,
    ) -> dict[str, Any]:
        architecture = domain_architecture if isinstance(domain_architecture, Mapping) else {}
        rows = architecture.get("domain_rows") or []
        rows = [dict(row) for row in rows if isinstance(row, Mapping)]
        distribution = (
            operational_distribution
            if isinstance(operational_distribution, Mapping)
            else {}
        )
        target = max(int(target_domain_count or architecture.get("domain_count") or len(rows) or 1), 1)
        survival = [dict(row) for row in survival_rows or [] if isinstance(row, Mapping)]
        graduation = [
            dict(row) for row in graduation_diagnostics or [] if isinstance(row, Mapping)
        ]
        survival_counts = self._survival_counts(survival)
        graduation_counts = self._graduation_counts(graduation)
        diagnostics = [
            self._domain_diagnostic(
                row,
                distribution=distribution,
                survival_counts=survival_counts,
                graduation_counts=graduation_counts,
            )
            for row in rows
        ]
        active = [
            row for row in diagnostics
            if row["semantic_concept_count"]
            or row["execution_package_count"]
            or row["program_blueprint_count"]
            or row["candidate_count"]
            or row["operational_citizen_count"]
        ]
        operational = [
            row for row in active
            if row["operational_citizen_count"] > 0
        ]
        distribution_values = [
            int(value or 0)
            for value in distribution.values()
            if isinstance(value, (int, float))
        ]
        total_population = sum(distribution_values)
        monopoly_share = (
            round(max(distribution_values, default=0) / total_population, 4)
            if total_population
            else 0.0
        )
        collaboration = self._collaboration(active)
        score = self._average(row["domain_operationalization_score"] for row in active)
        primitive = self._average(row["domain_primitive_coverage"] for row in active)
        diversity = (
            round(1.0 - monopoly_share, 4)
            if total_population
            else 0.0
        )
        coverage = self._ratio(len(operational), target)
        growth_rate = self._ratio(
            len([row for row in active if row["domain_expansion_priority"] != "LOW"]),
            max(len(active), 1),
        )
        bottlenecks = Counter(
            row["domain_operationalization_bottleneck"]
            for row in active
            if row["domain_operationalization_bottleneck"] != "none"
        )
        bottleneck = (
            sorted(bottlenecks.items(), key=lambda item: (-item[1], item[0]))[0][0]
            if bottlenecks
            else "none"
        )
        health = self._average([
            score or 0.0,
            coverage,
            diversity,
            collaboration["domain_collaboration_score"],
            primitive or 0.0,
        ])
        return {
            "system": "operational_domain_infrastructure",
            "operational_domain_health": health,
            "operational_domain_coverage": coverage,
            "domain_operationalization_score": score,
            "domain_operationalization_bottleneck": bottleneck,
            "domain_population_balance": (
                "BALANCED"
                if monopoly_share <= 0.35 and len(operational) >= min(target, 5)
                else "IMBALANCED"
                if operational
                else "NO_OPERATIONAL_DOMAINS"
            ),
            "domain_collaboration_score": collaboration["domain_collaboration_score"],
            "domain_operational_growth_rate": growth_rate,
            "domain_primitive_coverage": primitive,
            "domain_capability_diversity": diversity,
            "domain_infrastructure_readiness": (
                "READY_FOR_EXPANSION"
                if health is not None and health >= 0.75 and len(operational) >= 5
                else "EXPANSION_REQUIRED"
                if active
                else "NOT_MEASURABLE"
            ),
            "operational_domain_population": len(operational),
            "domain_diversification_score": diversity,
            "domain_monopoly_pressure": (
                "HIGH"
                if monopoly_share >= 0.50
                else "MEDIUM"
                if monopoly_share >= 0.35
                else "LOW"
            ),
            "operational_domain_growth_rate": growth_rate,
            "operational_domain_evolution_speed": self._ratio(len(operational), max(len(active), 1)),
            "domain_diagnostics": active,
            "domain_operationalization_gaps": [
                row for row in active
                if row["domain_operationalization_bottleneck"] != "none"
            ],
            "domain_collaboration_rows": collaboration["domain_collaboration_rows"],
            "domain_collaboration_graph": collaboration["domain_collaboration_graph"],
            "isolated_operational_domains": collaboration["isolated_operational_domains"],
            "productive_operational_domains": collaboration["productive_operational_domains"],
            "domain_operational_targets": [
                self._target(row) for row in active
            ],
            "domain_expansion_roadmap": [
                self._roadmap(row) for row in sorted(
                    active,
                    key=lambda item: (
                        item["domain_expansion_rank"],
                        item["domain_name"],
                    ),
                )
            ][:7],
        }

    def _domain_diagnostic(
        self,
        row: Mapping[str, Any],
        *,
        distribution: Mapping[str, Any],
        survival_counts: Mapping[str, int],
        graduation_counts: Mapping[str, int],
    ) -> dict[str, Any]:
        domain = self._domain_label(row.get("domain_name"))
        semantic = self._int(row.get("semantic_concept_count"))
        packages = self._int(row.get("execution_package_count"))
        programs = self._int(row.get("program_blueprint_count"))
        candidates = self._int(row.get("candidate_count"))
        arena = self._int(row.get("arena_candidate_count"))
        validated = self._int(row.get("validated_program_count"))
        citizens = self._int(distribution.get(domain))
        surviving = self._int(survival_counts.get(domain))
        graduating = self._int(graduation_counts.get(domain))
        primitive_coverage = self._ratio(packages, max(semantic, 1))
        bottleneck = self._bottleneck(
            semantic=semantic,
            packages=packages,
            programs=programs,
            candidates=candidates,
            arena=arena,
            validated=validated,
            citizens=citizens,
            surviving=surviving,
            graduating=graduating,
            row=row,
        )
        score = self._average([
            self._ratio(packages, max(semantic, 1)),
            self._ratio(programs, max(packages, 1)),
            self._ratio(candidates, max(programs, 1)),
            self._ratio(arena, max(candidates, 1)),
            self._ratio(validated, max(arena, 1)),
            1.0 if citizens else 0.0,
        ])
        priority_rank = {
            "candidate_generation_gap": 1,
            "arena_entry_gap": 2,
            "validation_gap": 3,
            "graduation_gap": 4,
            "execution_package_gap": 5,
            "compiler_gap": 6,
            "primitive_coverage_gap": 7,
            "none": 9,
        }.get(bottleneck, 8)
        return {
            **dict(row),
            "domain_label": domain,
            "operational_citizen_count": citizens,
            "surviving_capability_count": surviving,
            "graduation_candidate_count": graduating,
            "validation_success_count": validated,
            "domain_primitive_coverage": primitive_coverage,
            "domain_operationalization_score": score,
            "domain_operationalization_bottleneck": bottleneck,
            "domain_operational_health": self._health(score, citizens, bottleneck),
            "domain_population_state": (
                "OPERATIONAL_POPULATION_PRESENT" if citizens else "MISSING_OPERATIONAL_POPULATION"
            ),
            "domain_expansion_priority": (
                "CRITICAL"
                if not citizens and priority_rank <= 3
                else "HIGH"
                if not citizens
                else "MEDIUM"
                if bottleneck != "none"
                else "LOW"
            ),
            "domain_expansion_rank": priority_rank,
            "domain_training_guidance": self._training_guidance(domain, bottleneck),
        }

    def _bottleneck(self, **kwargs: Any) -> str:
        row = kwargs.get("row") if isinstance(kwargs.get("row"), Mapping) else {}
        semantic = kwargs["semantic"]
        packages = kwargs["packages"]
        programs = kwargs["programs"]
        candidates = kwargs["candidates"]
        arena = kwargs["arena"]
        validated = kwargs["validated"]
        citizens = kwargs["citizens"]
        surviving = kwargs["surviving"]
        graduating = kwargs["graduating"]
        gap = str(row.get("operationalization_gap") or "")
        if semantic and packages < semantic:
            return "execution_package_gap"
        if packages and not programs:
            return "compiler_gap"
        if programs and not candidates:
            return "candidate_generation_gap"
        if candidates and not arena:
            return "arena_entry_gap"
        if arena and not validated:
            return "validation_gap"
        if (validated or surviving or graduating) and not citizens:
            return "graduation_gap"
        if semantic and packages < semantic:
            return "primitive_coverage_gap"
        if gap and gap != "none":
            return gap
        return "none"

    def _collaboration(self, rows: list[Mapping[str, Any]]) -> dict[str, Any]:
        by_domain = {self._domain_label(row.get("domain_name")): row for row in rows}
        graph: dict[str, list[str]] = {domain: [] for domain in by_domain}
        collaborations = []
        productive = Counter()
        for spec in DOMAIN_COLLABORATION_SPECS:
            domains = list(spec["participating_domains"])
            present = [domain for domain in domains if domain in by_domain]
            missing = [domain for domain in domains if domain not in by_domain]
            readiness = self._average(
                by_domain[domain].get("domain_operationalization_score", 0.0)
                for domain in present
            )
            status = (
                "READY"
                if not missing and readiness is not None and readiness >= 0.70
                else "PARTIAL"
                if present
                else "BLOCKED"
            )
            for left, right in combinations(present, 2):
                graph.setdefault(left, [])
                graph.setdefault(right, [])
                if right not in graph[left]:
                    graph[left].append(right)
                if left not in graph[right]:
                    graph[right].append(left)
                productive[left] += 1
                productive[right] += 1
            collaborations.append({
                "composition_name": spec["composition_name"],
                "participating_domains": domains,
                "present_domains": present,
                "missing_domains": missing,
                "required_capabilities": list(spec["required_capabilities"]),
                "domain_collaboration_readiness": readiness,
                "collaboration_status": status,
            })
        for domain in graph:
            graph[domain] = sorted(set(graph[domain]))
        score = self._average(
            row["domain_collaboration_readiness"]
            for row in collaborations
            if row["domain_collaboration_readiness"] is not None
        )
        return {
            "domain_collaboration_score": score,
            "domain_collaboration_rows": collaborations,
            "domain_collaboration_graph": graph,
            "isolated_operational_domains": sorted(
                domain for domain, peers in graph.items() if not peers
            ),
            "productive_operational_domains": [
                domain for domain, _ in productive.most_common()
            ],
        }

    def _target(self, row: Mapping[str, Any]) -> dict[str, Any]:
        bottleneck = row.get("domain_operationalization_bottleneck")
        target = {
            "candidate_generation_gap": "Candidate Generation",
            "arena_entry_gap": "Arena Participation",
            "validation_gap": "Validation Success",
            "graduation_gap": "Operational Citizen",
            "execution_package_gap": "Execution Package Coverage",
            "compiler_gap": "Compiler Support",
            "primitive_coverage_gap": "Primitive Coverage",
        }.get(str(bottleneck), "Maintain Operational Balance")
        return {
            "domain_name": row.get("domain_name"),
            "domain_label": row.get("domain_label"),
            "target": target,
            "bottleneck": bottleneck,
            "training_guidance": row.get("domain_training_guidance"),
        }

    def _roadmap(self, row: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "domain_name": row.get("domain_name"),
            "domain_label": row.get("domain_label"),
            "priority": row.get("domain_expansion_priority"),
            "bottleneck": row.get("domain_operationalization_bottleneck"),
            "target": self._target(row).get("target"),
            "score": row.get("domain_operationalization_score"),
            "operational_citizens": row.get("operational_citizen_count"),
        }

    def _survival_counts(self, rows: list[Mapping[str, Any]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in rows:
            state = str(row.get("lifecycle_state") or "")
            if state not in {"SURVIVING_CAPABILITY", "OPERATIONAL_CITIZEN"}:
                continue
            domain = self._domain_label(row.get("domain"))
            counts[domain] = counts.get(domain, 0) + 1
        return counts

    def _graduation_counts(self, rows: list[Mapping[str, Any]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in rows:
            domain = self._domain_label(row.get("domain"))
            counts[domain] = counts.get(domain, 0) + 1
        return counts

    def _training_guidance(self, domain: str, bottleneck: str) -> str:
        return {
            "candidate_generation_gap": f"domain_candidate_generation_task_for:{domain}",
            "arena_entry_gap": f"arena_participation_task_for:{domain}",
            "validation_gap": f"validator_acceptance_task_for:{domain}",
            "graduation_gap": f"graduation_sprint_task_for:{domain}",
            "execution_package_gap": f"execution_package_coverage_review_for:{domain}",
            "compiler_gap": f"compiler_support_task_for:{domain}",
            "primitive_coverage_gap": f"primitive_coverage_task_for:{domain}",
        }.get(bottleneck, f"domain_balance_monitor_for:{domain}")

    def _health(self, score: float | None, citizens: int, bottleneck: str) -> str:
        if citizens and bottleneck == "none":
            return "HEALTHY"
        if score is not None and score >= 0.70:
            return "EXPANSION_READY"
        if score is not None and score >= 0.45:
            return "PARTIAL"
        return "BLOCKED"

    def _domain_label(self, value: Any) -> str:
        text = str(value or "Unknown").strip()
        text = text.replace(" Cognitive Domain", "").replace(" Domain", "")
        return text or "Unknown"

    def _int(self, value: Any, default: int = 0) -> int:
        try:
            return int(value if value is not None else default)
        except (TypeError, ValueError):
            return default

    def _ratio(self, numerator: float, denominator: float) -> float:
        if not denominator:
            return 0.0
        return round(max(0.0, min(1.0, float(numerator) / float(denominator))), 4)

    def _average(self, values: Any) -> float | None:
        if isinstance(values, (int, float)):
            return round(float(values), 4)
        rows = [
            float(value)
            for value in values
            if isinstance(value, (int, float))
        ]
        if not rows:
            return None
        return round(sum(rows) / len(rows), 4)


operational_domain_infrastructure = OperationalDomainInfrastructure()


__all__ = [
    "OperationalDomainInfrastructure",
    "operational_domain_infrastructure",
]
