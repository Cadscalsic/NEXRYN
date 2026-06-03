from runtime.stability.cognitive_thermodynamics import (
    CognitiveThermodynamics,
)


def test_cognitive_thermodynamics_dissipates_critical_semantic_heat():

    thermodynamics = CognitiveThermodynamics()

    context = {
        "runtime_entropy": 0.8868,
        "semantic_distance_fields_report": {
            "average_merge_risk": 0.74,
        },
        "dynamic_cognitive_swapping_report": {
            "observed_concept_count": 19,
            "latent_concepts": [
                {
                    "concept": f"latent_concept_{index}",
                }
                for index in range(8)
            ],
        },
        "predictive_attention_routing_v2_report": {
            "rebuilt_routes": [
                {
                    "entropy_delta_after": 0.66,
                },
                {
                    "entropy_delta_after": 0.58,
                },
            ],
        },
        "distributed_semantic_execution_fabric_report": {
            "entropy_field_regulator": {
                "semantic_heat_after": 0.79,
            },
        },
        "hierarchical_attention_collapse_report": {
            "attention_saturation_after": 0.67,
        },
        "recursive_budget_market_report": {
            "allocations": [
                {
                    "hypothesis": "low_entropy_shape_rule",
                    "expected_utility": 0.78,
                    "cognitive_energy_cost": 0.34,
                },
                {
                    "hypothesis": "compact_color_rule",
                    "expected_utility": 0.69,
                    "cognitive_energy_cost": 0.29,
                },
            ],
        },
    }

    updated = thermodynamics.run_cycle(
        context
    )

    report = updated[
        "cognitive_thermodynamics_report"
    ]

    entropy_field = report[
        "entropy_field_engine"
    ]

    assert entropy_field["explosion_risk"] in [
        "high",
        "critical",
    ]

    cooling = report[
        "semantic_cooling_system"
    ]

    assert cooling["cooling_strength"] >= 0.24

    dissipation = report[
        "semantic_heat_dissipation"
    ]

    assert (
        dissipation["semantic_heat_after"]
        <
        dissipation["semantic_heat_before"]
    )

    assert (
        report["attention_economics"][
            "market_policy"
        ]
        ==
        "tax_hot_attention"
    )

    assert (
        len(
            report["cognitive_energy_router"][
                "allocations"
            ]
        )
        >
        0
    )
