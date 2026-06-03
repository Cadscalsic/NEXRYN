# ============================================
# NEXRYN MEMORY STORE
# ============================================

import copy


# ============================================
# MEMORY STORE
# ============================================

class MemoryStore:

    def __init__(self):

        # ========================================
        # SHORT TERM MEMORY
        # ========================================

        self.short_term_memory = []

        # ========================================
        # LONG TERM MEMORY
        # ========================================

        self.long_term_memory = []

        # ========================================
        # EPISODIC MEMORY
        # ========================================

        self.episodic_memory = []

    # ============================================
    # STORE SHORT TERM MEMORY
    # ============================================

    def store_short_term(

        self,

        item
    ):

        self.short_term_memory.append(

            copy.deepcopy(item)
        )

    # ============================================
    # STORE LONG TERM MEMORY
    # ============================================

    def store_long_term(

        self,

        item
    ):

        self.long_term_memory.append(

            copy.deepcopy(item)
        )

    # ============================================
    # STORE EPISODE
    # ============================================

    def store_episode(

        self,

        context
    ):

        self.episodic_memory.append(

            copy.deepcopy(context)
        )

    # ============================================
    # GET SHORT TERM MEMORY
    # ============================================

    def get_short_term_memory(self):

        return (
            self.short_term_memory
        )

    # ============================================
    # GET LONG TERM MEMORY
    # ============================================

    def get_long_term_memory(self):

        return (
            self.long_term_memory
        )

    # ============================================
    # GET EPISODIC MEMORY
    # ============================================

    def get_episodic_memory(self):

        return (
            self.episodic_memory
        )

    # ============================================
    # CLEAR SHORT TERM MEMORY
    # ============================================

    def clear_short_term_memory(self):

        self.short_term_memory = []

    # ============================================
    # MEMORY STATS
    # ============================================

    def get_memory_stats(self):

        return {

            "short_term_items":
            len(
                self.short_term_memory
            ),

            "long_term_items":
            len(
                self.long_term_memory
            ),

            "episodic_items":
            len(
                self.episodic_memory
            )
        }

    # ============================================
    # PRINT MEMORY REPORT
    # ============================================

    def print_memory_report(self):

        stats = (
            self.get_memory_stats()
        )

        print("\n==================================================")
        print("NEXRYN :: MEMORY REPORT")
        print("==================================================\n")

        print(stats)

        print()