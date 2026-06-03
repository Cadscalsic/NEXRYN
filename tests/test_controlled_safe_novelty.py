from runtime.stability.controlled_safe_novelty import (
    ControlledSafeNovelty,
    NoveltyPromotionGate,
)


def test_controlled_safe_novelty_de_escalates_overprotection():

    novelty = ControlledSafeNovelty()

    context = {
        "runtime_entropy": 0.9136,
        "executive_state": "identity_protection",
        "cognitive_identity_report": {
            "identity_state": "identity_guarded",
            "identity_risk": 0.74,
        },
        "identity_core_report": {
            "identity_drift": 0.4662,
        },
        "identity_anchor_core_report": {
            "identity_drift_before": 0.4662,
        },
        "rejected_merges": [
            {
                "sources": [
                    "symbolic_remapping",
                    "attribute_substitution",
                ],
            },
        ],
        "mutation_candidates": [
            {
                "proposal": "low_entropy_variant",
            },
        ],
        "recursive_paths": [
            "branch:counterfactual_shape_rule",
        ],
    }

    updated = novelty.run_cycle(
        context
    )

    report = updated[
        "controlled_safe_novelty_report"
    ]

    assert report["novelty_state"] == "reopened_under_sandbox"

    assert (
        report["semantic_immune_confidence_calibration"][
            "immunity_state"
        ]
        ==
        "de_escalated"
    )

    assert (
        report["safe_exploratory_sandbox"][
            "core_identity_contamination"
        ]
        ==
        0.0
    )

    assert (
        report["conceptive_neurogenesis"][
            "generated_count"
        ]
        >
        0
    )

    assert (
        report["recursive_simulation_worlds"][
            "direct_reasoning_bypass"
        ]
        is True
    )

    assert (
        report["identity_elasticity_layer"][
            "identity_guardian_mode"
        ]
        ==
        "advisor"
    )

    assert (
        report["novelty_promotion_gate"][
            "minimum_task_count"
        ]
        ==
        3
    )


def test_novelty_promotion_gate_keeps_half_viable_concepts_latent():

    gate = NoveltyPromotionGate()

    context = {
        "runtime_entropy": 0.9136,
    }

    neurogenesis_report = {
        "generated_concepts": [
            {
                "concept": (
                    "bridge_object_identity_preservation_"
                    "shape_preservation"
                ),
                "viability": 0.4996,
                "status": "sandbox_candidate",
            },
        ],
    }

    worlds_report = {
        "worlds": [
            {
                "release_recommendation": "release_to_latent_memory",
            },
        ],
    }

    elasticity_report = {
        "elasticity": 0.46,
        "novelty_release_budget": 0.39,
    }

    report = gate.evaluate(
        context,
        neurogenesis_report,
        worlds_report,
        elasticity_report
    )

    evaluation = report[
        "evaluations"
    ][0]

    assert evaluation["task_count"] == 3

    assert evaluation["decision"] == "latent"

    assert (
        evaluation["average_entropy_impact"]
        >
        0
    )

    assert (
        evaluation["average_identity_continuity"]
        >
        0
    )

    assert (
        evaluation["average_execution_usefulness"]
        >
        0
    )
