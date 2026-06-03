import json
from pathlib import Path

from core.epistemic_models import clamp
from core.causality.causal_support_score import (
    calculate_causal_support_score,
)


class CausalEvidenceAccumulator:
    """Accumulates repeated causal edge observations before core admission."""

    def __init__(
        self,
        minimum_supporting_observations=3,
        storage_path=None,
    ):
        self.minimum_supporting_observations = max(
            int(minimum_supporting_observations),
            1,
        )
        self.storage_path = (
            Path(storage_path)
            if storage_path
            else None
        )
        self._records = {}
        self._load()

    def _persist(self):
        if self.storage_path is None:
            return
        temporary_path = self.storage_path.with_suffix(
            f"{self.storage_path.suffix}.tmp"
        )
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(
                    {
                        "schema_version": 1,
                        "minimum_supporting_observations":
                        self.minimum_supporting_observations,
                        "records": self._records,
                    },
                    file,
                    indent=2,
                    sort_keys=True,
                )
            temporary_path.replace(self.storage_path)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    def _load(self):
        if self.storage_path is None or not self.storage_path.exists():
            return
        with self.storage_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        self._records = {
            str(key): {
                "source": str(record.get("source", "")),
                "target": str(record.get("target", "")),
                "observation_count":
                int(record.get("observation_count", 0)),
                "supporting_observation_count":
                int(record.get("supporting_observation_count", 0)),
                "conflicting_observation_count":
                int(record.get("conflicting_observation_count", 0)),
                "cumulative_causal_strength":
                float(record.get("cumulative_causal_strength", 0.0)),
            }
            for key, record in payload.get("records", {}).items()
            if isinstance(record, dict)
        }

    def _key(self, source, target):
        return f"{source}->{target}"

    def observe(
        self,
        source,
        target,
        causal_strength,
        minimum_causal_strength,
    ):
        key = self._key(source, target)
        record = self._records.setdefault(key, {
            "source": source,
            "target": target,
            "observation_count": 0,
            "supporting_observation_count": 0,
            "conflicting_observation_count": 0,
            "cumulative_causal_strength": 0.0,
        })
        causal_strength = clamp(causal_strength)
        record["observation_count"] += 1
        record["cumulative_causal_strength"] += causal_strength
        if causal_strength >= minimum_causal_strength:
            record["supporting_observation_count"] += 1
        else:
            record["conflicting_observation_count"] += 1
        self._persist()
        return self.report_for(source, target)

    def report_for(self, source, target):
        record = self._records.get(
            self._key(source, target),
            {
                "source": source,
                "target": target,
                "observation_count": 0,
                "supporting_observation_count": 0,
                "conflicting_observation_count": 0,
                "cumulative_causal_strength": 0.0,
            },
        )
        observation_count = record["observation_count"]
        supporting_count = record["supporting_observation_count"]
        average_strength = (
            record["cumulative_causal_strength"] / observation_count
            if observation_count
            else 0.0
        )
        support_score = calculate_causal_support_score(
            supporting_count,
            observation_count,
            self.minimum_supporting_observations,
        )
        causal_support_score = support_score["causal_support_score"]
        return {
            **record,
            **support_score,
            "average_causal_strength": round(average_strength, 4),
            "minimum_supporting_observations":
            self.minimum_supporting_observations,
            "remaining_supporting_observations": max(
                self.minimum_supporting_observations - supporting_count,
                0,
            ),
            "causal_support_score": causal_support_score,
            "causal_support_ready": causal_support_score >= 1.0,
        }

    def report(self):
        return {
            "system": "causal_evidence_accumulator",
            "minimum_supporting_observations":
            self.minimum_supporting_observations,
            "persistent_storage_enabled":
            self.storage_path is not None,
            "storage_path": (
                str(self.storage_path)
                if self.storage_path is not None
                else None
            ),
            "relationships": [
                self.report_for(
                    record["source"],
                    record["target"],
                )
                for record in self._records.values()
            ],
        }


__all__ = [
    "CausalEvidenceAccumulator",
]
