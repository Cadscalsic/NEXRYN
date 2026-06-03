# ============================================
# NEXRYN ADAPTIVE TASK SCHEDULER
# ============================================

import json
from datetime import datetime
from pathlib import Path


# ============================================
# ADAPTIVE TASK SCHEDULER
# ============================================

class AdaptiveTaskScheduler:

    DEFAULT_TARGET_CONCEPT_COUNT = 20
    RARITY_WEIGHT = 10.0
    CURRICULUM_BONUS = {
        "phase_7_scarcity": 40,
        "phase_7_targeted": 20,
    }

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.scheduler_state = {

            "adaptive_scheduling":
            True,

            "cognitive_balancing":
            True,

            "priority_management":
            True,

            "load_distribution":
            True
        }

        self.schedule_history = []

        self.task_queue = []

    # ========================================
    # TASK METADATA
    # ========================================

    def _load_task_metadata(

        self,

        task_path,
        task_directory=None,
    ):

        task_file = Path(task_path)
        if not task_file.exists() and task_directory:
            task_file = Path(task_directory) / task_file.name

        if not task_file.exists():
            return {}

        try:
            with task_file.open("r", encoding="utf-8") as file:
                task = json.load(file)
            metadata = task.get("nexryn_metadata", {})
            return metadata if isinstance(metadata, dict) else {}
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return {}

    def _concept_rarity_score(

        self,

        target_concepts,
        concept_counts=None,
    ):

        if not isinstance(target_concepts, (list, tuple, set)):
            return 0.0

        score = 0.0
        for concept in target_concepts:
            if not isinstance(concept, str):
                continue
            if concept_counts is None:
                score += 1.0
            else:
                deficit = self.DEFAULT_TARGET_CONCEPT_COUNT - int(
                    concept_counts.get(concept, 0)
                )
                score += max(deficit, 1)

        return round(score, 4)

    def _curriculum_bonus(

        self,

        metadata,
    ):

        curriculum = metadata.get("curriculum", "")
        if not isinstance(curriculum, str):
            return 0

        normalized = curriculum.lower()
        bonus = 0
        for prefix, value in self.CURRICULUM_BONUS.items():
            if prefix in normalized:
                bonus = max(bonus, value)
        return bonus

    def _task_priority(

        self,

        task_path,
        concept_counts=None,
        task_directory=None,
    ):

        complexity_report = self.estimate_complexity(
            task_path
        )
        metadata = self._load_task_metadata(
            task_path,
            task_directory,
        )
        rarity_score = self._concept_rarity_score(
            metadata.get("target_concepts", []),
            concept_counts,
        )
        curriculum_bonus = self._curriculum_bonus(metadata)
        priority = (
            rarity_score * self.RARITY_WEIGHT
            + curriculum_bonus
            - complexity_report["complexity"]
        )

        return {
            **complexity_report,
            "rarity_score": rarity_score,
            "curriculum_bonus": curriculum_bonus,
            "priority": round(priority, 4),
        }

    # ========================================
    # ESTIMATE TASK COMPLEXITY
    # ========================================
    # ========================================

    def estimate_complexity(

        self,

        task_path
    ):

        complexity_score = 1.0

        if "001" in task_path:

            complexity_score = 0.20

        elif "002" in task_path:

            complexity_score = 0.30

        elif "003" in task_path:

            complexity_score = 0.40

        else:

            complexity_score = 0.75

        return {

            "task":
            task_path,

            "complexity":
            complexity_score
        }

    # ========================================
    # BUILD TASK QUEUE
    # ========================================

    def build_task_queue(

        self,

        task_paths,
        concept_counts=None,
        task_directory=None,
    ):

        scheduled_tasks = []

        for task_path in task_paths:

            task_report = self._task_priority(
                task_path,
                concept_counts=concept_counts,
                task_directory=task_directory,
            )

            scheduled_tasks.append(
                task_report
            )

        scheduled_tasks = sorted(

            scheduled_tasks,

            key=lambda x: (
                -x["priority"],
                x["complexity"],
                x["task"],
            )
        )

        self.task_queue = (
            scheduled_tasks
        )

        return scheduled_tasks

    # ========================================
    # GENERATE EXECUTION PLAN
    # ========================================

    def generate_execution_plan(

        self,

        task_paths,
        concept_counts=None,
        task_directory=None,
    ):

        scheduled_tasks = (

            self.build_task_queue(
                task_paths,
                concept_counts=concept_counts,
                task_directory=task_directory,
            )
        )

        execution_plan = {

            "scheduled_tasks":
            scheduled_tasks,

            "task_count":
            len(scheduled_tasks),

            "timestamp":
            str(datetime.utcnow())
        }

        self.schedule_history.append(
            execution_plan
        )

        return execution_plan

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "scheduler_state":
            self.scheduler_state,

            "scheduled_batches":

            len(
                self.schedule_history
            ),

            "queued_tasks":

            len(
                self.task_queue
            )
        }