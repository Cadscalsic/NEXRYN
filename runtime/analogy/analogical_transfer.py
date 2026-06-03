# ============================================
# NEXRYN ANALOGICAL TRANSFER ENGINE
# ============================================


# ============================================
# ANALOGICAL TRANSFER ENGINE
# ============================================

class AnalogicalTransferEngine:

    def __init__(self):

        self.transfer_memory = []

    # ============================================
    # EXTRACT CONCEPTS
    # ============================================

    def extract_concepts(

        self,

        semantic_graph
    ):

        concepts = []

        for node in semantic_graph.get(
            "concept_nodes",
            []
        ):

            concepts.append(

                node.get(
                    "concept"
                )
            )

        return concepts

    # ============================================
    # COMPUTE SIMILARITY
    # ============================================

    def compute_similarity(

        self,

        concepts_a,

        concepts_b
    ):

        set_a = set(concepts_a)

        set_b = set(concepts_b)

        if not set_a and not set_b:

            return 0.0

        intersection = len(
            set_a.intersection(set_b)
        )

        union = len(
            set_a.union(set_b)
        )

        return round(

            intersection / union,

            4
        )

    # ============================================
    # FIND ANALOGIES
    # ============================================

    def find_analogies(

        self,

        semantic_graph
    ):

        current_concepts = (

            self.extract_concepts(
                semantic_graph
            )
        )

        analogies = []

        for memory in self.transfer_memory:

            memory_concepts = (

                memory.get(
                    "concepts",
                    []
                )
            )

            similarity = (

                self.compute_similarity(

                    current_concepts,

                    memory_concepts
                )
            )

            analogies.append({

                "task_id":
                memory.get(
                    "task_id",
                    "unknown"
                ),

                "similarity":
                similarity,

                "shared_concepts":
                list(

                    set(current_concepts)

                    .intersection(

                        set(memory_concepts)
                    )
                )
            })

        ranked_analogies = sorted(

            analogies,

            key=lambda a: a[
                "similarity"
            ],

            reverse=True
        )

        return ranked_analogies

    # ============================================
    # STORE SEMANTIC EXPERIENCE
    # ============================================

    def store_semantic_experience(

        self,

        task_id,

        semantic_graph
    ):

        concepts = (

            self.extract_concepts(
                semantic_graph
            )
        )

        self.transfer_memory.append({

            "task_id":
            task_id,

            "concepts":
            concepts
        })

    # ============================================
    # BUILD TRANSFER REPORT
    # ============================================

    def build_transfer_report(

        self,

        analogies
    ):

        if analogies:

            best_match = analogies[0]

        else:

            best_match = {}

        return {

            "analogy_count":
            len(analogies),

            "best_similarity":
            best_match.get(
                "similarity",
                0.0
            ),

            "best_match":
            best_match
        }