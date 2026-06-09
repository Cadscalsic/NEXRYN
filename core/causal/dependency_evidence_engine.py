from copy import deepcopy
from datetime import datetime

from core.epistemic_models import clamp


class DependencyEvidenceEngine:
    """Evidence ledger for dependency support, transfer, and review."""

    def __init__(self):
        self.evidence_ledger = {}
        self.confidence_history = {}
        self.context_history = {}
        self.support_thresholds = {
            "promoted_confidence": 0.85,
            "promoted_support_count": 5,
            "validated_confidence": 0.75,
            "validated_support_count": 3,
            "provisional_confidence": 0.55,
        }
        self.contradiction_thresholds = {
            "review_required": 0.35,
            "blocked": 0.60,
            "promotion_max": 0.15,
        }

    def get_or_create_record(self, dependency_key):
        key = str(dependency_key or "unknown_dependency")
        if key not in self.evidence_ledger:
            self.evidence_ledger[key] = {
                "dependency_key": key,
                "support_count": 0,
                "contradiction_count": 0,
                "contexts_seen": [],
                "tasks_seen": [],
                "confidence_history": [],
                "transfer_success_count": 0,
                "transfer_failure_count": 0,
                "last_seen": None,
                "status": "PROVISIONAL",
            }
        return self.evidence_ledger[key]

    def record_evidence(self, dependency_key, evidence):
        record = self.get_or_create_record(dependency_key)
        clean_evidence = deepcopy(dict(evidence or {}))
        if "timestamp" not in clean_evidence:
            clean_evidence["timestamp"] = datetime.utcnow().isoformat()
        self.update_record(record, clean_evidence)
        record["status"] = self.classify_status(record)
        return self.build_evidence_report(record["dependency_key"])

    def update_record(self, record, evidence):
        supported = bool(evidence.get("supported", False))
        contradicted = bool(evidence.get("contradicted", False))
        contradiction_score = clamp(evidence.get("contradiction_score", 0.0))
        if supported and not contradicted:
            record["support_count"] += 1
        if contradicted or contradiction_score >= 0.35:
            record["contradiction_count"] += 1

        context = evidence.get("context")
        if context is not None and context not in record["contexts_seen"]:
            record["contexts_seen"].append(context)
        task_id = evidence.get("task_id")
        if task_id is not None and task_id not in record["tasks_seen"]:
            record["tasks_seen"].append(task_id)

        confidence = clamp(evidence.get("confidence", 0.5))
        record["confidence_history"].append(confidence)
        if evidence.get("transfer_success") is True:
            record["transfer_success_count"] += 1
        elif evidence.get("transfer_success") is False:
            record["transfer_failure_count"] += 1

        record["last_seen"] = evidence.get("timestamp")
        key = record["dependency_key"]
        self.confidence_history[key] = list(record["confidence_history"])
        self.context_history[key] = list(record["contexts_seen"])
        return record

    def compute_support_score(self, record):
        support = int(record.get("support_count", 0))
        contradictions = int(record.get("contradiction_count", 0))
        total = support + contradictions
        if total == 0:
            return 0.0
        evidence_volume = clamp(total / 5.0)
        support_ratio = support / total
        return clamp((support_ratio + evidence_volume) / 2.0)

    def compute_transfer_score(self, record):
        success = int(record.get("transfer_success_count", 0))
        failure = int(record.get("transfer_failure_count", 0))
        total = success + failure
        if total == 0:
            return 0.5
        return clamp(success / total)

    def compute_stability_score(self, record):
        history = [
            clamp(value)
            for value in record.get("confidence_history", [])
        ]
        if not history:
            return 0.0
        if len(history) == 1:
            return 1.0
        average = sum(history) / len(history)
        drift = sum(abs(value - average) for value in history) / len(history)
        return clamp(1.0 - drift)

    def compute_contradiction_risk(self, record):
        support = int(record.get("support_count", 0))
        contradictions = int(record.get("contradiction_count", 0))
        total = support + contradictions
        if total == 0:
            return 0.0
        return clamp(contradictions / total)

    def compute_dependency_confidence(self, record):
        support_score = self.compute_support_score(record)
        transfer_score = self.compute_transfer_score(record)
        stability_score = self.compute_stability_score(record)
        contradiction_resistance = clamp(
            1.0 - self.compute_contradiction_risk(record)
        )
        return clamp(
            (
                support_score
                + transfer_score
                + stability_score
                + contradiction_resistance
            )
            / 4.0
        )

    def classify_status(self, record):
        confidence = self.compute_dependency_confidence(record)
        support_count = int(record.get("support_count", 0))
        contradiction_risk = self.compute_contradiction_risk(record)
        if contradiction_risk >= self.contradiction_thresholds["blocked"]:
            return "BLOCKED"
        if contradiction_risk >= self.contradiction_thresholds[
            "review_required"
        ]:
            return "REVIEW_REQUIRED"
        if (
            confidence >= self.support_thresholds["promoted_confidence"]
            and support_count >= self.support_thresholds[
                "promoted_support_count"
            ]
            and contradiction_risk < self.contradiction_thresholds[
                "promotion_max"
            ]
        ):
            return "PROMOTED"
        if (
            confidence >= self.support_thresholds["validated_confidence"]
            and support_count >= self.support_thresholds[
                "validated_support_count"
            ]
        ):
            return "VALIDATED"
        if confidence >= self.support_thresholds["provisional_confidence"]:
            return "PROVISIONAL"
        return "BLOCKED"

    def recommend_action(self, status, record):
        if status == "PROMOTED":
            return "PROMOTE_DEPENDENCY"
        if status == "VALIDATED":
            return "USE_FOR_TRUTH_SUPPORT"
        if status == "PROVISIONAL":
            return "HOLD_FOR_MORE_EVIDENCE"
        if status == "REVIEW_REQUIRED":
            return "REQUIRE_DEPENDENCY_REVIEW"
        return "BLOCK_DEPENDENCY"

    def build_evidence_report(self, dependency_key):
        record = self.get_or_create_record(dependency_key)
        transfer_score = self.compute_transfer_score(record)
        stability_score = self.compute_stability_score(record)
        contradiction_risk = self.compute_contradiction_risk(record)
        confidence = self.compute_dependency_confidence(record)
        status = self.classify_status(record)
        record["status"] = status
        return {
            "system": "dependency_evidence_engine",
            "dependency_key": record["dependency_key"],
            "support_count": record["support_count"],
            "contradiction_count": record["contradiction_count"],
            "contexts_seen": list(record["contexts_seen"]),
            "tasks_seen": list(record["tasks_seen"]),
            "transfer_success_rate": transfer_score,
            "stability_score": stability_score,
            "contradiction_risk": contradiction_risk,
            "dependency_confidence": confidence,
            "status": status,
            "recommended_action": self.recommend_action(status, record),
            "last_seen": record["last_seen"],
        }

    def analyze_dependency(self, dependency_key):
        return self.build_evidence_report(dependency_key)

    def analyze_many(self, dependency_keys):
        return [
            self.analyze_dependency(key)
            for key in list(dependency_keys or [])
        ]

    def export_ledger(self):
        return {
            "system": "dependency_evidence_engine",
            "evidence_ledger": deepcopy(self.evidence_ledger),
            "confidence_history": deepcopy(self.confidence_history),
            "context_history": deepcopy(self.context_history),
        }

    def import_ledger(self, ledger):
        ledger = deepcopy(dict(ledger or {}))
        imported = ledger.get("evidence_ledger", ledger)
        if not isinstance(imported, dict):
            return 0
        self.evidence_ledger = {}
        for key, record in imported.items():
            if not isinstance(record, dict):
                continue
            clean = self.get_or_create_record(key)
            clean.update({
                "dependency_key": str(record.get("dependency_key", key)),
                "support_count": max(
                    int(record.get("support_count", 0)),
                    0,
                ),
                "contradiction_count": max(
                    int(record.get("contradiction_count", 0)),
                    0,
                ),
                "contexts_seen": list(record.get("contexts_seen", [])),
                "tasks_seen": list(record.get("tasks_seen", [])),
                "confidence_history": [
                    clamp(value)
                    for value in record.get("confidence_history", [])
                ],
                "transfer_success_count": max(
                    int(record.get("transfer_success_count", 0)),
                    0,
                ),
                "transfer_failure_count": max(
                    int(record.get("transfer_failure_count", 0)),
                    0,
                ),
                "last_seen": record.get("last_seen"),
                "status": str(record.get("status", "PROVISIONAL")),
            })
        self.confidence_history = {
            key: list(record.get("confidence_history", []))
            for key, record in self.evidence_ledger.items()
        }
        self.context_history = {
            key: list(record.get("contexts_seen", []))
            for key, record in self.evidence_ledger.items()
        }
        return len(self.evidence_ledger)


__all__ = [
    "DependencyEvidenceEngine",
]
