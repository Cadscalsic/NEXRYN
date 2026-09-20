# ============================================
# NEXRYN COGNITIVE CACHE MANAGER
# ============================================

from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json
import builtins
from pathlib import Path
import time
from typing import Optional

from runtime.planning.cache_metrics import CacheMetrics


@dataclass(frozen=True)
class ConceptCacheKey:

    concept_name: str

    evidence_hash: str

    dependency_hash: str

    context_hash: str

    runtime_version: str


@dataclass
class CacheEntry:

    cache_key: ConceptCacheKey

    dependency_chain: Optional[list]

    explanation_path: Optional[list]

    validated_contexts: Optional[list]

    truth_commit_result: Optional[dict]

    process_semantic_model: Optional[dict]

    created_at: float

    last_accessed: float


class CognitiveCacheManager:
    _legacy_warning_printed_global = False

    VOLATILE_CONTEXT_KEYS = {
        "timestamp",
        "runtime_boot",
        "performance_report",
        "cache_metrics_report",
        "cognitive_cache_report",
        "pipeline_cache_report",
        "pipeline_cache_store_report",
        "runtime_metrics_report",
        "runtime_finalization_report",
        "finalization_report",
        "dependency_execution_trace",
        "dependency_reasoning_report",
        "telemetry_enabled",
        "execution_id",
        "runtime_id",
        "telemetry_id",
    }

    DEFAULT_CACHE_PATH = (
        Path(__file__).resolve().parents[1]
        / "cache"
        / "concept_cache.json"
    )

    def __init__(
        self,
        cache_path=None,
        persistence_enabled=True,
        max_load_bytes=25_000_000,
    ):

        self._cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.invalidations = 0
        self.reused_concepts = []
        self.invalidated_concepts = []
        self.cache_path = Path(cache_path or self.DEFAULT_CACHE_PATH)
        self.persistence_enabled = bool(persistence_enabled)
        self.max_load_bytes = int(max_load_bytes)
        self.loaded = False
        self.load_skipped = False
        self.load_skip_reason = None
        self.cache_load_time = 0.0
        self.cache_save_time = 0.0
        self._dirty = False

    def build_key(
        self,
        task_signature=None,
        concept_signature=None,
        dependency_hash=None,
        evidence_hash=None,
        context_hash=None,
        concept_version_hash=None,
        runtime_version="nexryn-alpha-1.4",
        artifact_type="generic",
    ):

        return json.dumps(
            {
                "task_signature": task_signature,
                "concept_signature": concept_signature,
                "dependency_hash": dependency_hash,
                "evidence_hash": evidence_hash,
                "context_hash": context_hash,
                "concept_version_hash": concept_version_hash,
                "runtime_version": runtime_version,
                "artifact_type": artifact_type,
            },
            sort_keys=True,
            default=str,
        )

    def lookup(self, cache_key):

        self._ensure_loaded()
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if self._entry_invalid(cache_key, entry):
                self.invalidate(
                    lambda key, _entry: key == cache_key
                )
                self.cache_misses += 1
                return None
            self.cache_hits += 1
            if isinstance(entry, CacheEntry):
                entry.last_accessed = time.time()
                self._dirty = True
                self._record_reused(entry.cache_key.concept_name)
                return deepcopy(entry)
            return deepcopy(entry["value"])

        self.cache_misses += 1
        return None

    def store(self, cache_key, value, metadata=None):

        self._cache[cache_key] = {
            "value": deepcopy(value),
            "metadata": deepcopy(metadata or {}),
            "stored_at": time.time(),
        }
        self._dirty = True
        return deepcopy(value)

    def concept_version_hash(
        self,
        evidence_hash,
        dependency_hash,
        context_hash,
    ):

        encoded = json.dumps(
            {
                "evidence_hash": evidence_hash,
                "dependency_hash": dependency_hash,
                "context_hash": context_hash,
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def stable_hash(self, value):

        encoded = json.dumps(
            self._stable_value(value),
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def stable_context_hash(self, runtime_context):

        return self.stable_hash(runtime_context or {})

    def concept_key(
        self,
        concept_name,
        evidence_hash,
        dependency_hash,
        context_hash,
        runtime_version="nexryn-alpha-1.4.4",
    ):

        return ConceptCacheKey(
            concept_name=str(concept_name),
            evidence_hash=str(evidence_hash),
            dependency_hash=str(dependency_hash),
            context_hash=str(context_hash),
            runtime_version=str(runtime_version),
        )

    def lookup_concept(self, cache_key):

        entry = self.lookup(cache_key)

        if isinstance(entry, CacheEntry):
            return entry

        return None

    def store_concept(
        self,
        cache_key,
        dependency_chain=None,
        explanation_path=None,
        validated_contexts=None,
        truth_commit_result=None,
        process_semantic_model=None,
    ):

        now = time.time()
        entry = CacheEntry(
            cache_key=cache_key,
            dependency_chain=deepcopy(dependency_chain),
            explanation_path=deepcopy(explanation_path),
            validated_contexts=deepcopy(validated_contexts),
            truth_commit_result=deepcopy(truth_commit_result),
            process_semantic_model=deepcopy(process_semantic_model),
            created_at=now,
            last_accessed=now,
        )
        self._cache[cache_key] = entry
        self._dirty = True
        return deepcopy(entry)

    def partial_lookup(self, cache_key, fields):

        entry = self.lookup_concept(cache_key)
        if entry is None:
            return None

        partial = {}
        for field in fields:
            if hasattr(entry, field):
                value = getattr(entry, field)
                if value is not None:
                    partial[field] = deepcopy(value)

        return partial or None

    def invalidate(self, predicate=None):

        self._ensure_loaded()
        if predicate is None:
            return 0

        keys = [
            key
            for key, entry in self._cache.items()
            if predicate(key, entry)
        ]
        for key in keys:
            entry = self._cache.get(key)
            if isinstance(entry, CacheEntry):
                self._record_invalidated(entry.cache_key.concept_name)
            self._cache.pop(key, None)
        self.invalidations += len(keys)
        if keys:
            self._dirty = True
        return len(keys)

    def load(self):

        if not self.persistence_enabled:
            return 0
        if self.loaded:
            return len(self._cache)

        started_at = time.perf_counter()
        try:
            if not self.cache_path.exists():
                self.loaded = True
                return 0
            if self.cache_path.stat().st_size > self.max_load_bytes:
                self._cache = {}
                self.loaded = True
                self.load_skipped = True
                self.load_skip_reason = "cache_file_too_large"
                self._warn_legacy_cache_detected()
                return 0
            with self.cache_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            entries = payload.get("entries", [])
            for item in entries:
                restored = self._deserialize_entry(item)
                if restored is not None:
                    key, value = restored
                    self._cache[key] = value
            self._dirty = False
            self.loaded = True
            return len(self._cache)
        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
            MemoryError,
        ):
            self._cache = {}
            self._dirty = False
            self.loaded = True
            self.load_skipped = True
            self.load_skip_reason = "cache_unreadable"
            return 0
        finally:
            self.cache_load_time = round(
                time.perf_counter() - started_at,
                6,
            )

    def save(self, force=False):

        if not self.persistence_enabled:
            return 0
        if not force and not self._dirty:
            return len(self._cache)

        started_at = time.perf_counter()
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "saved_at": time.time(),
            "entries": [
                self._serialize_entry(key, entry)
                for key, entry in self._cache.items()
            ],
        }
        with self.cache_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True, default=str)
        self._dirty = False
        self.cache_save_time = round(
            time.perf_counter() - started_at,
            6,
        )
        return len(self._cache)

    def metrics(self):

        total = self.cache_hits + self.cache_misses
        hit_rate = (
            self.cache_hits / total
            if total
            else 0.0
        )
        return CacheMetrics(
            cache_hits=self.cache_hits,
            cache_misses=self.cache_misses,
            invalidations=self.invalidations,
            hit_rate=round(hit_rate, 4),
            entry_count=len(self._cache),
            load_time=self.cache_load_time,
            save_time=self.cache_save_time,
            reuse_ratio=round(hit_rate, 4),
            persistence_enabled=self.persistence_enabled,
        )

    def build_report(self):

        metrics = self.metrics()
        return {
            "cache_hits": metrics.cache_hits,
            "cache_misses": metrics.cache_misses,
            "invalidations": metrics.invalidations,
            "hit_rate": metrics.hit_rate,
            "cache_hit_rate": metrics.hit_rate,
            "cache_entry_count": metrics.entry_count,
            "cache_load_time": metrics.load_time,
            "cache_save_time": metrics.save_time,
            "cache_reuse_ratio": metrics.reuse_ratio,
            "cache_persistence_enabled":
            metrics.persistence_enabled,
            "cache_loaded": self.loaded,
            "cache_load_skipped": self.load_skipped,
            "cache_load_skip_reason": self.load_skip_reason,
            "reused_concepts": list(self.reused_concepts),
            "invalidated_concepts": list(self.invalidated_concepts),
            "cache_entries": len(self._cache),
        }

    def _stable_value(self, value):

        if isinstance(value, dict):
            return {
                key: self._stable_value(item)
                for key, item in value.items()
                if key not in self.VOLATILE_CONTEXT_KEYS
                and not str(key).endswith("_timestamp")
            }
        if isinstance(value, (list, tuple)):
            return [
                self._stable_value(item)
                for item in value
            ]
        return value

    def _ensure_loaded(self):

        if not self.loaded and not self.load_skipped:
            self.load()

    def _warn_legacy_cache_detected(self):

        if (
            CognitiveCacheManager._legacy_warning_printed_global
            or getattr(builtins, "_nexryn_legacy_cache_warning", False)
        ):
            return
        print("Legacy concept_cache.json detected but not loaded during boot")
        CognitiveCacheManager._legacy_warning_printed_global = True
        builtins._nexryn_legacy_cache_warning = True

    def _entry_invalid(self, cache_key, entry):

        if isinstance(entry, CacheEntry):
            return entry.cache_key != cache_key
        if not isinstance(entry, dict):
            return False
        metadata = entry.get("metadata", {})
        if not metadata:
            return False
        version_hash = metadata.get("concept_version_hash")
        if not version_hash:
            return False
        expected = self.concept_version_hash(
            metadata.get("evidence_hash"),
            metadata.get("dependency_hash"),
            metadata.get("context_hash"),
        )
        return version_hash != expected

    def _serialize_entry(self, key, entry):

        if isinstance(entry, CacheEntry):
            return {
                "entry_type": "concept",
                "key": asdict(key),
                "value": {
                    "cache_key": asdict(entry.cache_key),
                    "dependency_chain": entry.dependency_chain,
                    "explanation_path": entry.explanation_path,
                    "validated_contexts": entry.validated_contexts,
                    "truth_commit_result": entry.truth_commit_result,
                    "process_semantic_model": entry.process_semantic_model,
                    "created_at": entry.created_at,
                    "last_accessed": entry.last_accessed,
                },
            }
        return {
            "entry_type": "artifact",
            "key": key,
            "value": entry,
        }

    def _deserialize_entry(self, item):

        entry_type = item.get("entry_type")
        if entry_type == "concept":
            key = ConceptCacheKey(**item["key"])
            value = item["value"]
            entry = CacheEntry(
                cache_key=ConceptCacheKey(**value["cache_key"]),
                dependency_chain=value.get("dependency_chain"),
                explanation_path=value.get("explanation_path"),
                validated_contexts=value.get("validated_contexts"),
                truth_commit_result=value.get("truth_commit_result"),
                process_semantic_model=value.get(
                    "process_semantic_model"
                ),
                created_at=value.get("created_at", time.time()),
                last_accessed=value.get("last_accessed", time.time()),
            )
            return key, entry
        if entry_type == "artifact":
            return item.get("key"), item.get("value")
        return None

    def _record_reused(self, concept_name):

        if concept_name not in self.reused_concepts:
            self.reused_concepts.append(concept_name)

    def _record_invalidated(self, concept_name):

        if concept_name not in self.invalidated_concepts:
            self.invalidated_concepts.append(concept_name)


cognitive_cache_manager = CognitiveCacheManager()
