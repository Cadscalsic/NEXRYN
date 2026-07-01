import json
import random
import uuid
from datetime import datetime
from pathlib import Path

from runtime.training.curriculum_manager import CurriculumManager


class TrainingAssistant:
    SCHEMA_VERSION = 1
    TASK_COOLDOWN_RUNS = 20
    UNSEEN_TASK_BOOST = 3.0
    RECENT_TASK_PENALTY = 0.1
    SELECTION_MODES = {"random", "weighted_random", "curriculum"}

    def __init__(
        self,
        state_path="runtime_data/training_assistant_state.json",
        batch_size=3,
        curriculum_manager=None,
        selection_memory_path="runtime/cache/task_selection_memory.json",
        selection_mode="weighted_random",
        random_seed=None,
        task_cooldown_runs=TASK_COOLDOWN_RUNS,
    ):
        self.state_path = Path(state_path)
        self.batch_size = max(int(batch_size), 1)
        self.curriculum_manager = curriculum_manager or CurriculumManager()
        self.selection_memory_path = Path(selection_memory_path)
        self.selection_mode = self._selection_mode(selection_mode)
        self.random_seed = random_seed
        self.task_cooldown_runs = max(int(task_cooldown_runs), 0)
        self.state = self._load()
        self.selection_memory = self._load_selection_memory()

    def _default_state(self):
        return {
            "schema_version": self.SCHEMA_VERSION,
            "next_task_index": 0,
            "completed_cycles": 0,
            "active_batch": [],
            "pending_next_task_index": None,
            "prioritized_concepts": [],
            "selected_concepts": [],
            "curriculum_report": {},
            "selection_diversity_report": {},
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

    def _default_selection_memory(self):
        return {
            "schema_version": 1,
            "run_counter": 0,
            "previous_batch": [],
            "recent_runs": [],
            "tasks": {},
        }

    def _load_selection_memory(self):
        if not self.selection_memory_path.exists():
            return self._default_selection_memory()
        try:
            with self.selection_memory_path.open("r", encoding="utf-8") as file:
                memory = json.load(file)
            if not isinstance(memory, dict):
                return self._default_selection_memory()
            return {
                **self._default_selection_memory(),
                **memory,
                "previous_batch": list(memory.get("previous_batch", [])),
                "recent_runs": list(memory.get("recent_runs", [])),
                "tasks": dict(memory.get("tasks", {})),
            }
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return self._default_selection_memory()

    def _persist_selection_memory(self):
        temporary_path = self.selection_memory_path.with_suffix(
            f"{self.selection_memory_path.suffix}.tmp"
        )
        self.selection_memory_path.parent.mkdir(parents=True, exist_ok=True)
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(
                self.selection_memory,
                file,
                indent=2,
                ensure_ascii=True,
            )
        temporary_path.replace(self.selection_memory_path)

    def reset(self):
        self.state = self._default_state()
        self.selection_memory = self._default_selection_memory()
        self._persist()
        self._persist_selection_memory()
        return self.report()

    def reset_selection_memory(self):
        self.selection_memory = self._default_selection_memory()
        self._persist_selection_memory()
        return self.report()

    def _normalized_tasks(self, task_files):
        return sorted({
            str(task_file)
            for task_file in task_files
            if str(task_file).endswith(".json")
        })

    def _selection_mode(self, selection_mode):
        selection_mode = str(selection_mode or "weighted_random")
        if selection_mode not in self.SELECTION_MODES:
            raise ValueError(
                "selection_mode must be one of: "
                f"{', '.join(sorted(self.SELECTION_MODES))}"
            )
        return selection_mode

    def _active_batch_is_valid(self, task_files):
        active_batch = self.state.get("active_batch", [])
        return (
            bool(active_batch)
            and len(active_batch) == min(self.batch_size, len(task_files))
            and all(
            task_file in task_files
            for task_file in active_batch
            )
        )

    def _prioritized_tasks(
        self,
        task_files,
        start,
        concept_counts=None,
        concept_states=None,
        task_directory=None,
        observed_task_ids=None,
        history=None,
        core_knowledge=None,
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
            history=history,
            core_knowledge=core_knowledge,
        )
        return (
            curriculum_report["ranked_task_files"],
            curriculum_report,
        )

    def _rng_for_run(self):
        if self.random_seed is not None:
            seed = int(self.random_seed)
        else:
            seed = random.SystemRandom().randrange(1, 2 ** 63)
        return random.Random(seed), seed

    def _recent_task_ids(self):
        if self.task_cooldown_runs <= 0:
            return set()
        recent_runs = list(self.selection_memory.get("recent_runs", []))
        recent = recent_runs[-self.task_cooldown_runs:]
        return {
            str(task_file)
            for run in recent
            if isinstance(run, dict)
            for task_file in run.get("task_ids", [])
        }

    def _task_record(self, task_file):
        record = self.selection_memory.setdefault("tasks", {}).get(
            task_file,
            {},
        )
        return {
            "task_id": task_file,
            "times_selected": int(record.get("times_selected", 0)),
            "last_selected_at": record.get("last_selected_at"),
            "last_run_id": record.get("last_run_id"),
            "recent_selection_count": int(
                record.get("recent_selection_count", 0)
            ),
        }

    def _selection_weight(self, task_file, recent_task_ids, rng):
        record = self._task_record(task_file)
        unseen_boost = (
            self.UNSEEN_TASK_BOOST
            if record["times_selected"] <= 0
            else 1.0
        )
        cooldown_factor = (
            self.RECENT_TASK_PENALTY
            if task_file in recent_task_ids
            else 1.0
        )
        inverse_frequency_factor = 1.0 / (
            1.0 + record["times_selected"]
        )
        random_jitter = rng.uniform(0.85, 1.15)
        return (
            1.0
            * unseen_boost
            * cooldown_factor
            * inverse_frequency_factor
            * random_jitter
        )

    def _weighted_choice_without_replacement(
        self,
        candidates,
        weights,
        rng,
        count,
    ):
        remaining = list(zip(candidates, weights))
        selected = []
        while remaining and len(selected) < count:
            total_weight = sum(max(weight, 0.0) for _, weight in remaining)
            if total_weight <= 0.0:
                rng.shuffle(remaining)
                selected.extend(
                    task_file
                    for task_file, _ in remaining[:count - len(selected)]
                )
                break
            threshold = rng.random() * total_weight
            cumulative = 0.0
            selected_index = 0
            for index, (_, weight) in enumerate(remaining):
                cumulative += max(weight, 0.0)
                if cumulative >= threshold:
                    selected_index = index
                    break
            task_file, _ = remaining.pop(selected_index)
            selected.append(task_file)
        return selected

    def _selection_diversity_score(
        self,
        selected,
        previous_overlap,
        unseen_selected,
        average_frequency,
    ):
        if not selected:
            return 0.0
        unique_score = len(set(selected)) / len(selected)
        no_overlap_score = 1.0 - previous_overlap / len(selected)
        unseen_score = unseen_selected / len(selected)
        frequency_score = 1.0 / (1.0 + average_frequency)
        return round(
            max(
                0.0,
                min(
                    1.0,
                    unique_score * 0.35
                    + no_overlap_score * 0.30
                    + unseen_score * 0.20
                    + frequency_score * 0.15,
                ),
            ),
            4,
        )

    def _randomized_select(self, task_files, batch_size, selection_mode, rng):
        previous_batch = set(self.selection_memory.get("previous_batch", []))
        recent_task_ids = self._recent_task_ids()
        dataset_large = len(task_files) > batch_size * 5
        shuffled_tasks = list(task_files)
        rng.shuffle(shuffled_tasks)

        excluded = set(recent_task_ids)
        if dataset_large:
            excluded.update(previous_batch)
        available = [
            task_file
            for task_file in shuffled_tasks
            if task_file not in excluded
        ]
        cooldown_relaxed = False
        if len(available) < batch_size:
            cooldown_relaxed = True
            available = [
                task_file
                for task_file in shuffled_tasks
                if not (dataset_large and task_file in previous_batch)
            ]
        if len(available) < batch_size:
            available = list(shuffled_tasks)

        if selection_mode == "random":
            selected = available[:batch_size]
        else:
            weights = [
                self._selection_weight(task_file, recent_task_ids, rng)
                for task_file in available
            ]
            selected = self._weighted_choice_without_replacement(
                available,
                weights,
                rng,
                batch_size,
            )

        selected = list(dict.fromkeys(selected))[:batch_size]
        selected_set = set(selected)
        selected_records = [self._task_record(task_file) for task_file in selected]
        unseen_selected = sum(
            1 for record in selected_records if record["times_selected"] <= 0
        )
        average_frequency = (
            sum(record["times_selected"] for record in selected_records)
            / len(selected_records)
            if selected_records
            else 0.0
        )
        previous_overlap = len(selected_set & previous_batch)
        cooldown_filtered = sorted(
            task_file
            for task_file in shuffled_tasks
            if task_file in recent_task_ids and task_file not in selected_set
        )
        repeated_penalty = any(
            self._task_record(task_file)["times_selected"] > 0
            or task_file in recent_task_ids
            for task_file in selected
        )
        return selected, {
            "system": "training_selection_diversity",
            "total_available_tasks": len(task_files),
            "selected_tasks": list(selected),
            "selection_mode": selection_mode,
            "previous_batch_overlap_count": previous_overlap,
            "unseen_tasks_selected": unseen_selected,
            "cooldown_filtered_tasks": len(cooldown_filtered),
            "cooldown_filtered_task_ids": cooldown_filtered[:10],
            "average_task_selection_frequency": round(average_frequency, 4),
            "repeated_task_penalty_applied": repeated_penalty,
            "diversity_score": self._selection_diversity_score(
                selected,
                previous_overlap,
                unseen_selected,
                average_frequency,
            ),
            "cooldown_window_runs": self.task_cooldown_runs,
            "cooldown_relaxed": cooldown_relaxed,
            "dataset_large": dataset_large,
        }

    def _record_selection(self, selected, run_id):
        now = datetime.utcnow().isoformat()
        recent_runs = list(self.selection_memory.get("recent_runs", []))
        recent_task_ids = self._recent_task_ids()
        tasks = self.selection_memory.setdefault("tasks", {})
        for task_file in selected:
            record = self._task_record(task_file)
            record["times_selected"] += 1
            record["last_selected_at"] = now
            record["last_run_id"] = run_id
            record["recent_selection_count"] = (
                record["recent_selection_count"] + 1
                if task_file in recent_task_ids
                else 1
            )
            tasks[task_file] = record
        self.selection_memory["run_counter"] = int(
            self.selection_memory.get("run_counter", 0)
        ) + 1
        self.selection_memory["previous_batch"] = list(selected)
        self.selection_memory["recent_runs"] = [
            *recent_runs[-max(self.task_cooldown_runs * 2, 1):],
            {
                "run_id": run_id,
                "task_ids": list(selected),
                "selected_at": now,
            },
        ]
        self._persist_selection_memory()

    def select_batch(
        self,
        task_files,
        concept_counts=None,
        concept_states=None,
        task_directory=None,
        observed_task_ids=None,
        core_knowledge=None,
        selection_mode=None,
        random_seed=None,
    ):
        task_files = self._normalized_tasks(task_files)
        if not task_files:
            raise ValueError("at least one JSON training task is required")
        selection_mode = self._selection_mode(
            selection_mode or self.selection_mode
        )
        original_random_seed = self.random_seed
        if random_seed is not None:
            self.random_seed = random_seed

        resumed = (
            selection_mode == "curriculum"
            and
            self._active_batch_is_valid(task_files)
            and (
                task_directory is None
                or
                self.state.get("curriculum_report", {})
                .get("training_diversity_report", {})
                .get("knowledge_expansion_score", 0.0)
                > 0.0
            )
        )
        run_id = f"selection-{uuid.uuid4()}"
        rng, effective_seed = self._rng_for_run()
        selection_report = dict(
            self.state.get("selection_diversity_report", {})
        )
        if resumed:
            selected = list(self.state["active_batch"])
            prioritized_concepts = list(
                self.state.get("prioritized_concepts", [])
            )
            selected_concepts = list(
                self.state.get("selected_concepts", [])
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
                history=self.state.get("history", []),
                core_knowledge=core_knowledge,
            )
            prioritized_concepts = curriculum_report[
                "prioritized_concepts"
            ]
            if selection_mode == "curriculum":
                selected = self.curriculum_manager.select_batch_tasks(
                    curriculum_report,
                    min(self.batch_size, len(task_files)),
                )
                previous_batch = set(
                    self.selection_memory.get("previous_batch", [])
                )
                selected_records = [
                    self._task_record(task_file)
                    for task_file in selected
                ]
                unseen_selected = sum(
                    1
                    for record in selected_records
                    if record["times_selected"] <= 0
                )
                average_frequency = (
                    sum(
                        record["times_selected"]
                        for record in selected_records
                    )
                    / len(selected_records)
                    if selected_records
                    else 0.0
                )
                previous_overlap = len(set(selected) & previous_batch)
                selection_report = {
                    "system": "training_selection_diversity",
                    "total_available_tasks": len(task_files),
                    "selected_tasks": list(selected),
                    "selection_mode": selection_mode,
                    "random_seed": effective_seed,
                    "run_id": run_id,
                    "previous_batch_overlap_count": previous_overlap,
                    "unseen_tasks_selected": unseen_selected,
                    "cooldown_filtered_tasks": 0,
                    "cooldown_filtered_task_ids": [],
                    "average_task_selection_frequency": round(
                        average_frequency,
                        4,
                    ),
                    "repeated_task_penalty_applied": False,
                    "diversity_score": self._selection_diversity_score(
                        selected,
                        previous_overlap,
                        unseen_selected,
                        average_frequency,
                    ),
                    "cooldown_window_runs": self.task_cooldown_runs,
                    "cooldown_relaxed": False,
                    "dataset_large": len(task_files)
                    > min(self.batch_size, len(task_files)) * 5,
                }
            else:
                selected, selection_report = self._randomized_select(
                    list(ranked_tasks or task_files),
                    min(self.batch_size, len(task_files)),
                    selection_mode,
                    rng,
                )
                selection_report["random_seed"] = effective_seed
                selection_report["run_id"] = run_id
            selected_concepts = sorted({
                concept
                for report in curriculum_report.get("task_priorities", [])
                if report.get("task_file") in selected
                for concept in report.get("target_concepts", [])
            })
            self.state["active_batch"] = selected
            self.state["prioritized_concepts"] = prioritized_concepts
            self.state["selected_concepts"] = selected_concepts
            self.state["curriculum_report"] = curriculum_report
            self.state["selection_diversity_report"] = selection_report
            self.state["pending_next_task_index"] = (
                start + len(selected)
            ) % len(task_files)
            self._persist()
            self._record_selection(selected, run_id)

        if random_seed is not None:
            self.random_seed = original_random_seed

        training_diversity_report = dict(
            curriculum_report.get("training_diversity_report")
            or self.state.get("curriculum_report", {}).get(
                "training_diversity_report",
                {},
            )
            or {}
        )
        if selection_report:
            training_diversity_report["selection_diversity_score"] = (
                selection_report.get("diversity_score", 0.0)
            )

        return {
            "system": "training_assistant",
            "training_mode":
            (
                selection_mode
                if selection_mode != "curriculum"
                else curriculum_report.get(
                    "training_mode",
                    "bounded_round_robin_batch",
                )
            ),
            "prioritized_concepts": prioritized_concepts,
            "selected_concepts": selected_concepts,
            "curriculum_report": curriculum_report,
            "training_diversity_report": training_diversity_report,
            "selection_diversity_report": selection_report,
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
        selected_concepts = list(self.state.get("selected_concepts", []))
        self.state["selected_concepts"] = []
        self.state["curriculum_report"] = {}
        self.state["selection_diversity_report"] = {}
        self.state["history"] = [
            *list(self.state.get("history", []))[-31:],
            {
                "cycle": completed_cycles,
                "task_files": active_batch,
                "concepts": selected_concepts,
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
            "selected_concepts":
            list(self.state.get("selected_concepts", [])),
            "selection_diversity_report": dict(
                self.state.get("selection_diversity_report", {})
            ),
            "selection_memory_path": str(self.selection_memory_path),
            "selection_mode": self.selection_mode,
            "history_size": len(self.state.get("history", [])),
            "state_path": str(self.state_path),
        }


__all__ = [
    "TrainingAssistant",
]
