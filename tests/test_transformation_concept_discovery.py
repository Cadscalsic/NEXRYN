from runtime.stages.inference import (
    build_multi_transformation_graph,
    prioritize_transformation_concepts,
    transformation_concept_score,
)


def test_density_expansion_beats_preservation_bias_when_grid_changes():
    hypotheses = [
        {
            "type": "object_count_delta",
            "primitive": "preserve_objects",
            "confidence": 1.0,
            "semantic_class": "invariant",
            "residual_reduction": 0.0,
            "explanatory_power": 0.0,
        },
        {
            "type": "shape_transformation",
            "primitive": "preserve_shape",
            "confidence": 1.0,
            "semantic_class": "invariant",
            "residual_reduction": 0.0,
            "explanatory_power": 0.0,
        },
        {
            "type": "density_change",
            "primitive": "expand_pattern",
            "confidence": 0.97,
            "semantic_class": "transformation",
            "residual_reduction": 0.76,
            "explanatory_power": 0.76,
            "geometric_grounding": {
                "density_delta": 6,
                "operator": "expand_pattern",
            },
        },
    ]

    prioritized = prioritize_transformation_concepts(
        hypotheses,
        grid_changed=True,
    )

    assert prioritized[0]["type"] == "density_change"
    assert prioritized[0]["primitive"] == "expand_pattern"
    assert (
        prioritized[0]["transformation_discovery_state"]
        == "TRANSFORMATION_CONCEPT_DISCOVERED"
    )
    assert prioritized[0]["transformation_concept_score"] > (
        prioritized[-1]["transformation_concept_score"]
    )


def test_preservation_no_op_is_penalized_on_changed_grid():
    preserve_score = transformation_concept_score(
        {
            "type": "object_count_delta",
            "primitive": "preserve_objects",
            "confidence": 1.0,
            "semantic_class": "invariant",
        },
        grid_changed=True,
    )
    transform_score = transformation_concept_score(
        {
            "type": "density_change",
            "primitive": "expand_pattern",
            "confidence": 0.97,
            "semantic_class": "transformation",
            "residual_reduction": 0.76,
            "explanatory_power": 0.76,
        },
        grid_changed=True,
    )

    assert transform_score > preserve_score


def test_multi_transformation_graph_keeps_primary_and_latent_concepts():
    hypotheses = prioritize_transformation_concepts(
        [
            {
                "type": "density_change",
                "primitive": "expand_pattern",
                "confidence": 0.97,
                "semantic_class": "transformation",
                "residual_reduction": 0.76,
                "explanatory_power": 0.76,
                "geometric_grounding": {"density_delta": 6},
            },
            {
                "type": "object_size",
                "primitive": "preserve_size",
                "confidence": 0.86,
                "semantic_class": "invariant",
                "residual_reduction": 0.76,
                "explanatory_power": 0.76,
                "object_centric_transformation": "object_size_change",
            },
            {
                "type": "shape_transformation",
                "primitive": "preserve_shape",
                "confidence": 0.96,
                "semantic_class": "invariant",
            },
        ],
        grid_changed=True,
    )

    graph = build_multi_transformation_graph(hypotheses)
    concepts = {node["concept"] for node in graph["nodes"]}
    roles = {node["concept"]: node["role"] for node in graph["nodes"]}

    assert "propagation" in concepts
    assert "growth" in concepts
    assert "shape_relation" in concepts
    assert roles["propagation"] == "primary_transformation"
    assert roles["growth"] == "latent_transformation"
    assert graph["primary_transformation_count"] == 1
    assert graph["latent_transformation_count"] >= 2
    assert graph["edge_count"] >= 2
