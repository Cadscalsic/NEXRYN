from core.epistemic_models import Belief, BeliefState, EvidenceAggregate
from runtime.causal import RuntimeCausalAlignmentEngine
from runtime.truth_candidate_engine import TruthCandidateEngine


def test_runtime_causal_alignment_explains_preservation_transform_boundary():
    report = RuntimeCausalAlignmentEngine().evaluate(
        "color_preservation",
        EvidenceAggregate(
            concept="color_preservation",
            contradiction_score=0.1525,
        ),
        {
            "causal_conditions": {
                "color_mode": "transform",
            },
            "causal_boundary_observations": {
                "color_preservation": [
                    {"outcome": "holds", "conditions": {"color_mode": "preserve"}},
                    {"outcome": "breaks", "conditions": {"color_mode": "transform"}},
                ],
            },
        },
    )

    assert report["alignment_state"] == "CONTEXTUAL_BOUNDARY_EXPLAINED"
    assert report["contradiction_interpretable"] is True
    assert report["raw_contradiction_score"] == 0.1525
    assert report["adjusted_contradiction_score"] == 0.06
    assert report["causal_alignment_supported"] is True


def test_truth_candidate_uses_contextual_boundary_before_review_severity():
    report = TruthCandidateEngine().evaluate(
        Belief(
            concept="color_preservation",
            claim="color_preservation",
            state=BeliefState.VALIDATED,
            confidence=0.91,
        ),
        EvidenceAggregate(
            concept="color_preservation",
            evidence_strength=0.91,
            contradiction_score=0.1525,
            causal_alignment=0.91,
        ),
        {
            "active_concepts": ["symbolic_remapping"],
            "causal_boundary_observations": {
                "color_preservation": [
                    {"outcome": "holds", "conditions": {"color_mode": "preserve"}},
                    {"outcome": "breaks", "conditions": {"color_mode": "transform"}},
                ],
            },
        },
    )

    assert "contradiction_score" not in report["blocked_metrics"]
    assert report["effective_contradiction_score"] == 0.06
    assert report["raw_contradiction_score"] == 0.1525
    assert report["contradiction_review_required"] is False
    assert report["causal_boundary_alignment"][
        "preservation_and_transform_are_contextual_not_absolute"
    ] is True


def test_runtime_causal_alignment_handles_shape_transformation_boundary():
    report = RuntimeCausalAlignmentEngine().evaluate(
        "shape_preservation",
        EvidenceAggregate(
            concept="shape_preservation",
            contradiction_score=0.12,
        ),
        {
            "active_concepts": ["shape_transformation"],
        },
    )

    assert report["alignment_state"] == "CONTEXTUAL_BOUNDARY_EXPLAINED"
    assert report["contradiction_interpretable"] is True


def test_runtime_causal_alignment_handles_topology_growth_boundary():
    report = RuntimeCausalAlignmentEngine().evaluate(
        "topology_preservation",
        EvidenceAggregate(
            concept="topology_preservation",
            contradiction_score=0.11,
        ),
        {
            "active_concepts": ["grow_topology"],
        },
    )

    assert report["alignment_state"] == "CONTEXTUAL_BOUNDARY_EXPLAINED"
    assert report["contradiction_interpretable"] is True


def test_runtime_causal_alignment_handles_symmetry_reasoning_boundary():
    report = RuntimeCausalAlignmentEngine().evaluate(
        "symmetry_preservation",
        EvidenceAggregate(
            concept="symmetry_preservation",
            contradiction_score=0.13,
        ),
        {
            "active_concepts": ["symmetry_reasoning"],
        },
    )

    assert report["alignment_state"] == "CONTEXTUAL_BOUNDARY_EXPLAINED"
    assert report["contradiction_interpretable"] is True


def test_runtime_causal_alignment_handles_attribute_remapping_as_color_transform_boundary():
    report = RuntimeCausalAlignmentEngine().evaluate(
        "color_preservation",
        EvidenceAggregate(
            concept="color_preservation",
            contradiction_score=0.14,
        ),
        {
            "active_concepts": ["attribute_remapping"],
        },
    )

    assert report["alignment_state"] == "CONTEXTUAL_BOUNDARY_EXPLAINED"
    assert report["contradiction_interpretable"] is True
