from __future__ import annotations

import hashlib
import json
from typing import Any


VOLATILE_KEYS = {
    "timestamp",
    "last_validation_timestamp",
    "performance_report",
    "cache_metrics_report",
    "cognitive_cache_report",
    "governance_cache_report",
    "locked_truth_report",
    "learning_saturation_report",
}


def stable_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): stable_value(item)
            for key, item in value.items()
            if key not in VOLATILE_KEYS
            and not str(key).endswith("_timestamp")
        }
    if isinstance(value, (list, tuple)):
        return [stable_value(item) for item in value]
    return value


def stable_hash(value: Any) -> str:
    encoded = json.dumps(
        stable_value(value),
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


__all__ = ["stable_hash", "stable_value"]
