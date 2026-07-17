"""Canonical organization of semantic knowledge into cognitive domains."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


FOUNDATIONAL_DOMAINS = {
    "Physics": "Physics Domain",
    "Topology": "Topology Domain",
    "Spatial": "Spatial Domain",
    "Transformation": "Transformation Domain",
    "Geometry": "Geometry Domain",
    "Identity": "Identity Domain",
    "Pattern Completion": "Pattern Completion Domain",
    "Reasoning": "Reasoning Domain",
    "Context": "Context Domain",
    "Dependency": "Dependency Domain",
    "Growth": "Growth Domain",
    "Temporal": "Temporal Domain",
    "Symbolic": "Symbolic Domain",
    "Color": "Color Domain",
    "Cognitive Governance": "Cognitive Governance Domain",
}

DOMAIN_BY_FAMILY = {
    "Physics": "Physics",
    "Topology": "Topology",
    "Connectivity": "Topology",
    "Spatial": "Spatial",
    "Motion": "Spatial",
    "Transformation": "Transformation",
    "Geometry": "Geometry",
    "Symmetry": "Geometry",
    "Identity": "Identity",
    "Object Identity": "Identity",
    "Pattern Completion": "Pattern Completion",
    "Reasoning": "Reasoning",
    "Context": "Context",
    "Dependency": "Dependency",
    "Growth": "Growth",
    "Temporal": "Temporal",
    "Symbolic": "Symbolic",
    "Color": "Color",
}

DOMAIN_BY_CONCEPT_TOKEN = (
    ("Physics", ("gravity", "falling", "collision", "support", "rest_state", "downward_motion")),
    ("Topology", ("topology", "component", "connectivity", "bridge", "hole")),
    ("Spatial", ("spatial", "position", "directional", "motion", "orientation")),
    ("Geometry", ("rotation", "reflection", "symmetry", "scaling")),
    ("Color", ("color", "symbolic_remapping")),
    ("Growth", ("growth", "density", "propagation")),
    ("Identity", ("identity", "object_identity")),
    ("Pattern Completion", ("path", "completion", "repair")),
    ("Dependency", ("dependency", "causal")),
    ("Temporal", ("temporal", "sequence")),
    ("Context", ("context",)),
)

DOMAIN_DEPENDENCIES = {
    "Physics Domain": {
        "required_domains": ["Spatial Domain", "Geometry Domain"],
        "optional_domains": ["Temporal Domain"],
    },
    "Topology Domain": {
        "required_domains": ["Spatial Domain", "Identity Domain"],
        "optional_domains": ["Geometry Domain"],
    },
    "Pattern Completion Domain": {
        "required_domains": ["Geometry Domain", "Transformation Domain"],
        "optional_domains": ["Context Domain"],
    },
    "Growth Domain": {
        "required_domains": ["Spatial Domain", "Temporal Domain"],
        "optional_domains": ["Topology Domain"],
    },
    "Transformation Domain": {
        "required_domains": ["Geometry Domain"],
        "optional_domains": ["Spatial Domain"],
    },
    "Color Domain": {
        "required_domains": [],
        "optional_domains": [],
    },
}

DOMAIN_CONCEPT_BOUNDARIES = {
    "Physics Domain": ("gravity", "falling", "collision", "support", "rest_state", "downward_motion"),
    "Topology Domain": ("topology", "component", "connectivity", "bridge", "hole"),
    "Spatial Domain": ("spatial", "position", "directional", "motion", "orientation", "relative"),
    "Transformation Domain": ("rotation", "reflection", "remapping", "transformation", "scaling"),
    "Geometry Domain": ("geometry", "symmetry", "shape", "rotation", "reflection", "scaling"),
    "Identity Domain": ("identity", "preservation", "object_identity"),
    "Pattern Completion Domain": ("path", "completion", "repair", "pattern"),
    "Growth Domain": ("growth", "density", "propagation"),
    "Color Domain": ("color", "mapping", "symbolic_remapping"),
}

PROHIBITED_DOMAIN_ASSIGNMENTS = {
    "Transformation Domain": ("gravity", "collision", "topology_change"),
    "Context Domain": ("hole_removal", "bridge_creation", "rotation"),
    "Growth Domain": ("object_identity_preservation",),
}

DOMAIN_PRIVATE_CAPABILITIES = {
    "Physics Domain": ["collision_simulation"],
    "Topology Domain": ["topology_validation"],
    "Spatial Domain": ["spatial_constraint_solving"],
    "Transformation Domain": ["transformation_detection"],
    "Pattern Completion Domain": ["pattern_inference"],
}

DOMAIN_SHARED_CAPABILITIES = {
    "Spatial Domain": ["relative_position", "directional_motion", "spatial_constraints"],
    "Geometry Domain": ["object_shape", "shape_geometry", "symmetry_analysis"],
    "Transformation Domain": ["transformation_detection", "orientation_change"],
    "Color Domain": ["color_mapping"],
    "Identity Domain": ["object_identity_preservation"],
    "Physics Domain": ["object_motion_reasoning"],
    "Topology Domain": ["connectivity_reasoning"],
    "Pattern Completion Domain": ["pattern_inference"],
}

DOMAIN_OPERATIONAL_COMPOSITIONS = {
    "Object Falling Simulation": {
        "domains": ["Physics Domain", "Spatial Domain", "Geometry Domain"],
        "required_capabilities": ["gravity", "relative_position", "object_shape"],
    },
    "Bridge Creation Capability": {
        "domains": ["Topology Domain", "Spatial Domain", "Transformation Domain"],
        "required_capabilities": ["bridge_creation", "relative_position", "transformation_detection"],
    },
    "Pattern Completion Capability": {
        "domains": ["Pattern Completion Domain", "Transformation Domain", "Color Domain"],
        "required_capabilities": ["pattern_inference", "transformation_detection", "color_mapping"],
    },
}

DOMAIN_SEMANTIC_BOUNDARIES = {
    "Physics Domain": {
        "allowed_families": ["physics", "motion"],
        "forbidden_families": ["color", "topology", "temporal"],
        "allowed_capability_tokens": ["gravity", "falling", "collision", "support", "motion", "physics"],
        "forbidden_capability_tokens": ["color", "topology", "bridge", "hole"],
        "allowed_program_tokens": ["physics", "gravity"],
        "allowed_mental_model_tokens": ["gravity", "physics", "collision"],
    },
    "Topology Domain": {
        "allowed_families": ["topology", "connectivity"],
        "forbidden_families": ["physics", "color", "temporal"],
        "allowed_capability_tokens": ["topology", "connectivity", "component", "bridge", "hole"],
        "forbidden_capability_tokens": ["gravity", "color", "temporal"],
        "allowed_program_tokens": ["topology", "component"],
        "allowed_mental_model_tokens": ["topology", "connectivity"],
    },
    "Spatial Domain": {
        "allowed_families": ["spatial", "motion"],
        "forbidden_families": ["color"],
        "allowed_capability_tokens": ["spatial", "position", "direction", "motion", "relative"],
        "forbidden_capability_tokens": ["color"],
        "allowed_program_tokens": ["spatial", "path"],
        "allowed_mental_model_tokens": ["spatial"],
    },
    "Transformation Domain": {
        "allowed_families": ["transformation", "geometry"],
        "forbidden_families": ["physics", "topology"],
        "allowed_capability_tokens": ["rotation", "reflection", "transformation", "remapping", "scaling", "orientation"],
        "forbidden_capability_tokens": ["gravity", "collision", "topology"],
        "allowed_program_tokens": ["transformation", "rotation", "reflection"],
        "allowed_mental_model_tokens": ["transformation"],
    },
    "Growth Domain": {
        "allowed_families": ["growth"],
        "forbidden_families": ["identity"],
        "allowed_capability_tokens": ["growth", "density", "propagation"],
        "forbidden_capability_tokens": ["identity"],
        "allowed_program_tokens": ["growth"],
        "allowed_mental_model_tokens": ["growth"],
    },
    "Color Domain": {
        "allowed_families": ["color", "symbolic"],
        "forbidden_families": ["physics", "topology"],
        "allowed_capability_tokens": ["color", "mapping", "symbolic"],
        "forbidden_capability_tokens": ["gravity", "topology"],
        "allowed_program_tokens": ["color", "mapping"],
        "allowed_mental_model_tokens": ["color"],
    },
}

CAPABILITY_CANONICAL_OWNER = {
    "gravity": "Physics Domain",
    "falling": "Physics Domain",
    "collision": "Physics Domain",
    "relative_position": "Spatial Domain",
    "directional_motion": "Spatial Domain",
    "spatial_constraints": "Spatial Domain",
    "topology_change": "Topology Domain",
    "connectivity_change": "Topology Domain",
    "component_connection": "Topology Domain",
    "bridge_creation": "Topology Domain",
    "hole_removal": "Topology Domain",
    "rotation": "Transformation Domain",
    "reflection": "Transformation Domain",
    "color_mapping": "Color Domain",
    "density_preservation": "Growth Domain",
}

CAPABILITY_MIGRATION_HISTORY = [
    {
        "capability": "density_preservation",
        "previous_owner": "Transformation Domain",
        "new_owner": "Growth Domain",
        "migration_reason": "semantic_refinement_to_growth_density_behavior",
        "migration_timestamp": "2026-07-17T00:00:00Z",
    },
]


@dataclass
class CognitiveDomain:
    domain_id: str
    domain_name: str
    semantic_families: list[str] = field(default_factory=list)
    mental_models: list[str] = field(default_factory=list)
    program_blueprints: list[str] = field(default_factory=list)
    semantic_concepts: list[str] = field(default_factory=list)
    execution_packages: list[str] = field(default_factory=list)
    lifecycle_status: str = "FOUNDATIONAL"
    maturity_level: str = "FOUNDATIONAL"
    concept_count: int = 0
    mental_model_count: int = 0
    program_count: int = 0
    execution_package_count: int = 0
    operational_capabilities: list[str] = field(default_factory=list)
    missing_capabilities: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CognitiveDomainIntelligence:
    domain_id: str
    domain_name: str
    semantic_capabilities: list[str] = field(default_factory=list)
    operational_capabilities: list[str] = field(default_factory=list)
    semantic_families: list[str] = field(default_factory=list)
    mental_models: list[str] = field(default_factory=list)
    program_blueprints: list[str] = field(default_factory=list)
    semantic_concepts: list[str] = field(default_factory=list)
    execution_packages: list[str] = field(default_factory=list)
    supported_operations: list[str] = field(default_factory=list)
    missing_capabilities: list[str] = field(default_factory=list)
    required_domains: list[str] = field(default_factory=list)
    optional_domains: list[str] = field(default_factory=list)
    independent_capabilities: list[str] = field(default_factory=list)
    readiness_state: str = "NOT_READY"
    maturity_level: str = "FOUNDATIONAL"
    semantic_concept_count: int = 0
    semantic_family_count: int = 0
    mental_model_count: int = 0
    program_blueprint_count: int = 0
    execution_package_count: int = 0
    operational_capability_count: int = 0
    validation_failures: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CognitiveDomainLifecycle:
    domain_id: str
    domain_name: str
    lifecycle_stage: str = "DISCOVERED"
    maturity_level: str = "FOUNDATIONAL"
    semantic_readiness: str = "NOT_READY"
    mental_model_readiness: str = "NOT_READY"
    program_readiness: str = "NOT_READY"
    execution_readiness: str = "NOT_READY"
    candidate_readiness: str = "NOT_READY"
    operational_readiness: str = "NOT_READY"
    required_domains: list[str] = field(default_factory=list)
    optional_domains: list[str] = field(default_factory=list)
    inherited_capabilities: dict[str, list[str]] = field(default_factory=dict)
    semantic_capability_evolution: list[str] = field(default_factory=list)
    mental_model_evolution: list[str] = field(default_factory=list)
    program_blueprint_evolution: list[str] = field(default_factory=list)
    execution_capability_evolution: list[str] = field(default_factory=list)
    candidate_capability_evolution: list[str] = field(default_factory=list)
    operational_capability_evolution: list[str] = field(default_factory=list)
    missing_capabilities: list[str] = field(default_factory=list)
    missing_dependencies: list[str] = field(default_factory=list)
    lifecycle_failures: list[dict[str, Any]] = field(default_factory=list)
    operational_status: str = "NOT_READY"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DomainInteraction:
    source_domain: str
    target_domain: str
    interaction_type: str
    shared_capabilities: list[str] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)
    optional_capabilities: list[str] = field(default_factory=list)
    operational_constraints: list[str] = field(default_factory=list)
    interaction_status: str = "FOUNDATIONAL"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CognitiveDomainGovernance:
    domain_name: str
    ownership_rules: dict[str, Any] = field(default_factory=dict)
    semantic_boundaries: dict[str, Any] = field(default_factory=dict)
    allowed_capabilities: list[str] = field(default_factory=list)
    forbidden_capabilities: list[str] = field(default_factory=list)
    maturity_constraints: dict[str, Any] = field(default_factory=dict)
    dependency_constraints: dict[str, Any] = field(default_factory=dict)
    capability_admission_rules: dict[str, Any] = field(default_factory=dict)
    capability_conflicts: list[dict[str, Any]] = field(default_factory=list)
    migration_history: list[dict[str, Any]] = field(default_factory=list)
    boundary_violations: list[dict[str, Any]] = field(default_factory=list)
    missing_governance_requirements: list[str] = field(default_factory=list)
    semantic_coherence_score: float = 1.0
    ownership_consistency_score: float = 1.0
    maturity_consistency_score: float = 1.0
    dependency_consistency_score: float = 1.0
    governance_integrity_score: float = 1.0
    governance_status: str = "VALID"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CognitiveDomainEcosystem:
    total_domains: int = 0
    total_semantic_concepts: int = 0
    total_mental_models: int = 0
    total_program_blueprints: int = 0
    total_execution_packages: int = 0
    total_operational_capabilities: int = 0
    total_candidate_ready_programs: int = 0
    total_operational_domains: int = 0
    domain_distribution: dict[str, int] = field(default_factory=dict)
    capability_coverage: float = 0.0
    semantic_integrity_score: float = 1.0
    governance_integrity_score: float = 1.0
    ecosystem_maturity_score: float = 0.0
    capability_coverage_score: float = 0.0
    collaboration_score: float = 0.0
    operational_readiness_score: float = 0.0
    architectural_coherence_score: float = 0.0
    covered_domains: list[str] = field(default_factory=list)
    partially_covered_domains: list[str] = field(default_factory=list)
    missing_domains: list[str] = field(default_factory=list)
    dependency_graph: dict[str, list[str]] = field(default_factory=dict)
    collaboration_graph: dict[str, list[str]] = field(default_factory=dict)
    operational_capability_graph: dict[str, list[str]] = field(default_factory=dict)
    missing_ecosystem_capabilities: list[str] = field(default_factory=list)
    cognitive_imbalances: list[dict[str, Any]] = field(default_factory=list)
    cognitive_bottlenecks: list[dict[str, Any]] = field(default_factory=list)
    ecosystem_maturity: str = "FOUNDATIONAL"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


CONSTITUTIONAL_PRINCIPLES = [
    "EXPLICIT_OWNERSHIP",
    "SEMANTIC_INTEGRITY",
    "ZERO_SILENT_FAILURE",
    "EXPLICIT_COLLABORATION",
    "CONTROLLED_EVOLUTION",
    "ARCHITECTURAL_COHERENCE",
    "CAPABILITY_TRANSPARENCY",
    "EXTENSIBILITY",
    "CONSTITUTIONAL_PROTECTION",
]

ARCHITECTURAL_INVARIANTS = [
    "SINGLE_CANONICAL_DOMAIN_PER_CONCEPT_UNLESS_SHARED",
    "SINGLE_DOMAIN_PER_PROGRAM_BLUEPRINT",
    "MENTAL_MODEL_HAS_DOMAIN",
    "DOMAIN_EXPOSES_LIFECYCLE_AND_GOVERNANCE",
    "OPERATIONAL_CAPABILITY_DECLARES_DEPENDENCIES",
    "NO_SILENT_CAPABILITY_DISAPPEARANCE",
    "OWNERSHIP_CONFLICTS_OBSERVABLE",
    "NO_SEMANTIC_DOMAIN_POLLUTION",
    "NO_UNAUTHORIZED_CAPABILITY_MIGRATION",
    "DOMAIN_REMAINS_CONSTITUTIONALLY_VALID",
]

DOMAIN_CONSTITUTIONAL_RIGHTS = [
    "explicit_ownership_rights",
    "semantic_boundary_protection",
    "capability_ownership_protection",
    "lifecycle_protection",
    "governance_protection",
    "collaboration_protection",
]

DOMAIN_CONSTITUTIONAL_RESPONSIBILITIES = [
    "maintain_semantic_coherence",
    "expose_lifecycle_states",
    "expose_governance_states",
    "expose_dependencies",
    "support_constitutional_validation",
    "support_ecosystem_transparency",
]


@dataclass
class CognitiveDomainConstitution:
    constitutional_principles: list[str] = field(default_factory=list)
    architectural_invariants: list[str] = field(default_factory=list)
    constitutional_validations: dict[str, bool] = field(default_factory=dict)
    constitutional_violations: list[dict[str, Any]] = field(default_factory=list)
    domain_constitutional_health: list[dict[str, Any]] = field(default_factory=list)
    domain_rights: list[str] = field(default_factory=list)
    domain_responsibilities: list[str] = field(default_factory=list)
    constitutional_status: str = "FOUNDATIONAL"
    constitutional_integrity_score: float = 0.0
    architectural_integrity_score: float = 0.0
    semantic_integrity_score: float = 0.0
    governance_integrity_score: float = 0.0
    collaboration_integrity_score: float = 0.0
    ecosystem_coherence_score: float = 0.0
    constitutional_compliance_score: float = 0.0
    silent_constitutional_failures: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CognitiveKnowledgeDomainRegistry:
    """Organize concepts, mental models, programs, and packages by domain."""

    system_name = "cognitive_knowledge_domain_registry"

    def build(
        self,
        *,
        concept_lifecycle_report: Mapping[str, Any] | None = None,
        program_blueprint_intelligence_report: Mapping[str, Any] | None = None,
        cognitive_program_lifecycle_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        domains = self._seed_domains()
        concept_rows = _rows(concept_lifecycle_report, "concept_lifecycles")
        intelligence_rows = _rows(program_blueprint_intelligence_report, "program_blueprint_intelligence")
        program_rows = _rows(cognitive_program_lifecycle_report, "program_registry")

        for row in concept_rows:
            self._assign_concept(domains, row)
        for row in intelligence_rows:
            self._assign_program_intelligence(domains, row)
        for row in program_rows:
            self._assign_program_lifecycle(domains, row)

        domain_rows = [self._finalize(domain).as_dict() for domain in domains.values()]
        validation = self._validate(domain_rows, concept_rows, intelligence_rows, program_rows)
        return {
            "system": self.system_name,
            "COGNITIVE_KNOWLEDGE_DOMAINS_REPORT": True,
            "domain_count": len(domain_rows),
            "domains": domain_rows,
            "orphan_concepts": validation["orphan_concepts"],
            "invalid_family_assignments": validation["invalid_family_assignments"],
            "invalid_mental_model_assignments": validation["invalid_mental_model_assignments"],
            "invalid_program_blueprint_assignments": validation["invalid_program_blueprint_assignments"],
            "missing_domain_ownership": validation["missing_domain_ownership"],
            "validation_success": validation["validation_success"],
            "silent_domain_assignment_failures": False,
        }

    def _seed_domains(self) -> dict[str, CognitiveDomain]:
        return {
            key: CognitiveDomain(
                domain_id=f"domain:{_normalize(key)}",
                domain_name=name,
                semantic_families=[key],
            )
            for key, name in FOUNDATIONAL_DOMAINS.items()
        }

    def _assign_concept(self, domains: dict[str, CognitiveDomain], row: Mapping[str, Any]) -> None:
        concept = _normalize(row.get("concept_name"))
        if not concept:
            return
        family = str(row.get("semantic_cluster") or "")
        domain_key = self._domain_key(family, concept)
        domain = self._domain(domains, domain_key)
        _append(domain.semantic_concepts, concept)
        if family:
            _append(domain.semantic_families, family)
        mental_model = str(row.get("mental_model") or "")
        if mental_model and mental_model != "Not Available":
            _append(domain.mental_models, mental_model)
        package_state = str(row.get("execution_package_available") or "")
        if package_state == "TRUE":
            _append(domain.execution_packages, f"{concept}_execution_package")
        for requirement in row.get("missing_requirements", []) or []:
            _append(domain.missing_capabilities, str(requirement))

    def _assign_program_intelligence(self, domains: dict[str, CognitiveDomain], row: Mapping[str, Any]) -> None:
        family = str(row.get("semantic_family") or "")
        domain = self._domain(domains, self._domain_key(family, ""))
        program_type = str(row.get("program_type") or "")
        if program_type:
            _append(domain.program_blueprints, program_type)
        if family:
            _append(domain.semantic_families, family)
        mental_model = str(row.get("mental_model") or "")
        if mental_model and mental_model != "Not Available":
            _append(domain.mental_models, mental_model)
        for concept in row.get("supported_concepts", []) or []:
            _append(domain.semantic_concepts, _normalize(concept))
        for package in row.get("required_packages", []) or []:
            package = str(package)
            if package not in (row.get("missing_requirements", []) or []):
                _append(domain.execution_packages, package)
        for requirement in row.get("missing_requirements", []) or []:
            _append(domain.missing_capabilities, str(requirement))
        for capability in (row.get("capability_profile", {}) or {}).get("execution_capabilities", []) or []:
            _append(domain.operational_capabilities, str(capability))

    def _assign_program_lifecycle(self, domains: dict[str, CognitiveDomain], row: Mapping[str, Any]) -> None:
        family = str(row.get("semantic_family") or "")
        domain = self._domain(domains, self._domain_key(family, ""))
        program_type = str(row.get("program_type") or "")
        if program_type:
            _append(domain.program_blueprints, program_type)
        for concept in row.get("supported_concepts", []) or []:
            _append(domain.semantic_concepts, _normalize(concept))
        for package in row.get("required_packages", []) or []:
            if str(package) not in (row.get("missing_requirements", []) or []):
                _append(domain.execution_packages, str(package))
        for requirement in row.get("missing_requirements", []) or []:
            _append(domain.missing_capabilities, str(requirement))
        capability_profile = row.get("capability_profile", {}) or {}
        for capability in capability_profile.get("execution_capabilities", []) or []:
            _append(domain.operational_capabilities, str(capability))

    def _domain_key(self, family: str, concept: str) -> str:
        if family in DOMAIN_BY_FAMILY:
            return DOMAIN_BY_FAMILY[family]
        if family:
            return family
        concept = _normalize(concept)
        for domain, tokens in DOMAIN_BY_CONCEPT_TOKEN:
            if any(token in concept for token in tokens):
                return domain
        return "Context"

    def _domain(self, domains: dict[str, CognitiveDomain], key: str) -> CognitiveDomain:
        if key not in domains:
            domains[key] = CognitiveDomain(
                domain_id=f"domain:{_normalize(key)}",
                domain_name=f"{key} Domain",
                semantic_families=[key],
            )
        return domains[key]

    def _finalize(self, domain: CognitiveDomain) -> CognitiveDomain:
        domain.semantic_families = _dedupe(domain.semantic_families)
        domain.mental_models = _dedupe(domain.mental_models)
        domain.program_blueprints = _dedupe(domain.program_blueprints)
        domain.semantic_concepts = _dedupe([item for item in domain.semantic_concepts if item])
        domain.execution_packages = _dedupe(domain.execution_packages)
        domain.operational_capabilities = _dedupe(domain.operational_capabilities)
        domain.missing_capabilities = _dedupe(domain.missing_capabilities)
        domain.concept_count = len(domain.semantic_concepts)
        domain.mental_model_count = len(domain.mental_models)
        domain.program_count = len(domain.program_blueprints)
        domain.execution_package_count = len(domain.execution_packages)
        domain.maturity_level = self._maturity(domain)
        domain.lifecycle_status = domain.maturity_level
        return domain

    def _maturity(self, domain: CognitiveDomain) -> str:
        if domain.operational_capabilities and not domain.missing_capabilities:
            return "FULLY_OPERATIONAL"
        if domain.operational_capabilities:
            return "PARTIALLY_OPERATIONAL"
        if domain.program_blueprints and domain.execution_packages:
            return "ADVANCED"
        if domain.program_blueprints:
            return "DEVELOPING"
        return "FOUNDATIONAL"

    def _validate(
        self,
        domains: list[dict[str, Any]],
        concept_rows: list[Mapping[str, Any]],
        intelligence_rows: list[Mapping[str, Any]],
        program_rows: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        assigned = {
            concept
            for domain in domains
            for concept in domain.get("semantic_concepts", [])
        }
        source_concepts = {
            _normalize(row.get("concept_name"))
            for row in concept_rows
            if row.get("concept_name")
        }
        for row in intelligence_rows + program_rows:
            for concept in row.get("supported_concepts", []) or []:
                source_concepts.add(_normalize(concept))
        orphan = sorted(source_concepts - assigned)
        invalid_family = [
            str(row.get("program_type") or row.get("concept_name") or "unknown")
            for row in intelligence_rows + program_rows
            if not (row.get("semantic_family") or row.get("semantic_cluster"))
        ]
        invalid_model = [
            str(row.get("mental_model"))
            for row in concept_rows + intelligence_rows
            if row.get("mental_model") in {"", None}
        ]
        invalid_program = [
            str(row.get("program_type"))
            for row in intelligence_rows + program_rows
            if not row.get("program_type")
        ]
        missing_ownership = orphan + invalid_family + invalid_model + invalid_program
        return {
            "orphan_concepts": orphan,
            "invalid_family_assignments": _dedupe(invalid_family),
            "invalid_mental_model_assignments": _dedupe(invalid_model),
            "invalid_program_blueprint_assignments": _dedupe(invalid_program),
            "missing_domain_ownership": _dedupe(missing_ownership),
            "validation_success": not missing_ownership,
        }


class CognitiveDomainIntelligenceLayer:
    """Describe capabilities, dependencies, and boundaries for each domain."""

    system_name = "cognitive_domain_intelligence_layer"

    def analyze(
        self,
        cognitive_knowledge_domains_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        report = cognitive_knowledge_domains_report if isinstance(cognitive_knowledge_domains_report, Mapping) else {}
        domains = report.get("domains", [])
        domains = domains if isinstance(domains, list) else []
        domain_names = {
            str(domain.get("domain_name"))
            for domain in domains
            if isinstance(domain, Mapping) and domain.get("domain_name")
        }
        intelligence = [
            self._build_domain_intelligence(domain, domain_names).as_dict()
            for domain in domains
            if isinstance(domain, Mapping)
        ]
        validation = self._validate(intelligence, domain_names)
        readiness_distribution: dict[str, int] = {}
        for domain in intelligence:
            state = str(domain.get("readiness_state") or "NOT_READY")
            readiness_distribution[state] = readiness_distribution.get(state, 0) + 1
        return {
            "system": self.system_name,
            "COGNITIVE_DOMAIN_INTELLIGENCE_REPORT": True,
            "domain_intelligence_count": len(intelligence),
            "domain_intelligence": intelligence,
            "readiness_distribution": readiness_distribution,
            "validation": validation,
            "validation_success": validation["validation_success"],
            "silent_domain_intelligence_failures": False,
        }

    def _build_domain_intelligence(
        self,
        domain: Mapping[str, Any],
        domain_names: set[str],
    ) -> CognitiveDomainIntelligence:
        domain_name = str(domain.get("domain_name") or "Unknown Domain")
        semantic_concepts = _dedupe(_as_list(domain.get("semantic_concepts")))
        semantic_families = _dedupe(_as_list(domain.get("semantic_families")))
        mental_models = _dedupe(_as_list(domain.get("mental_models")))
        program_blueprints = _dedupe(_as_list(domain.get("program_blueprints")))
        execution_packages = _dedupe(_as_list(domain.get("execution_packages")))
        missing_capabilities = _dedupe(_as_list(domain.get("missing_capabilities")))
        operational = _dedupe(_as_list(domain.get("operational_capabilities")))
        semantic_capabilities = _dedupe([
            *semantic_concepts,
            *[
                capability
                for capability in domain.get("operational_capabilities", []) or []
                if str(capability).endswith("_semantic")
            ],
        ])
        supported_operations = self._supported_operations(
            program_blueprints,
            execution_packages,
            operational,
        )
        dependencies = DOMAIN_DEPENDENCIES.get(
            domain_name,
            {"required_domains": [], "optional_domains": []},
        )
        required_domains = [
            dependency
            for dependency in dependencies.get("required_domains", [])
            if dependency in domain_names
        ]
        optional_domains = [
            dependency
            for dependency in dependencies.get("optional_domains", [])
            if dependency in domain_names
        ]
        validation_failures = self._domain_validation_failures(
            domain_name,
            semantic_concepts,
            semantic_families,
            mental_models,
            program_blueprints,
            dependencies,
            domain_names,
        )
        readiness = self._readiness(
            semantic_concepts=semantic_concepts,
            mental_models=mental_models,
            program_blueprints=program_blueprints,
            execution_packages=execution_packages,
            operational_capabilities=operational,
            missing_capabilities=missing_capabilities,
            validation_failures=validation_failures,
        )
        return CognitiveDomainIntelligence(
            domain_id=str(domain.get("domain_id") or f"domain:{_normalize(domain_name)}"),
            domain_name=domain_name,
            semantic_capabilities=semantic_capabilities,
            operational_capabilities=operational,
            semantic_families=semantic_families,
            mental_models=mental_models,
            program_blueprints=program_blueprints,
            semantic_concepts=semantic_concepts,
            execution_packages=execution_packages,
            supported_operations=supported_operations,
            missing_capabilities=missing_capabilities,
            required_domains=required_domains,
            optional_domains=optional_domains,
            independent_capabilities=self._independent_capabilities(domain_name, semantic_capabilities),
            readiness_state=readiness,
            maturity_level=str(domain.get("maturity_level") or readiness),
            semantic_concept_count=len(semantic_concepts),
            semantic_family_count=len(semantic_families),
            mental_model_count=len(mental_models),
            program_blueprint_count=len(program_blueprints),
            execution_package_count=len(execution_packages),
            operational_capability_count=len(operational),
            validation_failures=validation_failures,
        )

    def _supported_operations(
        self,
        program_blueprints: list[str],
        execution_packages: list[str],
        operational_capabilities: list[str],
    ) -> list[str]:
        operations = [
            item.replace("_program", "_operation")
            for item in program_blueprints
        ]
        operations.extend(
            item.replace("_execution_package", "_execution")
            for item in execution_packages
        )
        operations.extend(operational_capabilities)
        return _dedupe(operations)

    def _independent_capabilities(
        self,
        domain_name: str,
        semantic_capabilities: list[str],
    ) -> list[str]:
        if DOMAIN_DEPENDENCIES.get(domain_name, {}).get("required_domains"):
            return []
        return semantic_capabilities

    def _readiness(
        self,
        *,
        semantic_concepts: list[str],
        mental_models: list[str],
        program_blueprints: list[str],
        execution_packages: list[str],
        operational_capabilities: list[str],
        missing_capabilities: list[str],
        validation_failures: list[dict[str, Any]],
    ) -> str:
        if validation_failures:
            return "NOT_READY"
        if operational_capabilities and not missing_capabilities:
            return "FULLY_OPERATIONAL"
        if operational_capabilities:
            return "PARTIALLY_OPERATIONAL"
        if execution_packages and program_blueprints:
            return "ADVANCED"
        if program_blueprints:
            return "OPERATIONAL"
        if semantic_concepts and mental_models:
            return "FOUNDATIONAL"
        return "NOT_READY"

    def _domain_validation_failures(
        self,
        domain_name: str,
        semantic_concepts: list[str],
        semantic_families: list[str],
        mental_models: list[str],
        program_blueprints: list[str],
        dependencies: Mapping[str, Any],
        domain_names: set[str],
    ) -> list[dict[str, Any]]:
        failures: list[dict[str, Any]] = []
        boundary = DOMAIN_CONCEPT_BOUNDARIES.get(domain_name)
        prohibited = PROHIBITED_DOMAIN_ASSIGNMENTS.get(domain_name, ())
        if boundary:
            invalid = [
                concept
                for concept in semantic_concepts
                if not any(token in concept for token in boundary)
            ]
            for concept in invalid:
                failures.append({
                    "failure_type": "invalid_concept_assignment",
                    "domain": domain_name,
                    "item": concept,
                    "reason": "DOMAIN_BOUNDARY_VIOLATION",
                })
        for concept in semantic_concepts:
            if concept in prohibited:
                failures.append({
                    "failure_type": "domain_pollution",
                    "domain": domain_name,
                    "item": concept,
                    "reason": "PROHIBITED_ASSIGNMENT",
                })
        if semantic_concepts and not semantic_families:
            failures.append({
                "failure_type": "semantic_family_inconsistency",
                "domain": domain_name,
                "item": domain_name,
                "reason": "MISSING_SEMANTIC_FAMILY",
            })
        if semantic_concepts and not mental_models and program_blueprints:
            failures.append({
                "failure_type": "invalid_mental_model_assignment",
                "domain": domain_name,
                "item": domain_name,
                "reason": "MISSING_MENTAL_MODEL",
            })
        for program in program_blueprints:
            expected = _normalize(domain_name.replace(" Domain", ""))
            if expected not in _normalize(program) and domain_name in FOUNDATIONAL_DOMAINS.values():
                failures.append({
                    "failure_type": "invalid_program_assignment",
                    "domain": domain_name,
                    "item": program,
                    "reason": "PROGRAM_DOMAIN_MISMATCH",
                })
        for dependency in dependencies.get("required_domains", []) or []:
            if dependency not in domain_names:
                failures.append({
                    "failure_type": "invalid_domain_dependency",
                    "domain": domain_name,
                    "item": dependency,
                    "reason": "REQUIRED_DOMAIN_MISSING",
                })
        return failures

    def _validate(
        self,
        intelligence: list[dict[str, Any]],
        domain_names: set[str],
    ) -> dict[str, Any]:
        failures = [
            failure
            for domain in intelligence
            for failure in domain.get("validation_failures", [])
        ]
        return {
            "invalid_concept_assignments": [
                failure for failure in failures
                if failure.get("failure_type") == "invalid_concept_assignment"
            ],
            "invalid_mental_model_assignments": [
                failure for failure in failures
                if failure.get("failure_type") == "invalid_mental_model_assignment"
            ],
            "invalid_program_assignments": [
                failure for failure in failures
                if failure.get("failure_type") == "invalid_program_assignment"
            ],
            "invalid_domain_dependencies": [
                failure for failure in failures
                if failure.get("failure_type") == "invalid_domain_dependency"
            ],
            "semantic_family_inconsistencies": [
                failure for failure in failures
                if failure.get("failure_type") == "semantic_family_inconsistency"
            ],
            "domain_pollution": [
                failure for failure in failures
                if failure.get("failure_type") == "domain_pollution"
            ],
            "known_domain_count": len(domain_names),
            "validation_failures": failures,
            "validation_success": not failures,
        }


class CognitiveDomainLifecycleRegistry:
    """Track domain maturation, readiness, failures, and capability evolution."""

    system_name = "cognitive_domain_lifecycle_registry"

    def build(
        self,
        cognitive_domain_intelligence_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        report = cognitive_domain_intelligence_report if isinstance(cognitive_domain_intelligence_report, Mapping) else {}
        rows = report.get("domain_intelligence", [])
        rows = rows if isinstance(rows, list) else []
        intelligence = [
            row for row in rows
            if isinstance(row, Mapping)
        ]
        capabilities_by_domain = {
            str(row.get("domain_name")): _dedupe(_as_list(row.get("semantic_capabilities")))
            for row in intelligence
            if row.get("domain_name")
        }
        registry = [
            self._build_lifecycle(row, capabilities_by_domain).as_dict()
            for row in intelligence
        ]
        metrics = self._metrics(registry)
        return {
            "system": self.system_name,
            "COGNITIVE_DOMAIN_LIFECYCLE_REPORT": True,
            "total_domains": len(registry),
            "domain_registry": registry,
            "domain_readiness_distribution": metrics["domain_readiness_distribution"],
            "lifecycle_distribution": metrics["lifecycle_distribution"],
            "capability_distribution": metrics["capability_distribution"],
            "operational_domains": metrics["operational_domains"],
            "partially_operational_domains": metrics["partially_operational_domains"],
            "foundational_domains": metrics["foundational_domains"],
            "advanced_domains": metrics["advanced_domains"],
            "silent_domain_lifecycle_failures": False,
        }

    def _build_lifecycle(
        self,
        row: Mapping[str, Any],
        capabilities_by_domain: Mapping[str, list[str]],
    ) -> CognitiveDomainLifecycle:
        semantic = _dedupe(_as_list(row.get("semantic_capabilities")))
        mental_models = _dedupe(_as_list(row.get("mental_models")))
        programs = _dedupe(_as_list(row.get("program_blueprints")))
        packages = _dedupe(_as_list(row.get("execution_packages")))
        operational = _dedupe(_as_list(row.get("operational_capabilities")))
        missing = _dedupe(_as_list(row.get("missing_capabilities")))
        required_domains = _dedupe(_as_list(row.get("required_domains")))
        optional_domains = _dedupe(_as_list(row.get("optional_domains")))
        inherited = {
            dependency: capabilities_by_domain.get(dependency, [])
            for dependency in required_domains + optional_domains
            if capabilities_by_domain.get(dependency)
        }
        readiness = {
            "semantic": "READY" if semantic else "NOT_READY",
            "mental_model": "READY" if mental_models else "NOT_READY",
            "program": "READY" if programs else "NOT_READY",
            "execution": "READY" if packages else "NOT_READY",
            "candidate": self._candidate_readiness(missing, programs),
            "operational": "READY" if operational and not missing else "NOT_READY",
        }
        stage = self._lifecycle_stage(readiness, operational, missing)
        failures = self._failures(
            domain_name=str(row.get("domain_name") or "Unknown Domain"),
            readiness=readiness,
            missing=missing,
            required_domains=required_domains,
            packages=packages,
            mental_models=mental_models,
            programs=programs,
        )
        maturity = self._maturity(stage, readiness, operational, missing)
        return CognitiveDomainLifecycle(
            domain_id=str(row.get("domain_id") or f"domain:{_normalize(row.get('domain_name'))}"),
            domain_name=str(row.get("domain_name") or "Unknown Domain"),
            lifecycle_stage=stage,
            maturity_level=maturity,
            semantic_readiness=readiness["semantic"],
            mental_model_readiness=readiness["mental_model"],
            program_readiness=readiness["program"],
            execution_readiness=readiness["execution"],
            candidate_readiness=readiness["candidate"],
            operational_readiness=readiness["operational"],
            required_domains=required_domains,
            optional_domains=optional_domains,
            inherited_capabilities=inherited,
            semantic_capability_evolution=semantic,
            mental_model_evolution=mental_models,
            program_blueprint_evolution=programs,
            execution_capability_evolution=packages,
            candidate_capability_evolution=[
                item for item in missing
                if "candidate" in item
            ],
            operational_capability_evolution=operational,
            missing_capabilities=missing,
            missing_dependencies=[],
            lifecycle_failures=failures,
            operational_status=maturity,
        )

    def _candidate_readiness(
        self,
        missing: list[str],
        programs: list[str],
    ) -> str:
        if any("candidate" in item for item in missing):
            return "NOT_READY"
        return "READY" if programs else "NOT_READY"

    def _lifecycle_stage(
        self,
        readiness: Mapping[str, str],
        operational: list[str],
        missing: list[str],
    ) -> str:
        if readiness["semantic"] != "READY":
            return "DISCOVERED"
        if readiness["mental_model"] != "READY":
            return "SEMANTICALLY_DEFINED"
        if readiness["program"] != "READY":
            return "MENTAL_MODEL_DEFINED"
        if readiness["execution"] != "READY":
            return "PROGRAM_DEFINED"
        if readiness["candidate"] != "READY":
            return "EXECUTION_DEFINED"
        if readiness["operational"] != "READY":
            return "PARTIALLY_OPERATIONAL"
        if operational and missing:
            return "OPERATIONAL"
        if len(operational) > 1:
            return "ADVANCED"
        return "FULLY_OPERATIONAL"

    def _maturity(
        self,
        stage: str,
        readiness: Mapping[str, str],
        operational: list[str],
        missing: list[str],
    ) -> str:
        if stage == "DISCOVERED":
            return "FOUNDATIONAL"
        if stage in {"SEMANTICALLY_DEFINED", "MENTAL_MODEL_DEFINED"}:
            return "EARLY_DEVELOPMENT"
        if stage == "PROGRAM_DEFINED":
            return "DEVELOPING"
        if stage in {"EXECUTION_DEFINED", "PARTIALLY_OPERATIONAL"}:
            return "PARTIALLY_OPERATIONAL"
        if stage == "OPERATIONAL":
            return "OPERATIONAL"
        if stage == "ADVANCED":
            return "ADVANCED"
        if readiness["operational"] == "READY" and operational and not missing:
            return "FULLY_OPERATIONAL"
        return "FOUNDATIONAL"

    def _failures(
        self,
        *,
        domain_name: str,
        readiness: Mapping[str, str],
        missing: list[str],
        required_domains: list[str],
        packages: list[str],
        mental_models: list[str],
        programs: list[str],
    ) -> list[dict[str, Any]]:
        failures: list[dict[str, Any]] = []
        if readiness["mental_model"] != "READY" and readiness["semantic"] == "READY":
            failures.append({
                "domain": domain_name,
                "failed_lifecycle_stage": "MENTAL_MODEL_DEFINED",
                "reason": "mental_model_missing",
                "missing_capabilities": ["mental_model"],
                "missing_dependencies": [],
                "missing_execution_packages": [],
                "missing_mental_models": ["mental_model"] if not mental_models else [],
                "missing_programs": [],
            })
        if readiness["program"] != "READY" and readiness["mental_model"] == "READY":
            failures.append({
                "domain": domain_name,
                "failed_lifecycle_stage": "PROGRAM_DEFINED",
                "reason": f"{_normalize(domain_name.replace(' Domain', ''))}_program_missing",
                "missing_capabilities": ["program_blueprint"],
                "missing_dependencies": [],
                "missing_execution_packages": [],
                "missing_mental_models": [],
                "missing_programs": ["program_blueprint"] if not programs else [],
            })
        if readiness["execution"] != "READY" and readiness["program"] == "READY":
            failures.append({
                "domain": domain_name,
                "failed_lifecycle_stage": "EXECUTION_DEFINED",
                "reason": f"{_normalize(domain_name.replace(' Domain', ''))}_execution_package_missing",
                "missing_capabilities": missing or ["execution_package"],
                "missing_dependencies": required_domains,
                "missing_execution_packages": ["execution_package"] if not packages else [],
                "missing_mental_models": [],
                "missing_programs": [],
            })
        if readiness["candidate"] != "READY" and readiness["execution"] == "READY":
            failures.append({
                "domain": domain_name,
                "failed_lifecycle_stage": "PARTIALLY_OPERATIONAL",
                "reason": "candidate_support_missing",
                "missing_capabilities": [
                    item for item in missing
                    if "candidate" in item
                ] or ["candidate_support"],
                "missing_dependencies": required_domains,
                "missing_execution_packages": [],
                "missing_mental_models": [],
                "missing_programs": [],
            })
        return failures

    def _metrics(self, registry: list[dict[str, Any]]) -> dict[str, Any]:
        readiness_distribution: dict[str, int] = {}
        lifecycle_distribution: dict[str, int] = {}
        capability_distribution = {
            "semantic": 0,
            "mental_model": 0,
            "program": 0,
            "execution": 0,
            "candidate": 0,
            "operational": 0,
        }
        for row in registry:
            maturity = str(row.get("maturity_level") or "FOUNDATIONAL")
            stage = str(row.get("lifecycle_stage") or "DISCOVERED")
            readiness_distribution[maturity] = readiness_distribution.get(maturity, 0) + 1
            lifecycle_distribution[stage] = lifecycle_distribution.get(stage, 0) + 1
            capability_distribution["semantic"] += len(row.get("semantic_capability_evolution", []) or [])
            capability_distribution["mental_model"] += len(row.get("mental_model_evolution", []) or [])
            capability_distribution["program"] += len(row.get("program_blueprint_evolution", []) or [])
            capability_distribution["execution"] += len(row.get("execution_capability_evolution", []) or [])
            capability_distribution["candidate"] += len(row.get("candidate_capability_evolution", []) or [])
            capability_distribution["operational"] += len(row.get("operational_capability_evolution", []) or [])
        return {
            "domain_readiness_distribution": readiness_distribution,
            "lifecycle_distribution": lifecycle_distribution,
            "capability_distribution": capability_distribution,
            "operational_domains": sum(1 for row in registry if row.get("maturity_level") == "OPERATIONAL"),
            "partially_operational_domains": sum(1 for row in registry if row.get("maturity_level") == "PARTIALLY_OPERATIONAL"),
            "foundational_domains": sum(1 for row in registry if row.get("maturity_level") == "FOUNDATIONAL"),
            "advanced_domains": sum(1 for row in registry if row.get("maturity_level") == "ADVANCED"),
        }


class CognitiveDomainInteractionRegistry:
    """Build explicit cross-domain collaboration and capability sharing maps."""

    system_name = "cognitive_domain_interaction_registry"

    def build(
        self,
        cognitive_domain_lifecycle_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        report = cognitive_domain_lifecycle_report if isinstance(cognitive_domain_lifecycle_report, Mapping) else {}
        rows = report.get("domain_registry", [])
        rows = rows if isinstance(rows, list) else []
        domains = [row for row in rows if isinstance(row, Mapping)]
        domain_names = {
            str(row.get("domain_name"))
            for row in domains
            if row.get("domain_name")
        }
        capabilities = {
            str(row.get("domain_name")): self._domain_capabilities(row)
            for row in domains
            if row.get("domain_name")
        }
        interactions: list[dict[str, Any]] = []
        domain_reports = []
        for row in domains:
            domain_reports.append(
                self._domain_interaction_report(row, domain_names, capabilities, interactions)
            )
        compositions = [
            self._composition_status(name, spec, capabilities, domain_names)
            for name, spec in DOMAIN_OPERATIONAL_COMPOSITIONS.items()
        ]
        validation = self._validate(interactions, compositions)
        return {
            "system": self.system_name,
            "COGNITIVE_DOMAIN_INTERACTION_REPORT": True,
            "domain_interaction_count": len(interactions),
            "domain_interactions": interactions,
            "domain_interaction_reports": domain_reports,
            "dependency_graph": self._dependency_graph(domain_reports),
            "operational_capability_compositions": compositions,
            "validation": validation,
            "validation_success": validation["validation_success"],
            "silent_domain_interaction_failures": False,
        }

    def _domain_interaction_report(
        self,
        row: Mapping[str, Any],
        domain_names: set[str],
        capabilities: Mapping[str, list[str]],
        interactions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        source = str(row.get("domain_name") or "Unknown Domain")
        required_domains = _dedupe(_as_list(row.get("required_domains")))
        optional_domains = _dedupe(_as_list(row.get("optional_domains")))
        shared = DOMAIN_SHARED_CAPABILITIES.get(source, [])
        private = DOMAIN_PRIVATE_CAPABILITIES.get(source, [])
        missing_collab: list[str] = []
        collaborators = _dedupe(required_domains + optional_domains)
        for target in required_domains:
            interaction = self._interaction(
                source,
                target,
                "DEPENDENCY",
                required_capabilities=capabilities.get(target, []),
                shared_capabilities=shared,
                domain_names=domain_names,
            )
            if interaction["interaction_status"] == "BLOCKED":
                missing_collab.extend(interaction["required_capabilities"] or [target])
            interactions.append(interaction)
        for target in optional_domains:
            interactions.append(
                self._interaction(
                    source,
                    target,
                    "OPTIONAL_SUPPORT",
                    optional_capabilities=capabilities.get(target, []),
                    shared_capabilities=shared,
                    domain_names=domain_names,
                )
            )
        for target in self._collaboration_targets(source, domain_names):
            interactions.append(
                self._interaction(
                    source,
                    target,
                    "COLLABORATION",
                    optional_capabilities=capabilities.get(target, []),
                    shared_capabilities=shared,
                    domain_names=domain_names,
                )
            )
            _append(collaborators, target)
        compositions = [
            name
            for name, spec in DOMAIN_OPERATIONAL_COMPOSITIONS.items()
            if source in spec.get("domains", [])
        ]
        return {
            "domain_name": source,
            "collaborating_domains": collaborators,
            "shared_capabilities": shared,
            "private_capabilities": private,
            "dependency_relationships": required_domains,
            "optional_relationships": optional_domains,
            "capability_composition_status": self._composition_maturity(compositions),
            "operational_capability_composition": compositions,
            "missing_collaborative_capabilities": _dedupe(missing_collab),
            "collaboration_maturity": self._maturity(collaborators),
            "capability_sharing_maturity": self._maturity(shared),
            "dependency_maturity": self._maturity(required_domains),
            "operational_composition_maturity": self._composition_maturity(compositions),
        }

    def _interaction(
        self,
        source: str,
        target: str,
        interaction_type: str,
        *,
        shared_capabilities: list[str] | None = None,
        required_capabilities: list[str] | None = None,
        optional_capabilities: list[str] | None = None,
        domain_names: set[str],
    ) -> dict[str, Any]:
        required_capabilities = required_capabilities or []
        optional_capabilities = optional_capabilities or []
        target_exists = target in domain_names
        status = "READY" if target_exists and (required_capabilities or optional_capabilities or interaction_type != "DEPENDENCY") else "BLOCKED"
        return DomainInteraction(
            source_domain=source,
            target_domain=target,
            interaction_type=interaction_type,
            shared_capabilities=_dedupe(shared_capabilities or []),
            required_capabilities=_dedupe(required_capabilities),
            optional_capabilities=_dedupe(optional_capabilities),
            operational_constraints=[] if target_exists else ["target_domain_missing"],
            interaction_status=status,
        ).as_dict()

    def _domain_capabilities(self, row: Mapping[str, Any]) -> list[str]:
        return _dedupe([
            *_as_list(row.get("semantic_capability_evolution")),
            *_as_list(row.get("operational_capability_evolution")),
            *DOMAIN_SHARED_CAPABILITIES.get(str(row.get("domain_name") or ""), []),
        ])

    def _collaboration_targets(self, source: str, domain_names: set[str]) -> list[str]:
        suggestions = {
            "Physics Domain": ["Topology Domain"],
            "Topology Domain": ["Geometry Domain"],
            "Pattern Completion Domain": ["Transformation Domain", "Color Domain"],
            "Transformation Domain": ["Spatial Domain", "Color Domain"],
        }.get(source, [])
        return [target for target in suggestions if target in domain_names]

    def _composition_status(
        self,
        name: str,
        spec: Mapping[str, Any],
        capabilities: Mapping[str, list[str]],
        domain_names: set[str],
    ) -> dict[str, Any]:
        required_domains = _dedupe(_as_list(spec.get("domains")))
        required_capabilities = _dedupe(_as_list(spec.get("required_capabilities")))
        available = set()
        missing_domains = [domain for domain in required_domains if domain not in domain_names]
        for domain in required_domains:
            available.update(capabilities.get(domain, []))
        missing_capabilities = [
            capability
            for capability in required_capabilities
            if capability not in available
        ]
        return {
            "composition_name": name,
            "participating_domains": required_domains,
            "required_capabilities": required_capabilities,
            "missing_domains": missing_domains,
            "missing_capabilities": missing_capabilities,
            "composition_status": "READY" if not missing_domains and not missing_capabilities else "BLOCKED",
        }

    def _dependency_graph(self, domain_reports: list[dict[str, Any]]) -> dict[str, list[str]]:
        return {
            row["domain_name"]: row.get("dependency_relationships", [])
            for row in domain_reports
        }

    def _maturity(self, values: list[str]) -> str:
        if not values:
            return "FOUNDATIONAL"
        if len(values) == 1:
            return "PARTIAL"
        if len(values) == 2:
            return "DEVELOPING"
        return "OPERATIONAL"

    def _composition_maturity(self, compositions: list[str]) -> str:
        if not compositions:
            return "FOUNDATIONAL"
        if len(compositions) == 1:
            return "DEVELOPING"
        return "ADVANCED"

    def _validate(
        self,
        interactions: list[dict[str, Any]],
        compositions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        invalid_interactions = [
            interaction for interaction in interactions
            if interaction.get("interaction_status") == "BLOCKED"
        ]
        invalid_compositions = [
            composition for composition in compositions
            if composition.get("composition_status") == "BLOCKED"
        ]
        graph = {
            str(interaction.get("source_domain")): str(interaction.get("target_domain"))
            for interaction in interactions
            if interaction.get("interaction_type") == "DEPENDENCY"
        }
        circular = [
            {"source_domain": source, "target_domain": target}
            for source, target in graph.items()
            if graph.get(target) == source
        ]
        return {
            "invalid_domain_interactions": invalid_interactions,
            "circular_dependencies": circular,
            "invalid_capability_composition": invalid_compositions,
            "prohibited_capability_sharing": [],
            "missing_shared_capabilities": [
                composition for composition in invalid_compositions
                if composition.get("missing_capabilities")
            ],
            "invalid_operational_constraints": [
                interaction for interaction in interactions
                if interaction.get("operational_constraints")
            ],
            "validation_success": not invalid_interactions and not invalid_compositions and not circular,
        }


class CognitiveDomainGovernanceRegistry:
    """Govern domain ownership, boundaries, conflicts, and evolution integrity."""

    system_name = "cognitive_domain_governance_registry"

    def build(
        self,
        cognitive_domain_lifecycle_report: Mapping[str, Any] | None = None,
        cognitive_domain_interaction_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        lifecycle = cognitive_domain_lifecycle_report if isinstance(cognitive_domain_lifecycle_report, Mapping) else {}
        interaction = cognitive_domain_interaction_report if isinstance(cognitive_domain_interaction_report, Mapping) else {}
        registry = lifecycle.get("domain_registry", [])
        registry = registry if isinstance(registry, list) else []
        domain_rows = [row for row in registry if isinstance(row, Mapping)]
        shared = self._shared_capability_map(interaction)
        ownership = self._ownership_map(domain_rows)
        duplicate_conflicts = self._duplicate_ownership_conflicts(ownership, shared)
        governance = [
            self._govern_domain(row, ownership, duplicate_conflicts, shared)
            for row in domain_rows
        ]
        validation = self._validate(governance)
        return {
            "system": self.system_name,
            "COGNITIVE_DOMAIN_GOVERNANCE_REPORT": True,
            "domain_governance_count": len(governance),
            "domain_governance": [item.as_dict() for item in governance],
            "capability_ownership_map": {
                capability: owners
                for capability, owners in ownership.items()
            },
            "capability_conflicts": validation["capability_conflicts"],
            "migration_history": CAPABILITY_MIGRATION_HISTORY,
            "validation": validation,
            "validation_success": validation["validation_success"],
            "silent_domain_governance_failures": False,
        }

    def _govern_domain(
        self,
        row: Mapping[str, Any],
        ownership: Mapping[str, list[str]],
        duplicate_conflicts: list[dict[str, Any]],
        shared: Mapping[str, list[str]],
    ) -> CognitiveDomainGovernance:
        domain = str(row.get("domain_name") or "Unknown Domain")
        capabilities = _dedupe([
            *_as_list(row.get("semantic_capability_evolution")),
            *_as_list(row.get("operational_capability_evolution")),
        ])
        boundaries = DOMAIN_SEMANTIC_BOUNDARIES.get(domain, {})
        boundary_violations = self._boundary_violations(domain, capabilities, boundaries)
        ownership_conflicts = self._ownership_conflicts(domain, capabilities, ownership, duplicate_conflicts, shared)
        maturity_conflicts = self._maturity_conflicts(row)
        dependency_conflicts = self._dependency_conflicts(row)
        missing_requirements = []
        if not boundaries:
            missing_requirements.append("semantic_boundary_policy")
        if domain not in DOMAIN_DEPENDENCIES and _as_list(row.get("required_domains")):
            missing_requirements.append("dependency_governance_policy")
        status = self._status(
            ownership_conflicts,
            boundary_violations,
            maturity_conflicts,
            dependency_conflicts,
            missing_requirements,
        )
        semantic_score = self._score(len(boundary_violations), len(capabilities))
        ownership_score = self._score(len(ownership_conflicts), len(capabilities))
        maturity_score = self._score(len(maturity_conflicts), 1)
        dependency_score = self._score(len(dependency_conflicts), max(1, len(_as_list(row.get("required_domains")))))
        integrity = round((semantic_score + ownership_score + maturity_score + dependency_score) / 4.0, 4)
        return CognitiveDomainGovernance(
            domain_name=domain,
            ownership_rules={
                "canonical_owner_required": True,
                "shared_capabilities_must_be_declared": True,
                "capabilities": capabilities,
            },
            semantic_boundaries=boundaries,
            allowed_capabilities=_dedupe(boundaries.get("allowed_capability_tokens", [])),
            forbidden_capabilities=_dedupe(boundaries.get("forbidden_capability_tokens", [])),
            maturity_constraints={
                "allowed_sequence": [
                    "FOUNDATIONAL",
                    "EARLY_DEVELOPMENT",
                    "DEVELOPING",
                    "PARTIALLY_OPERATIONAL",
                    "OPERATIONAL",
                    "ADVANCED",
                    "FULLY_OPERATIONAL",
                ],
                "current_maturity": row.get("maturity_level"),
            },
            dependency_constraints={
                "required_domains": _as_list(row.get("required_domains")),
                "optional_domains": _as_list(row.get("optional_domains")),
            },
            capability_admission_rules={
                "semantic_boundary_check_required": True,
                "canonical_owner_check_required": True,
                "shared_capability_exception_allowed": True,
            },
            capability_conflicts=ownership_conflicts + maturity_conflicts + dependency_conflicts,
            migration_history=[
                event for event in CAPABILITY_MIGRATION_HISTORY
                if event["previous_owner"] == domain or event["new_owner"] == domain
            ],
            boundary_violations=boundary_violations,
            missing_governance_requirements=missing_requirements,
            semantic_coherence_score=semantic_score,
            ownership_consistency_score=ownership_score,
            maturity_consistency_score=maturity_score,
            dependency_consistency_score=dependency_score,
            governance_integrity_score=integrity,
            governance_status=status,
        )

    def _ownership_map(self, rows: list[Mapping[str, Any]]) -> dict[str, list[str]]:
        owners: dict[str, list[str]] = {}
        for row in rows:
            domain = str(row.get("domain_name") or "Unknown Domain")
            for capability in _dedupe([
                *_as_list(row.get("semantic_capability_evolution")),
                *_as_list(row.get("operational_capability_evolution")),
            ]):
                owners.setdefault(capability, [])
                _append(owners[capability], domain)
        return owners

    def _shared_capability_map(self, interaction: Mapping[str, Any]) -> dict[str, list[str]]:
        shared: dict[str, list[str]] = {}
        reports = interaction.get("domain_interaction_reports", [])
        reports = reports if isinstance(reports, list) else []
        for row in reports:
            if not isinstance(row, Mapping):
                continue
            domain = str(row.get("domain_name") or "Unknown Domain")
            for capability in _as_list(row.get("shared_capabilities")):
                shared.setdefault(capability, [])
                _append(shared[capability], domain)
        return shared

    def _duplicate_ownership_conflicts(
        self,
        ownership: Mapping[str, list[str]],
        shared: Mapping[str, list[str]],
    ) -> list[dict[str, Any]]:
        conflicts = []
        for capability, owners in ownership.items():
            if len(owners) <= 1:
                continue
            shared_owners = set(shared.get(capability, []))
            if not set(owners).issubset(shared_owners):
                conflicts.append({
                    "conflict_type": "duplicate_ownership",
                    "capability": capability,
                    "owners": owners,
                    "reason": "CAPABILITY_HAS_MULTIPLE_CANONICAL_OWNERS_WITHOUT_SHARED_INTERACTION",
                })
        return conflicts

    def _ownership_conflicts(
        self,
        domain: str,
        capabilities: list[str],
        ownership: Mapping[str, list[str]],
        duplicate_conflicts: list[dict[str, Any]],
        shared: Mapping[str, list[str]],
    ) -> list[dict[str, Any]]:
        conflicts = []
        for capability in capabilities:
            canonical = CAPABILITY_CANONICAL_OWNER.get(capability)
            if canonical and canonical != domain and domain not in shared.get(capability, []):
                conflicts.append({
                    "conflict_type": "invalid_ownership",
                    "capability": capability,
                    "expected_owner": canonical,
                    "actual_owner": domain,
                    "reason": "CANONICAL_OWNER_MISMATCH",
                })
            for duplicate in duplicate_conflicts:
                if duplicate["capability"] == capability and domain in duplicate["owners"]:
                    conflicts.append(duplicate)
        return conflicts

    def _boundary_violations(
        self,
        domain: str,
        capabilities: list[str],
        boundaries: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        violations = []
        forbidden = _as_list(boundaries.get("forbidden_capability_tokens"))
        allowed = _as_list(boundaries.get("allowed_capability_tokens"))
        for capability in capabilities:
            if any(token in capability for token in forbidden):
                violations.append({
                    "violation_type": "forbidden_capability",
                    "domain": domain,
                    "capability": capability,
                    "reason": "FORBIDDEN_CAPABILITY_TOKEN",
                })
            if allowed and not any(token in capability for token in allowed):
                violations.append({
                    "violation_type": "capability_outside_boundary",
                    "domain": domain,
                    "capability": capability,
                    "reason": "CAPABILITY_NOT_ALLOWED_BY_DOMAIN_BOUNDARY",
                })
        return violations

    def _maturity_conflicts(self, row: Mapping[str, Any]) -> list[dict[str, Any]]:
        maturity = str(row.get("maturity_level") or "FOUNDATIONAL")
        stage = str(row.get("lifecycle_stage") or "DISCOVERED")
        if maturity == "FULLY_OPERATIONAL" and stage not in {"FULLY_OPERATIONAL", "ADVANCED"}:
            return [{
                "conflict_type": "maturity_conflict",
                "domain": row.get("domain_name"),
                "reason": "FULLY_OPERATIONAL_MATURITY_WITHOUT_FINAL_LIFECYCLE_STAGE",
            }]
        return []

    def _dependency_conflicts(self, row: Mapping[str, Any]) -> list[dict[str, Any]]:
        domain = str(row.get("domain_name") or "Unknown Domain")
        expected = set(DOMAIN_DEPENDENCIES.get(domain, {}).get("required_domains", []))
        actual = set(_as_list(row.get("required_domains")))
        missing = sorted(expected - actual) if actual else []
        return [
            {
                "conflict_type": "dependency_conflict",
                "domain": domain,
                "missing_dependency": dependency,
                "reason": "EXPECTED_DEPENDENCY_NOT_DECLARED",
            }
            for dependency in missing
        ]

    def _status(
        self,
        ownership_conflicts: list[dict[str, Any]],
        boundary_violations: list[dict[str, Any]],
        maturity_conflicts: list[dict[str, Any]],
        dependency_conflicts: list[dict[str, Any]],
        missing_requirements: list[str],
    ) -> str:
        if boundary_violations:
            return "BOUNDARY_VIOLATION"
        if ownership_conflicts or dependency_conflicts:
            return "CONFLICT_DETECTED"
        if maturity_conflicts:
            return "UNDER_REVIEW"
        if missing_requirements:
            return "PARTIALLY_GOVERNED"
        return "FULLY_GOVERNED"

    def _score(self, failures: int, total: int) -> float:
        total = max(total, 1)
        return round(max(0.0, 1.0 - (failures / total)), 4)

    def _validate(self, governance: list[CognitiveDomainGovernance]) -> dict[str, Any]:
        conflicts = [
            conflict
            for domain in governance
            for conflict in domain.capability_conflicts
        ]
        boundaries = [
            violation
            for domain in governance
            for violation in domain.boundary_violations
        ]
        missing = [
            requirement
            for domain in governance
            for requirement in domain.missing_governance_requirements
        ]
        return {
            "capability_conflicts": conflicts,
            "boundary_violations": boundaries,
            "missing_governance_requirements": _dedupe(missing),
            "migration_events": CAPABILITY_MIGRATION_HISTORY,
            "validation_success": not conflicts and not boundaries,
        }


class CognitiveDomainEcosystemRegistry:
    """Aggregate domain architecture into a global cognitive ecosystem state."""

    system_name = "cognitive_domain_ecosystem_registry"

    def build(
        self,
        cognitive_domain_lifecycle_report: Mapping[str, Any] | None = None,
        cognitive_domain_interaction_report: Mapping[str, Any] | None = None,
        cognitive_domain_governance_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        lifecycle = cognitive_domain_lifecycle_report if isinstance(cognitive_domain_lifecycle_report, Mapping) else {}
        interaction = cognitive_domain_interaction_report if isinstance(cognitive_domain_interaction_report, Mapping) else {}
        governance = cognitive_domain_governance_report if isinstance(cognitive_domain_governance_report, Mapping) else {}
        rows = lifecycle.get("domain_registry", [])
        rows = rows if isinstance(rows, list) else []
        domain_rows = [row for row in rows if isinstance(row, Mapping)]
        interaction_reports = interaction.get("domain_interaction_reports", [])
        interaction_reports = interaction_reports if isinstance(interaction_reports, list) else []
        governance_rows = governance.get("domain_governance", [])
        governance_rows = governance_rows if isinstance(governance_rows, list) else []

        distribution = self._domain_distribution(domain_rows)
        totals = self._global_totals(domain_rows)
        covered, partial, missing = self._coverage_sets(domain_rows)
        health = self._health_metrics(domain_rows, interaction_reports, governance_rows, totals)
        dependency_graph = interaction.get("dependency_graph", {})
        dependency_graph = dependency_graph if isinstance(dependency_graph, dict) else {}
        collaboration_graph = self._collaboration_graph(interaction_reports)
        operational_graph = self._operational_capability_graph(interaction)
        bottlenecks = self._bottlenecks(domain_rows)
        imbalances = self._imbalances(domain_rows)
        ecosystem = CognitiveDomainEcosystem(
            total_domains=totals["domains"],
            total_semantic_concepts=totals["semantic"],
            total_mental_models=totals["mental_models"],
            total_program_blueprints=totals["programs"],
            total_execution_packages=totals["execution_packages"],
            total_operational_capabilities=totals["operational"],
            total_candidate_ready_programs=totals["candidate_ready"],
            total_operational_domains=totals["operational_domains"],
            domain_distribution=distribution,
            capability_coverage=health["capability_coverage_score"],
            semantic_integrity_score=health["semantic_integrity_score"],
            governance_integrity_score=health["governance_integrity_score"],
            ecosystem_maturity_score=health["ecosystem_maturity_score"],
            capability_coverage_score=health["capability_coverage_score"],
            collaboration_score=health["collaboration_score"],
            operational_readiness_score=health["operational_readiness_score"],
            architectural_coherence_score=health["architectural_coherence_score"],
            covered_domains=covered,
            partially_covered_domains=partial,
            missing_domains=missing,
            dependency_graph=dependency_graph,
            collaboration_graph=collaboration_graph,
            operational_capability_graph=operational_graph,
            missing_ecosystem_capabilities=self._missing_capabilities(domain_rows, governance),
            cognitive_imbalances=imbalances,
            cognitive_bottlenecks=bottlenecks,
            ecosystem_maturity=self._ecosystem_maturity(health["ecosystem_maturity_score"]),
        )
        return {
            "system": self.system_name,
            "COGNITIVE_DOMAIN_ECOSYSTEM_REPORT": True,
            "ecosystem": ecosystem.as_dict(),
            "global_cognitive_coverage": {
                "domains": ecosystem.total_domains,
                "semantic_concepts": ecosystem.total_semantic_concepts,
                "mental_models": ecosystem.total_mental_models,
                "program_blueprints": ecosystem.total_program_blueprints,
                "execution_packages": ecosystem.total_execution_packages,
                "operational_capabilities": ecosystem.total_operational_capabilities,
                "candidate_ready_programs": ecosystem.total_candidate_ready_programs,
                "operational_domains": ecosystem.total_operational_domains,
            },
            "domain_distribution": distribution,
            "ecosystem_health_metrics": health,
            "dependency_graph": dependency_graph,
            "collaboration_graph": collaboration_graph,
            "operational_capability_graph": operational_graph,
            "missing_ecosystem_capabilities": ecosystem.missing_ecosystem_capabilities,
            "cognitive_imbalances": imbalances,
            "cognitive_bottlenecks": bottlenecks,
            "ecosystem_maturity": ecosystem.ecosystem_maturity,
            "silent_ecosystem_failures": False,
        }

    def _global_totals(self, rows: list[Mapping[str, Any]]) -> dict[str, int]:
        return {
            "domains": len(rows),
            "semantic": sum(len(_as_list(row.get("semantic_capability_evolution"))) for row in rows),
            "mental_models": sum(len(_as_list(row.get("mental_model_evolution"))) for row in rows),
            "programs": sum(len(_as_list(row.get("program_blueprint_evolution"))) for row in rows),
            "execution_packages": sum(len(_as_list(row.get("execution_capability_evolution"))) for row in rows),
            "operational": sum(len(_as_list(row.get("operational_capability_evolution"))) for row in rows),
            "candidate_ready": sum(1 for row in rows if row.get("candidate_readiness") == "READY"),
            "operational_domains": sum(1 for row in rows if row.get("operational_readiness") == "READY"),
        }

    def _domain_distribution(self, rows: list[Mapping[str, Any]]) -> dict[str, int]:
        distribution = {
            "FOUNDATIONAL": 0,
            "DEVELOPING": 0,
            "PARTIALLY_OPERATIONAL": 0,
            "OPERATIONAL": 0,
            "ADVANCED": 0,
            "FULLY_OPERATIONAL": 0,
        }
        for row in rows:
            maturity = str(row.get("maturity_level") or "FOUNDATIONAL")
            if maturity == "EARLY_DEVELOPMENT":
                maturity = "DEVELOPING"
            distribution[maturity] = distribution.get(maturity, 0) + 1
        return distribution

    def _coverage_sets(self, rows: list[Mapping[str, Any]]) -> tuple[list[str], list[str], list[str]]:
        present = {str(row.get("domain_name")) for row in rows if row.get("domain_name")}
        covered = []
        partial = []
        for row in rows:
            name = str(row.get("domain_name") or "")
            if row.get("operational_readiness") == "READY" or row.get("execution_readiness") == "READY":
                covered.append(name)
            elif _as_list(row.get("semantic_capability_evolution")) or _as_list(row.get("program_blueprint_evolution")):
                partial.append(name)
        foundational_names = set(FOUNDATIONAL_DOMAINS.values())
        missing = sorted(foundational_names - present)
        return _dedupe(covered), _dedupe(partial), missing

    def _health_metrics(
        self,
        rows: list[Mapping[str, Any]],
        interaction_reports: list[Any],
        governance_rows: list[Any],
        totals: Mapping[str, int],
    ) -> dict[str, float]:
        domain_count = max(totals["domains"], 1)
        semantic_scores = [
            float(row.get("semantic_coherence_score", 1.0))
            for row in governance_rows
            if isinstance(row, Mapping)
        ]
        governance_scores = [
            float(row.get("governance_integrity_score", 1.0))
            for row in governance_rows
            if isinstance(row, Mapping)
        ]
        maturity_score = self._maturity_score(rows)
        capability_score = round(
            min(1.0, (totals["programs"] + totals["execution_packages"] + totals["operational"]) / max(totals["semantic"], 1)),
            4,
        )
        collaboration_score = round(
            min(1.0, sum(len(_as_list(row.get("collaborating_domains"))) for row in interaction_reports if isinstance(row, Mapping)) / domain_count),
            4,
        )
        operational_score = round(totals["operational_domains"] / domain_count, 4)
        semantic_integrity = self._average(semantic_scores)
        governance_integrity = self._average(governance_scores)
        coherence = round((semantic_integrity + governance_integrity + collaboration_score + capability_score) / 4.0, 4)
        return {
            "semantic_integrity_score": semantic_integrity,
            "governance_integrity_score": governance_integrity,
            "ecosystem_maturity_score": maturity_score,
            "capability_coverage_score": capability_score,
            "collaboration_score": collaboration_score,
            "operational_readiness_score": operational_score,
            "architectural_coherence_score": coherence,
        }

    def _maturity_score(self, rows: list[Mapping[str, Any]]) -> float:
        weights = {
            "FOUNDATIONAL": 0.15,
            "EARLY_DEVELOPMENT": 0.25,
            "DEVELOPING": 0.4,
            "PARTIALLY_OPERATIONAL": 0.6,
            "OPERATIONAL": 0.75,
            "ADVANCED": 0.9,
            "FULLY_OPERATIONAL": 1.0,
        }
        if not rows:
            return 0.0
        return round(sum(weights.get(str(row.get("maturity_level") or "FOUNDATIONAL"), 0.15) for row in rows) / len(rows), 4)

    def _collaboration_graph(self, reports: list[Any]) -> dict[str, list[str]]:
        return {
            str(row.get("domain_name")): _as_list(row.get("collaborating_domains"))
            for row in reports
            if isinstance(row, Mapping) and row.get("domain_name")
        }

    def _operational_capability_graph(self, interaction: Mapping[str, Any]) -> dict[str, list[str]]:
        compositions = interaction.get("operational_capability_compositions", [])
        compositions = compositions if isinstance(compositions, list) else []
        return {
            str(row.get("composition_name")): _as_list(row.get("participating_domains"))
            for row in compositions
            if isinstance(row, Mapping) and row.get("composition_name")
        }

    def _missing_capabilities(self, rows: list[Mapping[str, Any]], governance: Mapping[str, Any]) -> list[str]:
        missing = []
        for row in rows:
            missing.extend(_as_list(row.get("missing_capabilities")))
        missing.extend(_as_list(governance.get("missing_governance_requirements")))
        return _dedupe(missing)

    def _imbalances(self, rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
        imbalances = []
        for row in rows:
            semantic_count = len(_as_list(row.get("semantic_capability_evolution")))
            operational_count = len(_as_list(row.get("operational_capability_evolution")))
            if semantic_count >= 6 and operational_count <= 1:
                imbalances.append({
                    "domain": row.get("domain_name"),
                    "imbalance_type": "capability_concentration",
                    "semantic_capabilities": semantic_count,
                    "operational_capabilities": operational_count,
                })
            if semantic_count > 0 and operational_count == 0 and row.get("maturity_level") in {"PARTIALLY_OPERATIONAL", "OPERATIONAL", "ADVANCED"}:
                imbalances.append({
                    "domain": row.get("domain_name"),
                    "imbalance_type": "operational_maturity_issue",
                    "semantic_capabilities": semantic_count,
                    "operational_capabilities": operational_count,
                })
        return imbalances

    def _bottlenecks(self, rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
        bottlenecks = []
        for row in rows:
            missing = _as_list(row.get("missing_capabilities"))
            if any("candidate" in item for item in missing):
                bottlenecks.append({
                    "domain": row.get("domain_name"),
                    "bottleneck_type": "candidate_proposal_support",
                    "missing_capabilities": missing,
                })
            if any("execution" in item or "package" in item for item in missing):
                bottlenecks.append({
                    "domain": row.get("domain_name"),
                    "bottleneck_type": "execution_package_coverage",
                    "missing_capabilities": missing,
                })
            if row.get("program_readiness") == "READY" and row.get("execution_readiness") != "READY":
                bottlenecks.append({
                    "domain": row.get("domain_name"),
                    "bottleneck_type": "program_to_execution_gap",
                    "missing_capabilities": missing,
                })
        return bottlenecks

    def _ecosystem_maturity(self, score: float) -> str:
        if score >= 0.95:
            return "FULLY_OPERATIONAL"
        if score >= 0.85:
            return "ADVANCED"
        if score >= 0.7:
            return "OPERATIONAL"
        if score >= 0.5:
            return "PARTIALLY_OPERATIONAL"
        if score >= 0.3:
            return "DEVELOPING"
        return "FOUNDATIONAL"

    def _average(self, values: list[float]) -> float:
        if not values:
            return 1.0
        return round(sum(values) / len(values), 4)


class CognitiveDomainConstitutionRegistry:
    """Audit constitutional invariants across the cognitive domain ecosystem."""

    system_name = "cognitive_domain_constitution_registry"

    def build(
        self,
        cognitive_domain_lifecycle_report: Mapping[str, Any] | None = None,
        cognitive_domain_interaction_report: Mapping[str, Any] | None = None,
        cognitive_domain_governance_report: Mapping[str, Any] | None = None,
        cognitive_domain_ecosystem_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        lifecycle = cognitive_domain_lifecycle_report if isinstance(cognitive_domain_lifecycle_report, Mapping) else {}
        interaction = cognitive_domain_interaction_report if isinstance(cognitive_domain_interaction_report, Mapping) else {}
        governance = cognitive_domain_governance_report if isinstance(cognitive_domain_governance_report, Mapping) else {}
        ecosystem = cognitive_domain_ecosystem_report if isinstance(cognitive_domain_ecosystem_report, Mapping) else {}
        lifecycle_rows = [
            row for row in lifecycle.get("domain_registry", [])
            if isinstance(row, Mapping)
        ]
        interaction_rows = [
            row for row in interaction.get("domain_interaction_reports", [])
            if isinstance(row, Mapping)
        ]
        governance_rows = [
            row for row in governance.get("domain_governance", [])
            if isinstance(row, Mapping)
        ]
        ecosystem_payload = ecosystem.get("ecosystem", {})
        ecosystem_payload = ecosystem_payload if isinstance(ecosystem_payload, Mapping) else {}

        violations = []
        violations.extend(self._ownership_violations(lifecycle_rows, governance_rows, interaction_rows))
        violations.extend(self._program_blueprint_violations(lifecycle_rows))
        violations.extend(self._mental_model_violations(lifecycle_rows))
        violations.extend(self._state_visibility_violations(lifecycle_rows, governance_rows))
        violations.extend(self._dependency_violations(lifecycle_rows))
        violations.extend(self._governance_violations(governance_rows, governance))
        violations.extend(self._collaboration_violations(interaction_rows, interaction))
        violations.extend(self._ecosystem_violations(ecosystem, ecosystem_payload))
        violations.extend(self._silent_failure_violations(lifecycle, interaction, governance, ecosystem))

        domain_health = self._domain_health(lifecycle_rows, governance_rows, violations)
        validations = self._validations(violations)
        metrics = self._metrics(
            validations,
            governance_rows,
            interaction_rows,
            ecosystem,
            ecosystem_payload,
            domain_health,
        )
        constitution = CognitiveDomainConstitution(
            constitutional_principles=CONSTITUTIONAL_PRINCIPLES,
            architectural_invariants=ARCHITECTURAL_INVARIANTS,
            constitutional_validations=validations,
            constitutional_violations=violations,
            domain_constitutional_health=domain_health,
            domain_rights=DOMAIN_CONSTITUTIONAL_RIGHTS,
            domain_responsibilities=DOMAIN_CONSTITUTIONAL_RESPONSIBILITIES,
            constitutional_status=self._constitutional_status(metrics["constitutional_compliance_score"], violations),
            constitutional_integrity_score=metrics["constitutional_integrity_score"],
            architectural_integrity_score=metrics["architectural_integrity_score"],
            semantic_integrity_score=metrics["semantic_integrity_score"],
            governance_integrity_score=metrics["governance_integrity_score"],
            collaboration_integrity_score=metrics["collaboration_integrity_score"],
            ecosystem_coherence_score=metrics["ecosystem_coherence_score"],
            constitutional_compliance_score=metrics["constitutional_compliance_score"],
            silent_constitutional_failures=False,
        )
        return {
            "system": self.system_name,
            "COGNITIVE_DOMAIN_CONSTITUTION_REPORT": True,
            "constitution": constitution.as_dict(),
            "constitutional_principles": constitution.constitutional_principles,
            "architectural_invariants": constitution.architectural_invariants,
            "constitutional_validations": validations,
            "constitutional_violations": violations,
            "constitutional_status": constitution.constitutional_status,
            "constitutional_health_metrics": metrics,
            "domain_constitutional_health": domain_health,
            "domain_rights": constitution.domain_rights,
            "domain_responsibilities": constitution.domain_responsibilities,
            "governance_compliance": validations["governance_integrity"],
            "ownership_compliance": validations["ownership_integrity"],
            "lifecycle_compliance": validations["lifecycle_integrity"],
            "silent_constitutional_failures": False,
        }

    def _ownership_violations(
        self,
        lifecycle_rows: list[Mapping[str, Any]],
        governance_rows: list[Mapping[str, Any]],
        interaction_rows: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        capability_owners: dict[str, list[str]] = {}
        for row in lifecycle_rows:
            domain = str(row.get("domain_name") or "")
            for capability in _as_list(row.get("semantic_capability_evolution")):
                capability_owners.setdefault(capability, []).append(domain)
        shared = {
            capability
            for row in interaction_rows
            for capability in _as_list(row.get("shared_capabilities"))
        }
        violations = []
        for capability, owners in capability_owners.items():
            unique = _dedupe(owners)
            if not unique:
                violations.append(self._violation("MISSING_CANONICAL_OWNER", None, capability, "capability_exists_without_domain_owner"))
            if len(unique) > 1 and capability not in shared:
                violations.append(self._violation("OWNERSHIP_CONFLICT", unique[0], capability, "concept_owned_by_multiple_domains_without_explicit_sharing", owners=unique))
        for row in governance_rows:
            for conflict in row.get("capability_conflicts", []) or []:
                if isinstance(conflict, Mapping):
                    violation_type = "MISSING_CANONICAL_OWNER" if not conflict.get("expected_owner") else "OWNERSHIP_CONFLICT"
                    violations.append(self._violation(violation_type, row.get("domain_name"), conflict.get("capability"), conflict.get("reason", "governance_reported_ownership_conflict"), details=dict(conflict)))
        return violations

    def _program_blueprint_violations(self, lifecycle_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
        owners: dict[str, list[str]] = {}
        for row in lifecycle_rows:
            for program in _as_list(row.get("program_blueprint_evolution")):
                owners.setdefault(program, []).append(str(row.get("domain_name") or "Unknown Domain"))
        return [
            self._violation("PROGRAM_BLUEPRINT_OWNERSHIP_CONFLICT", domains[0], program, "program_blueprint_owned_by_multiple_domains", owners=_dedupe(domains))
            for program, domains in owners.items()
            if len(_dedupe(domains)) > 1
        ]

    def _mental_model_violations(self, lifecycle_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
        return [
            self._violation("MENTAL_MODEL_DOMAIN_MISSING", row.get("domain_name"), None, "domain_has_concepts_or_programs_without_mental_model")
            for row in lifecycle_rows
            if (
                _as_list(row.get("semantic_capability_evolution"))
                or _as_list(row.get("program_blueprint_evolution"))
            )
            and not _as_list(row.get("mental_model_evolution"))
        ]

    def _state_visibility_violations(
        self,
        lifecycle_rows: list[Mapping[str, Any]],
        governance_rows: list[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        governance_domains = {str(row.get("domain_name")) for row in governance_rows if row.get("domain_name")}
        violations = []
        for row in lifecycle_rows:
            domain = str(row.get("domain_name") or "Unknown Domain")
            if not row.get("lifecycle_stage") and not row.get("maturity_level"):
                violations.append(self._violation("LIFECYCLE_STATE_MISSING", domain, None, "domain_lifecycle_state_not_exposed"))
            if domain not in governance_domains:
                violations.append(self._violation("GOVERNANCE_STATE_MISSING", domain, None, "domain_governance_state_not_exposed"))
        return violations

    def _dependency_violations(self, lifecycle_rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
        violations = []
        for row in lifecycle_rows:
            domain = str(row.get("domain_name") or "Unknown Domain")
            if _as_list(row.get("operational_capability_evolution")) and domain in DOMAIN_DEPENDENCIES:
                expected = set(DOMAIN_DEPENDENCIES.get(domain, {}).get("required_domains", []))
                actual = set(_as_list(row.get("required_domains")))
                for dependency in sorted(expected - actual):
                    violations.append(self._violation("MISSING_OPERATIONAL_DEPENDENCY", domain, dependency, "operational_capability_without_required_dependency"))
        return violations

    def _governance_violations(
        self,
        governance_rows: list[Mapping[str, Any]],
        governance: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        violations = []
        for row in governance_rows:
            for boundary in row.get("boundary_violations", []) or []:
                if isinstance(boundary, Mapping):
                    violations.append(self._violation("SEMANTIC_BOUNDARY_BREACH", row.get("domain_name"), boundary.get("capability"), boundary.get("reason", "semantic_boundary_breach"), details=dict(boundary)))
            for migration in row.get("migration_history", []) or []:
                if isinstance(migration, Mapping) and not migration.get("migration_reason"):
                    violations.append(self._violation("UNAUTHORIZED_CAPABILITY_MIGRATION", row.get("domain_name"), migration.get("capability"), "capability_migration_without_governance_reason", details=dict(migration)))
        for requirement in _as_list(governance.get("missing_governance_requirements")):
            violations.append(self._violation("GOVERNANCE_REQUIREMENT_MISSING", None, requirement, "required_governance_capability_missing"))
        return violations

    def _collaboration_violations(
        self,
        interaction_rows: list[Mapping[str, Any]],
        interaction: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        violations = []
        if interaction.get("silent_domain_interaction_failures"):
            violations.append(self._violation("SILENT_COLLABORATION_FAILURE", None, None, "domain_interaction_report_declared_silent_failure"))
        for row in interaction_rows:
            if _as_list(row.get("required_capabilities")) and not _as_list(row.get("collaborating_domains")):
                violations.append(self._violation("COLLABORATION_NOT_EXPLICIT", row.get("domain_name"), None, "required_cross_domain_capability_without_collaborating_domain"))
        return violations

    def _ecosystem_violations(
        self,
        ecosystem: Mapping[str, Any],
        ecosystem_payload: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        violations = []
        for bottleneck in ecosystem.get("cognitive_bottlenecks", []) or []:
            if isinstance(bottleneck, Mapping):
                violations.append(self._violation("ECOSYSTEM_BOTTLENECK_OBSERVED", bottleneck.get("domain"), bottleneck.get("bottleneck_type"), "ecosystem_bottleneck_requires_governance_visibility", details=dict(bottleneck)))
        for imbalance in ecosystem.get("cognitive_imbalances", []) or []:
            if isinstance(imbalance, Mapping):
                violations.append(self._violation("ECOSYSTEM_IMBALANCE_OBSERVED", imbalance.get("domain"), imbalance.get("imbalance_type"), "ecosystem_imbalance_requires_governance_visibility", details=dict(imbalance)))
        if ecosystem_payload.get("architectural_coherence_score", 1.0) < 0.5:
            violations.append(self._violation("ARCHITECTURAL_COHERENCE_LOW", None, None, "ecosystem_coherence_below_constitutional_threshold"))
        return violations

    def _silent_failure_violations(self, *reports: Mapping[str, Any]) -> list[dict[str, Any]]:
        violations = []
        for report in reports:
            for key, value in report.items():
                if key.startswith("silent_") and value:
                    violations.append(self._violation("SILENT_FAILURE_DECLARED", None, key, "silent_failure_flag_true"))
        return violations

    def _domain_health(
        self,
        lifecycle_rows: list[Mapping[str, Any]],
        governance_rows: list[Mapping[str, Any]],
        violations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        governance_by_domain = {
            str(row.get("domain_name")): row
            for row in governance_rows
            if row.get("domain_name")
        }
        health = []
        for row in lifecycle_rows:
            domain = str(row.get("domain_name") or "Unknown Domain")
            domain_violations = [violation for violation in violations if violation.get("domain") == domain]
            governance = governance_by_domain.get(domain, {})
            base = float(governance.get("governance_integrity_score", 1.0)) if isinstance(governance, Mapping) else 1.0
            score = round(max(0.0, base - (0.1 * len(domain_violations))), 4)
            health.append({
                "domain_name": domain,
                "constitutional_status": "VALID" if not domain_violations else "VIOLATION_DETECTED",
                "constitutional_health_score": score,
                "violation_count": len(domain_violations),
                "rights": DOMAIN_CONSTITUTIONAL_RIGHTS,
                "responsibilities": DOMAIN_CONSTITUTIONAL_RESPONSIBILITIES,
            })
        return health

    def _validations(self, violations: list[dict[str, Any]]) -> dict[str, bool]:
        types = {str(violation.get("violation_type")) for violation in violations}
        return {
            "semantic_integrity": "SEMANTIC_BOUNDARY_BREACH" not in types,
            "ownership_integrity": not ({"OWNERSHIP_CONFLICT", "MISSING_CANONICAL_OWNER", "PROGRAM_BLUEPRINT_OWNERSHIP_CONFLICT"} & types),
            "lifecycle_integrity": "LIFECYCLE_STATE_MISSING" not in types,
            "governance_integrity": not ({"GOVERNANCE_STATE_MISSING", "GOVERNANCE_REQUIREMENT_MISSING", "UNAUTHORIZED_CAPABILITY_MIGRATION"} & types),
            "collaboration_integrity": not ({"COLLABORATION_NOT_EXPLICIT", "SILENT_COLLABORATION_FAILURE"} & types),
            "dependency_integrity": "MISSING_OPERATIONAL_DEPENDENCY" not in types,
            "architectural_coherence": not ({"ARCHITECTURAL_COHERENCE_LOW", "ECOSYSTEM_IMBALANCE_OBSERVED"} & types),
            "capability_transparency": "SILENT_FAILURE_DECLARED" not in types,
            "constitutional_compliance": not violations,
        }

    def _metrics(
        self,
        validations: Mapping[str, bool],
        governance_rows: list[Mapping[str, Any]],
        interaction_rows: list[Mapping[str, Any]],
        ecosystem: Mapping[str, Any],
        ecosystem_payload: Mapping[str, Any],
        domain_health: list[Mapping[str, Any]],
    ) -> dict[str, float]:
        compliance = self._boolean_score(validations.values())
        semantic = self._average([float(row.get("semantic_coherence_score", 1.0)) for row in governance_rows])
        governance = self._average([float(row.get("governance_integrity_score", 1.0)) for row in governance_rows])
        collaboration = 1.0 if interaction_rows else 0.0
        health = ecosystem.get("ecosystem_health_metrics", {})
        health = health if isinstance(health, Mapping) else {}
        coherence = float(health.get("architectural_coherence_score", ecosystem_payload.get("architectural_coherence_score", 1.0)))
        domain_score = self._average([float(row.get("constitutional_health_score", 1.0)) for row in domain_health])
        architectural = round((coherence + domain_score + compliance) / 3.0, 4)
        constitutional = round((semantic + governance + collaboration + architectural + compliance) / 5.0, 4)
        return {
            "constitutional_integrity_score": constitutional,
            "architectural_integrity_score": architectural,
            "semantic_integrity_score": semantic,
            "governance_integrity_score": governance,
            "collaboration_integrity_score": collaboration,
            "ecosystem_coherence_score": coherence,
            "constitutional_compliance_score": compliance,
        }

    def _constitutional_status(self, score: float, violations: list[dict[str, Any]]) -> str:
        if not violations and score >= 0.98:
            return "FULLY_CONSTITUTIONAL"
        if not violations and score >= 0.9:
            return "CONSTITUTIONALLY_COMPLIANT"
        if score >= 0.85:
            return "ADVANCED"
        if score >= 0.65:
            return "VALID"
        if score >= 0.4:
            return "PARTIALLY_CONSTITUTIONAL"
        return "FOUNDATIONAL"

    def _boolean_score(self, values: Any) -> float:
        values = list(values)
        if not values:
            return 1.0
        return round(sum(1 for value in values if value) / len(values), 4)

    def _average(self, values: list[float]) -> float:
        if not values:
            return 1.0
        return round(sum(values) / len(values), 4)

    def _violation(
        self,
        violation_type: str,
        domain: Any,
        capability: Any,
        reason: Any,
        **extra: Any,
    ) -> dict[str, Any]:
        violation = {
            "violation_type": violation_type,
            "domain": domain,
            "capability": capability,
            "reason": reason,
        }
        violation.update(extra)
        return violation


def _rows(report: Mapping[str, Any] | None, key: str) -> list[Mapping[str, Any]]:
    report = report if isinstance(report, Mapping) else {}
    rows = report.get(key, [])
    return rows if isinstance(rows, list) else []


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item not in (None, "")]
    if value in (None, ""):
        return []
    return [str(value)]


def _append(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(str(item) for item in items if item))


cognitive_knowledge_domain_registry = CognitiveKnowledgeDomainRegistry()
cognitive_domain_intelligence_layer = CognitiveDomainIntelligenceLayer()
cognitive_domain_lifecycle_registry = CognitiveDomainLifecycleRegistry()
cognitive_domain_interaction_registry = CognitiveDomainInteractionRegistry()
cognitive_domain_governance_registry = CognitiveDomainGovernanceRegistry()
cognitive_domain_ecosystem_registry = CognitiveDomainEcosystemRegistry()
cognitive_domain_constitution_registry = CognitiveDomainConstitutionRegistry()

__all__ = [
    "CognitiveDomain",
    "CognitiveDomainConstitution",
    "CognitiveDomainConstitutionRegistry",
    "CognitiveDomainEcosystem",
    "CognitiveDomainEcosystemRegistry",
    "CognitiveDomainGovernance",
    "CognitiveDomainGovernanceRegistry",
    "CognitiveDomainIntelligence",
    "CognitiveDomainIntelligenceLayer",
    "CognitiveDomainInteractionRegistry",
    "CognitiveDomainLifecycle",
    "CognitiveDomainLifecycleRegistry",
    "CognitiveKnowledgeDomainRegistry",
    "DomainInteraction",
    "cognitive_domain_constitution_registry",
    "cognitive_domain_ecosystem_registry",
    "cognitive_domain_governance_registry",
    "cognitive_domain_intelligence_layer",
    "cognitive_domain_interaction_registry",
    "cognitive_domain_lifecycle_registry",
    "cognitive_knowledge_domain_registry",
]
