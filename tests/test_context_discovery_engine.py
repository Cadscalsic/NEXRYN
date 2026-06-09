from core.belief_engine import EpistemicCognitionLayer
from core.context_discovery import ContextDiscoveryEngine


def recoloring_observation():
    return {
        "task_id": "task_recolor",
        "input_grid": [
            [0, 1, 0],
            [0, 1, 0],
            [0, 0, 0],
        ],
        "output_grid": [
            [0, 2, 0],
            [0, 2, 0],
            [0, 0, 0],
        ],
    }


def translation_observation():
    return {
        "task_id": "task_translate",
        "input_grid": [
            [1, 0, 0],
            [1, 0, 0],
            [0, 0, 0],
        ],
        "output_grid": [
            [0, 1, 0],
            [0, 1, 0],
            [0, 0, 0],
        ],
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


def test_context_discovery_classifies_recoloring_from_raw_grids():
    engine = ContextDiscoveryEngine()
    report = engine.discover_context(recoloring_observation())

    assert report["transformation_family"] == "recoloring"
    assert report["topology_behavior"] == "topology_preserved"
    assert report["color_behavior"] == "color_changed"
    assert report["identity_behavior"] == "identity_modified"
    assert report["confidence"] >= 0.90
    assert report["cluster"] == "Attribute Transformation"
    assert "colors changed consistently" in report["explanation"]["why"]


def test_context_discovery_classifies_translation_from_motion():
    engine = ContextDiscoveryEngine()
    report = engine.discover_context(translation_observation())

    assert report["transformation_family"] == "translation"
    assert report["color_behavior"] == "color_preserved"
    assert report["identity_behavior"] == "identity_preserved"
    assert report["cluster"] == "Geometric Transformation"


def test_context_clustering_groups_geometric_transformations():
    engine = ContextDiscoveryEngine()
    translation = engine.discover_context(translation_observation())
    reflection = engine.discover_context({
        "task_id": "task_reflect",
        "active_concepts": ["reflection"],
    })
    clusters = engine.cluster_contexts()["clusters"]

    geometric = next(
        item
        for item in clusters
        if item["cluster_name"] == "Geometric Transformation"
    )

    assert translation["cluster"] == "Geometric Transformation"
    assert reflection["cluster"] == "Geometric Transformation"
    assert len(geometric["member_contexts"]) == 2
    assert geometric["stability_score"] == 1.0


def test_context_similarity_compares_discovered_signatures():
    engine = ContextDiscoveryEngine()
    recolor = engine.generate_context_signature(recoloring_observation())
    translation = engine.generate_context_signature(translation_observation())

    assert engine.compute_context_similarity(recolor, recolor) == 1.0
    assert engine.compute_context_similarity(recolor, translation) < 1.0


def test_object_identity_split_inherits_duplication_context():
    report = ContextDiscoveryEngine().discover_context({
        "task_id": "task_identity_split",
        "concept": "object_identity_preservation",
        "identity_behavior": "identity_split",
        "topology_behavior": "topology_splitting",
    })

    assert report["transformation_family"] == "duplication"
    assert report["cluster"] == "Structural Transformation"
    assert report["context_signature"]["identity_behavior"] == (
        "identity_split"
    )
    assert report["context_signature"]["topology_behavior"] == (
        "topology_splitting"
    )


def test_object_identity_preservation_discovers_identity_context():
    report = ContextDiscoveryEngine().discover_context({
        "task_id": "task_identity_preservation",
        "concept": "object_identity_preservation",
    })

    assert report["transformation_family"] == "identity_preservation"
    assert report["cluster"] == "Identity Preservation"
    assert report["confidence"] >= 0.80
    assert report["context_signature"]["identity_behavior"] == (
        "identity_preserved"
    )


def test_runtime_report_exposes_discovered_context():
    layer = EpistemicCognitionLayer()
    context = {
        **recoloring_observation(),
        "epistemic_hypotheses": [{
            "concept": "color_preservation",
            "prior_confidence": 0.98,
            "semantic_consistency": 1.0,
            "causal_alignment": 1.0,
        }],
        "epistemic_evidence": [
            strong_evidence("color_preservation", source)
            for source in [
                "causal_observation",
                "semantic_anchor_graph",
                "mutation_rehearsal",
            ]
        ],
    }

    report = layer.run_cycle(context)
    discovery = report["context_discovery_engine"]["evaluations"][0]
    contextual_truth = report["evaluations"][0]["contextual_truth"]

    assert discovery["transformation_family"] == "recoloring"
    assert discovery["color_behavior"] == "color_changed"
    assert "recoloring" in " ".join(contextual_truth["when_invalid"])
