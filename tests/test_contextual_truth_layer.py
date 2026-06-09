from core.contextual_truth import (
    ContextSignature,
    ContextualTruthEngine,
)
from core.epistemic_models import (
    Belief,
    BeliefState,
    EpistemicTrial,
    EvidenceAggregate,
    TrialResult,
)
from core.truth_commit_engine import TruthCommitEngine


def context(family, color="preserve", topology="preserve"):
    return {
        "task_cluster": family,
        "transformation_family": family,
        "color_behavior": color,
        "topology_behavior": topology,
        "identity_behavior": "preserve",
    }


def evidence(task, support=1.0, contradiction=0.0, family="translation"):
    return {
        "source": task,
        "support_score": support,
        "contradiction_score": contradiction,
        "metadata": {
            "task_id": task,
            "transformation_family": family,
            "task_cluster": family,
            "color_behavior": (
                "recolor"
                if family == "recoloring"
                else "preserve"
            ),
            "identity_behavior": "preserve",
        },
    }


def passing_trials():
    return [
        EpistemicTrial(
            concept="color_preservation",
            support_score=1.0,
            contradiction_score=0.0,
            evidence_strength=1.0,
            semantic_consistency=1.0,
            causal_alignment=1.0,
            trial_result=TrialResult.PASSED,
            evidence_count=3,
            trial_number=number,
        )
        for number in [1, 2]
    ]


def test_context_signature_similarity_operates_on_context_fields():
    translation = ContextSignature.from_context(context("translation"))
    reflection = ContextSignature.from_context(context("reflection"))
    recoloring = ContextSignature.from_context(
        context("recoloring", color="recolor")
    )

    assert translation.similarity(translation) == 1.0
    assert translation.similarity(reflection) > translation.similarity(
        recoloring
    )


def test_contextual_truth_specializes_valid_and_invalid_contexts():
    engine = ContextualTruthEngine()
    report = engine.specialize_truth(
        "color_preservation",
        [
            evidence("task_a", family="translation"),
            evidence("task_b", family="reflection"),
            evidence(
                "task_c",
                support=0.1,
                contradiction=0.9,
                family="recoloring",
            ),
        ],
        context("translation"),
    )

    truth = report["truth"]
    valid = [
        item["transformation_family"]
        for item in truth["valid_contexts"]
    ]
    invalid = [
        item["transformation_family"]
        for item in truth["invalid_contexts"]
    ]

    assert "translation" in valid
    assert "reflection" in valid
    assert "recoloring" in invalid
    assert report["specialized_truths"]


def test_contextual_contradiction_is_assigned_to_context_mismatch():
    engine = ContextualTruthEngine()
    report = engine.analyze_contextual_contradictions(
        "color_preservation",
        [
            evidence(
                "task_recolor",
                support=0.1,
                contradiction=0.9,
                family="recoloring",
            )
        ],
        context("recoloring", color="recolor"),
    )

    assert report["context_mismatch"] is True
    assert report["contradiction_type"] == "CONTEXT_MISMATCH"


def test_contextual_truth_confidence_combines_causal_and_transfer_factors():
    engine = ContextualTruthEngine()
    engine.specialize_truth(
        "color_preservation",
        [
            evidence("task_a", family="translation"),
            evidence("task_b", family="reflection"),
            evidence("task_c", family="translation"),
        ],
        context("translation"),
    )

    report = engine.generate_contextual_truth_report(
        "color_preservation",
        context("translation"),
        {
            "validation_score": 1.0,
        },
        identity_compatibility=1.0,
    )

    assert report["contextual_truth_score"] >= 0.75
    assert report["status"] == "CONTEXT_VALIDATED"
    assert report["when_valid"]


def test_contextual_truth_report_includes_context_binding_why_valid():
    engine = ContextualTruthEngine()

    report = engine.generate_contextual_truth_report(
        "shape_preservation",
        {
            "transformation_family": "duplication",
            "context_discovery": {
                "transformation_family": "duplication",
                "confidence": 0.9,
            },
            "context_hierarchy": {
                "context_hierarchy_score": 0.94,
            },
            "semantic_context": {
                "properties": ["preserves_shape", "creates_objects"],
                "capabilities": ["structural_replication"],
                "confidence": 0.9,
            },
        },
        {
            "validation_score": 0.85,
        },
        identity_compatibility=1.0,
    )

    assert report["context_binding"]["binding_state"] == "CONTEXT_BOUND"
    assert report["context_binding_score"] >= 0.75
    assert (
        "duplication -> structural_replication -> "
        "preserves_shape -> shape_preservation"
    ) in report["why_valid"]


def test_contextual_truth_preserves_discovered_context_signature():
    signature = ContextSignature.from_context(
        {
            "context_discovery": {
                "transformation_family": "duplication",
                "topology_behavior": "topology_splitting",
                "color_behavior": "color_reassigned",
                "identity_behavior": "identity_split",
                "confidence": 0.76,
                "cluster": "Structural Transformation",
            },
            "context_hierarchy": {
                "context_hierarchy_score": 0.94,
            },
            "semantic_context": {
                "semantic_context_score": 0.90,
            },
        }
    )

    assert signature.transformation_family == "duplication"
    assert signature.task_cluster == "duplication"
    assert signature.topology_behavior == "topology_splitting"
    assert signature.color_behavior == "color_reassigned"
    assert signature.identity_behavior == "identity_split"


def test_truth_commit_requires_contextual_truth_score():
    engine = TruthCommitEngine()
    belief = Belief(
        concept="color_preservation",
        claim="color_preservation is stable",
        state=BeliefState.TRUTH_CANDIDATE,
        confidence=0.95,
    )
    aggregate = EvidenceAggregate(
        concept="color_preservation",
        evidence_count=3,
        evidence_strength=0.95,
        contradiction_score=0.0,
        semantic_consistency=1.0,
        causal_alignment=1.0,
    )

    commit = engine.evaluate(
        belief,
        aggregate,
        passing_trials(),
        {
            "identity_continuity": 1.0,
            "semantic_drift": 0.0,
            "identity_safe_truth_integration": {
                "integration_safe": True,
                "semantic_containment": {
                    "integration_allowed": True,
                },
                "epistemic_drift_containment": {
                    "integration_allowed": True,
                },
            },
            "causal_spine_alignment": {
                "alignment_ready": True,
                "compatible_with_core_truths": True,
            },
            "causal_graph_validation": {
                "validation_ready": True,
            },
            "causal_graph_alignment": {
                "alignment_ready": True,
            },
            "causal_validation": {
                "validation_score": 1.0,
                "validation_ready": True,
            },
            "contextual_truth": {
                "contextual_truth_score": 0.61,
                "contextual_consistency": False,
            },
        },
    )

    assert commit.decision == "REMAIN_BELIEF"
    assert "contextual_truth_score" in commit.reasons
