LOCKED = "LOCKED"


CORE_TRUTHS = {
    "density_preservation": LOCKED,
    "symmetry_preservation": LOCKED,
}


class CoreTruthRegistry:
    """Defines the locked truths every new core candidate must respect."""

    def __init__(self, core_truths=None):
        self.core_truths = dict(
            CORE_TRUTHS
            if core_truths is None
            else core_truths
        )

    def is_locked(self, concept):
        return self.core_truths.get(str(concept)) == LOCKED

    def locked_truths(self, truth_registry):
        if truth_registry is None:
            return []
        return [
            {
                **truth,
                "core_truth_state": LOCKED,
            }
            for truth in truth_registry.active_truths()
            if self.is_locked(truth.get("concept"))
        ]

    def compatible_with_core_truths(self, comparisons):
        required = [
            comparison
            for comparison in comparisons
            if comparison.get("required_for_core_compatibility")
        ]
        return all(
            comparison.get(
                "core_compatibility_passed",
                comparison.get("passed", False),
            )
            for comparison in required
        )

    def report(self, truth_registry=None):
        active_locked_truths = self.locked_truths(truth_registry)
        return {
            "system": "core_truth_registry",
            "core_truths": dict(self.core_truths),
            "locked_truth_concepts": sorted(
                concept
                for concept, state in self.core_truths.items()
                if state == LOCKED
            ),
            "active_locked_truths": active_locked_truths,
            "active_locked_truth_count": len(active_locked_truths),
            "compatible_with_core_truths_required": True,
            "automatic_core_truth_rewrite_forbidden": True,
        }


core_truth_registry = CoreTruthRegistry()


__all__ = [
    "CORE_TRUTHS",
    "LOCKED",
    "CoreTruthRegistry",
    "core_truth_registry",
]
