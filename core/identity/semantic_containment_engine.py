class SemanticContainmentEngine:
    """Blocks truth integration that repeats a remembered unsafe merge."""

    def _failure_memory(self, context):
        return context.get(
            "cognitive_failure_memory",
            context.get("cognitive_failure_memory_report", {}),
        )

    def _sources_for(self, concept, context):
        sources = context.get(
            "truth_candidate_semantic_sources",
            context.get("semantic_merge_sources", []),
        )
        if isinstance(sources, dict):
            sources = sources.get(concept, [])
        if isinstance(sources, str):
            sources = sources.split("::")
        return [
            str(source)
            for source in sources
            if source
        ]

    def _unsafe_pairs(self, context):
        memory = self._failure_memory(context)
        failures = list(memory.get("failures", []))
        latest_failure = memory.get("latest_failure", {})
        if latest_failure:
            failures.append(latest_failure)

        pairs = set()
        for failure in failures:
            if not isinstance(failure, dict):
                continue
            collapse_source = str(failure.get("collapse_source", ""))
            if (
                failure.get("contradiction_type") != "unsafe_merge"
                or "::" not in collapse_source
            ):
                continue
            left, right = collapse_source.split("::", 1)
            pairs.add(frozenset([left, right]))
        return pairs

    def evaluate(self, concept, context=None):
        context = context if isinstance(context, dict) else {}
        sources = self._sources_for(concept, context)
        proposed_pair = (
            frozenset(sources[:2])
            if len(sources) >= 2
            else None
        )
        unsafe_pairs = self._unsafe_pairs(context)
        matched_unsafe_merge = (
            proposed_pair in unsafe_pairs
            if proposed_pair is not None
            else False
        )

        return {
            "system": "semantic_containment_engine",
            "concept": concept,
            "proposed_merge_sources": sources,
            "unsafe_merge_detected": matched_unsafe_merge,
            "containment_active": matched_unsafe_merge,
            "integration_allowed": not matched_unsafe_merge,
            "containment_state": (
                "UNSAFE_MERGE_CONTAINED"
                if matched_unsafe_merge
                else "SEMANTIC_CONTAINMENT_CLEAR"
            ),
            "blocked_collapse_source": (
                "::".join(sources[:2])
                if matched_unsafe_merge
                else None
            ),
        }


semantic_containment_engine = SemanticContainmentEngine()


__all__ = [
    "SemanticContainmentEngine",
    "semantic_containment_engine",
]
