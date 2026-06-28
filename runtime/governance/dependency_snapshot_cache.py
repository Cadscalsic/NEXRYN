from __future__ import annotations

from datetime import datetime
import hashlib
import json
from typing import Any


class DependencySnapshotCache:
    def __init__(self):
        self.snapshots: dict[str, dict[str, Any]] = {}
        self.hits = 0
        self.misses = 0
        self.store_count = 0
        self.invalidations = 0

    def build_snapshot(
        self,
        concept: str,
        dependency_report: dict,
        truth_report: dict,
    ) -> dict:
        dependency_report = (
            dependency_report if isinstance(dependency_report, dict) else {}
        )
        truth_report = truth_report if isinstance(truth_report, dict) else {}
        truth_state = self._field(
            "final_commit_state",
            truth_report,
            default=self._field("truth_state", truth_report),
        )
        snapshot = {
            "concept": concept,
            "snapshot_state": "ACTIVE",
            "truth_state": truth_state,
            "dependency_chain_depth": self._int_field(
                dependency_report,
                "dependency_chain_depth",
            ),
            "dependency_chain_coverage": self._float_field(
                dependency_report,
                "dependency_chain_coverage",
            ),
            "dependency_coherence": self._float_field(
                dependency_report,
                "dependency_coherence",
                "dependency_coherence_average",
            ),
            "links_loaded": self._int_field(
                dependency_report,
                "process_dependency_links_loaded",
                "links_loaded",
            ),
            "links_used": self._int_field(
                dependency_report,
                "process_dependency_links_used",
                "links_used",
                default=len(
                    dependency_report.get("used_dependency_links", [])
                    if isinstance(
                        dependency_report.get("used_dependency_links"),
                        list,
                    )
                    else []
                ),
            ),
            "explanation_path_summary": self._summary_path(
                dependency_report,
            ),
            "identity_runtime_state": self._field(
                "identity_runtime_state",
                truth_report,
            ),
            "contextual_truth_supported": self._field(
                "contextual_truth_supported",
                truth_report,
            ),
            "created_at": datetime.utcnow().isoformat(),
            "reuse_count": 0,
        }
        snapshot["dependency_signature"] = self._signature(snapshot)
        return snapshot

    def get_snapshot(self, concept: str, context: dict) -> dict:
        context = context if isinstance(context, dict) else {}
        snapshot = None
        context_snapshots = context.get("dependency_snapshots")
        if isinstance(context_snapshots, dict):
            candidate = context_snapshots.get(concept)
            if isinstance(candidate, dict):
                snapshot = candidate
        if snapshot is None:
            candidate = self.snapshots.get(concept)
            if isinstance(candidate, dict):
                snapshot = candidate

        if snapshot is None:
            self.misses += 1
            return {
                "dependency_snapshot_reused": False,
                "dependency_reasoning_skipped": False,
                "reason": "snapshot_missing",
            }

        if not self.can_reuse_snapshot(concept, snapshot, context):
            self.misses += 1
            return {
                "dependency_snapshot_reused": False,
                "dependency_reasoning_skipped": False,
                "reason": "snapshot_not_reusable",
                "snapshot": snapshot,
            }

        snapshot["reuse_count"] = int(snapshot.get("reuse_count", 0) or 0) + 1
        self.snapshots[concept] = snapshot
        self.hits += 1
        return {
            "system": "dependency_snapshot_cache",
            "concept": concept,
            "dependency_snapshot_reused": True,
            "dependency_reasoning_skipped": True,
            "snapshot_state": snapshot["snapshot_state"],
            "truth_state": snapshot["truth_state"],
            "dependency_chain_depth": snapshot["dependency_chain_depth"],
            "dependency_chain_coverage":
            snapshot["dependency_chain_coverage"],
            "dependency_coherence": snapshot["dependency_coherence"],
            "dependency_coherence_average": snapshot["dependency_coherence"],
            "process_dependency_links_loaded": snapshot["links_loaded"],
            "process_dependency_links_used": snapshot["links_used"],
            "links_loaded": snapshot["links_loaded"],
            "links_used": snapshot["links_used"],
            "missing_dependencies": [],
            "dependency_signature": snapshot["dependency_signature"],
            "explanation_path_summary":
            list(snapshot["explanation_path_summary"]),
            "dependency_reasoning_invoked": False,
            "dependency_execution_trace": {
                "concept": concept,
                "memory_loaded": False,
                "operator_available": True,
                "reasoning_invoked": False,
                "bypass_reason": "dependency_snapshot_reused",
            },
            "governance_consumable": True,
            "reuse_count": snapshot["reuse_count"],
        }

    def store_snapshot(self, concept: str, snapshot: dict) -> dict:
        if not isinstance(snapshot, dict):
            return {
                "system": "dependency_snapshot_cache",
                "concept": concept,
                "stored": False,
                "reason": "invalid_snapshot",
            }
        if snapshot.get("concept") != concept:
            return {
                "system": "dependency_snapshot_cache",
                "concept": concept,
                "stored": False,
                "reason": "concept_mismatch",
            }
        self.snapshots[concept] = dict(snapshot)
        self.store_count += 1
        return {
            "system": "dependency_snapshot_cache",
            "concept": concept,
            "stored": True,
            "snapshot_state": snapshot.get("snapshot_state"),
            "dependency_signature": snapshot.get("dependency_signature"),
        }

    def can_reuse_snapshot(
        self,
        concept: str,
        snapshot: dict,
        context: dict,
    ) -> bool:
        context = context if isinstance(context, dict) else {}
        if not isinstance(snapshot, dict):
            return False
        if snapshot.get("concept") != concept:
            return False
        if snapshot.get("snapshot_state") != "ACTIVE":
            return False
        if snapshot.get("truth_state") != "LOCKED_TRUTH_PRESERVED":
            return False
        if snapshot.get("identity_runtime_state") != (
            "IDENTITY_RUNTIME_STABLE"
        ):
            return False
        if snapshot.get("contextual_truth_supported") is not True:
            return False
        if self._number(snapshot.get("dependency_chain_coverage")) < 0.90:
            return False
        if self._number(snapshot.get("dependency_coherence")) < 0.80:
            return False
        if context.get("contradiction_review_required") is True:
            return False
        if self._has_failures(context.get("failed_gates")):
            return False
        if self._has_failures(context.get("failed_identity_governance_gates")):
            return False
        if self._has_failures(context.get("missing_dependencies")):
            return False
        if context.get("identity_runtime_state") not in {
            None,
            "IDENTITY_RUNTIME_STABLE",
        }:
            return False
        if context.get("contextual_truth_supported") is False:
            return False
        truth_state = (
            context.get("final_commit_state")
            or context.get("truth_state")
        )
        if truth_state not in {None, "LOCKED_TRUTH_PRESERVED"}:
            return False
        drift_limit = context.get("maximum_semantic_drift")
        semantic_drift = context.get("semantic_drift")
        if drift_limit is not None and semantic_drift is not None:
            if self._number(semantic_drift) > self._number(drift_limit):
                self._invalidate(concept)
                return False
        memory_version = context.get("dependency_memory_version")
        if memory_version is not None:
            snapshot_version = snapshot.get("dependency_memory_version")
            if snapshot_version not in {None, memory_version}:
                self._invalidate(concept)
                return False
        return True

    def report(self) -> dict:
        return {
            "system": "dependency_snapshot_cache",
            "snapshot_count": len(self.snapshots),
            "dependency_snapshot_hits": self.hits,
            "dependency_snapshot_misses": self.misses,
            "dependency_snapshot_store_count": self.store_count,
            "invalidations": self.invalidations,
            "active_concepts": sorted(self.snapshots),
        }

    def _field(self, field, report, default=None):
        if not isinstance(report, dict):
            return default
        if field in report:
            return report[field]
        metadata = report.get("metadata")
        if isinstance(metadata, dict):
            if field in metadata:
                return metadata[field]
            for value in metadata.values():
                if isinstance(value, dict) and field in value:
                    return value[field]
        for value in report.values():
            if isinstance(value, dict) and field in value:
                return value[field]
        return default

    def _float_field(self, report, *fields, default=0.0):
        for field in fields:
            if field in report:
                return round(self._number(report.get(field)), 4)
        return default

    def _int_field(self, report, *fields, default=0):
        for field in fields:
            if field in report:
                try:
                    return int(report.get(field) or 0)
                except (TypeError, ValueError):
                    return default
        return default

    def _summary_path(self, report):
        path = report.get("explanation_path_summary")
        if not isinstance(path, list):
            path = report.get("explanation_path")
        if not isinstance(path, list):
            path = report.get("dependency_chain")
        if not isinstance(path, list):
            return []
        summary = []
        for item in path[:8]:
            if isinstance(item, str):
                summary.append(item)
            elif isinstance(item, dict):
                summary.append(
                    str(
                        item.get("target")
                        or item.get("concept")
                        or item.get("name")
                        or item.get("relation")
                        or "dependency"
                    )
                )
            else:
                summary.append(str(item))
        return summary

    def _signature(self, snapshot):
        payload = {
            key: snapshot.get(key)
            for key in [
                "concept",
                "truth_state",
                "dependency_chain_depth",
                "dependency_chain_coverage",
                "dependency_coherence",
                "links_loaded",
                "links_used",
                "explanation_path_summary",
            ]
        }
        encoded = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _number(self, value):
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _has_failures(self, value):
        if value is None:
            return False
        if isinstance(value, (list, tuple, set, dict)):
            return len(value) > 0
        return bool(value)

    def _invalidate(self, concept):
        snapshot = self.snapshots.get(concept)
        if isinstance(snapshot, dict):
            snapshot["snapshot_state"] = "INVALIDATED"
            self.invalidations += 1


dependency_snapshot_cache = DependencySnapshotCache()


__all__ = [
    "DependencySnapshotCache",
    "dependency_snapshot_cache",
]
