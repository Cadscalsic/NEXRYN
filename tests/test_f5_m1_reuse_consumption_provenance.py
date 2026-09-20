from runtime.provenance import (
    build_candidate_origin_report,
    build_current_candidate_origin_report,
)
from runtime.reasoning.candidate_proposal_runtime import CandidateProposalRuntime


def _program_record(program_id="program-abc"):
    return {
        "program_id": program_id,
        "program": {
            "program_steps": [
                {
                    "operation": "replace_color",
                    "parameters": {},
                }
            ]
        },
        "metadata": {
            "source_run_id": "ORIGIN_NOT_OBSERVABLE",
        },
    }


def test_persisted_program_identity_survives_reuse_proposal():
    report = CandidateProposalRuntime().collect(
        candidate_sources={"adaptive_reuse": {"reused_programs": [_program_record()]}}
    )

    proposal = report["candidate_proposals"][0]
    assert proposal["proposal_status"] == "PROPOSED"
    assert proposal["learned_object_id"] == "program-abc"
    assert proposal["source_learned_object_id"] == "program-abc"
    assert proposal["learned_object_type"] == "PROGRAM"
    assert proposal["reuse_proposal_id"] == "adaptive_reuse:0"
    assert proposal["authority"] == "OBSERVATION_ONLY"
    assert proposal["behavioral_authority"] == "NONE"
    assert proposal["metadata"]["source_learned_object_id"] == "program-abc"


def test_same_run_generation_is_not_cross_run_reuse_by_identity_alone():
    report = CandidateProposalRuntime().collect(
        candidate_sources={
            "adaptive_reuse": {
                "reused_programs": [
                    {
                        **_program_record(),
                        "metadata": {
                            "source_run_id": "run_same",
                            "target_run_id": "run_same",
                        },
                    }
                ]
            }
        }
    )

    proposal = report["candidate_proposals"][0]
    assert proposal["learned_object_id"] == "program-abc"
    assert proposal["metadata"]["source_run_id"] == "run_same"
    assert proposal["metadata"]["target_run_id"] == "run_same"
    assert proposal["metadata"]["behavioral_authority"] == "NONE"


def test_retrieval_hit_without_executable_payload_is_not_consumption():
    report = CandidateProposalRuntime().collect(
        candidate_sources={
            "adaptive_reuse": {
                "retrieval_successes": 1,
                "reused_strategies": [{"strategy_id": "strategy-1"}],
            }
        }
    )

    proposal = report["candidate_proposals"][0]
    assert proposal["proposal_status"] == "REJECTED"
    assert proposal["candidate_available"] is False
    assert proposal["rejection_reason"] == "COGNITIVE_REUSE_ONLY"
    assert proposal["learned_object_id"] is None
    assert proposal["authority"] == "OBSERVATION_ONLY"
    assert proposal["behavioral_authority"] == "NONE"


def test_candidate_origin_can_bind_reused_object_id_to_candidate_handoff():
    origin = build_candidate_origin_report(
        producer_component="adaptive_reuse",
        producer_operation_id="program_execution",
        candidate_id="candidate:reuse:1",
        program_id="program-abc",
        learned_object_id="program-abc",
        learned_object_type="PROGRAM",
        reuse_proposal_id="adaptive_reuse:0",
        retrieval_source="adaptive_reuse_layer",
        run_id="run_target",
        task_id="task_target",
    )
    handoff = build_current_candidate_origin_report(
        context={"candidate_origin_report": origin},
        residual_evidence={"source_candidate_id": "candidate:reuse:1"},
    )

    assert origin["authority"] == "OBSERVATION_ONLY"
    assert origin["behavioral_authority"] == "NONE"
    assert origin["learned_object_id"] == "program-abc"
    assert origin["source_learned_object_id"] == "program-abc"
    assert handoff["candidate_id"] == "candidate:reuse:1"
    assert handoff["learned_object_id"] == "program-abc"
    assert handoff["reuse_proposal_id"] == "adaptive_reuse:0"
