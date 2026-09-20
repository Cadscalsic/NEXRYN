import json
from pathlib import Path

from runtime.governance.cache.dependency_version_tracker import (
    dependency_version_tracker,
)
from runtime.governance.cache.cache_invalidation_engine import (
    governance_cache_invalidation_engine,
)
from runtime.governance.cache.truth_snapshot import TruthSnapshot
from runtime.governance.cache.validation_hash_engine import (
    validation_hash_engine,
)


class GovernanceCache:

    DEFAULT_CACHE_PATH = (
        Path(__file__).resolve().parent
        / "governance_cache.json"
    )

    def __init__(self, cache_path=None):

        self.cache_path = Path(cache_path or self.DEFAULT_CACHE_PATH)
        self.snapshots = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.invalidation_count = 0
        self.recomputation_time_saved = 0.0
        self.load()

    def load(self):

        try:
            if not self.cache_path.exists():
                return 0
            with self.cache_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.snapshots = dict(payload.get("snapshots", {}))
            return len(self.snapshots)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            self.snapshots = {}
            return 0

    def save(self):

        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "snapshots": self.snapshots,
        }
        with self.cache_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True, default=str)
        return len(self.snapshots)

    def truth_hash(self, concept_record):

        return validation_hash_engine.stable_hash(concept_record or {})

    def current_hashes(self, runtime_context, concept_record):

        return {
            "truth_hash": self.truth_hash(concept_record),
            "dependency_hash":
            dependency_version_tracker.dependency_hash(runtime_context),
            "context_hash":
            dependency_version_tracker.context_hash(runtime_context),
            "identity_hash":
            dependency_version_tracker.identity_hash(runtime_context),
        }

    def lookup(self, concept_name, runtime_context, concept_record):

        snapshot = self.snapshots.get(str(concept_name))
        if not isinstance(snapshot, dict):
            self.cache_misses += 1
            return None, "no_snapshot"

        hashes = self.current_hashes(runtime_context, concept_record)
        invalidation = governance_cache_invalidation_engine.evaluate(
            snapshot,
            hashes,
            runtime_context,
        )
        if invalidation["should_invalidate"]:
            self.cache_misses += 1
            self.invalidation_count += 1
            return None, ",".join(invalidation["reasons"])

        self.cache_hits += 1
        return dict(snapshot), "stable_verified_continuity"

    def store(
        self,
        concept_name,
        runtime_context,
        concept_record,
        final_commit_state,
        identity_runtime_continuity,
        contextual_truth_score,
    ):

        hashes = self.current_hashes(runtime_context, concept_record)
        snapshot = TruthSnapshot.create(
            concept_name=concept_name,
            truth_hash=hashes["truth_hash"],
            dependency_hash=hashes["dependency_hash"],
            context_hash=hashes["context_hash"],
            identity_hash=hashes["identity_hash"],
            final_commit_state=final_commit_state,
            identity_runtime_continuity=identity_runtime_continuity,
            contextual_truth_score=contextual_truth_score,
        )
        self.snapshots[str(concept_name)] = snapshot.as_dict()
        self.save()
        return snapshot.as_dict()

    def add_time_saved(self, seconds):

        self.recomputation_time_saved += max(float(seconds or 0.0), 0.0)

    def build_report(self):

        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total if total else 0.0
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": round(hit_rate, 4),
            "cache_hit_rate": round(hit_rate, 4),
            "recomputation_time_saved":
            round(self.recomputation_time_saved, 4),
            "invalidation_count": self.invalidation_count,
            "cache_entry_count": len(self.snapshots),
            "truth_validation_mode":
            "CACHE_REUSE" if self.cache_hits else "FULL_VALIDATION",
        }


governance_cache = GovernanceCache()


__all__ = [
    "GovernanceCache",
    "governance_cache",
]
