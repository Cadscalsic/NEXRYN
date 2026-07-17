from runtime.hypothesis import (
    HypothesisMemory,
    HypothesisRanker,
    HypothesisRegistry,
    HypothesisValidator,
    MultiHypothesisEngine,
)
from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer


def _runtime_context():
    return {
        "context_support": 0.86,
        "truth_support": 0.88,
        "dependency_support": 0.84,
        "identity_confidence": 0.90,
        "truth_governance_report": {"validation_success": True},
        "identity_governance_report": {"validation_success": True},
        "context_governance_report": {"validation_success": True},
        "dependency_governance_report": {"validation_success": True},
    }


def test_multi_hypothesis_engine_generates_multiple_families():
    engine = MultiHypothesisEngine(
        registry=HypothesisRegistry(),
        validator=HypothesisValidator(),
        ranker=HypothesisRanker(),
        memory=HypothesisMemory(),
    )

    report = engine.generate(
        concepts=["replication"],
        runtime_context=_runtime_context(),
    )

    names = {
        hypothesis["hypothesis_name"]
        for hypothesis in report["generated_hypotheses"]
    }

    assert report["generation_success"] is True
    assert report["hypothesis_count"] >= 3
    assert "duplicate_object" in names
    assert "mirror_duplicate_object" in names
    assert "topology_preserving_duplicate" in names
    assert report["semantic_hypotheses_generated"] is True
    assert report["transformation_hypotheses_generated"] is True
    assert report["hypothesis_ranking_operational"] is True
    assert report["hypothesis_validation_operational"] is True
    assert report["hypothesis_memory_operational"] is True
    assert report["MULTI_HYPOTHESIS_REPORT"]["Generated Hypotheses"] >= 3


def test_color_preservation_generates_required_variants():
    report = MultiHypothesisEngine(
        registry=HypothesisRegistry(),
        memory=HypothesisMemory(),
    ).generate(
        concepts=["color_preservation"],
        runtime_context=_runtime_context(),
    )

    names = [
        hypothesis["hypothesis_name"]
        for hypothesis in report["generated_hypotheses"]
    ]

    assert names[:4] == [
        "preserve_color",
        "preserve_palette",
        "preserve_object_colors",
        "preserve_contextual_colors",
    ]


def test_validator_blocks_hypothesis_when_governance_fails():
    validator = HypothesisValidator()
    result = validator.validate(
        {
            "hypothesis_id": "hypothesis:replication:duplicate_object",
            "semantic_support": 0.9,
            "context_support": 0.9,
            "execution_ready": True,
        },
        runtime_context={
            "truth_governance_report": {"validation_success": False},
        },
    )

    assert result["validation_passed"] is False
    assert "truth_consistency" in result["rejection_reasons"]
    assert result["execution_ready"] is False


def test_ranker_prefers_validated_execution_ready_hypothesis():
    hypotheses = [
        {
            "hypothesis_id": "hypothesis:a",
            "hypothesis_name": "semantic_only",
            "confidence": 0.99,
            "semantic_support": 0.99,
            "context_support": 0.5,
            "execution_ready": False,
        },
        {
            "hypothesis_id": "hypothesis:b",
            "hypothesis_name": "duplicate_object",
            "confidence": 0.86,
            "semantic_support": 0.86,
            "context_support": 0.86,
            "truth_support": 0.86,
            "dependency_support": 0.86,
            "identity_confidence": 0.86,
            "execution_confidence": 0.86,
            "execution_ready": True,
        },
    ]
    validation = {
        "validated_hypotheses": [
            {"hypothesis_id": "hypothesis:a", "validation_passed": True, "validation_score": 1.0},
            {"hypothesis_id": "hypothesis:b", "validation_passed": True, "validation_score": 1.0},
        ]
    }

    ranked = HypothesisRanker().rank(hypotheses, validation)

    assert ranked["hypothesis_ranking_operational"] is True
    assert ranked["best_candidates"][0]["hypothesis_name"] == "duplicate_object"


def test_hypothesis_memory_reuses_and_evolves_confidence():
    memory = HypothesisMemory()
    hypothesis = {
        "hypothesis_id": "hypothesis:replication:duplicate_object",
        "hypothesis_name": "duplicate_object",
        "source_concept": "replication",
        "matched_concepts": ["replication"],
        "confidence": 0.8,
        "execution_ready": True,
    }

    memory.remember(hypothesis, success=True)
    memory.remember(hypothesis, success=True)
    reused = memory.retrieve(["replication"])
    report = memory.report()

    assert reused[0]["hypothesis_name"] == "duplicate_object"
    assert reused[0]["evolved_confidence"] > 0.8
    assert "hypothesis:replication:duplicate_object" in report["frequently_successful_hypotheses"]


def test_final_report_renders_multi_hypothesis_section():
    engine_report = MultiHypothesisEngine(
        registry=HypothesisRegistry(),
        memory=HypothesisMemory(),
    ).generate(
        concepts=["replication"],
        runtime_context=_runtime_context(),
    )
    report = DeterministicFinalReportRenderer().render(
        {
            "runtime_status": "completed",
            "tasks_executed": 1,
            "successful_tasks": 1,
            "generated_concepts": 1,
            "generated_programs": 1,
            "average_program_confidence": 0.8,
            "overall_search_quality": 0.7,
            "execution_coverage": 1.0,
            "MULTI_HYPOTHESIS_ENGINE_REPORT": engine_report,
        },
        runtime_metadata={
            "system": "NEXRYN",
            "mode": "test",
            "profile": "unit",
            "execution_id": "hypothesis-test",
            "timestamp": "2026-07-17T00:00:00Z",
        },
    )

    assert "MULTI HYPOTHESIS REPORT" in report
    assert "Generated Hypotheses:" in report
    assert "Best Ranked:" in report
