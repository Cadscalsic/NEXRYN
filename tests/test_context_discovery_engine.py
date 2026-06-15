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

    assert report["semantic_context"] == "color_context"
    assert report["process_operator"] == "recoloring"
    assert report["topology_behavior"] == "topology_preserved"
    assert report["color_behavior"] == "color_changed"
    assert report["identity_behavior"] == "identity_modified"
    assert report["confidence"] >= 0.90
    assert report["cluster"] == "Color Context"
    assert "colors changed consistently" in report["context_signature"][
        "operator_reasons"
    ]


def test_context_discovery_classifies_translation_from_motion():
    engine = ContextDiscoveryEngine()
    report = engine.discover_context(translation_observation())

    assert report["semantic_context"] == "position_context"
    assert report["process_operator"] == "translation"
    assert report["color_behavior"] == "color_preserved"
    assert report["identity_behavior"] == "identity_preserved"
    assert report["cluster"] == "Position Context"


def test_context_clustering_groups_geometric_transformations():
    engine = ContextDiscoveryEngine()
    translation = engine.discover_context(translation_observation())
    reflection = engine.discover_context({
        "task_id": "task_reflect",
        "active_concepts": ["reflection"],
    })
    clusters = engine.cluster_contexts()["clusters"]

    position = next(
        item
        for item in clusters
        if item["cluster_name"] == "Position Context"
    )

    assert translation["cluster"] == "Position Context"
    assert reflection["cluster"] == "Shape Context"
    assert len(position["member_contexts"]) == 1
    assert position["stability_score"] == 1.0


def test_context_similarity_compares_discovered_signatures():
    engine = ContextDiscoveryEngine()
    recolor = engine.generate_context_signature(recoloring_observation())
    translation = engine.generate_context_signature(translation_observation())

    assert engine.compute_context_similarity(recolor, recolor) == 1.0
    assert engine.compute_context_similarity(recolor, translation) < 1.0


def test_identity_forking_discovers_split_context():
    report = ContextDiscoveryEngine().discover_context({
        "task_id": "task_identity_split",
        "concept": "identity_forking",
        "identity_behavior": "identity_split",
        "topology_behavior": "topology_splitting",
    })

    assert report["semantic_context"] == "identity_forking"
    assert report["process_operator"] == "replication"
    assert report["cluster"] == "Identity Forking"
    assert report["context_signature"]["identity_behavior"] == (
        "identity_split"
    )
    assert report["context_signature"]["topology_behavior"] == (
        "topology_splitting"
    )


def test_identity_persistence_discovers_persistence_context():
    report = ContextDiscoveryEngine().discover_context({
        "task_id": "task_identity_preservation",
        "concept": "identity_persistence",
    })

    assert report["semantic_context"] == "identity_persistence"
    assert report["process_operator"] == "identity_preservation"
    assert report["cluster"] == "Identity Preservation"
    assert report["confidence"] >= 0.80
    assert report["context_signature"]["identity_behavior"] == (
        "identity_preserved"
    )


def test_process_context_discovery_generates_native_surfaces():
    engine = ContextDiscoveryEngine()

    expected = {
        "growth": (
            "Growth Context",
            "topology_expansion",
            "identity_preservation_under_growth",
        ),
        "propagation": (
            "Propagation Context",
            "directional_spread",
            "signal_transfer",
        ),
        "replication": (
            "Replication Context",
            "structural_copying",
            "object_creation",
        ),
        "topological_growth": (
            "Topological Growth Context",
            "topology_expansion",
            "region_expansion",
        ),
        "directional_motion": (
            "Directional Motion Context",
            "position_delta",
            "directional_displacement",
        ),
    }

    for concept, (cluster, surface, native_context) in expected.items():
        report = engine.discover_context({
            "task_id": f"task_{concept}",
            "concept": concept,
            "active_concepts": [concept],
        })

        assert report["semantic_context"] == f"{concept}_context"
        if concept == "topological_growth":
            assert report["semantic_context"] == "topological_growth_context"
        if concept == "directional_motion":
            assert report["semantic_context"] == "directional_motion_context"
        assert report["process_operator"] == concept
        assert report["cluster"] == cluster
        assert report["context_signature"]["process_context_surface"] == (
            surface
        )
        assert native_context in report["context_signature"][
            "process_native_contexts"
        ]
        assert report["context_signature"]["process_native_context_ready"] is True


def test_truth_context_discovery_differentiates_color_and_symmetry():
    engine = ContextDiscoveryEngine()

    expected = {
        "color_preservation": (
            "color_context",
            "Color Context",
            "color_stability",
        ),
        "symmetry_reasoning": (
            "symmetry_context",
            "Symmetry Context",
            "symmetry_relation",
        ),
    }

    for concept, (family, cluster, surface) in expected.items():
        report = engine.discover_context({
            "task_id": f"task_{concept}",
            "concept": concept,
            "active_concepts": [concept],
            "input_grid": [[1, 0]],
            "output_grid": [[1, 0], [1, 0]],
        })

        assert report["semantic_context"] == family
        assert report["cluster"] == cluster
        assert report["context_signature"]["context_surface"] == surface
        assert report["context_signature"]["truth_native_context_ready"] is True
        assert report["semantic_context"] != "duplication"


def test_position_preservation_uses_position_context_not_operator():
    report = ContextDiscoveryEngine().discover_context({
        "task_id": "task_position_preservation_split_noise",
        "concept": "position_preservation",
        "active_concepts": ["position_preservation", "duplication"],
        "identity_behavior": "identity_split",
        "topology_behavior": "topology_splitting",
        "color_behavior": "color_reassigned",
        "input_grid": [[1, 0]],
        "output_grid": [[1, 0], [1, 0]],
    })

    assert report["semantic_context"] == "position_context"
    assert report["discovered_context"]["context_name"] == "position_context"
    assert report["process_operator"] == "duplication"
    assert report["discovered_context"]["context_name"] != "duplication"


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

    assert discovery["semantic_context"] == "color_context"
    assert discovery["process_operator"] == "recoloring"
    assert discovery["color_behavior"] == "color_preserved"
    assert "color_context" in " ".join(contextual_truth["when_valid"])
    assert "recoloring" not in " ".join(contextual_truth["when_valid"])
    assert "recoloring" not in " ".join(contextual_truth["when_invalid"])
