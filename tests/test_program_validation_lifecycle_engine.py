import pytest

from runtime.validation import (
    ProgramLifecycleError,
    ProgramValidationLifecycleEngine,
)


def _program(program_id="program:a", signature="sig:a", lifecycle="CANDIDATE"):
    return {
        "program_id": program_id,
        "program_name": program_id.replace(":", "_"),
        "program_type": "concept_composition",
        "program_signature": signature,
        "required_concepts": ["concept:a"],
        "required_transformations": ["symbolic_attribute_mapping"],
        "required_constraints": ["concept_alignment_required"],
        "confidence": 0.82,
        "lifecycle": lifecycle,
    }


def test_successful_lifecycle_progression_preserves_history():
    engine = ProgramValidationLifecycleEngine()
    record = engine.register_program(_program())
    program_id = record["program_id"]

    engine.validate_structural(program_id)
    engine.validate_semantic(program_id)
    engine.validate_execution(program_id)
    engine.validate_generalization(program_id)
    engine.approve_program(program_id)
    canonical = engine.canonicalize_program(program_id)

    assert canonical["current_state"] == "CANONICAL"
    assert canonical["approval_status"] == "APPROVED"
    assert canonical["execution_status"] == "PASSED"
    assert canonical["generalization_status"] == "PASSED"
    assert canonical["state_history"] == [
        "NEW",
        "GENERATED",
        "STRUCTURALLY_VALIDATED",
        "SEMANTICALLY_VALIDATED",
        "EXECUTION_VALIDATED",
        "GENERALIZATION_VALIDATED",
        "APPROVED",
        "CANONICAL",
    ]
    assert len(canonical["validation_history"]) == 7


def test_rejected_program_handling_keeps_rejection_analysis():
    engine = ProgramValidationLifecycleEngine()
    program_id = engine.register_program(_program())["program_id"]

    rejected = engine.reject_program(
        program_id,
        reason="operator_invalid",
        failed_stage="structural",
        failed_constraints=("valid_operator",),
        alternative_candidates=("program:b",),
        replacement_program="program:c",
        possible_recovery="swap_operator",
    )

    assert rejected["current_state"] == "REJECTED"
    assert rejected["approval_status"] == "REJECTED"
    assert rejected["rejection_analysis"]["rejection_reason"] == "operator_invalid"
    assert rejected["rejection_analysis"]["failed_validation_stage"] == "structural"
    assert engine.lookup(program_id)["current_state"] == "REJECTED"


def test_duplicate_detection_marks_second_program_without_disappearing():
    engine = ProgramValidationLifecycleEngine()
    original = engine.register_program(_program("program:a", "same-signature"))
    duplicate = engine.register_program(_program("program:b", "same-signature"))

    assert original["current_state"] == "GENERATED"
    assert duplicate["current_state"] == "DUPLICATE"
    assert duplicate["duplicate_of"] == "program:a"
    assert set(engine.registry) == {"program:a", "program:b"}


def test_program_replacement_records_evolution_graph():
    engine = ProgramValidationLifecycleEngine()
    parent = engine.register_program(_program("program:parent", "sig:parent"))
    child = engine.register_program(_program("program:child", "sig:child"))

    replaced = engine.replace_program(parent["program_id"], child["program_id"])
    graph = engine.evolution_graph()

    assert replaced["current_state"] == "SUPERSEDED"
    assert engine.registry["program:child"]["parent_program"] == "program:parent"
    assert {"from": "program:parent", "to": "program:child", "relation": "replaced_by"} in graph["edges"]


def test_program_merging_records_sources_and_target():
    engine = ProgramValidationLifecycleEngine()
    engine.register_program(_program("program:a", "sig:a"))
    engine.register_program(_program("program:b", "sig:b"))
    merged = engine.register_program(_program("program:merged", "sig:merged"))

    result = engine.merge_programs(("program:a", "program:b"), merged["program_id"])

    assert result["merged_from"] == ["program:a", "program:b"]
    assert engine.registry["program:a"]["current_state"] == "MERGED"
    assert engine.registry["program:b"]["merged_program"] == "program:merged"


def test_execution_and_generalization_validation_are_explicit():
    engine = ProgramValidationLifecycleEngine()
    program_id = engine.register_program(_program())["program_id"]
    engine.validate_structural(program_id)
    engine.validate_semantic(program_id)

    executed = engine.validate_execution(
        program_id,
        details={"output_correctness": 1.0, "constraint_satisfaction": 1.0},
    )
    generalized = engine.validate_generalization(
        program_id,
        details={"transfer_success": 0.91, "cross_task_stability": 0.88},
    )

    assert executed["current_state"] == "EXECUTION_VALIDATED"
    assert generalized["current_state"] == "GENERALIZATION_VALIDATED"
    assert generalized["execution_history"]
    assert generalized["generalization_history"]


def test_illegal_transition_rejection():
    engine = ProgramValidationLifecycleEngine()
    program_id = engine.register_program(_program())["program_id"]

    with pytest.raises(ProgramLifecycleError):
        engine.validate_execution(program_id)

    assert engine.registry[program_id]["current_state"] == "GENERATED"
    assert engine.failures[-1]["failure"] == "illegal_transition"


def test_registry_consistency_and_report_counts():
    engine = ProgramValidationLifecycleEngine()
    approved = engine.register_program(_program("program:approved", "sig:approved"))["program_id"]
    rejected = engine.register_program(_program("program:rejected", "sig:rejected"))["program_id"]
    duplicate = engine.register_program(_program("program:duplicate", "sig:approved"))["program_id"]

    engine.validate_structural(approved)
    engine.validate_semantic(approved)
    engine.validate_execution(approved)
    engine.validate_generalization(approved)
    engine.approve_program(approved)
    engine.reject_program(
        rejected,
        reason="truth_incompatible",
        failed_stage="semantic",
        failed_constraints=("truth_alignment_required",),
    )

    report = engine.build_report()

    assert duplicate == "program:duplicate"
    assert report["generated_programs"] == 3
    assert report["approved_programs"] == 1
    assert report["rejected_programs"] == 1
    assert report["duplicate_programs"] == 1
    assert report["pending_programs"] == 0
    assert report["registry_consistency"]["valid"] is True


def test_synthesis_report_enrichment_explains_every_generated_program():
    engine = ProgramValidationLifecycleEngine()
    report = engine.register_from_synthesis_report({
        "generated_programs": 3,
        "generated_program_objects": [
            {
                **_program("program:validated", "sig:validated", "PROMOTED"),
                "validation_results": {"accepted": True},
            },
            _program("program:pending", "sig:pending"),
        ],
        "rejected_programs": [
            {
                "program_id": "program:rejected",
                "program_signature": "sig:rejected",
                "reason": "ranking_score_below_threshold",
            }
        ],
    })

    lifecycle = report["PROGRAM_VALIDATION_LIFECYCLE_REPORT"]

    assert lifecycle["generated_programs"] == 3
    assert lifecycle["approved_programs"] == 1
    assert lifecycle["pending_programs"] == 1
    assert lifecycle["rejected_programs"] == 1
    assert set(report["program_lifecycle_registry"]) == {
        "program:validated",
        "program:pending",
        "program:rejected",
    }


def test_synthesis_report_registers_placeholders_for_unlisted_generated_programs():
    engine = ProgramValidationLifecycleEngine()
    report = engine.register_from_synthesis_report({
        "generated_programs": 3,
        "generated_program_objects": [
            _program("program:listed", "sig:listed"),
        ],
    })

    lifecycle = report["PROGRAM_VALIDATION_LIFECYCLE_REPORT"]

    assert lifecycle["generated_programs"] == 3
    assert lifecycle["pending_programs"] == 3
    assert "program:listed" in report["program_lifecycle_registry"]
    assert "program:generated:0" in report["program_lifecycle_registry"]
    assert "program:generated:1" in report["program_lifecycle_registry"]
