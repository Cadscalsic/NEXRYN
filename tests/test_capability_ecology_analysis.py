from runtime.capability_intelligence.capability_ecology_analysis import (
    CapabilityEcologyAnalysis,
)


def test_capability_ecology_detects_composite_candidates_and_synergy():
    report = CapabilityEcologyAnalysis().analyze(
        known_operations=[
            "translate",
            "preserve_topology",
            "preserve_colors",
            "duplicate_object",
            "replace_color",
            "preserve_grid",
        ],
        experience_distribution=[
            {
                "operation": "translate",
                "experience_count": 12,
                "independent_reuse_success_count": 8,
            },
            {
                "operation": "preserve_topology",
                "experience_count": 6,
                "independent_reuse_success_count": 4,
            },
            {
                "operation": "replace_color",
                "experience_count": 20,
                "independent_reuse_success_count": 18,
            },
        ],
        survival_rows=[
            {
                "operation": "translate",
                "lifecycle_state": "SURVIVING_CAPABILITY",
                "distinct_task_count": 10,
                "arena_quality_count": 9,
                "best_accuracy": 0.96,
                "average_accuracy": 0.82,
            },
            {
                "operation": "preserve_topology",
                "lifecycle_state": "OPERATIONAL_CITIZEN",
                "average_accuracy": 0.88,
            },
        ],
        graduation_diagnostics=[
            {
                "operation": "translate",
                "graduation_status": "BLOCKED_AT_FINAL_VALIDATION",
            }
        ],
    )

    candidates = {
        row["composite_name"]: row
        for row in report["composite_capability_candidates"]
    }

    assert report["capability_ecology_state"] == "CAPABILITY_ECOLOGY_ACTIVE"
    assert report["composite_operational_capability_count"] >= 2
    assert report["capability_cooperation_score"] > 0
    assert report["capability_economy_health"] > 0
    assert (
        candidates["Topology Preserving Translation"]["composition_state"]
        == "COMPOSITE_OPERATIONAL_CANDIDATE"
    )
    assert (
        candidates["Symbolic Object Replication"]["composition_state"]
        == "COMPOSITE_OPERATIONAL_CANDIDATE"
    )
    assert report["capability_synergy_matrix"]
    assert report["capability_investment_priorities"][0]["operation"]


def test_capability_ecology_reports_partial_composition_opportunities():
    report = CapabilityEcologyAnalysis().analyze(
        known_operations=["translate", "preserve_topology"],
        survival_rows=[
            {
                "operation": "translate",
                "lifecycle_state": "SURVIVING_CAPABILITY",
            }
        ],
    )

    opportunities = {
        row["composite_name"]: row
        for row in report["capability_composition_opportunities"]
    }

    assert report["composite_operational_capability_count"] == 0
    assert (
        opportunities["Topology Preserving Translation"]["composition_state"]
        == "PARTIAL_COMPOSITE_OPPORTUNITY"
    )
    assert opportunities["Topology Preserving Translation"]["missing_capabilities"] == [
        "preserve_colors"
    ]
