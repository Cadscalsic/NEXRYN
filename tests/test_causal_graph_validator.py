from pathlib import Path
from tempfile import TemporaryDirectory

from core.belief_engine import EpistemicCognitionLayer
from core.causality.causal_evidence_accumulator import (
    CausalEvidenceAccumulator,
)
from core.causality.causal_graph_validator import CausalGraphValidator
from core.causality.causal_support_score import (
    calculate_causal_support_score,
)


def semantic_graph(causal_strength=0.42, include_edge=True):
    edges = [{
        "source": 0,
        "target": 1,
        "relation": "depends_on",
        "edge_weight": 0.74,
        "causal_strength": 0.44,
    }]
    if include_edge:
        edges.append({
            "source": 1,
            "target": 2,
            "relation": "depends_on",
            "edge_weight": 0.70,
            "causal_strength": causal_strength,
        })
    return {
        "concept_nodes": [
            {"concept": "density_preservation"},
            {"concept": "topology_preservation"},
            {"concept": "symmetry_preservation"},
        ],
        "concept_edges": edges,
    }


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


def truth_context(concept, graph):
    return {
        "semantic_graph": graph,
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
    }


def test_causal_graph_validator_resolves_indexed_semantic_graph_edges():
    report = CausalGraphValidator(
        evidence_accumulator=CausalEvidenceAccumulator(
            minimum_supporting_observations=1,
        )
    ).evaluate(
        "topology_preservation",
        semantic_graph(),
    )

    assert report["validation_state"] == "CAUSAL_GRAPH_VALIDATED"
    assert report["causal_consistency_score"] == 0.44
    assert report["relationship_checks"][0]["source"] == (
        "density_preservation"
    )
    assert report["relationship_checks"][0]["target"] == (
        "topology_preservation"
    )
    assert report["downstream_relationships"][0]["source"] == (
        "topology_preservation"
    )
    assert report["downstream_relationships"][0]["target"] == (
        "symmetry_preservation"
    )


def test_causal_support_score_exposes_maturity_and_reliability():
    report = calculate_causal_support_score(
        supporting_observation_count=2,
        observation_count=3,
        minimum_supporting_observations=3,
    )

    assert report == {
        "support_maturity": 0.6667,
        "support_reliability": 0.6667,
        "causal_support_score": 0.4444,
    }


def test_causal_graph_validator_accumulates_support_before_validation():
    validator = CausalGraphValidator()

    first = validator.evaluate("topology_preservation", semantic_graph())
    second = validator.evaluate("topology_preservation", semantic_graph())
    third = validator.evaluate("topology_preservation", semantic_graph())

    assert first["validation_state"] == "CAUSAL_SUPPORT_ACCUMULATING"
    assert first["causal_support_score"] == 0.3333
    assert first["blocked_relationships"] == []
    assert len(first["accumulating_relationships"]) == 1
    assert second["causal_support_score"] == 0.6667
    assert third["causal_support_score"] == 1.0
    assert third["validation_state"] == "CAUSAL_GRAPH_VALIDATED"
    assert third["validation_ready"] is True
    assert third["relationship_checks"][0]["causal_support"][
        "supporting_observation_count"
    ] == 3


def test_causal_evidence_accumulator_penalizes_conflicting_observations():
    accumulator = CausalEvidenceAccumulator(
        minimum_supporting_observations=2,
    )

    accumulator.observe("density", "topology", 0.42, 0.30)
    accumulator.observe("density", "topology", 0.12, 0.30)
    report = accumulator.observe("density", "topology", 0.44, 0.30)

    assert report["supporting_observation_count"] == 2
    assert report["conflicting_observation_count"] == 1
    assert report["causal_support_score"] == 0.6667
    assert report["causal_support_ready"] is False


def test_causal_evidence_accumulator_resumes_after_process_restart():
    with TemporaryDirectory() as directory:
        storage_path = Path(directory) / "causal_evidence_ledger.json"
        first = CausalEvidenceAccumulator(storage_path=storage_path)
        first.observe("density", "topology", 0.42, 0.30)
        first.observe("density", "topology", 0.44, 0.30)

        resumed = CausalEvidenceAccumulator(storage_path=storage_path)
        report = resumed.observe("density", "topology", 0.46, 0.30)

        assert report["observation_count"] == 3
        assert report["supporting_observation_count"] == 3
        assert report["remaining_supporting_observations"] == 0
        assert report["causal_support_score"] == 1.0
        assert report["causal_support_ready"] is True
        assert resumed.report()["persistent_storage_enabled"] is True


def test_causal_graph_validator_resumes_accumulated_support_after_restart():
    with TemporaryDirectory() as directory:
        storage_path = Path(directory) / "causal_evidence_ledger.json"
        first = CausalGraphValidator(
            evidence_accumulator=CausalEvidenceAccumulator(
                storage_path=storage_path
            )
        )
        first.evaluate("topology_preservation", semantic_graph())
        first.evaluate("topology_preservation", semantic_graph())

        resumed = CausalGraphValidator(
            evidence_accumulator=CausalEvidenceAccumulator(
                storage_path=storage_path
            )
        )
        report = resumed.evaluate(
            "topology_preservation",
            semantic_graph(),
        )

        assert report["validation_state"] == "CAUSAL_GRAPH_VALIDATED"
        assert report["causal_support_score"] == 1.0


def test_cognition_layer_exposes_persistent_causal_evidence_ledger():
    with TemporaryDirectory() as directory:
        layer = EpistemicCognitionLayer(
            causal_evidence_ledger_path=(
                Path(directory) / "causal_evidence_ledger.json"
            )
        )
        report = layer.run_cycle(
            truth_context(
                "topology_preservation",
                semantic_graph(),
            )
        )

        accumulator = report["causal_graph_validator"][
            "causal_evidence_accumulator"
        ]
        assert accumulator["persistent_storage_enabled"] is True
        assert len(accumulator["relationships"]) == 1


def test_causal_graph_validator_blocks_missing_required_relationship():
    report = CausalGraphValidator().evaluate(
        "symmetry_preservation",
        semantic_graph(include_edge=False),
    )

    assert report["validation_state"] == (
        "CAUSAL_GRAPH_VALIDATION_REQUIRED"
    )
    assert report["validation_ready"] is False
    assert report["blocked_relationships"] == [{
        "source": "topology_preservation",
        "target": "symmetry_preservation",
    }]


def test_causal_graph_validator_retains_mature_support_when_edge_is_absent():
    validator = CausalGraphValidator()
    for _ in range(3):
        validator.evaluate(
            "symmetry_preservation",
            semantic_graph(),
        )

    report = validator.evaluate(
        "symmetry_preservation",
        semantic_graph(include_edge=False),
    )

    check = report["relationship_checks"][0]
    assert report["validation_state"] == "CAUSAL_GRAPH_VALIDATED"
    assert report["validation_ready"] is True
    assert check["edge_observed"] is False
    assert check["current_edge_supported"] is False
    assert check["accumulated_support_ready"] is True
    assert check["support_source"] == "ACCUMULATED_CAUSAL_EVIDENCE"


def test_truth_commit_requires_causal_graph_validation_when_graph_is_observed():
    layer = EpistemicCognitionLayer()
    context = truth_context(
        "symmetry_preservation",
        semantic_graph(include_edge=False),
    )

    layer.run_cycle(context)
    report = layer.run_cycle(context)
    evaluation = report["evaluations"][0]

    assert evaluation["causal_graph_validation"][
        "validation_ready"
    ] is False
    assert evaluation["truth_commit"]["decision"] == "REMAIN_BELIEF"
    assert "causal_graph_validation" in evaluation["truth_commit"]["reasons"]
    assert report["causal_graph_validator"]["blocked_concepts"] == [
        "symmetry_preservation",
    ]


def test_downstream_relationship_does_not_block_current_concept_admission():
    validator = CausalGraphValidator(
        evidence_accumulator=CausalEvidenceAccumulator(
            minimum_supporting_observations=1,
        )
    )

    report = validator.evaluate(
        "symmetry_preservation",
        semantic_graph(),
    )

    assert report["validation_state"] == "CAUSAL_GRAPH_VALIDATED"
    assert report["validation_ready"] is True
    assert report["required_relationships"] == [{
        "source": "topology_preservation",
        "target": "symmetry_preservation",
    }]
    assert report["downstream_relationships"] == [{
        "source": "symmetry_preservation",
        "target": "object_identity_preservation",
    }]
    assert report["downstream_relationships_are_diagnostic_only"] is True
