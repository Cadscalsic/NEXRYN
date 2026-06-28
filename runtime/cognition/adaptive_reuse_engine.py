"""Conservative adaptive cognition reuse for validated runtime artifacts."""

from __future__ import annotations

import time
from typing import Any

from runtime.cache.cache_keys import stable_hash
from runtime.cache.cache_manager import CacheManager


REUSE_TYPES = (
    "truth",
    "strategy",
    "context",
    "process_context",
    "dependency_snapshot",
    "program",
    "transformation_sequence",
    "world_model",
    "semantic_abstraction",
    "learned_heuristic",
)


class AdaptiveReuseEngine:
    def __init__(
        self,
        cache_manager: CacheManager | None = None,
        semantic_drift_threshold: float = 0.10,
        contradiction_threshold: float = 0.10,
        context_compatibility_threshold: float = 0.80,
        dependency_compatibility_threshold: float = 0.80,
        world_model_compatibility_threshold: float = 0.80,
    ):
        self.cache_manager = cache_manager or CacheManager(auto_migrate=False)
        self.thresholds = {
            "semantic_drift": semantic_drift_threshold,
            "effective_contradiction": contradiction_threshold,
            "context_compatibility": context_compatibility_threshold,
            "dependency_compatibility": dependency_compatibility_threshold,
            "world_model_compatibility": world_model_compatibility_threshold,
        }
        self.counters = {f"{name}_hits": 0 for name in REUSE_TYPES}
        self.counters.update({f"{name}_misses": 0 for name in REUSE_TYPES})
        self.counters.update({
            "cache_hits": 0,
            "cache_misses": 0,
            "estimated_compute_saved": 0.0,
            "estimated_runtime_saved": 0.0,
            "estimated_governance_saved": 0.0,
            "estimated_dependency_saved": 0.0,
        })
        self.reused_assets: list[dict[str, Any]] = []
        self.missed_opportunities: list[dict[str, Any]] = []

    def evaluate_reuse(self, runtime_context: dict[str, Any] | None = None) -> dict[str, Any]:
        started_at = time.perf_counter()
        runtime_context = runtime_context if isinstance(runtime_context, dict) else {}
        eligible, reason = self._eligible(runtime_context)
        result = {
            "system": "adaptive_reuse_engine",
            "eligible": eligible,
            "eligibility_reason": reason,
            "reused_assets": {},
            "skip_redundant_reasoning": False,
            "dependency_reasoning_skipped": False,
        }
        if not eligible:
            self._record_miss("truth", reason)
            result.update(self.report())
            result["evaluation_time_seconds"] = round(time.perf_counter() - started_at, 4)
            return result

        reuse_calls = [
            ("truth", self.reuse_truth),
            ("strategy", self.reuse_strategy),
            ("context", self.reuse_context),
            ("program", self.reuse_program),
            ("dependency_snapshot", self.reuse_dependency_snapshot),
            ("world_model", self.reuse_world_model),
            ("semantic_abstraction", self.reuse_semantic_abstraction),
            ("learned_heuristic", self.reuse_learned_heuristic),
            ("transformation_sequence", self.reuse_transformation_sequence),
            ("process_context", self.reuse_process_context),
        ]
        for reuse_type, reuse_call in reuse_calls:
            asset = reuse_call(runtime_context)
            if asset is not None:
                result["reused_assets"][reuse_type] = asset

        result["skip_redundant_reasoning"] = bool(result["reused_assets"])
        result["dependency_reasoning_skipped"] = "dependency_snapshot" in result["reused_assets"]
        result.update(self.report())
        result["evaluation_time_seconds"] = round(time.perf_counter() - started_at, 4)
        return result

    def reuse_truth(self, runtime_context: dict[str, Any] | None = None):
        runtime_context = runtime_context if isinstance(runtime_context, dict) else {}
        candidates = runtime_context.get("truth_commitments") or runtime_context.get(
            "reusable_truth_commitments"
        )
        for truth in self._iter_candidates(candidates):
            if not self._truth_preserved(truth):
                continue
            concept = self._concept(truth, runtime_context, "truth")
            key = self.cache_manager.key(
                "truth",
                concept=concept,
                truth_signature=stable_hash(truth),
            )
            self.cache_manager.put(
                "truth",
                key=key,
                value=truth,
                metadata=self._metadata(runtime_context, concept),
            )
            cached = self.cache_manager.get("truth", key=key, context=runtime_context)
            if cached is not None:
                return self._record_hit("truth", concept, cached, 1.25, 0.20)
        return self._lookup_any("truth", runtime_context, 1.25, 0.20)

    def reuse_strategy(self, runtime_context: dict[str, Any] | None = None):
        return self._lookup_any("strategy", runtime_context, 1.0, 0.18)

    def reuse_context(self, runtime_context: dict[str, Any] | None = None):
        return self._lookup_any("context", runtime_context, 0.75, 0.15)

    def reuse_program(self, runtime_context: dict[str, Any] | None = None):
        return self._lookup_any("program", runtime_context, 1.5, 0.30)

    def reuse_dependency_snapshot(self, runtime_context: dict[str, Any] | None = None):
        return self._lookup_any("dependency_snapshot", runtime_context, 1.0, 0.25)

    def reuse_world_model(self, runtime_context: dict[str, Any] | None = None):
        return self._lookup_any("world_model", runtime_context, 0.9, 0.20)

    def reuse_semantic_abstraction(self, runtime_context: dict[str, Any] | None = None):
        return self._lookup_any("semantic", runtime_context, 0.6, 0.12, counter_type="semantic_abstraction")

    def reuse_learned_heuristic(self, runtime_context: dict[str, Any] | None = None):
        return self._lookup_any("knowledge", runtime_context, 0.5, 0.10, counter_type="learned_heuristic")

    def reuse_transformation_sequence(self, runtime_context: dict[str, Any] | None = None):
        return self._lookup_any("program", runtime_context, 0.8, 0.16, counter_type="transformation_sequence")

    def reuse_process_context(self, runtime_context: dict[str, Any] | None = None):
        return self._lookup_any("context", runtime_context, 0.5, 0.10, counter_type="process_context")

    def report(self) -> dict[str, Any]:
        hits = int(self.counters["cache_hits"])
        misses = int(self.counters["cache_misses"])
        total = hits + misses
        return {
            **self.counters,
            "reuse_rate": round(hits / total, 4) if total else 0.0,
            "top_reused_assets": self.reused_assets[-10:],
            "reuse_opportunities_missed": self.missed_opportunities[-10:],
        }

    def _lookup_any(
        self,
        cache_type: str,
        runtime_context: dict[str, Any] | None,
        compute_saved: float,
        runtime_saved: float,
        counter_type: str | None = None,
    ):
        runtime_context = runtime_context if isinstance(runtime_context, dict) else {}
        counter_type = counter_type or cache_type
        store = self.cache_manager.caches.get(cache_type)
        if store is None:
            return self._record_miss(counter_type, "cache_unavailable")
        store.load_with_timeout(self.cache_manager.cache_load_timeout_seconds)
        concept = self._concept(runtime_context, runtime_context, cache_type)
        candidate_keys = [
            key
            for key, entry in store.entries.items()
            if self._entry_matches(entry, concept)
        ]
        if not candidate_keys:
            candidate_keys = list(store.entries.keys())[:1]
        for key in candidate_keys:
            value = self.cache_manager.get(cache_type, key=key, context=runtime_context)
            if value is not None:
                return self._record_hit(
                    counter_type,
                    self._concept(value, runtime_context, cache_type),
                    value,
                    compute_saved,
                    runtime_saved,
                )
        return self._record_miss(counter_type, "no_compatible_validated_asset")

    def _eligible(self, context: dict[str, Any]) -> tuple[bool, str]:
        identity_state = context.get("identity_runtime_state")
        identity_ready = context.get("identity_runtime_ready")
        if identity_state not in {None, "IDENTITY_RUNTIME_STABLE"}:
            return False, "identity_runtime_unstable"
        if identity_ready is not True:
            return False, "identity_runtime_not_ready"
        if self._number(context.get("semantic_drift"), 0.0) > self.thresholds["semantic_drift"]:
            return False, "semantic_drift_above_threshold"
        contradiction = self._number(
            context.get("effective_contradiction", context.get("effective_contradiction_score")),
            0.0,
        )
        if contradiction > self.thresholds["effective_contradiction"]:
            return False, "effective_contradiction_above_threshold"
        if context.get("failed_gates") or context.get("failed_identity_governance_gates"):
            return False, "failed_governance_gates"
        if context.get("contradiction_review_required") is True:
            return False, "contradiction_review_active"
        if context.get("truth_integrity_preserved") is False:
            return False, "truth_integrity_not_preserved"
        if self._number(context.get("context_compatibility"), 1.0) < self.thresholds["context_compatibility"]:
            return False, "context_incompatible"
        if self._number(context.get("dependency_compatibility"), 1.0) < self.thresholds["dependency_compatibility"]:
            return False, "dependency_incompatible"
        if self._number(context.get("world_model_compatibility"), 1.0) < self.thresholds["world_model_compatibility"]:
            return False, "world_model_incompatible"
        return True, "eligible"

    def _record_hit(self, reuse_type, concept, value, compute_saved, runtime_saved):
        self.counters[f"{reuse_type}_hits"] += 1
        self.counters["cache_hits"] += 1
        self.counters["estimated_compute_saved"] = round(
            self.counters["estimated_compute_saved"] + compute_saved,
            4,
        )
        self.counters["estimated_runtime_saved"] = round(
            self.counters["estimated_runtime_saved"] + runtime_saved,
            4,
        )
        if reuse_type == "dependency_snapshot":
            self.counters["estimated_dependency_saved"] = round(
                self.counters["estimated_dependency_saved"] + runtime_saved,
                4,
            )
        if reuse_type in {"truth", "strategy", "program", "context"}:
            self.counters["estimated_governance_saved"] = round(
                self.counters["estimated_governance_saved"] + runtime_saved / 2,
                4,
            )
        self.reused_assets.append({
            "reuse_type": reuse_type,
            "concept": concept,
        })
        return value

    def _record_miss(self, reuse_type, reason):
        self.counters[f"{reuse_type}_misses"] += 1
        self.counters["cache_misses"] += 1
        self.missed_opportunities.append({
            "reuse_type": reuse_type,
            "reason": reason,
        })
        return None

    def _metadata(self, context, concept):
        return {
            "concept": concept,
            "identity_runtime_state": context.get("identity_runtime_state"),
            "identity_runtime_ready": context.get("identity_runtime_ready"),
            "semantic_drift": context.get("semantic_drift", 0.0),
            "effective_contradiction": context.get("effective_contradiction", 0.0),
            "context_compatibility": context.get("context_compatibility", 1.0),
            "truth_integrity_preserved": context.get("truth_integrity_preserved", True),
            "contradiction_review_required": context.get("contradiction_review_required", False),
        }

    def _entry_matches(self, entry, concept):
        if not concept:
            return True
        metadata = entry.get("metadata", {}) if isinstance(entry, dict) else {}
        value = entry.get("value", {}) if isinstance(entry, dict) else {}
        return concept in {
            metadata.get("concept"),
            value.get("concept") if isinstance(value, dict) else None,
            value.get("concept_name") if isinstance(value, dict) else None,
        }

    def _truth_preserved(self, truth):
        if not isinstance(truth, dict):
            return False
        return (
            truth.get("decision") == "TRUTH_COMMITTED"
            and truth.get("final_commit_state") == "LOCKED_TRUTH_PRESERVED"
        ) or truth.get("truth_state") == "LOCKED_TRUTH_PRESERVED"

    def _iter_candidates(self, value):
        if isinstance(value, dict):
            yield value
            for item in value.values():
                if isinstance(item, dict):
                    yield item
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item

    def _concept(self, value, context, fallback):
        if isinstance(value, dict):
            return (
                value.get("concept")
                or value.get("concept_name")
                or value.get("task_concept")
                or context.get("concept")
                or fallback
            )
        return context.get("concept") or fallback

    def _number(self, value, default):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default


__all__ = ["AdaptiveReuseEngine"]
