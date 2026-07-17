"""Generate canonical program blueprints from concept lifecycles."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


PROGRAM_TYPE_BY_CONCEPT = {
    "rotation": "rotation_program",
    "orientation_change": "rotation_program",
    "reflection": "reflection_program",
    "rotation_reflection": "reflection_program",
    "symbolic_remapping": "color_mapping_program",
    "color_mapping": "color_mapping_program",
    "color_preservation": "color_mapping_program",
    "growth": "growth_program",
    "topological_growth": "growth_program",
    "topology_preservation": "topology_program",
    "topology_change": "topology_program",
    "topology_repair": "topology_program",
    "gravity": "gravity_program",
    "falling": "gravity_program",
    "support": "gravity_program",
    "collision": "gravity_program",
    "rest_state": "gravity_program",
    "path_finding": "path_program",
    "path_construction": "path_program",
    "route_completion": "path_program",
    "noise_removal": "noise_filtering_program",
    "artifact_filtering": "noise_filtering_program",
    "object_removal": "noise_filtering_program",
    "component_merging": "component_merging_program",
    "bridge_creation": "component_merging_program",
    "component_connection": "component_merging_program",
    "connectivity_change": "component_merging_program",
    "object_identity_preservation": "object_identity_program",
}

PROGRAM_TYPE_BY_CLUSTER = {
    "Physics": "physics_program",
    "Topology": "topology_program",
    "Connectivity": "component_merging_program",
    "Spatial": "spatial_program",
    "Motion": "spatial_program",
    "Color": "color_mapping_program",
    "Geometry": "geometry_program",
    "Growth": "growth_program",
    "Transformation": "transformation_program",
    "Temporal": "temporal_program",
    "Object Identity": "object_identity_program",
    "Pattern Completion": "path_program",
    "Symmetry": "reflection_program",
    "Reasoning": "reasoning_program",
    "Dependency": "dependency_program",
    "Context": "context_program",
}

VALID_LIFECYCLE_STATUSES = {
    "DISCOVERED",
    "DISCOVERED_BUT_NOT_EXECUTABLE",
    "DISCOVERED_BUT_NOT_COMPILABLE",
    "CANDIDATE_AVAILABLE",
    "OPERATIONAL",
}


@dataclass
class ProgramBlueprint:
    program_id: str
    concept_name: str
    semantic_cluster: str
    program_type: str
    compiler_supported: str
    generation_attempted: str
    generation_success: str
    executable: str
    execution_package_available: str
    candidate_ready: str
    blocking_reason: str
    missing_requirements: list[str] = field(default_factory=list)
    generation_status: str = "NOT_ELIGIBLE"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProgramGenerationLayer:
    """Transform compiler-supported concepts into program blueprints."""

    system_name = "program_generation_layer"

    def generate(
        self,
        lifecycle_report: Mapping[str, Any] | None,
        *,
        generation_enabled: bool = True,
    ) -> dict[str, Any]:
        lifecycle_report = lifecycle_report if isinstance(lifecycle_report, Mapping) else {}
        lifecycles = lifecycle_report.get("concept_lifecycles", [])
        lifecycles = lifecycles if isinstance(lifecycles, list) else []
        blueprints = [
            self._blueprint(row, generation_enabled=generation_enabled).as_dict()
            for row in lifecycles
            if isinstance(row, Mapping)
        ]
        eligible = [
            item for item in blueprints
            if item["generation_attempted"] == "TRUE"
        ]
        generated = [
            item for item in blueprints
            if item["generation_success"] == "TRUE"
        ]
        blocked = [
            item for item in blueprints
            if item["generation_status"] in {"BLOCKED", "FAILED", "UNSUPPORTED"}
        ]
        missing = sorted({
            requirement
            for item in blueprints
            for requirement in item.get("missing_requirements", []) or []
        })
        success_rate = (
            round(len(generated) / len(eligible), 4)
            if eligible
            else 0.0
        )
        return {
            "system": self.system_name,
            "PROGRAM_GENERATION_REPORT": True,
            "generated_programs": len(generated),
            "eligible_concepts": len(eligible),
            "generated_blueprints": len(generated),
            "blocked_programs": len(blocked),
            "missing_requirements": missing,
            "generation_success_rate": success_rate,
            "program_blueprints": blueprints,
            "generation_attempt_count": len(eligible),
            "generation_failure_count": len(blocked),
            "execution_agnostic": True,
            "competition_agnostic": True,
        }

    def _blueprint(
        self,
        lifecycle: Mapping[str, Any],
        *,
        generation_enabled: bool,
    ) -> ProgramBlueprint:
        concept = _normalize(lifecycle.get("concept_name"))
        cluster = str(lifecycle.get("semantic_cluster") or "Not Available")
        compiler_supported = _truth(lifecycle.get("compiler_supported"))
        package_available = _truth(lifecycle.get("execution_package_available"), unknown="UNKNOWN")
        lifecycle_status = str(lifecycle.get("lifecycle_status") or "DISCOVERED")
        program_type = self._program_type(concept, cluster)
        base = {
            "program_id": f"program_blueprint:{concept or 'unknown'}",
            "concept_name": concept,
            "semantic_cluster": cluster,
            "program_type": program_type,
            "compiler_supported": compiler_supported,
            "execution_package_available": package_available,
            "candidate_ready": "FALSE",
        }
        if not generation_enabled:
            return ProgramBlueprint(
                **base,
                generation_attempted="FALSE",
                generation_success="FALSE",
                executable="FALSE",
                blocking_reason="PROGRAM_GENERATION_DISABLED",
                missing_requirements=["program_generation_enabled"],
                generation_status="BLOCKED",
            )
        if not concept:
            return ProgramBlueprint(
                **base,
                generation_attempted="FALSE",
                generation_success="FALSE",
                executable="FALSE",
                blocking_reason="UNSUPPORTED_CONCEPT",
                missing_requirements=["concept_name"],
                generation_status="NOT_ELIGIBLE",
            )
        if lifecycle_status not in VALID_LIFECYCLE_STATUSES:
            return ProgramBlueprint(
                **base,
                generation_attempted="FALSE",
                generation_success="FALSE",
                executable="FALSE",
                blocking_reason="SEMANTIC_NOT_OPERATIONAL",
                missing_requirements=["valid_lifecycle_status"],
                generation_status="NOT_ELIGIBLE",
            )
        if cluster in {"Not Available", "UNKNOWN", ""}:
            return ProgramBlueprint(
                **base,
                generation_attempted="FALSE",
                generation_success="FALSE",
                executable="FALSE",
                blocking_reason="UNKNOWN_SEMANTIC_CLUSTER",
                missing_requirements=["semantic_cluster"],
                generation_status="NOT_ELIGIBLE",
            )
        if compiler_supported != "TRUE":
            return ProgramBlueprint(
                **base,
                generation_attempted="FALSE",
                generation_success="FALSE",
                executable="FALSE",
                blocking_reason="NO_COMPILER_SUPPORT",
                missing_requirements=["compiler_support"],
                generation_status="NOT_ELIGIBLE",
            )
        if package_available == "FALSE":
            return ProgramBlueprint(
                **base,
                generation_attempted="TRUE",
                generation_success="FALSE",
                executable="FALSE",
                blocking_reason="NO_EXECUTION_PACKAGE",
                missing_requirements=[_execution_package_requirement(concept)],
                generation_status="BLOCKED",
            )
        if package_available == "UNKNOWN":
            return ProgramBlueprint(
                **base,
                generation_attempted="TRUE",
                generation_success="FALSE",
                executable="FALSE",
                blocking_reason="PROGRAM_PACKAGE_MISSING",
                missing_requirements=[_execution_package_requirement(concept)],
                generation_status="PARTIALLY_GENERATED",
            )
        return ProgramBlueprint(
            **base,
            generation_attempted="TRUE",
            generation_success="TRUE",
            executable="TRUE",
            blocking_reason="Not Available",
            missing_requirements=["candidate_proposal_support"],
            generation_status="GENERATED",
        )

    def _program_type(self, concept: str, cluster: str) -> str:
        if concept in PROGRAM_TYPE_BY_CONCEPT:
            return PROGRAM_TYPE_BY_CONCEPT[concept]
        if cluster in PROGRAM_TYPE_BY_CLUSTER:
            return PROGRAM_TYPE_BY_CLUSTER[cluster]
        return f"{_normalize(cluster) or 'generic'}_program"


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


def _execution_package_requirement(concept: str) -> str:
    return f"{concept}_execution_package" if concept else "execution_package"


program_generation_layer = ProgramGenerationLayer()

__all__ = [
    "ProgramBlueprint",
    "ProgramGenerationLayer",
    "program_generation_layer",
]
