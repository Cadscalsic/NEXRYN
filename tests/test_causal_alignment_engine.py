from core.belief_engine import EpistemicCognitionLayer
from core.causality.causal_alignment_engine import CausalAlignmentEngine
from core.identity.core_truth_registry import (
    CORE_TRUTHS,
    LOCKED,
    CoreTruthRegistry,
)


class SpineRegistry:
    def __init__(self, truths=None):
        self.truths = list(truths or [])

    def active_truths(self):
        return list(self.truths)


def strong_evidence(concept, source):
    return {
        "concept": concept,
        "source": source,
        "support_score": 1.0,
        "contradiction_score": 0.0,
        "reliability": 1.0,
        "semantic_consistency": 1.0,
        "causal_alignment": 1.0,
    }


def truth_context(concept, **extra):
    return {
        "epistemic_hypotheses": [{
            "concept": concept,
            "prior_confidence": 0.98,
            "semantic_consistency": 1.0,
            "causal_alignment": 1.0,
        }],
        "epistemic_evidence": [
            strong_evidence(concept, source)
            for source in [
                "causal_observation",
                "semantic_anchor_graph",
                "mutation_rehearsal",
            ]
        ],
        **extra,
    }


def test_causal_alignment_engine_allows_semantic_spine_bootstrap():
    report = CausalAlignmentEngine().evaluate(
        "topology_preservation",
        0.94,
        SpineRegistry(),
    )

    assert report["alignment_state"] == "CAUSAL_SPINE_BOOTSTRAP"
    assert report["alignment_ready"] is True


def test_causal_alignment_engine_uses_explicit_spine_relation():
    report = CausalAlignmentEngine().evaluate(
        "density_preservation",
        0.96,
        SpineRegistry([{
            "truth_id": "truth:topology",
            "concept": "topology_preservation",
            "causal_alignment": 0.95,
        }]),
        {
            "causal_spine_alignments": {
                "density_preservation": {
                    "topology_preservation": 0.52,
                },
            },
        },
    )

    assert report["alignment_score"] == 0.52
    assert report["alignment_ready"] is False
    assert report["blocked_by_spine_truths"] == [
        "topology_preservation",
    ]


def test_truth_commit_requires_alignment_with_active_semantic_spine():
    layer = EpistemicCognitionLayer()
    topology = truth_context("topology_preservation")
    layer.run_cycle(topology)
    layer.run_cycle(topology)

    density = truth_context(
        "density_preservation",
        causal_spine_alignments={
            "density_preservation": {
                "topology_preservation": 0.52,
            },
        },
    )
    layer.run_cycle(density)
    report = layer.run_cycle(density)
    evaluation = report["evaluations"][0]

    assert evaluation["causal_spine_alignment"]["alignment_ready"] is False
    assert evaluation["truth_commit"]["decision"] == "REMAIN_BELIEF"
    assert "causal_spine_alignment" in evaluation["truth_commit"]["reasons"]
    assert report["causal_alignment_engine"]["blocked_concepts"] == [
        "density_preservation",
    ]
    assert [
        truth["concept"]
        for truth in report["reusable_truth_commitments"]
    ] == ["topology_preservation"]


def test_core_truth_registry_defines_locked_identity_truths():
    registry = CoreTruthRegistry()

    assert CORE_TRUTHS == {
        "density_preservation": LOCKED,
        "symmetry_preservation": LOCKED,
    }
    assert registry.is_locked("color_preservation") is False
    assert registry.is_locked("topology_preservation") is False


def test_causal_alignment_ignores_color_preservation_when_not_locked():
    report = CausalAlignmentEngine().evaluate(
        "topology_preservation",
        0.96,
        SpineRegistry([
            {
                "truth_id": "truth:color",
                "concept": "color_preservation",
                "causal_alignment": 0.95,
            },
            {
                "truth_id": "truth:shape",
                "concept": "shape_preservation",
                "causal_alignment": 0.95,
            },
        ]),
        {
            "causal_spine_alignments": {
                "topology_preservation": {
                    "color_preservation": 0.54,
                    "shape_preservation": 0.92,
                },
            },
        },
    )

    assert report["locked_core_truths"] == []
    assert report["compatible_with_core_truths"] is True
    assert report["blocked_by_spine_truths"] == ["color_preservation"]
    assert report["blocked_by_core_truths"] == []


def test_historical_spine_score_does_not_create_false_pairwise_conflict():
    report = CausalAlignmentEngine().evaluate(
        "density_preservation",
        0.96,
        SpineRegistry([{
            "truth_id": "truth:color",
            "concept": "color_preservation",
            "causal_alignment": 0.42,
        }]),
    )

    comparison = report["comparisons"][0]
    assert comparison["alignment_score"] == 0.96
    assert comparison["spine_truth_local_causal_alignment"] == 0.42
    assert comparison["alignment_source"] == (
        "candidate_local_alignment_proxy"
    )
    assert comparison["core_compatibility_state"] == (
        "NOT_REQUIRED"
    )
    assert report["alignment_ready"] is True
    assert report["compatible_with_core_truths"] is True
    assert report["pairwise_attestation_pending"] == [
        "color_preservation",
    ]


def test_missing_pairwise_attestation_is_not_core_incompatibility():
    report = CausalAlignmentEngine().evaluate(
        "topology_preservation",
        0.62,
        SpineRegistry([{
            "truth_id": "truth:color",
            "concept": "color_preservation",
            "causal_alignment": 0.95,
        }]),
    )

    assert report["alignment_ready"] is False
    assert report["blocked_by_spine_truths"] == ["color_preservation"]
    assert report["compatible_with_core_truths"] is True
    assert report["blocked_by_core_truths"] == []
