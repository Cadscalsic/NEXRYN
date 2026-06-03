import json
from dataclasses import fields
from pathlib import Path

from runtime.truth_registry.truth_index import TruthIndex
from runtime.truth_registry.truth_lineage_graph import TruthLineageGraph
from runtime.truth_registry.truth_record import TruthRecord, utc_timestamp
from core.epistemic_models import clamp
from runtime.semantics.concept_schema_validator import (
    concept_schema_validator,
)


class TruthRegistry:
    SCHEMA_VERSION = 1

    def __init__(self, storage_path=None):
        self._records = {}
        self.index = TruthIndex()
        self.lineage_graph = TruthLineageGraph()
        self.storage_path = (
            Path(storage_path)
            if storage_path
            else None
        )
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
            payload = {
                "schema_version": self.SCHEMA_VERSION,
                "truths": self.all_truths(),
            }
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(
                    payload,
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
            records = payload.get("truths", [])
            record_fields = self._record_fields()
            for item in records:
                normalized, rejected = (
                    concept_schema_validator.normalize_item(
                        item,
                        record_type="truth_commitment",
                    )
                )
                if rejected or not isinstance(normalized, dict):
                    continue
                record = TruthRecord(**{
                    key: value
                    for key, value in normalized.items()
                    if key in record_fields
                })
                self._records[record.truth_id] = record
                self.index.add(record)
                self.lineage_graph.add(
                    record.truth_id,
                    record.parent_truths,
                )
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

    def _verification_event(self, record, decision, reasons):
        return {
            "decision": decision,
            "reasons": list(reasons),
            "revision": record.revision,
            "timestamp": record.reviewed_at,
        }

    def commit_truth(
        self,
        concept,
        claim,
        evidence_strength,
        causal_alignment,
        contradiction_score,
        confidence,
        trial_count,
        parent_truths=None,
        evidence_sources=None,
        evidence=None,
        causal_history=None,
        generalization_score=0.0,
        identity_impact=None,
        metadata=None,
        decision="TRUTH_COMMITTED",
        reasons=None,
    ):
        normalized, rejected = concept_schema_validator.normalize_item(
            {"concept": concept, "claim": claim},
            record_type="truth_commitment",
        )
        if rejected:
            raise ValueError(rejected["reason"])
        concept = normalized["concept"]
        claim = normalized["claim"]
        previous = self.retrieve_record(concept)
        timestamp = utc_timestamp()
        parent_truths = list(parent_truths or [])
        evidence_sources = sorted(set(evidence_sources or []))
        causal_history = self._merge_history(
            previous.causal_history if previous else [],
            causal_history or [],
        )
        record = TruthRecord.create(
            **(
                {"truth_id": previous.truth_id}
                if previous
                else {}
            ),
            concept=concept,
            claim=claim,
            status="ACTIVE",
            evidence_strength=evidence_strength,
            calibrated_confidence=confidence,
            contradiction_score=contradiction_score,
            causal_alignment=causal_alignment,
            trial_count=trial_count,
            creation_time=previous.creation_time if previous else timestamp,
            reviewed_at=timestamp,
            commit_timestamp=timestamp,
            lineage={
                "parent_truths": parent_truths,
                "evidence_sources": evidence_sources,
            },
            evidence=list(evidence or []),
            causal_history=causal_history,
            generalization_score=clamp(generalization_score),
            identity_impact=dict(identity_impact or {}),
            parent_truths=parent_truths,
            evidence_sources=evidence_sources,
            verification_history=(
                list(previous.verification_history)
                if previous
                else []
            ),
            revision=previous.revision + 1 if previous else 1,
            reusable=True,
            metadata=dict(metadata or {}),
        )
        record.verification_history.append(
            self._verification_event(record, decision, reasons or [])
        )
        self._records[record.truth_id] = record
        self.index.add(record)
        self.lineage_graph.add(record.truth_id, record.parent_truths)
        self._persist()
        return record

    def _merge_history(self, existing, additions):
        merged = list(existing)
        for item in additions:
            if item not in merged:
                merged.append(item)
        return merged

    def revoke_truth(self, concept, decision="TRUTH_REVOKED", reasons=None):
        record = self.retrieve_record(concept)
        if record is None:
            return None
        record.status = "REVOKED"
        record.reusable = False
        record.reviewed_at = utc_timestamp()
        record.revision += 1
        record.verification_history.append(
            self._verification_event(record, decision, reasons or [])
        )
        self._persist()
        return record

    def reinforce_truth(
        self,
        concept,
        confidence=None,
        evidence_strength=None,
        generalization_score=None,
        evidence=None,
        causal_history=None,
        reasons=None,
    ):
        record = self.retrieve_record(concept)
        if record is None:
            return None
        record.calibrated_confidence = max(
            record.calibrated_confidence,
            clamp(confidence)
            if confidence is not None
            else record.calibrated_confidence,
        )
        record.evidence_strength = max(
            record.evidence_strength,
            clamp(evidence_strength)
            if evidence_strength is not None
            else record.evidence_strength,
        )
        record.generalization_score = max(
            record.generalization_score,
            clamp(generalization_score)
            if generalization_score is not None
            else record.generalization_score,
        )
        record.evidence = self._merge_history(
            record.evidence,
            evidence or [],
        )
        record.causal_history = self._merge_history(
            record.causal_history,
            causal_history or [],
        )
        record.reviewed_at = utc_timestamp()
        record.revision += 1
        record.verification_history.append(
            self._verification_event(
                record,
                "TRUTH_REINFORCED",
                reasons or [],
            )
        )
        self._persist()
        return record

    def retrieve_record(self, concept):
        truth_id = self.index.truth_id_for(concept)
        return self._records.get(truth_id)

    def retrieve_truth(self, concept):
        record = self.retrieve_record(concept)
        return record.as_dict() if record is not None else None

    def find_related_truths(self, concept):
        records = [
            self._records[truth_id]
            for truth_id in self.index.related_truth_ids(concept)
            if truth_id in self._records
        ]
        return [
            record.as_dict()
            for record in sorted(
                records,
                key=lambda item: item.calibrated_confidence,
                reverse=True,
            )
        ]

    def rank_truths_by_confidence(self):
        return [
            record.as_dict()
            for record in sorted(
                self._records.values(),
                key=lambda item: item.calibrated_confidence,
                reverse=True,
            )
        ]

    def active_truths(self):
        return [
            record.as_dict()
            for record in self._records.values()
            if record.status == "ACTIVE" and record.reusable
        ]

    def all_truths(self):
        return [
            record.as_dict()
            for record in self._records.values()
        ]

    def report(self):
        return {
            "system": "truth_registry",
            "phase": "7.0",
            "truths": self.all_truths(),
            "active_truths": self.active_truths(),
            "truth_count": len(self._records),
            "active_truth_count": len(self.active_truths()),
            "lineage_enabled": True,
            "causal_history_enabled": True,
            "identity_impact_tracking_enabled": True,
            "generalization_score_tracking_enabled": True,
            "retrieval_enabled": True,
            "concept_schema_validation_enabled": True,
            "concept_schema": "nexryn_concept_v1",
            "persistent_storage_enabled": self.storage_path is not None,
            "storage_path": (
                str(self.storage_path)
                if self.storage_path is not None
                else None
            ),
            "hydrated_truth_count": self.hydrated_truth_count,
            "last_persistence_error": self.last_persistence_error,
            "truth_lineage_graph": self.lineage_graph.report(),
        }
