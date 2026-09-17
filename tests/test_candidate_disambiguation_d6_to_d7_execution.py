import json
from pathlib import Path

from runtime.arena import ArenaMemory, CognitiveCandidateArena
from runtime.evidence import (
    CandidateDisambiguationPlanningAdapter,
    CandidateDisambiguationProductionInvocationPolicy,
)
from runtime.training.validation_curriculum_registry import ValidationCurriculumRegistry
from runtime.validation.validation_task_execution_pipeline import (
    ValidationTaskExecutionPipeline,
)
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


def _tie_report(run_id="run_d7"):
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
        runtime_context={"run_id": run_id, "task_id": "task_d7"},
        task_signature="candidate-disambiguation-d6-to-d7",
    )
    assert report["selection_state"] == "TIE_REQUIRES_REVIEW"
    return report


def _write_curriculum(path: Path, *, non_discriminating=False):
    path.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "task_id": "candidate_discriminative_probe_validation_task",
                        "task_name": "Candidate Discriminative Probe",
                        "target_capability": "candidate_disambiguation",
                        "target_domain": "Candidate Disambiguation",
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
                        "validation_task_type": (
                            "ordinary_manifest_observation"
                            if non_discriminating
                            else "candidate_discriminative_probe"
                        ),
                        "validation_objective": (
                            "execute direct output-level discriminative probe"
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


def _produce_d6(tmp_path, *, run_id="run_d7"):
    adapter = CandidateDisambiguationPlanningAdapter(tmp_path / "state")
    policy = CandidateDisambiguationProductionInvocationPolicy(adapter)
    report = policy.invoke_from_arena_report(_tie_report(run_id), current_run_id=run_id)
    row = report["invocation_rows"][0]
    plan_id = row["adapter_report"]["evidence_plan_report"]["evidence_plan_id"]
    adapter.plan_store.mark_consumption_pending(plan_id)
    adapter.plan_store.persist_selection_from_consumption_report(
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
    return adapter, report, plan_id


def _schedule_and_execute(tmp_path, adapter, plan_id, registry):
    scheduler = ValidationTaskScheduler(
        tmp_path / "state" / "evidence_acquisition_plans",
        registry,
        need_authority=adapter.need_authority,
        sponsorship_authority=adapter.sponsorship_authority,
        request_authority=adapter.request_authority,
    )
    schedule = scheduler.schedule_plan(plan_id)
    pipeline = ValidationTaskExecutionPipeline(
        tmp_path / "state" / "evidence_acquisition_plans",
        registry,
        need_authority=adapter.need_authority,
        sponsorship_authority=adapter.sponsorship_authority,
        request_authority=adapter.request_authority,
    )
    execution = pipeline.execute_schedule(schedule["schedule_id"])
    return schedule, execution


def test_natural_d6_candidate_disambiguation_plan_executes_discriminative_d7(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    adapter, invocation, plan_id = _produce_d6(tmp_path)

    schedule, execution = _schedule_and_execute(
        tmp_path,
        adapter,
        plan_id,
        _registry(curriculum),
    )

    d7 = execution["candidate_disambiguation_execution"]
    assert invocation["d6_plan_reached_count"] == 1
    assert schedule["scheduling_state"] == "SCHEDULED"
    assert execution["execution_state"] == "RAW_RESULT_CAPTURED"
    assert execution["execution_invoked"] is True
    assert execution["raw_result_captured"] is True
    assert execution["candidate_disambiguation_d7_execution_state"] == (
        "DISCRIMINATIVE_EXECUTION_VALID"
    )
    assert d7["d7_execution_state"] == "DISCRIMINATIVE_EXECUTION_VALID"
    assert d7["disambiguation_method"] == "DIRECT"
    assert d7["candidate_a_prediction"] != d7["candidate_b_prediction"]
    assert d7["discriminating_condition_exercised"] is True
    assert execution["plan_id"] == plan_id
    assert execution["schedule_id"] == schedule["schedule_id"]
    assert d7["evidence_plan_id"] == plan_id
    assert d7["validation_schedule_id"] == schedule["schedule_id"]
    assert d7["validation_request_id"]
    assert execution["evidence_evaluation_invoked"] is False
    assert execution["evidence_accepted"] is False
    assert execution["arena_reentry_invoked"] is False
    assert execution["candidate_ranking_modified"] is False
    assert execution["candidate_execution_authority"] == "NONE"


def test_reprocessing_same_d6_schedule_reuses_raw_result_without_duplicate_execution(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    adapter, _, plan_id = _produce_d6(tmp_path, run_id="run_replay_d7")
    registry = _registry(curriculum)
    schedule, first = _schedule_and_execute(tmp_path, adapter, plan_id, registry)
    second = ValidationTaskExecutionPipeline(
        tmp_path / "state" / "evidence_acquisition_plans",
        registry,
        need_authority=adapter.need_authority,
        sponsorship_authority=adapter.sponsorship_authority,
        request_authority=adapter.request_authority,
    ).execute_schedule(schedule["schedule_id"])

    assert first["raw_result_creation_result"] == "CREATED_NEW_RAW_RESULT"
    assert second["raw_result_creation_result"] == "REUSED_EXISTING_RAW_RESULT"
    assert second["execution_invoked"] is False
    assert first["raw_result_id"] == second["raw_result_id"]
    assert len(list((tmp_path / "state" / "evidence_acquisition_plans" / "raw_results").glob("*.json"))) == 1


def test_candidate_disambiguation_execution_fails_closed_on_identity_and_disagreement_breaks(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    adapter, _, plan_id = _produce_d6(tmp_path, run_id="run_bad_d7")
    registry = _registry(curriculum)
    scheduler = ValidationTaskScheduler(
        tmp_path / "state" / "evidence_acquisition_plans",
        registry,
        need_authority=adapter.need_authority,
        sponsorship_authority=adapter.sponsorship_authority,
        request_authority=adapter.request_authority,
    )
    schedule = scheduler.schedule_plan(plan_id)
    plan_path = tmp_path / "state" / "evidence_acquisition_plans" / "pending" / f"{plan_id}.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["capability_subject"]["validation_intent"]["candidate_ids"] = []
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    report = ValidationTaskExecutionPipeline(
        tmp_path / "state" / "evidence_acquisition_plans",
        registry,
        need_authority=adapter.need_authority,
        sponsorship_authority=adapter.sponsorship_authority,
        request_authority=adapter.request_authority,
    ).execute_schedule(schedule["schedule_id"])

    assert report["execution_admission_state"] == (
        "BLOCKED_CANDIDATE_DISAMBIGUATION_CONTRACT"
    )
    assert report["execution_admission_reason"] == (
        "candidate_disambiguation_contract_INVALID_CANDIDATE_BINDING"
    )
    assert report["execution_invoked"] is False
    assert report["raw_result_captured"] is False


def test_non_discriminating_candidate_predictions_do_not_execute_as_d7(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    adapter, _, plan_id = _produce_d6(tmp_path, run_id="run_nondiscriminating_d7")
    registry = _registry(curriculum)
    schedule = ValidationTaskScheduler(
        tmp_path / "state" / "evidence_acquisition_plans",
        registry,
        need_authority=adapter.need_authority,
        sponsorship_authority=adapter.sponsorship_authority,
        request_authority=adapter.request_authority,
    ).schedule_plan(plan_id)
    plan_path = tmp_path / "state" / "evidence_acquisition_plans" / "pending" / f"{plan_id}.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    intent = plan["capability_subject"]["validation_intent"]
    first = intent["candidate_ids"][0]
    same = intent["expected_discriminating_outcome"]["candidate_predictions"][first]
    for candidate_id in intent["candidate_ids"]:
        intent["expected_discriminating_outcome"]["candidate_predictions"][candidate_id] = same
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    report = ValidationTaskExecutionPipeline(
        tmp_path / "state" / "evidence_acquisition_plans",
        registry,
        need_authority=adapter.need_authority,
        sponsorship_authority=adapter.sponsorship_authority,
        request_authority=adapter.request_authority,
    ).execute_schedule(schedule["schedule_id"])

    assert report["execution_admission_state"] == (
        "BLOCKED_CANDIDATE_DISAMBIGUATION_CONTRACT"
    )
    assert report["execution_admission_reason"] == (
        "candidate_disambiguation_contract_NON_DISCRIMINATING_EXECUTION"
    )
    assert report["execution_invoked"] is False


def test_cross_plan_execution_attempt_is_blocked_before_runner_invocation(tmp_path):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    adapter, _, plan_id = _produce_d6(tmp_path, run_id="run_cross_plan_d7")
    registry = _registry(curriculum)
    schedule = ValidationTaskScheduler(
        tmp_path / "state" / "evidence_acquisition_plans",
        registry,
        need_authority=adapter.need_authority,
        sponsorship_authority=adapter.sponsorship_authority,
        request_authority=adapter.request_authority,
    ).schedule_plan(plan_id)
    schedule_path = tmp_path / "state" / "evidence_acquisition_plans" / "schedules" / f"{schedule['schedule_id']}.json"
    schedule_record = json.loads(schedule_path.read_text(encoding="utf-8"))
    schedule_record["plan_id"] = "evidence_plan_other"
    schedule_path.write_text(json.dumps(schedule_record, indent=2), encoding="utf-8")

    report = ValidationTaskExecutionPipeline(
        tmp_path / "state" / "evidence_acquisition_plans",
        registry,
        need_authority=adapter.need_authority,
        sponsorship_authority=adapter.sponsorship_authority,
        request_authority=adapter.request_authority,
    ).execute_schedule(schedule["schedule_id"])

    assert report["execution_admission_state"] == "DENIED_PLAN_NOT_CURRENT"
    assert report["execution_invoked"] is False
