# ============================================
# NEXRYN MEMORY RETRIEVAL ENGINE
# ============================================

import os
import gc
import json

from datetime import datetime

from runtime.memory.semantic_experience_index import (

    semantic_experience_index
)


# ============================================
# MEMORY RETRIEVAL ENGINE
# ============================================

class MemoryRetrievalEngine:

    # ========================================
    # INITIALIZE ENGINE
    # ========================================

    def __init__(self):

        # ====================================
        # EXPERIENCE STORAGE
        # ====================================

        self.experience_path = (
            "runtime/memory/storage/experiences"
        )

        # ====================================
        # MEMORY ARCHIVE
        # ====================================

        self.memory_archive = []

        # ====================================
        # RETRIEVAL STATE
        # ====================================

        self.retrieval_state = {

            "retrieval_mode":
            "conceptual_semantic_recall",

            "adaptive_similarity":
            True,

            "strategy_reuse":
            True,

            "semantic_matching":
            True,

            "conceptual_retrieval":
            True,

            "transfer_learning":
            True,

            "memory_indexing":
            True,

            "retrieval_cycles":
            0,

            "indexing_cycles":
            0
        }

        # ====================================
        # RETRIEVAL HISTORY
        # ====================================

        self.retrieval_history = []

        # ====================================
        # INDEX HISTORY
        # ====================================

        self.index_history = []

    # ========================================
    # INDEX MEMORY
    # ========================================

    def index_memory(

        self,

        runtime_context
    ):

        # ====================================
        # SAFE CONTEXT NORMALIZATION
        # ====================================

        if runtime_context is None:

            return {

                "index_state":
                "skipped",

                "reason":
                "runtime_context_none"
            }

        if not isinstance(
            runtime_context,
            dict
        ):

            return {

                "index_state":
                "invalid",

                "reason":
                "runtime_context_not_dict"
            }

        # ====================================
        # MEMORY SNAPSHOT
        # ====================================

        memory_snapshot = {

            "winner_hypothesis":

            runtime_context.get(
                "winner_hypothesis",
                {}
            ),

            "semantic_summary":

            runtime_context.get(
                "semantic_summary",
                {}
            ),

            "execution_plan":

            runtime_context.get(
                "execution_plan",
                {}
            ),

            "evaluation_result":

            runtime_context.get(
                "evaluation_result",
                {}
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        # ====================================
        # ARCHIVE STORAGE
        # ====================================

        self.memory_archive.append(
            memory_snapshot
        )

        # ====================================
        # SEMANTIC EXPERIENCE INDEX
        # ====================================

        try:

            if hasattr(

                semantic_experience_index,

                "index_experience"
            ):

                semantic_experience_index.index_experience(

                    memory_snapshot
                )

        except Exception:

            pass

        # ====================================
        # INDEX HISTORY
        # ====================================

        self.index_history.append({

            "index_state":
            "stored",

            "archive_size":
            len(self.memory_archive),

            "timestamp":
            str(datetime.utcnow())
        })

        # ====================================
        # UPDATE STATE
        # ====================================

        self.retrieval_state[
            "indexing_cycles"
        ] += 1

        # ====================================
        # MEMORY BALANCING
        # ====================================

        if len(self.memory_archive) > 500:

            self.memory_archive = (

                self.memory_archive[-250:]
            )

            gc.collect()

        # ====================================
        # FINAL REPORT
        # ====================================

        return {

            "index_state":
            "stored",

            "archive_size":
            len(self.memory_archive),

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # LOAD EXPERIENCE FILE
    # ========================================

    def load_experience_file(

        self,

        file_path
    ):

        try:

            with open(

                file_path,

                "r",

                encoding="utf-8"
            ) as file:

                return json.load(
                    file
                )

        except Exception:

            return None

    # ========================================
    # LOAD EXPERIENCES
    # ========================================

    def load_experiences(self):

        experiences = []

        if not os.path.exists(
            self.experience_path
        ):

            return experiences

        for file_name in os.listdir(

            self.experience_path
        ):

            if not file_name.endswith(
                ".json"
            ):

                continue

            file_path = (

                f"{self.experience_path}/"
                f"{file_name}"
            )

            loaded = self.load_experience_file(
                file_path
            )

            if loaded:

                experiences.append(
                    loaded
                )

        # ====================================
        # ARCHIVE EXPERIENCES
        # ====================================

        experiences.extend(
            self.memory_archive
        )

        return experiences

    # ========================================
    # COMPUTE SIMILARITY
    # ========================================

    def compute_similarity(

        self,

        runtime_context,

        experience
    ):

        similarity_score = 0.0

        # ====================================
        # WINNER HYPOTHESIS
        # ====================================

        current_hypothesis = (

            runtime_context.get(
                "winner_hypothesis",
                {}
            )
        )

        stored_hypothesis = (

            experience.get(
                "winner_hypothesis"
            ) or {}
        )

        if current_hypothesis.get(
            "type"
        ) == stored_hypothesis.get(
            "type"
        ):

            similarity_score += 0.4

        # ====================================
        # SEMANTIC SUMMARY
        # ====================================

        current_semantic = (

            runtime_context.get(
                "semantic_summary",
                {}
            )
        )

        stored_semantic = (

            experience.get(
                "semantic_summary"
            ) or {}
        )

        if current_semantic == stored_semantic:

            similarity_score += 0.3

        # ====================================
        # EXECUTION PLAN
        # ====================================

        current_plan = (

            runtime_context.get(
                "execution_plan",
                {}
            )
        )

        stored_plan = (

            experience.get(
                "execution_plan"
            ) or {}
        )

        if current_plan.get(
            "node_count"
        ) == stored_plan.get(
            "node_count"
        ):

            similarity_score += 0.2

        # ====================================
        # EVALUATION RESULT
        # ====================================

        current_evaluation = (

            runtime_context.get(
                "evaluation_result",
                {}
            )
        )

        stored_evaluation = (

            experience.get(
                "evaluation_result"
            ) or {}
        )

        if current_evaluation.get(
            "success"
        ) == stored_evaluation.get(
            "success"
        ):

            similarity_score += 0.1

        return round(
            similarity_score,
            4
        )

    # ========================================
    # RETRIEVE SIMILAR EXPERIENCES
    # ========================================

    def retrieve_similar_experiences(

        self,

        runtime_context,

        similarity_threshold=0.5
    ):

        # ====================================
        # SAFE CONTEXT
        # ====================================

        if runtime_context is None:

            runtime_context = {}

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        # ====================================
        # LOAD EXPERIENCES
        # ====================================

        experiences = (
            self.load_experiences()
        )

        # ====================================
        # SEMANTIC CONCEPT RETRIEVAL
        # ====================================

        semantic_graph = (

            runtime_context.get(
                "semantic_graph"
            )

            or {}
        )

        concept_nodes = (

            semantic_graph.get(
                "concept_nodes",
                []
            )
        )

        semantic_concepts = []

        for node in concept_nodes:

            if not isinstance(
                node,
                dict
            ):

                continue

            concept = node.get(
                "concept"
            )

            if concept:

                semantic_concepts.append(
                    concept
                )

        # ====================================
        # CONCEPTUAL MATCHES
        # ====================================

        try:

            conceptual_matches = (

                semantic_experience_index
                .retrieve_by_concepts(

                    semantic_concepts
                )
            )

        except Exception:

            conceptual_matches = []

        # ====================================
        # MERGE EXPERIENCES
        # ====================================

        experiences.extend(
            conceptual_matches
        )

        # ====================================
        # REMOVE DUPLICATES
        # ====================================

        unique_experiences = []

        seen = set()

        for item in experiences:

            identifier = str(
                id(item)
            )

            if identifier in seen:

                continue

            seen.add(
                identifier
            )

            unique_experiences.append(
                item
            )

        experiences = unique_experiences

        # ====================================
        # SIMILARITY SEARCH
        # ====================================

        retrieved = []

        for experience in experiences:

            if not isinstance(
                experience,
                dict
            ):

                continue

            similarity = (

                self.compute_similarity(

                    runtime_context,

                    experience
                )
            )

            if similarity >= (
                similarity_threshold
            ):

                retrieved.append({

                    "similarity":
                    similarity,

                    "experience":
                    experience
                })

        # ====================================
        # SORT RESULTS
        # ====================================

        retrieved = sorted(

            retrieved,

            key=lambda item:
            item["similarity"],

            reverse=True
        )

        # ====================================
        # UPDATE HISTORY
        # ====================================

        self.retrieval_history.append({

            "retrieved_count":
            len(retrieved),

            "semantic_concepts":
            semantic_concepts,

            "timestamp":
            str(datetime.utcnow())
        })

        self.retrieval_state[
            "retrieval_cycles"
        ] += 1

        # ====================================
        # RETURN RESULTS
        # ====================================

        return retrieved

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "retrieval_state":
            self.retrieval_state,

            "retrieval_history":
            len(
                self.retrieval_history
            ),

            "index_history":
            len(
                self.index_history
            ),

            "memory_archive_size":
            len(
                self.memory_archive
            ),

            "timestamp":
            str(datetime.utcnow())
        }
        # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return self.build_report()



# ============================================
# GLOBAL RETRIEVAL ENGINE
# ============================================

memory_retrieval_engine = (
    MemoryRetrievalEngine()
)