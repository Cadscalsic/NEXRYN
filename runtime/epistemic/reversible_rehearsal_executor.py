import json
from pathlib import Path

from runtime.semantic_drift_controller import SemanticDriftController


class ReversibleRehearsalExecutor:
    def __init__(self, drift_controller=None, storage_path=None):
        self.drift_controller = drift_controller or SemanticDriftController()
        self.storage_path = (
            Path(storage_path)
            if storage_path
            else None
        )
        self._cycle_counts = {}
        self._simulation_checkpoints = {}
        self.execution_history = []
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
                        "cycle_counts": self._cycle_counts,
                        "simulation_checkpoints":
                        self._simulation_checkpoints,
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
        self._cycle_counts = {
            str(concept): int(count)
            for concept, count in payload.get("cycle_counts", {}).items()
        }
        self._simulation_checkpoints = {
            str(concept): {
                "identity_continuity":
                checkpoint.get("identity_continuity"),
                "semantic_drift":
                checkpoint.get("semantic_drift"),
            }
            for concept, checkpoint
            in payload.get("simulation_checkpoints", {}).items()
            if isinstance(checkpoint, dict)
        }

    def _next_cycle_id(self, concept):
        count = self._cycle_counts.get(concept, 0) + 1
        self._cycle_counts[concept] = count
        self._persist()
        return f"truth_internalization:{concept}:cycle_{count}"

    def execute(self, rehearsal, context=None):
        if not rehearsal:
            return {
                "system": "reversible_rehearsal_executor",
                "phase": "6.1",
                "execution_state": "REHEARSAL_NOT_REQUIRED",
                "result": None,
            }
        if not (
            rehearsal.get("sandbox_only") is True
            and rehearsal.get("reversible") is True
            and rehearsal.get("persistent_identity_write_forbidden") is True
        ):
            return {
                "system": "reversible_rehearsal_executor",
                "phase": "6.1",
                "execution_state": "REHEARSAL_BLOCKED",
                "reason": "reversible_sandbox_contract_required",
                "result": None,
            }

        concept = rehearsal["concept"]
        checkpoint = self._simulation_checkpoints.get(concept, {})
        effective_rehearsal = {
            **rehearsal,
            "baseline_identity_continuity":
            checkpoint.get(
                "identity_continuity",
                rehearsal.get("baseline_identity_continuity"),
            ),
            "baseline_semantic_drift":
            checkpoint.get(
                "semantic_drift",
                rehearsal.get("baseline_semantic_drift"),
            ),
        }
        control = self.drift_controller.regulate(
            effective_rehearsal,
            context,
        )
        self._simulation_checkpoints[concept] = {
            "identity_continuity": control["identity_continuity"],
            "semantic_drift": control["semantic_drift"],
        }
        self._persist()
        result = {
            "concept": concept,
            "rehearsal_cycle_id": self._next_cycle_id(concept),
            "identity_continuity": control["identity_continuity"],
            "semantic_drift": control["semantic_drift"],
            "identity_repair_inactive":
            control["identity_repair_inactive"],
            "semantic_containment_inactive":
            control["semantic_containment_inactive"],
            "semantic_spine_state": control["semantic_spine_state"],
            "semantic_drift_control": control,
            "sandbox_validated": True,
            "isolated_world": True,
            "reversible": True,
            "simulation_only": True,
            "persistent_identity_write_forbidden": True,
        }
        report = {
            "system": "reversible_rehearsal_executor",
            "phase": "6.1",
            "execution_state": "REVERSIBLE_REHEARSAL_COMPLETED",
            "result": result,
            "persistent_identity_write_forbidden": True,
            "automatic_truth_commit_forbidden": True,
        }
        self.execution_history.append(report)
        self.execution_history = self.execution_history[-256:]
        return report


__all__ = [
    "ReversibleRehearsalExecutor",
]
