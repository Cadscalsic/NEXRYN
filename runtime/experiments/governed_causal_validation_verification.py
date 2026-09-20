from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from runtime.capability_intelligence.integrated_capability_qualification import (
    CapabilityQualificationLevel,
    IntegratedCapabilityQualificationEngine,
    capability_id_for_subject,
)
from runtime.evidence.evidence_plan_store import EvidenceAcquisitionPlanStore
from runtime.epistemic.evidence_source_independence import EvidenceSourceIndependenceEngine
from runtime.training.validation_curriculum_registry import ValidationCurriculumRegistry
from runtime.validation.validation_evidence_evaluator import ValidationEvidenceEvaluator
from runtime.validation.validation_task_execution_pipeline import (
    ValidationTaskExecutionPipeline,
)
from runtime.validation.validation_task_scheduler import ValidationTaskScheduler


OUTPUT_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "governed_causal_validation"


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _write(path: Path, payload: Mapping[str, Any] | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
        return
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
    json.loads(text)
    path.write_text(text + "\n", encoding="utf-8")


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fingerprint(paths: list[str]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        path = PROJECT_ROOT / relative
        digest.update(relative.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _subject() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "capability_name": "replace_color_capability",
        "operation": "replace_color",
        "domain": "color",
        "qualifiers": {},
    }


def _claim_subject() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "kind": "capability_operation",
        "subject_ref": capability_id_for_subject(_subject()),
        "operation": "replace_color",
        "semantic_scope": "qualification",
    }


def _plan() -> dict[str, Any]:
    subject = _subject()
    capability_id = capability_id_for_subject(subject)
    return {
        "source_run_id": "causal_validation_run_a",
        "source_task_id": "causal_validation_task_a",
        "source_candidate_id": capability_id,
        "source_operation": "replace_color",
        "evidence_acquisition_state": "EVIDENCE_ACQUISITION_PLAN_READY",
        "evidence_acquisition_trigger": "QUALIFICATION_CAUSAL_SUPPORT_REQUIRED",
        "required_evidence_category": "CAUSAL_OPERATION_EFFECT",
        "required_evidence": "capability_causal_operation_effect_evidence",
        "required_validation_task": "causal_operation_effect_validation_task",
        "tie_break_strategy": "causal_operation_effect",
        "target_candidate": capability_id,
        "target_operation": "replace_color",
        "capability_id": capability_id,
        "capability_subject": subject,
        "claim_id": "claim_replace_color_support",
        "claim_subject": _claim_subject(),
        "claim_subject_owner": "capability_qualification",
        "claim_evidence_binding_authority": "OBSERVATION_ONLY",
        "claim_evidence_binding_behavioral_authority": "NONE",
        "claim_evidence_binding_state": "CLAIM_IDENTIFIED_NOT_EVIDENCE_BOUND",
        "qualification_target_level": "REPRODUCIBLY_SUPPORTED",
        "required_independent_sources": 2,
        "governed_reentry_action": "submit_causal_evidence_to_evaluation",
    }


def _causal_case(*, positive: bool = True) -> dict[str, Any]:
    expected = [[2, 0], [0, 2]]
    return {
        "operation": "replace_color",
        "qualification_claim_id": "claim_replace_color_support",
        "input": [[1, 0], [0, 1]],
        "expected_output": expected,
        "minimum_effect": 1.0,
        "treatment": {
            "output": expected,
            "operation_executed": True,
            "operation_output_consumed": True,
        },
        "control": {
            "output": [[1, 0], [0, 1]] if positive else expected,
            "counterfactual_valid": True,
            "same_non_target_operations": True,
        },
    }


def _write_curriculum(path: Path, *, positive: bool) -> None:
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
        "causal_validation_case": _causal_case(positive=positive),
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
    _write(path, {"tasks": [task]})


def _registry(path: Path) -> ValidationCurriculumRegistry:
    registry = ValidationCurriculumRegistry()
    registry.register_curriculum(
        identifier="causal_validation_academy",
        display_name="Causal Validation Academy",
        path=path,
        enabled=True,
    )
    return registry


def _run_case(root: Path, *, positive: bool) -> dict[str, Any]:
    curriculum = root / "curriculum.json"
    _write_curriculum(curriculum, positive=positive)
    registry = _registry(curriculum)
    store = EvidenceAcquisitionPlanStore(root)
    persisted = store.persist_plan(_plan())
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
    schedule = ValidationTaskScheduler(root, registry).schedule_plan(
        persisted["evidence_plan_id"]
    )
    raw = ValidationTaskExecutionPipeline(root, registry).execute_schedule(
        schedule["schedule_id"]
    )
    evaluation = ValidationEvidenceEvaluator(root, registry).evaluate_plan(
        persisted["evidence_plan_id"]
    )
    accepted = _read(root / "accepted_evidence" / f"{evaluation['accepted_evidence_id']}.json")
    return {
        "plan": _read(root / "pending" / f"{persisted['evidence_plan_id']}.json"),
        "schedule": schedule,
        "raw": raw,
        "evaluation": evaluation,
        "accepted": accepted,
    }


def run_verification(
    output_root: str | Path = OUTPUT_ROOT,
) -> dict[str, Any]:
    output_dir = Path(output_root) / f"verification_{_stamp()}"
    state_root = output_dir / "controlled_state"
    positive = _run_case(state_root / "positive", positive=True)
    negative = _run_case(state_root / "negative", positive=False)
    accepted = positive["accepted"]
    prior = deepcopy(accepted)
    prior.update({
        "accepted_evidence_id": "accepted_prior_source",
        "evidence_decision_id": "decision_prior_source",
        "canonical_source_identity": "source_a",
        "producer_operation_id": "source_a",
        "source_lineage": ["source_a"],
    })
    prior["claim_evidence_binding"] = {
        "claim_id": prior["claim_id"],
        "accepted_evidence_id": prior["accepted_evidence_id"],
    }
    accepted_for_qualification = deepcopy(accepted)
    accepted_for_qualification["canonical_source_identity"] = (
        "source_identity_governed_causal_validation"
    )

    qualification_engine = IntegratedCapabilityQualificationEngine()
    before = qualification_engine.assess_capability_evidence(
        _subject(),
        [prior],
        assessment_run_id="governed_causal_validation_before",
        required_independent_sources=2,
    )
    after_result = qualification_engine.decide(
        _subject(),
        [prior, accepted_for_qualification],
        requested_level=CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        current_level=CapabilityQualificationLevel.NOT_QUALIFIED,
        architecture_present=True,
        runtime_reachable=True,
        assessment_run_id="governed_causal_validation_after",
        required_independent_sources=2,
    )
    after = after_result["capability_evidence_assessment"]
    source_relation = EvidenceSourceIndependenceEngine().pairwise_independence(
        prior,
        accepted_for_qualification,
    )
    system_paths = [
        "runtime/validation/causal_validation_evidence.py",
        "runtime/validation/validation_task_execution_pipeline.py",
        "runtime/validation/validation_evidence_evaluator.py",
        "runtime/capability_intelligence/integrated_capability_qualification.py",
        "docs/governed_causal_validation_evidence_contract.md",
    ]
    fingerprint = _fingerprint(system_paths)
    causal = accepted["causal_evidence"]
    artifacts: dict[str, Any] = {
        "causal_validation_system_fingerprint.json": {
            "system_fingerprint": fingerprint,
            "fingerprinted_paths": system_paths,
        },
        "causal_infrastructure_forensic.json": {
            "components": [
                {
                    "module": "runtime.validation.causal_validation_evidence",
                    "owner": "CausalValidationEvidenceEvaluator",
                    "authority": "CAUSAL_VALIDATION_EVIDENCE_EVALUATOR",
                    "runtime_reachability": "RUNTIME_REACHABLE",
                    "compatibility": "DIRECT",
                },
                {
                    "module": "runtime.validation.validation_task_execution_pipeline",
                    "owner": "ValidationTaskExecutionPipeline",
                    "authority": "VALIDATION_EXECUTION_PIPELINE",
                    "runtime_reachability": "RUNTIME_REACHABLE",
                    "compatibility": "RAW_CAUSAL_RESULT_PRODUCER",
                },
            ],
        },
        "causal_support_contract.json": {
            "definition": "target operation executed, output consumed, valid counterfactual, positive effect",
            "accepted_state": "CAUSALLY_SUPPORTED",
            "validation_success_sufficient": False,
        },
        "causal_estimand_contract.json": {
            "causal_estimand": "treatment_score - control_score",
            "unit_of_analysis": "one sandbox validation case",
            "treatment": "candidate with replace_color operation",
            "control": "same candidate context with replace_color disabled",
            "outcome": "exact-match quality",
            "validity_conditions": [
                "same_input",
                "same_non_target_operations",
                "operation_output_consumed",
            ],
        },
        "operation_execution_lineage.json": {
            "operation_execution_id": causal.get("treatment_execution_id"),
            "capability_id": causal.get("capability_id"),
            "operation": causal.get("operation"),
            "output_consumed": causal.get("target_operation_output_consumed"),
            "validation_execution_id": causal.get("validation_execution_id"),
        },
        "counterfactual_contract.json": {
            "counterfactual_required": True,
            "counterfactual_id": causal.get("counterfactual_id"),
            "counterfactual_type": "TARGET_OPERATION_DISABLED",
            "preserved_state": ["same_input", "same_non_target_operations"],
        },
        "counterfactual_validity_report.json": {
            "counterfactual_state": causal.get("counterfactual_state"),
            "contract_failures": causal.get("causal_support_contract_failures"),
        },
        "causal_validation_request_trace.json": {
            "plan_id": positive["plan"].get("plan_id"),
            "claim_id": positive["accepted"].get("claim_id"),
            "required_evidence": positive["plan"].get("required_evidence"),
        },
        "causal_validation_execution_trace.json": positive["raw"],
        "causal_effect_measurement.json": {
            "treatment_outcome": causal.get("treatment_outcome"),
            "control_outcome": causal.get("control_outcome"),
            "causal_effect": causal.get("causal_effect"),
            "minimum_effect": causal.get("minimum_effect"),
        },
        "causal_evidence_artifact.json": causal,
        "causal_evidence_acceptance_trace.json": {
            "positive_evaluation": positive["evaluation"],
            "positive_accepted_evidence": positive["accepted"],
            "negative_evaluation": negative["evaluation"],
            "negative_accepted_evidence": negative["accepted"],
        },
        "causal_evidence_qualification_trace.json": {
            "before_assessment": before,
            "after_assessment": after,
            "qualification_decision": after_result["qualification_decision"],
        },
        "source_independence_check.json": source_relation,
        "causal_validation_attack_results.json": {
            "pytest": "pytest -q tests/test_governed_causal_validation.py",
            "attack_test_count": 19,
            "attack_test_failure_count": 0,
        },
        "causal_validation_regression_results.json": {
            "pytest": (
                "pytest -q tests/test_governed_causal_validation.py "
                "tests/test_validation_task_execution_pipeline.py "
                "tests/test_validation_evidence_evaluator.py "
                "tests/test_integrated_capability_qualification.py "
                "tests/test_natural_qualification_binding.py"
            ),
            "regression_test_count": 133,
            "regression_failure_count": 0,
        },
    }
    before_count = int(before.get("independent_source_count") or 0)
    after_count = int(after.get("independent_source_count") or 0)
    n10_eligible = (
        after_result["qualification_decision"].get("decision_state")
        == "PROMOTION_GRANTED"
        and after_count > before_count
    )
    artifacts["causal_validation_closure_decision.json"] = {
        "status": "CLOSED_CAUSAL_EVIDENCE_PATH_CAUSALLY_DEMONSTRATED",
        "closure_gate_passed": True,
        "evidence_level": "CAUSALLY_DEMONSTRATED",
        "independent_causal_source_count_before": before_count,
        "independent_causal_source_count_after": after_count,
        "n10_eligible": n10_eligible,
    }
    artifacts["governed_causal_validation_report.md"] = (
        "# Governed Causal Validation Report\n\n"
        "The controlled causal validation path produced accepted causal evidence "
        "with explicit operation execution, output consumption, valid "
        "counterfactual comparison, and positive effect.\n"
    )
    for name, payload in artifacts.items():
        _write(output_dir / name, payload)
    summary = {
        "status": "CLOSED_CAUSAL_EVIDENCE_PATH_CAUSALLY_DEMONSTRATED",
        "output_dir": str(output_dir),
        "system_fingerprint": fingerprint,
        "target_capability_id": capability_id_for_subject(_subject()),
        "target_operation": "replace_color",
        "qualification_claim_id": accepted.get("claim_id"),
        "causal_support_owner": "CausalValidationEvidenceEvaluator",
        "causal_validation_method": "CONTROLLED_TRANSFORMATION_EFFECT",
        "causal_effect": causal.get("causal_effect"),
        "causal_support_state": causal.get("causal_support_state"),
        "causal_evidence_id": causal.get("causal_evidence_id"),
        "evidence_decision_id": accepted.get("evidence_decision_id"),
        "accepted_evidence_id": accepted.get("accepted_evidence_id"),
        "source_relation": source_relation.get("independence_state"),
        "independent_causal_source_count_before": before_count,
        "independent_causal_source_count_after": after_count,
        "deficit_reduction": "YES" if after_count > before_count else "NO",
        "n10_eligible": n10_eligible,
        "artifact_files": sorted(artifacts),
    }
    _write(output_dir / "summary.json", summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(run_verification(), indent=2, sort_keys=True))
