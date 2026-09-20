import inspect

from runtime.cognitive_pipeline.orchestrator import CognitivePipelineOrchestrator
from runtime.reasoning.candidate_proposal_runtime import CandidateProposalRuntime
from tests.test_e5_phase3b_post_repair_quality_efficiency import (
    _condition,
    _source_experience_for,
)


def test_reuse_sufficiency_signals_are_candidate_admission_not_substitution(tmp_path):
    _, _, experience = _source_experience_for(tmp_path / "source", 1, 2)
    treatment = _condition(
        tmp_path / "treatment",
        "e5_r2_treatment",
        1,
        2,
        experience=experience,
    )
    reuse_report = treatment["reuse"]
    nested = reuse_report["experience_reuse_report"]

    assert reuse_report["skip_redundant_reasoning"] is True
    assert nested["executable_reuse_available"] is True
    assert nested["arena_admission_eligible"] is True
    assert reuse_report.get("substitution_authority") is None
    assert nested.get("reuse_terminal") is None
    assert nested.get("skip_search") is None
    assert nested.get("skip_synthesis") is None


def test_candidate_proposal_runtime_admits_reuse_without_declaring_schedule_skip(tmp_path):
    _, _, experience = _source_experience_for(tmp_path / "source", 1, 2)
    treatment = _condition(
        tmp_path / "treatment",
        "e5_r2_proposal",
        1,
        2,
        experience=experience,
    )

    report = CandidateProposalRuntime().collect(
        candidate_sources={"adaptive_reuse": treatment["reuse"]["experience_reuse_report"]},
    )

    assert report["proposal_phase_status"] == "SINGLE_SOURCE"
    assert report["candidate_proposals"][0]["proposal_status"] == "PROPOSED"
    assert report["candidate_proposals"][0]["authority"] == "OBSERVATION_ONLY"
    assert report["candidate_proposals"][0]["behavioral_authority"] == "NONE"
    assert "skip_search" not in report
    assert "skip_synthesis" not in report
    assert "substitution_authority" not in report


def test_pipeline_orchestrator_has_external_skip_hook_not_reuse_policy():
    signature = inspect.signature(CognitivePipelineOrchestrator.execute)
    source = inspect.getsource(CognitivePipelineOrchestrator.execute)

    assert "should_skip" in signature.parameters
    assert "should_skip(stage, context)" in source
    assert "adaptive_reuse" not in source
    assert "executable_reuse_available" not in source
    assert "skip_redundant_reasoning" not in source
