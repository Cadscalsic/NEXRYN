from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from runtime.cache.cache_keys import stable_hash
from runtime.cache.cache_serializer import CacheSerializer


CACHE_TYPES = {
    "knowledge",
    "truth",
    "strategy",
    "context",
    "program",
    "dependency_snapshot",
    "world_model",
    "semantic",
    "process_context",
    "transformation_sequence",
    "learned_heuristic",
}


@dataclass
class CacheStore:
    cache_type: str
    path: Path
    entries: dict[str, dict[str, Any]] = field(default_factory=dict)
    loaded: bool = False
    loader: Any = None

    def load_with_timeout(self, timeout_seconds: float | None = None) -> None:
        if self.loaded:
            return
        if self.loader is not None:
            self.loader(self)
        else:
            self.loaded = True


class CacheManager:
    def __init__(
        self,
        cache_dir: str | Path = "runtime/cache",
        auto_migrate: bool = False,
        enable_legacy_cache_migration: bool | None = None,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if enable_legacy_cache_migration is not None:
            auto_migrate = bool(enable_legacy_cache_migration)
        self.auto_migrate = bool(auto_migrate)
        self.serializer = CacheSerializer()
        self.cache_load_timeout_seconds = 0.25
        self.caches = {
            cache_type: CacheStore(
                cache_type,
                self.cache_dir / f"{cache_type}_cache.json",
                loader=self._load,
            )
            for cache_type in CACHE_TYPES
        }
        self.hits: dict[str, int] = {cache_type: 0 for cache_type in CACHE_TYPES}
        self.misses: dict[str, int] = {cache_type: 0 for cache_type in CACHE_TYPES}
        self.invalidated_entries = 0
        self.legacy_cache_detected = (
            self.cache_dir / "concept_cache.json"
        ).exists()
        self.legacy_cache_migration_skipped = (
            self.legacy_cache_detected and not self.auto_migrate
        )
        self.cache_boot_loaded = False
        self.cache_boot_skipped = True
        self.migration_completed = False
        if self.auto_migrate:
            self.migration_completed = bool(
                self.migrate_legacy_once().get("migration_completed")
            )

    def key(self, cache_type: str, **parts: Any) -> str:
        payload = {"cache_type": cache_type, **parts}
        return f"{cache_type}:{stable_hash(payload)}"

    def put(
        self,
        cache_type: str,
        key: str,
        value: Any,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        store = self._store(cache_type)
        if not store.loaded:
            self._load(store)
        store.entries[str(key)] = {
            "key": str(key),
            "cache_type": cache_type,
            "value": value,
            "metadata": metadata or {},
        }
        return {"stored": True, "key": str(key), "cache_type": cache_type}

    def get(
        self,
        cache_type: str,
        key: str,
        context: dict[str, Any] | None = None,
    ) -> Any:
        store = self._store(cache_type)
        if not store.loaded:
            self._load(store)
        entry = store.entries.get(str(key))
        if not entry:
            self.misses[cache_type] = self.misses.get(cache_type, 0) + 1
            return None
        value = entry.get("value")
        if not self._valid_for_context(cache_type, value, context or {}):
            self.invalidated_entries += 1
            self.misses[cache_type] = self.misses.get(cache_type, 0) + 1
            return None
        self.hits[cache_type] = self.hits.get(cache_type, 0) + 1
        return value

    def values(self, cache_type: str) -> list[Any]:
        store = self._store(cache_type)
        if not store.loaded:
            self._load(store)
        return [
            entry.get("value")
            for entry in store.entries.values()
            if isinstance(entry, dict)
        ]

    def flush(self) -> dict[str, Any]:
        written = 0
        for store in self.caches.values():
            if not store.loaded:
                continue
            payload = {"entries": store.entries}
            store.path.write_text(
                json.dumps(payload, sort_keys=True, default=str),
                encoding="utf-8",
            )
            written += 1
        return {"system": "adaptive_cache_flush", "files_written": written}

    def compact(self) -> dict[str, Any]:
        before = 0
        after = 0
        for store in self.caches.values():
            if not store.loaded:
                self._load(store)
            for entry in store.entries.values():
                before += len(json.dumps(entry, default=str))
                entry["value"] = self.serializer.compact(entry.get("value"))
                after += len(json.dumps(entry, default=str))
        return {
            **self.serializer.report(),
            "system": "adaptive_cache_compaction",
            "entries_compacted": sum(len(store.entries) for store in self.caches.values()),
            "compaction_ratio": round(after / max(before, 1), 4),
        }

    def migrate_legacy_once(self) -> dict[str, Any]:
        marker = self.cache_dir / ".adaptive_cache_migrated"
        if marker.exists():
            return {"migration_skipped": True, "reason": "already_migrated"}
        legacy_path = self.cache_dir / "concept_cache.json"
        if not legacy_path.exists():
            marker.write_text("no legacy cache found", encoding="utf-8")
            self.legacy_cache_migration_skipped = False
            return {"migration_completed": True, "legacy_entries": 0}
        try:
            payload = json.loads(legacy_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            payload = {}
        entries = payload.get("entries", [])
        if isinstance(entries, dict):
            entries = list(entries.values())
        migrated = 0
        for item in entries:
            if not isinstance(item, dict):
                continue
            value = item.get("value", {})
            cache_key = item.get("key", {})
            concept = (
                cache_key.get("concept_name")
                if isinstance(cache_key, dict)
                else None
            ) or value.get("concept") or "legacy"
            if value.get("truth_commit_result"):
                key = self.key("truth", concept=concept)
                self.put("truth", key, value["truth_commit_result"])
                migrated += 1
            if value.get("dependency_chain") or value.get("explanation_path"):
                key = self.key("dependency_snapshot", concept=concept)
                self.put(
                    "dependency_snapshot",
                    key,
                    {
                        "concept": concept,
                        "dependency_chain": value.get("dependency_chain", []),
                        "explanation_path": value.get("explanation_path", []),
                        "snapshot_state": "ACTIVE",
                    },
                )
                migrated += 1
        self.flush()
        marker.write_text("migrated", encoding="utf-8")
        self.legacy_cache_migration_skipped = False
        self.migration_completed = True
        return {
            "migration_completed": True,
            "legacy_entries": len(entries),
            "migrated_entries": migrated,
        }

    def boot_report(self) -> dict[str, Any]:
        return {
            "cache_boot_loaded": self.cache_boot_loaded,
            "cache_boot_skipped": self.cache_boot_skipped,
            "legacy_cache_detected": self.legacy_cache_detected,
            "legacy_cache_migration_skipped":
            self.legacy_cache_migration_skipped,
            "cache_migration_completed": self.migration_completed,
        }

    def report(self) -> dict[str, Any]:
        hits = sum(self.hits.values())
        misses = sum(self.misses.values())
        cache_size = sum(len(store.entries) for store in self.caches.values())
        report = {
            "system": "adaptive_cache_manager",
            "cache_hits": hits,
            "cache_misses": misses,
            "cache_hit_rate": round(hits / max(hits + misses, 1), 4),
            "reuse_rate": round(hits / max(hits + misses, 1), 4),
            "invalidated_entries": self.invalidated_entries,
            "estimated_compute_saved": round(hits * 0.5, 4),
            "estimated_runtime_saved": round(hits * 0.1, 4),
            "estimated_governance_saved": round(self.hits.get("truth", 0) * 0.1, 4),
            "estimated_dependency_saved": round(
                self.hits.get("dependency_snapshot", 0) * 0.2,
                4,
            ),
            "cache_size": cache_size,
            "compaction_ratio": 1.0,
            **self.boot_report(),
        }
        for cache_type in CACHE_TYPES:
            report[f"{cache_type}_hits"] = self.hits.get(cache_type, 0)
            report[f"{cache_type}_misses"] = self.misses.get(cache_type, 0)
        return report

    def _store(self, cache_type: str) -> CacheStore:
        cache_type = str(cache_type)
        if cache_type not in self.caches:
            self.caches[cache_type] = CacheStore(
                cache_type,
                self.cache_dir / f"{cache_type}_cache.json",
                loader=self._load,
            )
            self.hits.setdefault(cache_type, 0)
            self.misses.setdefault(cache_type, 0)
        return self.caches[cache_type]

    def _load(self, store: CacheStore) -> None:
        store.loaded = True
        if not store.path.exists():
            store.entries = {}
            return
        try:
            payload = json.loads(store.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            store.entries = {}
            return
        entries = payload.get("entries", payload)
        if isinstance(entries, list):
            store.entries = {
                str(item.get("key", index)): item
                for index, item in enumerate(entries)
                if isinstance(item, dict)
            }
        elif isinstance(entries, dict):
            store.entries = {
                str(key): (
                    item
                    if isinstance(item, dict) and "value" in item
                    else {"key": str(key), "value": item}
                )
                for key, item in entries.items()
            }
        else:
            store.entries = {}

    def _valid_for_context(
        self,
        cache_type: str,
        value: Any,
        context: dict[str, Any],
    ) -> bool:
        if context.get("identity_runtime_state") == "IDENTITY_RUNTIME_UNSTABLE":
            return False
        if context.get("identity_runtime_ready") is False:
            return False
        if context.get("truth_integrity_preserved") is False:
            return False
        if context.get("contradiction_review_required") is True:
            return False
        if context.get("ontology_violation") is True:
            return False
        if context.get("failed_gates") or context.get(
            "failed_identity_governance_gates"
        ):
            return False
        if cache_type == "truth" and isinstance(value, dict):
            return value.get("decision") == "TRUTH_COMMITTED" or value.get(
                "final_commit_state"
            ) == "LOCKED_TRUTH_PRESERVED"
        if cache_type == "dependency_snapshot" and isinstance(value, dict):
            return value.get("snapshot_state", "ACTIVE") == "ACTIVE"
        return True


__all__ = ["CacheManager", "CacheStore"]
