from __future__ import annotations

from runtime.telemetry.route_contribution import (
    attach_route_origin_lineage,
    build_route_contribution_manifest,
    compact_route_contribution_summary,
    route_origin_lineage_from_record,
)
from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer


def _routes(count=6):
    return [
        {
            "route_id": f"route_{index}",
            "route_rank": index,
            "route_score": round(1.0 - index / 10, 3),
            "route_source": "synthetic_test_route",
            "route_family": "positive_control",
        }
        for index in range(1, count + 1)
    ]


def _lifecycle(count=6):
    records = []
    for index in range(1, count + 1):
        records.append({
            "run_id": "run_a",
            "task_id": "task_a",
            "route_id": f"route_{index}",
            "state": "ACTIVE_ROUTE",
            "event_id": f"route_{index}:active",
        })
        records.append({
            "run_id": "run_a",
            "task_id": "task_a",
            "route_id": f"route_{index}",
            "state": "RELEASED_ROUTE",
            "event_id": f"route_{index}:released",
        })
    return records


def _context(**overrides):
    context = {
        "run_id": "run_a",
        "task_id": "task_a",
        "route_selection_report": {
            "active_routes": _routes(),
            "candidate_routes": _routes(),
            "available_routes": _routes(),
        },
        "route_lifecycle_records": _lifecycle(),
    }
    context.update(overrides)
    return context


def _manifest(context=None, **kwargs):
    return build_route_contribution_manifest(
        context=context or _context(),
        route_records=kwargs.pop("route_records", None),
        route_lifecycle_records=kwargs.pop("route_lifecycle_records", None),
        budget_report={
            "run_id": "run_a",
            "task_id": "task_a",
            "maximum_active_routes": 6,
        },
        **kwargs,
    )


def _scoped_partition_manifest():
    routes = _routes(12)
    lifecycle = []
    for index in range(1, 7):
        lifecycle.extend([
            {"run_id": "run_a", "task_id": "task_a", "route_id": f"route_{index}", "state": "ACTIVE_ROUTE"},
            {"run_id": "run_a", "task_id": "task_a", "route_id": f"route_{index}", "state": "RELEASED_ROUTE"},
        ])
    for index in range(7, 13):
        lifecycle.append({
            "run_id": "run_a",
            "task_id": "task_a",
            "route_id": f"route_{index}",
            "state": "DEFERRED_BY_BUDGET",
        })
    context = _context(
        route_output_lineage_records=[
            {
                "origin_route_id": "route_2",
                "output_type": "candidate",
                "candidate_id": "candidate_base",
                "output_fingerprint": "candidate:base",
                "qualification_state": "QUALIFIED",
                "arena_state": "EVALUATED",
            },
            {
                "origin_route_id": "route_5",
                "output_type": "candidate",
                "candidate_id": "candidate_marginal_a",
                "output_fingerprint": "candidate:marginal:a",
                "qualification_state": "QUALIFIED",
                "arena_state": "EVALUATED",
            },
            {
                "origin_route_id": "route_6",
                "output_type": "candidate",
                "candidate_id": "candidate_marginal_b",
                "output_fingerprint": "candidate:marginal:b",
                "qualification_state": "QUALIFIED",
                "arena_state": "EVALUATED",
            },
        ],
    )
    return _manifest(
        context,
        route_records=routes,
        route_lifecycle_records=lifecycle,
    )


def test_positive_control_classifies_marginal_routes_without_authority():
    context = _context(
        route_output_lineage_records=[
            {
                "origin_route_id": "route_1",
                "output_type": "candidate",
                "candidate_id": "candidate_base_1",
                "output_fingerprint": "candidate:base:1",
                "qualification_state": "QUALIFIED",
                "arena_state": "EVALUATED",
            },
            {
                "origin_route_id": "route_2",
                "output_type": "program",
                "program_id": "program_base_2",
                "output_fingerprint": "program:base:2",
                "validation_state": "VALIDATED",
            },
            {
                "origin_route_id": "route_3",
                "output_type": "candidate",
                "candidate_id": "candidate_unique_3",
                "output_fingerprint": "candidate:unique:3",
                "qualification_state": "QUALIFIED",
                "arena_state": "EVALUATED",
            },
            {
                "origin_route_id": "route_4",
                "output_type": "candidate",
                "candidate_id": "candidate_duplicate_4",
                "output_fingerprint": "candidate:base:1",
                "qualification_state": "QUALIFIED",
            },
            {
                "origin_route_id": "route_5",
                "output_type": "candidate",
                "candidate_id": "candidate_low_5",
                "output_fingerprint": "candidate:low:5",
                "validation_state": "REJECTED",
            },
        ]
    )

    manifest = _manifest(context)
    states = {
        route["route_position"]: route["contribution_state"]
        for route in manifest["routes"]
    }

    assert states[3] == "UNIQUE_USEFUL_CONTRIBUTION"
    assert states[4] == "DUPLICATE_CONTRIBUTION"
    assert states[5] == "LOW_VALUE_CONTRIBUTION"
    assert states[6] == "NO_OBSERVABLE_CONTRIBUTION"
    assert manifest["aggregate_summary"]["marginal_unique_contribution_rate"] == 0.25
    assert manifest["aggregate_summary"]["marginal_redundancy_rate"] == 0.25
    assert manifest["telemetry_consumed_by_cognition"] is False
    assert manifest["authority"] == "OBSERVATION_ONLY"
    assert manifest["behavioral_authority"] == "NONE"


def test_scoped_route_accounting_partitions_selected_and_executed_routes():
    manifest = _scoped_partition_manifest()
    aggregate = manifest["aggregate_summary"]

    assert manifest["attribution_completeness_state"] == "ROUTE_ATTRIBUTION_COMPLETE"
    assert aggregate["selected_routes"] == 12
    assert aggregate["executed_routes"] == 6
    assert aggregate["routes_with_unique_useful_contribution"] == 3
    assert aggregate["routes_with_duplicate_contribution"] == 0
    assert aggregate["routes_with_low_value_contribution"] == 0
    assert aggregate["routes_with_no_observable_contribution"] == 3
    assert aggregate["selected_routes_with_unmeasurable_contribution"] == 6
    assert aggregate["executed_routes_with_unmeasurable_contribution"] == 0
    assert aggregate["selected_route_partition_delta"] == 0
    assert aggregate["selected_route_partition_integrity"] == "VERIFIED"
    assert aggregate["executed_route_partition_delta"] == 0
    assert aggregate["executed_route_partition_integrity"] == "VERIFIED"


def test_deferred_routes_are_selected_unmeasurable_not_executed_unmeasurable():
    manifest = _scoped_partition_manifest()
    aggregate = manifest["aggregate_summary"]

    deferred = [route for route in manifest["routes"] if route["route_position"] >= 7]
    assert {route["execution_state"] for route in deferred} == {"NOT_EXECUTED"}
    assert {route["contribution_measurability_state"] for route in deferred} == {
        "CONTRIBUTION_NOT_MEASURABLE"
    }
    assert aggregate["selected_routes_with_unmeasurable_contribution"] == 6
    assert aggregate["executed_routes_with_unmeasurable_contribution"] == 0
    assert aggregate["unmeasurable_because_not_executed"] == 6


def test_unmeasurable_reason_counts_expose_lineage_and_downstream_causes():
    lineage_manifest = _manifest(
        _context(
            route_output_lineage_records=[
                {
                    "origin_route_id": "route_1",
                    "run_id": "old_run",
                    "output_type": "candidate",
                    "candidate_id": "candidate_stale",
                    "qualification_state": "QUALIFIED",
                }
            ]
        )
    )
    downstream_manifest = _manifest(
        _context(
            route_output_lineage_records=[
                {
                    "origin_route_id": "route_1",
                    "output_type": "candidate",
                    "candidate_id": "candidate_unknown",
                    "output_fingerprint": "candidate:unknown",
                }
            ]
        )
    )

    assert lineage_manifest["routes"][0]["contribution_state"] == "CONTRIBUTION_NOT_MEASURABLE"
    assert lineage_manifest["routes"][0]["unmeasurable_reasons"] == ["lineage_error"]
    assert lineage_manifest["aggregate_summary"]["unmeasurable_because_lineage_error"] == 1
    assert downstream_manifest["routes"][0]["contribution_state"] == "CONTRIBUTION_NOT_MEASURABLE"
    assert downstream_manifest["routes"][0]["unmeasurable_reasons"] == [
        "insufficient_downstream_lineage"
    ]
    assert (
        downstream_manifest["aggregate_summary"][
            "unmeasurable_because_insufficient_downstream_lineage"
        ]
        == 1
    )


def test_compact_summary_preserves_legacy_unmeasurable_scope_and_adds_scoped_fields():
    summary = compact_route_contribution_summary(_scoped_partition_manifest())

    assert summary["schema_version"] == "1.0"
    assert summary["unmeasurable_routes"] == 6
    assert summary["unmeasurable_routes_scope"] == "SELECTED_ROUTES"
    assert summary["selected_routes"] == 12
    assert summary["executed_routes"] == 6
    assert summary["selected_routes_with_unmeasurable_contribution"] == 6
    assert summary["executed_routes_with_unmeasurable_contribution"] == 0
    assert summary["executed_route_attribution_state"] == "ROUTE_ATTRIBUTION_COMPLETE"
    assert summary["executed_route_attribution_scope"] == "EXECUTED_ROUTES"
    assert summary["telemetry_consumed_by_cognition"] is False


def test_marginal_accounting_remains_executed_position_scoped():
    aggregate = _scoped_partition_manifest()["aggregate_summary"]

    assert aggregate["marginal_routes_executed"] == 4
    assert aggregate["marginal_routes_measurable"] == 4
    assert aggregate["marginal_routes_unmeasurable"] == 0
    assert aggregate["marginal_unique_useful_routes"] == 2
    assert aggregate["marginal_duplicate_routes"] == 0
    assert aggregate["marginal_low_value_routes"] == 0
    assert aggregate["marginal_no_observable_routes"] == 2
    assert aggregate["marginal_unique_contribution_rate"] == 0.5
    assert aggregate["marginal_redundancy_rate"] == 0.0


def test_human_route_report_wording_exposes_scope():
    summary = compact_route_contribution_summary(_scoped_partition_manifest())
    renderer = DeterministicFinalReportRenderer()
    report = renderer.render(
        {
            "runtime_status": "completed",
            "training_batch_size": 3,
            "EXECUTION_PLAN_REPORT": {
                "execution_plan_id": "plan_a",
                "execution_plan_schema_version": "1.0",
                "finalized": True,
                "route_contribution_summary": summary,
            },
        },
        runtime_metadata={"execution_id": "run_a", "mode": "adaptive"},
    )

    assert "Executed Route Attribution State: ROUTE_ATTRIBUTION_COMPLETE" in report
    assert "Selected Routes: 12" in report
    assert "Executed Routes: 6" in report
    assert "Legacy Unmeasurable Routes Scope: SELECTED_ROUTES" in report
    assert "Legacy Unmeasurable Routes: 6" in report
    assert "Selected Routes With Unmeasurable Contribution: 6" in report
    assert "Executed Routes With Unmeasurable Contribution: 0" in report
    assert "\nUnmeasurable Routes: 6\n" not in report


def test_stable_route_identity_is_current_run_and_task_bound():
    manifest = _manifest()

    route_ids = [route["route_execution_id"] for route in manifest["routes"]]
    assert len(route_ids) == len(set(route_ids)) == 6
    assert all(route["run_id"] == "run_a" for route in manifest["routes"])
    assert all(route["task_id"] == "task_a" for route in manifest["routes"])
    assert all(route["route_fingerprint"] for route in manifest["routes"])


def test_duplicate_route_id_fails_closed():
    routes = _routes(2)
    routes[1]["route_id"] = routes[0]["route_id"]

    manifest = _manifest(route_records=routes)

    assert manifest["identity_validation_state"] == "ROUTE_IDENTITY_CONFLICT"
    assert manifest["attribution_completeness_state"] == "ROUTE_ATTRIBUTION_INSUFFICIENT"
    assert manifest["identity_breaks"][0]["break_type"] == "duplicate_route_id"


def test_stale_previous_run_route_id_fails_closed():
    routes = _routes(1)
    routes[0]["run_id"] = "old_run"

    manifest = _manifest(route_records=routes)

    assert manifest["identity_validation_state"] == "ROUTE_IDENTITY_CONFLICT"
    assert manifest["identity_breaks"][0]["break_type"] == "stale_previous_run_route_id"


def test_cross_task_route_attribution_fails_closed():
    routes = _routes(1)
    routes[0]["task_id"] = "other_task"

    manifest = _manifest(route_records=routes)

    assert manifest["identity_validation_state"] == "ROUTE_IDENTITY_CONFLICT"
    assert manifest["identity_breaks"][0]["break_type"] == "cross_task_route_attribution"


def test_candidate_attributed_to_wrong_route_breaks_lineage():
    context = _context(
        route_output_lineage_records=[
            {
                "origin_route_execution_id": "foreign_route",
                "candidate_id": "candidate_wrong",
                "output_type": "candidate",
                "qualification_state": "QUALIFIED",
            }
        ]
    )

    manifest = _manifest(context)

    assert manifest["lineage_continuity_state"] == "ROUTE_LINEAGE_PARTIAL"
    assert manifest["lineage_breaks"][0]["break_type"] == "candidate_attributed_to_wrong_route"


def test_candidate_with_no_route_lineage_breaks_lineage_without_guessing():
    context = _context(
        route_output_lineage_records=[
            {
                "candidate_id": "candidate_unbound",
                "output_type": "candidate",
                "qualification_state": "QUALIFIED",
            }
        ]
    )

    manifest = _manifest(context)

    assert manifest["lineage_continuity_state"] == "ROUTE_LINEAGE_PARTIAL"
    assert manifest["lineage_breaks"][0]["break_type"] == "candidate_with_no_route_lineage"


def test_jointly_produced_candidate_preserves_multiple_route_origins():
    routes = [
        {"route_id": "route_1", "route_rank": 1, "route_execution_id": "rex_1"},
        {"route_id": "route_2", "route_rank": 2, "route_execution_id": "rex_2"},
    ]
    lifecycle = [
        {"route_id": "route_1", "state": "ACTIVE_ROUTE"},
        {"route_id": "route_1", "state": "RELEASED_ROUTE"},
        {"route_id": "route_2", "state": "ACTIVE_ROUTE"},
        {"route_id": "route_2", "state": "RELEASED_ROUTE"},
    ]
    context = _context(
        route_output_lineage_records=[
            {
                "origin_route_execution_ids": ["rex_1", "rex_2"],
                "candidate_id": "candidate_joint",
                "output_type": "candidate",
                "qualification_state": "QUALIFIED",
            }
        ]
    )

    manifest = _manifest(
        context,
        route_records=routes,
        route_lifecycle_records=lifecycle,
    )

    assert {
        route["contribution_state"] for route in manifest["routes"]
    } == {"UNIQUE_USEFUL_CONTRIBUTION"}
    assert all(route["candidate_ids"] == ["candidate_joint"] for route in manifest["routes"])


def test_duplicate_program_fingerprint_measures_duplicate_contribution():
    context = _context(
        route_output_lineage_records=[
            {
                "origin_route_id": "route_1",
                "program_id": "program_a",
                "output_type": "program",
                "output_fingerprint": "program:same",
                "validation_state": "VALIDATED",
            },
            {
                "origin_route_id": "route_2",
                "program_id": "program_b",
                "output_type": "program",
                "output_fingerprint": "program:same",
                "validation_state": "VALIDATED",
            },
        ]
    )

    manifest = _manifest(context)

    assert manifest["routes"][1]["contribution_state"] == "DUPLICATE_CONTRIBUTION"


def test_route_admitted_but_never_executed_remains_unmeasurable():
    manifest = _manifest(
        route_records=[{"route_id": "route_1", "route_rank": 1}],
        route_lifecycle_records=[{"route_id": "route_1", "state": "ROUTE_ADMITTED"}],
    )

    route = manifest["routes"][0]
    assert route["admitted"] is True
    assert route["executed"] is False
    assert route["contribution_state"] == "CONTRIBUTION_NOT_MEASURABLE"


def test_executed_route_with_no_artifact_is_no_observable_contribution():
    manifest = _manifest(
        route_records=[{"route_id": "route_1", "route_rank": 1}],
        route_lifecycle_records=[
            {"route_id": "route_1", "state": "ACTIVE_ROUTE"},
            {"route_id": "route_1", "state": "RELEASED_ROUTE"},
        ],
    )

    assert manifest["routes"][0]["contribution_state"] == "NO_OBSERVABLE_CONTRIBUTION"
    assert manifest["lineage_continuity_state"] == "ROUTE_LINEAGE_CONTINUITY_VERIFIED"
    assert manifest["attribution_completeness_state"] == "ROUTE_ATTRIBUTION_COMPLETE"


def test_no_downstream_outputs_are_not_lineage_breaks_when_no_artifact_exists():
    manifest = _manifest()

    assert manifest["lineage_continuity_state"] == "ROUTE_LINEAGE_CONTINUITY_VERIFIED"
    assert manifest["attribution_completeness_state"] == "ROUTE_ATTRIBUTION_COMPLETE"
    assert not manifest["lineage_breaks"]


def test_failed_deferred_and_rejected_routes_do_not_gain_false_contribution():
    manifest = _manifest(
        route_records=[
            {"route_id": "route_1", "route_rank": 1},
            {"route_id": "route_2", "route_rank": 2},
            {"route_id": "route_3", "route_rank": 3},
        ],
        route_lifecycle_records=[
            {"route_id": "route_1", "state": "FAILED_ROUTE"},
            {"route_id": "route_2", "state": "DEFERRED_BY_BUDGET"},
            {"route_id": "route_3", "state": "REJECTED_BY_BUDGET"},
        ],
    )

    assert [route["lifecycle_state"] for route in manifest["routes"]] == [
        "ROUTE_FAILED",
        "ROUTE_DEFERRED",
        "ROUTE_REJECTED",
    ]
    assert all(
        route["contribution_state"] == "CONTRIBUTION_NOT_MEASURABLE"
        for route in manifest["routes"]
    )


def test_arena_candidate_with_missing_route_lineage_breaks_lineage():
    context = _context(
        candidate_lineage_records=[
            {
                "candidate_id": "candidate_arena_unbound",
                "arena_state": "EVALUATED",
            }
        ]
    )

    manifest = _manifest(context)

    assert manifest["lineage_breaks"][0]["break_type"] == "candidate_with_no_route_lineage"


def test_repair_event_with_missing_route_lineage_does_not_create_contribution():
    context = _context(
        route_output_lineage_records=[
            {
                "output_type": "repair_proposal",
                "output_id": "repair_unbound",
                "repair_state": "ROUTE_CONTRIBUTED_TO_RESIDUAL_REDUCTION",
                "residual_reduction": 3,
            }
        ]
    )

    manifest = _manifest(context)

    assert manifest["lineage_breaks"][0]["break_type"] == "output_with_no_route_lineage"
    assert all(
        route["repair_contribution_count"] == 0
        for route in manifest["routes"]
    )


def test_copied_route_manifest_is_not_consumed_as_current_lineage():
    context = _context(
        route_contribution_manifest={
            "run_id": "old_run",
            "routes": [
                {
                    "route_id": "route_1",
                    "contribution_state": "UNIQUE_USEFUL_CONTRIBUTION",
                }
            ],
        }
    )

    manifest = _manifest(context)

    assert manifest["run_id"] == "run_a"
    assert manifest["routes"][0]["contribution_state"] == "NO_OBSERVABLE_CONTRIBUTION"


def test_incomplete_telemetry_reports_insufficient_or_partial_state():
    manifest = _manifest(context={"run_id": "run_a", "task_id": "task_a"})

    assert manifest["attribution_completeness_state"] == "ROUTE_ATTRIBUTION_INSUFFICIENT"
    assert manifest["lineage_continuity_state"] == "ROUTE_LINEAGE_BROKEN"


def test_classification_without_downstream_evidence_is_not_measurable():
    context = _context(
        route_output_lineage_records=[
            {
                "origin_route_id": "route_1",
                "output_type": "candidate",
                "candidate_id": "candidate_unknown_value",
                "output_fingerprint": "candidate:unknown:value",
            }
        ]
    )

    manifest = _manifest(context)

    assert manifest["routes"][0]["contribution_state"] == "CONTRIBUTION_NOT_MEASURABLE"


def test_compact_summary_exposes_only_bounded_human_report_fields():
    manifest = _manifest()

    summary = compact_route_contribution_summary(manifest)

    assert summary["authority"] == "OBSERVATION_ONLY"
    assert summary["behavioral_authority"] == "NONE"
    assert summary["telemetry_consumed_by_cognition"] is False
    assert "routes" not in summary


def test_route_origin_lineage_matches_current_executed_source_descriptor():
    manifest = _manifest(
        route_records=[
            {"route_id": "color_mapping", "route_rank": 1},
        ],
        route_lifecycle_records=[
            {"route_id": "color_mapping", "state": "ACTIVE_ROUTE"},
            {"route_id": "color_mapping", "state": "RELEASED_ROUTE"},
        ],
    )
    record = {
        "candidate_id": "candidate_color",
        "source": "program_generation",
        "intent": "color_mapping",
        "metadata": {"source_domain": "Color"},
    }

    lineage = route_origin_lineage_from_record(
        manifest,
        source_name="program_generation",
        record=record,
        produced_at_stage="program_generation_activation",
        producer_component="program_generation",
    )
    attached = attach_route_origin_lineage(record, lineage)

    assert lineage["route_lineage_scope_state"] == "ROUTE_ORIGIN_CURRENT"
    assert lineage["route_lineage_origin_type"] == "DIRECT_SOURCE_DESCRIPTOR"
    assert attached["origin_route_id"] == "color_mapping"
    assert attached["origin_route_execution_id"]
    assert attached["metadata"]["route_lineage_authority"] == "OBSERVATION_ONLY"
    assert attached["metadata"]["route_lineage_behavioral_authority"] == "NONE"


def test_route_origin_lineage_does_not_attach_unexecuted_or_stale_origin():
    manifest = _manifest(
        route_records=[
            {"route_id": "transformation_compilation", "route_rank": 10},
        ],
        route_lifecycle_records=[
            {"route_id": "transformation_compilation", "state": "DEFERRED_BY_BUDGET"},
        ],
    )
    record = {"candidate_id": "candidate_transform", "source": "program_generation"}

    lineage = route_origin_lineage_from_record(
        manifest,
        source_name="program_generation",
        record=record,
        produced_at_stage="program_generation_activation",
    )

    assert lineage["route_lineage_scope_state"] == "ROUTE_ORIGIN_NOT_OBSERVABLE"
    assert "origin_route_execution_id" not in attach_route_origin_lineage(record, lineage)
