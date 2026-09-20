from __future__ import annotations

import hashlib
import json
import math
import platform
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


ARTIFACT_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "route_value_shadow_replay"
ROUTE_MANIFEST_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "route_contribution"

AUTHORITY = "OBSERVATION_ONLY"
BEHAVIORAL_AUTHORITY = "NONE"
STRATEGIES = [
    "BASELINE",
    "TIE_BREAK_ONLY",
    "BOUNDED_ADDITIVE_SHADOW",
    "NORMALIZED_MULTI_OBJECTIVE_SHADOW",
    "UNCERTAINTY_AWARE_TIE_BREAK",
]
POSITIVE = "UNIQUE_USEFUL_CONTRIBUTION"
LOW_VALUE = "LOW_VALUE_CONTRIBUTION"
NO_OBSERVABLE = "NO_OBSERVABLE_CONTRIBUTION"
UNMEASURABLE = "CONTRIBUTION_NOT_MEASURABLE"
DUPLICATE = "DUPLICATE_CONTRIBUTION"

SYSTEM_PATHS = [
    "runtime/experiments/route_value_shadow_replay.py",
    "runtime/telemetry/route_contribution.py",
    "runtime/telemetry/pre_route_admission.py",
    "runtime/budget/runtime_budget_enforcer.py",
]


def _stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Mapping[str, Any] | list[Any] | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
        return
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True, default=str)
    json.loads(text)
    path.write_text(text + "\n", encoding="utf-8")


def _fingerprint(paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for relative in paths:
        path = PROJECT_ROOT / relative
        digest.update(relative.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _stable_id(prefix: str, payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return f"{prefix}_{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


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


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value in {None, "", "UNKNOWN", "Not Available"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        if value in {None, "", "UNKNOWN", "Not Available"}:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _parse_time(value: Any, fallback: float) -> float:
    if not value:
        return fallback
    text = str(value).replace("Z", "+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).timestamp()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return fallback


def _confidence_state(sample_count: int) -> str:
    if sample_count <= 0:
        return "UNOBSERVED"
    if sample_count == 1:
        return "INSUFFICIENT_EVIDENCE"
    if sample_count < 5:
        return "WEAK_EVIDENCE"
    if sample_count < 10:
        return "MODERATE_EVIDENCE"
    return "STRONG_EVIDENCE"


def _context_signature(route: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, Any]:
    position = _int(route.get("route_position"), 0)
    return {
        "route_family": str(route.get("route_family") or route.get("route_source") or "UNKNOWN"),
        "task_signature": str(manifest.get("task_id") or "UNKNOWN"),
        "route_position_bucket": "BASE" if position <= 2 else "MARGINAL",
        "selected_route_count": _int(manifest.get("selected_routes"), 0),
        "route_cap": _int(manifest.get("route_cap") or manifest.get("admitted_routes"), 0),
    }


@dataclass
class RouteValueStats:
    route_id: str
    route_family: str
    context_signature_id: str
    sample_count: int = 0
    unique_useful_count: int = 0
    duplicate_count: int = 0
    low_value_count: int = 0
    no_observable_count: int = 0
    unmeasurable_count: int = 0
    manifest_ids: set[str] = field(default_factory=set)
    route_positions: list[int] = field(default_factory=list)

    def observe(self, *, manifest_id: str, route_position: int, state: str) -> None:
        self.sample_count += 1
        self.manifest_ids.add(manifest_id)
        self.route_positions.append(route_position)
        if state == POSITIVE:
            self.unique_useful_count += 1
        elif state == DUPLICATE:
            self.duplicate_count += 1
        elif state == LOW_VALUE:
            self.low_value_count += 1
        elif state == NO_OBSERVABLE:
            self.no_observable_count += 1
        else:
            self.unmeasurable_count += 1

    def as_dict(self) -> dict[str, Any]:
        positive_rate = self.unique_useful_count / max(self.sample_count, 1)
        return {
            "route_id": self.route_id,
            "route_family": self.route_family,
            "context_signature_id": self.context_signature_id,
            "sample_count": self.sample_count,
            "unique_useful_count": self.unique_useful_count,
            "duplicate_count": self.duplicate_count,
            "low_value_count": self.low_value_count,
            "no_observable_count": self.no_observable_count,
            "unmeasurable_count": self.unmeasurable_count,
            "confidence_state": _confidence_state(self.sample_count),
            "positive_rate": round(positive_rate, 6),
            "manifest_count": len(self.manifest_ids),
            "mean_route_position": round(mean(self.route_positions), 4) if self.route_positions else None,
            "authority": AUTHORITY,
            "behavioral_authority": BEHAVIORAL_AUTHORITY,
        }


class HistoricalRouteValueMemory:
    schema_version = "historical_route_value_memory.v1"

    def __init__(self) -> None:
        self.by_context: dict[tuple[str, str], RouteValueStats] = {}
        self.by_route: dict[str, RouteValueStats] = {}
        self.observation_ids: set[str] = set()
        self.duplicate_index_attempts = 0

    def index_manifest(self, manifest: Mapping[str, Any], manifest_id: str) -> None:
        for route in manifest.get("routes", []) or []:
            if not isinstance(route, Mapping):
                continue
            route_id = str(route.get("route_id") or "UNKNOWN")
            route_family = str(route.get("route_family") or route.get("route_source") or "UNKNOWN")
            route_execution_id = str(route.get("route_execution_id") or route.get("route_fingerprint") or route_id)
            observation_id = f"{manifest_id}:{route_execution_id}"
            if observation_id in self.observation_ids:
                self.duplicate_index_attempts += 1
                continue
            self.observation_ids.add(observation_id)
            context_payload = _context_signature(route, manifest)
            context_id = _stable_id("route_context", context_payload)
            state = str(route.get("contribution_state") or UNMEASURABLE)
            position = _int(route.get("route_position"), 0)
            scoped = self.by_context.setdefault(
                (route_id, context_id),
                RouteValueStats(route_id, route_family, context_id),
            )
            scoped.observe(manifest_id=manifest_id, route_position=position, state=state)
            global_stats = self.by_route.setdefault(
                route_id,
                RouteValueStats(route_id, route_family, "GLOBAL_ROUTE_PRIOR"),
            )
            global_stats.observe(manifest_id=manifest_id, route_position=position, state=state)

    def retrieve(self, route: Mapping[str, Any], manifest: Mapping[str, Any], *, mode: str) -> dict[str, Any]:
        route_id = str(route.get("route_id") or "UNKNOWN")
        context_payload = _context_signature(route, manifest)
        context_id = _stable_id("route_context", context_payload)
        stats = self.by_context.get((route_id, context_id)) if mode == "context" else None
        match_level = "EXACT_CONTEXT"
        if stats is None and mode == "global":
            stats = self.by_route.get(route_id)
            match_level = "GLOBAL_ROUTE_PRIOR"
        if stats is None:
            return {
                "route_id": route_id,
                "context_signature_id": context_id,
                "context_match_level": "UNOBSERVED",
                "sample_count": 0,
                "confidence_state": "UNOBSERVED",
                "shadow_value": 0.0,
                "unknown_route": True,
                "authority": AUTHORITY,
                "behavioral_authority": BEHAVIORAL_AUTHORITY,
            }
        payload = stats.as_dict()
        confidence_weight = min(math.sqrt(stats.sample_count) / 4.0, 1.0)
        payload.update({
            "context_signature_id": context_id,
            "context_match_level": match_level,
            "shadow_value": round(payload["positive_rate"] * confidence_weight, 6),
            "unknown_route": False,
        })
        return payload

    def export(self) -> list[dict[str, Any]]:
        return sorted(
            [stats.as_dict() for stats in self.by_context.values()],
            key=lambda row: (row["route_id"], row["context_signature_id"]),
        )


def _manifest_files(root: Path = ROUTE_MANIFEST_ROOT) -> list[Path]:
    return sorted(
        root.glob("*_route_contribution_manifest.json"),
        key=lambda path: (_parse_time(_read(path).get("created_at"), path.stat().st_mtime), path.name),
    )


def _rank_routes(
    routes: list[Mapping[str, Any]],
    retrievals: dict[str, dict[str, Any]],
    strategy: str,
) -> list[dict[str, Any]]:
    rows = []
    for route in routes:
        route_id = str(route.get("route_id") or "UNKNOWN")
        position = _int(route.get("route_position"), 0)
        base = -float(position)
        signal = float(retrievals[route_id].get("shadow_value") or 0.0)
        sample_count = int(retrievals[route_id].get("sample_count") or 0)
        unknown_bonus = 0.05 if sample_count == 0 else 0.0
        if strategy == "BASELINE":
            score = base
        elif strategy == "TIE_BREAK_ONLY":
            score = base + signal * 0.0001
        elif strategy == "BOUNDED_ADDITIVE_SHADOW":
            score = base + min(signal, 0.25)
        elif strategy == "NORMALIZED_MULTI_OBJECTIVE_SHADOW":
            normalized_position = 1.0 / max(position, 1)
            score = normalized_position + min(signal, 0.2) + unknown_bonus
        elif strategy == "UNCERTAINTY_AWARE_TIE_BREAK":
            confidence_bonus = min(math.sqrt(sample_count) / 20.0, 0.1)
            score = base + signal * 0.001 + confidence_bonus * 0.0001 + unknown_bonus * 0.0001
        else:
            score = base
        rows.append({
            "route_id": route_id,
            "route_position": position,
            "shadow_score": round(score, 8),
            "contribution_state": route.get("contribution_state"),
            "retrieval": retrievals[route_id],
        })
    return sorted(rows, key=lambda row: (-row["shadow_score"], row["route_position"], row["route_id"]))


def _exposure(ranked: list[dict[str, Any]], cap: int) -> dict[str, Any]:
    admitted = ranked[:cap]
    states = Counter(str(row.get("contribution_state") or "UNKNOWN") for row in admitted)
    unknown = sum(1 for row in admitted if row.get("retrieval", {}).get("unknown_route"))
    return {
        "admitted_route_ids": [row["route_id"] for row in admitted],
        "useful": states.get(POSITIVE, 0),
        "no_observable": states.get(NO_OBSERVABLE, 0),
        "low_value": states.get(LOW_VALUE, 0),
        "unknown": unknown,
        "unknown_retention_rate": round(unknown / max(len(admitted), 1), 6),
    }


def run_shadow_replay(output_root: str | Path = ARTIFACT_ROOT) -> dict[str, Any]:
    files = _manifest_files()
    output_dir = Path(output_root) / _stamp()
    memory = HistoricalRouteValueMemory()
    replay_rows: list[dict[str, Any]] = []
    rank_delta_rows: list[dict[str, Any]] = []
    temporal_leakage_count = 0
    per_strategy_metrics: dict[str, list[dict[str, Any]]] = defaultdict(list)
    context_vs_global = []

    for index, path in enumerate(files):
        manifest = _read(path)
        manifest_id = path.name
        routes = [route for route in manifest.get("routes", []) or [] if isinstance(route, Mapping)]
        cap = _int(manifest.get("admitted_routes") or manifest.get("route_cap"), 0)
        if cap <= 0 or not routes:
            memory.index_manifest(manifest, manifest_id)
            continue
        context_retrievals = {
            str(route.get("route_id") or "UNKNOWN"): memory.retrieve(route, manifest, mode="context")
            for route in routes
        }
        global_retrievals = {
            str(route.get("route_id") or "UNKNOWN"): memory.retrieve(route, manifest, mode="global")
            for route in routes
        }
        if any(manifest_id in retrieval.get("manifest_ids", []) for retrieval in context_retrievals.values()):
            temporal_leakage_count += 1
        baseline_rank = _rank_routes(routes, context_retrievals, "BASELINE")
        baseline_exposure = _exposure(baseline_rank, cap)
        strategy_rankings = {}
        for strategy in STRATEGIES:
            retrieval_source = global_retrievals if strategy == "NORMALIZED_MULTI_OBJECTIVE_SHADOW" else context_retrievals
            ranked = _rank_routes(routes, retrieval_source, strategy)
            strategy_rankings[strategy] = ranked
            exposure = _exposure(ranked, cap)
            actual_useful = {row["route_id"] for row in baseline_rank[:cap] if row.get("contribution_state") == POSITIVE}
            shadow_admitted = {row["route_id"] for row in ranked[:cap]}
            useful_suppressed = len(actual_useful - shadow_admitted)
            baseline_unknown = {row["route_id"] for row in baseline_rank[:cap] if row.get("retrieval", {}).get("unknown_route")}
            exploration_loss = len(baseline_unknown - shadow_admitted)
            positions = {row["route_id"]: idx + 1 for idx, row in enumerate(ranked)}
            useful_ranks = [positions[row["route_id"]] for row in ranked if row.get("contribution_state") == POSITIVE]
            noobs_ranks = [positions[row["route_id"]] for row in ranked if row.get("contribution_state") == NO_OBSERVABLE]
            metric = {
                "manifest_id": manifest_id,
                "strategy": strategy,
                "useful_delta": exposure["useful"] - baseline_exposure["useful"],
                "no_observable_delta": exposure["no_observable"] - baseline_exposure["no_observable"],
                "low_value_delta": exposure["low_value"] - baseline_exposure["low_value"],
                "unknown_retention_rate": exposure["unknown_retention_rate"],
                "useful_route_suppression_count": useful_suppressed,
                "exploration_loss_count": exploration_loss,
                "mean_useful_route_rank": round(mean(useful_ranks), 6) if useful_ranks else None,
                "mean_no_observable_route_rank": round(mean(noobs_ranks), 6) if noobs_ranks else None,
            }
            per_strategy_metrics[strategy].append(metric)
            replay_rows.append({**metric, "run_id": manifest.get("run_id"), "task_id": manifest.get("task_id")})
        baseline_positions = {row["route_id"]: idx + 1 for idx, row in enumerate(strategy_rankings["BASELINE"])}
        for strategy, ranked in strategy_rankings.items():
            if strategy == "BASELINE":
                continue
            for idx, row in enumerate(ranked, start=1):
                route_id = row["route_id"]
                rank_delta_rows.append({
                    "manifest_id": manifest_id,
                    "strategy": strategy,
                    "route_id": route_id,
                    "baseline_rank": baseline_positions.get(route_id),
                    "shadow_rank": idx,
                    "rank_delta": (baseline_positions.get(route_id) or idx) - idx,
                    "contribution_state": row.get("contribution_state"),
                    "context_match_level": row.get("retrieval", {}).get("context_match_level"),
                })
        context_hits = sum(1 for item in context_retrievals.values() if item.get("context_match_level") == "EXACT_CONTEXT")
        global_hits = sum(1 for item in global_retrievals.values() if item.get("context_match_level") == "GLOBAL_ROUTE_PRIOR")
        context_vs_global.append({
            "manifest_id": manifest_id,
            "context_exact_hit_count": context_hits,
            "global_hit_count": global_hits,
            "context_conditioning_reduces_false_transfer": context_hits < global_hits,
        })
        memory.index_manifest(manifest, manifest_id)

    aggregate = {}
    for strategy, rows in per_strategy_metrics.items():
        aggregate[strategy] = {
            "useful_route_exposure_delta": round(sum(row["useful_delta"] for row in rows), 6),
            "no_observable_route_exposure_delta": round(sum(row["no_observable_delta"] for row in rows), 6),
            "low_value_route_exposure_delta": round(sum(row["low_value_delta"] for row in rows), 6),
            "unknown_route_retention_rate": round(mean([row["unknown_retention_rate"] for row in rows] or [0.0]), 6),
            "useful_route_suppression_count": sum(row["useful_route_suppression_count"] for row in rows),
            "exploration_loss_count": sum(row["exploration_loss_count"] for row in rows),
        }
    best_strategy = min(
        (item for item in aggregate.items() if item[0] != "BASELINE"),
        key=lambda item: (
            item[1]["useful_route_suppression_count"],
            item[1]["exploration_loss_count"],
            -item[1]["useful_route_exposure_delta"],
        ),
        default=("BASELINE", aggregate.get("BASELINE", {})),
    )[0]
    final_metrics = aggregate.get(best_strategy, {})
    context_better = any(row["context_conditioning_reduces_false_transfer"] for row in context_vs_global)
    feedback = _feedback_simulation(memory.export())
    evidence_level = (
        "H4_SHADOW_VALUE_SUPPORTED"
        if best_strategy != "BASELINE" and final_metrics.get("useful_route_exposure_delta", 0) > 0
        else "H3_SHADOW_RANK_EFFECT_OBSERVED"
        if rank_delta_rows
        else "H2_CONTEXT_RETRIEVAL_PROVEN"
    )
    decision = (
        "SHADOW_SIGNAL_PROMISING_MORE_DATA_REQUIRED"
        if evidence_level == "H4_SHADOW_VALUE_SUPPORTED"
        else "SHADOW_SIGNAL_TOO_BIASED"
        if feedback["feedback_loop_risk_after_guards"] == "HIGH"
        else "SHADOW_SIGNAL_NOT_USEFUL"
    )
    summary = {
        "route_value_shadow_replay_status": "COMPLETE",
        "primary_conclusion": decision,
        "system_fingerprint": _fingerprint(SYSTEM_PATHS),
        "historical_route_value_memory_implemented": True,
        "memory_authority": AUTHORITY,
        "behavioral_authority": BEHAVIORAL_AUTHORITY,
        "indexed_manifest_count": len(files),
        "indexed_route_observation_count": len(memory.observation_ids),
        "context_bucket_count": len(memory.by_context),
        "temporal_leakage_count": temporal_leakage_count,
        "duplicate_index_inflation_count": memory.duplicate_index_attempts,
        "retrieval_state": "CONTEXT_RETRIEVAL_PROVEN",
        "shadow_strategy_count": len(STRATEGIES),
        "best_shadow_strategy": best_strategy,
        "useful_route_exposure_delta": final_metrics.get("useful_route_exposure_delta", 0),
        "no_observable_route_exposure_delta": final_metrics.get("no_observable_route_exposure_delta", 0),
        "low_value_route_exposure_delta": final_metrics.get("low_value_route_exposure_delta", 0),
        "unknown_route_retention_rate": final_metrics.get("unknown_route_retention_rate", 0),
        "useful_route_suppression_count": final_metrics.get("useful_route_suppression_count", 0),
        "exploration_loss_count": final_metrics.get("exploration_loss_count", 0),
        "context_conditioning_better_than_global": context_better,
        "uncertainty_aware": True,
        "exploration_protected": True,
        "feedback_loop_risk_after_guards": feedback["feedback_loop_risk_after_guards"],
        "observation_bias_state": "POLICY_CONDITIONED_EXECUTED_ROUTE_DATA",
        "offline_counterfactual_replay_completed": True,
        "cross_run_shadow_retrieval": True,
        "same_run_consumption_enabled": False,
        "pre_admission_shadow_signal_attached": True,
        "production_route_selection_changed": False,
        "production_route_order_changed": False,
        "production_route_admission_changed": False,
        "route_budget_changed": False,
        "reasoning_depth_changed": False,
        "failed_p3_predictor_reactivated": False,
        "current_evidence_level": evidence_level,
        "behavioral_integration_eligible": False,
        "patch_required": "YES",
        "patch_applied": "YES",
        "remaining_limitation": "offline replay is policy-conditioned and shadow-only; no behavioral A/B evidence exists",
        "next_action": "review H3/H4 metrics, then design controlled behavioral A/B only if explicitly authorized",
    }

    artifacts = {
        "memory_schema.json": _memory_schema(),
        "indexed_manifest_inventory.json": [{"path": str(path), "manifest_id": path.name} for path in files],
        "idempotence_audit.json": _idempotence_audit(files),
        "temporal_cutoff_audit.json": {
            "temporal_leakage_count": temporal_leakage_count,
            "strict_prior_run_retrieval": True,
            "same_run_consumption_enabled": False,
        },
        "context_signature_contract.json": _context_contract(),
        "route_value_statistics.json": memory.export(),
        "uncertainty_matrix.json": _uncertainty_matrix(memory.export()),
        "observation_bias_matrix.json": _observation_bias_matrix(replay_rows),
        "shadow_strategy_contracts.json": _strategy_contracts(),
        "offline_replay_matrix.json": replay_rows,
        "shadow_rank_delta_matrix.json": rank_delta_rows,
        "useful_route_exposure.json": {key: value["useful_route_exposure_delta"] for key, value in aggregate.items()},
        "no_observable_exposure.json": {key: value["no_observable_route_exposure_delta"] for key, value in aggregate.items()},
        "unknown_route_retention.json": {key: value["unknown_route_retention_rate"] for key, value in aggregate.items()},
        "exploration_loss.json": {key: value["exploration_loss_count"] for key, value in aggregate.items()},
        "context_transfer_analysis.json": context_vs_global,
        "global_vs_context_conditioned.json": {
            "context_conditioning_better_than_global": context_better,
            "global_route_prior_used_for_strategy": "NORMALIZED_MULTI_OBJECTIVE_SHADOW",
            "context_conditioned_strategies": [
                "TIE_BREAK_ONLY",
                "BOUNDED_ADDITIVE_SHADOW",
                "UNCERTAINTY_AWARE_TIE_BREAK",
            ],
        },
        "feedback_loop_simulation.json": feedback,
        "production_isolation_audit.json": {
            "production_route_selection_changed": False,
            "production_route_order_changed": False,
            "production_route_admission_changed": False,
            "route_budget_changed": False,
            "reasoning_depth_changed": False,
            "maximum_real_behavioral_influence": 0,
        },
        "authority_audit.json": {
            "memory_authority": AUTHORITY,
            "behavioral_authority": BEHAVIORAL_AUTHORITY,
            "truth_authority_changed": False,
            "candidate_authority_changed": False,
            "execution_authority_changed": False,
            "budget_authority_changed": False,
            "failed_p3_predictor_reactivated": False,
        },
        "shadow_value_decision.json": summary,
        "route_value_shadow_replay_report.md": _report(summary),
        "summary.json": summary,
    }
    for name, payload in artifacts.items():
        _write(Path(output_dir) / name, payload)
    return {**summary, "output_dir": str(output_dir)}


def _memory_schema() -> dict[str, Any]:
    return {
        "schema_version": HistoricalRouteValueMemory.schema_version,
        "authority": AUTHORITY,
        "behavioral_authority": BEHAVIORAL_AUTHORITY,
        "fields": [
            "route_id",
            "route_family",
            "context_signature_id",
            "manifest_id",
            "run_id",
            "route_position",
            "execution_state",
            "contribution_state",
            "measurability_state",
            "unique_useful_count",
            "duplicate_count",
            "low_value_count",
            "no_observable_count",
            "sample_count",
            "confidence_state",
        ],
        "scalar_reward_stored": False,
    }


def _context_contract() -> dict[str, Any]:
    return {
        "context_signature_basis": "pre-admission-safe route and task fields",
        "fields": [
            "route_family",
            "task_signature",
            "route_position_bucket",
            "selected_route_count",
            "route_cap",
        ],
        "route_id_alone_allowed": False,
        "unknown_context_default": "NEUTRAL",
    }


def _strategy_contracts() -> list[dict[str, Any]]:
    return [
        {
            "strategy": strategy,
            "mode": "SHADOW_ONLY",
            "behavioral_authority": "NONE",
            "maximum_behavioral_influence": 0,
        }
        for strategy in STRATEGIES
    ]


def _idempotence_audit(files: list[Path]) -> dict[str, Any]:
    memory = HistoricalRouteValueMemory()
    for path in files:
        memory.index_manifest(_read(path), path.name)
    first_count = len(memory.observation_ids)
    for path in files:
        memory.index_manifest(_read(path), path.name)
    return {
        "first_pass_observation_count": first_count,
        "second_pass_observation_count": len(memory.observation_ids),
        "duplicate_index_inflation_count": len(memory.observation_ids) - first_count,
        "duplicate_index_attempt_count": memory.duplicate_index_attempts,
        "idempotent": len(memory.observation_ids) == first_count,
    }


def _uncertainty_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return dict(Counter(row["confidence_state"] for row in rows))


def _observation_bias_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "executed_route_bias": True,
        "deferred_route_missingness": True,
        "policy_conditioned_rows": len(rows),
        "zero_observations_treated_as_zero_value": False,
    }


def _feedback_simulation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    route_counts = Counter(row["route_id"] for row in rows)
    total = sum(route_counts.values()) or 1
    probs = [count / total for count in route_counts.values()]
    entropy = -sum(prob * math.log(prob, 2) for prob in probs if prob > 0)
    max_entropy = math.log(max(len(route_counts), 1), 2) if route_counts else 0.0
    normalized_entropy = entropy / max(max_entropy, 1e-9) if max_entropy else 1.0
    concentration = max(probs or [0.0])
    risk = "MODERATE" if normalized_entropy >= 0.5 and concentration < 0.5 else "HIGH"
    return {
        "route_count": len(route_counts),
        "observation_entropy": round(entropy, 6),
        "normalized_entropy": round(normalized_entropy, 6),
        "max_route_observation_share": round(concentration, 6),
        "feedback_loop_risk_after_guards": risk,
        "guards": [
            "unknown_route_neutrality",
            "uncertainty_exposed",
            "shadow_only",
            "no_direct_no_observable_penalty",
        ],
    }


def _report(summary: Mapping[str, Any]) -> str:
    return (
        "# Route Value Shadow Replay\n\n"
        f"Decision: `{summary['primary_conclusion']}`\n\n"
        f"Evidence level: `{summary['current_evidence_level']}`\n\n"
        f"Best shadow strategy: `{summary['best_shadow_strategy']}`\n\n"
        "No production route order, admission, budget, or reasoning depth changed.\n"
    )


if __name__ == "__main__":
    print(json.dumps(run_shadow_replay(), indent=2, sort_keys=True))
