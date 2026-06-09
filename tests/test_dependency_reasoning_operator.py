from core.dependency import (
    DependencyChainLedger,
    DependencyGraphEngine,
    DependencyReasoningOperator,
    ProcessDependencyGraph,
    ProcessDependencyMemory,
)


def test_dependency_reasoning_operator_builds_duplication_to_color_chain():
    report = DependencyReasoningOperator().reason(
        [
            "duplication",
            "identity_split",
            "topology_splitting",
            "color_reassigned",
        ],
        evidence={
            "context_confidence": 0.902,
            "semantic_context_score": 0.90,
            "context_hierarchy_score": 0.94,
            "causal_graph_alignment": 0.7943,
        },
    )

    chain = report["dependency_chain"]
    path = report["dependency_path"]

    assert report["reasoning_state"] == "DEPENDENCY_CHAIN_REASONED"
    assert chain["source"] == "duplication"
    assert chain["target"] == "color_reassigned"
    assert chain["path"] == [
        "identity_split",
        "object_count_increase",
        "topology_splitting",
    ]
    assert path == {
        "root": "duplication",
        "chain": [
            "identity_split",
            "object_count_increase",
            "topology_splitting",
            "color_reassigned",
        ],
        "confidence": report["confidence"],
        "nodes": [
            "duplication",
            "identity_split",
            "object_count_increase",
            "topology_splitting",
            "color_reassigned",
        ],
        "chain_depth": 4,
    }
    assert report["inferred_signals"] == ["object_count_increase"]
    assert report["confidence"] >= 0.80
    assert report["recommended_action"] == (
        "INGEST_REASONED_DEPENDENCY_CHAIN"
    )
    assert [
        (item["source"], item["target"])
        for item in report["dependency_evidence"]
    ] == [
        ("duplication", "identity_split"),
        ("identity_split", "object_count_increase"),
        ("object_count_increase", "topology_splitting"),
        ("topology_splitting", "color_reassigned"),
    ]


def test_dependency_reasoning_operator_builds_growth_to_shape_chain():
    report = DependencyReasoningOperator().reason(
        [
            "growth",
            "topology_expansion",
            "shape_preservation",
        ],
        source="growth",
        target="shape_preservation",
        evidence={
            "context_confidence": 0.93,
            "semantic_context_score": 0.91,
            "context_hierarchy_score": 0.96,
            "causal_graph_alignment": 0.87,
        },
    )

    assert report["reasoning_state"] == "DEPENDENCY_CHAIN_REASONED"
    assert report["dependency_chain"]["nodes"] == [
        "growth",
        "cell_count_increase",
        "topology_expansion",
        "local_shape",
        "shape_preservation",
    ]
    assert report["inferred_signals"] == [
        "cell_count_increase",
        "local_shape",
    ]
    assert report["confidence"] >= 0.80


def test_dependency_graph_engine_ingests_reasoned_dependency_chain(tmp_path):
    engine = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
    )

    report = engine.ingest_reasoned_dependency_chain(
        [
            "duplication",
            "identity_split",
            "topology_splitting",
            "color_reassigned",
        ]
    )
    paths = engine.find_dependency_paths(
        "duplication",
        target="color_reassigned",
    )
    coherence = engine.validate_dependency_coherence(
        "duplication",
        required_dependencies=["identity_split"],
    )

    assert report["mode"] == "reasoned_dependency_chain"
    assert report["ingested_dependencies"] == 4
    assert paths["best_path"]["nodes"] == [
        "duplication",
        "identity_split",
        "object_count_increase",
        "topology_splitting",
        "color_reassigned",
    ]
    assert coherence["dependency_coherence"] >= 0.80


def test_dependency_graph_engine_ingests_runtime_dependency_chains(tmp_path):
    engine = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
        dependency_chain_ledger_path=tmp_path / "dependency_chain_ledger.json",
    )

    report = engine.ingest_reasoned_dependency_chains([
        {
            "concept": "growth",
            "context_discovery": {
                "transformation_family": "growth",
                "confidence": 0.93,
                "context_signature": {
                    "transformation_family": "growth",
                    "topology_behavior": "topology_expansion",
                    "identity_behavior": "identity_preserved",
                },
            },
            "identity_runtime_report": {
                "runtime_ready": True,
                "identity_continuity_preserved": True,
            },
            "semantic_context": {
                "semantic_context_score": 0.91,
            },
            "context_hierarchy": {
                "context_hierarchy_score": 0.96,
            },
            "causal_graph_alignment": {
                "alignment_score": 0.87,
            },
        },
        {
            "concept": "replication",
            "context_discovery": {
                "transformation_family": "replication",
                "confidence": 0.90,
                "context_signature": {
                    "transformation_family": "replication",
                    "identity_behavior": "identity_split",
                    "topology_behavior": "topology_splitting",
                },
            },
            "identity_runtime_report": {
                "runtime_ready": True,
                "identity_split": True,
            },
            "semantic_context": {
                "semantic_context_score": 0.90,
            },
            "context_hierarchy": {
                "context_hierarchy_score": 0.94,
            },
            "causal_graph_alignment": {
                "alignment_score": 0.86,
            },
        },
    ])

    growth_path = engine.find_dependency_paths(
        "growth",
        target="shape_preservation",
    )
    replication_path = engine.find_dependency_paths(
        "replication",
        target="shape_preservation",
        max_depth=5,
    )

    assert report["mode"] == "reasoned_dependency_chain_ingestion"
    assert report["dependency_chain_ingestion_layer_active"] is True
    assert report["record_count"] == 2
    assert report["reasoned_chain_count"] == 2
    assert report["ingested_dependencies"] >= 8
    assert report["dependency_coherence_average"] >= 0.80
    assert growth_path["best_path"]["nodes"] == [
        "growth",
        "cell_count_increase",
        "topology_expansion",
        "local_shape",
        "shape_preservation",
    ]
    assert replication_path["best_path"]["nodes"] == [
        "replication",
        "identity_split",
        "object_count_increase",
        "topology_splitting",
        "local_shape",
        "shape_preservation",
    ]


def test_dependency_chain_ledger_persists_and_rehydrates_graph(tmp_path):
    ledger_path = tmp_path / "dependency_chain_ledger.json"
    graph_path = tmp_path / "dependency_graph.json"
    ledger = DependencyChainLedger(storage_path=ledger_path)

    added = ledger.add_chain(
        [
            "growth",
            "object_persistence",
            "identity_continuity",
            "object_identity_preservation",
        ],
        confidence=0.91,
        context="growth",
    )
    hydrated_ledger = DependencyChainLedger(storage_path=ledger_path)
    engine = DependencyGraphEngine(
        graph_path=graph_path,
        dependency_chain_ledger=hydrated_ledger,
    )
    report = engine.ingest_dependency_chain_ledger()
    path = engine.find_dependency_paths(
        "growth",
        target="object_identity_preservation",
        max_depth=3,
    )

    assert added["added"] is True
    assert hydrated_ledger.report()["record_count"] == 1
    assert report["mode"] == "dependency_chain_ledger_rehydration"
    assert report["reasoned_chain_count"] == 1
    assert path["best_path"]["nodes"] == [
        "growth",
        "object_persistence",
        "identity_continuity",
        "object_identity_preservation",
    ]


def test_process_dependency_graph_ingests_process_knowledge(tmp_path):
    process_graph = ProcessDependencyGraph()
    engine = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
        dependency_chain_ledger_path=tmp_path / "dependency_chain_ledger.json",
        process_dependency_graph=process_graph,
    )

    report = engine.ingest_process_dependency_graph([
        "growth",
        "duplication",
    ])
    growth = report["coherence_reports"]["growth"]
    duplication = report["coherence_reports"]["duplication"]
    growth_path = engine.find_dependency_paths(
        "growth",
        target="identity_continuity",
    )
    duplication_path = engine.find_dependency_paths(
        "duplication",
        target="identity_split",
    )
    duplication_shape_path = engine.find_dependency_paths(
        "duplication",
        target="shape_preservation",
        max_depth=6,
    )

    assert report["mode"] == "process_dependency_graph_ingestion"
    assert report["process_dependency_graph"]["process_count"] == 2
    assert report["ingest"]["ingested_dependencies"] >= 10
    assert report["dependency_coherence_average"] >= 0.80
    assert growth["dependency_coherence"] >= 0.80
    assert duplication["dependency_coherence"] >= 0.80
    assert growth_path["best_path"]["nodes"] == [
        "growth",
        "identity_continuity",
    ]
    assert duplication_path["best_path"]["nodes"] == [
        "duplication",
        "identity_split",
    ]
    assert duplication_shape_path["best_path"]["nodes"] == [
        "duplication",
        "identity_split",
        "object_count_increase",
        "replication",
        "topology_splitting",
        "local_shape",
        "shape_preservation",
    ]
    assert engine.dependency_chain_ledger.report()["record_count"] >= 10


def test_process_dependency_memory_loads_typed_causal_chains(tmp_path):
    memory_path = tmp_path / "process_dependency_memory.json"
    memory_path.write_text(
        """
        {
          "process_chains": {
            "duplication": [
              {
                "source": "duplication",
                "relation": "causes",
                "target": "identity_split",
                "confidence": 0.94
              },
              {
                "source": "identity_split",
                "relation": "causes",
                "target": "object_count_increase",
                "confidence": 0.92
              },
              {
                "source": "object_count_increase",
                "relation": "enables",
                "target": "replication",
                "confidence": 0.90
              },
              {
                "source": "replication",
                "relation": "may_cause",
                "target": "topological_growth",
                "confidence": 0.86
              }
            ]
          }
        }
        """,
        encoding="utf-8",
    )

    memory = ProcessDependencyMemory(
        storage_path=memory_path,
        seed_defaults=False,
    )
    graph = ProcessDependencyGraph(process_dependency_memory=memory)
    resolution = graph.resolve_dependency_chain("duplication")

    assert memory.report()["loaded_from_storage"] is True
    assert memory.links_loaded == 4
    assert [
        relation.relation
        for relation in graph.relations_for("duplication")
    ] == ["causes", "causes", "enables", "causes"]
    assert resolution["resolved_dependency_chain"] == [
        "duplication",
        "identity_split",
        "object_count_increase",
        "replication",
        "topological_growth",
    ]
    assert resolution["process_dependency_links_used"] == 4
    assert resolution["dependency_chain_coverage"] == 1.0


def test_dependency_reasoning_operator_queries_process_memory():
    memory = ProcessDependencyMemory(seed_defaults=True)
    operator = DependencyReasoningOperator(
        process_dependency_graph=ProcessDependencyGraph(
            process_dependency_memory=memory,
        ),
    )

    report = operator.reason(
        ["topological_growth", "growth"],
        source="topological_growth",
        target="growth",
    )

    assert report["process_dependency_memory"]["queried"] is True
    assert report["process_dependency_links_loaded"] >= 1
    assert report["process_dependency_links_used"] >= 1
    assert report["dependency_chain_depth"] >= 1
    assert report["dependency_chain_coverage"] == 1.0
    assert report["dependency_chain"]["nodes"] == [
        "topological_growth",
        "growth",
    ]


def test_dependency_graph_engine_ingests_process_dependency_memory(tmp_path):
    engine = DependencyGraphEngine(
        graph_path=tmp_path / "dependency_graph.json",
        dependency_chain_ledger_path=tmp_path / "dependency_chain_ledger.json",
        process_dependency_memory_path=tmp_path / "process_dependency_memory.json",
    )

    report = engine.ingest_process_dependency_memory([
        "growth",
        "replication",
    ])

    assert report["mode"] == "process_dependency_memory_ingestion"
    assert report["process_dependency_memory_ingestion_layer_active"] is True
    assert report["process_dependency_links_loaded"] >= 1
    assert report["process_dependency_links_used"] >= 1
    assert report["dependency_chain_depth"] >= 1
    assert report["dependency_chain_coverage"] > 0.0
    assert report["dependency_coherence_average"] >= 0.80
    assert report["boundary_refinement_dependency_debug"][0]["concept"] == (
        "growth"
    )
