import json
from datetime import datetime
from pathlib import Path

from runtime.training.curriculum_manager import CurriculumManager


class TrainingAssistant:
    SCHEMA_VERSION = 1

    def __init__(
        self,
        state_path="runtime_data/training_assistant_state.json",
        batch_size=5,
        curriculum_manager=None,
    ):
        self.state_path = Path(state_path)
        self.batch_size = max(int(batch_size), 1)
        self.curriculum_manager = curriculum_manager or CurriculumManager()
        self.state = self._load()

    def _default_state(self):
        return {
            "schema_version": self.SCHEMA_VERSION,
            "next_task_index": 0,
            "completed_cycles": 0,
            "active_batch": [],
            "pending_next_task_index": None,
            "prioritized_concepts": [],
            "curriculum_report": {},
            "history": [],
        }

    def _load(self):
        if not self.state_path.exists():
            return self._default_state()
        try:
            with self.state_path.open("r", encoding="utf-8") as file:
                state = json.load(file)
            if not isinstance(state, dict):
                return self._default_state()
            return {
                **self._default_state(),
                **state,
            }
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return self._default_state()

    def _persist(self):
        temporary_path = self.state_path.with_suffix(
            f"{self.state_path.suffix}.tmp"
        )
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(
                self.state,
                file,
                indent=2,
                ensure_ascii=True,
            )
        temporary_path.replace(self.state_path)

    def reset(self):
        self.state = self._default_state()
        self._persist()
        return self.report()

    def _normalized_tasks(self, task_files):
        return sorted({
            str(task_file)
            for task_file in task_files
            if str(task_file).endswith(".json")
        })

    def _active_batch_is_valid(self, task_files):
        active_batch = self.state.get("active_batch", [])
        return bool(active_batch) and all(
            task_file in task_files
            for task_file in active_batch
        )

    def _prioritized_tasks(
        self,
        task_files,
        start,
        concept_counts=None,
        concept_states=None,
        task_directory=None,
        observed_task_ids=None,
    ):
        rotated = [
            task_files[(start + offset) % len(task_files)]
            for offset in range(len(task_files))
        ]
        curriculum_report = self.curriculum_manager.rank_tasks(
            rotated,
            concept_counts=concept_counts,
            concept_states=concept_states,
            task_directory=task_directory,
            observed_task_ids=observed_task_ids,
        )
        return (
            curriculum_report["ranked_task_files"],
            curriculum_report,
        )

    def select_batch(
        self,
        task_files,
        concept_counts=None,
        concept_states=None,
        task_directory=None,
        observed_task_ids=None,
    ):
        task_files = self._normalized_tasks(task_files)
        if not task_files:
            raise ValueError("at least one JSON training task is required")

        resumed = self._active_batch_is_valid(task_files)
        if resumed:
            selected = list(self.state["active_batch"])
            prioritized_concepts = list(
                self.state.get("prioritized_concepts", [])
            )
            curriculum_report = dict(
                self.state.get("curriculum_report", {})
            )
        else:
            start = int(self.state.get("next_task_index", 0))
            start %= len(task_files)
            ranked_tasks, curriculum_report = self._prioritized_tasks(
                task_files,
                start,
                concept_counts=concept_counts,
                concept_states=concept_states,
                task_directory=task_directory,
                observed_task_ids=observed_task_ids,
            )
            prioritized_concepts = curriculum_report[
                "prioritized_concepts"
            ]
            selected = self.curriculum_manager.select_batch_tasks(
                curriculum_report,
                min(self.batch_size, len(task_files)),
            )
            self.state["active_batch"] = selected
            self.state["prioritized_concepts"] = prioritized_concepts
            self.state["curriculum_report"] = curriculum_report
            self.state["pending_next_task_index"] = (
                start + len(selected)
            ) % len(task_files)
            self._persist()

        return {
            "system": "training_assistant",
            "training_mode":
            curriculum_report.get(
                "training_mode",
                "bounded_round_robin_batch",
            ),
            "prioritized_concepts": prioritized_concepts,
            "curriculum_report": curriculum_report,
            "batch_size": self.batch_size,
            "available_task_count": len(task_files),
            "selected_task_count": len(selected),
            "selected_task_files": selected,
            "resumed_active_batch": resumed,
            "completed_cycles": self.state.get("completed_cycles", 0),
            "next_task_index_after_completion":
            self.state.get("pending_next_task_index"),
        }

    def complete_cycle(self, successful_tasks=0, failed_tasks=0):
        active_batch = list(self.state.get("active_batch", []))
        if not active_batch:
            return {
                **self.report(),
                "cycle_completion_state": "NO_ACTIVE_BATCH",
            }

        completed_cycles = int(self.state.get("completed_cycles", 0)) + 1
        self.state["next_task_index"] = int(
            self.state.get("pending_next_task_index", 0)
        )
        self.state["completed_cycles"] = completed_cycles
        self.state["active_batch"] = []
        self.state["pending_next_task_index"] = None
        self.state["prioritized_concepts"] = []
        self.state["curriculum_report"] = {}
        self.state["history"] = [
            *list(self.state.get("history", []))[-31:],
            {
                "cycle": completed_cycles,
                "task_files": active_batch,
                "successful_tasks": int(successful_tasks),
                "failed_tasks": int(failed_tasks),
                "timestamp": datetime.utcnow().isoformat(),
            },
        ]
        self._persist()
        return {
            **self.report(),
            "cycle_completion_state": "TRAINING_BATCH_COMPLETED",
            "completed_task_files": active_batch,
        }

    def report(self):
        return {
            "system": "training_assistant",
            "training_mode": "bounded_round_robin_batch",
            "batch_size": self.batch_size,
            "next_task_index": self.state.get("next_task_index", 0),
            "completed_cycles": self.state.get("completed_cycles", 0),
            "active_batch": list(self.state.get("active_batch", [])),
            "prioritized_concepts":
            list(self.state.get("prioritized_concepts", [])),
            "history_size": len(self.state.get("history", [])),
            "state_path": str(self.state_path),
        }


__all__ = [
    "TrainingAssistant",
]
