from runtime.semantics.semantic_abstraction import SemanticAbstractionEngine


def test_object_count_increase_reclassifies_preservation_as_replication():
    abstraction = SemanticAbstractionEngine().abstract_hypothesis(
        {
            "type": "object_count_delta",
            "primitive": "preserve_objects",
            "confidence": 0.97,
            "geometric_grounding": {
                "input_count": 1,
                "output_count": 2,
                "delta": 1,
            },
        }
    )

    assert abstraction["original_primitive"] == "preserve_objects"
    assert abstraction["primitive"] == "duplicate_object"
    assert abstraction["semantic_concept"] == "replication"
    assert abstraction["causal_effect"] == "increase_object_count"
    assert (
        abstraction["semantic_reclassification_reason"]
        == "object_count_increase"
    )
    assert abstraction["semantic_validator"] == "transformation_semantic_validator"
    assert abstraction["semantic_valid"] is True
    assert abstraction["semantic_contradictions"] == []


def test_object_count_preservation_stays_preservation_when_delta_is_zero():
    abstraction = SemanticAbstractionEngine().abstract_hypothesis(
        {
            "type": "object_count_delta",
            "primitive": "preserve_objects",
            "confidence": 0.97,
            "geometric_grounding": {
                "input_count": 1,
                "output_count": 1,
                "delta": 0,
            },
        }
    )

    assert abstraction["primitive"] == "preserve_objects"
    assert abstraction["semantic_concept"] == "object_identity_preservation"
    assert abstraction["semantic_reclassification_reason"] is None
    assert abstraction["semantic_valid"] is True


def test_task_context_forbids_object_count_preservation_when_count_increases():
    abstraction = SemanticAbstractionEngine().abstract_hypothesis(
        {
            "type": "object_count_delta",
            "primitive": "preserve_objects",
            "confidence": 0.97,
        },
        evidence_context={
            "input_summary": {"object_count": 1},
            "output_summary": {"object_count": 2},
        },
    )

    assert abstraction["original_primitive"] == "preserve_objects"
    assert abstraction["primitive"] == "duplicate_object"
    assert abstraction["semantic_concept"] == "replication"
    assert abstraction["causal_effect"] == "increase_object_count"
    assert (
        abstraction["semantic_reclassification_reason"]
        == "object_count_increase"
    )
    assert abstraction["semantic_evidence_scope"] == "task_context"


def test_task_context_allows_object_count_preservation_when_count_is_stable():
    abstraction = SemanticAbstractionEngine().abstract_hypothesis(
        {
            "type": "contextual_object_count_delta",
            "primitive": "preserve_objects",
            "confidence": 1.0,
        },
        evidence_context={
            "input_summary": {"object_count": 1},
            "output_summary": {"object_count": 1},
        },
    )

    assert abstraction["primitive"] == "preserve_objects"
    assert abstraction["semantic_concept"] == "object_identity_preservation"
    assert abstraction["semantic_reclassification_reason"] is None


def test_pattern_rule_evidence_forbids_object_count_preservation():
    abstraction = SemanticAbstractionEngine().abstract_hypothesis(
        {
            "type": "object_count_delta",
            "primitive": "preserve_objects",
            "confidence": 1.0,
        },
        evidence_context={
            "patterns": [
                {"pattern": "input_object_count", "value": 1},
                {"pattern": "output_object_count", "value": 2},
                {"pattern": "object_count_changed", "value": True},
            ],
            "rules": [
                {
                    "rule": "object_change",
                    "input_count": 1,
                    "output_count": 2,
                    "difference": 1,
                },
            ],
        },
    )

    assert abstraction["primitive"] == "duplicate_object"
    assert abstraction["semantic_concept"] == "replication"
    assert abstraction["causal_effect"] == "increase_object_count"
    assert (
        abstraction["semantic_reclassification_reason"]
        == "object_count_increase"
    )
    assert abstraction["semantic_valid"] is True
    assert abstraction["semantic_contradictions"] == []
    assert abstraction["semantic_evidence"]["object_count_delta"] == 1.0


def test_evidence_validator_rejects_preservation_even_if_reclassification_fails():
    engine = SemanticAbstractionEngine()
    engine.classify_transformation_primitive = (
        lambda hypothesis, primitive, evidence_context=None: (primitive, None)
    )

    abstraction = engine.abstract_hypothesis(
        {
            "type": "object_count_delta",
            "primitive": "preserve_objects",
            "confidence": 1.0,
        },
        evidence_context={
            "patterns": [
                {"pattern": "input_object_count", "value": 1},
                {"pattern": "output_object_count", "value": 2},
                {"pattern": "object_count_changed", "value": True},
            ],
            "rules": [
                {
                    "rule": "object_change",
                    "input_count": 1,
                    "output_count": 2,
                    "difference": 1,
                },
            ],
        },
    )

    assert abstraction["primitive"] == "preserve_objects"
    assert abstraction["semantic_concept"] == "object_identity_preservation"
    assert abstraction["semantic_valid"] is False
    assert abstraction["semantic_consistency"] is False
    assert abstraction["semantic_consistency_reason"] == (
        "semantic_evidence_contradiction"
    )
    assert (
        "object_count_changed_but_object_identity_preservation"
        in abstraction["semantic_contradictions"]
    )
    assert abstraction["semantic_evidence"]["object_count_direction"] == "increase"


def test_shared_task_evidence_prevents_per_hypothesis_fragmentation():
    abstractions = SemanticAbstractionEngine().abstract_hypotheses(
        [
            {
                "type": "contextual_density_change",
                "primitive": "expand_pattern",
                "confidence": 0.97,
            },
            {
                "type": "recursive_symmetry_analysis",
                "primitive": "modify_symmetry",
                "confidence": 0.89,
            },
            {
                "type": "object_count_delta",
                "primitive": "preserve_objects",
                "confidence": 1.0,
                "geometric_grounding": {
                    "delta_type": "object_count",
                    "delta": 0,
                },
            },
        ],
        evidence_context={
            "patterns": [
                {"pattern": "input_object_count", "value": 1},
                {"pattern": "output_object_count", "value": 2},
                {"pattern": "object_count_changed", "value": True},
                {
                    "pattern": "density_change",
                    "value": {
                        "input_density": 0.04,
                        "output_density": 0.08,
                        "difference": 0.04,
                    },
                },
                {
                    "pattern": "symmetry_changes",
                    "value": {
                        "input_horizontal": False,
                        "output_horizontal": False,
                        "input_vertical": True,
                        "output_vertical": False,
                    },
                },
            ],
            "rules": [
                {
                    "rule": "object_change",
                    "input_count": 1,
                    "output_count": 2,
                    "difference": 1,
                },
                {
                    "rule": "density_change",
                    "input_density": 0.04,
                    "output_density": 0.08,
                    "difference": 0.04,
                },
            ],
        },
    )

    evidence_by_concept = {
        abstraction["semantic_concept"]: abstraction["semantic_evidence"]
        for abstraction in abstractions
    }

    assert {
        evidence["object_count_delta"]
        for evidence in evidence_by_concept.values()
    } == {1.0}
    assert {
        evidence["object_count_changed"]
        for evidence in evidence_by_concept.values()
    } == {True}
    assert {
        evidence["density_delta"]
        for evidence in evidence_by_concept.values()
    } == {0.04}
    assert abstractions[2]["primitive"] == "duplicate_object"
    assert abstractions[2]["semantic_concept"] == "replication"


def test_transformation_causal_graph_orders_replication_propagation_symmetry():
    engine = SemanticAbstractionEngine()
    abstractions = engine.abstract_hypotheses(
        [
            {
                "type": "recursive_density_change",
                "primitive": "expand_pattern",
                "confidence": 0.92,
            },
            {
                "type": "symmetry_analysis",
                "primitive": "modify_symmetry",
                "confidence": 0.84,
            },
            {
                "type": "contextual_object_count_delta",
                "primitive": "preserve_objects",
                "confidence": 0.97,
            },
        ],
        evidence_context={
            "patterns": [
                {"pattern": "input_object_count", "value": 1},
                {"pattern": "output_object_count", "value": 2},
                {"pattern": "object_count_changed", "value": True},
                {
                    "pattern": "density_change",
                    "value": {
                        "input_density": 0.08,
                        "output_density": 0.16,
                        "difference": 0.08,
                    },
                },
                {
                    "pattern": "symmetry_changes",
                    "value": {
                        "input_horizontal": False,
                        "output_horizontal": True,
                        "input_vertical": False,
                        "output_vertical": False,
                    },
                },
            ],
            "rules": [
                {
                    "rule": "object_change",
                    "input_count": 1,
                    "output_count": 2,
                    "difference": 1,
                },
                {
                    "rule": "density_change",
                    "input_density": 0.08,
                    "output_density": 0.16,
                    "difference": 0.08,
                },
                {
                    "rule": "symmetry_change",
                    "input_horizontal": False,
                    "output_horizontal": True,
                    "input_vertical": False,
                    "output_vertical": False,
                },
            ],
        },
    )

    graph = engine.build_semantic_graph(abstractions)
    causal_graph = graph["transformation_causal_graph"]

    assert causal_graph["causal_order"] == [
        "replication",
        "propagation",
        "symmetry_reasoning",
    ]
    assert causal_graph["primary_causal_chain"] == [
        "replication",
        "propagation",
        "symmetry_reasoning",
    ]
    assert [
        "replication",
        "propagation",
        "symmetry_reasoning",
    ] in causal_graph["causal_chains"]
    assert causal_graph["causal_chain_count"] >= 1
    assert causal_graph["causal_ordering_ready"] is True
    assert {
        (edge["source"], edge["target"], edge["relation"])
        for edge in causal_graph["edges"]
    } >= {
        (
            "replication",
            "propagation",
            "enables_density_increase",
        ),
        (
            "propagation",
            "symmetry_reasoning",
            "reshapes_symmetry",
        ),
    }
    assert graph["causal_order"] == causal_graph["causal_order"]
    assert graph["primary_causal_chain"] == causal_graph["primary_causal_chain"]
    assert graph["causal_edge_count"] >= 2
    assert graph["causal_chain_count"] >= 1


def test_transformation_causal_graph_links_growth_to_propagation_and_symmetry():
    graph = SemanticAbstractionEngine().build_transformation_causal_graph(
        [
            {
                "concept": "growth",
                "primitive": "expand_object",
                "causal_effect": "increase_area",
                "semantic_class": "additive",
                "confidence": 0.94,
                "semantic_evidence": {
                    "object_count_delta": 0.0,
                    "density_delta": 0.08,
                    "symmetry_changed": True,
                },
            },
            {
                "concept": "propagation",
                "primitive": "expand_pattern",
                "causal_effect": "increase_density",
                "semantic_class": "diffusive",
                "confidence": 0.91,
                "semantic_evidence": {
                    "object_count_delta": 0.0,
                    "density_delta": 0.08,
                    "symmetry_changed": True,
                },
            },
            {
                "concept": "symmetry_reasoning",
                "primitive": "modify_symmetry",
                "causal_effect": "unknown",
                "semantic_class": "transformation",
                "confidence": 0.86,
                "semantic_evidence": {
                    "object_count_delta": 0.0,
                    "density_delta": 0.08,
                    "symmetry_changed": True,
                },
            },
        ]
    )

    assert graph["causal_order"] == [
        "growth",
        "propagation",
        "symmetry_reasoning",
    ]
    assert graph["primary_causal_chain"] == [
        "growth",
        "propagation",
        "symmetry_reasoning",
    ]
    assert {
        (edge["source"], edge["target"], edge["relation"])
        for edge in graph["edges"]
    } >= {
        (
            "growth",
            "propagation",
            "expands_into_density_increase",
        ),
        (
            "growth",
            "symmetry_reasoning",
            "reshapes_symmetry_through_growth",
        ),
        (
            "propagation",
            "symmetry_reasoning",
            "reshapes_symmetry",
        ),
    }


def test_transformation_causal_graph_links_growth_to_containment_pressure():
    graph = SemanticAbstractionEngine().build_transformation_causal_graph(
        [
            {
                "concept": "growth",
                "primitive": "expand_object",
                "semantic_class": "additive",
                "confidence": 0.94,
                "semantic_evidence": {
                    "object_count_delta": 0.0,
                    "density_delta": 0.08,
                },
            },
            {
                "concept": "containment",
                "primitive": "fill_region",
                "semantic_class": "topological",
                "confidence": 0.82,
                "semantic_evidence": {
                    "object_count_delta": 0.0,
                    "density_delta": 0.08,
                },
            },
        ]
    )

    assert graph["primary_causal_chain"] == [
        "growth",
        "containment",
    ]
    assert {
        (edge["source"], edge["target"], edge["relation"])
        for edge in graph["edges"]
    } >= {
        (
            "growth",
            "containment",
            "creates_containment_pressure",
        ),
    }


def test_pattern_rule_evidence_rejects_symmetry_preservation_when_symmetry_changes():
    abstraction = SemanticAbstractionEngine().abstract_hypothesis(
        {
            "type": "symmetry_analysis",
            "primitive": "preserve_symmetry",
            "confidence": 0.91,
        },
        evidence_context={
            "patterns": [
                {
                    "pattern": "symmetry_changes",
                    "value": {
                        "input_horizontal": False,
                        "output_horizontal": False,
                        "input_vertical": True,
                        "output_vertical": False,
                    },
                },
            ],
            "rules": [
                {
                    "rule": "symmetry_change",
                    "input_horizontal": False,
                    "output_horizontal": False,
                    "input_vertical": True,
                    "output_vertical": False,
                },
            ],
        },
    )

    assert abstraction["semantic_concept"] == "symmetry_preservation"
    assert abstraction["semantic_valid"] is False
    assert abstraction["semantic_consistency"] is False
    assert (
        "symmetry_changed_but_preserve_symmetry"
        in abstraction["semantic_contradictions"]
    )


def test_density_increase_reclassifies_preservation_as_propagation():
    abstraction = SemanticAbstractionEngine().abstract_hypothesis(
        {
            "type": "density_change",
            "primitive": "preserve_density",
            "confidence": 0.99,
            "geometric_grounding": {
                "input_density": 2,
                "output_density": 6,
                "density_delta": 4,
            },
        }
    )

    assert abstraction["original_primitive"] == "preserve_density"
    assert abstraction["primitive"] == "expand_pattern"
    assert abstraction["semantic_concept"] == "propagation"
    assert abstraction["causal_effect"] == "increase_density"


def test_stable_object_count_density_increase_reclassifies_as_growth():
    abstraction = SemanticAbstractionEngine().abstract_hypothesis(
        {
            "type": "density_change",
            "primitive": "expand_pattern",
            "confidence": 0.92,
        },
        evidence_context={
            "patterns": [
                {"pattern": "input_object_count", "value": 1},
                {"pattern": "output_object_count", "value": 1},
                {"pattern": "object_count_changed", "value": False},
                {
                    "pattern": "density_change",
                    "value": {
                        "input_density": 0.08,
                        "output_density": 0.16,
                        "difference": 0.08,
                    },
                },
            ],
            "rules": [
                {
                    "rule": "object_change",
                    "input_count": 1,
                    "output_count": 1,
                    "difference": 0,
                },
                {
                    "rule": "density_change",
                    "input_density": 0.08,
                    "output_density": 0.16,
                    "difference": 0.08,
                },
            ],
        },
    )

    assert abstraction["original_primitive"] == "expand_pattern"
    assert abstraction["primitive"] == "expand_object"
    assert abstraction["semantic_concept"] == "growth"
    assert abstraction["causal_effect"] == "increase_area"
    assert (
        abstraction["semantic_reclassification_reason"]
        == "stable_count_density_growth"
    )
    assert abstraction["semantic_evidence"]["object_count_delta"] == 0.0
    assert abstraction["semantic_evidence"]["density_delta"] == 0.08


def test_density_increase_with_object_count_increase_stays_propagation():
    abstraction = SemanticAbstractionEngine().abstract_hypothesis(
        {
            "type": "density_change",
            "primitive": "expand_pattern",
            "confidence": 0.92,
        },
        evidence_context={
            "patterns": [
                {"pattern": "input_object_count", "value": 1},
                {"pattern": "output_object_count", "value": 2},
                {"pattern": "object_count_changed", "value": True},
                {
                    "pattern": "density_change",
                    "value": {
                        "input_density": 0.08,
                        "output_density": 0.16,
                        "difference": 0.08,
                    },
                },
            ],
            "rules": [
                {
                    "rule": "object_change",
                    "input_count": 1,
                    "output_count": 2,
                    "difference": 1,
                },
                {
                    "rule": "density_change",
                    "input_density": 0.08,
                    "output_density": 0.16,
                    "difference": 0.08,
                },
            ],
        },
    )

    assert abstraction["primitive"] == "expand_pattern"
    assert abstraction["semantic_concept"] == "propagation"
    assert abstraction["causal_effect"] == "increase_density"


def test_size_increase_reclassifies_preservation_as_growth():
    abstraction = SemanticAbstractionEngine().abstract_hypothesis(
        {
            "type": "object_size",
            "primitive": "preserve_size",
            "confidence": 0.94,
            "geometric_grounding": {
                "input_total_size": 2,
                "output_total_size": 5,
            },
        }
    )

    assert abstraction["original_primitive"] == "preserve_size"
    assert abstraction["primitive"] == "expand_object"
    assert abstraction["semantic_concept"] == "growth"
    assert abstraction["causal_effect"] == "increase_area"
