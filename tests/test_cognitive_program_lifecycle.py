from runtime.program_generation import CognitiveProgramLifecycleRegistry


def test_cognitive_program_lifecycle_tracks_gravity_blockers():
    report = CognitiveProgramLifecycleRegistry().build({
        "program_blueprint_intelligence": [
            {
                "blueprint_id": "program_intelligence:gravity_program",
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
    })

    lifecycle = report["program_registry"][0]

    assert lifecycle["program_type"] == "gravity_program"
    assert lifecycle["semantic_family"] == "Physics"
    assert lifecycle["lifecycle_status"] == "PACKAGE_REQUIREMENTS_IDENTIFIED"
    assert lifecycle["maturity_level"] == "FOUNDATIONAL"
    assert lifecycle["execution_readiness"] == "NOT_READY"
    assert lifecycle["candidate_readiness"] == "NOT_READY"
    assert lifecycle["operational_readiness"] == "NOT_READY"
    assert "gravity_execution_package" in lifecycle["missing_requirements"]
    assert lifecycle["lifecycle_failures"][0]["failed_stage"] == "EXECUTION_REQUIREMENTS_VALIDATED"
    assert lifecycle["lifecycle_failures"][0]["reason"] == "NO_EXECUTION_PACKAGE"
    assert report["blocked_program_count"] == 1
    assert report["partially_operational_program_count"] == 0
    assert report["silent_lifecycle_failures"] is False


def test_cognitive_program_lifecycle_marks_ready_program_operational():
    report = CognitiveProgramLifecycleRegistry().build({
        "program_blueprint_intelligence": [
            {
                "blueprint_id": "program_intelligence:rotation_program",
                "program_type": "rotation_program",
                "semantic_family": "Transformation",
                "mental_model": "Object Transformation Mental Model",
                "supported_concepts": ["rotation", "orientation_change"],
                "compiler_supported": "TRUE",
                "execution_ready": "EXECUTION_READY",
                "candidate_ready": "READY_FOR_PROPOSAL",
                "validation_ready": "TRUE",
                "required_packages": [
                    "transformation_execution_package",
                    "transformation_candidate_support",
                ],
                "missing_requirements": [],
                "capability_profile": {
                    "semantic_capabilities": ["rotation"],
                    "execution_capabilities": ["transformation_execution_blueprint"],
                },
            },
        ],
    })

    lifecycle = report["program_registry"][0]

    assert lifecycle["lifecycle_status"] == "OPERATIONAL"
    assert lifecycle["maturity_level"] == "FULLY_OPERATIONAL"
    assert lifecycle["execution_readiness"] == "READY"
    assert lifecycle["candidate_readiness"] == "READY"
    assert lifecycle["operational_readiness"] == "READY"
    assert lifecycle["lifecycle_failures"] == []
    assert report["operational_program_count"] == 1
