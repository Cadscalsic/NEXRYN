# ============================================
# NEXRYN SEMANTIC MEMORY
# ============================================

from datetime import datetime


# ============================================
# SEMANTIC MEMORY
# ============================================

class SemanticMemory:

    def __init__(self):

        self.knowledge_base = {}

        self.semantic_state = {

            "memory_type":
            "semantic_memory",

            "knowledge_abstraction":
            "enabled",

            "symbolic_reasoning":
            "enabled",

            "transfer_learning":
            "enabled"
        }

    # ============================================
    # STORE CONCEPT
    # ============================================

    def store_concept(

        self,

        concept_name,

        concept_data
    ):

        self.knowledge_base[
            concept_name
        ] = {

            "concept":
            concept_data,

            "usage_count":
            0,

            "created_at":
            str(
                datetime.utcnow()
            )
        }

    # ============================================
    # RETRIEVE CONCEPT
    # ============================================

    def retrieve_concept(

        self,

        concept_name
    ):

        concept = self.knowledge_base.get(

            concept_name
        )

        if concept:

            concept[
                "usage_count"
            ] += 1

        return concept

    # ============================================
    # UPDATE CONCEPT
    # ============================================

    def update_concept(

        self,

        concept_name,

        new_data
    ):

        if concept_name in self.knowledge_base:

            self.knowledge_base[
                concept_name
            ]["concept"] = new_data

    # ============================================
    # MOST USED CONCEPTS
    # ============================================

    def most_used_concepts(

        self,

        limit=10
    ):

        concepts = sorted(

            self.knowledge_base.items(),

            key=lambda x: x[1][
                "usage_count"
            ],

            reverse=True
        )

        return concepts[:limit]

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        return {

            "memory_type":
            "semantic_memory",

            "concept_count":
            len(
                self.knowledge_base
            ),

            "most_used_concepts":

            [

                concept[0]

                for concept in

                self.most_used_concepts(
                    limit=5
                )
            ],

            "state":
            "stable"
        }