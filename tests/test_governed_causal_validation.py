import json
from pathlib import Path

import pytest

from runtime.capability_intelligence.integrated_capability_qualification import (
    CapabilityQualificationLevel,
    IntegratedCapabilityQualificationEngine,
    capability_id_for_subject,
)
from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.epistemic.evidence_source_independence import (
    EvidenceSourceIndependenceEngine,
)
from runtime.training.validation_curriculum_registry import (
    ValidationCurriculumRegistry,
)
from runtime.validation.causal_validation_evidence import (
    CausalValidationEvidenceEvaluator,
)
from runtime.validation.validation_evidence_evaluator import (
    ValidationEvidenceEvaluator,
)
from runtime.validation.validation_task_execution_pipeline import (
    ValidationTaskExecutionPipeline,
)
from runtime.validation.validation_task_scheduler import ValidationTaskScheduler


def _subject(operation="replace_color"):
    return {
        "schema_version": "1.0",
        "capability_name": "replace_color_capability",
        "operation": operation,
        "domain": "color",
        "qualifiers": {},
    }


def _claim_subject(operation="replace_color"):
    return {
        "schema_version": "1.0",
        "kind": "capability_operation",
        "subject_ref": capability_id_for_subject(_subject(operation)),
        "operation": operation,
        "semantic_scope": "qualification",
    }


def _plan(**overrides):
    subject = _subject(overrides.pop("operation", "replace_color"))
    capability_id = capability_id_for_subject(subject)
    plan = {
        "source_run_id": "causal_validation_run_a",
        "source_task_id": "causal_validation_task_a",
        "source_candidate_id": capability_id,
        "source_operation": subject["operation"],
        "evidence_acquisition_state": "EVIDENCE_ACQUISITION_PLAN_READY",
        "evidence_acquisition_trigger": "QUALIFICATION_CAUSAL_SUPPORT_REQUIRED",
        "required_evidence_category": "CAUSAL_OPERATION_EFFECT",
        "required_evidence": "capability_causal_operation_effect_evidence",
        "required_validation_task": "causal_operation_effect_validation_task",
        "tie_break_strategy": "causal_operation_effect",
        "target_candidate": capability_id,
        "target_operation": subject["operation"],
        "capability_id": capability_id,
        "capability_subject": subject,
        "claim_id": "claim_replace_color_support",
        "claim_subject": _claim_subject(subject["operation"]),
        "claim_subject_owner": "capability_qualification",
        "claim_evidence_binding_authority": "OBSERVATION_ONLY",
        "claim_evidence_binding_behavioral_authority": "NONE",
        "claim_evidence_binding_state": "CLAIM_IDENTIFIED_NOT_EVIDENCE_BOUND",
        "qualification_target_level": "REPRODUCIBLY_SUPPORTED",
        "required_independent_sources": 2,
        "governed_reentry_action": "submit_causal_evidence_to_evaluation",
    }
    plan.update(overrides)
    return plan


def _causal_case(**overrides):
    case = {
        "operation": "replace_color",
        "qualification_claim_id": "claim_replace_color_support",
        "input": [[1, 0], [0, 1]],
        "expected_output": [[2, 0], [0, 2]],
        "minimum_effect": 1.0,
        "treatment": {
            "output": [[2, 0], [0, 2]],
            "operation_executed": True,
            "operation_output_consumed": True,
        },
        "control": {
            "output": [[1, 0], [0, 1]],
            "counterfactual_valid": True,
            "same_non_target_operations": True,
        },
    }
    case.update(overrides)
    return case


def _write_curriculum(path: Path, *, case=None):
    task = {
        "task_id": "causal_validation_task_replace_color",
        "task_name": "Replace Color Causal Effect",
        "target_capability": "replace_color",
        "target_domain": "Color",
        "primary_evidence_category": "CAUSAL_OPERATION_EFFECT",
        "secondary_evidence_categories": [
            "capability_causal_operation_effect_evidence"
        ],
        "required_validation_evidence": (
            "capability_causal_operation_effect_evidence"
        ),
        "required_grounding": ["controlled_transformation_effect"],
        "expected_validation_contract": "causal_operation_effect_contract",
        "validation_objective": "measure replace_color causal effect",
        "validation_task_type": "causal_operation_effect",
        "causal_validation_case": case or _causal_case(),
        "evaluation_contract": {
            "comparator_id": "causal_operation_effect_comparison",
            "comparator_version": "1.0",
            "minimum_case_coverage": 1.0,
            "exact_match_required": True,
            "minimum_effect": 1.0,
        },
        "expected_target_output": {"causal_contract": "evaluator_only"},
        "enabled": True,
    }
    path.write_text(json.dumps({"tasks": [task]}), encoding="utf-8")


def _registry(path):
    registry = ValidationCurriculumRegistry()
    registry.register_curriculum(
        identifier="causal_validation_academy",
        display_name="Causal Validation Academy",
        path=path,
        enabled=True,
    )
    return registry


def _run_path(tmp_path, *, case=None, plan_overrides=None):
    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum, case=case)
    registry = _registry(curriculum)
    store = EvidenceAcquisitionPlanStore(tmp_path)
    persisted = store.persist_plan(_plan(**(plan_overrides or {})))
    store.mark_consumption_pending(persisted["evidence_plan_id"])
    store.persist_selection_from_consumption_report({
        "current_plan_id": persisted["evidence_plan_id"],
        "selection_state": "WAITING_EXECUTION",
        "consumption_state": "MATCHING_COMPLETED",
        "selected_validation_task": "causal_validation_task_replace_color",
        "best_matching_curriculum": "Causal Validation Academy",
        "current_required_evidence": "capability_causal_operation_effect_evidence",
        "current_target_operation": "replace_color",
        "current_tie_break_strategy": "causal_operation_effect",
        "selected_validation_task_metadata": {
            "curriculum_id": "causal_validation_academy",
        },
    })
    schedule = ValidationTaskScheduler(tmp_path, registry).schedule_plan(
        persisted["evidence_plan_id"]
    )
    raw = ValidationTaskExecutionPipeline(tmp_path, registry).execute_schedule(
        schedule["schedule_id"]
    )
    evaluation = ValidationEvidenceEvaluator(tmp_path, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )
    accepted = json.loads(
        (
            tmp_path
            / "accepted_evidence"
            / f"{evaluation['accepted_evidence_id']}.json"
        ).read_text(encoding="utf-8")
    )
    return {
        "schedule": schedule,
        "raw": raw,
        "evaluation": evaluation,
        "accepted": accepted,
    }


def test_positive_causal_validation_reaches_accepted_evidence(tmp_path):
    result = _run_path(tmp_path)
    accepted = result["accepted"]

    assert result["raw"]["execution_state"] == "RAW_RESULT_CAPTURED"
    assert result["evaluation"]["evidence_acceptance_state"] == "ACCEPTED"
    assert accepted["causal_evidence_id"].startswith("causal_evidence_")
    assert accepted["capability_causal_support_state"] == "CAUSALLY_SUPPORTED"
    assert accepted["causal_evidence"]["target_operation_executed"] is True
    assert accepted["causal_evidence"]["target_operation_output_consumed"] is True
    assert accepted["causal_evidence"]["counterfactual_state"] == (
        "COUNTERFACTUAL_VALID"
    )
    assert accepted["causal_evidence"]["qualification_claim_id"] == (
        accepted["claim_id"]
    )
    assert accepted["capability_support_operation"] == "replace_color"
    assert accepted["causal_evidence_authority"] == (
        "CAUSAL_VALIDATION_EVIDENCE_EVALUATOR"
    )
    assert accepted["truth_authority"] == "NONE"


def test_negative_causal_result_can_be_accepted_without_causal_support(tmp_path):
    case = _causal_case(
        control={
            "output": [[2, 0], [0, 2]],
            "counterfactual_valid": True,
            "same_non_target_operations": True,
        }
    )
    result = _run_path(tmp_path, case=case)
    accepted = result["accepted"]

    assert result["evaluation"]["evidence_acceptance_state"] == "ACCEPTED"
    assert accepted["causal_support_state"] == "CAUSAL_SUPPORT_NOT_ESTABLISHED"
    assert accepted["capability_causal_support_state"] == (
        "CAUSAL_SUPPORT_NOT_ESTABLISHED"
    )
    assert accepted["causal_evidence"]["causal_effect"] == 0.0


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ({"treatment": {"operation_executed": False}}, "target_operation_not_executed"),
        (
            {"treatment": {"operation_output_consumed": False}},
            "target_operation_output_not_consumed",
        ),
        ({"control": {"counterfactual_valid": False}}, "invalid_counterfactual"),
        ({"control": {"input": [[9]], "same_non_target_operations": True}}, "counterfactual_input_mismatch"),
        (
            {"control": {"same_non_target_operations": False}},
            "counterfactual_non_target_operations_mismatch",
        ),
        ({"control": {"unrelated_control": True}}, "unrelated_control_candidate"),
        ({"operation": ""}, "missing_operation"),
        ({"qualification_claim_id": ""}, "missing_qualification_claim_id"),
    ],
)
def test_causal_contract_attacks_fail_closed(mutation, reason):
    case = _causal_case()
    for key, value in mutation.items():
        if isinstance(value, dict) and isinstance(case.get(key), dict):
            case[key].update(value)
        else:
            case[key] = value
    raw = {
        "capability_id": capability_id_for_subject(_subject()),
        "target_operation": "replace_color",
        "claim_id": "claim_replace_color_support",
        "causal_validation_result": {
            **case,
            "operation_executed": case["treatment"].get("operation_executed", True),
            "operation_output_consumed": case["treatment"].get(
                "operation_output_consumed", True
            ),
            "counterfactual_valid": case["control"].get("counterfactual_valid", True),
            "same_input": case["control"].get("input", case["input"]) == case["input"],
            "same_non_target_operations": case["control"].get(
                "same_non_target_operations", True
            ),
            "unrelated_control": case["control"].get("unrelated_control", False),
            "treatment_score": 1.0,
            "control_score": 0.0,
        },
    }

    report = CausalValidationEvidenceEvaluator().evaluate(raw)

    assert report["causal_support_state"] == "CAUSAL_SUPPORT_NOT_ESTABLISHED"
    assert reason in report["causal_support_contract_failures"]


def test_accepted_causal_evidence_reaches_qualification_without_direct_promotion(tmp_path):
    result = _run_path(tmp_path)
    accepted = result["accepted"]
    prior = {
        **accepted,
        "accepted_evidence_id": "accepted_prior_source",
        "evidence_decision_id": "decision_prior",
        "canonical_source_identity": "source_a",
        "producer_operation_id": "source_a",
        "source_lineage": ["source_a"],
        "source_provenance": {
            **accepted["source_provenance"],
            "producer_operation_id": "source_a",
            "source_lineage": ["source_a"],
        },
        "accepted_evidence_origin": {
            **accepted["accepted_evidence_origin"],
            "origin_operation_id": "source_a",
        },
    }
    prior["claim_evidence_binding"] = {
        "claim_id": prior["claim_id"],
        "accepted_evidence_id": prior["accepted_evidence_id"],
    }
    accepted["canonical_source_identity"] = "source_b"
    qualification = IntegratedCapabilityQualificationEngine().decide(
        _subject(),
        [prior, accepted],
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        architecture_present=True,
        runtime_reachable=True,
        required_independent_sources=2,
    )

    decision = qualification["qualification_decision"]
    assert decision["qualification_authority"] == (
        "INTEGRATED_CAPABILITY_QUALIFICATION_ENGINE"
    )
    assert decision["authority"]["truth"] == "NONE"
    assert decision["independent_source_count"] == 2
    assert decision["decision_state"] == "PROMOTION_GRANTED"


def test_source_independence_remains_downstream_of_causal_evidence(tmp_path):
    result = _run_path(tmp_path)
    accepted = result["accepted"]
    accepted["canonical_source_identity"] = "source_a"
    coverage = EvidenceSourceIndependenceEngine().source_coverage(
        [accepted],
        claim_id=accepted["claim_id"],
        required_independent_sources=2,
    )

    assert coverage["current_proven_independent_source_count"] == 1
    assert coverage["truth_authority"] == "NONE"


def test_single_accepted_causal_evidence_does_not_promote_reproducible_level(tmp_path):
    result = _run_path(tmp_path)
    accepted = result["accepted"]
    accepted["canonical_source_identity"] = "source_b"
    qualification = IntegratedCapabilityQualificationEngine().decide(
        _subject(),
        [accepted],
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        architecture_present=True,
        runtime_reachable=True,
        required_independent_sources=2,
    )

    assert qualification["qualification_decision"]["decision_state"] == (
        "PROMOTION_DENIED"
    )
    assert qualification["qualification_decision"]["independent_source_count"] == 1


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda e: e.update({"capability_id": "capability_wrong"}), "some_evidence_rejected"),
        (lambda e: e.update({"capability_support_operation": "rotate"}), "some_evidence_rejected"),
        (lambda e: e.update({"claim_id": "claim_other"}), "independent_reproducibility_not_established"),
    ],
)
def test_causal_evidence_wrong_binding_does_not_count(tmp_path, mutation, reason):
    result = _run_path(tmp_path)
    accepted = result["accepted"]
    accepted["canonical_source_identity"] = "source_b"
    mutation(accepted)
    qualification = IntegratedCapabilityQualificationEngine().decide(
        _subject(),
        [accepted],
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        architecture_present=True,
        runtime_reachable=True,
        required_independent_sources=2,
    )

    assert qualification["qualification_decision"]["decision_state"] == (
        "PROMOTION_DENIED"
    )
    assert reason in qualification["qualification_decision"]["promotion_failures"]


@pytest.mark.parametrize(
    "field",
    ["origin_run_id", "origin_task_id"],
)
def test_same_source_across_run_or_task_does_not_inflate_causal_sources(tmp_path, field):
    result = _run_path(tmp_path)
    first = result["accepted"]
    second = json.loads(json.dumps(first))
    first["accepted_evidence_id"] = "accepted_causal_a"
    second["accepted_evidence_id"] = "accepted_causal_b"
    first["claim_evidence_binding"] = {
        **first["claim_evidence_binding"],
        "accepted_evidence_id": "accepted_causal_a",
    }
    second["claim_evidence_binding"] = {
        **second["claim_evidence_binding"],
        "accepted_evidence_id": "accepted_causal_b",
    }
    first["canonical_source_identity"] = "source_a"
    second["canonical_source_identity"] = "source_a"
    second["accepted_evidence_origin"][field] = f"different_{field}"
    qualification = IntegratedCapabilityQualificationEngine().decide(
        _subject(),
        [first, second],
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        architecture_present=True,
        runtime_reachable=True,
        required_independent_sources=2,
    )

    assert qualification["qualification_decision"]["independent_source_count"] == 1
    assert qualification["qualification_decision"]["decision_state"] == (
        "PROMOTION_DENIED"
    )


def test_manifest_validation_success_is_not_causal_evidence(tmp_path):
    from tests.test_validation_evidence_evaluator import _accepted_result, _registry, _write_curriculum

    curriculum = tmp_path / "curriculum.json"
    _write_curriculum(curriculum)
    result = _accepted_result(tmp_path, _registry(curriculum))
    accepted = result["accepted"]

    assert accepted.get("causal_evidence_id") is None
    assert accepted.get("capability_causal_support_state") is None
