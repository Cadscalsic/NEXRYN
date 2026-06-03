import os
from core.evolutionary_graveyard import EvolutionaryGraveyard


def test_add_and_analyze():
    g = EvolutionaryGraveyard()
    g.add_entry("s1", "strategy", "failed_fitness", {"lineage": "L1"})
    g.add_entry("s2", "strategy", "failed_fitness", {"lineage": "L1"})
    g.add_entry("m1", "merge", "conflict", {"lineage": "L2"})

    entries = g.list_entries()
    assert len(entries) == 3

    causes = g.analyze_causes()
    assert causes.get("failed_fitness") == 2

    toxic = g.find_toxic_lineages(threshold=2)
    assert "L1" in toxic

    report = g.export_report()
    assert report["total_entries"] == 3


def test_cognitive_paleontology_ingests_evolutionary_debris():
    g = EvolutionaryGraveyard()

    context = {
        "extinction_engine_report":
        {
            "extinct_traits":
            [
                {
                    "id": "stale_bridge_trait",
                    "niche": "semantic_remapping",
                    "fitness": 0.08,
                    "stability_score": 0.12,
                    "mutation_rate": 0.32,
                },
            ],
        },

        "concept_fusion_report":
        {
            "rejected_fusions":
            [
                {
                    "source_concepts": [
                        "object_translation",
                        "structural_object_translation",
                    ],
                    "rejection_reason": "unstable_identity_merge",
                    "fusion_stability": 0.14,
                },
            ],
        },

        "cognitive_failure_memory":
        {
            "latest_failure":
            {
                "contradiction_type": "unsafe_merge",
                "collapse_source": "object_translation::structural_object_translation",
                "ontology_damage": 0.5,
                "recovery_action": "block_merge",
            },
        },

        "concept_lineage_report":
        {
            "failure_records":
            [
                {
                    "concept_id": "structural_object_translation",
                    "parents": [
                        "object_translation",
                    ],
                    "mutations": [
                        {
                            "type": "unsafe_merge",
                            "ontology_damage": 0.5,
                            "recovery_action": "block_merge",
                        },
                    ],
                },
            ],
        },
    }

    report = g.run_cycle(context)
    paleontology = report["cognitive_paleontology"]

    assert report["total_entries"] >= 4
    assert report["by_category"]["merge"] >= 2
    assert "unsafe_merge" in report["destructive_mutation_patterns"]
    assert report["graveyard_pressure"]["pressure_score"] > 0
    assert report["graveyard_pressure"]["engine"] == "cognitive_graveyard_pressure_engine"
    assert paleontology["layer"] == "cognitive_paleontology"
    assert paleontology["graveyard_pressure"]["pressure_state"] in [
        "graveyard_pressure_elevated",
        "graveyard_pressure_high",
        "graveyard_pressure_critical",
    ]
    assert paleontology["paleontology_state"] == "active_evolutionary_debris_detected"
    assert "object_translation::structural_object_translation" in paleontology["toxic_lineages"]
