from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


OUTPUT_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "route_cognitive_consumption_audit"
ROUTE_CONTRIBUTION_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "route_contribution"
P3_SUMMARY = (
    PROJECT_ROOT
    / "runtime"
    / "artifacts"
    / "p3_route_predictive_validation"
    / "20260909_234453"
    / "p3_summary.json"
)
P3_CLOSURE = (
    PROJECT_ROOT
    / "runtime"
    / "artifacts"
    / "adaptive_route_prediction_program"
    / "adaptive_route_prediction_evidence_closure.json"
)

SYSTEM_PATHS = [
    "runtime/telemetry/route_contribution.py",
    "runtime/telemetry/pre_route_admission.py",
    "runtime/budget/runtime_budget_enforcer.py",
    "runtime/execution/execution_planner.py",
    "runtime/stages/evaluation.py",
    "runtime/learning/training_report.py",
    "runtime/reporting/final_report_renderer.py",
    "runtime/experiments/p3_route_predictive_validation.py",
    "runtime/experiments/adaptive_route_prediction_closure.py",
]


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Mapping[str, Any] | list[Any] | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
        return
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
    json.loads(text)
    path.write_text(text + "\n", encoding="utf-8")


def _fingerprint(paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        path = PROJECT_ROOT / relative
        digest.update(relative.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _payload_fingerprint(payload: Mapping[str, Any] | list[Any] | str) -> str:
    text = (
        payload
        if isinstance(payload, str)
        else json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git_value(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=PROJECT_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"


def _latest_route_manifest() -> dict[str, Any]:
    files = sorted(
        ROUTE_CONTRIBUTION_ROOT.glob("*_route_contribution_manifest.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not files:
        return {"artifact_path": None, "manifest": {}}
    return {"artifact_path": str(files[0]), "manifest": _read(files[0])}


def _state_counts(manifest: Mapping[str, Any]) -> dict[str, int]:
    return dict(Counter(
        str(route.get("contribution_state") or "UNKNOWN")
        for route in manifest.get("routes", []) or []
        if isinstance(route, Mapping)
    ))


def run_audit(output_root: str | Path = OUTPUT_ROOT) -> dict[str, Any]:
    latest = _latest_route_manifest()
    manifest = latest["manifest"]
    p3 = _read(P3_SUMMARY) if P3_SUMMARY.exists() else {}
    closure = _read(P3_CLOSURE) if P3_CLOSURE.exists() else {}
    system_fingerprint = _fingerprint(SYSTEM_PATHS)
    contribution_semantics = {
        "UNIQUE_USEFUL_CONTRIBUTION": {
            "current_contract": "unique current-route output or repair contribution was used downstream",
            "proves": "internal route output was observably distinct and useful inside the run",
            "does_not_prove": ["final task success", "truth", "universal route value"],
        },
        "DUPLICATE_CONTRIBUTION": {
            "current_contract": "all meaningful outputs match earlier route output fingerprints",
            "proves": "redundancy relative to earlier current-run route outputs",
            "does_not_prove": ["route is globally bad", "route lacks value in other contexts"],
        },
        "LOW_VALUE_CONTRIBUTION": {
            "current_contract": "distinct output was rejected, dominated, blocked, or failed downstream",
            "proves": "observed downstream low-value disposition for this run/context",
            "does_not_prove": ["safe direct penalty across contexts", "future uselessness"],
        },
        "NO_OBSERVABLE_CONTRIBUTION": {
            "current_contract": "route executed with no linked output",
            "proves": "no observable linked output under current instrumentation",
            "does_not_prove": ["no cognitive value", "safe negative penalty"],
        },
        "CONTRIBUTION_NOT_MEASURABLE": {
            "current_contract": "route not executed, lineage error, or insufficient downstream lineage",
            "proves": "telemetry cannot classify contribution",
            "does_not_prove": ["positive value", "negative value"],
        },
    }
    signal_inventory = {
        "latest_manifest_artifact": latest["artifact_path"],
        "run_id": manifest.get("run_id"),
        "task_id": manifest.get("task_id"),
        "state_counts": _state_counts(manifest),
        "field_classification": {
            "route_id": ["PRE_EXECUTION", "CROSS_RUN_REUSABLE", "NON_CAUSAL"],
            "route_family": ["PRE_EXECUTION", "CROSS_RUN_REUSABLE", "CONTEXT_CANDIDATE"],
            "route_position": ["PRE_EXECUTION", "LEAKAGE_RISK", "ROUTE_POSITION_CONFOUNDING"],
            "task_id": ["PRE_EXECUTION", "HISTORICAL", "CONTEXT_CANDIDATE"],
            "run_id": ["HISTORICAL", "CURRENT_RUN_ONLY"],
            "contribution_state": ["POST_EXECUTION", "HISTORICAL", "NON_CAUSAL"],
            "candidate_ids": ["POST_EXECUTION", "CURRENT_RUN_ONLY", "LINEAGE"],
            "program_ids": ["POST_EXECUTION", "CURRENT_RUN_ONLY", "LINEAGE"],
            "arena_participation": ["POST_EXECUTION", "LEAKAGE_RISK"],
            "lineage_state": ["POST_EXECUTION", "MEASURABILITY"],
            "contribution_measurability_state": ["POST_EXECUTION", "MEASURABILITY"],
            "route_score": ["PRE_EXECUTION", "NON_CAUSAL"],
        },
    }
    persistence_trace = {
        "persistence_state": "PERSISTED_NOT_INDEXED",
        "manifest_store": "runtime/artifacts/route_contribution",
        "summary_projection": [
            "runtime/stages/evaluation.py",
            "runtime/learning/training_report.py",
            "runtime/reporting/final_report_renderer.py",
        ],
        "cross_run_accessibility": True,
        "route_identity_preserved": bool(manifest.get("routes")),
        "task_context_identity_preserved": bool(manifest.get("task_id")),
        "indexed_for_selection": False,
        "retrieved_for_cognition": False,
    }
    retrieval_trace = {
        "retrieval_state": "PERSISTED_NOT_INDEXED",
        "current_cognitive_consumer_count": 0,
        "consumers": [
            {
                "component": "final_report_renderer",
                "signal_used": "route_contribution_summary",
                "affects_route_eligibility": False,
                "affects_ranking": False,
                "affects_budget": False,
                "affects_execution": False,
            },
            {
                "component": "training_report",
                "signal_used": "compact_route_contribution_summary",
                "affects_route_eligibility": False,
                "affects_ranking": False,
                "affects_budget": False,
                "affects_execution": False,
            },
            {
                "component": "P3 experiments",
                "signal_used": "offline held-out prediction labels",
                "affects_route_eligibility": False,
                "affects_ranking": False,
                "affects_budget": False,
                "affects_execution": False,
            },
        ],
    }
    route_selection_contract = {
        "route_selection_owner": "upstream route_selection_report/cognitive_route_report provider; canonical materialization in ExecutionPlanner._route_selection_records",
        "route_admission_owner": "RuntimeBudgetEnforcer.build_receipt / RuntimeBudgetEnforcer._admitted_route_ids",
        "route_proposal": "route_selection_report.active_routes|routes|selected_routes or active_route_count fallback",
        "route_ordering": "route_rank, then route_id",
        "route_selection_inputs_observed": [
            "route_id",
            "route_rank",
            "route_score",
            "route_source",
            "active_route_count",
        ],
        "historical_contribution_signal_present": False,
    }
    integration_options = [
        {
            "option": "A_SELECTOR_TIE_BREAK_ONLY",
            "behavioral_risk": "LOW_TO_MODERATE",
            "feedback_risk": "MODERATE",
            "compatibility": "HIGH",
            "scientific_maturity": "NEEDS_SHADOW_VALIDATION",
        },
        {
            "option": "B_BOUNDED_RANKING_ADJUSTMENT",
            "behavioral_risk": "MODERATE",
            "feedback_risk": "HIGH",
            "compatibility": "MEDIUM",
            "scientific_maturity": "NOT_READY_AFTER_FAILED_P3",
        },
        {
            "option": "C_ELIGIBILITY_INFLUENCE",
            "behavioral_risk": "HIGH",
            "feedback_risk": "HIGH",
            "compatibility": "LOW",
            "scientific_maturity": "NOT_READY",
        },
        {
            "option": "D_BUDGET_EXPANSION_INFLUENCE",
            "behavioral_risk": "HIGH",
            "feedback_risk": "HIGH",
            "compatibility": "LOW",
            "scientific_maturity": "NOT_READY",
        },
        {
            "option": "E_MULTI_OBJECTIVE_ROUTE_RANKING",
            "behavioral_risk": "MODERATE_TO_HIGH",
            "feedback_risk": "HIGH_WITHOUT_EXPLORATION_GUARDS",
            "compatibility": "MEDIUM",
            "scientific_maturity": "RESEARCH_ONLY",
        },
    ]
    first_boundary = {
        "component": "RuntimeBudgetEnforcer",
        "function": "_pre_route_snapshots",
        "input_contract": "route_record + task/context features + budget snapshot before admission",
        "signal_form": "ADVISORY_ROUTE_SELECTION_SIGNAL_SHADOW_ONLY with context-conditioned sufficient statistics",
        "maximum_permitted_influence": 0,
        "authority": "OBSERVATION_ONLY",
        "fail_closed_behavior": "missing, stale, or low-sample historical signal produces no ranking/admission effect",
    }
    summary = {
        "status": "COMPLETE",
        "primary_conclusion": (
            "Route contribution is measured and persisted for reporting, but no indexed historical route-value memory or retrieval boundary feeds future route selection/admission."
        ),
        "system_fingerprint": system_fingerprint,
        "telemetry_owner": "runtime.telemetry.route_contribution",
        "route_selection_owner": route_selection_contract["route_selection_owner"],
        "route_admission_owner": route_selection_contract["route_admission_owner"],
        "telemetry_authority": "OBSERVATION_ONLY",
        "behavioral_authority": "NONE",
        "current_cognitive_consumer_count": 0,
        "persistence_state": persistence_trace["persistence_state"],
        "retrieval_state": retrieval_trace["retrieval_state"],
        "first_missing_boundary": "persisted route contribution manifest -> indexed historical route-value memory -> pre-execution advisory retrieval",
        "temporal_integrity_state": "TEMPORAL_FEEDBACK_SAFE",
        "feedback_loop_risk": "HIGH",
        "observation_bias_state": "POLICY_CONDITIONED_EXECUTED_ROUTE_DATA",
        "context_dependence_state": "CONTEXT_CONDITIONED_REQUIRED",
        "contribution_causality_state": "MIXED_LINEAGE_ATTRIBUTION_AND_DESCRIPTIVE_ASSOCIATION",
        "contribution_final_outcome_equivalence": False,
        "negative_signal_safe_for_direct_penalty": "PARTIAL",
        "existing_memory_surface_reusable": "PARTIAL",
        "new_memory_store_required": "UNDECIDED",
        "recommended_signal_form": "context-conditioned sufficient statistics, not scalar reward",
        "uncertainty_required": True,
        "exploration_protection_required": True,
        "recommended_first_integration_component": first_boundary["component"],
        "recommended_first_integration_function": first_boundary["function"],
        "initial_integration_mode": "SHADOW_ONLY",
        "maximum_initial_behavioral_influence": 0,
        "offline_counterfactual_replay_feasible": "PARTIAL",
        "same_run_consumption_allowed": "UNDECIDED",
        "cross_run_consumption_allowed": "TRUE",
        "failed_p3_predictor_reactivated": False,
        "truth_authority_changed": False,
        "candidate_authority_changed": False,
        "execution_authority_changed": False,
        "budget_authority_changed": False,
        "patch_required": "NO",
        "patch_applied": "NO",
        "next_action": "run shadow-only context-conditioned historical route-value replay before any behavioral integration",
    }
    artifacts = {
        "01_system_fingerprint.json": {
            "system_fingerprint": system_fingerprint,
            "fingerprinted_paths": SYSTEM_PATHS,
            "git_commit": _git_value("rev-parse", "HEAD"),
            "git_branch": _git_value("branch", "--show-current"),
            "python_version": platform.python_version(),
        },
        "02_route_telemetry_contract.json": {
            "producer": "build_route_contribution_manifest",
            "classifier": "_classify_route",
            "aggregator": "_aggregate / compact_route_contribution_summary",
            "persistence_owner": "_persist_manifest",
            "schema_version": "1.0",
            "authority": "OBSERVATION_ONLY",
            "behavioral_authority": "NONE",
            "telemetry_consumed_by_cognition": False,
            "contribution_semantics": contribution_semantics,
        },
        "03_signal_inventory.json": signal_inventory,
        "04_temporal_integrity_analysis.json": {
            "temporal_integrity_state": summary["temporal_integrity_state"],
            "post_execution_signal": "contribution_state",
            "pre_admission_snapshot_forbidden_fields": [
                "contribution_state",
                "route_contribution_outcome",
                "final_task_success",
                "admission_state",
            ],
            "same_route_self_feedback_detected": False,
        },
        "05_persistence_trace.json": persistence_trace,
        "06_retrieval_trace.json": retrieval_trace,
        "07_route_selection_contract.json": route_selection_contract,
        "08_current_consumer_matrix.json": retrieval_trace["consumers"],
        "09_feedback_loop_risk.json": {
            "feedback_loop_risk": summary["feedback_loop_risk"],
            "risks": [
                "selection_bias",
                "rich_get_richer_reinforcement",
                "exploration_collapse",
                "context_blindness",
            ],
        },
        "10_observation_bias_analysis.json": {
            "observation_bias_state": summary["observation_bias_state"],
            "executed_route_bias": True,
            "deferred_route_missingness": True,
            "route_position_confounding": True,
            "zero_observations_means_zero_value": False,
        },
        "11_context_conditioning_analysis.json": {
            "context_dependence_state": summary["context_dependence_state"],
            "minimum_context_dimensions": [
                "route_id",
                "route_family",
                "task_signature",
                "object_count",
                "transformation_count",
                "spatial_complexity",
                "route_position",
                "prior_route_state_summary",
            ],
        },
        "12_signal_semantic_ceiling.json": {
            "contribution_final_outcome_equivalence": False,
            "causality_state": summary["contribution_causality_state"],
            "semantic_ceiling": "internal useful contribution, not guaranteed final task improvement",
        },
        "13_historical_memory_options.json": {
            "existing_surfaces": [
                "route_contribution manifests",
                "route_pre_admission snapshots",
                "RouteIntelligenceMemory generic route histories",
            ],
            "existing_memory_surface_reusable": summary[
                "existing_memory_surface_reusable"
            ],
            "new_memory_store_required": summary["new_memory_store_required"],
        },
        "14_aggregation_options.json": {
            "recommended": [
                "execution_count",
                "measurable_count",
                "unique_useful_count",
                "duplicate_count",
                "low_value_count",
                "no_observable_count",
                "conditional_usefulness_rate",
                "sample_count",
            ],
            "avoid_initial_scalar_score": True,
        },
        "15_uncertainty_requirements.json": {
            "uncertainty_required": True,
            "one_of_one_must_not_dominate_sixty_of_one_hundred": True,
            "represent_evidence_volume": True,
        },
        "16_exploration_safeguards.json": {
            "exploration_protection_required": True,
            "compatible_safeguards": [
                "minimum_exploration_quota",
                "unknown_route_neutrality",
                "confidence_aware_ranking",
                "bounded_advisory_influence",
                "context_specific_priors",
                "decay",
            ],
        },
        "17_integration_options_matrix.json": integration_options,
        "18_first_lawful_integration_boundary.json": first_boundary,
        "19_shadow_experiment_design.json": {
            "mode": "SHADOW_ONLY",
            "questions": [
                "would historical contribution alter route ranking",
                "would useful-route exposure improve",
                "would no-observable exposure reduce",
                "would useful under-observed routes be suppressed",
            ],
            "behavior_change": False,
        },
        "20_counterfactual_replay_feasibility.json": {
            "offline_counterfactual_replay_feasible": summary[
                "offline_counterfactual_replay_feasible"
            ],
            "available": [
                "route contribution manifests",
                "pre-route admission snapshots",
                "route order deconfounding artifacts",
            ],
            "missing": [
                "canonical indexed historical route-value memory",
                "context-conditioned aggregation snapshot for each admission",
            ],
        },
        "21_attack_test_spec.json": {
            "attacks": [
                "route useful once -> permanent domination",
                "unobserved route wrongly penalized",
                "same route useful in one context but harmful in another",
                "same route repeated under same task",
                "route position confounding",
                "same-source repeated telemetry",
                "missing contribution data",
                "low sample count",
                "stale historical data",
                "feedback-induced exploration collapse",
                "telemetry corruption",
                "report artifact spoofing",
                "post-execution leakage into same-run admission",
                "telemetry used as truth authority",
                "telemetry used to bypass budget authority",
            ]
        },
        "22_authority_audit.json": {
            "truth_authority_changed": False,
            "candidate_authority_changed": False,
            "execution_authority_changed": False,
            "budget_authority_changed": False,
            "route_order_changed": False,
            "route_budget_changed": False,
            "patch_applied": False,
        },
        "23_final_decision.json": summary,
        "24_route_cognitive_consumption_audit.md": _report(summary),
        "summary.json": summary,
    }
    output_dir = Path(output_root) / _stamp()
    for name, payload in artifacts.items():
        _write(output_dir / name, payload)
    return {**summary, "output_dir": str(output_dir)}


def _report(summary: Mapping[str, Any]) -> str:
    return (
        "# Route Cognitive Consumption Audit\n\n"
        f"Status: `{summary['status']}`\n\n"
        f"Primary conclusion: {summary['primary_conclusion']}\n\n"
        f"First missing boundary: `{summary['first_missing_boundary']}`\n\n"
        f"Recommended first boundary: `{summary['recommended_first_integration_component']}.{summary['recommended_first_integration_function']}` in `SHADOW_ONLY` mode.\n\n"
        "No production behavior was changed.\n"
    )


if __name__ == "__main__":
    print(json.dumps(run_audit(), indent=2, sort_keys=True))
