from core.dependency.process_dependency_memory import ProcessDependencyMemory
from core.math_reasoning.dependency_semantics import DependencySemanticsEngine


def test_build_typed_dependency_record():
    dependency = DependencySemanticsEngine().build_typed_dependency(
        "identity_forking",
        "object_count_increase",
        "causes",
        0.91,
        {"identity_split": True},
        contexts=["replication_context"],
    )

    assert dependency == {
        "source": "identity_forking",
        "target": "object_count_increase",
        "relation": "causes",
        "confidence": 0.91,
        "evidence": {"identity_split": True},
        "contexts": ["replication_context"],
    }


def test_infer_causes_relation():
    relation = DependencySemanticsEngine().infer_relation(
        "identity_forking",
        "object_count_increase",
        {"object_count_change": True, "identity_split": True},
    )

    assert relation == "causes"


def test_infer_requires_relation():
    relation = DependencySemanticsEngine().infer_relation(
        "replication",
        "identity_forking",
        {"requires": True},
    )

    assert relation == "requires"


def test_infer_preserves_relation():
    relation = DependencySemanticsEngine().infer_relation(
        "topology_splitting",
        "local_shape",
        {"preserves": True},
    )

    assert relation == "preserves"


def test_generate_replication_dependency_semantics():
    report = DependencySemanticsEngine().analyze(
        "replication",
        transformation_report={
            "system": "transformation_algebra_engine",
            "transformation_signature": {
                "operator_types": ["duplicate"],
                "changes_object_count": True,
                "preserves_shape": True,
                "preserves_position": False,
                "preserves_color": True,
            },
        },
    )

    dependencies = {
        (item["source"], item["relation"], item["target"])
        for item in report["typed_dependencies"]
    }
    assert ("replication", "requires", "identity_forking") in dependencies
    assert ("identity_forking", "causes", "object_count_increase") in dependencies
    assert report["semantic_dependency_signature"]["process_context"] == "replication_context"
    assert report["semantic_dependency_signature"]["has_causal_chain"] is True


def test_generate_growth_dependency_semantics():
    report = DependencySemanticsEngine().analyze(
        "growth",
        set_report={
            "system": "set_operations_engine",
            "relation": "expanded",
            "added_items": [[1, 2]],
            "removed_items": [],
            "preserved_items": [[1, 1]],
        },
    )

    dependencies = {
        (item["source"], item["relation"], item["target"])
        for item in report["typed_dependencies"]
    }
    assert ("growth", "expands", "topology") in dependencies
    assert ("growth", "preserves", "identity_persistence") in dependencies


def test_generate_propagation_dependency_semantics():
    report = DependencySemanticsEngine().analyze(
        "propagation",
        spatial_report={
            "system": "spatial_relations_engine",
            "relations": [{"relation": "shifted_by"}],
            "spatial_signature": {},
        },
    )

    dependencies = {
        (item["source"], item["relation"], item["target"])
        for item in report["typed_dependencies"]
    }
    assert ("propagation", "propagates", "source_pattern_preserved") in dependencies
    assert ("directional_motion", "transforms", "position_change") in dependencies


def test_compute_semantic_dependency_score():
    engine = DependencySemanticsEngine()
    dependencies = [
        engine.build_typed_dependency("a", "b", "causes", 0.9, {"x": True}),
        engine.build_typed_dependency("b", "c", "preserves", 0.8, {"y": True}),
    ]

    assert engine.semantic_dependency_score(dependencies) > 0.75


def test_export_typed_dependencies_to_process_dependency_memory():
    engine = DependencySemanticsEngine()
    memory = ProcessDependencyMemory(seed_defaults=False)
    dependencies = [
        engine.build_typed_dependency(
            "growth",
            "topology",
            "expands",
            0.9,
            {"expanded": True},
            contexts=["growth_context"],
        )
    ]

    export = engine.export_to_process_dependency_memory(memory, dependencies)
    links = memory.links_for("growth")

    assert export["ingested_links"] == 1
    assert links[0].relation == "modifies"
    assert links[0].metadata["semantic_relation"] == "expands"


def test_explain_dependency_chain():
    engine = DependencySemanticsEngine()
    dependencies = [
        engine.build_typed_dependency("replication", "identity_forking", "requires", 0.91, {}),
        engine.build_typed_dependency("identity_forking", "object_count_increase", "causes", 0.92, {}),
    ]

    explanation = engine.explain_dependency_chain(dependencies)

    assert explanation["chain_length"] == 2
    assert explanation["summary"] == "replication -> identity_forking -> object_count_increase"
