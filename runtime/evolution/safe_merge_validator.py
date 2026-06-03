DERIVED_STRATEGY_PREFIXES = {
    "adaptive",
    "contextual",
    "dynamic",
    "evolved",
    "hybrid",
    "recursive",
    "structural",
}


class SafeMergeValidator:
    """Requires causal maturity before derived strategy merges."""

    def _is_derived(self, strategy_name, strategy_data):
        hypothesis = strategy_data.get("hypothesis", {})
        prefix = str(strategy_name).split("_", 1)[0]
        return (
            prefix in DERIVED_STRATEGY_PREFIXES
            or hypothesis.get("mutation_applied", False) is True
            or bool(hypothesis.get("parent_strategy"))
            or hypothesis.get("evolved", False) is True
        )

    def evaluate(self, first, second, first_data=None, second_data=None):
        first_data = first_data if isinstance(first_data, dict) else {}
        second_data = second_data if isinstance(second_data, dict) else {}
        derived_merge = (
            self._is_derived(first, first_data)
            or self._is_derived(second, second_data)
        )
        causal_support_ready = (
            first_data.get("causal_support_ready", False) is True
            and second_data.get("causal_support_ready", False) is True
        )
        merge_allowed = not derived_merge or causal_support_ready
        return {
            "system": "safe_merge_validator",
            "merge_allowed": merge_allowed,
            "derived_merge": derived_merge,
            "causal_support_ready": causal_support_ready,
            "reason": (
                "merge_allowed"
                if merge_allowed
                else "derived_strategy_causal_support_required"
            ),
            "automatic_derived_merge_forbidden_without_causal_support": True,
        }


__all__ = [
    "SafeMergeValidator",
]
