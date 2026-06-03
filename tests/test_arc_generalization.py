from runtime.reasoning.generalization import (
    ARCGeneralizationEngine,
)


def test_arc_generalization_extracts_rules_traits_causality_and_analogies():

    engine = ARCGeneralizationEngine()

    context = {
        "task_signature": {
            "shape": "3x3",
        },
        "evolutionary_memory_report": {
            "adaptive_trait_memory": {
                "traits": [
                    {
                        "id": "directional_motion",
                        "niche": "spatial_causal_reasoning",
                        "fitness": 0.72,
                        "inheritance_strength": 0.68,
                        "stability_score": 0.70,
                    },
                ],
            },
        },
    }

    symbolic_report = {
        "generalized_rules": [
            {
                "abstract_rule": "translate_right",
                "semantic_meaning": "move object along x axis",
                "confidence": 0.81,
            },
        ],
    }

    causal_report = {
        "causal_strength": 0.74,
        "dependencies": [
            {
                "source": "object_translation",
                "target": "position_shift",
            },
        ],
    }

    analogical_report = {
        "matches": [
            {
                "similarity": 0.77,
                "experience": {
                    "task_signature": {
                        "shape": "3x3",
                    },
                    "reasoning_result": {
                        "rule": "translate_right",
                    },
                },
            },
        ],
    }

    transfer_insight = {
        "transfer_detected": True,
        "transfer_confidence": 0.77,
        "recommended_reasoning": {
            "rule": "translate_right",
        },
    }

    spatial_report = {
        "hypotheses": [
            {
                "type": "object_translation",
                "description": "object shifts right",
                "confidence": 0.83,
            },
        ],
    }

    report = engine.run_cycle(
        context,
        symbolic_report,
        causal_report,
        analogical_report,
        transfer_insight,
        spatial_report,
    )

    assert report["abstract_rule_count"] >= 2
    assert report["transferable_trait_count"] == 1
    assert report["causal_abstraction_count"] == 1
    assert report["symbolic_analogy_count"] >= 1

    assert (
        report["generalization_state"]
        in [
            "general_adaptive_cognition",
            "arc_generalization_forming",
        ]
    )
