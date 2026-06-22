# ============================================
# NEXRYN CACHE METRICS
# ============================================

from dataclasses import dataclass


@dataclass
class CacheMetrics:

    cache_hits: int

    cache_misses: int

    invalidations: int

    hit_rate: float

    entry_count: int = 0

    load_time: float = 0.0

    save_time: float = 0.0

    reuse_ratio: float = 0.0

    persistence_enabled: bool = False
