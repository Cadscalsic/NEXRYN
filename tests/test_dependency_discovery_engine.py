from core.causal import DependencyDiscoveryEngine


def test_concept_dependency_discovery():
    engine = DependencyDiscoveryEngine()

    dependencies = engine.discover_concept_dependencies("color_preservation")

    targets = {item["target"] for item in dependencies}
    assert "color_behavior" in targets
    assert "color_mapping_rule" in targets
    assert all(item["source"] == "color_preservation" for item in dependencies)


def test_context_dependency_discovery():
    engine = DependencyDiscoveryEngine()

    dependencies = engine.discover_context_dependencies({
        "transformation": "duplication",
        "color": "color_reassigned",
        "topology": "topology_splitting",
        "identity": "identity_split",
    })

    targets = {item["target"] for item in dependencies}
    assert "object_count_increase" in targets
    assert "color_mapping_rule" in targets
    assert "connectivity_change" in targets
    assert "lineage_continuity" in targets


def test_semantic_dependency_discovery():
    engine = DependencyDiscoveryEngine()

    dependencies = engine.discover_semantic_dependencies({
        "context": "duplication",
        "properties": [
            "changes_color",
            "modifies_identity",
            "modifies_topology",
            "preserves_shape",
        ],
        "confidence": 0.9,
    })

    targets = {item["target"] for item in dependencies}
    assert "recolor_condition" in targets
    assert "identity_split_possible" in targets
    assert "connectivity_state_required" in targets
    assert "shape_equivalence" in targets


def test_causal_dependency_discovery():
    engine = DependencyDiscoveryEngine()

    dependencies = engine.discover_causal_dependencies({
        "causal_graph_alignment": 0.80,
        "causal_validation_score": 0.79,
        "dependency_coherence": 0.65,
        "context_consistency": 0.5,
    })

    targets = {item["target"] for item in dependencies}
    assert "missing_dependency_search_required" in targets
    assert "root_cause_link_required" in targets
    assert "context_boundary_condition" in targets


def test_identity_dependency_discovery():
    engine = DependencyDiscoveryEngine()

    dependencies = engine.discover_identity_dependencies(
        context_report={"identity": "identity_split"},
    )

    targets = {item["target"] for item in dependencies}
    assert "lineage_continuity" in targets
    assert "identity_branching" in targets
    assert "descendant_identity_mapping" in targets


def test_duplicate_merging_averages_confidence_and_combines_signals():
    engine = DependencyDiscoveryEngine()
    merged = engine.merge_dependencies([
        {
            "source": "color_preservation",
            "target": "color_behavior",
            "relation": "depends_on",
            "dependency_type": "contextual_dependency",
            "confidence": 0.7,
            "supporting_signals": ["concept_template"],
            "risk_factors": [],
            "context": {},
            "recommended_action": "VALIDATE_DEPENDENCY",
        },
        {
            "source": "color_preservation",
            "target": "color_behavior",
            "relation": "depends_on",
            "dependency_type": "contextual_dependency",
            "confidence": 0.9,
            "supporting_signals": ["semantic:changes_color"],
            "risk_factors": ["contextual_truth_required"],
            "context": {},
            "recommended_action": "VALIDATE_DEPENDENCY",
        },
    ])

    assert len(merged) == 1
    assert merged[0]["confidence"] == 0.8
    assert "concept_template" in merged[0]["supporting_signals"]
    assert "semantic:changes_color" in merged[0]["supporting_signals"]
    assert merged[0]["risk_factors"] == ["contextual_truth_required"]


def test_ranking_prioritizes_missing_critical_and_confidence():
    engine = DependencyDiscoveryEngine()

    ranked = engine.rank_dependencies([
        {"target": "low", "confidence": 0.95, "missing_critical": False},
        {"target": "critical", "confidence": 0.70, "missing_critical": True},
    ])

    assert ranked[0]["target"] == "critical"


def test_missing_critical_dependency_detection():
    engine = DependencyDiscoveryEngine()

    missing = engine.identify_critical_missing_dependencies(
        "shape_preservation",
        [{"target": "structural_integrity"}],
    )

    assert missing == ["object_boundary_consistency", "shape_equivalence"]


def test_graceful_behavior_with_empty_inputs():
    engine = DependencyDiscoveryEngine()

    report = engine.discover("unknown_concept")

    assert report["system"] == "dependency_discovery_engine"
    assert report["candidate_count"] == 0
    assert report["recommended_action"] == "BLOCK_UNDERDETERMINED_DEPENDENCY"


def test_color_preservation_under_duplication_context():
    engine = DependencyDiscoveryEngine()

    report = engine.discover(
        concept="color_preservation",
        context_report={
            "transformation": "duplication",
            "topology": "topology_splitting",
            "color": "color_reassigned",
            "identity": "identity_split",
        },
        semantic_context_report={
            "context": "duplication",
            "properties": [
                "changes_color",
                "creates_objects",
                "modifies_identity",
                "modifies_topology",
                "preserves_shape",
            ],
            "capabilities": [
                "attribute_remapping",
                "object_creation",
                "structural_replication",
            ],
            "constraints": [
                "color_mapping_changes",
                "identity_continuity_may_split",
            ],
            "implications": [
                "color_change",
                "object_count_increase",
                "shape_preservation_expected",
            ],
        },
        causal_validation_report={
            "causal_graph_alignment": 0.80,
            "causal_validation_score": 0.79,
            "dependency_coherence": 0.65,
            "context_consistency": 0.5,
            "identity_compatibility": 1.0,
        },
    )

    targets = {item["target"] for item in report["dependencies"]}
    assert report["candidate_count"] >= 8
    assert "color_behavior" in targets
    assert "color_mapping_rule" in targets
    assert "recolor_condition" in targets
    assert report["critical_missing_dependencies"] == []
    assert report["recommended_action"] == "SEND_TO_DEPENDENCY_KNOWLEDGE_ENGINE"


def test_shape_preservation_under_unknown_context():
    engine = DependencyDiscoveryEngine()

    report = engine.discover("shape_preservation")

    targets = {item["target"] for item in report["dependencies"]}
    assert "structural_integrity" in targets
    assert "shape_equivalence" in targets
    assert report["critical_missing_dependencies"] == []
    assert report["recommended_action"] == "SEND_TO_DEPENDENCY_KNOWLEDGE_ENGINE"


def test_object_identity_preservation_under_identity_split_context():
    engine = DependencyDiscoveryEngine()

    report = engine.discover(
        "object_identity_preservation",
        context_report={"identity": "identity_split"},
    )

    targets = {item["target"] for item in report["dependencies"]}
    assert "identity_behavior" in targets
    assert "lineage_continuity" in targets
    assert "identity_branching" in targets
    assert report["recommended_action"] == "SEND_TO_DEPENDENCY_KNOWLEDGE_ENGINE"
