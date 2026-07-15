from runtime.reasoning.transformation_language_engine import TransformationLanguageEngine
from runtime.reasoning.transformation_explanation_engine import (
    TransformationExplanationEngine,
)
from runtime.reasoning.transformation_synthesis_engine import TransformationSynthesisEngine
from runtime.memory.transformation_memory import TransformationMemory
from runtime.transforms.primitive_executor import PrimitiveExecutor


def test_language_engine_builds_gravity_if_until_statement():
    report = TransformationLanguageEngine().parse([
        "gravity",
        "falling",
        "collision",
        "support",
        "rest_state",
        "downward_motion",
        "topology_change",
    ])

    statement = report["primary_statement"]

    assert report["TRANSFORMATION_LANGUAGE_REPORT"] is True
    assert statement["statement_id"] == "gravity_motion_statement"
    assert statement["subject"] == "object"
    assert statement["action"] == "MOVE"
    assert statement["condition"] == "IF_UNSUPPORTED"
    assert statement["termination"] == "UNTIL_COLLISION_OR_SUPPORT"
    assert "ESTABLISH_SUPPORT" in statement["postconditions"]


def test_language_engine_assigns_symbolic_removal_roles():
    report = TransformationLanguageEngine().parse([
        "symbolic_remapping",
        "object_removal",
        "color_elimination",
        "relative_position",
    ])

    statement = report["primary_statement"]

    assert statement["statement_id"] == "symbolic_color_statement"
    assert statement["action"] == "REMAP+ELIMINATE_COLOR+REMOVE_OBJECT"
    assert "PRESERVE_RELATIVE_POSITION" in statement["constraints"]
    assert "action" in report["grammar_roles"]
    assert "spatial_relation" in report["grammar_roles"]


def test_language_engine_builds_symmetric_creation_statement():
    report = TransformationLanguageEngine().parse([
        "object_creation",
        "density_increase",
        "symmetry_creation",
        "relative_position",
        "topology_change",
    ])

    statement = report["primary_statement"]

    assert statement["statement_id"] == "symmetric_creation_statement"
    assert statement["action"] == "CREATE"
    assert statement["relation"] == "SYMMETRIC_RELATION"
    assert "INCREASE_DENSITY" in statement["constraints"]


def test_explanation_uses_transformation_language_statement():
    language = TransformationLanguageEngine().parse([
        "symbolic_remapping",
        "color_mapping",
        "object_removal",
        "color_elimination",
        "relative_position",
    ])
    explanation = TransformationExplanationEngine().explain(
        [
            "symbolic_remapping",
            "color_mapping",
            "object_removal",
            "color_elimination",
            "relative_position",
        ],
        transformation_language_report=language,
    )

    selected = explanation["selected_explanation"]

    assert explanation["primary_statement"]["statement_id"] == "symbolic_color_statement"
    assert selected["statement_id"] == "symbolic_color_statement"
    assert selected["transformation_statement"]["action"] == "REMAP+ELIMINATE_COLOR+REMOVE_OBJECT"


def test_synthesis_surfaces_language_before_explanation():
    report = TransformationSynthesisEngine(
        memory=TransformationMemory(),
        executor=PrimitiveExecutor(),
    ).synthesize(
        input_grid=[[1, 0]],
        output_grid=[[5, 0]],
        detected_concepts=[
            "symbolic_remapping",
            "color_mapping",
            "relative_position",
            "transformation_sequence",
        ],
    )

    synthesis = report["TRANSFORMATION_SYNTHESIS_REPORT"]
    language = synthesis["transformation_language_report"]
    explanation = synthesis["transformation_explanation_report"]

    assert language["primary_statement"]["statement_id"] == "symbolic_color_statement"
    assert explanation["primary_statement"]["statement_id"] == "symbolic_color_statement"
    assert synthesis["selected_program"]["steps"][0]["operation"] == "recolor"
    assert synthesis["transformation_accuracy"] == 1.0
