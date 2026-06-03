from runtime.stability.cognitive_operating_system_layer import (
    CognitiveOperatingSystemLayer,
)


def test_cognitive_operating_system_pages_reroutes_and_auctions_budget():

    os_layer = CognitiveOperatingSystemLayer()

    context = {
        "runtime_entropy": 0.9136,
        "active_concept_decay_report": {
            "activation_state": [
                {
                    "concept": f"concept_{index}",
                    "activation_strength": 1.0 - index * 0.04,
                }
                for index in range(13)
            ],
        },
        "cognitive_predictive_routing_report": {
            "routes": [
                {
                    "route": "deep_recursive_symbolic_route",
                    "entropy_delta": 0.82,
                    "collapse_risk": 0.91,
                    "route_policy": "block",
                },
            ],
        },
        "reasoning_hypotheses": [
            {
                "type": "compact_shape_rule",
                "confidence": 0.82,
            },
            {
                "type": "deep_recursive_symbolic_route",
                "confidence": 0.55,
            },
        ],
    }

    updated = os_layer.run_cycle(
        context
    )

    report = updated[
        "cognitive_operating_system_report"
    ]

    swapping = report[
        "dynamic_cognitive_swapping"
    ]

    assert swapping["observed_concept_count"] == 13

    assert swapping["loaded_concept_count"] < 13

    assert swapping["virtual_cognition_paging"] is True

    routing = report[
        "predictive_attention_routing_v2"
    ]

    assert routing["routing_state"] == "rerouted"

    assert (
        routing["alternate_low_entropy_paths"][0][
            "route_policy_after"
        ]
        ==
        "reroute"
    )

    assert (
        routing["alternate_low_entropy_paths"][0][
            "collapse_risk_after"
        ]
        <
        0.91
    )

    market = report[
        "recursive_budget_market"
    ]

    assert market["market_mode"] == "cognitive_energy_auction"

    assert len(
        market["allocations"]
    ) > 0

    assert (
        market["winner"][
            "recursion_budget_granted"
        ]
        > 0
    )
