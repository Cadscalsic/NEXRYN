from runtime.epistemic.causal_failure_analyzer import CausalFailureAnalyzer


class CounterexampleEngine(CausalFailureAnalyzer):
    """Backward-compatible alias for causal counterexample analysis."""

    compatibility_alias = True


__all__ = [
    "CounterexampleEngine",
]
