from runtime.reporting.canonical_report_binding_engine import (
    BindingState,
    CanonicalReportBindingEngine,
    ReportFieldBinding,
)
from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer


def _state():
    return {
        "runtime_status": "completed",
        "tasks_executed": 3,
        "successful_tasks": 3,
        "generated_concepts": 4,
        "generated_programs": 21,
        "truth_candidate_count": 2,
        "metric_attribution_state": {
            "metric_ownership_map": {"generated_programs": "Program Runtime"},
        },
        "runtime_snapshots": {
            "latest_snapshot_payload": {"payload_size": 12},
        },
        "PROGRAM_SYNTHESIS_REPORT": {
            "average_program_confidence": 0.6148,
            "highest_confidence": 0.91,
            "lowest_confidence": 0.42,
            "validation_distribution": {"VALID": 21},
        },
        "COGNITIVE_SEARCH_REPORT": {
            "overall_search_quality": 0.499,
            "search_efficiency": 0.5,
            "search_coverage": 0.7,
            "search_entropy": 0.33,
            "route_count": 5,
        },
        "RUNTIME_LIFECYCLE_REPORT": {
            "total_executions": 3,
            "completed_executions": 3,
            "execution_coverage": 1.0,
            "snapshot_coverage": 1.0,
            "lifecycle_coverage": 1.0,
        },
        "execution_timing": {
            "execution_timing_state": {
                "total_wall_time": 20.0,
                "cognitive_runtime_time": 15.0,
                "unattributed_time": 1.0,
                "timing_coverage": 0.95,
                "report_generation_time": 0.4,
                "finalization_time": 0.6,
            },
            "timing_records": [
                {
                    "execution_id": "old-exec",
                    "timing_scope": "SEARCH_TIME",
                    "timing_status": "OBSERVED",
                    "validation_status": "VALID",
                    "wall_duration_seconds": 99.0,
                },
                {
                    "timing_scope": "TASK_SELECTION_TIME",
                    "timing_status": "OBSERVED",
                    "validation_status": "VALID",
                    "wall_duration_seconds": 1.0,
                },
                {
                    "timing_scope": "GOVERNANCE_TIME",
                    "timing_status": "UNOBSERVED",
                    "validation_status": "VALID",
                    "wall_duration_seconds": 0.0,
                },
            ],
        },
        "performance_report": {
            "total_runtime_seconds": 20.0,
            "active_compute_time_seconds": 17.0,
            "untracked_runtime_seconds": 1.0,
            "stage_metrics": [
                {"stage_name": "program_synthesis", "total_duration": 3.0},
                {"stage_name": "evaluation", "total_duration": 0.5},
            ],
        },
    }


def _metadata():
    return {
        "system": "NEXRYN",
        "mode": "test",
        "profile": "unit",
        "execution_id": "exec-1",
        "timestamp": "2026-07-15T00:00:00Z",
        "execution_time": 1.25,
    }


def test_canonical_source_discovery_registers_known_sources():
    engine = CanonicalReportBindingEngine()

    sources = engine.discover_sources(_state(), runtime_metadata=_metadata())

    assert "execution_registry" in sources
    assert "metric_attribution_state" in sources
    assert "runtime_snapshots" in sources
    assert "unified_concept_lifecycle_report" in sources
    assert "program_generation_report" in sources
    assert "program_blueprint_intelligence_report" in sources
    assert "cognitive_program_lifecycle_report" in sources
    assert "cognitive_knowledge_domains_report" in sources
    assert "cognitive_domain_intelligence_report" in sources
    assert "cognitive_domain_lifecycle_report" in sources
    assert "cognitive_domain_interaction_report" in sources
    assert "cognitive_domain_governance_report" in sources
    assert "cognitive_domain_ecosystem_report" in sources
    assert "cognitive_domain_constitution_report" in sources
    assert sources["program_registry"].payload["average_program_confidence"] == 0.6148


def test_field_binding_resolves_visible_values():
    result = CanonicalReportBindingEngine().bind(
        _state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert result["field_values"]["generated_programs"] == "21"
    assert result["field_values"]["overall_search_quality"] == "0.499"
    assert result["field_values"]["average_program_confidence"] == "0.6148"
    assert result["field_values"]["execution_coverage"] == "100%"


def test_generated_outputs_bind_from_semantic_synthesis_when_top_level_missing():
    state = _state()
    state.pop("generated_concepts")
    state.pop("generated_programs")
    state["semantic_concept_count"] = 8
    state["TRANSFORMATION_SYNTHESIS_REPORT"] = {
        "detected_concepts": [
            "bridge_creation",
            "component_connection",
            "connectivity_change",
            "topology_change",
        ],
        "candidate_count": 3,
        "generated_transformations": [
            {"steps": [{"operation": "connect_components"}]},
            {"steps": [{"operation": "construct_path"}]},
            {"steps": [{"operation": "repair_topology"}]},
        ],
        "semantic_to_transformation_compilation_report": {
            "semantic_to_transformation_compilation_success": False,
            "detected_intents": [
                "bridge_creation",
                "component_connection",
                "connectivity_change",
                "topology_change",
            ],
            "execution_intents": [
                {
                    "intent": "component_connection",
                    "operation": "connect_components",
                }
            ],
            "candidate_count": 0,
        },
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    semantic_summary = result["field_bindings"]["semantic_compilation_summary"]["value"]

    assert result["field_values"]["generated_concepts"] == "8"
    assert result["field_values"]["generated_programs"] == "3"
    assert semantic_summary["generated_concepts"] == 8
    assert semantic_summary["generated_programs"] == 3
    assert semantic_summary["execution_intent_count"] == 1


def test_unified_concept_lifecycle_binding_tracks_concepts():
    state = _state()
    state["semantic_attribution_report"] = {
        "attributed_concepts": ["gravity", "rotation"],
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    lifecycle = result["field_bindings"]["unified_concept_lifecycle_summary"]["value"]
    concepts = {
        item["concept_name"]: item
        for item in lifecycle["concept_lifecycles"]
    }

    assert lifecycle["canonical_concept_lifecycle_source"] is True
    assert concepts["gravity"]["mental_model"] == "Gravity Simulation"
    assert concepts["gravity"]["execution_package_available"] == "FALSE"
    assert concepts["rotation"]["execution_package_available"] == "TRUE"


def test_program_generation_binding_builds_blueprints_from_lifecycle():
    state = _state()
    state["semantic_attribution_report"] = {
        "attributed_concepts": ["rotation", "gravity"],
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    generation = result["field_bindings"]["program_generation_summary"]["value"]
    blueprints = {
        item["concept_name"]: item
        for item in generation["program_blueprints"]
    }
    lifecycle = result["field_bindings"]["unified_concept_lifecycle_summary"]["value"]
    lifecycle_rows = {
        item["concept_name"]: item
        for item in lifecycle["concept_lifecycles"]
    }

    assert generation["generated_programs"] >= 1
    assert blueprints["rotation"]["generation_status"] == "GENERATED"
    assert blueprints["rotation"]["candidate_ready"] == "FALSE"
    assert blueprints["gravity"]["generation_status"] == "NOT_ELIGIBLE"
    assert lifecycle_rows["rotation"]["program_generation_attempted"] == "TRUE"
    assert lifecycle_rows["rotation"]["program_generated"] == "TRUE"


def test_program_blueprint_intelligence_binding_enriches_blueprints():
    state = _state()
    state["semantic_attribution_report"] = {
        "attributed_concepts": [
            "topology_change",
            "bridge_creation",
        ],
    }
    state["PROGRAM_GENERATION_REPORT"] = {
        "program_blueprints": [
            {
                "program_id": "program_blueprint:topology_change",
                "concept_name": "topology_change",
                "semantic_cluster": "Topology",
                "program_type": "topology_program",
                "compiler_supported": "TRUE",
                "generation_success": "TRUE",
                "generation_status": "GENERATED",
                "execution_package_available": "TRUE",
                "candidate_ready": "FALSE",
                "missing_requirements": ["candidate_proposal_support"],
            },
            {
                "program_id": "program_blueprint:bridge_creation",
                "concept_name": "bridge_creation",
                "semantic_cluster": "Connectivity",
                "program_type": "topology_program",
                "compiler_supported": "TRUE",
                "generation_success": "TRUE",
                "generation_status": "GENERATED",
                "execution_package_available": "TRUE",
                "candidate_ready": "FALSE",
                "missing_requirements": ["candidate_proposal_support"],
            },
        ],
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    intelligence = result["field_bindings"][
        "program_blueprint_intelligence_summary"
    ]["value"]
    topology = intelligence["program_blueprint_intelligence"][0]

    assert intelligence["validation_success"] is True
    assert topology["semantic_family"] == "Topology"
    assert "component_connection" in topology["supported_concepts"]
    assert topology["execution_ready"] == "EXECUTION_READY"
    assert topology["candidate_ready"] == "WAITING_FOR_VALIDATION"


def test_cognitive_program_lifecycle_binding_tracks_registry_metrics():
    state = _state()
    state["PROGRAM_BLUEPRINT_INTELLIGENCE_REPORT"] = {
        "program_blueprint_intelligence": [
            {
                "blueprint_id": "program_intelligence:gravity_program",
                "program_type": "gravity_program",
                "semantic_family": "Physics",
                "mental_model": "Gravity Simulation",
                "supported_concepts": ["gravity", "falling"],
                "compiler_supported": "TRUE",
                "execution_ready": "MISSING_PACKAGE",
                "candidate_ready": "WAITING_FOR_EXECUTION_PACKAGE",
                "validation_ready": "FALSE",
                "required_packages": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                    "gravity_validation_support",
                ],
                "missing_requirements": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                    "gravity_validation_support",
                ],
                "capability_profile": {
                    "semantic_capabilities": ["gravity", "falling"],
                },
            },
        ],
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    lifecycle = result["field_bindings"]["cognitive_program_lifecycle_summary"]["value"]
    row = lifecycle["program_registry"][0]

    assert lifecycle["total_program_blueprints"] == 1
    assert lifecycle["blocked_program_count"] == 1
    assert row["program_type"] == "gravity_program"
    assert row["maturity_level"] == "FOUNDATIONAL"
    assert row["candidate_readiness"] == "NOT_READY"


def test_cognitive_knowledge_domains_binding_organizes_concepts():
    state = _state()
    state["semantic_attribution_report"] = {
        "attributed_concepts": [
            "gravity",
            "falling",
        ],
    }
    state["PROGRAM_BLUEPRINT_INTELLIGENCE_REPORT"] = {
        "program_blueprint_intelligence": [
            {
                "blueprint_id": "program_intelligence:gravity_program",
                "program_type": "gravity_program",
                "semantic_family": "Physics",
                "mental_model": "Gravity Simulation",
                "supported_concepts": ["gravity", "falling", "support"],
                "compiler_supported": "TRUE",
                "execution_ready": "MISSING_PACKAGE",
                "candidate_ready": "WAITING_FOR_EXECUTION_PACKAGE",
                "validation_ready": "FALSE",
                "required_packages": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                ],
                "missing_requirements": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                ],
                "capability_profile": {
                    "semantic_capabilities": ["gravity", "falling"],
                },
            },
        ],
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    domains = result["field_bindings"]["cognitive_knowledge_domains_summary"]["value"]
    physics = {
        domain["domain_name"]: domain
        for domain in domains["domains"]
    }["Physics Domain"]

    assert domains["validation_success"] is True
    assert domains["silent_domain_assignment_failures"] is False
    assert physics["semantic_families"] == ["Physics"]
    assert "Gravity Simulation" in physics["mental_models"]
    assert "gravity_program" in physics["program_blueprints"]
    assert "gravity" in physics["semantic_concepts"]
    assert "gravity_candidate_support" in physics["missing_capabilities"]


def test_cognitive_domain_intelligence_binding_describes_domain_capabilities():
    state = _state()
    state["COGNITIVE_KNOWLEDGE_DOMAINS_REPORT"] = {
        "domains": [
            {
                "domain_id": "domain:spatial",
                "domain_name": "Spatial Domain",
                "semantic_families": ["Spatial"],
                "semantic_concepts": ["relative_position"],
                "mental_models": ["Spatial Reasoning"],
            },
            {
                "domain_id": "domain:identity",
                "domain_name": "Identity Domain",
                "semantic_families": ["Identity"],
                "semantic_concepts": ["object_identity_preservation"],
                "mental_models": ["Object Identity"],
            },
            {
                "domain_id": "domain:topology",
                "domain_name": "Topology Domain",
                "semantic_families": ["Topology"],
                "mental_models": ["Topology Reasoning"],
                "program_blueprints": ["topology_program"],
                "semantic_concepts": ["bridge_creation", "topology_change"],
                "execution_packages": ["topology_execution_package"],
                "operational_capabilities": ["topology_execution"],
                "missing_capabilities": ["topology_candidate_support"],
            },
        ],
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    intelligence = result["field_bindings"]["cognitive_domain_intelligence_summary"]["value"]
    topology = {
        domain["domain_name"]: domain
        for domain in intelligence["domain_intelligence"]
    }["Topology Domain"]

    assert intelligence["validation_success"] is True
    assert topology["semantic_capabilities"] == ["bridge_creation", "topology_change"]
    assert topology["required_domains"] == ["Spatial Domain", "Identity Domain"]
    assert topology["readiness_state"] == "PARTIALLY_OPERATIONAL"


def test_cognitive_domain_lifecycle_binding_tracks_domain_evolution():
    state = _state()
    state["COGNITIVE_DOMAIN_INTELLIGENCE_REPORT"] = {
        "domain_intelligence": [
            {
                "domain_id": "domain:spatial",
                "domain_name": "Spatial Domain",
                "semantic_capabilities": ["relative_position"],
                "mental_models": ["Spatial Reasoning"],
            },
            {
                "domain_id": "domain:geometry",
                "domain_name": "Geometry Domain",
                "semantic_capabilities": ["shape_geometry"],
                "mental_models": ["Geometry Reasoning"],
            },
            {
                "domain_id": "domain:physics",
                "domain_name": "Physics Domain",
                "semantic_capabilities": ["gravity", "falling"],
                "mental_models": ["Gravity Simulation"],
                "program_blueprints": ["physics_program"],
                "missing_capabilities": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                ],
                "required_domains": ["Spatial Domain", "Geometry Domain"],
            },
        ],
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    lifecycle = result["field_bindings"]["cognitive_domain_lifecycle_summary"]["value"]
    physics = {
        row["domain_name"]: row
        for row in lifecycle["domain_registry"]
    }["Physics Domain"]

    assert lifecycle["total_domains"] == 3
    assert physics["lifecycle_stage"] == "PROGRAM_DEFINED"
    assert physics["maturity_level"] == "DEVELOPING"
    assert physics["execution_readiness"] == "NOT_READY"
    assert physics["lifecycle_failures"][0]["reason"] == "physics_execution_package_missing"


def test_cognitive_domain_interaction_binding_builds_collaboration_graph():
    state = _state()
    state["COGNITIVE_DOMAIN_LIFECYCLE_REPORT"] = {
        "domain_registry": [
            {
                "domain_name": "Physics Domain",
                "semantic_capability_evolution": ["gravity"],
                "required_domains": ["Spatial Domain", "Geometry Domain"],
                "operational_capability_evolution": ["object_motion_reasoning"],
            },
            {
                "domain_name": "Spatial Domain",
                "semantic_capability_evolution": ["relative_position"],
            },
            {
                "domain_name": "Geometry Domain",
                "semantic_capability_evolution": ["object_shape"],
            },
        ],
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    interaction = result["field_bindings"]["cognitive_domain_interaction_summary"]["value"]
    physics = {
        row["domain_name"]: row
        for row in interaction["domain_interaction_reports"]
    }["Physics Domain"]

    assert interaction["dependency_graph"]["Physics Domain"] == [
        "Spatial Domain",
        "Geometry Domain",
    ]
    assert "Spatial Domain" in physics["collaborating_domains"]
    assert "object_motion_reasoning" in physics["shared_capabilities"]
    assert interaction["operational_capability_compositions"][0]["composition_name"] == (
        "Object Falling Simulation"
    )


def test_domain_interaction_bootstrap_composes_cognitive_domains_when_large_state():
    state = _state()
    state["large_payload"] = {
        f"section_{index}": list(range(50))
        for index in range(80)
    }
    state["TRANSFORMATION_SYNTHESIS_REPORT"] = {
        "detected_concepts": [
            "growth",
            "topology_change",
            "relative_position",
            "object_identity_preservation",
            "color_mapping",
            "transformation_sequence",
        ],
    }
    state["PROGRAM_GENERATION_REPORT"] = {
        "generated_programs": 4,
        "generated_blueprints": 4,
        "program_blueprints": [
            {
                "concept_name": "growth",
                "program_type": "growth_program",
                "supported_concepts": ["growth"],
            },
            {
                "concept_name": "topology_change",
                "program_type": "topology_program",
                "supported_concepts": ["topology_change"],
            },
            {
                "concept_name": "relative_position",
                "program_type": "spatial_program",
                "supported_concepts": ["relative_position"],
            },
            {
                "concept_name": "color_mapping",
                "program_type": "color_program",
                "supported_concepts": ["color_mapping"],
            },
        ],
    }
    state["CANDIDATE_PROPOSAL_REPORT"] = {
        "proposal_phase_entered": True,
        "eligible_source_count": 1,
        "proposal_count": 3,
        "candidate_proposals": [
            {"source": "program_generation", "proposal_status": "PROPOSED", "operation": "duplicate_object"},
            {"source": "program_generation", "proposal_status": "PROPOSED", "operation": "connect_components"},
            {"source": "program_generation", "proposal_status": "PROPOSED", "operation": "replace_color"},
        ],
    }
    state["COGNITIVE_CANDIDATE_ARENA_REPORT"] = {
        "candidate_arena_summary": {
            "selection_mode": "EVIDENCE_BASED_ARENA",
            "arena_state": "SINGLE_SOURCE_ONLY",
            "candidate_count": 3,
            "source_count": 1,
            "sources_entered": ["normalized_program_candidates"],
            "candidate_summary": [
                {"source": "normalized_program_candidates", "operation": "duplicate_object", "entered_arena": True},
                {"source": "normalized_program_candidates", "operation": "connect_components", "entered_arena": True},
                {"source": "normalized_program_candidates", "operation": "replace_color", "entered_arena": True},
            ],
        }
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    interaction = result["field_bindings"][
        "cognitive_domain_interaction_summary"
    ]["value"]

    assert interaction["domain_interaction_count"] > 0
    assert interaction["collaboration_score"] > 0.0
    assert interaction["cross_domain_operational_readiness"]
    assert interaction["operational_capability_lifecycle_count"] >= 3
    assert "capability_promotion_candidate_count" in interaction
    assert interaction["capability_organism_count"] >= 3
    assert interaction["emerging_capability_count"] >= 1
    assert interaction["capability_watch_count"] >= 1
    assert any(
        row["composition_name"] == "Bridge Creation Capability"
        and row["lifecycle_state"] in {"COMPOSITION_PARTIAL", "OPERATIONAL_READY"}
        and row["blocking_stage"]
        and row["governance_status"]
        and row["promotion_state"]
        and row["registry_eligibility"]
        and isinstance(row["promotion_score"], float)
        and row["growth_stage"] in {"EMERGING", "DEVELOPING", "SANDBOX_OPERATIONAL", "PROMOTED", "REUSABLE"}
        and row["organism_state"]
        and row["capability_identity"]["capability_id"]
        and isinstance(row["evolution_readiness"], float)
        and row["resource_decision"] in {"INVEST", "WATCH", "HOLD", "ARCHIVE"}
        and row["resource_budget"]["growth_budget"]
        and isinstance(row["value_score"], float)
        for row in interaction["operational_capability_compositions"]
    )


def test_cognitive_domain_governance_binding_detects_invalid_ownership():
    state = _state()
    state["COGNITIVE_DOMAIN_LIFECYCLE_REPORT"] = {
        "domain_registry": [
            {
                "domain_name": "Transformation Domain",
                "lifecycle_stage": "PROGRAM_DEFINED",
                "maturity_level": "DEVELOPING",
                "semantic_capability_evolution": ["rotation", "gravity"],
                "required_domains": ["Geometry Domain"],
            },
            {
                "domain_name": "Geometry Domain",
                "semantic_capability_evolution": ["object_shape"],
            },
        ],
    }
    state["COGNITIVE_DOMAIN_INTERACTION_REPORT"] = {
        "domain_interaction_reports": [],
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    governance = result["field_bindings"]["cognitive_domain_governance_summary"]["value"]
    transformation = {
        row["domain_name"]: row
        for row in governance["domain_governance"]
    }["Transformation Domain"]

    assert governance["validation_success"] is False
    assert transformation["governance_status"] == "BOUNDARY_VIOLATION"
    assert transformation["capability_conflicts"][0]["expected_owner"] == "Physics Domain"


def test_cognitive_domain_ecosystem_binding_summarizes_global_state():
    state = _state()
    state["COGNITIVE_DOMAIN_LIFECYCLE_REPORT"] = {
        "domain_registry": [
            {
                "domain_name": "Physics Domain",
                "maturity_level": "DEVELOPING",
                "semantic_capability_evolution": ["gravity", "falling"],
                "mental_model_evolution": ["Gravity Simulation"],
                "program_blueprint_evolution": ["physics_program"],
                "execution_capability_evolution": [],
                "candidate_capability_evolution": [],
                "operational_capability_evolution": [],
                "program_readiness": "READY",
                "execution_readiness": "NOT_READY",
                "candidate_readiness": "NOT_READY",
                "operational_readiness": "NOT_READY",
                "required_domains": ["Spatial Domain", "Geometry Domain"],
                "missing_capabilities": [
                    "gravity_execution_package",
                    "gravity_candidate_support",
                ],
            },
            {
                "domain_name": "Spatial Domain",
                "maturity_level": "OPERATIONAL",
                "semantic_capability_evolution": ["relative_position"],
                "mental_model_evolution": ["Spatial Reasoning"],
                "program_blueprint_evolution": ["spatial_program"],
                "execution_capability_evolution": ["spatial_execution_package"],
                "candidate_capability_evolution": ["spatial_candidate_support"],
                "operational_capability_evolution": ["relative_position_reasoning"],
                "program_readiness": "READY",
                "execution_readiness": "READY",
                "candidate_readiness": "READY",
                "operational_readiness": "READY",
            },
        ],
    }
    state["COGNITIVE_DOMAIN_INTERACTION_REPORT"] = {
        "dependency_graph": {
            "Physics Domain": ["Spatial Domain", "Geometry Domain"],
        },
        "domain_interaction_reports": [
            {
                "domain_name": "Physics Domain",
                "collaborating_domains": ["Spatial Domain", "Geometry Domain"],
            },
        ],
    }
    state["COGNITIVE_DOMAIN_GOVERNANCE_REPORT"] = {
        "domain_governance": [
            {
                "domain_name": "Physics Domain",
                "semantic_coherence_score": 1.0,
                "governance_integrity_score": 1.0,
            },
        ],
    }
    state["TRANSFORMATION_SYNTHESIS_REPORT"] = {
        "detected_concepts": ["bridge_creation", "color_preservation"],
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    ecosystem = result["field_bindings"]["cognitive_domain_ecosystem_summary"]["value"]

    assert ecosystem["global_cognitive_coverage"]["domains"] == 2
    assert ecosystem["global_cognitive_coverage"]["execution_packages"] >= 2
    assert ecosystem["dependency_graph"]["Physics Domain"] == [
        "Spatial Domain",
        "Geometry Domain",
    ]
    assert "gravity_execution_package" in ecosystem["missing_ecosystem_capabilities"]
    assert ecosystem["cognitive_bottlenecks"][0]["bottleneck_type"] in {
        "candidate_proposal_support",
        "execution_package_coverage",
        "program_to_execution_gap",
    }


def test_cognitive_domain_constitution_binding_audits_invariants():
    state = _state()
    state["COGNITIVE_DOMAIN_LIFECYCLE_REPORT"] = {
        "domain_registry": [
            {
                "domain_name": "Transformation Domain",
                "lifecycle_stage": "PROGRAM_DEFINED",
                "maturity_level": "DEVELOPING",
                "semantic_capability_evolution": ["rotation", "gravity"],
                "mental_model_evolution": ["Transformation Reasoning"],
                "program_blueprint_evolution": ["transformation_program"],
            },
            {
                "domain_name": "Physics Domain",
                "lifecycle_stage": "PROGRAM_DEFINED",
                "maturity_level": "DEVELOPING",
                "semantic_capability_evolution": ["gravity"],
                "mental_model_evolution": ["Gravity Simulation"],
                "program_blueprint_evolution": ["physics_program"],
            },
        ],
    }
    state["COGNITIVE_DOMAIN_INTERACTION_REPORT"] = {
        "domain_interaction_reports": [],
    }
    state["COGNITIVE_DOMAIN_GOVERNANCE_REPORT"] = {
        "domain_governance": [
            {
                "domain_name": "Transformation Domain",
                "capability_conflicts": [
                    {
                        "capability": "gravity",
                        "expected_owner": "Physics Domain",
                        "actual_owner": "Transformation Domain",
                    },
                ],
                "boundary_violations": [
                    {
                        "capability": "gravity",
                        "reason": "FORBIDDEN_CAPABILITY_TOKEN",
                    },
                ],
                "semantic_coherence_score": 0.5,
                "governance_integrity_score": 0.5,
            },
            {
                "domain_name": "Physics Domain",
                "semantic_coherence_score": 1.0,
                "governance_integrity_score": 1.0,
            },
        ],
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    constitution = result["field_bindings"]["cognitive_domain_constitution_summary"]["value"]
    violation_types = {
        violation["violation_type"]
        for violation in constitution["constitutional_violations"]
    }

    assert "SEMANTIC_BOUNDARY_BREACH" in violation_types
    assert "OWNERSHIP_CONFLICT" in violation_types
    assert constitution["ownership_compliance"] is False
    assert constitution["constitutional_status"] != "FULLY_CONSTITUTIONAL"


def test_duplicate_owner_and_conflicting_binding_detection():
    bindings = [
        ReportFieldBinding(
            "generated_programs",
            "Program Runtime",
            "report_state",
            ("NORMAL",),
            source_fields=("generated_programs",),
        ),
        ReportFieldBinding(
            "generated_programs",
            "Search Runtime",
            "search_metrics",
            ("NORMAL",),
            source_fields=("generated_programs",),
        ),
    ]

    errors = CanonicalReportBindingEngine(bindings).validate_field_registry()

    assert "conflicting_binding:generated_programs" in errors
    assert "duplicate_owner:generated_programs" in errors
    assert "conflicting_source:generated_programs" in errors


def test_visibility_validation_and_hidden_policy_state():
    bindings = [
        ReportFieldBinding(
            "metric_ownership_map",
            "Metric Attribution",
            "metric_attribution_state",
            ("DIAGNOSTIC",),
            source_fields=("metric_ownership_map",),
            representation_type="map",
        ),
        ReportFieldBinding(
            "bad_visibility",
            "Representation",
            "report_state",
            ("SIDEWAYS",),
        ),
    ]
    engine = CanonicalReportBindingEngine(bindings)

    result = engine.bind(_state(), report_level="normal")

    hidden = result["field_bindings"]["metric_ownership_map"]
    assert hidden["binding_status"] == BindingState.HIDDEN.value
    assert hidden["display_value"] == "Hidden by Report Policy"
    assert "invalid_visibility_policy:bad_visibility" in (
        result["binding_diagnostics"]["validation_errors"]
    )


def test_compression_and_externalization_states():
    result = CanonicalReportBindingEngine().bind(
        _state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    compressed = result["field_bindings"]["validation_distribution"]
    externalized = result["field_bindings"]["metric_ownership_map"]

    assert compressed["binding_status"] == BindingState.COMPRESSED.value
    assert compressed["display_value"] == "Compressed Summary: 1 fields"
    assert externalized["binding_status"] == BindingState.EXTERNALIZED.value
    assert externalized["display_value"] == "Externalized to Technical Appendix"


def test_required_field_validation_and_invalid_representation_type():
    bindings = [
        ReportFieldBinding(
            "generated_programs",
            "Program Runtime",
            "report_state",
            ("NORMAL",),
            representation_type="count",
            source_fields=("missing_program_count",),
            required=True,
        ),
        ReportFieldBinding(
            "bad_representation",
            "Representation",
            "report_state",
            ("NORMAL",),
            representation_type="mystery",
        ),
    ]

    result = CanonicalReportBindingEngine(bindings).bind(
        _state(),
        report_level="normal",
    )
    errors = result["binding_diagnostics"]["validation_errors"]

    assert result["field_bindings"]["generated_programs"]["binding_status"] == (
        BindingState.NOT_AVAILABLE.value
    )
    assert "required_field_not_bound:generated_programs" in errors
    assert "invalid_representation_type:bad_representation" in errors


def test_report_level_compatibility_and_deterministic_resolution():
    engine = CanonicalReportBindingEngine()

    first = engine.bind(_state(), runtime_metadata=_metadata(), report_level="normal")
    second = engine.bind(_state(), runtime_metadata=_metadata(), report_level="normal")

    assert first["field_values"] == second["field_values"]
    assert {
        name: field["binding_state"]
        for name, field in first["report_field_registry"].items()
    } == {
        name: field["binding_state"]
        for name, field in second["report_field_registry"].items()
    }
    assert first["field_bindings"]["snapshot_payload"]["binding_status"] == (
        BindingState.EXTERNALIZED.value
    )


def test_legacy_unknown_value_elimination_in_binding_and_final_report():
    state = _state()
    state["generated_programs"] = "UNKNOWN"

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert result["field_values"]["generated_programs"] == "Not Available"
    assert "UNKNOWN" not in report
    assert "Generated Programs: Not Available" in report


def test_prediction_provenance_binding_resolves_decision_summary():
    state = _state()
    state["TRANSFORMATION_SYNTHESIS_REPORT"] = {
        "detected_concepts": ["rotation", "reflection"],
        "candidate_count": 3,
        "transformation_confidence": 0.91,
        "transformation_accuracy": 1.0,
        "selected_program": {
            "step_count": 1,
            "steps": [
                {
                    "operation": "mirror_vertical",
                    "parameters": {"axis": "vertical"},
                }
            ],
        },
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata={"execution_id": "exec-1"},
        report_level="normal",
    )
    summary = result["field_bindings"]["prediction_provenance_summary"]["value"]

    assert summary["decision_owner"] == "Transformation Synthesis Engine"
    assert summary["prediction_source"] == "transformation_synthesis"
    assert summary["winning_candidate"] == "mirror_vertical"
    assert summary["generated_concept_count"] == 2
    assert summary["candidate_count"] == 3
    assert summary["program_validation"] == "SUCCESS"


def test_candidate_arena_binding_detects_single_source_dominance():
    state = _state()
    state["ADAPTIVE_REUSE_REPORT"] = {
        "reuse_success_rate": 1.0,
        "reused_programs": [
            {
                "steps": [
                    {"operation": "reuse_transform", "parameters": {}}
                ],
                "step_count": 1,
            }
        ],
    }
    state["PREDICTION_PROVENANCE_REPORT"] = {
        "prediction_source": "adaptive_reuse",
        "decision_owner": "Adaptive Reuse Layer",
        "winning_candidate": "reuse_transform",
        "decision_confidence": 1.0,
    }
    state["TRANSFORMATION_SYNTHESIS_REPORT"] = {
        "detected_concepts": ["bridge_creation", "component_connection"],
        "semantic_to_transformation_compilation_report": {
            "semantic_to_transformation_compilation_success": False,
            "detected_intents": ["bridge_creation", "component_connection"],
            "execution_intents": [],
            "semantic_intent_routing_report": {
                "semantic_intent_routing_success": False,
                "execution_intent_count": 0,
            },
            "candidate_count": 0,
            "compiled_program": {"steps": [], "step_count": 0},
            "failure_reason": "no_executable_semantic_intents",
        },
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata={"execution_id": "exec-1"},
        report_level="normal",
    )
    summary = result["field_bindings"]["candidate_arena_summary"]["value"]
    decision = result["field_bindings"]["prediction_provenance_summary"]["value"]

    assert summary["arena_state"] == "SINGLE_SOURCE_DOMINANCE"
    assert summary["candidate_count"] == 1
    assert summary["attempted_candidate_count"] == 2
    assert summary["explicit_rejection_count"] == 1
    assert summary["competitor_sources"] == ["adaptive_reuse"]
    assert summary["winner_takes_all_detected"] is True
    assert summary["dominance_source"] == "adaptive_reuse"
    assert summary["source_status"]["semantic_to_transformation_compiler"] == "BLOCKED"
    assert summary["source_outcomes"][0]["source"] == "semantic_to_transformation_compiler"
    assert summary["source_outcomes"][0]["status"] == "REJECTED"
    assert decision["compiler_attempted"] is True
    assert "Semantic Compilation" in decision["decision_pipeline"]


def test_candidate_arena_binding_admits_nested_adaptive_reuse_program_steps():
    state = _state()
    state["ADAPTIVE_REUSE_REPORT"] = {
        "reuse_success_rate": 1.0,
        "reused_programs": [
            {
                "program": {
                    "program_steps": [
                        {"operation": "translate", "parameters": {"delta_row": 1}}
                    ],
                },
                "step_count": 1,
            }
        ],
    }
    state["PREDICTION_PROVENANCE_REPORT"] = {
        "prediction_source": "adaptive_reuse",
        "decision_owner": "Adaptive Reuse Layer",
        "winning_candidate": "translate",
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata={"execution_id": "exec-1"},
        report_level="normal",
    )
    summary = result["field_bindings"]["candidate_arena_summary"]["value"]

    assert summary["candidate_count"] == 1
    assert summary["source_status"]["adaptive_reuse"] == "ENTERED"
    assert summary["competitor_sources"] == ["adaptive_reuse"]
    assert summary["source_outcomes"][0]["operation"] == "translate"


def test_selected_semantic_compiler_without_report_is_explicit_rejection():
    state = _state()
    state["tool_selection_report"] = {
        "enabled_tools": ["semantic_to_transformation_compiler"],
    }
    state["ADAPTIVE_REUSE_REPORT"] = {
        "reuse_success_rate": 1.0,
        "reused_programs": [
            {
                "steps": [
                    {"operation": "reuse_transform", "parameters": {}}
                ],
                "step_count": 1,
            }
        ],
    }
    state["PREDICTION_PROVENANCE_REPORT"] = {
        "prediction_source": "adaptive_reuse",
        "decision_owner": "Adaptive Reuse Layer",
        "winning_candidate": "reuse_transform",
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata={"execution_id": "exec-1"},
        report_level="normal",
    )
    semantic = result["field_bindings"]["semantic_compilation_summary"]["value"]
    decision = result["field_bindings"]["prediction_provenance_summary"]["value"]
    arena = result["field_bindings"]["candidate_arena_summary"]["value"]
    proposal = result["field_bindings"]["candidate_proposal_summary"]["value"]

    assert semantic["compiler_selected"] is True
    assert semantic["compiler_triggered"] is True
    assert semantic["compilation_status"] == "REQUIRED_REPORT_MISSING"
    assert decision["compiler_attempted"] is True
    assert "Semantic Compilation" in decision["decision_pipeline"]
    assert arena["attempted_candidate_count"] == 2
    assert arena["explicit_rejection_count"] == 1
    assert arena["source_status"]["semantic_to_transformation_compiler"] == "BLOCKED"
    assert proposal["proposal_phase_entered"] is True
    assert proposal["explicit_rejection_count"] == 1
    assert proposal["sources_rejected"] == ["semantic_to_transformation_compiler"]
    assert any(
        outcome["source"] == "semantic_to_transformation_compiler"
        and outcome["status"] == "REJECTED"
        for outcome in arena["source_outcomes"]
    )


def test_executable_semantic_coverage_identifies_unsupported_clusters():
    state = _state()
    state["TRANSFORMATION_SYNTHESIS_REPORT"] = {
        "detected_concepts": [
            "density_increase",
            "symmetry_break",
            "relative_position",
            "spatial_relation",
            "transformation_sequence",
            "bridge_creation",
            "component_connection",
            "connectivity_change",
            "topology_change",
            "density_modulation",
            "growth",
            "propagation",
            "directional_motion",
            "position_preservation",
            "object_identity_preservation",
            "shape_preservation",
            "rotation",
            "reflection",
        ],
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    coverage = result["field_bindings"][
        "executable_semantic_coverage_summary"
    ]["value"]

    assert coverage["generated_concepts"] == 18
    assert coverage["executable_concepts"] == 13
    assert coverage["unsupported_concepts"] == 5
    assert coverage["coverage_status"] == "HIGH"
    assert "density_modulation" in coverage["unsupported_operations"]
    assert "connect_components" in coverage["supported_operations"]
    assert "duplicate_object" in coverage["supported_operations"]
    assert "preserve_grid" in coverage["supported_operations"]
    assert "preserve_shape" in coverage["supported_operations"]


def test_cognitive_capability_coverage_reports_pipeline_bottlenecks():
    state = _state()
    state["TRANSFORMATION_SYNTHESIS_REPORT"] = {
        "detected_concepts": [
            "path_finding",
            "route_completion",
            "growth",
            "position_preservation",
        ],
    }
    state["PROGRAM_GENERATION_REPORT"] = {
        "generated_programs": 2,
        "eligible_concepts": 2,
        "generated_blueprints": 2,
        "missing_requirements": ["compiler_support"],
    }
    state["CANDIDATE_PROPOSAL_REPORT"] = {
        "proposal_phase_entered": True,
        "eligible_source_count": 1,
        "proposal_count": 1,
        "candidate_proposals": [
            {
                "source": "program_generation",
                "proposal_status": "PROPOSED",
                "operation": "construct_path",
            }
        ],
        "sources_with_proposals": ["program_generation"],
    }
    state["COGNITIVE_CANDIDATE_ARENA_REPORT"] = {
        "candidate_arena_summary": {
            "arena_state": "SINGLE_SOURCE_ONLY",
            "candidate_count": 1,
            "unique_candidate_count": 1,
            "source_count": 1,
            "sources_entered": ["normalized_program_candidates"],
            "candidate_summary": [
                {
                    "source": "normalized_program_candidates",
                    "candidate_id": "semantic_program:path_finding",
                    "operation": "construct_path",
                    "entered_arena": True,
                }
            ],
            "selection_mode": "EVIDENCE_BASED_ARENA",
        }
    }
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": False,
        "failure_reason": "no_supported_compiler_for_execution_intents",
        "compiler_failure_diagnostics": {
            "failure_reason_counts": {
                "operation_semantics_mismatch": 2,
                "invalid_composition": 1,
            },
            "failure_domain_distribution": {
                "Spatial": 2,
                "Topology": 1,
            },
            "failure_rows": [
                {
                    "operation": "preserve_grid",
                    "program": "semantic_program_preserve_grid",
                    "semantic_intent": "object_identity_preservation",
                    "expected_operation": "preserve_grid",
                    "resolved_operation": "translate",
                    "failure_stage": "semantic_operation_resolution",
                    "domain": "Spatial",
                    "reason": "operation_semantics_mismatch",
                    "compiler_rule": "RULE_GRID_PRESERVATION_01",
                    "detail": "candidate_not_emitted:preserve_grid",
                }
            ],
        },
    }
    state["EXECUTABLE_INTELLIGENCE_REPORT"] = {
        "compiled_programs": 1,
        "validated_programs": 1,
    }
    state["OPERATIONAL_CAPABILITY_MATERIALIZATION_REPORT"] = {
        "materialized_operational_capabilities": 0,
        "known_operational_capability_count": 2,
        "known_operational_operations": ["replace_color", "duplicate_object"],
        "known_operational_domain_count": 2,
        "known_operational_domains": ["Color", "Growth"],
        "operational_experience_count": 10,
        "operational_experience_task_count": 10,
        "reuse_evidence_count": 8,
        "independent_reuse_success_count": 8,
        "operational_capability_experience_distribution": [
            {
                "operation": "replace_color",
                "domain": "Color",
                "experience_count": 8,
                "independent_reuse_success_count": 7,
            },
            {
                "operation": "duplicate_object",
                "domain": "Growth",
                "experience_count": 2,
                "independent_reuse_success_count": 1,
            },
        ],
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    coverage = result["field_bindings"][
        "cognitive_capability_coverage_summary"
    ]["value"]

    assert coverage["generated_concepts"] == 4
    assert coverage["compiler_coverage"] == 0.5
    assert coverage["candidate_coverage"] == 0.5
    assert coverage["validated_executable_coverage"] == 0.25
    assert coverage["compiler_diagnostic_state"] == (
        "COMPILER_BOTTLENECK_DIAGNOSED"
    )
    assert coverage["compiler_failure_reason_distribution"][
        "operation_semantics_mismatch"
    ] == 2
    assert coverage["compiler_failure_domain_distribution"]["Spatial"] == 2
    assert coverage["compiler_failure_rows"][0]["operation"] == "preserve_grid"
    assert coverage["compiler_failure_rows"][0]["program"] == "semantic_program_preserve_grid"
    assert coverage["compiler_failure_rows"][0]["expected_operation"] == "preserve_grid"
    assert coverage["compiler_failure_rows"][0]["resolved_operation"] == "translate"
    assert coverage["compiler_failure_rows"][0]["failure_stage"] == "semantic_operation_resolution"
    assert coverage["compiler_failure_rows"][0]["compiler_rule"] == "RULE_GRID_PRESERVATION_01"
    assert "execution_package_health_score" in coverage
    assert "primitive_operation_coverage" in coverage
    assert "compiler_infrastructure_health" in coverage
    assert "multi_step_program_support" in coverage
    assert "execution_package_dependency_coverage" in coverage
    assert "primitive_infrastructure_coverage" in coverage
    assert "compiler_primitive_success_rate" in coverage
    assert "execution_package_utilization" in coverage
    assert "compiler_infrastructure_readiness" in coverage

    assert coverage["operational_capability_coverage"] == 0.0
    assert coverage["operational_capability_materialization_rate"] == 0.0
    assert coverage["knowledge_production_efficiency"] == 0.25
    assert coverage["knowledge_operationalization_efficiency"] == 0.0
    assert coverage["operational_knowledge_waste"] == 1.0
    assert coverage["operational_yield_stability"] == 0.8
    assert coverage["operational_yield_stability_basis"] == "experience_reuse_proxy"
    assert coverage["operational_yield_health_state"] == "LOW"
    assert coverage["operational_investment_accuracy"] is None
    assert coverage["operational_investment_accuracy_state"] == "NOT_MEASURABLE"
    assert coverage["high_value_operational_false_positives"] == 0
    assert coverage["validation_efficiency"] == 1.0
    assert coverage["high_value_validation_yield"] is None
    assert coverage["validation_bottleneck_inflation"] is None
    assert coverage["validation_bottleneck_state"] == "NOT_MEASURABLE"
    assert coverage["operational_capability_acquisition_rate"] == 0.2
    assert coverage["capability_survival_rate"] is None
    assert coverage["incubating_operational_capability_count"] == 0
    assert coverage["operational_citizen_count"] == 0
    assert coverage["target_experience_per_capability"] == 3
    assert coverage["expected_operational_capability_count"] == 4
    assert coverage["capability_population_evolution_gap"] == 2
    assert coverage["capability_population_evolution_speed"] == 0.5
    assert coverage["operational_experience_growth_speed"] == 1.0
    assert coverage["capability_population_evolution_lag"] == 0.5
    assert coverage["capability_population_evolution_state"] == "EVOLUTION_LAG"
    assert coverage["operational_specialization_pressure"] == "HIGH"
    assert coverage["current_operational_exploration_rate"] == 1.0
    assert coverage["current_operational_exploitation_rate"] == 0.0
    assert coverage["known_operational_candidate_count"] == 0
    assert coverage["novel_operational_candidate_count"] == 1
    assert coverage["historical_exploitation_bias"] == 0.8
    assert (
        coverage["exploration_exploitation_balance_state"]
        == "HISTORICAL_EXPLOITATION_BIAS_WITH_ACTIVE_EXPLORATION"
    )
    assert coverage["capability_monopoly_share"] == 0.8
    assert coverage["capability_monopoly_pressure"] == "HIGH"
    assert coverage["dominant_operational_capability"] == "replace_color"
    assert coverage["experienced_capability_count"] == 2
    assert coverage["independent_reuse_capability_count"] == 2
    assert coverage["materialized_operational_capabilities"] == 0
    assert (
        coverage["end_to_end_program_lifecycle"][
            "secondary_operationalization_bottleneck"
        ]
        == "capability_population_diversification"
    )
    assert (
        coverage["end_to_end_program_lifecycle"][
            "current_run_materialization_gap"
        ]
        == "capability_materialization"
    )
    assert coverage["missing_compiler_requirements"] == ["compiler_support"]
    assert coverage["candidate_attrition_summary"]["generated_candidates"] == 1
    assert coverage["candidate_attrition_summary"]["entered_arena"] == 1
    assert coverage["candidate_attrition_summary"]["arena_acceptance_rate"] == 1.0
    domain_summary = coverage["cognitive_domain_architecture_summary"]
    assert domain_summary["domain_count"] >= 1
    assert any(
        row["domain_name"] == "Spatial Cognitive Domain"
        for row in domain_summary["domain_rows"]
    )
    assert "domain_operationalization_gaps" in domain_summary
    assert coverage["candidate_source_lineage"][0]["raw_source"] == (
        "program_generation"
    )
    assert coverage["candidate_source_lineage"][0]["arena_source"] == (
        "normalized_program_candidates"
    )


def test_compiler_failure_diagnostics_synthesize_rows_from_aggregates():
    state = _state()
    state["PROGRAM_GENERATION_REPORT"] = {
        "generated_programs": 4,
        "generated_blueprints": 4,
    }
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": False,
        "compiler_failure_diagnostics": {
            "failure_reason_counts": {
                "operation_semantics_mismatch": 6,
                "missing_primitive": 1,
            },
            "failure_domain_distribution": {
                "Spatial": 5,
                "Topology": 2,
            },
            "failure_rows": [],
        },
    }
    state["EXECUTABLE_INTELLIGENCE_REPORT"] = {
        "compiler_runtime_activated_programs": 4,
        "compiled_programs": 1,
        "validated_programs": 1,
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    coverage = result["field_bindings"][
        "cognitive_capability_coverage_summary"
    ]["value"]

    assert coverage["compiler_failure_detail_capture_state"] == (
        "SYNTHETIC_FAILURE_ROWS_FROM_AGGREGATES"
    )
    row = coverage["compiler_failure_rows"][0]
    assert row["operation"] == "unresolved_compiler_attempt"
    assert row["program"] == "unresolved_compiler_attempt"
    assert row["semantic_intent"] == "unknown"
    assert row["expected_operation"] == "unresolved_compiler_attempt"
    assert row["resolved_operation"] == "unresolved_compiler_attempt"
    assert row["failure_stage"] == "compiler_failure_aggregation"
    assert row["domain"] == "Spatial"
    assert row["reason"] == "missing_primitive"
    assert row["compiler_rule"] == "RULE_NOT_CAPTURED"
    assert row["detail"] == "compiler_failure_detail_not_captured"
    assert row["diagnostic_row_source"] == "aggregate_failure_distribution"


def test_compiler_failure_diagnostics_distinguish_placeholder_rows():
    state = _state()
    state["PROGRAM_GENERATION_REPORT"] = {
        "generated_programs": 4,
        "generated_blueprints": 4,
    }
    state["semantic_to_transformation_compilation_report"] = {
        "semantic_to_transformation_compilation_success": False,
        "compiler_failure_diagnostics": {
            "failure_reason_counts": {
                "operation_semantics_mismatch": 1,
            },
            "failure_domain_distribution": {
                "Spatial": 1,
            },
            "failure_rows": [
                {
                    "trace_id": (
                        "compiler_trace:unresolved_compiler_attempt:"
                        "unresolved_compiler_attempt:unresolved_compiler_attempt"
                    ),
                    "program": "semantic_program_unresolved_compiler_attempt",
                    "semantic_intent": "unresolved_compiler_attempt",
                    "operation": "unresolved_compiler_attempt",
                    "expected_operation": "unresolved_compiler_attempt",
                    "resolved_operation": "unresolved_compiler_attempt",
                    "failure_stage": "compiler_failure_diagnostics",
                    "domain": "Spatial",
                    "reason": "operation_semantics_mismatch",
                    "compiler_rule": "RULE_NOT_CAPTURED",
                    "detail": "compiler_failure_detail_not_captured",
                }
            ],
        },
    }
    state["EXECUTABLE_INTELLIGENCE_REPORT"] = {
        "compiler_runtime_activated_programs": 2,
        "compiled_programs": 1,
        "validated_programs": 1,
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    coverage = result["field_bindings"][
        "cognitive_capability_coverage_summary"
    ]["value"]

    assert coverage["compiler_failure_detail_capture_state"] == (
        "STRUCTURED_PLACEHOLDER_ROWS_CAPTURED"
    )


def test_capability_survival_metrics_are_bound_from_materialization_report():
    state = _state()
    state["PROGRAM_GENERATION_REPORT"] = {
        "generated_programs": 3,
        "generated_blueprints": 3,
        "knowledge_investment_summary": {
            "high_value_knowledge_items": 2,
        },
    }
    state["CANDIDATE_PROPOSAL_REPORT"] = {
        "proposal_count": 3,
        "candidate_proposals": [
            {
                "source": "program_generation",
                "proposal_status": "PROPOSED",
                "operation": "construct_path",
            },
            {
                "source": "program_generation",
                "proposal_status": "PROPOSED",
                "operation": "preserve_topology",
            },
            {
                "source": "program_generation",
                "proposal_status": "PROPOSED",
                "operation": "replace_color",
            },
        ],
    }
    state["COGNITIVE_CANDIDATE_ARENA_REPORT"] = {
        "candidate_arena_summary": {
            "selection_mode": "EVIDENCE_BASED_ARENA",
            "candidate_count": 3,
            "unique_candidate_count": 3,
            "sources_entered": ["normalized_program_candidates"],
            "candidate_summary": [],
        },
    }
    state["OPERATIONAL_CAPABILITY_MATERIALIZATION_REPORT"] = {
        "materialized_operational_capabilities": 0,
        "known_operational_capability_count": 1,
        "known_operational_operations": ["replace_color"],
        "known_operational_domain_count": 1,
        "operational_experience_count": 6,
        "operational_experience_task_count": 6,
        "reuse_evidence_count": 5,
        "independent_reuse_success_count": 5,
        "capability_survival_rate": 0.125,
        "materialization_survival_rate": 0.25,
        "incubating_operational_capability_count": 3,
        "operational_citizen_count": 1,
        "validation_bottleneck_inflation": 0.75,
        "validation_bottleneck_state": "SEVERE_VALIDATION_BOTTLENECK",
        "unresolved_validation_gap_candidate_count": 2,
        "operational_citizen_domain_distribution": {
            "Color": 1,
            "Identity": 1,
        },
        "dominant_operational_domain": "Color",
        "domain_monopoly_share": 0.5,
        "domain_operational_imbalance_state": "DOMAIN_IMBALANCE",
        "capability_stability_regression_count": 1,
        "crystallization_candidate_count": 2,
        "quality_to_citizen_crystallization_rate": 0.5,
        "candidate_to_citizen_crystallization_rate": 0.125,
        "generated_to_citizen_pressure_ratio": 8.0,
        "capability_crystallization_state": "SEVERE_CRYSTALLIZATION_FAILURE",
        "capability_graduation_candidate_count": 1,
        "capability_graduation_pressure": 0.92,
        "capability_graduation_pressure_state": "HIGH",
        "world_governance_graduation_action": "GRADUATION_SPRINT_REQUIRED",
        "capability_graduation_health": 0.8125,
        "graduation_pipeline_health": "BACKLOGGED",
        "graduation_success_rate": 0.5,
        "graduation_failure_rate": 0.3333,
        "graduation_queue_health": "HEALTHY",
        "graduation_evidence_coverage": 0.8,
        "graduation_infrastructure_readiness": "READY",
        "average_capability_graduation_time": 17.0,
        "graduation_backlog_size": 1,
        "capability_graduation_queue_health": "HEALTHY",
        "capability_graduation_risk": "MEDIUM",
        "capability_graduation_complexity": "MEDIUM",
        "capability_graduation_confidence": 0.9444,
        "graduation_pipeline_stages": {
            "INCUBATING_VALIDATION_GAP": 2,
            "SURVIVING_CAPABILITY": 1,
            "COGNITIVE_CITIZEN": 0,
            "OPERATIONAL_CITIZEN": 1,
        },
        "graduation_transition_rows": [
            {
                "transition": (
                    "SURVIVING_CAPABILITY->COGNITIVE_CITIZEN"
                ),
                "source_count": 1,
                "target_count": 0,
                "stuck_count": 1,
                "stuck_reasons": {
                    "exact_or_governed_validation_success": 1,
                },
                "success_rate": 0.0,
                "average_graduation_time": 17.0,
            }
        ],
        "capability_graduation_diagnostics": [
            {
                "capability_id": (
                    "operational_capability:spatial:translate:spatial_reasoning"
                ),
                "operation": "translate",
                "graduation_status": "BLOCKED_AT_FINAL_VALIDATION",
                "validator_gap": "GOVERNED_VALIDATION_INCOMPLETE",
                "priority_missing_evidence": (
                    "exact_or_governed_validation_success"
                ),
            }
        ],
        "top_graduation_priority": {
            "capability_id": (
                "operational_capability:spatial:translate:spatial_reasoning"
            ),
            "operation": "translate",
        },
        "graduation_sprint_recommendations": [
            {
                "capability_id": (
                    "operational_capability:spatial:translate:spatial_reasoning"
                ),
                "operation": "translate",
                "priority": 0.9444,
                "minimum_required_evidence": (
                    "exact_or_governed_validation_success"
                ),
                "recommended_validation_type": "exact_or_governed_validation",
                "recommended_training_signal": (
                    "validator_acceptance_task_for:translate"
                ),
                "can_graduate_in_single_run": True,
                "estimated_runs_required": 1,
            }
        ],
        "validator_failure_distribution": {
            "GOVERNED_VALIDATION_INCOMPLETE": 1,
        },
        "top_graduation_candidates": [
            {
                "capability_id": "operational_capability:spatial:translate:spatial_reasoning",
                "operation": "translate",
                "domain": "Spatial",
                "lifecycle_state": "SURVIVING_CAPABILITY",
                "distinct_task_count": 17,
                "arena_quality_count": 16,
                "best_accuracy": 0.9444,
                "average_accuracy": 0.7772,
                "improvement_trend": "IMPROVING",
                "graduation_score": 0.92,
                "missing_graduation_evidence": "exact_or_governed_validation_success",
                "world_governance_graduation_action": "GRADUATION_SPRINT_REQUIRED",
            }
        ],
        "world_governance_promotion_policy_state": "RELAX_SANDBOX_CITIZENSHIP",
        "sandbox_citizenship_thresholds": {
            "min_distinct_tasks": 3,
            "min_arena_quality_count": 3,
            "min_average_accuracy": 0.8,
            "min_best_accuracy": 0.0,
            "allowed_trends": [
                "STABLE",
                "IMPROVING",
                "STABLE_HIGH_PERFORMANCE",
                "DECLINING_MINOR",
            ],
        },
        "trusted_capability_policy": {
            "policy_state": "STRICT_REVIEW_REQUIRED",
            "min_distinct_tasks": 10,
        },
        "decision_authority_policy": {
            "policy_state": "SEPARATE_AUTHORITY_REVIEW_REQUIRED",
            "automatic_authority_transfer": False,
        },
        "generated_survival_candidate_count": 8,
        "arena_simulated_survival_candidate_count": 7,
        "arena_quality_survival_candidate_count": 2,
        "capability_survival_store_path": "runtime/test_survival.json",
        "capability_survival_state_distribution": {
            "GENERATED_CANDIDATE": 1,
            "ARENA_SIMULATED": 5,
            "INCUBATING_VALIDATION_GAP": 2,
            "SURVIVING_CAPABILITY": 0,
            "OPERATIONAL_CITIZEN": 1,
        },
        "top_incubating_capabilities": [
            {
                "capability_id": "operational_capability:topology:construct_path:path",
                "operation": "construct_path",
                "domain": "Topology",
                "lifecycle_state": "INCUBATING_VALIDATION_GAP",
                "distinct_task_count": 2,
                "arena_simulated_count": 3,
                "best_accuracy": 0.67,
                "average_accuracy": 0.52,
                "validation_attempts": 2,
                "improvement_trend": "IMPROVING",
                "next_required_evidence": "repeatable_validation_across_independent_task",
            }
        ],
        "top_operational_citizens": [
            {
                "capability_id": "operational_capability:identity:preserve_grid:object_identity_preservation",
                "operation": "preserve_grid",
                "domain": "Identity",
                "lifecycle_state": "OPERATIONAL_CITIZEN",
                "distinct_task_count": 3,
                "arena_simulated_count": 3,
                "best_accuracy": 0.9722,
                "average_accuracy": 0.9241,
                "citizenship_basis": "sandbox_governed_survival_evidence",
                "trusted_for_decision": False,
            }
        ],
        "top_crystallization_candidates": [
            {
                "capability_id": "operational_capability:spatial:preserve_shape:shape_preservation",
                "operation": "preserve_shape",
                "domain": "Spatial",
                "lifecycle_state": "INCUBATING_VALIDATION_GAP",
                "distinct_task_count": 3,
                "arena_quality_count": 3,
                "best_accuracy": 0.96,
                "average_accuracy": 0.84,
                "improvement_trend": "STABLE",
                "next_required_evidence": "repeatable_validation_across_independent_task",
            }
        ],
        "cognitive_citizen_count": 1,
        "cognitive_citizenship_definition": (
            "independent_high_quality_sandbox_evidence_without_decision_authority"
        ),
        "top_cognitive_citizens": [
            {
                "capability_id": "operational_capability:spatial:preserve_grid:object_identity_preservation",
                "operation": "preserve_grid",
                "domain": "Spatial",
                "lifecycle_state": "ARENA_SIMULATED",
                "distinct_task_count": 9,
                "arena_quality_count": 8,
                "best_accuracy": 0.9722,
                "average_accuracy": 0.8092,
                "improvement_trend": "STABLE_HIGH_PERFORMANCE",
            }
        ],
        "top_stability_regressions": [
            {
                "capability_id": "operational_capability:spatial:preserve_grid:object_identity_preservation",
                "operation": "preserve_grid",
                "domain": "Spatial",
                "lifecycle_state": "SURVIVING_CAPABILITY",
                "stability_state": "STABILITY_REGRESSION",
                "distinct_task_count": 6,
                "average_accuracy": 0.7763,
                "next_required_evidence": "stability_recovery_evidence",
            }
        ],
        "capability_survival_report": {
            "validation_gap_candidate_count": 6,
            "capability_survival_rows": [
                {
                    "operation": "construct_path",
                    "lifecycle_state": "INCUBATING_VALIDATION_GAP",
                },
            ],
        },
    }

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    coverage = result["field_bindings"][
        "cognitive_capability_coverage_summary"
    ]["value"]

    assert coverage["capability_survival_rate"] == 0.125
    assert coverage["materialization_survival_rate"] == 0.25
    assert coverage["candidate_retention_rate"] == 0.875
    assert coverage["incubation_conversion_rate"] == 0.375
    assert coverage["surviving_capability_conversion_rate"] == 0.0
    assert coverage["operational_citizen_conversion_rate"] == 0.125
    assert coverage["current_run_operational_citizen_count"] == 1
    assert coverage["historical_operational_citizen_count"] == 1
    assert coverage["expected_operational_domain_citizen_count"] == 7
    assert coverage["historical_operational_domain_citizen_count"] == 1
    assert coverage["sandbox_operational_domain_citizen_count"] == 2
    assert coverage["operational_domain_citizen_count"] == 2
    assert coverage["operational_domain_citizenship_coverage"] == 0.2857
    assert coverage["operational_citizen_domain_distribution"] == {
        "Color": 1,
        "Identity": 1,
    }
    assert coverage["historical_operational_domain_distribution"] == {
        "Color": 1,
    }
    assert coverage["sandbox_operational_domain_distribution"] == {
        "Color": 1,
        "Identity": 1,
    }
    assert coverage["combined_operational_domain_distribution"] == {
        "Color": 2,
        "Identity": 1,
    }
    assert coverage["dominant_operational_domain"] == "Color"
    assert coverage["domain_monopoly_share"] == 0.6667
    assert coverage["domain_operational_imbalance_state"] == "DOMAIN_MONOPOLY"
    assert "operational_domain_health" in coverage
    assert "operational_domain_coverage" in coverage
    assert "domain_operationalization_score" in coverage
    assert "domain_operationalization_bottleneck" in coverage
    assert "domain_population_balance" in coverage
    assert "domain_collaboration_score" in coverage
    assert "domain_primitive_coverage" in coverage
    assert "domain_infrastructure_readiness" in coverage
    assert "capability_ecology_health" in coverage
    assert "capability_cooperation_score" in coverage
    assert "capability_composition_score" in coverage
    assert "composite_capability_score" in coverage
    assert "capability_synergy_matrix" in coverage
    assert "composite_capability_candidates" in coverage
    assert "capability_economy_health" in coverage
    assert "capability_specialization_report" in coverage
    assert "operational_economy_health" in coverage
    assert "knowledge_attrition_lifecycle" in coverage
    assert "knowledge_attrition_state" in coverage
    assert "operational_investment_return" in coverage
    assert "capability_economy_crisis_state" in coverage
    assert "operational_capability_clusters" in coverage
    assert "operational_economy_roadmap" in coverage
    assert coverage["operational_domain_population"] >= 1
    assert coverage["domain_expansion_roadmap"]
    assert coverage["operational_domain_diagnostics"]
    assert coverage["surviving_capability_domain_count"] == 0
    assert coverage["generated_survival_candidate_count"] == 8
    assert coverage["arena_simulated_survival_candidate_count"] == 7
    assert coverage["arena_quality_survival_candidate_count"] == 2
    assert coverage["incubating_operational_capability_count"] == 3
    assert coverage["operational_citizen_count"] == 1
    assert coverage["validation_bottleneck_inflation"] == 0.75
    assert coverage["validation_bottleneck_state"] == (
        "SEVERE_VALIDATION_BOTTLENECK"
    )
    assert coverage["validation_gap_candidate_count"] == 6
    assert coverage["unresolved_validation_gap_candidate_count"] == 2
    assert coverage["capability_stability_regression_count"] == 1
    assert coverage["crystallization_candidate_count"] == 2
    assert coverage["quality_to_citizen_crystallization_rate"] == 0.5
    assert coverage["candidate_to_citizen_crystallization_rate"] == 0.125
    assert coverage["generated_to_citizen_pressure_ratio"] == 8.0
    assert coverage["capability_crystallization_state"] == (
        "SEVERE_CRYSTALLIZATION_FAILURE"
    )
    assert coverage["capability_graduation_candidate_count"] == 1
    assert coverage["capability_graduation_pressure"] == 0.92
    assert coverage["capability_graduation_pressure_state"] == "HIGH"
    assert coverage["world_governance_graduation_action"] == (
        "GRADUATION_SPRINT_REQUIRED"
    )
    assert coverage["capability_graduation_health"] == 0.8125
    assert coverage["graduation_pipeline_health"] == "BACKLOGGED"
    assert coverage["graduation_success_rate"] == 0.5
    assert coverage["graduation_failure_rate"] == 0.3333
    assert coverage["graduation_queue_health"] == "HEALTHY"
    assert coverage["graduation_evidence_coverage"] == 0.8
    assert coverage["graduation_infrastructure_readiness"] == "READY"
    assert coverage["average_capability_graduation_time"] == 17.0
    assert coverage["graduation_backlog_size"] == 1
    assert coverage["capability_graduation_risk"] == "MEDIUM"
    assert coverage["capability_graduation_complexity"] == "MEDIUM"
    assert coverage["capability_graduation_confidence"] == 0.9444
    assert coverage["graduation_pipeline_stages"][
        "SURVIVING_CAPABILITY"
    ] == 1
    assert coverage["graduation_transition_rows"][0]["stuck_count"] == 1
    assert coverage["capability_graduation_diagnostics"][0][
        "validator_gap"
    ] == "GOVERNED_VALIDATION_INCOMPLETE"
    assert coverage["top_graduation_priority"]["operation"] == "translate"
    assert coverage["graduation_sprint_recommendations"][0][
        "recommended_validation_type"
    ] == "exact_or_governed_validation"
    assert coverage["validator_failure_distribution"] == {
        "GOVERNED_VALIDATION_INCOMPLETE": 1,
    }
    assert coverage["top_graduation_candidates"][0]["operation"] == "translate"
    assert coverage["top_graduation_candidates"][0][
        "missing_graduation_evidence"
    ] == "exact_or_governed_validation_success"
    assert coverage["world_governance_promotion_policy_state"] == (
        "RELAX_SANDBOX_CITIZENSHIP"
    )
    assert coverage["sandbox_citizenship_thresholds"][
        "min_average_accuracy"
    ] == 0.8
    assert coverage["trusted_capability_policy"]["policy_state"] == (
        "STRICT_REVIEW_REQUIRED"
    )
    assert coverage["decision_authority_policy"][
        "automatic_authority_transfer"
    ] is False
    assert coverage["capability_survival_store_path"] == (
        "runtime/test_survival.json"
    )
    assert coverage["capability_survival_state_distribution"][
        "ARENA_SIMULATED"
    ] == 5
    assert coverage["top_incubating_capabilities"][0]["operation"] == (
        "construct_path"
    )
    assert coverage["top_operational_citizens"][0]["operation"] == (
        "preserve_grid"
    )
    assert coverage["top_operational_citizens"][0]["trusted_for_decision"] is False
    assert coverage["top_crystallization_candidates"][0]["operation"] == (
        "preserve_shape"
    )
    assert coverage["cognitive_citizen_count"] == 1
    assert coverage["cognitive_citizenship_definition"] == (
        "independent_high_quality_sandbox_evidence_without_decision_authority"
    )
    assert coverage["top_cognitive_citizens"][0]["operation"] == "preserve_grid"
    assert coverage["top_stability_regressions"][0]["next_required_evidence"] == (
        "stability_recovery_evidence"
    )


def test_canonical_timing_bindings_use_existing_timing_sources():
    result = CanonicalReportBindingEngine().bind(
        _state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )
    fields = result["field_bindings"]

    assert fields["stage_timing_summary"]["canonical_source"] == "execution_timing_state"
    assert fields["runtime_timing_summary"]["canonical_source"] == "execution_timing_state"
    assert fields["top_time_consumers"]["canonical_source"] == "execution_timing_state"
    assert fields["active_compute_time"]["value"] == 17.0
    assert fields["untracked_time"]["value"] == 1.0
    assert fields["timing_coverage"]["display_value"] == "95%"
    stage_rows = fields["stage_timing_summary"]["value"]
    assert all(row["duration_seconds"] >= 0.0 for row in stage_rows)
    assert not any(row["stage_name"] == "Governance" for row in stage_rows)
    assert not any(row["duration_seconds"] == 99.0 for row in stage_rows)
    assert len({row["stage_name"] for row in stage_rows}) == len(stage_rows)
    assert stage_rows[0]["relationship_type"] == "ROOT"
    ranking = fields["resource_consumption_ranking"]["value"]
    assert [row["exclusive_duration"] for row in ranking] == sorted(
        [row["exclusive_duration"] for row in ranking],
        reverse=True,
    )
    assert sum(row["percentage_of_active_compute"] for row in ranking) <= 100.0001
    assert fields["top_time_consumers"]["value"][0]["stage_name"] == "Program Synthesis"


def test_timing_not_available_only_when_source_genuinely_missing():
    state = _state()
    state.pop("execution_timing")
    state["performance_report"] = {}

    result = CanonicalReportBindingEngine().bind(
        state,
        runtime_metadata={},
        report_level="normal",
    )

    assert result["field_bindings"]["active_compute_time"]["binding_status"] == (
        BindingState.NOT_AVAILABLE.value
    )
    assert result["field_bindings"]["stage_timing_summary"]["binding_status"] == (
        BindingState.BOUND.value
    )
    assert result["field_bindings"]["stage_timing_summary"]["value"] == []
