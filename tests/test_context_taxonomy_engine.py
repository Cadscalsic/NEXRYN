from core.context_discovery import ContextDiscoveryEngine
from runtime.context.context_governance_registry import ContextGovernanceRegistry
from runtime.context.context_taxonomy_engine import ContextTaxonomyEngine


def test_context_taxonomy_reclassifies_mapping_context():
    report = ContextTaxonomyEngine().classify({
        "context_name": "unknown",
        "changes_color": True,
        "preserves_identity": True,
        "preserves_topology": True,
    })

    assert report["context_name"] == "mapping_context"
    assert report["context_type"] == "TAXONOMY_CONTEXT"
    assert report["context_confidence"] >= 0.85
    assert report["governance_visible"] is True


def test_context_taxonomy_reclassifies_density_and_scale_aliases():
    taxonomy = ContextTaxonomyEngine()
    density = taxonomy.classify({
        "context_name": "unknown",
        "concept": "density_preservation",
    })
    scale = taxonomy.classify({
        "context_name": "unknown",
        "concept": "size_preservation",
    })

    assert density["context_name"] == "density_context"
    assert scale["context_name"] == "scale_context"
    assert taxonomy.report([density, scale])["unknown_context_count"] == 0


def test_context_discovery_uses_taxonomy_for_density_and_size_contexts():
    discovery = ContextDiscoveryEngine()
    density = discovery.discover_context({
        "task_id": "density_task",
        "concept": "density_preservation",
        "active_concepts": ["density_preservation"],
        "context_name": "unknown",
    })
    scale = discovery.discover_context({
        "task_id": "size_task",
        "concept": "size_preservation",
        "active_concepts": ["size_preservation"],
        "context_name": "unknown",
    })

    assert density["discovered_context"]["context_name"] == "density_context"
    assert density["cluster"] == "Density Context"
    assert scale["discovered_context"]["context_name"] == "scale_context"
    assert scale["cluster"] == "Scale Context"


def test_taxonomy_contexts_register_with_governance():
    taxonomy_report = ContextTaxonomyEngine().report([
        {
            "context_name": "unknown",
            "concept": "density_preservation",
        },
        {
            "context_name": "unknown",
            "concept": "size_preservation",
        },
        {
            "context_name": "unknown",
            "changes_color": True,
            "preserves_identity": True,
            "preserves_topology": True,
        },
    ])
    governance = ContextGovernanceRegistry().register_runtime_contexts({
        "context_taxonomy_report": taxonomy_report,
    })

    assert taxonomy_report["unknown_context_count"] == 0
    assert taxonomy_report["context_taxonomy_coverage"] == 1.0
    assert {
        "density_context",
        "scale_context",
        "mapping_context",
    }.issubset(set(governance["visible_context_ids"]))
