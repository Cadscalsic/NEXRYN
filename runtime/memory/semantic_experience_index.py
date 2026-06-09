# ============================================
# NEXRYN SEMANTIC EXPERIENCE INDEX
# ============================================

import os
import json

from datetime import datetime


# ============================================
# SEMANTIC EXPERIENCE INDEX
# ============================================

class SemanticExperienceIndex:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # SEMANTIC INDEX
        # ====================================

        self.semantic_index = {}

        # ====================================
        # STORAGE PATH
        # ====================================

        self.storage_path = (

            "runtime/memory/storage/"
            "semantic_index.json"
        )

        self.last_persistence_error = None

        # ====================================
        # LOAD PERSISTENT INDEX
        # ====================================

        self.load_persistent_index()

        # ====================================
        # INDEX HISTORY
        # ====================================

        self.index_history = []

        # ====================================
        # INDEX STATE
        # ====================================

        self.index_state = {

            "semantic_indexing":
            True,

            "conceptual_matching":
            True,

            "transfer_mapping":
            True,

            "adaptive_similarity":
            True,

            "persistent_semantic_memory":
            True,

            "indexed_experiences":
            0
        }

    # ========================================
    # SAVE PERSISTENT INDEX
    # ========================================

    def save_persistent_index(self):

        try:

            os.makedirs(

                "runtime/memory/storage",

                exist_ok=True
            )

            serializable_index = {}

            for concept, items in (

                self.semantic_index.items()
            ):

                serializable_index[
                    concept
                ] = items

            temporary_path = (
                f"{self.storage_path}.tmp"
            )

            with open(

                temporary_path,

                "w",

                encoding="utf-8"
            ) as file:

                json.dump(

                    serializable_index,

                    file,

                    indent=4
                )

            os.replace(
                temporary_path,
                self.storage_path
            )

        except Exception as error:

            self.last_persistence_error = str(error)

    # ========================================
    # LOAD PERSISTENT INDEX
    # ========================================

    def load_persistent_index(self):

        try:

            if not os.path.exists(
                self.storage_path
            ):

                return

            with open(

                self.storage_path,

                "r",

                encoding="utf-8"
            ) as file:

                loaded = json.load(
                    file
                )

            if isinstance(
                loaded,
                dict
            ):

                self.semantic_index = loaded

        except Exception:

            self.semantic_index = {}

    # ========================================
    # EXTRACT SEMANTIC CONCEPTS
    # ========================================

    def extract_semantic_concepts(

        self,

        experience
    ):

        concepts = []

        semantic_summary = (

            experience.get(
                "semantic_summary"
            )

            or {}
        )

        semantic_graph = (

            experience.get(
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

        for node in concept_nodes:

            concept = node.get(
                "concept"
            )

            if concept:

                concepts.append(
                    concept
                )

        abstraction_list = (

            experience.get(
                "semantic_abstractions",
                []
            )
        )

        for abstraction in abstraction_list:

            semantic_concept = abstraction.get(
                "semantic_concept"
            )

            if semantic_concept:

                concepts.append(
                    semantic_concept
                )

        summary_type = semantic_summary.get(
            "summary_type"
        )

        if summary_type:

            concepts.append(
                summary_type
            )

        return list(
            set(concepts)
        )

    # ========================================
    # INDEX EXPERIENCE
    # ========================================

    def index_experience(

        self,

        experience
    ):

        concepts = (

            self.extract_semantic_concepts(
                experience
            )
        )

        for concept in concepts:

            if concept not in (
                self.semantic_index
            ):

                self.semantic_index[
                    concept
                ] = []

            self.semantic_index[
                concept
            ].append(
                experience
            )

        # ====================================
        # SAVE INDEX
        # ====================================

        self.save_persistent_index()

        self.index_state[
            "indexed_experiences"
        ] += 1

        self.index_history.append({

            "concept_count":
            len(concepts),

            "timestamp":
            str(datetime.utcnow())
        })

    # ========================================
    # RETRIEVE BY CONCEPTS
    # ========================================

    def retrieve_by_concepts(

        self,

        semantic_concepts
    ):

        retrieved = []

        for concept in semantic_concepts:

            matches = (

                self.semantic_index.get(
                    concept,
                    []
                )
            )

            retrieved.extend(
                matches
            )

        # ====================================
        # REMOVE DUPLICATES
        # ====================================

        unique = []

        seen = set()

        for item in retrieved:

            identifier = str(
                id(item)
            )

            if identifier in seen:

                continue

            seen.add(
                identifier
            )

            unique.append(
                item
            )

        return unique

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "indexed_concepts":
            len(
                self.semantic_index
            ),

            "indexed_experiences":
            self.index_state[
                "indexed_experiences"
            ],

            "persistent_storage":
            self.storage_path,

            "index_cycles":
            len(
                self.index_history
            ),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL SEMANTIC INDEX
# ============================================

semantic_experience_index = (
    SemanticExperienceIndex()
)
