from core.cognition.concept_lineage import (
    ConceptLineage,
    MAX_MUTATIONS_PER_CONCEPT,
)


def test_concept_lineage_tracks_fusion_and_strategy_evolution():

    lineage = ConceptLineage()

    context = {
        "concept_fusion_report":
        {
            "fused_concepts":
            [
                {
                    "fusion_stability":
                    0.72,

                    "meta_concept":
                    {
                        "meta_concept_id":
                        "object_size",

                        "source_concepts":
                        [
                            "hybrid_object_size",
                            "structural_object_size",
                        ],
                    },
                },
            ],
        },

        "evolved_hypotheses":
        {
            "type":
            "structural_object_translation",

            "primitive":
            "translate_right",

            "parent_strategy":
            "object_translation",

            "confidence":
            1.0,
        },
    }

    report = lineage.run_cycle(
        context,
    )

    records = {
        record["concept_id"]:
        record
        for record in report["lineage_records"]
    }

    assert "object_size" in records
    assert records["object_size"]["parents"] == [
        "hybrid_object_size",
        "structural_object_size",
    ]

    assert "structural_object_translation" in records
    assert records["structural_object_translation"]["parents"] == [
        "object_translation",
    ]


def test_concept_lineage_tracks_unsafe_merge_failure_as_ancestry_warning():

    lineage = ConceptLineage()

    context = {
        "cognitive_failure_memory":
        {
            "latest_failure":
            {
                "contradiction_type":
                "unsafe_merge",

                "collapse_source":
                "object_translation::structural_object_translation",

                "ontology_damage":
                0.5,

                "recovery_action":
                "block_merge",
            },
        },
    }

    report = lineage.run_cycle(
        context,
    )

    records = {
        record["concept_id"]:
        record
        for record in report["lineage_records"]
    }

    warning = records["structural_object_translation"]

    assert warning["origin"] == "unsafe_merge_failure"
    assert warning["parents"] == [
        "object_translation",
    ]
    assert warning["mutations"][0]["type"] == "unsafe_merge"
    assert warning["mutations"][0]["recovery_action"] == "block_merge"


def test_concept_lineage_deduplicates_repeated_fusion_mutations():

    lineage = ConceptLineage()

    fusion = {
        "concept_fusion_report":
        {
            "fused_concepts":
            [
                {
                    "fusion_stability":
                    0.4731,

                    "meta_concept":
                    {
                        "meta_concept_id":
                        "object_size",

                        "source_concepts":
                        [
                            "hybrid_object_size",
                            "structural_object_size",
                        ],
                    },
                },
            ],
        },
    }

    for _ in range(32):

        lineage.run_cycle(
            fusion,
        )

    record = lineage.lineage_records[
        "object_size"
    ]

    fusion_mutations = [
        mutation
        for mutation in record["mutations"]
        if mutation.get(
            "type",
        )
        ==
        "fusion"
    ]

    assert len(record["mutations"]) <= MAX_MUTATIONS_PER_CONCEPT
    assert len(fusion_mutations) == 1
    assert fusion_mutations[0]["fusion_stability"] == 0.4731
