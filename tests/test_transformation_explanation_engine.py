from runtime.reasoning.transformation_explanation_engine import (
    TransformationExplanationEngine,
)
from runtime.reasoning.transformation_synthesis_engine import TransformationSynthesisEngine
from runtime.memory.transformation_memory import TransformationMemory
from runtime.transforms.primitive_executor import PrimitiveExecutor


def test_explanation_engine_compresses_gravity_micro_concepts():
    report = TransformationExplanationEngine().explain([
        "gravity",
        "falling",
        "support",
        "collision",
        "rest_state",
        "downward_motion",
        "component_merging",
        "connectivity_change",
        "topology_change",
        "transformation_sequence",
    ])

    selected = report["selected_explanation"]

    assert report["TRANSFORMATION_EXPLANATION_REPORT"] is True
    assert selected["explanation_id"] == "gravity_simulation_with_collision"
    assert selected["macro_concept"] == "gravity_simulation"
    assert "translate" in selected["canonical_operations"]
    assert report["executable_explanation"] is True


def test_explanation_engine_compresses_symmetric_object_creation():
    report = TransformationExplanationEngine().explain([
        "object_creation",
        "density_increase",
        "symmetry_creation",
        "relative_position",
        "spatial_relation",
        "topology_change",
    ])

    selected = report["selected_explanation"]

    assert selected["explanation_id"] == "symmetric_object_creation"
    assert selected["macro_concept"] == "symmetric_object_creation"
    assert "density" in selected["theory_families"]
    assert "duplicate" in selected["canonical_operations"]


def test_explanation_engine_compresses_symbolic_remapping():
    report = TransformationExplanationEngine().explain([
        "symbolic_remapping",
        "color_mapping",
        "shape_preservation",
        "object_identity_preservation",
    ])

    selected = report["selected_explanation"]

    assert selected["explanation_id"] == "symbolic_color_remapping"
    assert selected["macro_concept"] == "symbolic_color_remapping"
    assert selected["canonical_operations"] == ["recolor"]


def test_synthesis_surfaces_explanation_before_theory_and_mechanism():
    report = TransformationSynthesisEngine(
        memory=TransformationMemory(),
        executor=PrimitiveExecutor(),
    ).synthesize(
        input_grid=[[1, 0]],
        output_grid=[[5, 0]],
        detected_concepts=[
            "symbolic_remapping",
            "color_mapping",
            "transformation_sequence",
        ],
    )

    synthesis = report["TRANSFORMATION_SYNTHESIS_REPORT"]
    explanation = synthesis["transformation_explanation_report"]
    theory = synthesis["transformation_theory_report"]

    assert explanation["macro_concept"] == "symbolic_color_remapping"
    assert theory["macro_concept"] == "symbolic_color_remapping"
    assert synthesis["selected_program"]["steps"][0]["operation"] == "recolor"
    assert synthesis["transformation_accuracy"] == 1.0
