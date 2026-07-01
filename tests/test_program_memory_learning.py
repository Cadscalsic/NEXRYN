from runtime.meta.supervisor.program_memory import ProgramMemory, ProgramRecord
from runtime.meta.supervisor.program_memory_learning import remember_validated_program
from runtime.meta.supervisor.task_signature_engine import TaskSignature


def _successful_context():
    return {
        "semantic_abstractions": [
            {
                "semantic_concept": "replication",
            }
        ],
        "winner_hypothesis": {
            "primitive": "duplicate_object",
        },
        "synthesized_program": {
            "step_count": 1,
            "steps": [
                {
                    "operation": "duplicate_object",
                    "parameters": {"delta": 1},
                }
            ],
        },
        "execution_plan": {
            "nodes": [
                {
                    "execution_index": 0,
                    "operation": "duplicate_object",
                    "parameters": {"delta": 1},
                }
            ],
        },
        "execution_integrity_report": {
            "integrity_preserved": True,
        },
        "evaluation_result": {
            "accuracy": 1.0,
            "exact_success": True,
            "success": True,
            "success_state": "EXACT_SUCCESS",
        },
    }


def test_successful_evaluation_stores_reusable_program(tmp_path):
    memory = ProgramMemory(tmp_path / "program_memory.json")

    report = remember_validated_program(_successful_context(), memory=memory)

    assert report["program_memory_updated"] is True
    assert report["concept"] == "replication"
    assert len(memory.records) == 1
    record = memory.records[0]
    assert record.validation_state == "stable"
    assert record.integrity_verified is True
    assert record.program["concept"] == "replication"
    assert record.operation_sequence[0]["operation"] == "duplicate_object"
    assert memory.best_match(record.task_signature_id) == record


def test_program_memory_rejects_unverified_or_unsuccessful_programs(tmp_path):
    memory = ProgramMemory(tmp_path / "program_memory.json")
    context = _successful_context()
    context["evaluation_result"] = {
        "accuracy": 0.84,
        "success": False,
        "success_state": "LEARNING_PROGRESS",
    }

    report = remember_validated_program(context, memory=memory)

    assert report["program_memory_updated"] is False
    assert report["reason"] == "evaluation_not_validated_for_program_reuse"
    assert memory.records == []


def test_learning_progress_near_success_is_candidate_not_reusable(tmp_path):
    memory = ProgramMemory(tmp_path / "program_memory.json")
    context = _successful_context()
    context["task_concept"] = "near_success_task_a"
    context["evaluation_result"] = {
        "accuracy": 0.96,
        "success": True,
        "exact_success": False,
        "success_state": "LEARNING_PROGRESS",
        "difference_count": 1,
    }
    context["residual_analysis"] = {
        "residual_difference_count": 1,
    }

    report = remember_validated_program(context, memory=memory)

    assert report["program_memory_updated"] is True
    assert report["validation_state"] == "candidate"
    assert report["promotion_rule"] == "candidate_near_success"
    assert memory.records[0].validation_state == "candidate"
    assert memory.best_match(memory.records[0].task_signature_id) is None


def test_learning_progress_promotes_after_cross_task_near_success(tmp_path):
    memory = ProgramMemory(tmp_path / "program_memory.json")
    first = _successful_context()
    first["task_concept"] = "near_success_task_a"
    first["evaluation_result"] = {
        "accuracy": 0.96,
        "success": True,
        "exact_success": False,
        "success_state": "LEARNING_PROGRESS",
        "difference_count": 1,
    }
    first["residual_analysis"] = {
        "residual_difference_count": 1,
    }
    second = _successful_context()
    second["task_concept"] = "near_success_task_b"
    second["evaluation_result"] = {
        "accuracy": 0.97,
        "success": True,
        "exact_success": False,
        "success_state": "LEARNING_PROGRESS",
        "difference_count": 1,
    }
    second["residual_analysis"] = {
        "residual_difference_count": 1,
    }

    first_report = remember_validated_program(first, memory=memory)
    second_report = remember_validated_program(second, memory=memory)

    assert first_report["validation_state"] == "candidate"
    assert second_report["validation_state"] == "validated"
    assert second_report["promotion_rule"] == "cross_task_near_success"
    assert second_report["promotion_evidence_count"] == 2
    assert {record.validation_state for record in memory.records} == {"validated"}
    assert memory.best_match(memory.records[-1].task_signature_id) is not None


def test_learning_progress_candidate_rejects_semantic_contradictions(tmp_path):
    memory = ProgramMemory(tmp_path / "program_memory.json")
    context = _successful_context()
    context["evaluation_result"] = {
        "accuracy": 0.96,
        "success": True,
        "exact_success": False,
        "success_state": "LEARNING_PROGRESS",
        "difference_count": 1,
    }
    context["residual_analysis"] = {
        "residual_difference_count": 1,
    }
    context["semantic_abstractions"] = [
        {
            "semantic_concept": "object_identity_preservation",
            "semantic_valid": False,
            "semantic_contradictions": [
                "object_count_changed_but_object_identity_preservation",
            ],
        }
    ]

    report = remember_validated_program(context, memory=memory)

    assert report["program_memory_updated"] is False
    assert report["reason"] == "evaluation_not_validated_for_program_reuse"
    assert memory.records == []


def test_program_memory_semantic_fallback_matches_related_signature(tmp_path):
    memory = ProgramMemory(tmp_path / "program_memory.json")
    stored_signature = TaskSignature(
        concepts=("replication",),
        contexts=("object_replication_context",),
        transformations=("duplicate_object",),
    )
    query_signature = TaskSignature(
        concepts=("replication",),
        contexts=("object_replication_context",),
        transformations=("duplicate_object",),
        constraints=("preserve_topology",),
    )
    record = ProgramRecord(
        program_id="program-1",
        task_signature_id="different-exact-id",
        program={
            "concept": "replication",
            "steps": [{"operation": "duplicate_object"}],
        },
        operation_sequence=[{"operation": "duplicate_object"}],
        match_confidence=0.96,
        validation_state="validated",
        integrity_verified=True,
        metadata={
            "concept": "replication",
            "task_signature": stored_signature.as_dict(),
        },
    )
    memory.remember(record)

    assert memory.best_match_for_signature(query_signature) == record
