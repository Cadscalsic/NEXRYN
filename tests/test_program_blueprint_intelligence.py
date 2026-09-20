from runtime.program_generation import ProgramBlueprintIntelligenceLayer


def test_program_blueprint_intelligence_groups_topology_family():
    report = ProgramBlueprintIntelligenceLayer().analyze({
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
    })

    topology = report["program_blueprint_intelligence"][0]

    assert topology["program_type"] == "topology_program"
    assert topology["semantic_family"] == "Topology"
    assert topology["mental_model"] == "Topology Reasoning"
    assert "hole_removal" in topology["supported_concepts"]
    assert "bridge_creation" in topology["supported_concepts"]
    assert topology["compiler_supported"] == "TRUE"
    assert topology["execution_ready"] == "EXECUTION_READY"
    assert topology["candidate_ready"] == "WAITING_FOR_VALIDATION"
    assert "topology_execution_package" in topology["required_packages"]
    assert "topology_candidate_support" in topology["missing_requirements"]
    assert report["validation"]["validation_success"] is True
    assert report["capability_failures_silent"] is False


def test_program_blueprint_intelligence_exposes_gravity_missing_packages():
    report = ProgramBlueprintIntelligenceLayer().analyze({
        "program_blueprints": [
            {
                "program_id": "program_blueprint:gravity",
                "concept_name": "gravity",
                "semantic_cluster": "Physics",
                "program_type": "gravity_program",
                "compiler_supported": "TRUE",
                "generation_success": "FALSE",
                "generation_status": "BLOCKED",
                "execution_package_available": "FALSE",
                "candidate_ready": "FALSE",
                "missing_requirements": ["gravity_execution_package"],
            },
        ],
    })

    gravity = report["program_blueprint_intelligence"][0]

    assert gravity["semantic_family"] == "Physics"
    assert gravity["mental_model"] == "Gravity Simulation"
    assert "falling" in gravity["supported_concepts"]
    assert gravity["execution_ready"] == "MISSING_PACKAGE"
    assert gravity["candidate_ready"] == "WAITING_FOR_EXECUTION_PACKAGE"
    assert "gravity_execution_package" in gravity["required_packages"]
    assert "gravity_candidate_support" in gravity["missing_requirements"]
    assert "execution_package_missing" in gravity["capability_limitations"]
    assert gravity["lifecycle_status"] == "WAITING_FOR_EXECUTION_PACKAGE"
