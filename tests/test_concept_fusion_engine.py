from core.cognition.concept_fusion_engine import (
    ConceptFusionEngine,
    MAX_FUSIONS_PER_CYCLE,
)


def test_concept_fusion_unifies_partial_object_size_representations():

    engine = ConceptFusionEngine()

    concepts = [
        {
            "concept":
            "hybrid_object_size",

            "identity":
            {
                "local_identity":
                "hybrid_object_size",

                "structural_identity":
                [
                    "object",
                    "size",
                    "mixed_signature",
                ],

                "causal_identity":
                [
                    "spatial_expansion",
                    "object_scale_change",
                ],

                "archetypal_identity":
                "object_spatial_magnitude",

                "symbolic_identity":
                [
                    "object",
                    "size",
                ],
            },
        },
        {
            "concept":
            "structural_object_size",

            "identity":
            {
                "local_identity":
                "structural_object_size",

                "structural_identity":
                [
                    "object",
                    "size",
                    "structural_signature",
                ],

                "causal_identity":
                [
                    "spatial_expansion",
                    "object_scale_change",
                ],

                "archetypal_identity":
                "object_spatial_magnitude",

                "symbolic_identity":
                [
                    "object",
                    "size",
                ],
            },
        },
    ]

    similarity = engine.compute_semantic_similarity(
        concepts[0],
        concepts[1],
    )

    assert similarity["surface_similarity"] < 1.0
    assert similarity["hierarchical_similarity"] > 0.55

    report = engine.build_meta_representation(
        concepts,
    )

    assert report["fusion_count"] == 1

    fused = report["fused_concepts"][0]["meta_concept"]

    assert fused["meta_concept_id"] == "object_size"
    assert fused["identity_state"] in [
        "stable_fused_identity",
        "probationary_fused_identity",
    ]
    assert "structural_identity" in fused["identity"]


def test_concept_fusion_rejects_unstable_identity_conflict():

    engine = ConceptFusionEngine()

    concepts = [
        {
            "concept":
            "object_size",

            "identity":
            {
                "structural_identity":
                [
                    "object",
                    "size",
                ],

                "causal_identity":
                "spatial_expansion",

                "archetypal_identity":
                "object_spatial_magnitude",
            },
        },
        {
            "concept":
            "color_parity",

            "identity":
            {
                "structural_identity":
                [
                    "color",
                    "parity",
                ],

                "causal_identity":
                "symbolic_recoloring",

                "archetypal_identity":
                "symbolic_surface_rule",
            },
        },
    ]

    report = engine.build_meta_representation(
        concepts,
    )

    assert report["fusion_count"] == 0


def test_concept_fusion_deduplicates_repeated_pair_events():

    engine = ConceptFusionEngine()

    concepts = []

    for _ in range(40):

        concepts.extend([
            {
                "concept":
                "hybrid_object_size",

                "identity":
                {
                    "structural_identity":
                    [
                        "object",
                        "size",
                        "mixed_signature",
                    ],

                    "causal_identity":
                    "spatial_expansion",

                    "archetypal_identity":
                    "object_spatial_magnitude",
                },
            },
            {
                "concept":
                "structural_object_size",

                "identity":
                {
                    "structural_identity":
                    [
                        "object",
                        "size",
                        "structural_signature",
                    ],

                    "causal_identity":
                    "spatial_expansion",

                    "archetypal_identity":
                    "object_spatial_magnitude",
                },
            },
        ])

    report = engine.build_meta_representation(
        concepts,
    )

    assert (
        report["fusion_count"]
        <=
        MAX_FUSIONS_PER_CYCLE
    )
    assert report["fusion_count"] == 1
