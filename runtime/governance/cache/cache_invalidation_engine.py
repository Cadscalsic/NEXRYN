"""Selective invalidation for governance cache snapshots."""

from __future__ import annotations

from typing import Any, Mapping


class GovernanceCacheInvalidationEngine:
    """Invalidate only when trusted continuity has actually changed."""

    HASH_FIELDS = [
        "truth_hash",
        "dependency_hash",
        "context_hash",
        "identity_hash",
    ]

    def evaluate(
        self,
        snapshot: Mapping[str, Any] | None,
        current_hashes: Mapping[str, Any],
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(snapshot, Mapping):
            return {
                "should_invalidate": True,
                "reasons": ["no_snapshot"],
            }
        runtime_context = runtime_context or {}
        reasons = []
        for key in self.HASH_FIELDS:
            if snapshot.get(key) != current_hashes.get(key):
                reasons.append(f"{key}_changed")
        if runtime_context.get("contradiction_review_required") is True:
            reasons.append("contradiction_appeared")
        current_continuity = float(
            runtime_context.get("identity_runtime_continuity", 1.0) or 0.0
        )
        snapshot_continuity = float(
            snapshot.get("identity_runtime_continuity", 0.0) or 0.0
        )
        if current_continuity < snapshot_continuity:
            reasons.append("identity_continuity_dropped")
        if runtime_context.get("concept_definition_changed") is True:
            reasons.append("concept_definition_changed")
        return {
            "should_invalidate": bool(reasons),
            "reasons": reasons,
        }


governance_cache_invalidation_engine = GovernanceCacheInvalidationEngine()


__all__ = [
    "GovernanceCacheInvalidationEngine",
    "governance_cache_invalidation_engine",
]
