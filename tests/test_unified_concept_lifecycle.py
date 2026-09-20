from core.concept_lifecycle.unified_concept_lifecycle import (
    UnifiedConceptLifecycleBuilder,
)


def test_unified_concept_lifecycle_tracks_gravity_without_execution_package():
    report = UnifiedConceptLifecycleBuilder().build({
        "semantic_attribution_report": {
            "attributed_concepts": [
                "gravity",
                "falling",
                "collision",
            ],
        },
        "truth_candidate_report": {
            "evaluations": [
                {
                    "concept": "gravity",
                    "eligible_for_truth_candidate": True,
                    "state": "candidate",
                },
            ],
        },
        "semantic_memory_report": {
            "Semantic Entities": [
                {
                    "concept": "gravity",
                    "semantic_memory_id": "sem:gravity",
                    "memory_version": "1",
                    "memory_source": "semantic_memory_engine",
                },
            ],
        },
    })

    gravity = next(
        item for item in report["concept_lifecycles"]
        if item["concept_name"] == "gravity"
    )

    assert gravity["semantic_cluster"] == "Physics"
    assert gravity["mental_model"] == "Gravity Simulation"
    assert gravity["truth_candidate_state"] == "TRUE"
    assert gravity["execution_package_available"] == "FALSE"
    assert gravity["compiler_supported"] == "FALSE"
    assert gravity["program_generated"] == "FALSE"
    assert gravity["candidate_generated"] == "FALSE"
    assert gravity["prediction_contribution"] == "NONE"
    assert gravity["semantic_memory_integrated"] == "TRUE"
    assert gravity["memory_entry_id"] == "sem:gravity"
    assert "Gravity Execution Package" in gravity["missing_requirements"]
    assert gravity["lifecycle_status"] == "DISCOVERED_BUT_NOT_EXECUTABLE"


def test_unified_concept_lifecycle_tracks_operational_rotation():
    report = UnifiedConceptLifecycleBuilder().build({
        "TRANSFORMATION_SYNTHESIS_REPORT": {
            "detected_concepts": ["rotation"],
            "selected_program": {
                "steps": [{"operation": "rotate"}],
                "step_count": 1,
            },
            "semantic_to_transformation_compilation_report": {
                "semantic_to_transformation_compilation_success": True,
                "detected_intents": ["rotation"],
                "compiled_program": {
                    "steps": [{"operation": "rotate"}],
                    "step_count": 1,
                },
            },
        },
        "candidate_proposal_report": {
            "candidate_proposals": [
                {
                    "intent": "rotation",
                    "operation": "rotate",
                    "proposal_status": "PROPOSED",
                },
            ],
        },
        "candidate_arena_summary": {
            "candidate_summary": [
                {
                    "operation": "rotation",
                    "status": "WINNER",
                    "selected": True,
                    "entered_arena": True,
                },
            ],
        },
    })

    rotation = next(
        item for item in report["concept_lifecycles"]
        if item["concept_name"] == "rotation"
    )

    assert rotation["execution_package_available"] == "TRUE"
    assert rotation["compiler_supported"] == "TRUE"
    assert rotation["program_generated"] == "TRUE"
    assert rotation["candidate_generated"] == "TRUE"
    assert rotation["candidate_selected"] == "TRUE"
    assert rotation["prediction_contribution"] == "PRIMARY"
    assert rotation["lifecycle_status"] == "OPERATIONAL"


def test_unified_concept_lifecycle_expands_execution_package_support_without_physics():
    report = UnifiedConceptLifecycleBuilder().build({
        "TRANSFORMATION_SYNTHESIS_REPORT": {
            "detected_concepts": [
                "growth",
                "replication",
                "bridge_creation",
                "directional_motion",
                "object_identity_preservation",
                "gravity",
            ],
        },
    })

    rows = {
        item["concept_name"]: item
        for item in report["concept_lifecycles"]
    }

    for concept in (
        "growth",
        "replication",
        "bridge_creation",
        "directional_motion",
        "object_identity_preservation",
    ):
        assert rows[concept]["execution_package_available"] == "TRUE"
        assert rows[concept]["compiler_supported"] == "TRUE"

    assert rows["gravity"]["execution_package_available"] == "FALSE"
