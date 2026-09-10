"""Evidence closure for adaptive route prediction and core checkpoint selection."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
PROGRAM_ARTIFACT_DIR = ROOT / "runtime" / "artifacts" / "adaptive_route_prediction_program"
CHECKPOINT_ROOT = ROOT / "runtime" / "artifacts" / "core_architecture_checkpoint"
P1_SUMMARY = ROOT / "runtime" / "artifacts" / "pre_route_controlled_replication" / "20260908_182938" / "pre_route_controlled_replication_summary.json"
P2_SUMMARY = ROOT / "runtime" / "artifacts" / "route_order_deconfounding" / "20260908_184411" / "route_order_deconfounding_summary.json"
P3_SUMMARY = ROOT / "runtime" / "artifacts" / "p3_route_predictive_validation" / "20260909_234453" / "p3_summary.json"
P3_FORENSIC_SUMMARY = ROOT / "runtime" / "artifacts" / "p3_signal_failure_forensic" / "20260910_000713" / "p3_signal_failure_forensic_summary.json"


CONSUMED_VALIDATION_TASKS = [f"task_{index:03d}.json" for index in range(1, 21)]
SELECTED_GAP_ID = "governed_evidence_acceptance_contract_completion"


def run_closure_and_checkpoint(
    *,
    program_artifact_dir: str | Path = PROGRAM_ARTIFACT_DIR,
    checkpoint_root: str | Path = CHECKPOINT_ROOT,
) -> dict[str, Any]:
    program_artifact_dir = Path(program_artifact_dir)
    checkpoint_root = Path(checkpoint_root)
    checkpoint_dir = checkpoint_root / datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    program_artifact_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    p1 = _read_json(P1_SUMMARY)
    p2 = _read_json(P2_SUMMARY)
    p3 = _read_json(P3_SUMMARY)
    forensic = _read_json(P3_FORENSIC_SUMMARY)

    closure = _closure_artifact(p1=p1, p2=p2, p3=p3, forensic=forensic)
    closed_inventory = _closed_area_inventory()
    unresolved = _unresolved_gap_inventory()
    dependency_graph = _dependency_graph(unresolved)
    next_gap = _next_gap_decision(unresolved)
    manifest = _checkpoint_manifest(
        checkpoint_dir=checkpoint_dir,
        closure=closure,
        closed_inventory=closed_inventory,
        unresolved=unresolved,
        dependency_graph=dependency_graph,
        next_gap=next_gap,
    )

    _write_json(program_artifact_dir / "adaptive_route_prediction_evidence_closure.json", closure)
    (program_artifact_dir / "adaptive_route_prediction_evidence_closure.md").write_text(
        _closure_markdown(closure),
        encoding="utf-8",
    )
    _write_json(checkpoint_dir / "core_architecture_checkpoint_manifest.json", manifest)
    _write_json(checkpoint_dir / "core_closed_area_inventory.json", closed_inventory)
    _write_json(checkpoint_dir / "core_unresolved_gap_inventory.json", unresolved)
    _write_json(checkpoint_dir / "core_gap_dependency_graph.json", dependency_graph)
    _write_json(checkpoint_dir / "core_next_gap_decision.json", next_gap)
    (checkpoint_dir / "core_architecture_checkpoint.md").write_text(
        _checkpoint_markdown(manifest, next_gap),
        encoding="utf-8",
    )

    return {
        "closure": closure,
        "checkpoint_manifest": manifest,
        "closed_inventory": closed_inventory,
        "unresolved_gap_inventory": unresolved,
        "dependency_graph": dependency_graph,
        "next_gap_decision": next_gap,
        "program_artifact_dir": str(program_artifact_dir),
        "checkpoint_dir": str(checkpoint_dir),
    }


def _closure_artifact(
    *,
    p1: Mapping[str, Any],
    p2: Mapping[str, Any],
    p3: Mapping[str, Any],
    forensic: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "schema_version": "adaptive_route_prediction_evidence_closure.v1",
        "program_identity": {
            "program": "ADAPTIVE_ROUTE_PREDICTION_PROGRAM",
            "program_state": "PAUSED_PENDING_NEW_EVIDENCE",
            "closure_status": "CLOSED",
        },
        "scientific_record": {
            "P1": {
                "status": "P1_CANDIDATE_SIGNAL_OBSERVED",
                "result": "candidate_pre_admission_signals_observed",
                "artifact_path": _rel(P1_SUMMARY),
                "experiment_id": p1.get("experiment_id"),
            },
            "P2": {
                "status": "P2_ASSOCIATION_VALID",
                "evidence_level": p2.get("current_evidence_level"),
                "result": p2.get("primary_scientific_conclusion"),
                "supported_routes": ["identity_governance", "object_tracking"],
                "observed_value_level": "L3_INTERNAL_USEFUL",
                "decisive_final_outcome_value": "NO",
                "artifact_path": _rel(P2_SUMMARY),
                "experiment_id": p2.get("experiment_id"),
            },
            "P3_v1": {
                "status": "P3_PREDICTOR_FAILED",
                "evidence_level": p3.get("current_evidence_level"),
                "result": p3.get("primary_scientific_conclusion"),
                "held_out_task_count": p3.get("held_out_task_count"),
                "measurable_marginal_route_rows": p3.get("measurable_evaluation_rows"),
                "unique_useful_events": p3.get("held_out_unique_useful_events"),
                "positive_rate": p3.get("held_out_positive_rate"),
                "precision": p3.get("metrics", {}).get("precision"),
                "recall": p3.get("metrics", {}).get("recall"),
                "specificity": p3.get("metrics", {}).get("specificity"),
                "balanced_accuracy": p3.get("metrics", {}).get("balanced_accuracy"),
                "average_precision": p3.get("metrics", {}).get("average_precision"),
                "roc_auc": p3.get("metrics", {}).get("roc_auc"),
                "artifact_path": _rel(P3_SUMMARY),
                "experiment_id": p3.get("experiment_id"),
            },
            "P3_failure_forensic": {
                "primary_forensic_conclusion": forensic.get("primary_forensic_conclusion"),
                "primary_failure_cause": forensic.get("primary_failure_cause"),
                "within_route_discrimination": forensic.get("within_route_discrimination", {}).get("overall"),
                "non_route_feature_redundancy": forensic.get("failure_decomposition", {}).get("NON_ROUTE_FEATURE_REDUNDANCY"),
                "feature_semantic_insufficiency": forensic.get("failure_decomposition", {}).get("FEATURE_SEMANTIC_INSUFFICIENCY"),
                "artifact_path": _rel(P3_FORENSIC_SUMMARY),
            },
        },
        "candidate_v1_state": {
            "state": "REJECTED_FOR_PREDICTIVE_USE",
            "reason": "FAILED_OUT_OF_SAMPLE+NO_INCREMENTAL_CONDITIONAL_INFORMATION_BEYOND_ROUTE_IDENTITY",
            "frozen_contract_preserved": True,
            "signal_contract_id": p3.get("signal_contract_id"),
            "signal_contract_fingerprint": p3.get("signal_contract_fingerprint"),
            "frozen_threshold": p3.get("frozen_threshold"),
            "candidate_v1_mutated": False,
        },
        "consumed_validation_evidence": {
            "state": "CONSUMED_P3_V1_VALIDATION_EVIDENCE",
            "task_ids": CONSUMED_VALIDATION_TASKS,
            "fresh_validation_for_candidate_v2": False,
        },
        "negative_evidence_preservation": {
            "negative_evidence_preserved": True,
            "preserved_items": [
                "P3 held-out failure",
                "false-positive analysis",
                "baseline equivalence",
                "identical ranking result",
                "within-route discrimination failure",
                "feature redundancy evidence",
                "score compression evidence",
                "feature semantic insufficiency",
                "consumed held-out set identity",
            ],
        },
        "p4_state": "BLOCKED",
        "p5_state": "BLOCKED",
        "reopening_requirements": {
            "reopening_requires_new_information": True,
            "not_sufficient_reopening_conditions": [
                "more_compute",
                "threshold_change",
                "different_classifier",
                "more_repeats_only",
                "route_identity_association_only",
            ],
            "sufficient_new_information_examples": [
                "new_pre_admission_route_task_fit_instrumentation",
                "broader_development_evidence_across_multiple_task_contexts",
                "new_within_route_variation_for_conditional_discrimination",
                "new_pre_admission_state_variable_with_defensible_predictive_relevance",
            ],
        },
        "future_hypothesis_state": {
            "route_task_fit": "FUTURE_RESEARCH_HYPOTHESIS",
            "not_established_concept": True,
            "not_runtime_variable": True,
            "not_production_metric": True,
            "not_policy_input": True,
            "candidate_v2_created": False,
        },
        "authority_state": {
            "budget_authority": "RuntimeBudgetEnforcer",
            "prediction_authority": "OBSERVATION_ONLY",
            "behavioral_authority": "NONE",
            "cognitive_consumer_count": 0,
            "adaptive_policy_patch_allowed": False,
            "production_route_order_changed": "NO",
            "production_route_budget_changed": "NO",
            "production_behavior_changed": "NO",
            "architectural_repair_applied_this_turn": False,
        },
        "provenance_graph": _provenance_graph(p1, p2, p3, forensic),
    }
    payload["closure_fingerprint"] = _stable_id("adaptive_route_prediction_closure", payload)
    return payload


def _provenance_graph(
    p1: Mapping[str, Any],
    p2: Mapping[str, Any],
    p3: Mapping[str, Any],
    forensic: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        _node("P1 Signal Discovery", p1.get("experiment_id"), _rel(P1_SUMMARY), "candidate signals observed", "P1_CANDIDATE_SIGNAL_OBSERVED"),
        _node("Pre-Admission Instrumentation", p1.get("experiment_id"), _rel(P1_SUMMARY), "pre-admission snapshots available", "OPERATIONALLY_OBSERVED"),
        _node("Controlled Replication", p1.get("experiment_id"), _rel(P1_SUMMARY), p1.get("primary_scientific_conclusion"), p1.get("current_evidence_level")),
        _node("Route/Position Deconfounding", p2.get("experiment_id"), _rel(P2_SUMMARY), "route identity separated from route position", p2.get("current_evidence_level")),
        _node("P2 Association", p2.get("experiment_id"), _rel(P2_SUMMARY), p2.get("primary_scientific_conclusion"), "P2_ASSOCIATION_VALID"),
        _node("Frozen Candidate V1", p3.get("signal_contract_id"), _rel(P3_SUMMARY), "frozen observation-only candidate", "FROZEN_CONTRACT"),
        _node("P3 Held-Out Validation", p3.get("experiment_id"), _rel(P3_SUMMARY), p3.get("primary_scientific_conclusion"), p3.get("current_evidence_level")),
        _node("P3 Failure", p3.get("experiment_id"), _rel(P3_SUMMARY), p3.get("failure_mode"), "P3_PREDICTOR_FAILED"),
        _node("Failure Forensic", forensic.get("system_fingerprint"), _rel(P3_FORENSIC_SUMMARY), forensic.get("primary_forensic_conclusion"), "FORENSIC_COMPLETE"),
        _node("Program Pause", "ADAPTIVE_ROUTE_PREDICTION_PROGRAM", "runtime/artifacts/adaptive_route_prediction_program/adaptive_route_prediction_evidence_closure.json", "paused pending new evidence", "PAUSED_PENDING_NEW_EVIDENCE"),
    ]


def _closed_area_inventory() -> dict[str, Any]:
    areas = [
        ("runtime_topology", "OPERATIONALLY_OBSERVED", "runtime topology/reachability artifacts and tests present"),
        ("cognitive_authority", "OPERATIONALLY_OBSERVED", "authority tests and governed blocker states present"),
        ("memory_learning_reuse", "REPRODUCIBLY_SUPPORTED", "reuse/provenance phases completed without production authority escalation"),
        ("knowledge_evidence_identity_raw_capture", "OPERATIONALLY_OBSERVED", "raw validation identity and lifecycle tests present"),
        ("claim_evidence_binding", "RUNTIME_REACHABLE", "canonical report/evidence binding code and tests present"),
        ("task_epistemic_mapping", "RUNTIME_REACHABLE", "epistemic mapping/calibration modules and tests present"),
        ("source_independence", "OPERATIONALLY_OBSERVED", "truth independence tests present"),
        ("route_budget_science", "REPRODUCIBLY_SUPPORTED", "P1/P2/P3 artifacts and closure preserve positive and negative evidence"),
        ("route_contribution_telemetry", "OPERATIONALLY_OBSERVED", "route contribution manifests and lineage artifacts present"),
        ("human_report_accounting", "REPRODUCIBLY_SUPPORTED", "human report projection accounting artifacts and tests present"),
    ]
    return {
        "schema_version": "core_closed_area_inventory.v1",
        "closed_area_count": len(areas),
        "areas": [
            {
                "area": name,
                "current_evidence_level": level,
                "status": "NO_ACTION_REQUIRED",
                "basis": basis,
            }
            for name, level, basis in areas
        ],
    }


def _unresolved_gap_inventory() -> dict[str, Any]:
    gaps = [
        {
            "gap_id": SELECTED_GAP_ID,
            "title": "Governed evidence acceptance contract completion",
            "architectural_intent": "Convert captured raw validation results into accepted/insufficient/rejected evidence through governed semantics before capability graduation or trust.",
            "current_implementation": "Validation evaluator and report surfaces exist, but architecture still reports governed evidence acceptance as the promotion bottleneck.",
            "runtime_reachability": "RUNTIME_REACHABLE",
            "actual_consumer": "capability graduation and executable-intelligence reporting",
            "actual_authority": "evidence acceptance gate",
            "current_evidence_level": "RUNTIME_REACHABLE",
            "missing_contract": "study-grade evidence acceptance semantics for governed validation success",
            "missing_lifecycle_edge": "raw validation result -> governed accepted evidence -> capability/truth promotion",
            "production_consequence": "capabilities can remain blocked at final validation rather than graduating into trusted use",
            "study_readiness_consequence": "blocks mature study claims about executable intelligence and learned-object promotion",
            "classification": "CONFIRMED_ARCHITECTURAL_GAP",
            "repair_decision": "DESIGN_AND_REPAIR_BEFORE_STUDY",
            "core_criticality": "BLOCKING",
            "authority_risk": "HIGH",
            "integration_risk": "HIGH",
            "study_blocking": "YES",
            "dependency_order": "EARLY",
        },
        {
            "gap_id": "integrated_capability_qualification_freeze",
            "title": "Integrated capability qualification and baseline freeze",
            "architectural_intent": "Freeze core behavior only after governed evidence acceptance and capability qualification agree.",
            "current_implementation": "Qualification surfaces exist, but they depend on accepted evidence semantics.",
            "runtime_reachability": "RUNTIME_REACHABLE",
            "actual_consumer": "final reporting and capability architecture",
            "actual_authority": "baseline/study readiness",
            "current_evidence_level": "ARCHITECTURALLY_PRESENT",
            "missing_contract": "qualification freeze contract after acceptance",
            "missing_lifecycle_edge": "accepted evidence -> qualification -> baseline freeze",
            "production_consequence": "baseline freeze remains premature",
            "study_readiness_consequence": "study cannot claim frozen mature architecture",
            "classification": "INTEGRATION_GAP",
            "repair_decision": "DESIGN_AND_REPAIR_BEFORE_STUDY",
            "core_criticality": "HIGH",
            "authority_risk": "MEDIUM",
            "integration_risk": "HIGH",
            "study_blocking": "YES",
            "dependency_order": "MIDDLE",
        },
        {
            "gap_id": "execution_mode_semantic_differentiation",
            "title": "Execution-mode semantic differentiation",
            "architectural_intent": "Separate diagnostic, validation, sandbox, adaptive, and production semantics in final study evidence.",
            "current_implementation": "Mode fields exist across artifacts, but final cross-mode semantics still need checkpointing.",
            "runtime_reachability": "RUNTIME_REACHABLE",
            "actual_consumer": "final report renderer and validation surfaces",
            "actual_authority": "reporting/interpretation only",
            "current_evidence_level": "ARCHITECTURALLY_PRESENT",
            "missing_contract": "final study mode taxonomy",
            "missing_lifecycle_edge": "mode-specific evidence -> study projection",
            "production_consequence": "report interpretation ambiguity",
            "study_readiness_consequence": "may confuse diagnostic evidence with production evidence",
            "classification": "ONTOLOGY_AMBIGUITY",
            "repair_decision": "FORENSIC_FIRST",
            "core_criticality": "MEDIUM",
            "authority_risk": "MEDIUM",
            "integration_risk": "MEDIUM",
            "study_blocking": "NO",
            "dependency_order": "LATE",
        },
        {
            "gap_id": "adaptive_route_prediction_v2",
            "title": "Adaptive route prediction candidate_v2",
            "architectural_intent": "Optional optimization: predict useful route admission before execution.",
            "current_implementation": "candidate_v1 rejected; program paused pending new evidence.",
            "runtime_reachability": "OPERATIONALLY_OBSERVED",
            "actual_consumer": "none",
            "actual_authority": "NONE",
            "current_evidence_level": "REPRODUCIBLY_SUPPORTED_NEGATIVE_RESULT",
            "missing_contract": "new signal instrumentation only if research is reopened",
            "missing_lifecycle_edge": "none for core baseline with fixed governed route budgeting",
            "production_consequence": "fixed governed route budgeting remains valid",
            "study_readiness_consequence": "not a core blocker",
            "classification": "FUTURE_CAPABILITY_NOT_REQUIRED_FOR_CORE",
            "repair_decision": "DEFER_POST_BASELINE",
            "core_criticality": "LOW",
            "authority_risk": "LOW",
            "integration_risk": "LOW",
            "study_blocking": "NO",
            "dependency_order": "LATE",
        },
    ]
    return {
        "schema_version": "core_unresolved_gap_inventory.v1",
        "unresolved_core_gap_count": len(gaps),
        "study_blocking_gap_count": sum(1 for gap in gaps if gap["study_blocking"] == "YES"),
        "gaps": gaps,
    }


def _dependency_graph(unresolved: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "core_gap_dependency_graph.v1",
        "edges": [
            {
                "from": SELECTED_GAP_ID,
                "to": "integrated_capability_qualification_freeze",
                "reason": "qualification freeze depends on accepted evidence semantics",
            },
            {
                "from": "integrated_capability_qualification_freeze",
                "to": "execution_mode_semantic_differentiation",
                "reason": "study reporting follows qualification and baseline semantics",
            },
        ],
        "excluded_from_core_dependency_path": ["adaptive_route_prediction_v2"],
        "earliest_unresolved_prerequisite": SELECTED_GAP_ID,
    }


def _next_gap_decision(unresolved: Mapping[str, Any]) -> dict[str, Any]:
    selected = next(gap for gap in unresolved["gaps"] if gap["gap_id"] == SELECTED_GAP_ID)
    return {
        "schema_version": "core_next_gap_decision.v1",
        "selected_next_core_gap": selected["gap_id"],
        "title": selected["title"],
        "classification": selected["classification"],
        "selected_gap_evidence_level": selected["current_evidence_level"],
        "selected_gap_study_blocking": selected["study_blocking"],
        "selected_gap_required_action": selected["repair_decision"],
        "why_this_gap_precedes_others": "It is the earliest authority-bearing prerequisite for capability promotion, qualification, and study-grade baseline freeze.",
        "architectural_repair_applied_this_turn": False,
        "required_next_action_type": "DESIGN_AND_REPAIR_BEFORE_STUDY",
    }


def _checkpoint_manifest(
    *,
    checkpoint_dir: Path,
    closure: Mapping[str, Any],
    closed_inventory: Mapping[str, Any],
    unresolved: Mapping[str, Any],
    dependency_graph: Mapping[str, Any],
    next_gap: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "schema_version": "core_architecture_checkpoint_manifest.v1",
        "checkpoint_status": "COMPLETE_READ_ONLY_ARCHITECTURAL_FINDING",
        "checkpoint_dir": str(checkpoint_dir),
        "closure_fingerprint": closure["closure_fingerprint"],
        "closed_core_area_count": closed_inventory["closed_area_count"],
        "unresolved_core_gap_count": unresolved["unresolved_core_gap_count"],
        "study_blocking_gap_count": unresolved["study_blocking_gap_count"],
        "selected_next_core_gap": next_gap["selected_next_core_gap"],
        "selected_gap_classification": next_gap["classification"],
        "selected_gap_evidence_level": next_gap["selected_gap_evidence_level"],
        "selected_gap_required_action": next_gap["selected_gap_required_action"],
        "authority": "READ_ONLY_ARCHITECTURAL_FORENSIC",
        "architectural_repair_applied_this_turn": False,
        "git_revision": _git(["rev-parse", "HEAD"]),
        "dirty_state_summary": _git(["status", "--short"]),
        "python_runtime_version": platform.python_version(),
        "dependency_graph_fingerprint": _stable_id("core_gap_dependency_graph", dependency_graph),
    }
    payload["checkpoint_fingerprint"] = _stable_id("core_architecture_checkpoint", payload)
    return payload


def _closure_markdown(closure: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Adaptive Route Prediction Evidence Closure",
            "",
            "## Observed",
            "- Candidate pre-admission route signals were observed.",
            "- Route identity association replicated under deconfounding.",
            "- P3 held-out validation failed out of sample.",
            "",
            "## Inferred",
            "- Route identity association does not establish conditional predictive value.",
            "- Candidate v1 is rejected for predictive use.",
            "",
            "## Hypothesized",
            "- RouteTaskFit remains a future research hypothesis only.",
            "",
            "## Not Proven",
            "- Selective prediction of when a route will be useful.",
            "- Candidate v2 validity.",
            "- P4 controlled policy benefit.",
            "",
            f"Program state: `{closure['program_identity']['program_state']}`",
        ]
    )


def _checkpoint_markdown(manifest: Mapping[str, Any], next_gap: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Core Architecture Checkpoint",
            "",
            f"Status: `{manifest['checkpoint_status']}`",
            f"Selected next core gap: `{next_gap['selected_next_core_gap']}`",
            f"Classification: `{next_gap['classification']}`",
            f"Evidence level: `{next_gap['selected_gap_evidence_level']}`",
            f"Required action: `{next_gap['selected_gap_required_action']}`",
            "",
            next_gap["why_this_gap_precedes_others"],
            "",
        ]
    )


def _node(name: str, experiment_id: Any, path: str, claim: Any, level: Any) -> dict[str, Any]:
    return {
        "node": name,
        "experiment_id": experiment_id or "NOT_AVAILABLE",
        "artifact_path": path,
        "claim_result": claim or "NOT_AVAILABLE",
        "evidence_level": level or "NOT_AVAILABLE",
    }


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


def _stable_id(prefix: str, payload: Any) -> str:
    body = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=True)
    return f"{prefix}_{hashlib.sha256(body.encode('utf-8')).hexdigest()[:16]}"


def _git(args: list[str]) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "UNKNOWN"
    return completed.stdout.strip() or completed.stderr.strip() or "UNKNOWN"
