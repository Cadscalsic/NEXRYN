"""Observation-only current-run persistent state authority delta."""

from __future__ import annotations

import copy
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
REPORT_TYPE = "CURRENT_RUN_STATE_AUTHORITY_DELTA_REPORT"
AUTHORITY = "OBSERVATION_ONLY"
BEHAVIORAL_AUTHORITY = "NONE"
DEFAULT_ARTIFACT_DIR = Path("runtime/artifacts/runtime_data/state_authority_delta")
MAX_ENTRIES_PER_STORE = 500
MAX_IDS_PER_STORE = 200


DEFAULT_STORE_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "store_id": "shared_cognitive_state",
        "domain": "SHARED_COGNITIVE_STATE",
        "path": "runtime/artifacts/runtime_data/shared_cognitive_state/latest.json",
        "path_type": "file",
        "mutation_class": "CACHE_UPDATE",
        "semantic_authority_owner": "PRODUCER_RUNTIME",
        "persistence_executor": "SharedCognitiveState.save",
        "writer_component": "runtime.state.shared_cognitive_state.SharedCognitiveState",
        "owner_file": "runtime/state/shared_cognitive_state.py",
        "owner_symbol": "SharedCognitiveState.save",
    },
    {
        "store_id": "evidence_plan_state",
        "domain": "EVIDENCE_PLAN_STATE",
        "path": "runtime/state/evidence_acquisition_plans",
        "path_type": "directory",
        "mutation_class": "EVIDENCE_PLAN_WRITE",
        "semantic_authority_owner": "EvidenceAcquisitionPlanStore",
        "persistence_executor": "EvidenceAcquisitionPlanStore.persist_plan",
        "writer_component": "runtime.evidence.evidence_plan_store.EvidenceAcquisitionPlanStore",
        "owner_file": "runtime/evidence/evidence_plan_store.py",
        "owner_symbol": "EvidenceAcquisitionPlanStore.persist_plan",
    },
    {
        "store_id": "truth_registry",
        "domain": "TRUTH_REGISTRY",
        "path": "runtime/memory/storage/truth_registry.json",
        "path_type": "file",
        "mutation_class": "TRUTH_COMMIT_WRITE",
        "semantic_authority_owner": "TruthRegistry",
        "persistence_executor": "TruthRegistry._persist",
        "writer_component": "runtime.truth_registry.truth_registry.TruthRegistry",
        "owner_file": "runtime/truth_registry/truth_registry.py",
        "owner_symbol": "TruthRegistry._persist",
    },
    {
        "store_id": "provisional_truth_registry",
        "domain": "TRUTH_REGISTRY",
        "path": "runtime/memory/storage/provisional_truth_registry.json",
        "path_type": "file",
        "mutation_class": "TRUTH_CANDIDATE_WRITE",
        "semantic_authority_owner": "ProvisionalTruthCommitEngine",
        "persistence_executor": "core.truth.truth_registry.TruthRegistry._persist",
        "writer_component": "core.truth.truth_registry.TruthRegistry",
        "owner_file": "core/truth/truth_registry.py",
        "owner_symbol": "TruthRegistry._persist",
    },
    {
        "store_id": "meta_supervisor_program_memory",
        "domain": "PROGRAM_MEMORY",
        "path": "runtime/memory/storage/meta_supervisor/program_memory.json",
        "path_type": "file",
        "mutation_class": "PROGRAM_MEMORY_WRITE",
        "semantic_authority_owner": "ProgramMemory",
        "persistence_executor": "ProgramMemory.save",
        "writer_component": "runtime.meta.supervisor.program_memory.ProgramMemory",
        "owner_file": "runtime/meta/supervisor/program_memory.py",
        "owner_symbol": "ProgramMemory.save",
    },
    {
        "store_id": "synthesis_program_memory",
        "domain": "PROGRAM_MEMORY",
        "path": "runtime/artifacts/runtime_data/programs/program_memory.json",
        "path_type": "file",
        "mutation_class": "PROGRAM_MEMORY_WRITE",
        "semantic_authority_owner": "ProgramSynthesisIntelligenceEngine",
        "persistence_executor": "ProgramMemoryStore",
        "writer_component": "runtime.synthesis.program_synthesis_intelligence_engine",
        "owner_file": "runtime/synthesis/program_synthesis_intelligence_engine.py",
        "owner_symbol": "program_memory_store",
    },
    {
        "store_id": "task_selection_memory",
        "domain": "TASK_SELECTION_MEMORY",
        "path": "runtime/cache/task_selection_memory.json",
        "path_type": "file",
        "mutation_class": "TASK_SELECTION_WRITE",
        "semantic_authority_owner": "TrainingAssistant",
        "persistence_executor": "TrainingAssistant._persist_selection_memory",
        "writer_component": "runtime.learning.training_assistant.TrainingAssistant",
        "owner_file": "runtime/learning/training_assistant.py",
        "owner_symbol": "TrainingAssistant._persist_selection_memory",
    },
    {
        "store_id": "training_assistant_state",
        "domain": "TASK_SELECTION_MEMORY",
        "path": "runtime/artifacts/runtime_data/training_assistant_state.json",
        "path_type": "file",
        "mutation_class": "TASK_SELECTION_WRITE",
        "semantic_authority_owner": "TrainingAssistant",
        "persistence_executor": "TrainingAssistant._persist",
        "writer_component": "runtime.learning.training_assistant.TrainingAssistant",
        "owner_file": "runtime/learning/training_assistant.py",
        "owner_symbol": "TrainingAssistant._persist",
    },
    {
        "store_id": "knowledge_replication_ledger",
        "domain": "KNOWLEDGE_STATE",
        "path": "runtime/artifacts/runtime_data/knowledge_replication_ledger.json",
        "path_type": "file",
        "mutation_class": "KNOWLEDGE_WRITE",
        "semantic_authority_owner": "KnowledgeReplicationLedger",
        "persistence_executor": "KnowledgeReplicationLedger._persist",
        "writer_component": "runtime.epistemic.knowledge_replication_ledger.KnowledgeReplicationLedger",
        "owner_file": "runtime/epistemic/knowledge_replication_ledger.py",
        "owner_symbol": "KnowledgeReplicationLedger._persist",
    },
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str)


def canonical_hash(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _resolve_path(path: str | Path, repository_root: str | Path | None) -> Path:
    resolved = Path(path)
    if resolved.is_absolute():
        return resolved
    return Path(repository_root or ".") / resolved


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def _file_hash(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _stable_id(payload: Any, path: Path, root: Path) -> str:
    if isinstance(payload, dict):
        for key in (
            "id",
            "plan_id",
            "truth_id",
            "concept",
            "program_id",
            "task_id",
            "record_id",
            "candidate_id",
            "execution_id",
            "run_id",
        ):
            value = payload.get(key)
            if value not in (None, "", "Not Available"):
                return str(value)
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _entry_payloads(payload: Any, path: Path, root: Path) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {_stable_id(payload, path, root): {"value_type": type(payload).__name__}}
    for key in ("truths", "programs", "records", "entries", "items"):
        values = payload.get(key)
        if isinstance(values, list):
            return {
                _stable_id(item, path, root): item
                for item in values[:MAX_ENTRIES_PER_STORE]
                if isinstance(item, dict)
            }
    if all(isinstance(value, dict) for value in payload.values()) and payload:
        return {
            str(key): value
            for key, value in list(payload.items())[:MAX_ENTRIES_PER_STORE]
        }
    return {_stable_id(payload, path, root): payload}


def _run_id_values(payload: Any) -> set[str]:
    values: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in {"run_id", "source_run_id", "execution_run_id"} and value:
                run_value = str(value)
                if not run_value.startswith("selection-"):
                    values.add(run_value)
            elif isinstance(value, (dict, list)):
                values.update(_run_id_values(value))
    elif isinstance(payload, list):
        for item in payload[:25]:
            values.update(_run_id_values(item))
    return values


def _bounded_entry(path: Path, root: Path, payload: Any) -> dict[str, Any]:
    run_ids = sorted(_run_id_values(payload))[:10]
    return {
        "stable_id": _stable_id(payload, path, root),
        "path": path.as_posix(),
        "content_hash": canonical_hash(payload),
        "run_ids": run_ids,
        "bounded_metadata": _bounded_metadata(payload),
    }


def _bounded_metadata(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"value_type": type(payload).__name__}
    keys = (
        "schema_version",
        "status",
        "state",
        "lifecycle_state",
        "consumption_state",
        "truth_authority",
        "trust_authority",
        "graduation_authority",
        "execution_authority",
        "validation_state",
        "integrity_verified",
        "plan_id",
        "program_id",
        "task_id",
        "concept",
        "run_id",
        "source_run_id",
    )
    return {key: payload.get(key) for key in keys if key in payload}


def _capture_store(store: dict[str, Any], repository_root: str | Path | None) -> dict[str, Any]:
    started = time.perf_counter()
    path = _resolve_path(store["path"], repository_root)
    entries: dict[str, dict[str, Any]] = {}
    exists = path.exists()
    path_type = store.get("path_type", "file")
    if exists and path.is_file():
        payload = _load_json(path)
        root = path.parent
        for stable_id, item in _entry_payloads(payload, path, root).items():
            entries[stable_id] = _bounded_entry(path, root, item)
    elif exists and path.is_dir():
        root = path
        for child in sorted(path.rglob("*.json"))[:MAX_ENTRIES_PER_STORE]:
            if child.name.endswith(".tmp"):
                continue
            payload = _load_json(child)
            if payload is None:
                continue
            for stable_id, item in _entry_payloads(payload, child, root).items():
                entry = _bounded_entry(child, root, item)
                entries[stable_id] = entry
    return {
        **{key: value for key, value in store.items() if key != "path"},
        "path": str(path),
        "path_type": path_type,
        "exists": exists,
        "file_hash": _file_hash(path) if exists and path.is_file() else None,
        "entry_count": len(entries),
        "stable_identifiers": sorted(entries)[:MAX_IDS_PER_STORE],
        "entries": dict(sorted(entries.items())),
        "capture_duration_seconds": round(time.perf_counter() - started, 6),
    }


def capture_state_authority_snapshot(
    *,
    run_id: str,
    execution_plan_id: str | None = None,
    task_id: str | None = None,
    repository_root: str | Path | None = None,
    store_definitions: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    stores = [
        _capture_store(dict(store), repository_root)
        for store in (store_definitions or DEFAULT_STORE_DEFINITIONS)
    ]
    snapshot = {
        "snapshot_id": canonical_hash({
            "run_id": run_id,
            "execution_plan_id": execution_plan_id,
            "task_id": task_id,
            "stores": [
                {
                    "store_id": store["store_id"],
                    "entry_count": store["entry_count"],
                    "stable_identifiers": store["stable_identifiers"],
                    "file_hash": store.get("file_hash"),
                }
                for store in stores
            ],
        })[:16],
        "run_id": run_id,
        "execution_plan_id": execution_plan_id,
        "task_id": task_id,
        "captured_at": _now(),
        "authority": AUTHORITY,
        "behavioral_authority": BEHAVIORAL_AUTHORITY,
        "stores": stores,
        "snapshot_duration_seconds": round(time.perf_counter() - started, 6),
    }
    snapshot["snapshot_hash"] = canonical_hash(snapshot)
    return snapshot


def _store_map(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        store.get("store_id"): store
        for store in snapshot.get("stores", [])
        if isinstance(store, dict) and store.get("store_id")
    }


def _entry_delta(before: dict[str, Any] | None, after: dict[str, Any] | None) -> str:
    if before is None and after is not None:
        return "ADDED"
    if before is not None and after is None:
        return "REMOVED"
    if before and after and before.get("content_hash") != after.get("content_hash"):
        return "MODIFIED"
    return "UNCHANGED"


def derive_state_authority_delta(pre_run_snapshot: dict[str, Any], post_run_snapshot: dict[str, Any]) -> dict[str, Any]:
    pre_stores = _store_map(pre_run_snapshot)
    post_stores = _store_map(post_run_snapshot)
    stores: dict[str, Any] = {}
    for store_id in sorted(set(pre_stores) | set(post_stores)):
        before_store = pre_stores.get(store_id, {})
        after_store = post_stores.get(store_id, {})
        before_entries = before_store.get("entries", {})
        after_entries = after_store.get("entries", {})
        entries = {}
        counts = {"ADDED": 0, "REMOVED": 0, "MODIFIED": 0, "UNCHANGED": 0}
        for stable_id in sorted(set(before_entries) | set(after_entries)):
            state_delta = _entry_delta(before_entries.get(stable_id), after_entries.get(stable_id))
            counts[state_delta] += 1
            entries[stable_id] = {
                "stable_id": stable_id,
                "state_delta": state_delta,
                "current_run_state": "HISTORICAL_PRESENT" if state_delta == "UNCHANGED" else "CURRENT_RUN_MUTATED",
                "pre_ref": before_entries.get(stable_id),
                "post_ref": after_entries.get(stable_id),
            }
        stores[store_id] = {
            "store_id": store_id,
            "domain": after_store.get("domain") or before_store.get("domain"),
            "semantic_authority_owner": after_store.get("semantic_authority_owner") or before_store.get("semantic_authority_owner"),
            "persistence_executor": after_store.get("persistence_executor") or before_store.get("persistence_executor"),
            "counts": counts,
            "entries": entries,
        }
    return {
        "delta_id": canonical_hash({"pre": pre_run_snapshot.get("snapshot_hash"), "post": post_run_snapshot.get("snapshot_hash")})[:16],
        "stores": stores,
    }


def _operation_for(store: dict[str, Any], mutation_class: str) -> str:
    store_id = store.get("store_id")
    if mutation_class == "TRUTH_CANDIDATE_WRITE":
        return "truth_candidate_creation_or_update"
    if mutation_class == "TRUTH_COMMIT_WRITE":
        return "truth_commit_or_registry_update"
    if mutation_class == "EVIDENCE_PLAN_WRITE":
        return "evidence_plan_creation_or_lifecycle_update"
    if mutation_class == "PROGRAM_MEMORY_WRITE":
        return "program_memory_persistence"
    if mutation_class == "KNOWLEDGE_WRITE":
        return "knowledge_storage_or_replication_ledger_update"
    if mutation_class == "TASK_SELECTION_WRITE":
        return "task_selection_memory_update"
    if store_id == "shared_cognitive_state":
        return "shared_state_publication"
    return "persistent_state_update"


def _current_run_binding(run_id: str, entry: dict[str, Any]) -> tuple[str, bool]:
    run_ids = set(entry.get("run_ids") or [])
    if not run_ids:
        return "NO_OBJECT_RUN_ID_OBSERVED", True
    if run_id in run_ids:
        return "VALID", True
    return "REJECTED_RUN_MISMATCH", False


def build_mutation_observations(
    *,
    run_id: str,
    pre_run_snapshot: dict[str, Any],
    post_run_snapshot: dict[str, Any],
    derived_state_delta: dict[str, Any],
) -> list[dict[str, Any]]:
    post_stores = _store_map(post_run_snapshot)
    observations = []
    for store_id, store_delta in derived_state_delta.get("stores", {}).items():
        store = post_stores.get(store_id, {})
        for stable_id, entry_delta in store_delta.get("entries", {}).items():
            if entry_delta.get("state_delta") == "UNCHANGED":
                continue
            post_ref = entry_delta.get("post_ref") or entry_delta.get("pre_ref") or {}
            binding, included = _current_run_binding(run_id, post_ref)
            mutation_class = store.get("mutation_class", "OTHER_PERSISTENT_WRITE")
            observations.append({
                "mutation_id": canonical_hash({
                    "run_id": run_id,
                    "store_id": store_id,
                    "stable_id": stable_id,
                    "state_delta": entry_delta.get("state_delta"),
                })[:16],
                "run_id": run_id,
                "domain": store.get("domain"),
                "owner_component": store.get("writer_component"),
                "owner_file": store.get("owner_file"),
                "owner_symbol": store.get("owner_symbol"),
                "operation": _operation_for(store, mutation_class),
                "mutation_class": mutation_class,
                "target_store": store_id,
                "target_object_id": stable_id,
                "target_path": post_ref.get("path"),
                "authority_type": "OBSERVATION_ONLY_ATTRIBUTION",
                "authority_scope": "CURRENT_RUN_PERSISTENT_STATE_DELTA",
                "authority_grant": "NONE",
                "requested": False,
                "granted": False,
                "exercised": False,
                "persistence_attempted": True,
                "persistence_succeeded": entry_delta.get("state_delta") in {"ADDED", "MODIFIED", "REMOVED"},
                "semantic_authority_owner": store.get("semantic_authority_owner"),
                "persistence_executor": store.get("persistence_executor"),
                "pre_ref": entry_delta.get("pre_ref"),
                "post_ref": entry_delta.get("post_ref"),
                "current_run_state": entry_delta.get("current_run_state"),
                "current_run_binding": binding,
                "included_in_current_run_attribution": included,
                "truth_commitment_claimed": False,
                "evidence_acceptance_claimed": False,
                "learning_effect_claimed": False,
                "knowledge_promotion_claimed": False,
            })
    return observations


def _summary(observations: list[dict[str, Any]]) -> dict[str, Any]:
    by_domain: dict[str, int] = {}
    by_class: dict[str, int] = {}
    rejected = 0
    for item in observations:
        by_domain[item.get("domain") or "UNKNOWN"] = by_domain.get(item.get("domain") or "UNKNOWN", 0) + 1
        by_class[item.get("mutation_class") or "UNKNOWN"] = by_class.get(item.get("mutation_class") or "UNKNOWN", 0) + 1
        if item.get("included_in_current_run_attribution") is False:
            rejected += 1
    return {
        "mutation_count": len(observations),
        "by_domain": dict(sorted(by_domain.items())),
        "by_mutation_class": dict(sorted(by_class.items())),
        "rejected_run_mismatch_count": rejected,
        "semantic_authority_owner_observable": all(item.get("semantic_authority_owner") for item in observations),
        "persistence_executor_observable": all(item.get("persistence_executor") for item in observations),
        "unauthorized_persistent_mutation": False,
        "critical_authority_conflict": False,
    }


def build_current_run_state_authority_delta_report(
    *,
    run_id: str,
    execution_plan_id: str | None = None,
    task_id: str | None = None,
    pre_run_snapshot: dict[str, Any],
    repository_root: str | Path | None = None,
    store_definitions: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    pre_snapshot = copy.deepcopy(pre_run_snapshot)
    post_started = time.perf_counter()
    post_snapshot = capture_state_authority_snapshot(
        run_id=run_id,
        execution_plan_id=execution_plan_id,
        task_id=task_id,
        repository_root=repository_root,
        store_definitions=store_definitions,
    )
    post_time = round(time.perf_counter() - post_started, 6)
    delta_started = time.perf_counter()
    derived = derive_state_authority_delta(pre_snapshot, post_snapshot)
    observations = build_mutation_observations(
        run_id=run_id,
        pre_run_snapshot=pre_snapshot,
        post_run_snapshot=post_snapshot,
        derived_state_delta=derived,
    )
    delta_time = round(time.perf_counter() - delta_started, 6)
    summary = _summary(observations)
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "run_id": run_id,
        "execution_plan_id": execution_plan_id,
        "task_id": task_id,
        "authority": AUTHORITY,
        "behavioral_authority": BEHAVIORAL_AUTHORITY,
        "pre_run_snapshot": pre_snapshot,
        "mutation_observations": observations,
        "post_run_snapshot": post_snapshot,
        "derived_state_delta": derived,
        "authority_attribution_summary": summary,
        "observation_complete": True,
        "completeness_reason": "PRE_AND_POST_SNAPSHOTS_CAPTURED",
        "observation_contract": "PRE_RUN_SNAPSHOT_TO_CURRENT_RUN_MUTATION_OBSERVATIONS_TO_POST_RUN_SNAPSHOT",
        "observation_artifact_excluded_from_cognitive_delta": True,
        "cognitive_consumer_count": 0,
        "performance": {
            "pre_snapshot_time_seconds": pre_snapshot.get("snapshot_duration_seconds"),
            "mutation_capture_overhead_seconds": 0.0,
            "post_snapshot_time_seconds": post_time,
            "delta_derivation_time_seconds": delta_time,
            "serialization_time_seconds": 0.0,
            "artifact_size_bytes": 0,
            "total_observation_time_seconds": round(time.perf_counter() - started, 6),
        },
    }
    report["report_hash"] = canonical_hash({key: value for key, value in report.items() if key != "report_hash"})
    return report


def persist_current_run_state_authority_delta_report(
    report: dict[str, Any],
    *,
    artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR,
) -> dict[str, Any]:
    started = time.perf_counter()
    target_dir = Path(artifact_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    run_id = str(report.get("run_id") or "unknown").replace(":", "_").replace("/", "_").replace("\\", "_")
    path = target_dir / f"current_run_state_authority_delta_{run_id}.json"
    report["artifact_path"] = str(path)
    latest = target_dir / "latest.json"
    report["latest_artifact_path"] = str(latest)
    report.setdefault("performance", {})["serialization_time_seconds"] = 0.0
    report["performance"]["artifact_size_bytes"] = 0
    encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True, default=str)
    report["artifact_size_bytes"] = len((encoded + "\n").encode("utf-8"))
    report["performance"]["artifact_size_bytes"] = report["artifact_size_bytes"]
    report["performance"]["serialization_time_seconds"] = round(
        time.perf_counter() - started,
        6,
    )
    encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True, default=str)
    path.write_text(encoded + "\n", encoding="utf-8")
    latest.write_text(encoded + "\n", encoding="utf-8")
    actual_size = path.stat().st_size
    if actual_size != report["artifact_size_bytes"]:
        report["artifact_size_bytes"] = actual_size
        report["performance"]["artifact_size_bytes"] = actual_size
        encoded = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True, default=str)
        path.write_text(encoded + "\n", encoding="utf-8")
        latest.write_text(encoded + "\n", encoding="utf-8")
    return report


def finalize_current_run_state_authority_delta(
    *,
    run_id: str,
    execution_plan_id: str | None = None,
    task_id: str | None = None,
    pre_run_snapshot: dict[str, Any] | None,
    repository_root: str | Path | None = None,
    store_definitions: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
    artifact_dir: str | Path = DEFAULT_ARTIFACT_DIR,
) -> dict[str, Any]:
    try:
        if not isinstance(pre_run_snapshot, dict):
            pre_run_snapshot = {
                "run_id": run_id,
                "snapshot_error": "PRE_RUN_SNAPSHOT_NOT_AVAILABLE",
                "stores": [],
            }
        report = build_current_run_state_authority_delta_report(
            run_id=run_id,
            execution_plan_id=execution_plan_id,
            task_id=task_id,
            pre_run_snapshot=pre_run_snapshot,
            repository_root=repository_root,
            store_definitions=store_definitions,
        )
        return persist_current_run_state_authority_delta_report(report, artifact_dir=artifact_dir)
    except Exception as error:
        return {
            "schema_version": SCHEMA_VERSION,
            "report_type": REPORT_TYPE,
            "run_id": run_id,
            "execution_plan_id": execution_plan_id,
            "task_id": task_id,
            "authority": AUTHORITY,
            "behavioral_authority": BEHAVIORAL_AUTHORITY,
            "observation_complete": False,
            "completeness_reason": "OBSERVATION_FAILED",
            "observation_error": repr(error),
            "observation_failure_preserves_task_execution": True,
            "mutation_observations": [],
            "derived_state_delta": {"stores": {}},
            "authority_attribution_summary": {
                "mutation_count": 0,
                "unauthorized_persistent_mutation": False,
                "critical_authority_conflict": False,
            },
            "cognitive_consumer_count": 0,
        }


__all__ = [
    "AUTHORITY",
    "BEHAVIORAL_AUTHORITY",
    "DEFAULT_ARTIFACT_DIR",
    "DEFAULT_STORE_DEFINITIONS",
    "REPORT_TYPE",
    "SCHEMA_VERSION",
    "build_current_run_state_authority_delta_report",
    "build_mutation_observations",
    "canonical_hash",
    "capture_state_authority_snapshot",
    "derive_state_authority_delta",
    "finalize_current_run_state_authority_delta",
    "persist_current_run_state_authority_delta_report",
]
