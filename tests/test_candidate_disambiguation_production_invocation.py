import json

from runtime.arena import ArenaMemory, CognitiveCandidateArena
from runtime.evidence import (
    CandidateDisambiguationPlanningAdapter,
    CandidateDisambiguationProductionInvocationPolicy,
)


def _proposal(source, operation, steps, confidence=0.9, **extra):
    return {
        "source": source,
        "hypothesis_id": f"hypothesis:{source}:{operation}",
        "intent": operation,
        "operation": operation,
        "program": {"step_count": len(steps), "steps": steps},
        "source_confidence": confidence,
        "semantic_support": extra.pop("semantic_support", 0.9),
        "truth_support": extra.pop("truth_support", 0.9),
        "context_support": extra.pop("context_support", 0.9),
        "dependency_support": extra.pop("dependency_support", 0.9),
        "identity_support": extra.pop("identity_support", 0.9),
        "localization_support": extra.pop("localization_support", 0.9),
        **extra,
    }


def _tie_report(run_id="run_disambiguation"):
    report = CognitiveCandidateArena(memory=ArenaMemory()).run(
        [
            _proposal(
                "semantic_compiler",
                "replace_color",
                [
                    {
                        "operation": "replace_color",
                        "parameters": {
                            "color_mapping": {1: 2},
                            "affected_positions": [[0, 0], [0, 1]],
                        },
                    }
                ],
            ),
            _proposal(
                "rule_engine",
                "replace_color",
                [
                    {
                        "operation": "replace_color",
                        "parameters": {
                            "color_mapping": {1: 2},
                            "affected_positions": [[0, 0], [0, 2]],
                        },
                    }
                ],
            ),
        ],
        input_grid=[[1, 1, 1]],
        target_grid=[[2, 2, 2]],
        runtime_context={"run_id": run_id, "task_id": "task_disambiguation"},
        task_signature="candidate-disambiguation-production-invocation",
    )
    assert report["selection_state"] == "TIE_REQUIRES_REVIEW"
    return report


def _no_tie_report(run_id="run_no_tie"):
    report = CognitiveCandidateArena(memory=ArenaMemory()).run(
        [
            _proposal(
                "semantic_compiler",
                "replace_color",
                [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}],
            ),
            _proposal(
                "adaptive_reuse",
                "preserve_grid",
                [{"operation": "preserve_grid", "parameters": {}}],
                confidence=0.6,
            ),
        ],
        input_grid=[[1]],
        target_grid=[[2]],
        runtime_context={"run_id": run_id, "task_id": "task_no_tie"},
    )
    assert report["selection_state"] == "WINNER_SELECTED"
    return report


def _policy(tmp_path):
    return CandidateDisambiguationProductionInvocationPolicy(
        CandidateDisambiguationPlanningAdapter(tmp_path / "adapter")
    )


def _replace_need(report, need):
    report = json.loads(json.dumps(report))
    report["candidate_arena_diagnostics"]["candidate_disambiguation_report"][
        "candidate_disambiguation_evidence_needs"
    ] = [need]
    return report


def _need(report):
    return report["candidate_arena_diagnostics"]["candidate_disambiguation_report"][
        "candidate_disambiguation_evidence_needs"
    ][0]


def test_natural_arena_tie_invokes_planning_to_d6_same_run(tmp_path):
    report = _tie_report("run_positive")
    policy = _policy(tmp_path)

    result = policy.invoke_from_arena_report(report, current_run_id="run_positive")

    row = result["invocation_rows"][0]
    assert result["temporal_semantics"] == "SAME_RUN_PLANNING"
    assert result["d6_plan_reached_count"] == 1
    assert result["synthetic_downstream_object_count"] == 0
    assert row["semantic_replay_state"] == "NEW_DISAMBIGUATION_NEED"
    assert row["invocation_state"] == "PLANNING_ADMITTED_TO_D6"
    assert row["d3_to_d4"] is True
    assert row["d4_to_d5"] is True
    assert row["d5_to_d6"] is True
    assert result["authority"] == "NONE"
    assert result["safe_winner_forced"] is False
    assert result["tie_resolved"] is False
    assert result["raw_evidence_created"] is False
    assert result["accepted_evidence_created"] is False


def test_same_state_replay_reuses_existing_semantic_plan(tmp_path):
    report = _tie_report("run_replay")
    policy = _policy(tmp_path)

    first = policy.invoke_from_arena_report(report, current_run_id="run_replay")
    second = policy.invoke_from_arena_report(report, current_run_id="run_replay")

    assert first["created_or_reused_evidence_plan_ids"] == second[
        "created_or_reused_evidence_plan_ids"
    ]
    assert second["invocation_rows"][0]["semantic_replay_state"] == "SAME_STATE_REPLAY"
    assert second["duplicate_semantic_work_count"] == 1
    pending = tmp_path / "adapter" / "evidence_acquisition_plans" / "pending"
    assert len(list(pending.glob("*.json"))) == 1


def test_no_tie_or_no_candidate_need_does_not_plan(tmp_path):
    result = _policy(tmp_path).invoke_from_arena_report(
        _no_tie_report(),
        current_run_id="run_no_tie",
    )

    assert result["candidate_disambiguation_need_count"] == 0
    assert result["d6_plan_reached_count"] == 0
    assert result["created_or_reused_evidence_plan_ids"] == []


def test_invalid_need_controls_fail_closed(tmp_path):
    report = _tie_report("run_invalid")
    need = _need(report)
    policy = _policy(tmp_path)

    cases = [
        ({**need, "candidate_ids": []}, "fewer_than_two_discriminating_candidates"),
        ({**need, "candidate_set_id": None}, "missing_candidate_set_identity"),
        ({**need, "disagreement_id": None}, "missing_disagreement_identity"),
        ({**need, "arena_decision_id": None}, "missing_arena_lineage"),
        ({**need, "missing_discriminating_evidence": "FORGED_REQUIREMENT"}, "unsupported_or_forged_evidence_requirement"),
        ({**need, "proposed_evidence_method": "CAUSAL_DISAMBIGUATION"}, "unsupported_disambiguation_method"),
    ]
    for payload, expected_failure in cases:
        invalid_report = _replace_need(report, json.loads(json.dumps(payload)))
        result = policy.invoke_from_arena_report(
            invalid_report,
            current_run_id="run_invalid",
        )
        row = result["invocation_rows"][0]
        assert expected_failure in row["failure_reasons"]
        assert row["invocation_state"] == "FAILED_CLOSED"
        assert result["d6_plan_reached_count"] == 0


def test_non_discriminating_predictions_and_stale_lineage_fail_closed(tmp_path):
    report = _tie_report("run_lineage")
    need = json.loads(json.dumps(_need(report)))
    first = need["candidate_ids"][0]
    same_prediction = need["expected_candidate_predictions"][first]
    for candidate_id in need["candidate_ids"]:
        need["expected_candidate_predictions"][candidate_id] = same_prediction

    non_discriminating = _policy(tmp_path).invoke_from_arena_report(
        _replace_need(report, need),
        current_run_id="run_lineage",
    )
    assert "candidate_predictions_non_discriminating" in non_discriminating[
        "invocation_rows"
    ][0]["failure_reasons"]
    assert non_discriminating["d6_plan_reached_count"] == 0

    stale = _policy(tmp_path).invoke_from_arena_report(
        report,
        current_run_id="other_run",
    )
    assert "stale_or_invalid_runtime_lineage" in stale["invocation_rows"][0][
        "failure_reasons"
    ]
    assert stale["d6_plan_reached_count"] == 0


def test_identity_rebinding_under_old_need_id_fails_closed(tmp_path):
    report = _tie_report("run_rebinding")
    policy = _policy(tmp_path)
    assert policy.invoke_from_arena_report(
        report,
        current_run_id="run_rebinding",
    )["d6_plan_reached_count"] == 1

    altered = json.loads(json.dumps(_need(report)))
    altered["candidate_set_id"] = "candidate_set:altered"
    result = policy.invoke_from_arena_report(
        _replace_need(report, altered),
        current_run_id="run_rebinding",
    )

    row = result["invocation_rows"][0]
    assert row["semantic_replay_state"] == "INVALID_OR_STALE_NEED"
    assert row["invocation_state"] == "FAILED_CLOSED"
    assert result["d6_plan_reached_count"] == 0
