# ============================================
# NEXRYN PERSISTENT MEMORY ENGINE
# ============================================

from datetime import datetime

from runtime.memory.memory_store import (
    MemoryStore
)

from runtime.memory.experience_manager import (
    ExperienceManager
)

from runtime.memory.adaptive_memory import (
    AdaptiveMemory
)

from runtime.memory.reinforcement_memory import (
    ReinforcementMemory
)


# ============================================
# PERSISTENT MEMORY ENGINE
# ============================================

class PersistentMemoryEngine:

    def __init__(self):

        # ========================================
        # CORE MEMORY SYSTEMS
        # ========================================

        self.memory_store = (
            MemoryStore()
        )

        self.experience_manager = (
            ExperienceManager()
        )

        self.adaptive_memory = (
            AdaptiveMemory()
        )

        self.reinforcement_memory = (
            ReinforcementMemory()
        )

        # ========================================
        # MEMORY STATE
        # ========================================

        self.memory_state = {

            "memory_mode":
            "persistent_recursive",

            "episodic_memory":
            "active",

            "semantic_memory":
            "active",

            "adaptive_memory":
            "active",

            "reinforcement_memory":
            "active",

            "memory_consolidation":
            "enabled",

            "recursive_recall":
            "adaptive",

            "cross_memory_sync":
            "enabled",

            "memory_cycles":
            0,

            "memory_stability":
            "stable"
        }

        # ========================================
        # CONSOLIDATED MEMORY
        # ========================================

        self.consolidated_memories = []

        # ========================================
        # RECALL HISTORY
        # ========================================

        self.recall_history = []

    # ============================================
    # STORE RUNTIME EPISODE
    # ============================================

    def store_runtime_episode(

        self,

        runtime_context
    ):

        episode = {

            "dominant_reasoning":

            runtime_context.get(

                "recursive_report",

                {}
            ).get(
                "dominant_reasoning"
            ),

            "dominant_strategy":

            runtime_context.get(

                "identity_report",

                {}
            ).get(

                "identity_state",

                {}
            ).get(
                "dominant_strategy"
            ),

            "trajectory_score":

            runtime_context.get(

                "trajectory_score",

                {}
            ),

            "evaluation_result":

            runtime_context.get(

                "evaluation_result",

                {}
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        # ========================================
        # STORE EPISODE
        # ========================================

        self.memory_store.store_episode(
            episode
        )

        return episode

    # ============================================
    # STORE KNOWLEDGE
    # ============================================

    def store_knowledge(

        self,

        knowledge_expansion_report
    ):

        knowledge = {

            "abstractions":

            knowledge_expansion_report.get(

                "abstractions",

                []
            ),

            "fused_knowledge":

            knowledge_expansion_report.get(

                "fused_knowledge",

                []
            ),

            "semantic_relations":

            knowledge_expansion_report.get(

                "semantic_relations",

                []
            ),

            "knowledge_depth":

            knowledge_expansion_report.get(

                "knowledge_depth",

                0
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        # ========================================
        # STORE LONG TERM MEMORY
        # ========================================

        self.memory_store.store_long_term(
            knowledge
        )

        return knowledge

    # ============================================
    # CONSOLIDATE MEMORY
    # ============================================

    def consolidate_memory(

        self,

        episode,

        knowledge
    ):

        consolidated = {

            "memory_id":

            len(
                self.consolidated_memories
            ) + 1,

            "reasoning":

            episode.get(
                "dominant_reasoning"
            ),

            "strategy":

            episode.get(
                "dominant_strategy"
            ),

            "knowledge_depth":

            knowledge.get(
                "knowledge_depth",
                0
            ),

            "abstraction_count":

            len(

                knowledge.get(
                    "abstractions",
                    []
                )
            ),

            "fusion_count":

            len(

                knowledge.get(
                    "fused_knowledge",
                    []
                )
            ),

            "memory_strength":
            "stable",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.consolidated_memories.append(
            consolidated
        )

        return consolidated

    # ============================================
    # REGISTER EXPERIENCE
    # ============================================

    def register_experience(

        self,

        runtime_context
    ):

        self.experience_manager.store_experience(
            runtime_context
        )

    # ============================================
    # REINFORCE SUCCESSFUL HYPOTHESES
    # ============================================

    def reinforce_hypotheses(

        self,

        runtime_context
    ):

        hypotheses = (

            runtime_context.get(

                "hypotheses",

                []
            )
        )

        evaluation_result = (

            runtime_context.get(

                "evaluation_result",

                {}
            )
        )

        for hypothesis in hypotheses:

            self.reinforcement_memory.store_experience(

                hypothesis=
                hypothesis,

                evaluation_result=
                evaluation_result
            )

    # ============================================
    # RECALL MEMORY
    # ============================================

    def recall_memory(

        self,

        patterns
    ):

        recalled = (

            self.experience_manager.find_similar_experiences(

                patterns
            )
        )

        recall_event = {

            "patterns":
            patterns,

            "matches":
            len(recalled),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.recall_history.append(
            recall_event
        )

        return recalled

    # ============================================
    # RUN MEMORY CYCLE
    # ============================================

    def run_memory_cycle(

        self,

        runtime_context,

        knowledge_expansion_report
    ):

        # ========================================
        # STORE RUNTIME EPISODE
        # ========================================

        episode = (

            self.store_runtime_episode(

                runtime_context
            )
        )

        # ========================================
        # STORE KNOWLEDGE
        # ========================================

        knowledge = (

            self.store_knowledge(

                knowledge_expansion_report
            )
        )

        # ========================================
        # CONSOLIDATE MEMORY
        # ========================================

        consolidated_memory = (

            self.consolidate_memory(

                episode=
                episode,

                knowledge=
                knowledge
            )
        )

        # ========================================
        # REGISTER EXPERIENCE
        # ========================================

        self.register_experience(
            runtime_context
        )

        # ========================================
        # REINFORCEMENT LEARNING
        # ========================================

        self.reinforce_hypotheses(
            runtime_context
        )

        # ========================================
        # MEMORY RECALL
        # ========================================

        recalled_memories = (

            self.recall_memory(

                runtime_context.get(

                    "patterns",

                    []
                )
            )
        )

        # ========================================
        # BUILD MEMORY REPORT
        # ========================================

        memory_report = {

            "episode":
            episode,

            "knowledge":
            knowledge,

            "consolidated_memory":
            consolidated_memory,

            "recalled_memories":
            recalled_memories,

            "memory_growth":
            "active",

            "memory_state":
            "stable",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        # ========================================
        # UPDATE MEMORY CYCLES
        # ========================================

        self.memory_state[
            "memory_cycles"
        ] += 1

        return memory_report

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        return {

            "memory_state":
            self.memory_state,

            "short_term_memory":

            len(

                self.memory_store.get_short_term_memory()
            ),

            "long_term_memory":

            len(

                self.memory_store.get_long_term_memory()
            ),

            "episodic_memory":

            len(

                self.memory_store.get_episodic_memory()
            ),

            "stored_experiences":

            self.experience_manager.get_experience_count(),

            "reinforcement_memory":

            self.reinforcement_memory.memory_size(),

            "consolidated_memories":

            len(
                self.consolidated_memories
            ),

            "recall_events":

            len(
                self.recall_history
            ),

            "latest_memory":

            self.consolidated_memories[-1]

            if self.consolidated_memories

            else {}
        }


# ============================================
# GLOBAL PERSISTENT MEMORY ENGINE
# ============================================

persistent_memory_engine = (
    PersistentMemoryEngine()
)