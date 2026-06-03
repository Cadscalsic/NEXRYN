# ============================================
# NEXRYN ANALOGICAL REASONING ENGINE
# ============================================

from datetime import datetime

import copy


# ============================================
# ANALOGICAL REASONING ENGINE
# ============================================

class AnalogicalReasoningEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.analogy_history = []

        self.experience_memory = []

        self.engine_state = {

            "transfer_reasoning":
            True,

            "experience_retrieval":
            True,

            "similarity_mapping":
            True,

            "cross_task_generalization":
            True,

            "relational_alignment":
            True
        }

    # ========================================
    # STORE EXPERIENCE
    # ========================================

    def store_experience(

        self,

        task_signature,

        reasoning_result
    ):

        experience = {

            "task_signature":
            copy.deepcopy(
                task_signature
            ),

            "reasoning_result":
            copy.deepcopy(
                reasoning_result
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        self.experience_memory.append(
            experience
        )

    # ========================================
    # COMPUTE SIMILARITY
    # ========================================

    def compute_similarity(

        self,

        current_signature,

        previous_signature
    ):

        score = 0.0

        # ====================================
        # OBJECT COUNT
        # ====================================

        if current_signature.get(
            "object_count"
        ) == previous_signature.get(
            "object_count"
        ):

            score += 0.3

        # ====================================
        # COLOR COUNT
        # ====================================

        if current_signature.get(
            "color_count"
        ) == previous_signature.get(
            "color_count"
        ):

            score += 0.2

        # ====================================
        # SHAPE
        # ====================================

        if current_signature.get(
            "shape"
        ) == previous_signature.get(
            "shape"
        ):

            score += 0.3

        # ====================================
        # TRANSFORMATION TYPE
        # ====================================

        if current_signature.get(
            "transformation_type"
        ) == previous_signature.get(
            "transformation_type"
        ):

            score += 0.2

        return round(
            score,
            3
        )

    # ========================================
    # FIND SIMILAR EXPERIENCES
    # ========================================

    def find_similar_experiences(

        self,

        task_signature
    ):

        matches = []

        for experience in (

            self.experience_memory
        ):

            previous_signature = (

                experience.get(
                    "task_signature",
                    {}
                )
            )

            similarity_score = (

                self.compute_similarity(

                    task_signature,

                    previous_signature
                )
            )

            if similarity_score >= 0.5:

                matches.append({

                    "similarity":
                    similarity_score,

                    "experience":
                    experience
                })

        # ====================================
        # SORT MATCHES
        # ====================================

        matches = sorted(

            matches,

            key=lambda item:

            item.get(
                "similarity",
                0.0
            ),

            reverse=True
        )

        # ====================================
        # BUILD REPORT
        # ====================================

        report = {

            "match_count":
            len(matches),

            "matches":
            matches,

            "best_match":

            matches[0]
            if matches
            else {},

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.analogy_history.append(
            report
        )

        return report

    # ========================================
    # BUILD TRANSFER INSIGHT
    # ========================================

    def build_transfer_insight(

        self,

        similarity_report
    ):

        best_match = (

            similarity_report.get(
                "best_match",
                {}
            )
        )

        if not best_match:

            return {

                "transfer_detected":
                False
            }

        similarity = best_match.get(
            "similarity",
            0.0
        )

        experience = best_match.get(
            "experience",
            {}
        )

        insight = {

            "transfer_detected":
            True,

            "transfer_confidence":
            similarity,

            "recommended_reasoning":

            experience.get(
                "reasoning_result",
                {}
            ),

            "analogy_strength":

            "high"
            if similarity >= 0.8
            else "moderate"
        }

        return insight

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_report = {}

        if self.analogy_history:

            latest_report = (

                self.analogy_history[-1]
            )

        return {

            "experience_count":

            len(
                self.experience_memory
            ),

            "analogy_cycles":

            len(
                self.analogy_history
            ),

            "engine_state":
            self.engine_state,

            "latest_report":
            latest_report
        }


# ============================================
# GLOBAL ENGINE
# ============================================

analogical_reasoning_engine = (
    AnalogicalReasoningEngine()
)