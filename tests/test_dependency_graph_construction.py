from runtime.dependency.dependency_graph_discovery import DependencyGraphDiscovery
from runtime.dependency.dependency_graph_validator import DependencyGraphValidator
from runtime.memory.dependency_graph_memory import DependencyGraphMemory


def test_dependency_graph_discovery_builds_and_remembers_graph():
    memory = DependencyGraphMemory()
    discovery = DependencyGraphDiscovery(memory=memory)

    report = discovery.discover(
        concepts=["path_finding"],
        dependency_outputs=[
            {
                "concept": "path_finding",
                "resolved_dependency_chain": [
                    "path_finding",
                    "start",
                    "reachable_nodes",
                    "candidate_paths",
                    "goal",
                ],
                "dependency_confidence": 0.9,
            }
        ],
    )

    graph_report = report["DEPENDENCY_GRAPH_REPORT"]

    assert graph_report["graphs_generated"] == 1
    assert graph_report["node_count"] > 0
    assert graph_report["edge_count"] > 0
    assert graph_report["graph_confidence"] > 0.0
    assert graph_report["graph_failures"] == 0
    assert memory.build_report()["successful_graphs"] == 1


def test_dependency_graph_memory_reuses_known_topology():
    memory = DependencyGraphMemory()
    discovery = DependencyGraphDiscovery(memory=memory)

    first = discovery.discover(
        concepts=["bridge_creation"],
        dependency_outputs=[
            {
                "concept": "bridge_creation",
                "resolved_dependency_chain": [
                    "bridge_creation",
                    "component_A",
                    "connector",
                    "component_B",
                ],
                "dependency_confidence": 0.9,
            }
        ],
    )
    second = discovery.discover(
        concepts=["bridge_creation"],
        dependency_outputs=[
            {
                "concept": "bridge_creation",
                "resolved_dependency_chain": [
                    "bridge_creation",
                    "component_A",
                    "connector",
                    "component_B",
                ],
                "dependency_confidence": 0.9,
            }
        ],
    )

    assert first["DEPENDENCY_GRAPH_REPORT"]["graphs_generated"] == 1
    assert second["DEPENDENCY_GRAPH_REPORT"]["graph_reuse_hits"] == 1
    assert second["dependency_graph_reuse_rate"] == 1.0
    assert memory.build_report()["graph_reuse_count"] == 1


def test_dependency_graph_validator_detects_broken_edges():
    validation = DependencyGraphValidator().validate(
        {
            "root_concepts": ["broken"],
            "nodes": [
                {
                    "id": "broken:broken",
                    "label": "broken",
                    "node_family": "CONCEPT",
                }
            ],
            "edges": [
                {
                    "source": "broken:broken",
                    "target": "missing:node",
                    "edge_type": "requires",
                }
            ],
        }
    )

    assert validation["graph_connectivity_valid"] is False
    assert validation["graph_failures"] > 0
    assert validation["validation_score"] < 1.0
