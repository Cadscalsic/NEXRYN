# ============================================
# NEXRYN CONTEXT STATE HASHER
# ============================================

from datetime import datetime
import hashlib
import json
import uuid


# ============================================
# CONTEXT STATE HASHER
# ============================================

class ContextStateHasher:

    # ========================================
    # INITIALIZE HASHER
    # ========================================

    def __init__(self):

        # ====================================
        # HASH MEMORY
        # ====================================

        self.hash_memory = {}

        # ====================================
        # STATE MEMORY
        # ====================================

        self.state_memory = {}

        # ====================================
        # HASH HISTORY
        # ====================================

        self.hash_history = []

        # ====================================
        # DUPLICATE STATES
        # ====================================

        self.duplicate_states = []

        # ====================================
        # HASHER STATE
        # ====================================

        self.hasher_state = {

            "hasher_mode":
            "adaptive_runtime_hashing",

            "duplicate_detection":
            True,

            "state_tracking":
            True,

            "runtime_compression":
            True,

            "runtime_stability":
            "stable",

            "registered_states":
            0,

            "hash_cycles":
            0
        }

    # ========================================
    # NORMALIZE STATE
    # ========================================

    def normalize_state(

        self,

        state
    ):

        if state is None:

            state = {}

        # ====================================
        # NON SERIALIZABLE OBJECTS
        # ====================================

        if not isinstance(

            state,

            (
                dict,
                list,
                str,
                int,
                float,
                bool
            )
        ):

            state = str(state)

        return state

    # ========================================
    # SERIALIZE STATE
    # ========================================

    def serialize_state(

        self,

        state
    ):

        state = self.normalize_state(
            state
        )

        try:

            serialized = json.dumps(

                state,

                sort_keys=True,

                default=str
            )

        except Exception:

            serialized = str(state)

        return serialized

    # ========================================
    # COMPUTE HASH
    # ========================================

    def compute_hash(

        self,

        state
    ):

        serialized = (

            self.serialize_state(
                state
            )
        )

        state_hash = hashlib.sha256(

            serialized.encode()

        ).hexdigest()

        return state_hash

    # ========================================
    # REGISTER STATE
    # ========================================

    def register_state(

        self,

        state_id,

        state=None
    ):

        # ====================================
        # PIPELINE COMPATIBILITY
        # ====================================

        if state is None:

            state = state_id

            state_id = (
                f"runtime_state_"
                f"{len(self.state_memory)}"
            )

        # ====================================
        # NORMALIZE
        # ====================================

        if state is None:

            state = {}

        if not isinstance(
            state_id,
            str
        ):

            state_id = str(state_id)

        state = self.normalize_state(
            state
        )

        # ====================================
        # HASH STATE
        # ====================================

        state_hash = self.compute_hash(
            state
        )

        duplicate_detected = False

        duplicate_of = None

        # ====================================
        # DUPLICATE DETECTION
        # ====================================

        for existing_name, existing in (

            self.hash_memory.items()
        ):

            existing_hash = existing.get(
                "state_hash"
            )

            if existing_hash == state_hash:

                duplicate_detected = True

                duplicate_of = existing_name

                duplicate_event = {

                    "event_id":
                    str(uuid.uuid4()),

                    "state_name":
                    state_id,

                    "duplicate_of":
                    existing_name,

                    "state_hash":
                    state_hash,

                    "timestamp":
                    str(datetime.utcnow())
                }

                self.duplicate_states.append(
                    duplicate_event
                )

                break

        # ====================================
        # BUILD RECORD
        # ====================================

        record = {

            "state_id":
            state_id,

            "state_hash":
            state_hash,

            "duplicate_detected":
            duplicate_detected,

            "duplicate_of":
            duplicate_of,

            "state":
            state,

            "timestamp":
            str(datetime.utcnow())
        }

        # ====================================
        # STORE STATE MEMORY
        # ====================================

        self.state_memory[
            state_id
        ] = record

        # ====================================
        # STORE HASH MEMORY
        # ====================================

        self.hash_memory[
            state_id
        ] = {

            "state_hash":
            state_hash,

            "serialized_size":

            len(
                self.serialize_state(
                    state
                )
            ),

            "duplicate_detected":
            duplicate_detected,

            "duplicate_of":
            duplicate_of,

            "timestamp":
            str(datetime.utcnow())
        }

        # ====================================
        # HASH EVENT
        # ====================================

        hash_event = {

            "event_id":
            str(uuid.uuid4()),

            "state_name":
            state_id,

            "state_hash":
            state_hash,

            "duplicate_detected":
            duplicate_detected,

            "timestamp":
            str(datetime.utcnow())
        }

        # ====================================
        # STORE HISTORY
        # ====================================

        self.hash_history.append(
            hash_event
        )

        # ====================================
        # UPDATE HASHER STATE
        # ====================================

        self.hasher_state[
            "registered_states"
        ] += 1

        self.hasher_state[
            "hash_cycles"
        ] += 1

        # ====================================
        # RETURN REPORT
        # ====================================

        return {

            "record":
            record,

            "hash_event":
            hash_event
        }

    # ========================================
    # COMPARE STATES
    # ========================================

    def compare_states(

        self,

        state_a,

        state_b
    ):

        hash_a = self.compute_hash(
            state_a
        )

        hash_b = self.compute_hash(
            state_b
        )

        return {

            "match":
            hash_a == hash_b,

            "hash_a":
            hash_a,

            "hash_b":
            hash_b
        }

    # ========================================
    # GET STATE HASH
    # ========================================

    def get_state_hash(

        self,

        state_id
    ):

        state_data = (

            self.hash_memory.get(
                state_id,
                {}
            )
        )

        return state_data.get(
            "state_hash"
        )

    # ========================================
    # GET STATE RECORD
    # ========================================

    def get_state_record(

        self,

        state_id
    ):

        return self.state_memory.get(
            state_id
        )

    # ========================================
    # BUILD HASH SUMMARY
    # ========================================

    def build_hash_summary(self):

        total_size = 0

        for state in (

            self.hash_memory.values()
        ):

            total_size += state.get(
                "serialized_size",
                0
            )

        return {

            "registered_states":

            len(
                self.hash_memory
            ),

            "duplicate_states":

            len(
                self.duplicate_states
            ),

            "total_serialized_size":
            total_size,

            "runtime_state":
            self.hasher_state.get(
                "runtime_stability",
                "stable"
            )
        }

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "hasher_state":
            self.hasher_state,

            "hash_memory":

            len(
                self.hash_memory
            ),

            "state_memory":

            len(
                self.state_memory
            ),

            "hash_history":

            len(
                self.hash_history
            ),

            "duplicate_states":

            len(
                self.duplicate_states
            ),

            "hash_summary":

            self.build_hash_summary(),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL CONTEXT STATE HASHER
# ============================================

context_state_hasher = (
    ContextStateHasher()
)