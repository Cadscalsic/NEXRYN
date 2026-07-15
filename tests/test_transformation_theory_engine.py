from runtime.reasoning.transformation_theory_engine import TransformationTheoryEngine
from runtime.reasoning.mechanistic_reasoning_engine import MechanisticReasoningEngine
from runtime.reasoning.transformation_synthesis_engine import TransformationSynthesisEngine
from runtime.memory.transformation_memory import TransformationMemory
from runtime.transforms.primitive_executor import PrimitiveExecutor


def test_theory_engine_builds_canonical_density_transformation_space():
    report = TransformationTheoryEngine().build_theory([
        "density_increase",
        "relative_position",
        "spatial_relation",
    ])

    classes = report["transformation_space"]["classes"]
    density = report["transformation_theories"][0]

    assert report["TRANSFORMATION_THEORY_REPORT"] is True
    assert "OBJECT_EXPANSION" in classes
    assert "SPATIAL_TRANSFORMATION" in classes
    assert density["subtype"] == "DENSITY_MODULATION"
    assert "duplication" in density["mechanisms"]
    assert "expand" in report["transformation_space"]["operations"]
    assert report["worldview_count"] == 2


def test_theory_engine_covers_core_arc_transformation_families():
    report = TransformationTheoryEngine().build_theory([
        "density_increase",
        "rotation_reflection",
        "symbolic_remapping",
        "gravity",
        "object_counting",
        "connectivity_change",
        "transformation_sequence",
    ])

    assert report["transformation_space"]["classes"] == [
        "COMPOUND_TRANSFORMATION",
        "OBJECT_EXPANSION",
        "PHYSICS_TRANSFORMATION",
        "QUANTITY_TRANSFORMATION",
        "SPATIAL_TRANSFORMATION",
        "SYMBOLIC_TRANSFORMATION",
        "TOPOLOGICAL_TRANSFORMATION",
    ]
    assert report["worldview_count"] == 7
    assert "ordered_composition" in report["transformation_space"]["mechanisms"]


def test_mechanistic_reasoning_embeds_transformation_theory_constraints():
    theory = TransformationTheoryEngine().build_theory([
        "gravity",
        "falling",
        "support",
    ])
    report = MechanisticReasoningEngine().reason(
        concepts=["gravity", "falling", "support"],
        input_grid=[[0], [2], [0]],
        output_grid=[[0], [0], [2]],
        transformation_theory_report=theory,
    )

    graph = report["mechanism_graphs"][0]

    assert graph["transformation_class"] == "PHYSICS_TRANSFORMATION"
    assert "support_stops_motion" in graph["theory_constraints"]
    assert "support_surfaces" in graph["theory_dependencies"]
    assert graph["candidate_operations"] == ["translate"]


def test_synthesis_surfaces_theory_before_mechanisms_and_execution():
    report = TransformationSynthesisEngine(
        memory=TransformationMemory(),
        executor=PrimitiveExecutor(),
    ).synthesize(
        input_grid=[[1, 0, 0]],
        output_grid=[[5, 0, 0]],
        detected_concepts=[
            "symbolic_remapping",
            "color_mapping",
            "transformation_sequence",
        ],
    )

    synthesis = report["TRANSFORMATION_SYNTHESIS_REPORT"]
    theory = synthesis["transformation_theory_report"]

    assert theory["theory_families"] == ["color", "compound"]
    assert "SYMBOLIC_TRANSFORMATION" in theory["transformation_space"]["classes"]
    assert "COMPOUND_TRANSFORMATION" in theory["transformation_space"]["classes"]
    assert synthesis["selected_program"]["steps"][0]["operation"] == "recolor"
    assert synthesis["transformation_accuracy"] == 1.0
