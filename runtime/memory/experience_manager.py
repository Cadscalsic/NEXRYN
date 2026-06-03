# ============================================
# NEXRYN EXPERIENCE MANAGER
# ============================================

import copy


# ============================================
# EXPERIENCE MANAGER
# ============================================

class ExperienceManager:

    def __init__(self):

        # ========================================
        # EXPERIENCE DATABASE
        # ========================================

        self.experiences = []

    # ============================================
    # STORE EXPERIENCE
    # ============================================

    def store_experience(

        self,

        context
    ):

        experience = {

            # ====================================
            # PATTERNS
            # ====================================

            "patterns":
            copy.deepcopy(

                context.get(
                    "patterns",
                    []
                )
            ),

            # ====================================
            # RULES
            # ====================================

            "rules":
            copy.deepcopy(

                context.get(
                    "rules",
                    []
                )
            ),

            # ====================================
            # HYPOTHESES
            # ====================================

            "hypotheses":
            copy.deepcopy(

                context.get(
                    "hypotheses",
                    []
                )
            ),

            # ====================================
            # TRANSFORMATION REPORT
            # ====================================

            "transformation_report":
            copy.deepcopy(

                context.get(
                    "transformation_report",
                    {}
                )
            ),

            # ====================================
            # PREDICTED OUTPUT
            # ====================================

            "predicted_output":
            copy.deepcopy(

                context.get(
                    "predicted_output"
                )
            )
        }

        # ========================================
        # SAVE EXPERIENCE
        # ========================================

        self.experiences.append(
            experience
        )

    # ============================================
    # GET EXPERIENCES
    # ============================================

    def get_experiences(self):

        return self.experiences

    # ============================================
    # FIND SIMILAR EXPERIENCES
    # ============================================

    def find_similar_experiences(

        self,

        patterns
    ):

        similar_experiences = []

        # ========================================
        # CURRENT PATTERN NAMES
        # ========================================

        current_pattern_names = set([

            pattern.get(
                "pattern"
            )

            for pattern in patterns
        ])

        # ========================================
        # SEARCH EXPERIENCES
        # ========================================

        for experience in self.experiences:

            experience_patterns = (
                experience.get(
                    "patterns",
                    []
                )
            )

            experience_pattern_names = set([

                pattern.get(
                    "pattern"
                )

                for pattern in (
                    experience_patterns
                )
            ])

            # ====================================
            # CALCULATE OVERLAP
            # ====================================

            overlap = len(

                current_pattern_names.intersection(

                    experience_pattern_names
                )
            )

            # ====================================
            # SAVE MATCH
            # ====================================

            if overlap > 0:

                similar_experiences.append({

                    "experience":
                    experience,

                    "similarity":
                    overlap
                })

        # ========================================
        # SORT BY SIMILARITY
        # ========================================

        similar_experiences = sorted(

            similar_experiences,

            key=lambda item: item[
                "similarity"
            ],

            reverse=True
        )

        return similar_experiences

    # ============================================
    # EXPERIENCE COUNT
    # ============================================

    def get_experience_count(self):

        return len(
            self.experiences
        )

    # ============================================
    # CLEAR EXPERIENCES
    # ============================================

    def clear_experiences(self):

        self.experiences = []

    # ============================================
    # MEMORY STATS
    # ============================================

    def get_stats(self):

        return {

            "stored_experiences":
            len(
                self.experiences
            )
        }

    # ============================================
    # PRINT REPORT
    # ============================================

    def print_report(self):

        print("\n==================================================")
        print("NEXRYN :: EXPERIENCE REPORT")
        print("==================================================\n")

        print(
            self.get_stats()
        )

        print()