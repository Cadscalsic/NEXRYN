from runtime.ambiguity_resolution_engine import AmbiguityResolutionEngine


class AmbiguityResolver(AmbiguityResolutionEngine):
    """Backward-compatible alias for ambiguity resolution."""

    compatibility_alias = True


__all__ = [
    "AmbiguityResolver",
]
