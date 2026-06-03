# ============================================
# NEXRYN MEMORY MANAGER
# ============================================

from datetime import datetime

from runtime.memory import (
    WorkingMemory,
    EpisodicMemory,
    SemanticMemory,
    LongTermMemory
)


# ============================================
# MEMORY MANAGER
# ============================================

class MemoryManager:

    def __init__(self):

        # ====================================
        # MEMORY LAYERS
        # ====================================

        self.working_memory = (
            WorkingMemory()
        )

        self.episodic_memory = (
            EpisodicMemory()
        )

        self.semantic_memory = (
            SemanticMemory()
        )

        self.long_term_memory = (
            LongTermMemory()
        )

        # ====================================
        # MANAGER STATE
        # ====================================

        self.memory_state = {

            "memory_mode":
            "hierarchical_cognitive_memory",

            "working_memory":
            "active",

            "episodic_memory":
            "active",

            "semantic_memory":
            "active",

            "long_term_memory":
            "active",

            "cross_memory_routing":
            "enabled",

            "memory_persistence":
            "enabled"
        }

        # ====================================
        # MEMORY HISTORY
        # ====================================

        self.memory_history = []

    # ============================================
    # STORE WORKING MEMORY
    # ============================================

    def store_working_memory(

        self,

        key,

        value
    ):

        self.working_memory.store(

            key,

            value
        )

        self.memory_history.append({

            "memory_type":
            "working",

            "key":
            key,

            "timestamp":
            str(
                datetime.utcnow()
            )
        })

    # ============================================
    # STORE EPISODE
    # ============================================

    def store_episode(

        self,

        task_id,

        strategy,

        result,

        score=0.0
    ):

        episode = (

            self.episodic_memory.store_episode(

                task_id,

                strategy,

                result,

                score
            )
        )

        self.memory_history.append({

            "memory_type":
            "episodic",

            "task_id":
            task_id,

            "timestamp":
            str(
                datetime.utcnow()
            )
        })

        return episode

    # ============================================
    # STORE CONCEPT
    # ============================================

    def store_concept(

        self,

        concept_name,

        concept_data
    ):

        self.semantic_memory.store_concept(

            concept_name,

            concept_data
        )

        self.memory_history.append({

            "memory_type":
            "semantic",

            "concept":
            concept_name,

            "timestamp":
            str(
                datetime.utcnow()
            )
        })

    # ============================================
    # STORE LONG TERM MEMORY
    # ============================================

    def store_long_term_memory(

        self,

        memory_id,

        memory_data
    ):

        result = (

            self.long_term_memory.store_memory(

                memory_id,

                memory_data
            )
        )

        self.memory_history.append({

            "memory_type":
            "long_term",

            "memory_id":
            memory_id,

            "timestamp":
            str(
                datetime.utcnow()
            )
        })

        return result

    # ============================================
    # RETRIEVE
    # ============================================

    def retrieve(

        self,

        key
    ):

        # ====================================
        # WORKING MEMORY
        # ====================================

        result = (

            self.working_memory.retrieve(
                key
            )
        )

        if result is not None:

            return result

        # ====================================
        # SEMANTIC MEMORY
        # ====================================

        concept = (

            self.semantic_memory.retrieve_concept(
                key
            )
        )

        if concept is not None:

            return concept

        # ====================================
        # LONG TERM MEMORY
        # ====================================

        memory = (

            self.long_term_memory.retrieve_memory(
                key
            )
        )

        return memory

    # ============================================
    # MEMORY CONSOLIDATION
    # ============================================

    def consolidate_memory(self):

        best_episodes = (

            self.episodic_memory.best_strategies(
                limit=5
            )
        )

        consolidated = []

        for episode in best_episodes:

            concept_name = (

                f"strategy_"

                f"{episode['task_id']}"
            )

            concept_data = {

                "strategy":
                episode["strategy"],

                "score":
                episode["score"]
            }

            self.store_concept(

                concept_name,

                concept_data
            )

            consolidated.append(
                concept_name
            )

        return {

            "consolidated":
            consolidated,

            "count":
            len(consolidated)
        }

    # ============================================
    # BUILD MEMORY GRAPH
    # ============================================

    def build_memory_graph(self):

        nodes = [

            {

                "node":
                "working_memory",

                "state":
                "active"
            },

            {

                "node":
                "episodic_memory",

                "state":
                "active"
            },

            {

                "node":
                "semantic_memory",

                "state":
                "active"
            },

            {

                "node":
                "long_term_memory",

                "state":
                "active"
            }
        ]

        edges = [

            {

                "source":
                "working_memory",

                "target":
                "episodic_memory"
            },

            {

                "source":
                "episodic_memory",

                "target":
                "semantic_memory"
            },

            {

                "source":
                "semantic_memory",

                "target":
                "long_term_memory"
            }
        ]

        return {

            "nodes":
            nodes,

            "edges":
            edges,

            "graph_mode":
            "hierarchical_memory_graph"
        }

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        return {

            "memory_state":
            self.memory_state,

            "working_memory":
            self.working_memory.build_report(),

            "episodic_memory":
            self.episodic_memory.build_report(),

            "semantic_memory":
            self.semantic_memory.build_report(),

            "long_term_memory":
            self.long_term_memory.build_report(),

            "memory_graph":
            self.build_memory_graph(),

            "memory_cycles":
            len(
                self.memory_history
            )
        }


# ============================================
# GLOBAL MEMORY MANAGER
# ============================================

memory_manager = (
    MemoryManager()
)