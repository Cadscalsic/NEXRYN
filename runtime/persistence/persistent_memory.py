# ============================================
# NEXRYN PERSISTENT MEMORY
# ============================================

import json
import os


# ============================================
# PERSISTENT MEMORY
# ============================================

class PersistentMemory:

    def __init__(

        self,

        memory_path="runtime_data/persistent_memory.json"
    ):

        self.memory_path = memory_path

        self.memory = self.load_memory()

    # ============================================
    # LOAD MEMORY
    # ============================================

    def load_memory(self):

        directory = os.path.dirname(
            self.memory_path
        )

        if directory and not os.path.exists(directory):

            os.makedirs(
                directory
            )

        if not os.path.exists(
            self.memory_path
        ):

            return []

        try:

            with open(

                self.memory_path,

                "r",

                encoding="utf-8"
            ) as file:

                return json.load(
                    file
                )

        except Exception:

            return []

    # ============================================
    # SAVE MEMORY
    # ============================================

    def save_memory(self):

        with open(

            self.memory_path,

            "w",

            encoding="utf-8"
        ) as file:

            json.dump(

                self.memory,

                file,

                indent=4
            )

    # ============================================
    # STORE EXPERIENCE
    # ============================================

    def store_experience(

        self,

        experience
    ):

        self.memory.append(
            experience
        )

        self.save_memory()

    # ============================================
    # GET MEMORY
    # ============================================

    def get_memory(self):

        return self.memory

    # ============================================
    # MEMORY SIZE
    # ============================================

    def memory_size(self):

        return len(
            self.memory
        )

    # ============================================
    # PRINT STATUS
    # ============================================

    def print_status(self):

        print("\n==================================================")
        print("NEXRYN :: PERSISTENT MEMORY")
        print("==================================================\n")

        print(

            f"Stored Experiences: {self.memory_size()}"
        )