from runtime.knowledge.epistemic_graduation_engine import (
    evaluate_concept_graduation,
)


def test_epistemic_graduation_promotes_dependency_backed_context():
    report = evaluate_concept_graduation(
        observations=125,
        confidence=0.824,
        dependency_confidence=0.91,
        contradiction_rate=0.05,
        cross_task_stability=0.824,
        causal_support=0.91,
        context_support=0.0,
    )

    assert report["promotion_score"] >= 0.80
    assert report["graduation_stage"] == "PROCESS_CONTEXT"
    assert report["candidate_ready"] is True
    assert report["eligible_for_context"] is True
    assert report["eligible_for_truth_candidate"] is False
    assert report["blocked_metrics"] == ["context_support"]
    assert report["next_stage"] == "TRUTH_CANDIDATE"


def test_epistemic_graduation_requires_cross_task_validation_for_truth():
    report = evaluate_concept_graduation(
        observations=125,
        confidence=0.98,
        dependency_confidence=0.98,
        contradiction_rate=0.01,
        cross_task_stability=0.98,
        causal_support=0.98,
        context_support=0.98,
        cross_task_validation_passed=False,
    )

    assert report["promotion_score"] >= 0.95
    assert report["graduation_stage"] == "TRUTH_CANDIDATE"
    assert "cross_task_validation" in report["blocked_metrics"]

    validated = evaluate_concept_graduation(
        observations=125,
        confidence=0.98,
        dependency_confidence=0.98,
        contradiction_rate=0.01,
        cross_task_stability=0.98,
        causal_support=0.98,
        context_support=0.98,
        cross_task_validation_passed=True,
    )

    assert validated["graduation_stage"] == "ESTABLISHED_TRUTH"
