# ============================================
# NEXRYN PERFORMANCE OPTIMIZER
# ============================================


class PerformanceOptimizer:

    def lookup_or_compute(
        self,
        cache_manager,
        cache_key,
        compute,
        metadata=None,
    ):

        cached = cache_manager.lookup(cache_key)
        if cached is not None:
            return cached, {
                "cache_state": "hit",
                "recompute": False,
            }

        value = compute()
        cache_manager.store(
            cache_key,
            value,
            metadata=metadata,
        )
        return value, {
            "cache_state": "miss",
            "recompute": "full",
        }


performance_optimizer = PerformanceOptimizer()
