import json
from pathlib import Path

from runtime.arena import ArenaMemory, CognitiveCandidateArena
from runtime.evidence import CandidateDisambiguationPlanningAdapter
from runtime.training.validation_curriculum_registry import ValidationCurriculumRegistry
from runtime.validation.validation_task_scheduler import ValidationTaskScheduler


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


def _tie_need():
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
        runtime_context={"run_id": "run_disambiguation", "task_id": "task_disambiguation"},
        task_signature="candidate-disambiguation-planning",
    )
    assert report["selection_state"] == "TIE_REQUIRES_REVIEW"
    disambiguation = report["candidate_arena_diagnostics"][
        "candidate_disambiguation_report"
    ]
    return disambiguation["candidate_disambiguation_evidence_needs"][0]


def _write_curriculum(path: Path):
    path.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "task_id": "candidate_discriminative_probe_validation_task",
                        "task_name": "Candidate Discriminative Probe",
                        "target_capability": "candidate_disambiguation",
                        "target_domain": "Candidate Disambiguation",
                        "supported_evidence": [
                            "CANDIDATE_DISAMBIGUATION",
                            "candidate_discriminative_probe_evidence",
                        ],
                        "primary_evidence_category": "CANDIDATE_DISAMBIGUATION",
                        "secondary_evidence_categories": [
                            "candidate_discriminative_probe_evidence"
                        ],
                        "required_validation_evidence": (
                            "candidate_discriminative_probe_evidence"
                        ),
                        "required_grounding": [
                            "candidate_discriminative_probe",
                            "candidate_discriminative_probe_validation_task",
                        ],
                        "expected_validation_contract": (
                            "candidate_discriminative_probe_validation_task"
                        ),
                        "enabled": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def _registry(path: Path):
    registry = ValidationCurriculumRegistry()
    registry.register_curriculum(
        identifier="candidate_disambiguation_curriculum",
        display_name="Candidate Disambiguation Curriculum",
        path=path,
        enabled=True,
    )
    return registry


def _make_schedulable(adapter, plan_id):
    adapter.plan_store.mark_consumption_pending(plan_id)
    return adapter.plan_store.persist_selection_from_consumption_report(
        {
            "current_plan_id": plan_id,
            "selection_state": "WAITING_EXECUTION",
            "selected_validation_task": "candidate_discriminative_probe_validation_task",
            "best_matching_curriculum": "Candidate Disambiguation Curriculum",
            "current_required_evidence": "candidate_discriminative_probe_evidence",
            "current_target_operation": "candidate_discriminative_probe",
            "current_tie_break_strategy": "candidate_discriminative_probe",
            "selected_validation_task_metadata": {
                "curriculum_id": "candidate_disambiguation_curriculum",
            },
        }
    )


def test_candidate_disambiguation_need_reaches_schedulable_plan_d6(tmp_path):
    adapter = CandidateDisambiguationPlanningAdapter(tmp_path / "adapter")
    result = adapter.admit_need_to_plan(_tie_need())
    plan_id = result["evidence_plan_report"]["evidence_plan_id"]
    _make_schedulable(adapter, plan_id)
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    scheduler = ValidationTaskScheduler(
        tmp_path / "adapter" / "evidence_acquisition_plans",
        _registry(curriculum),
        need_authority=adapter.need_authority,
        sponsorship_authority=adapter.sponsorship_authority,
        request_authority=adapter.request_authority,
    )
    scheduled = scheduler.schedule_plan(plan_id)

    assert result["planning_status"] == "D6_EVIDENCE_PLAN_REACHED"
    assert result["adapter_authority"] == "NONE"
    assert result["outcome_blind_selection"] is True
    assert result["validation_intent"]["future_outcome_fields_used_for_selection"] == []
    assert result["governed_sponsorship_reachable"] is True
    assert result["validation_request_reachable"] is True
    assert result["evidence_plan_reachable"] is True
    assert result["safe_winner_forced"] is False
    assert result["tie_resolved"] is False
    assert scheduled["scheduling_admission_state"] == "ADMITTED"
    assert scheduled["scheduling_state"] == "SCHEDULED"
    assert scheduled["task_execution_started"] is False
    assert scheduled["execution_authority"] == "NONE"


def test_duplicate_disambiguation_need_reuses_semantic_plan(tmp_path):
    adapter = CandidateDisambiguationPlanningAdapter(tmp_path / "adapter")
    need = _tie_need()

    first = adapter.admit_need_to_plan(need)
    second = adapter.admit_need_to_plan(need)

    assert first["evidence_plan_report"]["evidence_plan_id"] == second[
        "evidence_plan_report"
    ]["evidence_plan_id"]
    assert second["evidence_plan_report"]["evidence_plan_storage_state"] == (
        "EQUIVALENT_PENDING_PLAN_REUSED"
    )
    assert len(list((tmp_path / "adapter" / "evidence_acquisition_plans" / "pending").glob("*.json"))) == 1


def test_no_tie_produces_no_disambiguation_planning_work():
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
        runtime_context={"run_id": "run_no_tie"},
    )
    disambiguation = report["candidate_arena_diagnostics"][
        "candidate_disambiguation_report"
    ]

    assert report["selection_state"] == "WINNER_SELECTED"
    assert disambiguation["candidate_disambiguation_evidence_needs"] == []


def test_invalid_and_unsupported_disambiguation_needs_fail_closed(tmp_path):
    adapter = CandidateDisambiguationPlanningAdapter(tmp_path / "adapter")
    need = _tie_need()

    missing_identity = {**need, "candidate_ids": []}
    missing_lineage = json.loads(json.dumps(need))
    missing_lineage["task_binding"]["run_id"] = None
    unsupported = {**need, "proposed_evidence_method": "CAUSAL_DISAMBIGUATION"}
    nondiscriminating = json.loads(json.dumps(need))
    first = nondiscriminating["candidate_ids"][0]
    same_prediction = nondiscriminating["expected_candidate_predictions"][first]
    for candidate_id in nondiscriminating["candidate_ids"]:
        nondiscriminating["expected_candidate_predictions"][candidate_id] = same_prediction

    for payload, expected in (
        (missing_identity, "INVALID"),
        (missing_lineage, "INVALID"),
        (unsupported, "UNSUPPORTED_METHOD"),
        (nondiscriminating, "INVALID"),
    ):
        report = adapter.admit_need_to_plan(payload)
        assert report["planning_status"] == expected
        assert report["evidence_plan_reachable"] is False
        assert report["safe_winner_forced"] is False
        assert report["accepted_evidence_created"] is False


def test_supported_method_taxonomy_is_minimal():
    adapter = CandidateDisambiguationPlanningAdapter()

    assert adapter.SUPPORTED_METHODS == {"DISCRIMINATIVE_VALIDATION"}
