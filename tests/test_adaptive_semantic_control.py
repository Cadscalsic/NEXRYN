from runtime.stability.adaptive_semantic_control import (
    AdaptiveSemanticControl,
)


def test_adaptive_semantic_control_builds_probabilistic_guards():

    control = AdaptiveSemanticControl()

    context = {
        "semantic_pointer_report": {
            "pointers": [
                {
                    "canonical_concept": "directional_motion",
                },
                {
                    "canonical_concept": "position_shift",
                },
                {
                    "canonical_concept": "symbolic_remapping",
                },
            ],
        },
        "semantic_activation_report": {
            "top_activations": [
                {
                    "concept": "directional_motion",
                    "activation_strength": 0.92,
                },
                {
                    "concept": "symbolic_remapping",
                    "activation_strength": 0.70,
                },
            ],
        },
        "dynamic_attention_allocation": {
            "attention_saturation": 0.91,
        },
        "attention_kernel_report": {
            "focus_window": [
                {
                    "key": "reasoning_hypotheses",
                    "priority": 0.95,
                },
                {
                    "key": "semantic_abstractions",
                    "priority": 0.88,
                },
            ],
        },
        "reasoning_hypotheses": [
            "deep_recursive_symbolic_route",
        ],
        "projected_entropy": 9,
    }

    updated = control.run_semantic_control(
        context
    )

    report = updated[
        "adaptive_semantic_control_report"
    ]

    assert (
        report["adaptive_semantic_compression"][
            "compression_mode"
        ]
        ==
        "probabilistic_semantic_folding"
    )

    assert (
        report["semantic_distance_fields"][
            "distance_count"
        ]
        >
        0
    )

    assert (
        report["hierarchical_attention_collapse"][
            "collapse_policy"
        ]
        ==
        "collapse_to_apex"
    )

    assert (
        report["cognitive_predictive_routing"][
            "routing_state"
        ]
        in [
            "guarded",
            "unsafe",
        ]
    )

    first_decay_count = (
        report["active_concept_decay"][
            "active_concept_count"
        ]
    )

    updated[
        "semantic_activation_report"
    ] = {
        "top_activations": []
    }

    updated = control.run_semantic_control(
        updated
    )

    second_decay = updated[
        "active_concept_decay_report"
    ]

    assert (
        second_decay[
            "active_concept_count"
        ]
        <=
        first_decay_count
    )
