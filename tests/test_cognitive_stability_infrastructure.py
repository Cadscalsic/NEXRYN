from runtime.stability.cognitive_stability_infrastructure import (
    CognitiveStabilityInfrastructure,
)


def test_phase_5_cognitive_stability_infrastructure_regulates_overload():

    infrastructure = CognitiveStabilityInfrastructure()

    context = {
        "semantic_fragmentation": 0.8182,
        "identity_drift": 0.4662,
        "projected_overload": 0.8263,
        "raw_reasoning_depth": 11,
        "semantic_activation_report": {
            "top_activations": [
                {
                    "concept": "Object Identity",
                    "activation_strength": 0.91,
                },
                {
                    "concept": "Topology Preservation",
                    "activation_strength": 0.74,
                },
            ],
        },
        "latent_reservoir_report": {
            "latent_concepts": [
                "symmetry_reasoning",
                "attribute_remapping",
            ],
        },
        "archived_cognition": [
            "old_route"
        ],
        "dead_abstractions": [
            "abandoned_shape_rule"
        ],
        "stale_semantic_routes": [
            "route:v1"
        ],
        "orphan_concepts": [
            "unattached_color_rule"
        ],
    }

    updated = infrastructure.run_cycle(
        context
    )

    report = updated[
        "phase_5_cognitive_stability_report"
    ]

    assert report["stability_state"] == "protected"

    assert (
        report["ontology_defragmenter"][
            "semantic_fragmentation_after"
        ]
        <
        0.8182
    )

    assert (
        report["identity_anchor_core"][
            "identity_drift_after"
        ]
        <
        0.4662
    )

    assert (
        report["predictive_collapse_engine"][
            "collapse_risk"
        ]
        ==
        "imminent"
    )

    assert (
        report["recursive_pressure_governor"][
            "regulated_reasoning_depth"
        ]
        ==
        7
    )

    assert (
        report["semantic_virtual_memory"][
            "partition_counts"
        ][
            "active"
        ]
        ==
        2
    )

    assert (
        report["semantic_paging_system"][
            "paging_actions"
        ][
            "latent_to_semantic"
        ]
        ==
        2
    )
