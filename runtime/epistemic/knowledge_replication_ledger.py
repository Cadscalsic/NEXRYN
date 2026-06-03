import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from core.epistemic_models import clamp


def unwrap_context_value(value):
    while (
        isinstance(value, dict)
        and "value" in value
        and set(value).issubset({"value", "priority", "timestamp"})
    ):
        value = value["value"]
    return value


def normalize_task_id(task_path):
    return str(unwrap_context_value(task_path)).replace("\\", "/")


@dataclass(frozen=True)
class ReplicationRecord:
    concept: str
    task_id: str
    task_path: str
    success: bool
    causal_alignment: float
    contradiction_score: float
    confidence: float
    timestamp: str
    conditions: dict = field(default_factory=dict)
    failure_reason: str = ""
    reliability: float = 0.0
    semantic_consistency: float = 0.0

    def as_dict(self):
        return asdict(self)


class KnowledgeReplicationLedger:
    SCHEMA_VERSION = 1

    def __init__(
        self,
        maximum_replication_bonus=0.125,
        storage_path=None,
    ):
        self.maximum_replication_bonus = clamp(
            maximum_replication_bonus,
            0.0,
            0.25,
        )
        self.storage_path = (
            Path(storage_path)
            if storage_path
            else None
        )
        self._records = {}
        self._task_keys = set()
        self.hydrated_record_count = 0
        self.last_persistence_error = None
        self.load()

    def _persist(self):
        if self.storage_path is None:
            return False
        temporary_path = self.storage_path.with_suffix(
            f"{self.storage_path.suffix}.tmp"
        )
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(
                    {
                        "schema_version": self.SCHEMA_VERSION,
                        "records": [
                            record.as_dict()
                            for records in self._records.values()
                            for record in records
                        ],
                    },
                    file,
                    indent=2,
                    ensure_ascii=True,
                )
            temporary_path.replace(self.storage_path)
            self.last_persistence_error = None
            return True
        except (OSError, TypeError, ValueError) as error:
            self.last_persistence_error = repr(error)
            return False

    def load(self):
        if self.storage_path is None or not self.storage_path.exists():
            return 0
        try:
            with self.storage_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
            records = payload.get("records", [])
            for item in records:
                self._add_record(
                    ReplicationRecord(**item),
                    persist=False,
                )
            self.hydrated_record_count = sum(
                len(records)
                for records in self._records.values()
            )
            self.last_persistence_error = None
            return self.hydrated_record_count
        except (
            OSError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            self.last_persistence_error = repr(error)
            return 0

    def _task_key(self, concept, task_id):
        return (
            f"{str(unwrap_context_value(concept))}:"
            f"{normalize_task_id(task_id)}"
        )

    def add_record(self, record=None, **kwargs):
        if record is None:
            record = ReplicationRecord(**kwargs)
        elif isinstance(record, dict):
            record = ReplicationRecord(**record)
        if not isinstance(record, ReplicationRecord):
            raise TypeError(
                "record must be a ReplicationRecord object or mapping"
            )

        return self._add_record(record)

    def _add_record(self, record, persist=True):
        concept = str(unwrap_context_value(record.concept))
        task_id = normalize_task_id(record.task_id)
        key = self._task_key(concept, task_id)
        if key in self._task_keys:
            return False

        normalized = ReplicationRecord(
            concept=concept,
            task_id=task_id,
            task_path=str(unwrap_context_value(record.task_path)),
            success=bool(record.success),
            causal_alignment=clamp(record.causal_alignment),
            contradiction_score=clamp(record.contradiction_score),
            confidence=clamp(record.confidence),
            timestamp=str(record.timestamp),
            conditions=dict(record.conditions or {}),
            failure_reason=str(record.failure_reason or ""),
            reliability=clamp(record.reliability),
            semantic_consistency=clamp(record.semantic_consistency),
        )
        self._task_keys.add(key)
        self._records.setdefault(normalized.concept, []).append(normalized)
        if persist:
            self._persist()
        return True

    def has_task(self, concept, task_id):
        return self._task_key(concept, task_id) in self._task_keys

    def get_concept_records(self, concept):
        return list(self._records.get(concept, []))

    def get_replication_count(self, concept):
        return len(self.get_concept_records(concept))

    def get_observed_task_ids(self):
        return sorted({
            record.task_id
            for records in self._records.values()
            for record in records
        })

    def get_cross_task_support(self, concept):
        records = self.get_concept_records(concept)
        if not records:
            return 0.0
        return clamp(
            sum(record.confidence for record in records)
            / len(records)
        )

    def get_independent_success_rate(self, concept):
        records = self.get_concept_records(concept)
        if not records:
            return 0.0
        return clamp(
            sum(record.success for record in records)
            / len(records)
        )

    def get_replication_bonus(self, concept):
        count = self.get_replication_count(concept)
        quality = min(
            self.get_cross_task_support(concept),
            self.get_independent_success_rate(concept),
        )
        return clamp(
            min(count, 5) * 0.025 * quality,
            0.0,
            self.maximum_replication_bonus,
        )

    def evidence_exports(self):
        return [
            {
                "concept": record.concept,
                "source": "independent_execution_replication",
                "support_score": record.confidence,
                "contradiction_score": record.contradiction_score,
                "reliability": (
                    record.reliability
                    if record.reliability
                    else clamp(0.68 + record.confidence * 0.18)
                ),
                "causal_alignment": record.causal_alignment,
                "semantic_consistency": (
                    record.semantic_consistency
                    if record.semantic_consistency
                    else record.confidence
                ),
                "observed_at": record.timestamp,
                "metadata": {
                    "evidence_id":
                    f"cross_task_replication:{record.concept}:{record.task_id}",
                    "task_id": record.task_id,
                    "task_path": record.task_path,
                    "collector": "knowledge_replication_ledger_hydration",
                    "independent_task": True,
                    "replication_is_evidence_not_truth": True,
                    "hydrated_from_persistent_ledger": True,
                    "conditions": dict(record.conditions),
                    "failure_reason": record.failure_reason,
                },
            }
            for records in self._records.values()
            for record in records
        ]

    def concept_report(self, concept):
        records = self.get_concept_records(concept)
        return {
            "concept": concept,
            "used_task_count": len(records),
            "concept_used_task_count": len(records),
            "used_task_count_scope": "concept_specific",
            "used_task_ids": [
                record.task_id
                for record in records
            ],
            "independent_replications": len(records),
            "cross_task_support": self.get_cross_task_support(concept),
            "independent_success_rate":
            self.get_independent_success_rate(concept),
            "replication_bonus": self.get_replication_bonus(concept),
            "records": [
                record.as_dict()
                for record in records
            ],
        }

    def report(self):
        observed_task_ids = self.get_observed_task_ids()
        return {
            "system": "knowledge_replication_ledger",
            "concepts": [
                self.concept_report(concept)
                for concept in sorted(self._records)
            ],
            "record_count": sum(
                len(records)
                for records in self._records.values()
            ),
            "observed_task_count": len(observed_task_ids),
            "observed_task_ids": observed_task_ids,
            "persistent_storage_enabled": self.storage_path is not None,
            "storage_path": (
                str(self.storage_path)
                if self.storage_path is not None
                else None
            ),
            "hydrated_record_count": self.hydrated_record_count,
            "last_persistence_error": self.last_persistence_error,
            "duplicate_task_replication_forbidden": True,
            "replication_is_evidence_not_truth": True,
        }


def utc_timestamp():
    return datetime.utcnow().isoformat()


__all__ = [
    "KnowledgeReplicationLedger",
    "ReplicationRecord",
    "normalize_task_id",
    "unwrap_context_value",
    "utc_timestamp",
]
