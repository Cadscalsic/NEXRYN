import json
from pathlib import Path

from core.epistemic_models import clamp


class SemanticSpineRecoveryEngine:
    def __init__(
        self,
        required_recovery_cycles=3,
        minimum_identity_continuity=0.62,
        maximum_semantic_drift=0.58,
        storage_path=None,
    ):
        self.required_recovery_cycles = required_recovery_cycles
        self.minimum_identity_continuity = minimum_identity_continuity
        self.maximum_semantic_drift = maximum_semantic_drift
        self.storage_path = (
            Path(storage_path)
            if storage_path
            else None
        )
        self._reports = {}
        self._processed_cycle_ids = {}
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
                        "reports": self._reports,
                        "processed_cycle_ids": {
                            concept: sorted(cycle_ids)
                            for concept, cycle_ids
                            in self._processed_cycle_ids.items()
                        },
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
        self._reports = {
            str(concept): dict(report)
            for concept, report in payload.get("reports", {}).items()
            if isinstance(report, dict)
        }
        self._processed_cycle_ids = {
            str(concept): {
                str(cycle_id)
                for cycle_id in cycle_ids
            }
            for concept, cycle_ids
            in payload.get("processed_cycle_ids", {}).items()
            if isinstance(cycle_ids, list)
        }

    def report_for(self, concept):
        return dict(
            self._reports.get(
                concept,
                {
                    "system": "semantic_spine_recovery_engine",
                    "concept": concept,
                    "recovery_state": "RECOVERY_NOT_STARTED",
                    "recovery_streak": 0,
                    "required_recovery_cycles":
                    self.required_recovery_cycles,
                    "remaining_recovery_cycles":
                    self.required_recovery_cycles,
                    "semantic_spine_recovery_confirmed": False,
                },
            )
        )

    def evaluate(self, belief, integration, identity_repair):
        previous = self.report_for(belief.concept)
        result = identity_repair.get("accepted_rehearsal_result")
        cycle_id = result.get("rehearsal_cycle_id") if result else None
        confirmed_recovery_retained = (
            result is None
            and previous.get(
                "semantic_spine_recovery_confirmed",
                False,
            )
            is True
        )
        processed_cycle_ids = self._processed_cycle_ids.setdefault(
            belief.concept,
            set(),
        )
        duplicate_cycle = cycle_id in processed_cycle_ids
        identity_continuity = (
            clamp(result.get("identity_continuity", 0.0))
            if result
            else None
        )
        semantic_drift = (
            clamp(result.get("semantic_drift", 1.0))
            if result
            else None
        )
        checks = {
            "validated_reversible_rehearsal":
            result is not None or confirmed_recovery_retained,
            "identity_continuity_preserved":
            (
                identity_continuity is not None
                and identity_continuity >= self.minimum_identity_continuity
            )
            or confirmed_recovery_retained,
            "semantic_drift_below_limit":
            (
                semantic_drift is not None
                and semantic_drift < self.maximum_semantic_drift
            )
            or confirmed_recovery_retained,
            "identity_repair_inactive":
            bool(result and result["identity_repair_inactive"])
            or confirmed_recovery_retained,
            "semantic_containment_inactive":
            bool(result and result["semantic_containment_inactive"])
            or confirmed_recovery_retained,
            "semantic_spine_recovering":
            bool(
                result
                and result["semantic_spine_state"]
                in [
                    "semantic_spine_recovering",
                    "stable_semantic_spine",
                ]
            )
            or confirmed_recovery_retained,
        }
        recovery_cycle_passed = (
            result is not None
            and all(checks.values())
            and not duplicate_cycle
        )
        if recovery_cycle_passed:
            processed_cycle_ids.add(cycle_id)
        candidate_ready = integration.get(
            "checks",
            {},
        ).get(
            "truth_candidate_ready",
            False,
        )
        recovery_streak = (
            previous.get("recovery_streak", 0) + 1
            if recovery_cycle_passed
            else previous.get("recovery_streak", 0)
            if (
                duplicate_cycle
                or not candidate_ready
                or confirmed_recovery_retained
            )
            else 0
        )
        confirmed = (
            confirmed_recovery_retained
            or recovery_streak >= self.required_recovery_cycles
        )
        rehearsal_validation_pending = (
            candidate_ready
            and result is None
            and not confirmed_recovery_retained
        )
        recovery_blocker_type = (
            "VALIDATED_REVERSIBLE_REHEARSAL_PENDING"
            if rehearsal_validation_pending
            else "RECOVERY_CHECKS_FAILED"
            if candidate_ready and not recovery_cycle_passed and not duplicate_cycle
            else None
        )
        reported_identity_continuity = (
            identity_continuity
            if identity_continuity is not None
            else previous.get("identity_continuity")
        )
        reported_semantic_drift = (
            semantic_drift
            if semantic_drift is not None
            else previous.get("semantic_drift")
        )
        report = {
            "system": "semantic_spine_recovery_engine",
            "concept": belief.concept,
            "recovery_state": (
                "STABLE_SEMANTIC_SPINE"
                if confirmed
                else "RECOVERY_MONITORING"
                if recovery_cycle_passed
                else "REHEARSAL_VALIDATION_REQUIRED"
                if candidate_ready
                else "WAITING_FOR_TRUTH_CANDIDATE"
            ),
            "recovery_streak": recovery_streak,
            "required_recovery_cycles": self.required_recovery_cycles,
            "remaining_recovery_cycles":
            max(self.required_recovery_cycles - recovery_streak, 0),
            "recovery_cycle_passed": recovery_cycle_passed,
            "rehearsal_validation_pending":
            rehearsal_validation_pending,
            "recovery_blocker_type": recovery_blocker_type,
            "rehearsal_cycle_id": cycle_id,
            "duplicate_rehearsal_cycle_ignored": duplicate_cycle,
            "confirmed_recovery_retained_without_new_rehearsal":
            confirmed_recovery_retained,
            "semantic_spine_recovery_confirmed": confirmed,
            "identity_continuity": reported_identity_continuity,
            "semantic_drift": reported_semantic_drift,
            "checks": checks,
            "failed_checks": [
                name
                for name, passed in checks.items()
                if not passed
            ],
            "persistent_identity_write_forbidden": not confirmed,
            "truth_commit_review_unblocked": confirmed,
            "automatic_truth_commit_forbidden": True,
        }
        self._reports[belief.concept] = report
        self._persist()
        return report


__all__ = [
    "SemanticSpineRecoveryEngine",
]
