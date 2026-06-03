from core.cognition.cognitive_immune_system import (
    CognitiveImmuneSystem,
    MAX_MERGE_ATTEMPTS_PER_FAMILY,
)


def test_cognitive_immune_system_canonicalizes_preservation_family():

    immune = CognitiveImmuneSystem()

    context = {
        "candidate_concepts":
        [
            {
                "concept":
                "color_preservation",
            },
            {
                "concept":
                "shape_preservation",
            },
            {
                "concept":
                "size_preservation",
            },
        ],
    }

    report = immune.run_cycle(
        context,
    )

    families = report["identity_canonicalization"]["canonical_families"]

    assert "preservation_family" in families
    assert len(families["preservation_family"]) == 3
    assert {
        item["subtype"]
        for item in families["preservation_family"]
    } == {
        "color",
        "shape",
        "size",
    }


def test_cognitive_immune_system_stores_hidden_conflict_memory():

    immune = CognitiveImmuneSystem()

    context = {
        "identity_reasoner_report":
        {
            "identity_analyses":
            [
                {
                    "overlap":
                    {
                        "source":
                        "color_preservation",

                        "target":
                        "shape_preservation",
                    },

                    "failure_explanation":
                    {
                        "hidden_conflicts":
                        {
                            "hidden_conflict_detected":
                            True,

                            "conflict_layers":
                            [
                                "local_identity",
                            ],
                        },
                    },

                    "merge_stability":
                    {
                        "merge_state":
                        "repair_before_merge",
                    },
                },
            ],
        },
    }

    first = immune.run_cycle(
        context,
    )

    second = immune.run_cycle(
        context,
    )

    assert (
        first["hidden_conflict_stabilization"][
            "latent_conflict_count"
        ]
        ==
        1
    )
    assert (
        second["hidden_conflict_stabilization"][
            "latent_conflict_count"
        ]
        ==
        1
    )


def test_cognitive_immune_system_detects_fever_and_freezes_merges():

    immune = CognitiveImmuneSystem()

    context = {
        "memory_pressure_score":
        0.9664,

        "identity_reasoner_report":
        {
            "repair_required_count":
            208,
        },

        "identity_continuity_guardian_report":
        {
            "drift_monitoring":
            {
                "drift_pressure":
                0.72,
            },
        },
    }

    report = immune.run_cycle(
        context,
    )

    policy = report["immune_policy"]

    assert (
        report["semantic_fever_detection"][
            "cognitive_fever_state"
        ]
        ==
        "cognitive_fever_state"
    )
    assert policy["freeze_new_fusions"] is True
    assert policy["freeze_neurogenesis"] is True
    assert policy["aggressive_compression"] is True
    assert policy["sandbox_only_mode"] is True


def test_cognitive_immune_system_prevents_merge_exhaustion():

    immune = CognitiveImmuneSystem()

    context = {
        "concept_fusion_report":
        {
            "fused_concepts":
            [
                {
                    "meta_concept":
                    {
                        "meta_concept_id":
                        "color_preservation",
                    },
                }
            ],
        },
    }

    for _ in range(
        MAX_MERGE_ATTEMPTS_PER_FAMILY + 1,
    ):

        report = immune.run_cycle(
            context,
        )

    assert (
        report["merge_exhaustion_prevention"][
            "merge_exhaustion_state"
        ]
        ==
        "merge_exhaustion_detected"
    )
    assert (
        report["immune_policy"]["sandbox_only_mode"]
        is True
    )
