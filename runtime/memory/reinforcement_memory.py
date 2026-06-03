# ============================================
# NEXRYN REINFORCEMENT MEMORY
# ============================================


# ============================================
# REINFORCEMENT MEMORY
# ============================================

class ReinforcementMemory:

    def __init__(self):

        # ========================================
        # MEMORY STORAGE
        # ========================================

        self.memory = []

    # ============================================
    # STORE EXPERIENCE
    # ============================================

    def store_experience(

        self,

        hypothesis,

        evaluation_result
    ):

        success = evaluation_result.get(
            "success",
            False
        )

        accuracy = evaluation_result.get(
            "accuracy",
            0.0
        )

        experience = {

            "hypothesis_type":
            hypothesis.get(
                "type"
            ),

            "confidence":
            hypothesis.get(
                "confidence",
                0.0
            ),

            "metadata":
            hypothesis.get(
                "metadata",
                {}
            ),

            "success":
            success,

            "accuracy":
            accuracy
        }

        self.memory.append(
            experience
        )

    # ============================================
    # RETRIEVE SUCCESSFUL EXPERIENCES
    # ============================================

    def retrieve_successful(

        self,

        hypothesis_type=None
    ):

        successful = []

        for experience in self.memory:

            if not experience.get(
                "success"
            ):

                continue

            if hypothesis_type is not None:

                if experience.get(
                    "hypothesis_type"
                ) != hypothesis_type:

                    continue

            successful.append(
                experience
            )

        return successful

    # ============================================
    # GET MEMORY SIZE
    # ============================================

    def memory_size(self):

        return len(
            self.memory
        )

    # ============================================
    # PRINT MEMORY
    # ============================================

    def print_memory(self):

        print("\n==================================================")
        print("NEXRYN :: REINFORCEMENT MEMORY")
        print("==================================================\n")

        for experience in self.memory:

            print(experience)