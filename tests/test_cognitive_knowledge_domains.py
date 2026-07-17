from runtime.knowledge import CognitiveKnowledgeDomainRegistry


def test_cognitive_knowledge_domains_organize_gravity_lifecycle():
    report = CognitiveKnowledgeDomainRegistry().build(
        concept_lifecycle_report={
            "concept_lifecycles": [
                {
                    "concept_name": "gravity",
                    "semantic_cluster": "Physics",
                    "mental_model": "Gravity Simulation",
                    "execution_package_available": "FALSE",
                    "missing_requirements": ["gravity_execution_package"],
                },
                {
                    "concept_name": "falling",
                    "semantic_cluster": "Physics",
                    "mental_model": "Gravity Simulation",
                    "execution_package_available": "FALSE",
                    "missing_requirements": ["gravity_execution_package"],
                },
            ],
        },
        program_blueprint_intelligence_report={
            "program_blueprint_intelligence": [
                {
                    "program_type": "gravity_program",
                    "semantic_family": "Physics",
                    "mental_model": "Gravity Simulation",
                    "supported_concepts": [
                        "gravity",
                        "falling",
                        "support",
                        "collision",
                        "rest_state",
                    ],
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
        },
        cognitive_program_lifecycle_report={
            "program_registry": [
                {
                    "program_type": "gravity_program",
                    "semantic_family": "Physics",
                    "supported_concepts": ["gravity", "falling"],
                    "required_packages": [
                        "gravity_execution_package",
                        "gravity_candidate_support",
                    ],
                    "missing_requirements": [
                        "gravity_execution_package",
                        "gravity_candidate_support",
                    ],
                    "capability_profile": {
                        "semantic_capabilities": ["gravity"],
                    },
                },
            ],
        },
    )

    physics = {
        domain["domain_name"]: domain
        for domain in report["domains"]
    }["Physics Domain"]

    assert report["domain_count"] >= 15
    assert report["validation_success"] is True
    assert report["silent_domain_assignment_failures"] is False
    assert report["orphan_concepts"] == []
    assert "gravity" in physics["semantic_concepts"]
    assert "falling" in physics["semantic_concepts"]
    assert "Gravity Simulation" in physics["mental_models"]
    assert "gravity_program" in physics["program_blueprints"]
    assert "gravity_candidate_support" in physics["missing_capabilities"]
    assert physics["maturity_level"] == "DEVELOPING"


def test_cognitive_knowledge_domains_group_topology_family():
    report = CognitiveKnowledgeDomainRegistry().build(
        concept_lifecycle_report={
            "concept_lifecycles": [
                {
                    "concept_name": "component_splitting",
                    "semantic_cluster": "Topology",
                    "mental_model": "Topology Reasoning",
                },
            ],
        },
        program_blueprint_intelligence_report={
            "program_blueprint_intelligence": [
                {
                    "program_type": "topology_program",
                    "semantic_family": "Topology",
                    "mental_model": "Topology Reasoning",
                    "supported_concepts": [
                        "topology_change",
                        "bridge_creation",
                        "connectivity_change",
                    ],
                    "required_packages": ["topology_execution_package"],
                    "missing_requirements": ["topology_candidate_support"],
                    "capability_profile": {
                        "execution_capabilities": ["topology_execution_blueprint"],
                    },
                },
            ],
        },
    )

    topology = {
        domain["domain_name"]: domain
        for domain in report["domains"]
    }["Topology Domain"]

    assert "Topology" in topology["semantic_families"]
    assert "Topology Reasoning" in topology["mental_models"]
    assert "topology_program" in topology["program_blueprints"]
    assert "component_splitting" in topology["semantic_concepts"]
    assert "bridge_creation" in topology["semantic_concepts"]
    assert "topology_execution_package" in topology["execution_packages"]
    assert "topology_candidate_support" in topology["missing_capabilities"]
    assert topology["maturity_level"] == "PARTIALLY_OPERATIONAL"


def test_cognitive_knowledge_domains_keep_future_domains_extensible():
    report = CognitiveKnowledgeDomainRegistry().build(
        program_blueprint_intelligence_report={
            "program_blueprint_intelligence": [
                    {
                        "program_type": "attention_program",
                        "semantic_family": "Attention",
                        "mental_model": "Attention Control",
                        "supported_concepts": ["attention_focus"],
                        "missing_requirements": ["attention_execution_package"],
                    },
            ],
        },
    )

    domains = {domain["domain_name"]: domain for domain in report["domains"]}

    assert "Attention Domain" in domains
    assert domains["Attention Domain"]["semantic_concepts"] == ["attention_focus"]
    assert report["invalid_family_assignments"] == []
    assert report["validation_success"] is True
