"""Operational capability descriptions for program blueprints."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


FAMILY_BY_PROGRAM_TYPE = {
    "gravity_program": "Physics",
    "physics_program": "Physics",
    "topology_program": "Topology",
    "component_merging_program": "Topology",
    "spatial_program": "Spatial",
    "rotation_program": "Transformation",
    "reflection_program": "Transformation",
    "geometry_program": "Transformation",
    "color_mapping_program": "Transformation",
    "growth_program": "Transformation",
    "transformation_program": "Transformation",
    "object_identity_program": "Identity",
    "path_program": "Pattern Completion",
    "noise_filtering_program": "Transformation",
}

MENTAL_MODEL_BY_FAMILY = {
    "Physics": "Gravity Simulation",
    "Topology": "Topology Reasoning",
    "Spatial": "Spatial Reasoning Mental Model",
    "Transformation": "Object Transformation Mental Model",
    "Identity": "Object Identity Mental Model",
    "Pattern Completion": "Pattern Completion Mental Model",
}

SUPPORTED_CONCEPTS_BY_FAMILY = {
    "Physics": [
        "gravity",
        "falling",
        "support",
        "collision",
        "rest_state",
        "downward_motion",
    ],
    "Topology": [
        "topology_preservation",
        "topology_change",
        "hole_removal",
        "bridge_creation",
        "connectivity_change",
        "component_connection",
        "component_splitting",
    ],
    "Spatial": [
        "relative_position",
        "object_relocation",
        "spatial_constraints",
        "directional_motion",
        "orientation_change",
        "spatial_relation",
    ],
    "Transformation": [
        "rotation",
        "reflection",
        "symbolic_remapping",
        "scaling",
        "color_mapping",
        "growth",
    ],
    "Identity": [
        "object_identity_preservation",
        "position_preservation",
    ],
    "Pattern Completion": [
        "path_finding",
        "path_construction",
        "route_completion",
        "hole_removal",
    ],
}

REQUIRED_PACKAGES_BY_FAMILY = {
    "Physics": [
        "gravity_execution_package",
        "gravity_candidate_support",
        "gravity_validation_support",
    ],
    "Topology": [
        "topology_execution_package",
        "topology_candidate_support",
    ],
    "Spatial": [
        "spatial_execution_package",
    ],
    "Transformation": [
        "transformation_execution_package",
        "transformation_candidate_support",
    ],
    "Identity": [
        "identity_execution_package",
        "identity_candidate_support",
    ],
    "Pattern Completion": [
        "path_execution_package",
        "path_candidate_support",
    ],
}


@dataclass
class ProgramBlueprintIntelligence:
    blueprint_id: str
    program_type: str
    semantic_family: str
    semantic_cluster: str
    mental_model: str
    supported_concepts: list[str] = field(default_factory=list)
    compiler_supported: str = "FALSE"
    execution_ready: str = "NOT_SUPPORTED"
    candidate_ready: str = "NOT_READY"
    validation_ready: str = "FALSE"
    execution_package_available: str = "FALSE"
    required_packages: list[str] = field(default_factory=list)
    capability_profile: dict[str, Any] = field(default_factory=dict)
    missing_requirements: list[str] = field(default_factory=list)
    capability_limitations: list[str] = field(default_factory=list)
    lifecycle_status: str = "BLUEPRINT_ONLY"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProgramBlueprintIntelligenceLayer:
    """Classify and enrich generated program blueprints with capabilities."""

    system_name = "program_blueprint_intelligence_layer"

    def analyze(
        self,
        program_generation_report: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        report = program_generation_report if isinstance(program_generation_report, Mapping) else {}
        blueprints = report.get("program_blueprints", [])
        blueprints = blueprints if isinstance(blueprints, list) else []
        grouped: dict[str, list[Mapping[str, Any]]] = {}
        for blueprint in blueprints:
            if not isinstance(blueprint, Mapping):
                continue
            program_type = str(blueprint.get("program_type") or "generic_program")
            grouped.setdefault(program_type, []).append(blueprint)

        intelligence = [
            self._intelligence(program_type, items).as_dict()
            for program_type, items in sorted(grouped.items())
        ]
        validation = self._validation(intelligence)
        readiness_counts: dict[str, int] = {}
        for item in intelligence:
            state = str(item.get("execution_ready") or "NOT_SUPPORTED")
            readiness_counts[state] = readiness_counts.get(state, 0) + 1
        return {
            "system": self.system_name,
            "PROGRAM_BLUEPRINT_INTELLIGENCE_REPORT": True,
            "program_intelligence_count": len(intelligence),
            "program_blueprint_intelligence": intelligence,
            "execution_readiness_counts": readiness_counts,
            "validation": validation,
            "capability_failures_silent": False,
        }

    def _intelligence(
        self,
        program_type: str,
        blueprints: list[Mapping[str, Any]],
    ) -> ProgramBlueprintIntelligence:
        family = self._semantic_family(program_type, blueprints)
        concepts = self._supported_concepts(family, blueprints)
        compiler_supported = "TRUE" if any(_truth(item.get("compiler_supported")) == "TRUE" for item in blueprints) else "FALSE"
        package_available = self._package_available(blueprints)
        execution_ready = self._execution_ready(blueprints, package_available)
        candidate_ready = self._candidate_ready(blueprints, execution_ready, compiler_supported)
        validation_ready = "TRUE" if execution_ready in {"EXECUTION_READY", "PARTIALLY_OPERATIONAL"} else "FALSE"
        required = self._required_packages(family, blueprints)
        missing = self._missing_requirements(blueprints, required, package_available, candidate_ready)
        limitations = self._capability_limitations(compiler_supported, execution_ready, candidate_ready, missing)
        status = self._lifecycle_status(execution_ready, candidate_ready, compiler_supported)
        semantic_cluster = self._semantic_cluster(family, blueprints)
        profile = {
            "semantic_capabilities": concepts,
            "execution_capabilities": self._execution_capabilities(family, execution_ready),
            "compiler_capabilities": ["semantic_blueprint_mapping"] if compiler_supported == "TRUE" else [],
            "candidate_capabilities": ["candidate_blueprint_ready"] if candidate_ready == "READY_FOR_PROPOSAL" else [],
            "mental_model_support": MENTAL_MODEL_BY_FAMILY.get(family, "Not Available"),
        }
        return ProgramBlueprintIntelligence(
            blueprint_id=f"program_intelligence:{program_type}",
            program_type=program_type,
            semantic_family=family,
            semantic_cluster=semantic_cluster,
            mental_model=MENTAL_MODEL_BY_FAMILY.get(family, "Not Available"),
            supported_concepts=concepts,
            compiler_supported=compiler_supported,
            execution_ready=execution_ready,
            candidate_ready=candidate_ready,
            validation_ready=validation_ready,
            execution_package_available=package_available,
            required_packages=required,
            capability_profile=profile,
            missing_requirements=missing,
            capability_limitations=limitations,
            lifecycle_status=status,
        )

    def _semantic_family(self, program_type: str, blueprints: list[Mapping[str, Any]]) -> str:
        if program_type in FAMILY_BY_PROGRAM_TYPE:
            return FAMILY_BY_PROGRAM_TYPE[program_type]
        clusters = {
            str(item.get("semantic_cluster"))
            for item in blueprints
            if item.get("semantic_cluster")
        }
        if "Topology" in clusters or "Connectivity" in clusters:
            return "Topology"
        if "Physics" in clusters:
            return "Physics"
        if "Spatial" in clusters or "Motion" in clusters:
            return "Spatial"
        if "Object Identity" in clusters:
            return "Identity"
        return "Transformation"

    def _supported_concepts(self, family: str, blueprints: list[Mapping[str, Any]]) -> list[str]:
        concepts = list(SUPPORTED_CONCEPTS_BY_FAMILY.get(family, []))
        for item in blueprints:
            concept = _normalize(item.get("concept_name"))
            if concept:
                concepts.append(concept)
        return list(dict.fromkeys(concepts))

    def _semantic_cluster(self, family: str, blueprints: list[Mapping[str, Any]]) -> str:
        clusters = [
            str(item.get("semantic_cluster"))
            for item in blueprints
            if item.get("semantic_cluster")
        ]
        return clusters[0] if clusters else family

    def _package_available(self, blueprints: list[Mapping[str, Any]]) -> str:
        states = {_truth(item.get("execution_package_available"), unknown="UNKNOWN") for item in blueprints}
        if "TRUE" in states and "FALSE" not in states and "UNKNOWN" not in states:
            return "TRUE"
        if "FALSE" in states:
            return "FALSE"
        return "UNKNOWN"

    def _execution_ready(self, blueprints: list[Mapping[str, Any]], package_available: str) -> str:
        if package_available == "FALSE":
            return "MISSING_PACKAGE"
        if any(item.get("generation_status") == "GENERATED" for item in blueprints):
            return "EXECUTION_READY" if package_available == "TRUE" else "PARTIALLY_OPERATIONAL"
        if any(item.get("generation_status") == "PARTIALLY_GENERATED" for item in blueprints):
            return "PARTIALLY_OPERATIONAL"
        if any(item.get("generation_status") == "BLOCKED" for item in blueprints):
            return "BLOCKED"
        return "BLUEPRINT_ONLY"

    def _candidate_ready(self, blueprints, execution_ready: str, compiler_supported: str) -> str:
        if compiler_supported != "TRUE":
            return "WAITING_FOR_COMPILER_SUPPORT"
        if execution_ready == "MISSING_PACKAGE":
            return "WAITING_FOR_EXECUTION_PACKAGE"
        if execution_ready == "EXECUTION_READY" and all(
            "candidate_proposal_support" not in (item.get("missing_requirements") or [])
            for item in blueprints
        ):
            return "READY_FOR_PROPOSAL"
        if execution_ready in {"EXECUTION_READY", "PARTIALLY_OPERATIONAL"}:
            return "WAITING_FOR_VALIDATION"
        return "NOT_READY"

    def _required_packages(self, family: str, blueprints: list[Mapping[str, Any]]) -> list[str]:
        required = list(REQUIRED_PACKAGES_BY_FAMILY.get(family, []))
        for item in blueprints:
            for requirement in item.get("missing_requirements", []) or []:
                if str(requirement).endswith("_execution_package"):
                    required.append(str(requirement))
        return list(dict.fromkeys(required))

    def _missing_requirements(
        self,
        blueprints: list[Mapping[str, Any]],
        required: list[str],
        package_available: str,
        candidate_ready: str,
    ) -> list[str]:
        missing = []
        for item in blueprints:
            missing.extend(str(requirement) for requirement in item.get("missing_requirements", []) or [])
        if package_available != "TRUE":
            missing.extend(required)
        if candidate_ready != "READY_FOR_PROPOSAL":
            family_candidate = next((item for item in required if item.endswith("_candidate_support")), None)
            if family_candidate:
                missing.append(family_candidate)
        return list(dict.fromkeys(missing))

    def _capability_limitations(
        self,
        compiler_supported: str,
        execution_ready: str,
        candidate_ready: str,
        missing: list[str],
    ) -> list[str]:
        limitations = []
        if compiler_supported != "TRUE":
            limitations.append("compiler_support_missing")
        if execution_ready in {"MISSING_PACKAGE", "BLOCKED"}:
            limitations.append("execution_package_missing")
        if candidate_ready != "READY_FOR_PROPOSAL":
            limitations.append("candidate_proposal_not_ready")
        if missing:
            limitations.append("required_packages_missing")
        return list(dict.fromkeys(limitations))

    def _execution_capabilities(self, family: str, execution_ready: str) -> list[str]:
        if execution_ready not in {"EXECUTION_READY", "PARTIALLY_OPERATIONAL"}:
            return []
        return [f"{_normalize(family)}_execution_blueprint"]

    def _lifecycle_status(self, execution_ready: str, candidate_ready: str, compiler_supported: str) -> str:
        if compiler_supported != "TRUE":
            return "WAITING_FOR_COMPILER_SUPPORT"
        if execution_ready == "EXECUTION_READY" and candidate_ready == "READY_FOR_PROPOSAL":
            return "READY_FOR_CANDIDATE_PROPOSAL"
        if execution_ready == "MISSING_PACKAGE":
            return "WAITING_FOR_EXECUTION_PACKAGE"
        if execution_ready == "PARTIALLY_OPERATIONAL":
            return "PARTIALLY_OPERATIONAL"
        return "BLUEPRINT_INTELLIGENCE_AVAILABLE"

    def _validation(self, intelligence: list[dict[str, Any]]) -> dict[str, Any]:
        failures = []
        for item in intelligence:
            if not item.get("semantic_family"):
                failures.append(f"semantic_family_missing:{item.get('program_type')}")
            if not item.get("supported_concepts"):
                failures.append(f"supported_concepts_missing:{item.get('program_type')}")
            if not item.get("required_packages"):
                failures.append(f"required_packages_missing:{item.get('program_type')}")
            if not item.get("execution_ready"):
                failures.append(f"execution_readiness_missing:{item.get('program_type')}")
            if not item.get("candidate_ready"):
                failures.append(f"candidate_readiness_missing:{item.get('program_type')}")
        return {
            "validation_success": not failures,
            "validation_failures": failures,
            "semantic_family_consistency": not any("semantic_family" in failure for failure in failures),
            "package_requirements_declared": not any("required_packages" in failure for failure in failures),
            "readiness_declared": not any("readiness" in failure for failure in failures),
        }


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _truth(value: Any, *, unknown: str = "FALSE") -> str:
    text = str(value or "").upper()
    if text in {"TRUE", "FALSE"}:
        return text
    if text in {"UNKNOWN", "NOT_AVAILABLE", "NOT AVAILABLE"}:
        return unknown
    if value is True:
        return "TRUE"
    if value is False:
        return "FALSE"
    return unknown


program_blueprint_intelligence_layer = ProgramBlueprintIntelligenceLayer()

__all__ = [
    "ProgramBlueprintIntelligence",
    "ProgramBlueprintIntelligenceLayer",
    "program_blueprint_intelligence_layer",
]
