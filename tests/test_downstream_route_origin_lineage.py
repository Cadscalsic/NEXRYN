from __future__ import annotations

from runtime.arena.cognitive_candidate_arena import CognitiveCandidateArena
from runtime.reasoning.candidate_proposal_runtime import CandidateProposalRuntime
from runtime.telemetry.route_contribution import (
    attach_route_origin_lineage,
    build_route_contribution_manifest,
    route_origin_lineage_from_record,
)


def _manifest():
    return build_route_contribution_manifest(
        context={"run_id": "run_x", "task_id": "task_x"},
        route_records=[
            {"route_id": "color_mapping", "route_rank": 1},
        ],
        route_lifecycle_records=[
            {"route_id": "color_mapping", "state": "ACTIVE_ROUTE"},
            {"route_id": "color_mapping", "state": "RELEASED_ROUTE"},
        ],
        budget_report={
            "run_id": "run_x",
            "task_id": "task_x",
            "maximum_active_routes": 6,
        },
    )


def _candidate():
    return {
        "source": "program_generation",
        "candidate_id": "candidate_color",
        "intent": "color_mapping",
        "operation": "replace_color",
        "program": {
            "step_count": 1,
            "steps": [{
                "operation": "replace_color",
                "parameters": {"color_mapping": {1: 2}},
            }],
        },
        "source_confidence": 0.9,
        "metadata": {"source_domain": "Color"},
    }


def test_candidate_proposal_runtime_preserves_route_origin_lineage():
    manifest = _manifest()
    candidate = _candidate()
    lineage = route_origin_lineage_from_record(
        manifest,
        source_name="program_generation",
        record=candidate,
        produced_at_stage="program_generation_activation",
    )
    candidate = attach_route_origin_lineage(candidate, lineage)

    report = CandidateProposalRuntime().collect(
        candidate_sources={"program_generation": [candidate]},
    )
    proposal = report["candidate_proposals"][0]

    assert proposal["origin_route_id"] == "color_mapping"
    assert proposal["route_lineage_scope_state"] == "ROUTE_ORIGIN_CURRENT"
    assert proposal["metadata"]["origin_route_id"] == "color_mapping"
    assert proposal["authority"] == "OBSERVATION_ONLY"
    assert proposal["behavioral_authority"] == "NONE"


def test_arena_preserves_route_origin_without_changing_selection():
    manifest = _manifest()
    candidate = attach_route_origin_lineage(
        _candidate(),
        route_origin_lineage_from_record(
            manifest,
            source_name="program_generation",
            record=_candidate(),
            produced_at_stage="program_generation_activation",
        ),
    )
    plain_candidate = _candidate()
    arena = CognitiveCandidateArena()

    with_lineage = arena.run(
        [candidate],
        input_grid=[[1]],
        target_grid=[[2]],
        analysis_only=True,
        task_signature="task_x",
    )
    without_lineage = arena.run(
        [plain_candidate],
        input_grid=[[1]],
        target_grid=[[2]],
        analysis_only=True,
        task_signature="task_x",
    )

    lineage_row = with_lineage["candidate_summary"][0]
    plain_row = without_lineage["candidate_summary"][0]
    assert lineage_row["origin_route_id"] == "color_mapping"
    assert lineage_row["route_lineage_scope_state"] == "ROUTE_ORIGIN_CURRENT"
    assert lineage_row["status"] == plain_row["status"]
    assert lineage_row["score"] == plain_row["score"]
