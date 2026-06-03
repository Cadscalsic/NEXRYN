from runtime.epistemic.contradiction_attribution_engine import (
    CONTRADICTION_SOURCE_WEIGHTS,
    ContradictionAttributionEngine,
)


contradiction_attribution_engine = ContradictionAttributionEngine()


__all__ = [
    "CONTRADICTION_SOURCE_WEIGHTS",
    "ContradictionAttributionEngine",
    "contradiction_attribution_engine",
]
