# =========================================================
# NEXRYN RECURSIVE AUTONOMOUS RESEARCH ENGINE
# =========================================================

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime

import time
import uuid


# =========================================================
# RESEARCH OBJECT
# =========================================================

@dataclass
class ResearchTask:

    task_id: str

    topic: str

    objective: str

    priority: float = 1.0

    status: str = "pending"

    recursion_depth: int = 0

    parent_task: str = None

    novelty_score: float = 0.0

    cognitive_gain: float = 0.0

    created_at: float = field(
        default_factory=time.time
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


# =========================================================
# AUTONOMOUS RESEARCH ENGINE
# =========================================================

class AutonomousResearchEngine:

    def __init__(self):

        # =================================================
        # RESEARCH MEMORY
        # =================================================

        self.research_queue = []

        self.completed_research = []

        self.failed_research = []

        self.research_memory = []

        self.discovery_graph = []

        self.generated_hypotheses = []

        # =================================================
        # ENGINE STATE
        # =================================================

        self.engine_state = {

            "research_mode":
            "recursive_autonomous_cognition",

            "runtime_state":
            "stable",

            "active_tasks":
            0,

            "completed_tasks":
            0,

            "failed_tasks":
            0,

            "recursive_expansion":
            "enabled",

            "curiosity_engine":
            "active",

            "novelty_detection":
            "enabled",

            "cognitive_growth":
            "active"
        }

    # =====================================================
    # CREATE RESEARCH TASK
    # =====================================================

    def create_research_task(

        self,

        topic,

        objective,

        priority=1.0,

        recursion_depth=0,

        parent_task=None,

        metadata=None
    ):

        novelty_score = self.compute_novelty(
            topic
        )

        task = ResearchTask(

            task_id=str(uuid.uuid4()),

            topic=topic,

            objective=objective,

            priority=priority,

            recursion_depth=recursion_depth,

            parent_task=parent_task,

            novelty_score=novelty_score,

            metadata=metadata or {}
        )

        self.research_queue.append(
            task
        )

        self.engine_state[
            "active_tasks"
        ] += 1

        return task

    # =====================================================
    # COMPUTE NOVELTY
    # =====================================================

    def compute_novelty(

        self,

        topic
    ):

        existing_topics = [

            task.topic.lower()

            for task in self.completed_research
        ]

        if topic.lower() not in existing_topics:

            return 0.95

        return 0.45

    # =====================================================
    # PRIORITIZE TASKS
    # =====================================================

    def prioritize_tasks(self):

        self.research_queue.sort(

            key=lambda task:

            (
                task.priority
                +
                task.novelty_score
            ),

            reverse=True
        )

    # =====================================================
    # GENERATE RESEARCH HYPOTHESES
    # =====================================================

    def generate_hypotheses(

        self,

        task
    ):

        hypotheses = []

        topic = task.topic.lower()

        # -------------------------------------------------
        # REASONING
        # -------------------------------------------------

        if "reasoning" in topic:

            hypotheses.append({

                "type":
                "symbolic_reasoning",

                "confidence":
                0.92,

                "complexity":
                "high"
            })

            hypotheses.append({

                "type":
                "recursive_reasoning",

                "confidence":
                0.88,

                "complexity":
                "very_high"
            })

        # -------------------------------------------------
        # VISION
        # -------------------------------------------------

        if "vision" in topic:

            hypotheses.append({

                "type":
                "visual_perception",

                "confidence":
                0.90,

                "complexity":
                "medium"
            })

        # -------------------------------------------------
        # ABSTRACTION
        # -------------------------------------------------

        if "abstraction" in topic:

            hypotheses.append({

                "type":
                "hierarchical_abstraction",

                "confidence":
                0.94,

                "complexity":
                "high"
            })

        # -------------------------------------------------
        # GENERAL
        # -------------------------------------------------

        if not hypotheses:

            hypotheses.append({

                "type":
                "general_research",

                "confidence":
                0.50,

                "complexity":
                "low"
            })

        self.generated_hypotheses.extend(
            hypotheses
        )

        return hypotheses

    # =====================================================
    # GENERATE SUBTASKS
    # =====================================================

    def generate_subtasks(

        self,

        task,

        hypotheses
    ):

        subtasks = []

        if task.recursion_depth >= 2:

            return subtasks

        for hypothesis in hypotheses:

            subtask = self.create_research_task(

                topic=hypothesis["type"],

                objective=
                f"expand_{hypothesis['type']}",

                priority=0.8,

                recursion_depth=
                task.recursion_depth + 1,

                parent_task=
                task.task_id
            )

            subtasks.append(
                subtask
            )

        return subtasks

    # =====================================================
    # EXECUTE RESEARCH TASK
    # =====================================================

    def execute_task(

        self,

        task
    ):

        task.status = "running"

        hypotheses = (

            self.generate_hypotheses(
                task
            )
        )

        best_hypothesis = max(

            hypotheses,

            key=lambda h:
            h["confidence"]
        )

        cognitive_gain = round(

            best_hypothesis[
                "confidence"
            ]
            *
            task.novelty_score,

            2
        )

        task.cognitive_gain = (
            cognitive_gain
        )

        generated_subtasks = (

            self.generate_subtasks(

                task,

                hypotheses
            )
        )

        result = {

            "task_id":
            task.task_id,

            "topic":
            task.topic,

            "objective":
            task.objective,

            "hypotheses":
            hypotheses,

            "selected_hypothesis":
            best_hypothesis,

            "generated_subtasks":
            len(generated_subtasks),

            "research_depth":
            len(hypotheses) * 3,

            "novelty_score":
            task.novelty_score,

            "cognitive_gain":
            cognitive_gain,

            "success":
            True
        }

        task.status = "completed"

        self.completed_research.append(
            task
        )

        self.research_memory.append(
            result
        )

        self.discovery_graph.append({

            "task":
            task.topic,

            "children":

            [

                subtask.topic

                for subtask in generated_subtasks
            ]
        })

        self.engine_state[
            "completed_tasks"
        ] += 1

        self.engine_state[
            "active_tasks"
        ] -= 1

        return result

    # =====================================================
    # EXECUTE RESEARCH CYCLE
    # =====================================================

    def run_cycle(self):

        self.prioritize_tasks()

        results = []

        for task in list(self.research_queue):

            try:

                result = self.execute_task(
                    task
                )

                results.append(
                    result
                )

                self.research_queue.remove(
                    task
                )

            except Exception as error:

                task.status = "failed"

                self.failed_research.append(
                    task
                )

                self.engine_state[
                    "failed_tasks"
                ] += 1

                results.append({

                    "task_id":
                    task.task_id,

                    "success":
                    False,

                    "error":
                    str(error)
                })

        return results

    # =====================================================
    # BUILD DISCOVERY REPORT
    # =====================================================

    def build_discovery_report(self):

        return {

            "research_memory":
            len(self.research_memory),

            "discovery_graph":
            self.discovery_graph,

            "generated_hypotheses":
            len(self.generated_hypotheses),

            "recursive_research":
            "active"
        }

    # =====================================================
    # ENGINE REPORT
    # =====================================================

    def generate_report(self):

        return {

            "engine_state":
            self.engine_state,

            "queued_tasks":
            len(self.research_queue),

            "completed_research":
            len(self.completed_research),

            "failed_research":
            len(self.failed_research),

            "research_memory":
            len(self.research_memory),

            "discovery_graph":
            len(self.discovery_graph),

            "runtime_health":
            "stable",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }