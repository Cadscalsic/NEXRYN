# ============================================
# NEXRYN PERSISTENT COGNITIVE MEMORY
# ============================================

import os
import json
import uuid

from datetime import datetime


# ============================================
# PERSISTENT COGNITIVE MEMORY
# ============================================

class PersistentCognitiveMemory:

    # ========================================
    # INITIALIZE MEMORY
    # ========================================

    def __init__(self):

        # ====================================
        # MEMORY PATHS
        # ====================================

        self.memory_root = (
            "runtime/memory/storage"
        )

        self.strategy_path = (
            f"{self.memory_root}/strategies"
        )

        self.semantic_path = (
            f"{self.memory_root}/semantic"
        )

        self.experience_path = (
            f"{self.memory_root}/experiences"
        )

        self.archive_path = (
            f"{self.memory_root}/archive"
        )

        # ====================================
        # CREATE STORAGE
        # ====================================

        self.initialize_storage()

        # ====================================
        # MEMORY STATE
        # ====================================

        self.memory_state = {

            "memory_mode":
            "persistent_cognitive_memory",

            "strategy_persistence":
            "enabled",

            "semantic_persistence":
            "enabled",

            "experience_indexing":
            "enabled",

            "long_term_memory":
            "enabled",

            "memory_cycles":
            0
        }

        # ====================================
        # MEMORY HISTORY
        # ====================================

        self.memory_history = []

    # ========================================
    # INITIALIZE STORAGE
    # ========================================

    def initialize_storage(self):

        os.makedirs(
            self.memory_root,
            exist_ok=True
        )

        os.makedirs(
            self.strategy_path,
            exist_ok=True
        )

        os.makedirs(
            self.semantic_path,
            exist_ok=True
        )

        os.makedirs(
            self.experience_path,
            exist_ok=True
        )

        os.makedirs(
            self.archive_path,
            exist_ok=True
        )

    # ========================================
    # SAVE JSON
    # ========================================

    def save_json(

        self,

        path,

        data
    ):

        try:

            with open(

                path,

                "w",

                encoding="utf-8"

            ) as file:

                json.dump(

                    data,

                    file,

                    indent=4,

                    ensure_ascii=False
                )

            return True

        except Exception as error:

            return {

                "save_error":
                repr(error)
            }

    # ========================================
    # LOAD JSON
    # ========================================

    def load_json(

        self,

        path
    ):

        try:

            if not os.path.exists(
                path
            ):

                return None

            with open(

                path,

                "r",

                encoding="utf-8"

            ) as file:

                return json.load(
                    file
                )

        except Exception:

            return None

    # ========================================
    # SAVE STRATEGY
    # ========================================

    def save_strategy(

        self,

        strategy
    ):

        if not isinstance(
            strategy,
            dict
        ):

            return None

        strategy_name = strategy.get(

            "type",

            "unknown_strategy"
        )

        strategy_id = str(
            uuid.uuid4()
        )

        strategy_data = {

            "strategy_id":
            strategy_id,

            "strategy":
            strategy,

            "timestamp":
            str(datetime.utcnow())
        }

        file_path = (

            f"{self.strategy_path}/"

            f"{strategy_name}_"

            f"{strategy_id}.json"
        )

        self.save_json(

            file_path,

            strategy_data
        )

        self.memory_history.append({

            "memory_event":
            "strategy_saved",

            "strategy":
            strategy_name,

            "timestamp":
            str(datetime.utcnow())
        })

        return strategy_data

    # ========================================
    # SAVE SEMANTIC MEMORY
    # ========================================

    def save_semantic_memory(

        self,

        semantic_memory
    ):

        memory_id = str(
            uuid.uuid4()
        )

        semantic_data = {

            "memory_id":
            memory_id,

            "semantic_memory":
            semantic_memory,

            "timestamp":
            str(datetime.utcnow())
        }

        file_path = (

            f"{self.semantic_path}/"

            f"semantic_{memory_id}.json"
        )

        self.save_json(

            file_path,

            semantic_data
        )

        self.memory_history.append({

            "memory_event":
            "semantic_saved",

            "timestamp":
            str(datetime.utcnow())
        })

        return semantic_data

    # ========================================
    # SAVE EXPERIENCE
    # ========================================

    def save_experience(

        self,

        runtime_context
    ):

        experience_id = str(
            uuid.uuid4()
        )

        experience = {

            "experience_id":
            experience_id,

            "winner_hypothesis":

            runtime_context.get(
                "winner_hypothesis"
            ),

            "evaluation_result":

            runtime_context.get(
                "evaluation_result"
            ),

            "best_evolved_strategy":

            runtime_context.get(
                "best_evolved_strategy"
            ),

            "semantic_summary":

            runtime_context.get(
                "semantic_summary"
            ),

            "semantic_graph":

            runtime_context.get(
                "semantic_graph"
            ),

            "execution_plan":

            runtime_context.get(
                "execution_plan"
            ),

            "reasoning_trace":

            runtime_context.get(
                "reasoning_trace"
            ),

            "cognitive_pressure":

            runtime_context.get(
                "cognitive_pressure"
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        file_path = (

            f"{self.experience_path}/"

            f"experience_{experience_id}.json"
        )

        self.save_json(

            file_path,

            experience
        )

        self.memory_history.append({

            "memory_event":
            "experience_saved",

            "timestamp":
            str(datetime.utcnow())
        })

        return experience

    # ========================================
    # RETRIEVE SIMILAR STRATEGIES
    # ========================================

    def retrieve_similar_strategies(

        self,

        strategy_type
    ):

        retrieved = []

        if not os.path.exists(
            self.strategy_path
        ):

            return retrieved

        for file_name in os.listdir(

            self.strategy_path
        ):

            if strategy_type in file_name:

                file_path = (

                    f"{self.strategy_path}/"
                    f"{file_name}"
                )

                loaded = self.load_json(
                    file_path
                )

                if loaded:

                    retrieved.append(
                        loaded
                    )

        return retrieved

    # ========================================
    # LOAD EXPERIENCE HISTORY
    # ========================================

    def load_experience_history(self):

        experiences = []

        if not os.path.exists(
            self.experience_path
        ):

            return experiences

        for file_name in os.listdir(

            self.experience_path
        ):

            file_path = (

                f"{self.experience_path}/"
                f"{file_name}"
            )

            loaded = self.load_json(
                file_path
            )

            if loaded:

                experiences.append(
                    loaded
                )

        return experiences

    # ========================================
    # BUILD MEMORY SUMMARY
    # ========================================

    def build_memory_summary(self):

        strategy_count = len(

            os.listdir(
                self.strategy_path
            )
        )

        semantic_count = len(

            os.listdir(
                self.semantic_path
            )
        )

        experience_count = len(

            os.listdir(
                self.experience_path
            )
        )

        return {

            "strategy_memories":
            strategy_count,

            "semantic_memories":
            semantic_count,

            "experience_memories":
            experience_count,

            "memory_cycles":

            self.memory_state.get(
                "memory_cycles",
                0
            ),

            "memory_mode":
            "persistent_cognitive_memory"
        }

    # ========================================
    # RUN MEMORY CYCLE
    # ========================================

    def run_memory_cycle(

        self,

        runtime_context
    ):

        # ====================================
        # WINNER HYPOTHESIS
        # ====================================

        winner_hypothesis = (

            runtime_context.get(
                "winner_hypothesis"
            )
        )

        # ====================================
        # SAVE STRATEGY
        # ====================================

        strategy_saved = False

        if winner_hypothesis:

            self.save_strategy(
                winner_hypothesis
            )

            strategy_saved = True

        # ====================================
        # SEMANTIC SUMMARY
        # ====================================

        semantic_summary = (

            runtime_context.get(
                "semantic_summary"
            )
        )

        # ====================================
        # SAVE SEMANTIC MEMORY
        # ====================================

        semantic_saved = False

        if semantic_summary:

            self.save_semantic_memory(

                semantic_summary
            )

            semantic_saved = True

        # ====================================
        # SAVE EXPERIENCE
        # ====================================

        experience = (

            self.save_experience(
                runtime_context
            )
        )

        experience_saved = (
            experience is not None
        )

        # ====================================
        # MEMORY REPORT
        # ====================================

        memory_report = {

            "memory_cycle":
            "completed",

            "strategy_saved":
            strategy_saved,

            "semantic_saved":
            semantic_saved,

            "experience_saved":
            experience_saved,

            "winner_strategy":

            winner_hypothesis.get(
                "type",
                "unknown"
            )

            if winner_hypothesis

            else None,

            "memory_summary":

            self.build_memory_summary(),

            "runtime_context_size":

            len(
                runtime_context
            ),

            "memory_state":
            "stable",

            "timestamp":
            str(datetime.utcnow())
        }

        # ====================================
        # MEMORY HISTORY
        # ====================================

        self.memory_history.append({

            "memory_event":
            "memory_cycle_completed",

            "strategy_saved":
            strategy_saved,

            "semantic_saved":
            semantic_saved,

            "experience_saved":
            experience_saved,

            "timestamp":
            str(datetime.utcnow())
        })

        # ====================================
        # UPDATE MEMORY CYCLES
        # ====================================

        self.memory_state[
            "memory_cycles"
        ] += 1

        return memory_report

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "memory_state":
            self.memory_state,

            "memory_summary":

            self.build_memory_summary(),

            "history_size":

            len(
                self.memory_history
            ),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL PERSISTENT MEMORY
# ============================================

persistent_cognitive_memory = (
    PersistentCognitiveMemory()
)