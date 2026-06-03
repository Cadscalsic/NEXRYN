# ============================================
# NEXRYN SHARED TRANSFER MEMORY
# ============================================

from datetime import datetime


# ============================================
# SHARED TRANSFER MEMORY
# ============================================

class SharedTransferMemory:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # STRATEGY MEMORY
        # ====================================

        self.strategy_memory = []

        # ====================================
        # SEMANTIC MEMORY
        # ====================================

        self.semantic_memory = []

        # ====================================
        # PROGRAM MEMORY
        # ====================================

        self.program_memory = []

        # ====================================
        # TRANSFER HISTORY
        # ====================================

        self.transfer_history = []

        # ====================================
        # MEMORY STATE
        # ====================================

        self.memory_state = {

            "transfer_learning":
            True,

            "cross_task_reuse":
            True,

            "semantic_adaptation":
            True,

            "program_reuse":
            True
        }

    # ========================================
    # STORE HYPOTHESES
    # ========================================

    def store_hypotheses(

        self,

        hypotheses
    ):

        for hypothesis in hypotheses:

            self.strategy_memory.append({

                "hypothesis":
                hypothesis,

                "timestamp":
                str(datetime.utcnow())
            })

    # ========================================
    # STORE SEMANTIC ABSTRACTIONS
    # ========================================

    def store_semantics(

        self,

        semantic_abstractions
    ):

        for abstraction in (
            semantic_abstractions
        ):

            self.semantic_memory.append({

                "semantic":
                abstraction,

                "timestamp":
                str(datetime.utcnow())
            })

    # ========================================
    # STORE PROGRAM
    # ========================================

    def store_program(

        self,

        synthesized_program
    ):

        self.program_memory.append({

            "program":
            synthesized_program,

            "timestamp":
            str(datetime.utcnow())
        })

    # ========================================
    # TRANSFER KNOWLEDGE
    # ========================================

    def transfer_knowledge(

        self,

        final_context
    ):

        hypotheses = (

            final_context.get(
                "hypotheses",
                []
            )
        )

        semantics = (

            final_context.get(
                "semantic_abstractions",
                []
            )
        )

        synthesized_program = (

            final_context.get(
                "synthesized_program",
                {}
            )
        )

        # ====================================
        # STORE KNOWLEDGE
        # ====================================

        self.store_hypotheses(
            hypotheses
        )

        self.store_semantics(
            semantics
        )

        self.store_program(
            synthesized_program
        )

        # ====================================
        # TRANSFER EVENT
        # ====================================

        transfer_event = {

            "hypotheses":
            len(hypotheses),

            "semantic_patterns":
            len(semantics),

            "program_stored":

            bool(
                synthesized_program
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        self.transfer_history.append(
            transfer_event
        )

        return transfer_event

    # ========================================
    # RETRIEVE STRATEGIES
    # ========================================

    def retrieve_strategies(

        self,

        limit=10
    ):

        return self.strategy_memory[
            -limit:
        ]

    # ========================================
    # RETRIEVE SEMANTICS
    # ========================================

    def retrieve_semantics(

        self,

        limit=10
    ):

        return self.semantic_memory[
            -limit:
        ]

    # ========================================
    # RETRIEVE PROGRAMS
    # ========================================

    def retrieve_programs(

        self,

        limit=10
    ):

        return self.program_memory[
            -limit:
        ]

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "strategy_count":

            len(
                self.strategy_memory
            ),

            "semantic_count":

            len(
                self.semantic_memory
            ),

            "program_count":

            len(
                self.program_memory
            ),

            "transfer_events":

            len(
                self.transfer_history
            ),

            "memory_state":
            self.memory_state
        }