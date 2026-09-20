from runtime.arena.candidate_proposal_gateway import CandidateProposalGateway
from runtime.arena.cognitive_candidate_arena import CognitiveCandidateArena
from runtime.execution.executable_intelligence_engine import ExecutableIntelligenceEngine


def _reuse_proposal():
    return {
        "candidate_id": "adaptive_reuse:0",
        "source": "adaptive_reuse",
        "operation": "replace_color",
        "program": {
            "steps": [
                {
                    "operation": "replace_color",
                    "parameters": {"color_mapping": {1: 5, 2: 7}},
                }
            ]
        },
        "source_confidence": 0.9,
        "learned_object_id": "program-6097823aa7c9afc0",
        "source_learned_object_id": "program-6097823aa7c9afc0",
        "learned_object_type": "PROGRAM",
        "reuse_proposal_id": "adaptive_reuse:0",
        "source_run_id": "ORIGIN_NOT_OBSERVABLE",
        "authority": "OBSERVATION_ONLY",
        "behavioral_authority": "NONE",
        "metadata": {
            "learned_object_id": "program-6097823aa7c9afc0",
            "source_learned_object_id": "program-6097823aa7c9afc0",
            "learned_object_type": "PROGRAM",
            "reuse_proposal_id": "adaptive_reuse:0",
            "source_run_id": "ORIGIN_NOT_OBSERVABLE",
            "authority": "OBSERVATION_ONLY",
            "behavioral_authority": "NONE",
        },
    }


def test_gateway_preserves_reused_program_identity_for_arena_entry():
    report = CandidateProposalGateway().submit([_reuse_proposal()])

    proposal = report["proposals"][0]
    assert proposal["proposal_status"] == "PROPOSED"
    assert proposal["learned_object_id"] == "program-6097823aa7c9afc0"
    assert proposal["source_learned_object_id"] == "program-6097823aa7c9afc0"
    assert proposal["learned_object_type"] == "PROGRAM"
    assert proposal["reuse_proposal_id"] == "adaptive_reuse:0"
    assert proposal["authority"] == "OBSERVATION_ONLY"
    assert proposal["behavioral_authority"] == "NONE"
    assert (
        proposal["provenance"]["source_learned_object_id"]
        == "program-6097823aa7c9afc0"
    )


def test_arena_selected_candidate_and_summary_preserve_reused_program_identity():
    report = CognitiveCandidateArena().run(
        [_reuse_proposal()],
        input_grid=[[1, 2], [2, 1]],
        target_grid=[[5, 7], [7, 5]],
        runtime_context={"expected_candidate_sources": ["adaptive_reuse"]},
        analysis_only=True,
        task_signature="f5_m2_contract_probe",
    )

    probe = report["execution_recommendation"]["validation_probe_candidate"]
    summary = report["candidate_summary"][0]
    assert report["selection_state"] == "NO_SAFE_WINNER"
    assert report["execution_recommendation"]["selected_candidate"] is None
    assert probe["source_learned_object_id"] == "program-6097823aa7c9afc0"
    assert probe["authority"] == "OBSERVATION_ONLY"
    assert probe["behavioral_authority"] == "NONE"
    assert summary["source_learned_object_id"] == "program-6097823aa7c9afc0"
    assert summary["reuse_proposal_id"] == "adaptive_reuse:0"


def test_executable_report_preserves_consumed_reuse_candidate_identity_without_real_execution():
    arena_report = CognitiveCandidateArena().run(
        [_reuse_proposal()],
        input_grid=[[1, 2], [2, 1]],
        target_grid=[[5, 7], [7, 5]],
        runtime_context={"expected_candidate_sources": ["adaptive_reuse"]},
        analysis_only=True,
        task_signature="f5_m2_contract_probe",
    )

    result = ExecutableIntelligenceEngine().run(
        semantic_intent="replace_color",
        operation="replace_color",
        input_grid=[[1, 2], [2, 1]],
        target_grid=[[5, 7], [7, 5]],
        arena_execution_recommendation=arena_report["execution_recommendation"],
        governance_context={
            "analysis_only": True,
            "real_execution_authorized": False,
        },
    )

    report = result["EXECUTABLE_INTELLIGENCE_REPORT"]
    identity = report["consumed_candidate_identity"]
    assert report["real_execution_performed"] is False
    assert identity["source_learned_object_id"] == "program-6097823aa7c9afc0"
    assert identity["reuse_proposal_id"] == "adaptive_reuse:0"
    assert identity["authority"] == "OBSERVATION_ONLY"
    assert identity["behavioral_authority"] == "NONE"
    assert (
        result["final_execution_recommendation"]["source_candidate_identity"][
            "source_learned_object_id"
        ]
        == "program-6097823aa7c9afc0"
    )
