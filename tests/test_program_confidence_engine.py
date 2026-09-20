import math

from runtime.synthesis.program_confidence_engine import (
    CONFIDENCE_COMPONENTS,
    ProgramConfidenceEngine,
)


def _program():
    return {
        "program_id": "program:alpha",
        "program_name": "alpha_program",
        "program_signature": "sig:alpha",
        "required_concepts": ["concept:a", "concept:b"],
        "required_transformations": ["replace_color"],
        "required_constraints": ["preserve_shape"],
        "execution_strategy": {"steps": ["select", "transform", "validate"]},
        "utility": 0.8,
        "historical_success": 0.6,
        "generalization_score": 0.7,
        "lifecycle": "VALIDATED",
        "validation_results": {
            "correctness": 0.82,
            "completeness": 0.76,
            "constraint_satisfaction": 0.74,
            "consistency": 0.78,
            "concept_alignment": 0.9,
            "truth_alignment": 0.72,
            "generalization": 0.7,
            "execution_success": True,
            "accepted": True,
        },
    }


def test_program_confidence_engine_is_deterministic_and_explainable():
    engine = ProgramConfidenceEngine()

    first = engine.evaluate_program(_program())
    second = engine.evaluate_program(_program())

    assert first == second
    assert first["program_id"] == "program:alpha"
    assert 0.0 < first["confidence"] <= 1.0
    assert first["confidence_level"] in {"MEDIUM", "HIGH", "VERY_HIGH", "CANONICAL"}
    assert set(first["confidence_components"]) == set(CONFIDENCE_COMPONENTS)
    assert first["confidence_reason"]
    assert first["validation_status"] == "VALIDATED"
    assert first["stability_score"] > 0.0
    assert first["generalization_score"] == first["confidence_components"]["generalization_confidence"]
    assert first["transfer_score"] == first["confidence_components"]["transfer_confidence"]
    assert first["reuse_score"] == first["confidence_components"]["historical_confidence"]


def test_program_confidence_engine_rejects_invalid_component_values():
    engine = ProgramConfidenceEngine()

    errors = engine._validate_confidence(math.inf)

    assert "infinite" in errors


def test_program_confidence_report_exposes_distribution_and_counts():
    report = ProgramConfidenceEngine().build_report([_program()])

    assert report["PROGRAM_CONFIDENCE_REPORT"] is True
    assert report["program_confidence_authority"] is True
    assert report["programs_evaluated"] == 1
    assert report["average_program_confidence"] > 0.0
    assert report["highest_program_confidence"] >= report["average_program_confidence"]
    assert report["lowest_program_confidence"] <= report["average_program_confidence"]
    assert sum(report["confidence_distribution"].values()) == 1
    assert report["validated_program_count"] == 1
