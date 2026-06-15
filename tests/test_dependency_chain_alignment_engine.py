from runtime.dependency_chain_alignment_engine import (
    DependencyChainAlignmentEngine,
)


def test_dependency_chain_alignment_generates_typed_memory_links():
    report = DependencyChainAlignmentEngine().evaluate(
        "growth",
        runtime_dependency_chain={
            "resolved_dependency_chain": [
                "growth",
                "identity_persistence",
                "identity_continuity",
                "topology_expansion",
            ],
            "dependency_confidence": 0.91,
            "dependency_chain_coverage": 0.90,
        },
        process_dependency_memory={
            "resolved_dependency_chain": [
                "growth",
                "identity_persistence",
                "identity_continuity",
                "topology_expansion",
            ],
            "dependency_confidence": 0.91,
            "dependency_chain_coverage": 0.90,
        },
    )

    relations = {
        (link["source"], link["relation"], link["target"])
        for link in report["memory_ready_links"]
    }

    assert report["alignment_ready"] is True
    assert (
        "growth",
        "requires",
        "identity_persistence",
    ) in relations
    assert (
        "identity_persistence",
        "modifies",
        "identity_continuity",
    ) in relations
    assert (
        "identity_continuity",
        "creates",
        "topology_expansion",
    ) in relations
    assert all(
        link["metadata"]["semantic_relation_inferred"] is True
        for link in report["memory_ready_links"]
    )


def test_dependency_chain_alignment_types_replication_process_edges():
    report = DependencyChainAlignmentEngine().evaluate(
        "replication",
        runtime_dependency_chain={
            "resolved_dependency_chain": [
                "replication",
                "source_pattern_preserved",
                "identity_forking",
                "identity_split",
                "object_count_increase",
                "topological_growth",
            ],
            "dependency_confidence": 0.90,
            "dependency_chain_coverage": 0.90,
        },
        process_dependency_memory={
            "resolved_dependency_chain": [
                "replication",
                "source_pattern_preserved",
                "identity_forking",
                "identity_split",
                "object_count_increase",
                "topological_growth",
            ],
            "dependency_confidence": 0.90,
            "dependency_chain_coverage": 0.90,
        },
    )

    relations = {
        (link["source"], link["relation"], link["target"])
        for link in report["memory_ready_links"]
    }

    assert report["alignment_ready"] is True
    assert (
        "replication",
        "requires",
        "source_pattern_preserved",
    ) in relations
    assert (
        "source_pattern_preserved",
        "causes",
        "identity_forking",
    ) in relations
    assert ("identity_forking", "causes", "identity_split") in relations
    assert ("identity_split", "causes", "object_count_increase") in relations
    assert (
        "object_count_increase",
        "enables",
        "topological_growth",
    ) in relations
