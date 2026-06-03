# ============================================
# NEXRYN SYMBOLIC MEMORY RUNTIME
# ============================================

import json
import os

from datetime import datetime


# ============================================
# SYMBOLIC MEMORY
# ============================================

class SymbolicMemory:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(

        self,

        memory_path=
        "data/generated/memory.json"
    ):

        self.memory_path = (
            memory_path
        )

        # ====================================
        # MEMORY STORAGE
        # ====================================

        self.memories = []

        # ====================================
        # MEMORY METADATA
        # ====================================

        self.memory_state = {

            "persistent_memory":
            True,

            "semantic_retrieval":
            True,

            "memory_consolidation":
            True,

            "adaptive_memory":
            True,

            "memory_loaded":
            False
        }

        # ====================================
        # MEMORY INDEX
        # ====================================

        self.memory_index = {}

        # ====================================
        # MEMORY TELEMETRY
        # ====================================

        self.memory_telemetry = {

            "writes":
            0,

            "retrievals":
            0,

            "consolidations":
            0
        }

        # ====================================
        # LOAD MEMORY
        # ====================================

        self._load_memory()

    # ========================================
    # LOAD MEMORY
    # ========================================

    def _load_memory(self):

        if not os.path.exists(
            self.memory_path
        ):

            self.memories = []

            return

        try:

            with open(

                self.memory_path,

                "r",

                encoding="utf-8"
            ) as file:

                self.memories = (
                    json.load(file)
                )

            self.memory_state[
                "memory_loaded"
            ] = True

            self._build_index()

        except Exception:

            self.memories = []

    # ========================================
    # BUILD INDEX
    # ========================================

    def _build_index(self):

        self.memory_index = {}

        for memory in self.memories:

            transformation = (

                memory.get(
                    "transformation",
                    "unknown"
                )
            )

            if transformation not in (
                self.memory_index
            ):

                self.memory_index[
                    transformation
                ] = []

            self.memory_index[
                transformation
            ].append(memory)

    # ========================================
    # SAVE MEMORY
    # ========================================

    def save(self):

        os.makedirs(

            os.path.dirname(
                self.memory_path
            ),

            exist_ok=True
        )

        with open(

            self.memory_path,

            "w",

            encoding="utf-8"
        ) as file:

            json.dump(

                self.memories,

                file,

                indent=4
            )

    # ========================================
    # MEMORY IMPORTANCE
    # ========================================

    def compute_importance(

        self,

        score,

        confidence=1.0
    ):

        return round(

            (
                float(score)
                *
                float(confidence)
            ),

            4
        )

    # ========================================
    # ADD MEMORY
    # ========================================

    def add_memory(

        self,

        task_name,

        transformation,

        score,

        metadata=None,

        confidence=1.0
    ):

        importance = (

            self.compute_importance(

                score,

                confidence
            )
        )

        memory = {

            "memory_id":
            len(self.memories) + 1,

            "task":
            task_name,

            "transformation":
            transformation,

            "score":
            float(score),

            "confidence":
            float(confidence),

            "importance":
            importance,

            "metadata":
            metadata or {},

            "retrieval_count":
            0,

            "created_at":
            datetime.utcnow().isoformat()
        }

        self.memories.append(
            memory
        )

        self.memory_telemetry[
            "writes"
        ] += 1

        self._build_index()

        self.save()

        return memory

    # ========================================
    # BEST MEMORIES
    # ========================================

    def best_memories(

        self,

        limit=5
    ):

        sorted_memories = sorted(

            self.memories,

            key=lambda memory:

            memory.get(
                "importance",
                0.0
            ),

            reverse=True
        )

        return sorted_memories[:limit]

    # ========================================
    # SEMANTIC SEARCH
    # ========================================

    def search(

        self,

        transformation_name
    ):

        self.memory_telemetry[
            "retrievals"
        ] += 1

        results = (

            self.memory_index.get(
                transformation_name,
                []
            )
        )

        for memory in results:

            memory[
                "retrieval_count"
            ] += 1

        return results

    # ========================================
    # MEMORY CONSOLIDATION
    # ========================================

    def consolidate(self):

        consolidated = {}

        for memory in self.memories:

            transformation = (

                memory[
                    "transformation"
                ]
            )

            if transformation not in (
                consolidated
            ):

                consolidated[
                    transformation
                ] = memory

                continue

            existing = (
                consolidated[
                    transformation
                ]
            )

            if (

                memory["importance"]
                >
                existing["importance"]
            ):

                consolidated[
                    transformation
                ] = memory

        self.memories = list(
            consolidated.values()
        )

        self.memory_telemetry[
            "consolidations"
        ] += 1

        self._build_index()

        self.save()

    # ========================================
    # MEMORY SUMMARY
    # ========================================

    def summary(self):

        return {

            "total_memories":
            len(self.memories),

            "indexed_transformations":
            len(self.memory_index),

            "best_memories":
            self.best_memories(),

            "memory_state":
            self.memory_state,

            "telemetry":
            self.memory_telemetry
        }

    # ========================================
    # EXPORT MEMORY REPORT
    # ========================================

    def export_report(self):

        return {

            "memory_summary":
            self.summary(),

            "timestamp":
            str(datetime.utcnow())
        }