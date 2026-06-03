from core.ontological_stability import (
    InvariantBoundaryEngine,
    InvariantLevel,
    ontological_boundary_system,
)


def test_invariant_hierarchy_marks_core_truths_non_negotiable():

    engine = InvariantBoundaryEngine()

    absolute = engine.classify(
        "causal_continuity",
    )

    contextual = engine.classify(
        "symbolic_representation",
    )

    assert InvariantLevel.ABSOLUTE.name == absolute["level"]
    assert absolute["negotiable"] is False
    assert contextual["level"] == InvariantLevel.CONTEXTUAL.name
    assert contextual["negotiable"] is True


def test_ontological_boundary_system_freezes_existentially_risky_evolution():

    context = {
        "semantic_spine_report":
        {
            "spine_integrity": 0.31,
            "semantic_spine_state": "fragile_semantic_spine",
            "semantic_elastic_topology":
            {
                "elasticity": 0.18,
                "adaptation_without_collapse": False,
            },
        },

        "identity_reasoner_report":
        {
            "identity_analyses":
            [
                {
                    "failure_explanation":
                    {
                        "failure_reasons":
                        [
                            "causal_role_conflict",
                            "unsafe_merge_memory",
                        ],
                        "hidden_conflicts":
                        {
                            "conflict_layers":
                            [
                                "causal",
                            ],
                        },
                        "coherence":
                        {
                            "identity_coherence": 1.0,
                        },
                    },
                    "merge_stability":
                    {
                        "merge_state": "unstable_merge",
                        "semantic_similarity": 1.0,
                    },
                },
            ],
        },

        "extinction_engine_report":
        {
            "extinct_count": 1,
            "extinct_traits":
            [
                {
                    "id": "topology_preservation",
                    "trait_state": "extinct",
                },
            ],
        },

        "evolutionary_graveyard_report":
        {
            "graveyard_pressure":
            {
                "pressure_score": 0.62,
            },
        },

        "proposed_contextual_negotiations":
        [
            {
                "target": "constitutional_truth",
            },
            {
                "target": "symbolic_forms",
            },
        ],
    }

    report = ontological_boundary_system.run_cycle(
        context,
    )

    policy = report["ontological_policy"]

    assert report["layer"] == "contextual_existential_stabilization"
    assert policy["freeze_new_fusions"] is True
    assert policy["freeze_high_risk_mutations"] is True
    assert policy["increase_temporal_validation"] is True
    assert report["semantic_spine_protection"]["fragile_semantic_spine"] is True
    assert report["identity_boundary"]["blocked_identity_fusions"] == 1
    assert report["contextual_negotiation_limits"]["blocked_negotiations"]
    assert report["invariant_survival"]["rehabilitated_invariants"][0]["invariant_id"] == "topology_preservation"
    assert report["ontological_recovery"]["recovery_state"] == "ontological_recovery_active"
