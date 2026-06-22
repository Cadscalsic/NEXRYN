from runtime.reasoning.hypothesis_arbitration_engine import HypothesisArbitrationEngine
from runtime.reasoning.object_centric_reasoner import ObjectCentricReasoner


def test_localized_translation_salience_beats_static_invariant():
    input_objects = [
        {"object_id": "object_1", "centroid": [0, 0], "size": 1, "color": 2},
        {"object_id": "object_2", "centroid": [1, 0], "size": 1, "color": 3},
        {"object_id": "object_3", "centroid": [2, 0], "size": 8, "color": 8},
    ]
    output_objects = [
        {"object_id": "object_1", "centroid": [4, 0], "size": 1, "color": 2},
        {"object_id": "object_2", "centroid": [4, 0], "size": 1, "color": 3},
        {"object_id": "object_3", "centroid": [2, 0], "size": 8, "color": 8},
    ]
    hypotheses = [
        {
            "type": "object_translation",
            "primitive": "translate_down",
            "confidence": 0.75,
            "causal_support": 1.0,
        },
        {
            "type": "object_size",
            "primitive": "preserve_size",
            "confidence": 1.0,
            "causal_support": 1.0,
        },
    ]

    report = ObjectCentricReasoner().reason(
        input_objects=input_objects,
        output_objects=output_objects,
        hypotheses=hypotheses,
    )

    salience = report["TRANSFORMATION_SALIENCE_REPORT"]
    assert salience["dominant_transformation"] == "object_translation"
    assert salience["dominant_transformation"] != "invariant"
    winner = max(
        report["annotated_hypotheses"],
        key=lambda hypothesis: hypothesis["transformation_salience"],
    )
    assert winner["explanatory_power"] > 0.70
    assert report["OBJECT_CHANGE_REPORT"][0]["changed"] is True
    assert report["OBJECT_CHANGE_REPORT"][1]["changed"] is True
    assert report["OBJECT_CHANGE_REPORT"][2]["changed"] is False


def test_arbitration_penalizes_invariant_when_transformation_explains_residuals():
    hypotheses = [
        {
            "type": "object_translation",
            "primitive": "translate_down",
            "confidence": 0.75,
            "explanatory_power": 0.75,
            "residual_reduction": 0.75,
            "transformation_salience": 0.75,
            "causal_support": 1.0,
        },
        {
            "type": "object_size",
            "primitive": "preserve_size",
            "confidence": 1.0,
            "explanatory_power": 0.1,
            "residual_reduction": 0.0,
            "transformation_salience": 0.0,
            "causal_support": 1.0,
        },
    ]

    report = HypothesisArbitrationEngine().build_arbitration_report(hypotheses)

    winner = report["winner"]["hypothesis"]
    assert winner["primitive"] == "translate_down"
    assert report["winner"]["score"] > 0.70
