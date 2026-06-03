from core.cognition.concept_lineage import (
    ConceptLineage,
)

from core.cognition.recursive_guardian import (
    RecursiveGuardian,
)


def test_recursive_guardian_detects_cyclic_cognitive_ancestry():

    guardian = RecursiveGuardian()

    records = [
        {
            "concept_id":
            "object_count",

            "parents":
            [
                "structural_object_count",
            ],
        },
        {
            "concept_id":
            "structural_object_count",

            "parents":
            [
                "object_count",
            ],
        },
    ]

    report = guardian.run_cycle(
        {
            "lineage_records":
            records,
        }
    )

    assert report["cycle_report"]["cycle_count"] >= 1
    assert report["recursive_guardian_state"] == "recursive_safety_intervention"


def test_concept_lineage_breaks_cycle_and_limits_ancestry_recursion():

    lineage = ConceptLineage()

    lineage._record(
        "object_count",
        "strategy_evolution",
        parents=[
            "structural_object_count",
        ],
    )

    lineage._record(
        "structural_object_count",
        "strategy_evolution",
        parents=[
            "object_count",
        ],
    )

    object_record = lineage.lineage_records[
        "object_count"
    ]
    structural_record = lineage.lineage_records[
        "structural_object_count"
    ]

    assert (
        object_record["parents"]
        ==
        [
            "structural_object_count",
        ]
        or structural_record["parents"]
        ==
        [
            "object_count",
        ]
    )

    assert not (
        object_record["parents"]
        ==
        [
            "structural_object_count",
        ]
        and structural_record["parents"]
        ==
        [
            "object_count",
        ]
    )

    ancestry = lineage.ancestry_for(
        "object_count",
    )

    assert ancestry["depth"] <= lineage.recursive_guardian.max_depth
    assert ancestry["ancestors"]

    report = lineage.run_cycle(
        {}
    )

    assert report["recursive_safety"]["self_reference_state"] == "self_reference_safe"
