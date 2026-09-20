# ============================================
# NEXRYN CACHE INVALIDATION ENGINE
# ============================================


class CacheInvalidationEngine:

    def should_invalidate(
        self,
        previous_metadata,
        current_metadata,
    ):

        previous_metadata = previous_metadata or {}
        current_metadata = current_metadata or {}

        invalidation_reasons = []

        for key in (
            "evidence_hash",
            "dependency_hash",
            "context_hash",
            "concept_version_hash",
        ):
            if (
                key in previous_metadata
                or key in current_metadata
            ) and previous_metadata.get(key) != current_metadata.get(key):
                invalidation_reasons.append(f"{key}_changed")

        return {
            "should_invalidate": bool(invalidation_reasons),
            "reasons": invalidation_reasons,
        }

    def concept_version_changed(
        self,
        previous_metadata,
        current_metadata,
    ):

        previous_metadata = previous_metadata or {}
        current_metadata = current_metadata or {}
        return (
            previous_metadata.get("concept_version_hash")
            != current_metadata.get("concept_version_hash")
        )

    def invalidate_changed(
        self,
        cache_manager,
        current_metadata,
    ):

        def changed(_key, entry):
            if hasattr(entry, "cache_key"):
                previous = {
                    "evidence_hash": entry.cache_key.evidence_hash,
                    "dependency_hash": entry.cache_key.dependency_hash,
                    "context_hash": entry.cache_key.context_hash,
                    "runtime_version": entry.cache_key.runtime_version,
                    "concept_version_hash":
                    cache_manager.concept_version_hash(
                        entry.cache_key.evidence_hash,
                        entry.cache_key.dependency_hash,
                        entry.cache_key.context_hash,
                    ),
                }
            else:
                previous = entry.get("metadata", {})
            return self.should_invalidate(
                previous,
                current_metadata,
            )["should_invalidate"]

        return cache_manager.invalidate(changed)

    def invalidate_concepts(
        self,
        cache_manager,
        concept_names,
    ):

        concept_names = set(concept_names or [])
        if not concept_names:
            return 0

        def matches_concept(_key, entry):
            return (
                hasattr(entry, "cache_key")
                and entry.cache_key.concept_name in concept_names
            )

        return cache_manager.invalidate(matches_concept)


cache_invalidation_engine = CacheInvalidationEngine()
