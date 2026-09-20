from runtime.program_generation import ProgramGenerationLayer


def test_program_generation_creates_blueprint_for_supported_concept():
    lifecycle = {
        "concept_lifecycles": [
            {
                "concept_name": "rotation",
                "semantic_cluster": "Geometry",
                "compiler_supported": "TRUE",
                "execution_package_available": "TRUE",
                "lifecycle_status": "DISCOVERED",
            },
        ],
    }

    report = ProgramGenerationLayer().generate(lifecycle)
    blueprint = report["program_blueprints"][0]

    assert report["generated_programs"] == 1
    assert report["eligible_concepts"] == 1
    assert report["generation_success_rate"] == 1.0
    assert blueprint["program_type"] == "rotation_program"
    assert blueprint["generation_status"] == "GENERATED"
    assert blueprint["generation_attempted"] == "TRUE"
    assert blueprint["generation_success"] == "TRUE"
    assert blueprint["executable"] == "TRUE"
    assert blueprint["candidate_ready"] == "FALSE"
    assert blueprint["missing_requirements"] == ["candidate_proposal_support"]
    assert report["execution_agnostic"] is True
    assert report["competition_agnostic"] is True


def test_program_generation_blocks_compiler_supported_concept_without_execution_package():
    lifecycle = {
        "concept_lifecycles": [
            {
                "concept_name": "gravity",
                "semantic_cluster": "Physics",
                "compiler_supported": "TRUE",
                "execution_package_available": "FALSE",
                "lifecycle_status": "DISCOVERED_BUT_NOT_EXECUTABLE",
            },
        ],
    }

    report = ProgramGenerationLayer().generate(lifecycle)
    blueprint = report["program_blueprints"][0]

    assert report["generated_programs"] == 0
    assert report["eligible_concepts"] == 1
    assert report["blocked_programs"] == 1
    assert blueprint["program_type"] == "gravity_program"
    assert blueprint["generation_status"] == "BLOCKED"
    assert blueprint["blocking_reason"] == "NO_EXECUTION_PACKAGE"
    assert blueprint["missing_requirements"] == ["gravity_execution_package"]
    assert blueprint["candidate_ready"] == "FALSE"


def test_program_generation_rejects_compiler_unsupported_concepts_explicitly():
    lifecycle = {
        "concept_lifecycles": [
            {
                "concept_name": "unsupported_signal",
                "semantic_cluster": "Context",
                "compiler_supported": "FALSE",
                "execution_package_available": "UNKNOWN",
                "lifecycle_status": "DISCOVERED_BUT_NOT_COMPILABLE",
            },
        ],
    }

    report = ProgramGenerationLayer().generate(lifecycle)
    blueprint = report["program_blueprints"][0]

    assert report["eligible_concepts"] == 0
    assert blueprint["generation_status"] == "NOT_ELIGIBLE"
    assert blueprint["generation_attempted"] == "FALSE"
    assert blueprint["blocking_reason"] == "NO_COMPILER_SUPPORT"
    assert blueprint["missing_requirements"] == ["compiler_support"]
