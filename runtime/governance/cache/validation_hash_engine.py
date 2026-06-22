import hashlib
import json


class ValidationHashEngine:

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

    def stable_value(self, value):

        if isinstance(value, dict):
            return {
                str(key): self.stable_value(item)
                for key, item in value.items()
                if key not in self.VOLATILE_KEYS
                and not str(key).endswith("_timestamp")
            }

        if isinstance(value, (list, tuple)):
            return [
                self.stable_value(item)
                for item in value
            ]

        return value

    def stable_hash(self, value):

        encoded = json.dumps(
            self.stable_value(value),
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(
            encoded.encode("utf-8")
        ).hexdigest()


validation_hash_engine = ValidationHashEngine()


__all__ = [
    "ValidationHashEngine",
    "validation_hash_engine",
]
