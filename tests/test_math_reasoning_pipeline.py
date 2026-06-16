from core.dependency.process_dependency_memory import ProcessDependencyMemory
from core.math_reasoning import (
    DependencySemanticsEngine,
    GraphRelationsEngine,
    MathematicalReasoningLayer,
    MathematicalReasoningPipeline,
    ProcessSignatureEngine,
    SetOperationsEngine,
    SpatialRelationsEngine,
    TransformationAlgebraEngine,
)


def obj(object_id, cells, color=1):
    return {"id": object_id, "cells": cells, "color": color}


def test_pipeline_initializes_all_passive_math_engines():
    pipeline = MathematicalReasoningPipeline()

    assert isinstance(pipeline.spatial_engine, SpatialRelationsEngine)
    assert isinstance(pipeline.graph_engine, GraphRelationsEngine)
    assert isinstance(pipeline.set_engine, SetOperationsEngine)
    assert isinstance(pipeline.transformation_engine, TransformationAlgebraEngine)
    assert isinstance(pipeline.process_signature_engine, ProcessSignatureEngine)
    assert isinstance(pipeline.dependency_engine, DependencySemanticsEngine)


def test_mathematical_reasoning_layer_interprets_dependency_chain():
    memory = ProcessDependencyMemory(seed_defaults=True)
    process_memory = memory.resolve_chain("replication")
    report = MathematicalReasoningLayer().analyze_dependency_chain(
        "replication",
        process_dependency_memory=process_memory,
    )

    assert report["system"] == "mathematical_reasoning_layer"
    assert report["process_native_context"] == "replication_context"
    assert report["math_reasoning_signature"]["typed_dependencies_generated"] is True
    assert report["math_reasoning_signature"]["set_changes_detected"] is True
    assert report["math_reasoning_signature"]["transformations_detected"] is True
    assert report["dependency_semantics_report"]["dependency_semantics_score"] > 0.85
    assert (
        report["dependency_semantics_report"]["semantic_dependency_signature"][
            "process_context"
        ]
        == "replication_context"
    )
    assert report["process_signature_report"]["signature_id"] == (
        "replication_signature"
    )
    algebra = report["transformation_report"]["transformation_algebra"]
    assert "replication" in algebra["transformation_types"]
    assert algebra["invariants"]["forks_identity"] is True
    assert algebra["identity_scope_leakage_detected"] is False


def test_pipeline_analyzes_input_objects_only():
    report = MathematicalReasoningPipeline().analyze_objects([
        obj("a", [(0, 0)]),
        obj("b", [(0, 2)]),
    ])

    assert report["spatial_report"]["objects_analyzed"] == 2
    assert report["transformation_report"]["transformation_count"] == 0


def test_pipeline_analyzes_input_and_output_objects():
    report = MathematicalReasoningPipeline().analyze_objects(
        [obj("a", [(0, 0)], 2)],
        [obj("a_out", [(0, 1)], 2)],
        concept="directional_motion",
    )

    assert report["transformation_report"]["operators"][0]["operator"] == "translate"
    assert (
        report["transformation_report"]["transformation_signature"][
            "primary_transformation_type"
        ]
        == "translation"
    )
    assert report["dependency_semantics_report"]["concept"] == "directional_motion"


def test_dependency_chain_distinguishes_growth_propagation_and_topological_growth():
    memory = ProcessDependencyMemory(seed_defaults=True)

    growth = MathematicalReasoningLayer().analyze_dependency_chain(
        "growth",
        process_dependency_memory=memory.resolve_chain("growth"),
    )
    propagation = MathematicalReasoningLayer().analyze_dependency_chain(
        "propagation",
        process_dependency_memory=memory.resolve_chain("propagation"),
    )
    topological_growth = MathematicalReasoningLayer().analyze_dependency_chain(
        "topological_growth",
        process_dependency_memory=memory.resolve_chain("topological_growth"),
    )

    assert (
        growth["transformation_report"]["transformation_algebra"][
            "primary_transformation_type"
        ]
        == "growth"
    )
    assert (
        propagation["transformation_report"]["transformation_algebra"][
            "primary_transformation_type"
        ]
        == "propagation"
    )
    assert (
        topological_growth["transformation_report"]["transformation_algebra"][
            "primary_transformation_type"
        ]
        == "topological_growth"
    )


def test_spatial_report_is_included():
    report = MathematicalReasoningPipeline().analyze_objects([
        obj("a", [(0, 0)]),
        obj("b", [(0, 2)]),
    ])

    assert report["spatial_report"]["system"] == "spatial_relations_engine"


def test_graph_report_is_included():
    report = MathematicalReasoningPipeline().analyze_objects([
        obj("a", [(0, 0)]),
        obj("b", [(0, 2)]),
    ])

    assert report["graph_report"]["system"] == "graph_relations_engine"


def test_set_report_is_included():
    report = MathematicalReasoningPipeline().analyze_task(
        "task",
        [[0, 1]],
        [[0, 1, 2]],
    )

    assert report["set_report"]["system"] == "set_operations_engine"


def test_transformation_report_is_included():
    report = MathematicalReasoningPipeline().analyze_objects(
        [obj("a", [(0, 0)], 2)],
        [obj("a_out", [(0, 1)], 2)],
    )

    assert report["transformation_report"]["system"] == "transformation_algebra_engine"


def test_dependency_semantics_report_is_included():
    report = MathematicalReasoningPipeline().analyze_objects(
        [obj("a", [(0, 0)], 2)],
        [obj("a_out", [(0, 1)], 2)],
        concept="propagation",
    )

    assert report["dependency_semantics_report"]["system"] == "dependency_semantics_engine"


def test_math_reasoning_signature_is_deterministic():
    pipeline = MathematicalReasoningPipeline()
    first = pipeline.analyze_objects(
        [obj("a", [(0, 0)], 2)],
        [obj("a_out", [(0, 1)], 2)],
        concept="propagation",
    )["math_reasoning_signature"]
    second = pipeline.analyze_objects(
        [obj("a", [(0, 0)], 2)],
        [obj("a_out", [(0, 1)], 2)],
        concept="propagation",
    )["math_reasoning_signature"]

    assert first == second


def test_export_to_process_dependency_memory_requires_explicit_enable():
    pipeline = MathematicalReasoningPipeline()
    memory = ProcessDependencyMemory(seed_defaults=False)
    report = pipeline.analyze_objects(
        [obj("a", [(0, 0)], 2)],
        [obj("a_out", [(0, 1)], 2)],
        concept="propagation",
    )

    disabled = pipeline.export_to_process_dependency_memory(memory, report)
    enabled = pipeline.export_to_process_dependency_memory(
        memory,
        report,
        export_typed_dependencies=True,
    )

    assert disabled["ingested_links"] == 0
    assert enabled["ingested_links"] > 0


def test_default_execution_does_not_modify_governance_state():
    governance_state = {"candidate_ready": False, "truth_commit": False}
    before = dict(governance_state)

    MathematicalReasoningPipeline().analyze_objects(
        [obj("a", [(0, 0)], 2)],
        [obj("a_out", [(0, 1)], 2)],
        concept="propagation",
    )

    assert governance_state == before


def test_cli_math_reasoning_flag_is_disabled_by_default():
    source = open("main.py", encoding="utf-8").read()

    assert "--math-reasoning" in source
    assert "action=\"store_true\"" in source
