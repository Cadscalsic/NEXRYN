import json
from dataclasses import fields
from pathlib import Path

from core.truth.truth_record import TruthRecord
from runtime.semantics.concept_schema_validator import (
    concept_schema_validator,
)


class TruthRegistry:
    SCHEMA_VERSION = 1

    def __init__(self, storage_path=None):
        self.storage_path = (
            Path(storage_path)
            if storage_path
            else None
        )
        self._records = {}
        self._by_concept = {}
        self.hydrated_truth_count = 0
        self.last_persistence_error = None
        self.load()

    def _record_fields(self):
        return {
            item.name
            for item in fields(TruthRecord)
        }

    def _persist(self):
        if self.storage_path is None:
            return False
        temporary_path = self.storage_path.with_suffix(
            f"{self.storage_path.suffix}.tmp"
        )
        try:
            self.storage_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(
                    {
                        "schema_version": self.SCHEMA_VERSION,
                        "truths": self.all_truths(),
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
            record_fields = self._record_fields()
            for item in payload.get("truths", []):
                normalized, rejected = (
                    concept_schema_validator.normalize_item(
                        item,
                        record_type="truth_commitment",
                    )
                )
                if rejected:
                    continue
                record = TruthRecord(**{
                    key: value
                    for key, value in normalized.items()
                    if key in record_fields
                })
                self._records[record.truth_id] = record
                self._by_concept[record.concept] = record.truth_id
            self.hydrated_truth_count = len(self._records)
            self.last_persistence_error = None
            return self.hydrated_truth_count
        except (
            OSError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            self.last_persistence_error = repr(error)
            return 0

    def upsert(self, concept, **kwargs):
        normalized, rejected = concept_schema_validator.normalize_item(
            {"concept": concept},
            record_type="truth_commitment",
        )
        if rejected:
            raise ValueError(rejected["reason"])
        concept = normalized["concept"]
        previous = self.retrieve_record(concept)
        record = TruthRecord.create(
            concept=concept,
            truth_id=previous.truth_id if previous else None,
            created_at=previous.created_at if previous else kwargs.pop(
                "created_at",
                None,
            ),
            revision_count=(
                previous.revision_count + 1
                if previous
                else 0
            ),
            **kwargs,
        )
        self._records[record.truth_id] = record
        self._by_concept[record.concept] = record.truth_id
        self._persist()
        return record

    def retrieve_record(self, concept):
        truth_id = self._by_concept.get(str(concept))
        return self._records.get(truth_id)

    def retrieve_truth(self, concept):
        record = self.retrieve_record(concept)
        return record.as_dict() if record is not None else None

    def all_truths(self):
        return [
            record.as_dict()
            for record in self._records.values()
        ]

    def report(self):
        return {
            "system": "provisional_truth_registry",
            "phase": "7.0",
            "truths": self.all_truths(),
            "truth_count": len(self._records),
            "truth_state": "PROVISIONAL_TRUTH_COMMITMENT",
            "persistent_storage_enabled": self.storage_path is not None,
            "storage_path": (
                str(self.storage_path)
                if self.storage_path is not None
                else None
            ),
            "hydrated_truth_count": self.hydrated_truth_count,
            "last_persistence_error": self.last_persistence_error,
            "concept_schema_validation_enabled": True,
        }


__all__ = [
    "TruthRegistry",
]
