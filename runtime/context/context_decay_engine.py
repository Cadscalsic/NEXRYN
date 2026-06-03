# ============================================
# NEXRYN CONTEXT DECAY ENGINE
# ============================================

from datetime import datetime
import uuid


# ============================================
# CONTEXT DECAY ENGINE
# ============================================

class ContextDecayEngine:

    # ========================================
    # INITIALIZE ENGINE
    # ========================================

    def __init__(self):

        # ====================================
        # DECAY MEMORY
        # ====================================

        self.decay_memory = {}

        # ====================================
        # DECAY HISTORY
        # ====================================

        self.decay_history = []

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "decay_mode":
            "adaptive_temporal_decay",

            "temporal_decay":
            True,

            "importance_preservation":
            True,

            "memory_regulation":
            True,

            "runtime_stability":
            "stable",

            "decay_cycles":
            0
        }

        # ====================================
        # DECAY CONFIGURATION
        # ====================================

        self.default_decay_rate = 0.05

        self.minimum_strength = 0.05

    # ========================================
    # NORMALIZE KEY
    # ========================================

    def normalize_key(

        self,

        context_key
    ):

        if context_key is None:

            context_key = "undefined"

        if not isinstance(
            context_key,
            str
        ):

            context_key = str(
                context_key
            )

        return context_key

    # ========================================
    # REGISTER CONTEXT
    # ========================================

    def register_context(

        self,

        context_key,

        importance_score=0.5
    ):

        context_key = self.normalize_key(
            context_key
        )

        if context_key not in (

            self.decay_memory
        ):

            self.decay_memory[
                context_key
            ] = {

                "strength":
                1.0,

                "importance_score":
                importance_score,

                "decay_cycles":
                0,

                "last_decay":
                str(datetime.utcnow()),

                "memory_state":
                "active"
            }

        return self.decay_memory[
            context_key
        ]

    # ========================================
    # COMPUTE DECAY RATE
    # ========================================

    def compute_decay_rate(

        self,

        importance_score
    ):

        decay_rate = (

            self.default_decay_rate
        )

        # ====================================
        # PRESERVE IMPORTANT MEMORY
        # ====================================

        if importance_score >= 0.8:

            decay_rate *= 0.3

        elif importance_score >= 0.6:

            decay_rate *= 0.5

        elif importance_score <= 0.2:

            decay_rate *= 1.8

        return round(
            decay_rate,
            4
        )

    # ========================================
    # APPLY DECAY
    # ========================================

    def apply_decay(

        self,

        context_key
    ):

        context_key = self.normalize_key(
            context_key
        )

        memory = self.decay_memory.get(
            context_key
        )

        if memory is None:

            return None

        importance_score = memory.get(
            "importance_score",
            0.5
        )

        decay_rate = (

            self.compute_decay_rate(
                importance_score
            )
        )

        current_strength = memory.get(
            "strength",
            1.0
        )

        updated_strength = (

            current_strength
            - decay_rate
        )

        updated_strength = max(

            updated_strength,

            self.minimum_strength
        )

        # ====================================
        # UPDATE MEMORY
        # ====================================

        memory[
            "strength"
        ] = round(
            updated_strength,
            4
        )

        memory[
            "decay_cycles"
        ] += 1

        memory[
            "last_decay"
        ] = str(
            datetime.utcnow()
        )

        # ====================================
        # MEMORY STATE
        # ====================================

        if updated_strength <= 0.15:

            memory[
                "memory_state"
            ] = "fading"

        elif updated_strength <= 0.35:

            memory[
                "memory_state"
            ] = "weak"

        else:

            memory[
                "memory_state"
            ] = "stable"

        # ====================================
        # DECAY EVENT
        # ====================================

        decay_event = {

            "event_id":
            str(uuid.uuid4()),

            "context_key":
            context_key,

            "previous_strength":
            current_strength,

            "updated_strength":
            updated_strength,

            "decay_rate":
            decay_rate,

            "memory_state":
            memory[
                "memory_state"
            ],

            "timestamp":
            str(datetime.utcnow())
        }

        self.decay_history.append(
            decay_event
        )

        self.engine_state[
            "decay_cycles"
        ] += 1

        return decay_event

    # ========================================
    # DECAY ALL CONTEXTS
    # ========================================

    def decay_all_contexts(self):

        decay_results = []

        for context_key in (

            self.decay_memory.keys()
        ):

            decay_result = (

                self.apply_decay(
                    context_key
                )
            )

            if decay_result:

                decay_results.append(
                    decay_result
                )

        return decay_results

    # ========================================
    # REMOVE FADED MEMORIES
    # ========================================

    def remove_faded_memories(self):

        retained_memory = {}

        removed = []

        for key, memory in (

            self.decay_memory.items()
        ):

            strength = memory.get(
                "strength",
                1.0
            )

            if strength <= self.minimum_strength:

                removed.append(key)

                continue

            retained_memory[key] = memory

        self.decay_memory = retained_memory

        return {

            "removed_memories":
            removed,

            "removed_count":
            len(removed)
        }

    # ========================================
    # BUILD DECAY SUMMARY
    # ========================================

    def build_decay_summary(self):

        fading_memories = 0

        weak_memories = 0

        stable_memories = 0

        for memory in (

            self.decay_memory.values()
        ):

            state = memory.get(
                "memory_state",
                "stable"
            )

            if state == "fading":

                fading_memories += 1

            elif state == "weak":

                weak_memories += 1

            else:

                stable_memories += 1

        return {

            "stable_memories":
            stable_memories,

            "weak_memories":
            weak_memories,

            "fading_memories":
            fading_memories
        }
    

    # ========================================
    # RUN DECAY CYCLE
    # ========================================

    def run_decay_cycle(

        self,

        runtime_context=None
    ):

        if runtime_context is None:

            runtime_context = {}

        # ====================================
        # REGISTER CONTEXTS
        # ====================================

        for context_key in (

            runtime_context.keys()
        ):

            if context_key not in (

                self.decay_memory
            ):

                self.register_context(
                    context_key
                )

        # ====================================
        # APPLY GLOBAL DECAY
        # ====================================

        decay_results = (

            self.decay_all_contexts()
        )

        # ====================================
        # REMOVE FADED MEMORIES
        # ====================================

        removal_report = (

            self.remove_faded_memories()
        )

        # ====================================
        # BUILD SUMMARY
        # ====================================

        decay_summary = (

            self.build_decay_summary()
        )

        # ====================================
        # BUILD REPORT
        # ====================================

        report = {

            "decay_applied":
            True,

            "registered_contexts":

            len(runtime_context),

            "decayed_contexts":

            len(decay_results),

            "removed_memories":

            removal_report.get(
                "removed_count",
                0
            ),

            "decay_summary":
            decay_summary,

            "timestamp":
            str(datetime.utcnow())
        }

        # ====================================
        # STORE REPORT
        # ====================================

        self.decay_history.append(
            report
        )

        return report

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "engine_state":
            self.engine_state,

            "registered_memories":

            len(
                self.decay_memory
            ),

            "decay_history":

            len(
                self.decay_history
            ),

            "decay_summary":

            self.build_decay_summary(),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL CONTEXT DECAY ENGINE
# ============================================

context_decay_engine = (
    ContextDecayEngine()
)
