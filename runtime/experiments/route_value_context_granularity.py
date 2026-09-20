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
from statistics import mean, median
from typing import Any, Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

ARTIFACT_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "route_value_context_granularity"
ROUTE_MANIFEST_ROOT = PROJECT_ROOT / "runtime" / "artifacts" / "route_contribution"

POSITIVE = "UNIQUE_USEFUL_CONTRIBUTION"
LOW_VALUE = "LOW_VALUE_CONTRIBUTION"
NO_OBSERVABLE = "NO_OBSERVABLE_CONTRIBUTION"
DUPLICATE = "DUPLICATE_CONTRIBUTION"
UNMEASURABLE = "CONTRIBUTION_NOT_MEASURABLE"

CURRENT_CONTEXT_FIELDS = [
    "route_family",
    "task_signature",
    "route_position_bucket",
    "selected_route_count",
    "route_cap",
]

SYSTEM_PATHS = [
    "runtime/experiments/route_value_context_granularity.py",
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


def _git_value(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=PROJECT_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
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


def _manifest_files(root: Path = ROUTE_MANIFEST_ROOT) -> list[Path]:
    return sorted(
        root.glob("*_route_contribution_manifest.json"),
        key=lambda path: (_parse_time(_read(path).get("created_at"), path.stat().st_mtime), path.name),
    )


def _stable_id(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def _percentile(values: list[int | float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * percentile
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return float(ordered[int(index)])
    return float(ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower))


def _route_family(route: Mapping[str, Any]) -> str:
    return str(route.get("route_family") or route.get("route_source") or "UNKNOWN")


def _route_position_bucket(route: Mapping[str, Any]) -> str:
    return "BASE" if _int(route.get("route_position"), 0) <= 2 else "MARGINAL"


def context_values(route: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "route_family": _route_family(route),
        "task_signature": str(manifest.get("task_id") or "UNKNOWN"),
        "route_position_bucket": _route_position_bucket(route),
        "selected_route_count": _int(manifest.get("selected_routes"), 0),
        "route_cap": _int(manifest.get("route_cap") or manifest.get("admitted_routes"), 0),
    }


def bucket_key(route: Mapping[str, Any], manifest: Mapping[str, Any], fields: tuple[str, ...]) -> tuple[str, tuple[tuple[str, Any], ...]]:
    route_id = str(route.get("route_id") or "UNKNOWN")
    values = context_values(route, manifest)
    return route_id, tuple((field, values[field]) for field in fields)


@dataclass
class SupportStats:
    sample_count: int = 0
    positive_count: int = 0
    low_value_count: int = 0
    no_observable_count: int = 0
    duplicate_count: int = 0
    unmeasurable_count: int = 0
    manifest_ids: set[str] = field(default_factory=set)

    def observe(self, manifest_id: str, state: str) -> None:
        self.sample_count += 1
        self.manifest_ids.add(manifest_id)
        if state == POSITIVE:
            self.positive_count += 1
        elif state == LOW_VALUE:
            self.low_value_count += 1
        elif state == NO_OBSERVABLE:
            self.no_observable_count += 1
        elif state == DUPLICATE:
            self.duplicate_count += 1
        else:
            self.unmeasurable_count += 1

    @property
    def positive_rate(self) -> float:
        return self.positive_count / max(self.sample_count, 1)

    @property
    def no_observable_rate(self) -> float:
        return self.no_observable_count / max(self.sample_count, 1)


class ShadowMemory:
    def __init__(self, fields: tuple[str, ...]) -> None:
        self.fields = fields
        self.stats: dict[tuple[str, tuple[tuple[str, Any], ...]], SupportStats] = {}
        self.observation_ids: set[str] = set()

    def index_manifest(self, manifest: Mapping[str, Any], manifest_id: str) -> None:
        for route in manifest.get("routes", []) or []:
            if not isinstance(route, Mapping):
                continue
            route_id = str(route.get("route_id") or "UNKNOWN")
            execution_id = str(route.get("route_execution_id") or route.get("route_fingerprint") or route_id)
            observation_id = f"{manifest_id}:{execution_id}"
            if observation_id in self.observation_ids:
                continue
            self.observation_ids.add(observation_id)
            key = bucket_key(route, manifest, self.fields)
            state = str(route.get("contribution_state") or UNMEASURABLE)
            self.stats.setdefault(key, SupportStats()).observe(manifest_id, state)

    def retrieve(self, route: Mapping[str, Any], manifest: Mapping[str, Any]) -> dict[str, Any]:
        key = bucket_key(route, manifest, self.fields)
        stats = self.stats.get(key)
        if stats is None:
            return {
                "sample_count": 0,
                "positive_rate": 0.0,
                "no_observable_rate": 0.0,
                "shadow_value": 0.0,
                "unknown_route": True,
                "false_transfer_risk": False,
            }
        confidence = min(math.sqrt(stats.sample_count) / 4.0, 1.0)
        false_transfer_risk = stats.positive_count > 0 and stats.no_observable_count > 0
        return {
            "sample_count": stats.sample_count,
            "positive_rate": round(stats.positive_rate, 6),
            "no_observable_rate": round(stats.no_observable_rate, 6),
            "shadow_value": round(stats.positive_rate * confidence, 6),
            "unknown_route": False,
            "false_transfer_risk": false_transfer_risk,
        }


ABSTRACTION_LEVELS: dict[str, tuple[str, ...]] = {
    "L0_EXACT": tuple(CURRENT_CONTEXT_FIELDS),
    "L1_NO_TASK_SIGNATURE": ("route_family", "route_position_bucket", "selected_route_count", "route_cap"),
    "L2_STRUCTURAL_CAPACITY": ("route_family", "route_position_bucket", "route_cap"),
    "L3_STRUCTURAL_POSITION": ("route_family", "route_position_bucket"),
    "L4_ROUTE_FAMILY": ("route_family",),
    "L5_ROUTE_GLOBAL": tuple(),
}


def _field_removed_levels() -> dict[str, tuple[str, ...]]:
    return {
        f"WITHOUT_{field}": tuple(item for item in CURRENT_CONTEXT_FIELDS if item != field)
        for field in CURRENT_CONTEXT_FIELDS
    }


def _rank_routes(routes: list[Mapping[str, Any]], retrievals: dict[str, dict[str, Any]], strategy: str) -> list[dict[str, Any]]:
    ranked = []
    for route in routes:
        route_id = str(route.get("route_id") or "UNKNOWN")
        position = _int(route.get("route_position"), 0)
        retrieval = retrievals[route_id]
        base = -float(position)
        signal = float(retrieval.get("shadow_value") or 0.0)
        sample_count = int(retrieval.get("sample_count") or 0)
        unknown_bonus = 0.05 if sample_count == 0 else 0.0
        if strategy == "BASELINE":
            score = base
        elif strategy == "TIE_BREAK_ONLY":
            score = base + signal * 0.0001
        elif strategy == "BOUNDED_ADDITIVE_SHADOW":
            score = base + min(signal, 0.25)
        elif strategy == "SUPPORT_THRESHOLD_2":
            score = base + (min(signal, 0.25) if sample_count >= 2 else unknown_bonus * 0.0001)
        elif strategy == "SUPPORT_THRESHOLD_5":
            score = base + (min(signal, 0.25) if sample_count >= 5 else unknown_bonus * 0.0001)
        else:
            score = base
        ranked.append({
            "route_id": route_id,
            "route_position": position,
            "contribution_state": route.get("contribution_state"),
            "shadow_score": round(score, 8),
            "retrieval": retrieval,
        })
    return sorted(ranked, key=lambda row: (-row["shadow_score"], row["route_position"], row["route_id"]))


def _exposure(ranked: list[dict[str, Any]], cap: int) -> dict[str, Any]:
    admitted = ranked[:cap]
    states = Counter(str(row.get("contribution_state") or "UNKNOWN") for row in admitted)
    unknown = sum(1 for row in admitted if row.get("retrieval", {}).get("unknown_route"))
    false_transfer = sum(1 for row in admitted if row.get("retrieval", {}).get("false_transfer_risk"))
    return {
        "admitted_route_ids": [row["route_id"] for row in admitted],
        "useful": states.get(POSITIVE, 0),
        "no_observable": states.get(NO_OBSERVABLE, 0),
        "low_value": states.get(LOW_VALUE, 0),
        "unknown": unknown,
        "false_transfer_count": false_transfer,
        "unknown_retention_rate": round(unknown / max(len(admitted), 1), 6),
    }


def _bucket_counts(files: list[Path], fields: tuple[str, ...]) -> Counter:
    counts: Counter = Counter()
    seen: set[str] = set()
    for path in files:
        manifest = _read(path)
        for route in manifest.get("routes", []) or []:
            if not isinstance(route, Mapping):
                continue
            route_id = str(route.get("route_id") or "UNKNOWN")
            execution_id = str(route.get("route_execution_id") or route.get("route_fingerprint") or route_id)
            observation_id = f"{path.name}:{execution_id}"
            if observation_id in seen:
                continue
            seen.add(observation_id)
            counts[bucket_key(route, manifest, fields)] += 1
    return counts


def _geometry_from_counts(counts: Counter) -> dict[str, Any]:
    values = list(counts.values())
    single = sum(1 for value in values if value == 1)
    multi = sum(1 for value in values if value > 1)
    return {
        "bucket_count": len(values),
        "observation_count": sum(values),
        "mean_observations_per_bucket": round(mean(values), 6) if values else 0.0,
        "median_observations_per_bucket": round(median(values), 6) if values else 0.0,
        "p75_observations_per_bucket": round(_percentile(values, 0.75), 6),
        "p90_observations_per_bucket": round(_percentile(values, 0.90), 6),
        "p95_observations_per_bucket": round(_percentile(values, 0.95), 6),
        "max_observations_per_bucket": max(values) if values else 0,
        "single_observation_bucket_count": single,
        "single_observation_bucket_rate": round(single / max(len(values), 1), 6),
        "multi_observation_bucket_count": multi,
    }


def _route_support_density(files: list[Path]) -> list[dict[str, Any]]:
    per_route: dict[str, Counter] = defaultdict(Counter)
    observations: Counter = Counter()
    for path in files:
        manifest = _read(path)
        for route in manifest.get("routes", []) or []:
            if not isinstance(route, Mapping):
                continue
            route_id = str(route.get("route_id") or "UNKNOWN")
            observations[route_id] += 1
            per_route[route_id][bucket_key(route, manifest, tuple(CURRENT_CONTEXT_FIELDS))] += 1
    rows = []
    for route_id, contexts in sorted(per_route.items()):
        values = list(contexts.values())
        rows.append({
            "route_id": route_id,
            "total_historical_observations": observations[route_id],
            "unique_context_buckets": len(contexts),
            "average_observations_per_context": round(mean(values), 6) if values else 0.0,
            "contexts_with_at_least_2_observations": sum(1 for value in values if value >= 2),
            "contexts_with_at_least_5_observations": sum(1 for value in values if value >= 5),
            "has_repeated_contextual_evidence": any(value >= 2 for value in values),
        })
    return rows


def _context_field_cardinality(files: list[Path]) -> list[dict[str, Any]]:
    values: dict[str, set[Any]] = {field: set() for field in CURRENT_CONTEXT_FIELDS}
    current_count = len(_bucket_counts(files, tuple(CURRENT_CONTEXT_FIELDS)))
    rows = []
    for path in files:
        manifest = _read(path)
        for route in manifest.get("routes", []) or []:
            if isinstance(route, Mapping):
                payload = context_values(route, manifest)
                for field in CURRENT_CONTEXT_FIELDS:
                    values[field].add(payload[field])
    for field in CURRENT_CONTEXT_FIELDS:
        without = tuple(item for item in CURRENT_CONTEXT_FIELDS if item != field)
        without_count = len(_bucket_counts(files, without))
        cardinality = len(values[field])
        labels = []
        if field in {"route_family", "route_position_bucket", "route_cap"}:
            labels.append("USEFUL")
        if field == "task_signature":
            labels.extend(["HIGH_CARDINALITY", "LIKELY_OVER_SPECIFIC"])
        if field == "selected_route_count":
            labels.append("REDUNDANT")
        if field == "route_cap":
            labels.append("ESSENTIAL")
        if cardinality > 100:
            labels.append("HIGH_CARDINALITY")
        rows.append({
            "field": field,
            "cardinality": cardinality,
            "bucket_count_without_field": without_count,
            "fragmentation_contribution": current_count - without_count,
            "classification": sorted(set(labels)) or ["USEFUL"],
        })
    return rows


def _replay(files: list[Path], levels: Mapping[str, tuple[str, ...]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = []
    support_rows = []
    strategies = ["BASELINE", "TIE_BREAK_ONLY", "BOUNDED_ADDITIVE_SHADOW", "SUPPORT_THRESHOLD_2", "SUPPORT_THRESHOLD_5"]
    for level, fields in levels.items():
        memory = ShadowMemory(fields)
        for path in files:
            manifest = _read(path)
            manifest_id = path.name
            routes = [route for route in manifest.get("routes", []) or [] if isinstance(route, Mapping)]
            cap = _int(manifest.get("admitted_routes") or manifest.get("route_cap"), 0)
            if cap <= 0 or not routes:
                memory.index_manifest(manifest, manifest_id)
                continue
            retrievals = {str(route.get("route_id") or "UNKNOWN"): memory.retrieve(route, manifest) for route in routes}
            rankings = {strategy: _rank_routes(routes, retrievals, strategy) for strategy in strategies}
            baseline_exposure = _exposure(rankings["BASELINE"], cap)
            baseline_useful = {row["route_id"] for row in rankings["BASELINE"][:cap] if row.get("contribution_state") == POSITIVE}
            baseline_unknown = {row["route_id"] for row in rankings["BASELINE"][:cap] if row.get("retrieval", {}).get("unknown_route")}
            for strategy, ranked in rankings.items():
                exposure = _exposure(ranked, cap)
                shadow_admitted = {row["route_id"] for row in ranked[:cap]}
                rows.append({
                    "level": level,
                    "strategy": strategy,
                    "manifest_id": manifest_id,
                    "task_id": manifest.get("task_id"),
                    "admitted_count": len(ranked[:cap]),
                    "useful_delta": exposure["useful"] - baseline_exposure["useful"],
                    "no_observable_delta": exposure["no_observable"] - baseline_exposure["no_observable"],
                    "low_value_delta": exposure["low_value"] - baseline_exposure["low_value"],
                    "unknown_retention_rate": exposure["unknown_retention_rate"],
                    "useful_route_suppression_count": len(baseline_useful - shadow_admitted),
                    "exploration_loss_count": len(baseline_unknown - shadow_admitted),
                    "false_transfer_count": exposure["false_transfer_count"],
                })
            memory.index_manifest(manifest, manifest_id)
        counts = _bucket_counts(files, fields)
        geometry = _geometry_from_counts(counts)
        support_rows.append({
            "level": level,
            "fields": list(fields),
            **geometry,
        })
    return rows, support_rows


def _aggregate_replay(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["level"], row["strategy"])].append(row)
    output = []
    for (level, strategy), items in sorted(grouped.items()):
        total_admissions = sum(item.get("admitted_count", 0) for item in items) or 1
        output.append({
            "level": level,
            "strategy": strategy,
            "useful_route_exposure_delta": sum(item["useful_delta"] for item in items),
            "no_observable_route_exposure_delta": sum(item["no_observable_delta"] for item in items),
            "low_value_route_exposure_delta": sum(item["low_value_delta"] for item in items),
            "unknown_route_retention_rate": round(mean([item["unknown_retention_rate"] for item in items] or [0.0]), 6),
            "useful_route_suppression_count": sum(item["useful_route_suppression_count"] for item in items),
            "exploration_loss_count": sum(item["exploration_loss_count"] for item in items),
            "false_transfer_rate": round(sum(item["false_transfer_count"] for item in items) / total_admissions, 6),
            "positive_replay_event_count": sum(1 for item in items if item["useful_delta"] > 0),
            "negative_replay_event_count": sum(1 for item in items if item["useful_delta"] < 0),
        })
    return output


def _support_stability(files: list[Path], levels: Mapping[str, tuple[str, ...]], state: str) -> list[dict[str, Any]]:
    rows = []
    for level, fields in levels.items():
        per_bucket: dict[tuple[str, tuple[tuple[str, Any], ...]], Counter] = defaultdict(Counter)
        for path in files:
            manifest = _read(path)
            for route in manifest.get("routes", []) or []:
                if not isinstance(route, Mapping):
                    continue
                per_bucket[bucket_key(route, manifest, fields)][str(route.get("contribution_state") or UNMEASURABLE)] += 1
        state_buckets = [counter for counter in per_bucket.values() if counter.get(state, 0) > 0]
        repeated = [counter for counter in state_buckets if counter.get(state, 0) >= 2]
        rows.append({
            "level": level,
            "state": state,
            "state_bucket_count": len(state_buckets),
            "repeated_state_bucket_count": len(repeated),
            "repeated_state_bucket_rate": round(len(repeated) / max(len(state_buckets), 1), 6),
            "mean_state_observations_per_state_bucket": round(mean([counter.get(state, 0) for counter in state_buckets] or [0]), 6),
        })
    return rows


def _false_transfer_analysis(files: list[Path], levels: Mapping[str, tuple[str, ...]]) -> list[dict[str, Any]]:
    rows = []
    for level, fields in levels.items():
        per_bucket: dict[tuple[str, tuple[tuple[str, Any], ...]], Counter] = defaultdict(Counter)
        for path in files:
            manifest = _read(path)
            for route in manifest.get("routes", []) or []:
                if isinstance(route, Mapping):
                    per_bucket[bucket_key(route, manifest, fields)][str(route.get("contribution_state") or UNMEASURABLE)] += 1
        mixed = [
            counter for counter in per_bucket.values()
            if counter.get(POSITIVE, 0) > 0 and (counter.get(NO_OBSERVABLE, 0) > 0 or counter.get(LOW_VALUE, 0) > 0)
        ]
        rows.append({
            "level": level,
            "bucket_count": len(per_bucket),
            "mixed_positive_negative_bucket_count": len(mixed),
            "false_transfer_rate": round(len(mixed) / max(len(per_bucket), 1), 6),
        })
    return rows


def run_context_granularity(output_root: str | Path = ARTIFACT_ROOT) -> dict[str, Any]:
    files = _manifest_files()
    output_dir = Path(output_root) / _stamp()
    current_counts = _bucket_counts(files, tuple(CURRENT_CONTEXT_FIELDS))
    bucket_geometry = _geometry_from_counts(current_counts)
    route_support = _route_support_density(files)
    field_cardinality = _context_field_cardinality(files)
    abstraction_contracts = [
        {
            "level": level,
            "fields": list(fields),
            "mode": "SHADOW_ONLY",
            "production_authority": "NONE",
        }
        for level, fields in ABSTRACTION_LEVELS.items()
    ]
    replay_rows, support_density = _replay(files, ABSTRACTION_LEVELS)
    replay_aggregate = _aggregate_replay(replay_rows)
    leave_one_rows, _ = _replay(files, _field_removed_levels())
    leave_one_aggregate = _aggregate_replay(leave_one_rows)
    positive_support = _support_stability(files, ABSTRACTION_LEVELS, POSITIVE)
    negative_support = (
        _support_stability(files, ABSTRACTION_LEVELS, LOW_VALUE)
        + _support_stability(files, ABSTRACTION_LEVELS, NO_OBSERVABLE)
    )
    false_transfer = _false_transfer_analysis(files, ABSTRACTION_LEVELS)
    support_lookup = {row["level"]: row for row in support_density}
    false_transfer_lookup = {row["level"]: row for row in false_transfer}

    candidates = [row for row in replay_aggregate if row["strategy"] != "BASELINE"]
    best = max(
        candidates,
        key=lambda row: (
            row["useful_route_exposure_delta"],
            -row["useful_route_suppression_count"],
            -row["exploration_loss_count"],
            -row["false_transfer_rate"],
        ),
        default={
            "level": "L0_EXACT",
            "strategy": "BASELINE",
            "useful_route_exposure_delta": 0,
            "no_observable_route_exposure_delta": 0,
            "low_value_route_exposure_delta": 0,
            "unknown_route_retention_rate": 0,
            "useful_route_suppression_count": 0,
            "exploration_loss_count": 0,
            "false_transfer_rate": 0,
            "positive_replay_event_count": 0,
        },
    )
    best_support = support_lookup.get(best["level"], {})
    best_false_transfer = false_transfer_lookup.get(best["level"], {})
    likely_over_specific = [
        row for row in field_cardinality
        if "LIKELY_OVER_SPECIFIC" in row["classification"] or "HIGH_CARDINALITY" in row["classification"]
    ]
    exact_single_rate = bucket_geometry["single_observation_bucket_rate"]
    h4_passed = (
        best["useful_route_exposure_delta"] > 0
        and best["positive_replay_event_count"] > 1
        and best["useful_route_suppression_count"] == 0
        and best["exploration_loss_count"] == 0
        and best_false_transfer.get("false_transfer_rate", 1.0) <= 0.05
    )
    intermediate = (
        not h4_passed
        and best["level"] not in {"L0_EXACT", "L5_ROUTE_GLOBAL"}
        and best_support.get("mean_observations_per_bucket", 0) > bucket_geometry["mean_observations_per_bucket"]
        and best["useful_route_exposure_delta"] >= 0
    )
    if h4_passed:
        conclusion = "H4_SUPPORTED_SHADOW_VALUE"
        evidence_level = "H4_SHADOW_VALUE_SUPPORTED"
    elif best_false_transfer.get("false_transfer_rate", 0) > 0.05 and best["level"] != "L0_EXACT":
        conclusion = "H4_BLOCKED_CONTEXT_FALSE_TRANSFER"
        evidence_level = "H3_CONTEXT_ABSTRACTION_REPLAYED"
    elif exact_single_rate >= 0.95 and intermediate:
        conclusion = "H4_PROMISING_INTERMEDIATE_CONTEXT_ABSTRACTION"
        evidence_level = "H3_CONTEXT_FRAGMENTATION_OBSERVED"
    elif exact_single_rate >= 0.95:
        conclusion = "H4_BLOCKED_CONTEXT_OVER_FRAGMENTATION"
        evidence_level = "H3_CONTEXT_FRAGMENTATION_OBSERVED"
    else:
        conclusion = "H4_BLOCKED_SIGNAL_INTRINSICALLY_WEAK"
        evidence_level = "H3_SIGNAL_DENSITY_ANALYZED"

    positive_best = next((row for row in positive_support if row["level"] == best["level"]), {})
    negative_low_best = next((row for row in negative_support if row["level"] == best["level"] and row["state"] == LOW_VALUE), {})
    negative_noobs_best = next((row for row in negative_support if row["level"] == best["level"] and row["state"] == NO_OBSERVABLE), {})
    negative_stability = max(
        _number(negative_low_best.get("repeated_state_bucket_rate")),
        _number(negative_noobs_best.get("repeated_state_bucket_rate")),
    )
    h4_decision = {
        "primary_conclusion": conclusion,
        "h4_gate_passed": h4_passed,
        "best_level": best["level"],
        "best_strategy": best["strategy"],
        "best_metrics": best,
        "gate_requirements": {
            "useful_exposure_improved": best["useful_route_exposure_delta"] > 0,
            "more_than_one_positive_replay_event": best["positive_replay_event_count"] > 1,
            "no_useful_suppression": best["useful_route_suppression_count"] == 0,
            "no_exploration_loss": best["exploration_loss_count"] == 0,
            "low_false_transfer": best_false_transfer.get("false_transfer_rate", 1.0) <= 0.05,
        },
    }
    summary = {
        "route_value_context_granularity_status": "COMPLETE",
        "primary_conclusion": conclusion,
        "system_fingerprint": _fingerprint(SYSTEM_PATHS),
        "observation_count": bucket_geometry["observation_count"],
        "current_context_bucket_count": bucket_geometry["bucket_count"],
        "single_observation_bucket_count": bucket_geometry["single_observation_bucket_count"],
        "single_observation_bucket_rate": bucket_geometry["single_observation_bucket_rate"],
        "multi_observation_bucket_count": bucket_geometry["multi_observation_bucket_count"],
        "current_mean_observations_per_bucket": bucket_geometry["mean_observations_per_bucket"],
        "highest_cardinality_context_fields": [
            row["field"] for row in sorted(field_cardinality, key=lambda item: item["cardinality"], reverse=True)[:3]
        ],
        "likely_over_specific_field_count": len(likely_over_specific),
        "abstraction_levels_tested": len(ABSTRACTION_LEVELS),
        "best_abstraction_level": best["level"],
        "best_abstraction_bucket_count": best_support.get("bucket_count", 0),
        "best_abstraction_mean_observations_per_bucket": best_support.get("mean_observations_per_bucket", 0),
        "useful_route_exposure_delta": best["useful_route_exposure_delta"],
        "no_observable_route_exposure_delta": best["no_observable_route_exposure_delta"],
        "low_value_route_exposure_delta": best["low_value_route_exposure_delta"],
        "unknown_route_retention_rate": best["unknown_route_retention_rate"],
        "useful_route_suppression_count": best["useful_route_suppression_count"],
        "exploration_loss_count": best["exploration_loss_count"],
        "false_transfer_rate": best_false_transfer.get("false_transfer_rate", best["false_transfer_rate"]),
        "positive_support_stability": positive_best.get("repeated_state_bucket_rate", 0),
        "negative_support_stability": negative_stability,
        "h4_gate_passed": h4_passed,
        "current_evidence_level": evidence_level,
        "behavioral_ab_eligible": False,
        "failed_p3_predictor_reactivated": False,
        "production_route_selection_changed": False,
        "production_route_order_changed": False,
        "production_route_admission_changed": False,
        "route_budget_changed": False,
        "next_action": (
            "close route-value behavioral integration unless a future observation campaign increases repeated contextual support"
            if not h4_passed
            else "design a separately authorized behavioral A/B gate"
        ),
        "git_commit": _git_value("rev-parse", "--short", "HEAD"),
        "python_version": platform.python_version(),
    }

    artifacts = {
        "bucket_geometry.json": bucket_geometry,
        "route_support_density.json": route_support,
        "context_field_cardinality.json": field_cardinality,
        "leave_one_field_out.json": leave_one_aggregate,
        "context_abstraction_contracts.json": abstraction_contracts,
        "abstraction_support_density.json": support_density,
        "abstraction_replay_matrix.json": replay_aggregate,
        "positive_support_stability.json": positive_support,
        "negative_support_stability.json": negative_support,
        "false_transfer_analysis.json": false_transfer,
        "h4_gate_decision.json": h4_decision,
        "route_value_context_granularity_report.md": _report(summary, field_cardinality),
        "summary.json": summary,
    }
    for name, payload in artifacts.items():
        _write(output_dir / name, payload)
    return {**summary, "output_dir": str(output_dir)}


def _report(summary: Mapping[str, Any], field_cardinality: list[dict[str, Any]]) -> str:
    fields = "\n".join(
        f"- `{row['field']}`: cardinality={row['cardinality']}, classification={','.join(row['classification'])}"
        for row in field_cardinality
    )
    return (
        "# Route-Value Context Granularity Forensic\n\n"
        f"Decision: `{summary['primary_conclusion']}`\n\n"
        f"Current bucket geometry: `{summary['current_context_bucket_count']}` buckets for "
        f"`{summary['observation_count']}` observations; single bucket rate "
        f"`{summary['single_observation_bucket_rate']}`.\n\n"
        f"Best abstraction: `{summary['best_abstraction_level']}` with useful exposure delta "
        f"`{summary['useful_route_exposure_delta']}` and false transfer rate "
        f"`{summary['false_transfer_rate']}`.\n\n"
        "## Context Fields\n\n"
        f"{fields}\n\n"
        "Production route selection, route ordering, route admission, and route budget were not changed.\n"
    )


if __name__ == "__main__":
    print(json.dumps(run_context_granularity(), indent=2, sort_keys=True))
