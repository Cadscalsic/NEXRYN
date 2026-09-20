"""Capability ecology diagnostics for composite intelligence.

The analyzer only measures relationships among existing capabilities. It does
not create capabilities, change lifecycle policy, or alter runtime authority.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
from typing import Any, Mapping


COMPOSITE_CAPABILITY_SPECS = (
    {
        "composite_name": "Topology Preserving Translation",
        "required_capabilities": ("translate", "preserve_topology", "preserve_colors"),
        "participating_domains": ("Spatial", "Topology", "Color"),
        "synergy_type": "High Validation Synergy",
    },
    {
        "composite_name": "Symbolic Object Replication",
        "required_capabilities": ("duplicate_object", "replace_color", "preserve_grid"),
        "participating_domains": ("Identity", "Color", "Geometry"),
        "synergy_type": "High Operational Synergy",
    },
    {
        "composite_name": "Structural Bridge Intelligence",
        "required_capabilities": (
            "bridge_creation",
            "topological_reasoning",
            "spatial_reasoning",
        ),
        "participating_domains": ("Topology", "Spatial", "Identity"),
        "synergy_type": "High Domain Expansion Synergy",
    },
    {
        "composite_name": "Pattern Completion Intelligence",
        "required_capabilities": (
            "pattern_completion",
            "translate",
            "preserve_topology",
            "replace_color",
        ),
        "participating_domains": ("Transformation", "Spatial", "Topology", "Color"),
        "synergy_type": "Composite Reasoning Synergy",
    },
    {
        "composite_name": "Identity Preserving Transformation",
        "required_capabilities": (
            "preserve_grid",
            "preserve_shape",
            "translate",
            "preserve_topology",
        ),
        "participating_domains": ("Identity", "Geometry", "Spatial", "Topology"),
        "synergy_type": "High Graduation Synergy",
    },
    {
        "composite_name": "Spatial Growth Intelligence",
        "required_capabilities": (
            "growth_detection",
            "duplicate_object",
            "translate",
            "preserve_colors",
        ),
        "participating_domains": ("Growth", "Identity", "Spatial", "Color"),
        "synergy_type": "Operational Population Synergy",
    },
)


CAPABILITY_ALIASES = {
    "bridge_creation": {"bridge_creation", "bridge_creation_capability", "construct_path"},
    "duplicate_object": {"duplicate_object", "replicate_object", "object_replication"},
    "growth_detection": {"growth", "growth_detection", "object_falling_simulation"},
    "pattern_completion": {"pattern_completion", "complete_pattern"},
    "preserve_colors": {"preserve_colors", "preserve_color", "color_preservation"},
    "preserve_grid": {"preserve_grid", "grid_preservation"},
    "preserve_shape": {"preserve_shape", "shape_preservation"},
    "preserve_topology": {"preserve_topology", "topology_preservation"},
    "replace_color": {"replace_color", "color_mapping"},
    "spatial_reasoning": {"spatial_reasoning", "spatial_position", "translate"},
    "topological_reasoning": {"topological_reasoning", "topology", "preserve_topology"},
    "translate": {"translate", "translation"},
}


DOMAIN_BY_CAPABILITY = {
    "bridge_creation": "Topology",
    "construct_path": "Topology",
    "duplicate_object": "Identity",
    "growth": "Growth",
    "growth_detection": "Growth",
    "pattern_completion": "Transformation",
    "preserve_colors": "Color",
    "preserve_grid": "Identity",
    "preserve_shape": "Geometry",
    "preserve_topology": "Topology",
    "replace_color": "Color",
    "spatial_reasoning": "Spatial",
    "topological_reasoning": "Topology",
    "translate": "Spatial",
}


class CapabilityEcologyAnalysis:
    """Measure cooperation, specialization, and composite readiness."""

    def analyze(
        self,
        *,
        known_operations: list[Any] | None = None,
        experience_distribution: list[Mapping[str, Any]] | None = None,
        survival_rows: list[Mapping[str, Any]] | None = None,
        graduation_diagnostics: list[Mapping[str, Any]] | None = None,
        domain_collaboration_rows: list[Mapping[str, Any]] | None = None,
        operational_programs: list[Mapping[str, Any]] | None = None,
        compiler_infrastructure_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        rows = self._capability_rows(
            known_operations=known_operations or [],
            experience_distribution=experience_distribution or [],
            survival_rows=survival_rows or [],
            graduation_diagnostics=graduation_diagnostics or [],
            operational_programs=operational_programs or [],
            compiler_infrastructure_report=(
                compiler_infrastructure_report or {}
            ),
        )
        present = set(rows)
        composite_candidates = self._composite_candidates(present)
        cooperation_graph = self._cooperation_graph(
            rows,
            composite_candidates=composite_candidates,
            domain_collaboration_rows=domain_collaboration_rows or [],
        )
        capability_reports = self._capability_reports(rows, cooperation_graph)
        synergy_matrix = self._synergy_matrix(cooperation_graph, rows)
        economy = self._economy(capability_reports)

        possible_edges = len(present) * (len(present) - 1) / 2
        interaction_density = self._ratio(len(cooperation_graph), possible_edges)
        cooperation_score = self._average(
            row["capability_cooperation_score"] for row in capability_reports
        )
        composition_score = self._average(
            row["composition_readiness"] for row in composite_candidates
        )
        collaboration_diversity = self._ratio(
            len({
                tuple(sorted(edge["participating_domains"]))
                for edge in cooperation_graph
                if edge["participating_domains"]
            }),
            max(len(cooperation_graph), 1),
        )
        composite_count = len([
            row for row in composite_candidates
            if row["composition_state"] == "COMPOSITE_OPERATIONAL_CANDIDATE"
        ])
        ecology_health = self._average(
            [
                cooperation_score,
                composition_score,
                collaboration_diversity,
                interaction_density,
                economy["capability_economy_health"],
            ]
        )

        return {
            "system": "capability_ecology_analysis",
            "capability_ecology_health": ecology_health,
            "capability_cooperation_score": cooperation_score,
            "capability_composition_score": composition_score,
            "composite_capability_score": self._ratio(
                composite_count,
                len(composite_candidates),
            ),
            "capability_collaboration_diversity": collaboration_diversity,
            "composite_operational_capability_count": composite_count,
            "capability_interaction_density": interaction_density,
            "capability_composition_readiness": (
                "READY_FOR_COMPOSITE_INTELLIGENCE"
                if ecology_health >= 0.70 and composite_count
                else "COMPOSITION_OPPORTUNITIES_DETECTED"
                if composite_candidates
                else "NOT_MEASURABLE"
            ),
            "composite_intelligence_readiness": (
                "READY"
                if ecology_health >= 0.70 and composite_count
                else "DEVELOPING"
                if present
                else "NOT_MEASURABLE"
            ),
            "capability_ecology_state": (
                "CAPABILITY_ECOLOGY_ACTIVE"
                if len(present) >= 3 and cooperation_graph
                else "SINGLE_CAPABILITY_DOMINANT"
                if present
                else "NO_CAPABILITY_POPULATION"
            ),
            "capability_reports": capability_reports,
            "capability_specialization_report": capability_reports,
            "composite_capability_candidates": composite_candidates,
            "capability_composition_opportunities": [
                row for row in composite_candidates
                if row["composition_state"] != "COMPOSITE_OPERATIONAL_CANDIDATE"
            ],
            "capability_synergy_matrix": synergy_matrix,
            "capability_cooperation_graph": cooperation_graph,
            "capability_economy_health": economy["capability_economy_health"],
            "capability_economy_rows": economy["capability_economy_rows"],
            "high_value_capabilities": economy["high_value_capabilities"],
            "capability_investment_priorities": economy[
                "capability_investment_priorities"
            ],
            "capability_investment_intelligence_phase": economy[
                "capability_investment_intelligence_phase"
            ],
            "capability_investment_authority_scope": economy[
                "capability_investment_authority_scope"
            ],
            "capability_investment_forbidden_authority": economy[
                "capability_investment_forbidden_authority"
            ],
            "capability_investment_truth_boundary": economy[
                "capability_investment_truth_boundary"
            ],
            "capability_investment_governance_principle": economy[
                "capability_investment_governance_principle"
            ],
            "capability_promotion_roadmap": economy[
                "capability_promotion_roadmap"
            ],
        }

    def _capability_rows(
        self,
        *,
        known_operations: list[Any],
        experience_distribution: list[Mapping[str, Any]],
        survival_rows: list[Mapping[str, Any]],
        graduation_diagnostics: list[Mapping[str, Any]],
        operational_programs: list[Mapping[str, Any]],
        compiler_infrastructure_report: Mapping[str, Any],
    ) -> dict[str, dict[str, Any]]:
        rows: dict[str, dict[str, Any]] = {}

        for operation in known_operations:
            op = self._operation(operation)
            if op:
                self._ensure(rows, op, source="known_operational")

        for item in experience_distribution:
            if not isinstance(item, Mapping):
                continue
            op = self._operation(item.get("operation"))
            if not op:
                continue
            row = self._ensure(rows, op, source="experience")
            row["experience_count"] += self._int(item.get("experience_count"))
            row["reuse_success_count"] += self._int(
                item.get("independent_reuse_success_count")
            )

        for item in survival_rows:
            if not isinstance(item, Mapping):
                continue
            op = self._operation(item.get("operation"))
            if not op:
                continue
            row = self._ensure(rows, op, source="survival")
            state = item.get("lifecycle_state")
            if state:
                row["lifecycle_state"] = str(state)
            row["arena_quality_count"] += self._int(item.get("arena_quality_count"))
            row["distinct_task_count"] += self._int(item.get("distinct_task_count"))
            row["best_accuracy"] = max(
                row["best_accuracy"],
                self._float(item.get("best_accuracy")),
            )
            row["average_accuracy"] = max(
                row["average_accuracy"],
                self._float(item.get("average_accuracy")),
            )

        for item in graduation_diagnostics:
            if not isinstance(item, Mapping):
                continue
            op = self._operation(item.get("operation"))
            if not op:
                continue
            row = self._ensure(rows, op, source="graduation")
            row["graduation_signal_count"] += 1
            status = item.get("graduation_status")
            if status:
                row["graduation_status"] = str(status)

        for program in operational_programs:
            if not isinstance(program, Mapping):
                continue
            op = self._operation(program.get("operation") or program.get("name"))
            if op:
                self._ensure(rows, op, source="operational_program")
            steps = program.get("steps") or []
            if isinstance(steps, list):
                for step in steps:
                    if not isinstance(step, Mapping):
                        continue
                    step_op = self._operation(
                        step.get("operation") or step.get("primitive")
                    )
                    if step_op:
                        self._ensure(rows, step_op, source="program_step")

        self._add_compiler_infrastructure_capabilities(
            rows,
            compiler_infrastructure_report,
        )

        return rows

    def _add_compiler_infrastructure_capabilities(
        self,
        rows: dict[str, dict[str, Any]],
        compiler_infrastructure_report: Mapping[str, Any],
    ) -> None:
        if not isinstance(compiler_infrastructure_report, Mapping):
            return
        primitives = compiler_infrastructure_report.get(
            "primitive_operation_inventory",
        ) or []
        primitives = primitives if isinstance(primitives, list) else []
        executable_operations = {
            self._operation(row.get("operation"))
            for row in primitives
            if isinstance(row, Mapping) and row.get("executable")
        }
        for operation in executable_operations:
            if operation:
                self._ensure(rows, operation, source="compiler_infrastructure")
        package_rows = compiler_infrastructure_report.get(
            "execution_package_inventory",
        ) or []
        package_rows = package_rows if isinstance(package_rows, list) else []
        for package in package_rows:
            if not isinstance(package, Mapping):
                continue
            if package.get("package") != "growth_execution_package":
                continue
            if package.get("package_present"):
                self._ensure(
                    rows,
                    "growth_detection",
                    source="compiler_infrastructure",
                )

    def _ensure(
        self,
        rows: dict[str, dict[str, Any]],
        operation: str,
        *,
        source: str,
    ) -> dict[str, Any]:
        row = rows.setdefault(
            operation,
            {
                "operation": operation,
                "domain": self._domain(operation),
                "sources": set(),
                "experience_count": 0,
                "reuse_success_count": 0,
                "arena_quality_count": 0,
                "distinct_task_count": 0,
                "graduation_signal_count": 0,
                "best_accuracy": 0.0,
                "average_accuracy": 0.0,
                "lifecycle_state": "KNOWN_CAPABILITY",
                "graduation_status": "NOT_IN_GRADUATION_QUEUE",
            },
        )
        row["sources"].add(source)
        return row

    def _composite_candidates(self, present: set[str]) -> list[dict[str, Any]]:
        candidates = []
        for spec in COMPOSITE_CAPABILITY_SPECS:
            required = [self._operation(item) for item in spec["required_capabilities"]]
            present_required = [
                capability for capability in required
                if self._has_capability(capability, present)
            ]
            missing = [
                capability for capability in required
                if capability not in present_required
            ]
            readiness = self._ratio(len(present_required), len(required))
            candidates.append(
                {
                    "composite_name": spec["composite_name"],
                    "required_capabilities": required,
                    "present_capabilities": present_required,
                    "missing_capabilities": missing,
                    "participating_domains": list(spec["participating_domains"]),
                    "composition_readiness": readiness,
                    "synergy_type": spec["synergy_type"],
                    "composition_state": (
                        "COMPOSITE_OPERATIONAL_CANDIDATE"
                        if readiness >= 1.0
                        else "PARTIAL_COMPOSITE_OPPORTUNITY"
                        if readiness >= 0.5
                        else "COMPOSITE_EVIDENCE_GAP"
                    ),
                }
            )
        candidates.sort(
            key=lambda item: (
                -item["composition_readiness"],
                item["composite_name"],
            )
        )
        return candidates

    def _cooperation_graph(
        self,
        rows: dict[str, dict[str, Any]],
        *,
        composite_candidates: list[Mapping[str, Any]],
        domain_collaboration_rows: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        edges: dict[tuple[str, str], dict[str, Any]] = {}
        for candidate in composite_candidates:
            present = candidate.get("present_capabilities") or []
            for left, right in combinations(sorted(set(present)), 2):
                edge = edges.setdefault(
                    (left, right),
                    self._edge(left, right, rows),
                )
                edge["evidence_sources"].add("composite_spec")
                edge["composite_contexts"].add(candidate.get("composite_name"))
                edge["synergy_score"] = max(
                    edge["synergy_score"],
                    float(candidate.get("composition_readiness") or 0.0),
                )

        for domain_row in domain_collaboration_rows:
            if not isinstance(domain_row, Mapping):
                continue
            required = [
                self._operation(item)
                for item in domain_row.get("required_capabilities") or []
            ]
            present = [
                capability for capability in required
                if self._has_capability(capability, set(rows))
            ]
            for left, right in combinations(sorted(set(present)), 2):
                edge = edges.setdefault(
                    (left, right),
                    self._edge(left, right, rows),
                )
                edge["evidence_sources"].add("domain_collaboration")
                edge["composite_contexts"].add(domain_row.get("composition_name"))
                edge["synergy_score"] = max(
                    edge["synergy_score"],
                    float(domain_row.get("domain_collaboration_readiness") or 0.0),
                )

        graph = []
        for edge in edges.values():
            edge["evidence_sources"] = sorted(edge["evidence_sources"])
            edge["composite_contexts"] = sorted(
                context for context in edge["composite_contexts"] if context
            )
            graph.append(edge)
        graph.sort(key=lambda item: (-item["synergy_score"], item["capability_pair"]))
        return graph

    def _edge(
        self,
        left: str,
        right: str,
        rows: Mapping[str, Mapping[str, Any]],
    ) -> dict[str, Any]:
        domains = sorted({
            rows.get(left, {}).get("domain") or self._domain(left),
            rows.get(right, {}).get("domain") or self._domain(right),
        })
        return {
            "capability_pair": [left, right],
            "participating_domains": domains,
            "evidence_sources": set(),
            "composite_contexts": set(),
            "synergy_score": 0.0,
            "cooperation_state": "COOPERATION_OBSERVED",
        }

    def _capability_reports(
        self,
        rows: Mapping[str, Mapping[str, Any]],
        cooperation_graph: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        collaborators: dict[str, set[str]] = defaultdict(set)
        dependencies: dict[str, set[str]] = defaultdict(set)
        synergy: dict[str, float] = defaultdict(float)
        for edge in cooperation_graph:
            pair = edge.get("capability_pair") or []
            if len(pair) != 2:
                continue
            left, right = pair
            collaborators[left].add(right)
            collaborators[right].add(left)
            dependencies[left].add(right)
            dependencies[right].add(left)
            score = float(edge.get("synergy_score") or 0.0)
            synergy[left] += score
            synergy[right] += score

        reports = []
        max_experience = max(
            [int(row.get("experience_count") or 0) for row in rows.values()] or [1]
        )
        max_collaborators = max(
            [len(collaborators[operation]) for operation in rows] or [1]
        )
        for operation, row in rows.items():
            collaboration_value = self._ratio(
                len(collaborators[operation]),
                max(max_collaborators, 1),
            )
            contribution = self._average(
                [
                    self._ratio(row.get("experience_count"), max(max_experience, 1)),
                    self._ratio(row.get("reuse_success_count"), max(row.get("experience_count"), 1)),
                    collaboration_value,
                    float(row.get("average_accuracy") or 0.0),
                ]
            )
            reports.append(
                {
                    "operation": operation,
                    "domain": row.get("domain"),
                    "lifecycle_state": row.get("lifecycle_state"),
                    "collaborates_with": sorted(collaborators[operation]),
                    "depends_on": sorted(dependencies[operation]),
                    "capability_cooperation_score": collaboration_value,
                    "capability_composition_score": round(
                        synergy[operation] / max(len(collaborators[operation]), 1),
                        4,
                    ),
                    "capability_contribution_score": contribution,
                    "operational_value_score": contribution,
                    "capability_reuse_value": self._ratio(
                        row.get("reuse_success_count"),
                        max(row.get("experience_count"), 1),
                    ),
                    "capability_graduation_value": (
                        1.0 if row.get("graduation_signal_count") else 0.0
                    ),
                    "capability_collaboration_value": collaboration_value,
                    "capability_investment_score": self._average(
                        [
                            contribution,
                            collaboration_value,
                            1.0 if row.get("graduation_signal_count") else 0.0,
                        ]
                    ),
                    "specialization": self._specialization(
                        operation,
                        row.get("domain"),
                        len(collaborators[operation]),
                    ),
                    "capability_value_state": (
                        "HIGH_VALUE_CAPABILITY"
                        if contribution >= 0.70 or collaboration_value >= 0.75
                        else "UNDER_COLLABORATING_CAPABILITY"
                        if collaboration_value <= 0.20
                        else "DEVELOPING_CAPABILITY"
                    ),
                    "experience_count": row.get("experience_count"),
                    "reuse_success_count": row.get("reuse_success_count"),
                    "sources": sorted(row.get("sources") or []),
                }
            )
        reports.sort(
            key=lambda item: (
                -item["capability_investment_score"],
                item["operation"],
            )
        )
        return reports

    def _synergy_matrix(
        self,
        cooperation_graph: list[Mapping[str, Any]],
        rows: Mapping[str, Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        matrix = []
        for edge in cooperation_graph:
            pair = edge.get("capability_pair") or []
            if len(pair) != 2:
                continue
            score = float(edge.get("synergy_score") or 0.0)
            matrix.append(
                {
                    "capability_pair": pair,
                    "synergy_score": round(score, 4),
                    "synergy_state": (
                        "HIGH_SYNERGY"
                        if score >= 0.75
                        else "MODERATE_SYNERGY"
                        if score >= 0.50
                        else "LOW_SYNERGY"
                    ),
                    "domain_pair": [
                        rows.get(pair[0], {}).get("domain") or self._domain(pair[0]),
                        rows.get(pair[1], {}).get("domain") or self._domain(pair[1]),
                    ],
                    "contexts": edge.get("composite_contexts") or [],
                }
            )
        matrix.sort(key=lambda item: (-item["synergy_score"], item["capability_pair"]))
        return matrix

    def _economy(self, reports: list[Mapping[str, Any]]) -> dict[str, Any]:
        economy_rows = [
            {
                "operation": row.get("operation"),
                "domain": row.get("domain"),
                "capability_contribution_score": row.get(
                    "capability_contribution_score"
                ),
                "operational_value_score": row.get("operational_value_score"),
                "capability_reuse_value": row.get("capability_reuse_value"),
                "capability_graduation_value": row.get("capability_graduation_value"),
                "capability_collaboration_value": row.get(
                    "capability_collaboration_value"
                ),
                "capability_investment_score": row.get("capability_investment_score"),
                "capability_value_state": row.get("capability_value_state"),
            }
            for row in reports
        ]
        high_value = [
            row for row in economy_rows
            if row.get("capability_value_state") == "HIGH_VALUE_CAPABILITY"
        ]
        health = self._average(
            row.get("capability_investment_score") for row in economy_rows
        )
        return {
            "capability_economy_health": health,
            "capability_economy_rows": economy_rows,
            "high_value_capabilities": high_value,
            "capability_investment_priorities": economy_rows[:5],
            "capability_investment_intelligence_phase": "ROADMAP_ONLY",
            "capability_investment_authority_scope": [
                "validation_prioritization",
                "compute_allocation",
                "curriculum_selection",
                "investment_decisions",
            ],
            "capability_investment_forbidden_authority": [
                "validation_outcomes",
                "trust_scores",
                "graduation_authority",
                "governed_validation_contracts",
                "truth_governance",
            ],
            "capability_investment_truth_boundary": (
                "INVESTMENT_NEVER_INFLUENCES_TRUTH_FORMATION"
            ),
            "capability_investment_governance_principle": (
                "investment_allocates_validation_opportunities_only"
            ),
            "capability_promotion_roadmap": [
                "capability_discovery",
                "capability_validation",
                "capability_promotion",
                "trust_formation",
                "graduation_intelligence",
                "operational_capability_population",
                "capability_economy",
            ],
        }

    def _specialization(self, operation: str, domain: Any, collaborator_count: int) -> str:
        if collaborator_count >= 3:
            return "Composite Capability"
        if domain in {"Topology", "Identity", "Growth", "Geometry"}:
            return f"{domain} Specialized Capability"
        if domain in {"Color", "Spatial", "Transformation"}:
            return "General Purpose Capability"
        return "Domain Specific Capability"

    def _has_capability(self, capability: str, present: set[str]) -> bool:
        aliases = CAPABILITY_ALIASES.get(capability, {capability})
        return bool(aliases.intersection(present))

    def _operation(self, value: Any) -> str:
        if value is None:
            return ""
        text = str(value).strip().lower().replace(" ", "_").replace("-", "_")
        for canonical, aliases in CAPABILITY_ALIASES.items():
            if text in aliases:
                return canonical
        return text

    def _domain(self, operation: str) -> str:
        return DOMAIN_BY_CAPABILITY.get(operation, "General")

    def _int(self, value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    def _float(self, value: Any) -> float:
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _ratio(self, numerator: Any, denominator: Any) -> float:
        try:
            den = float(denominator)
            if den == 0:
                return 0.0
            return round(float(numerator or 0.0) / den, 4)
        except (TypeError, ValueError):
            return 0.0

    def _average(self, values: Any) -> float:
        valid = [
            float(value)
            for value in values
            if isinstance(value, (int, float))
        ]
        return round(sum(valid) / len(valid), 4) if valid else 0.0


capability_ecology_analysis = CapabilityEcologyAnalysis()


__all__ = [
    "CapabilityEcologyAnalysis",
    "capability_ecology_analysis",
]
