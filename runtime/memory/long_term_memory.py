# ============================================
# NEXRYN LONG TERM MEMORY
# ============================================

import json

from pathlib import Path

from datetime import datetime


# ============================================
# LONG TERM MEMORY
# ============================================

class LongTermMemory:

    def __init__(

        self,

        storage_path="runtime_data/long_term_memory"
    ):

        self.storage_path = Path(
            storage_path
        )

        self.storage_path.mkdir(

            parents=True,

            exist_ok=True
        )

        self.memory_index = {}

        self.memory_state = {

            "memory_type":
            "long_term_memory",

            "persistent_storage":
            "enabled",

            "compression":
            "enabled",

            "retrieval":
            "enabled"
        }

    # ============================================
    # STORE MEMORY
    # ============================================

    def store_memory(

        self,

        memory_id,

        memory_data
    ):

        memory_file = (

            self.storage_path

            /

            f"{memory_id}.json"
        )

        payload = {

            "memory_id":
            memory_id,

            "memory_data":
            memory_data,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        with open(

            memory_file,

            "w",

            encoding="utf-8"
        ) as file:

            json.dump(

                payload,

                file,

                indent=4
            )

        self.memory_index[
            memory_id
        ] = str(memory_file)

        return {

            "memory_id":
            memory_id,

            "storage":
            str(memory_file),

            "state":
            "stored"
        }

    # ============================================
    # RETRIEVE MEMORY
    # ============================================

    def retrieve_memory(

        self,

        memory_id
    ):

        if memory_id not in self.memory_index:

            return None

        memory_file = Path(

            self.memory_index[
                memory_id
            ]
        )

        if not memory_file.exists():

            return None

        with open(

            memory_file,

            "r",

            encoding="utf-8"
        ) as file:

            payload = json.load(
                file
            )

        return payload

    # ============================================
    # MEMORY EXISTS
    # ============================================

    def memory_exists(

        self,

        memory_id
    ):

        return memory_id in self.memory_index

    # ============================================
    # LIST MEMORIES
    # ============================================

    def list_memories(self):

        return list(

            self.memory_index.keys()
        )

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        return {

            "memory_type":
            "long_term_memory",

            "stored_memories":
            len(
                self.memory_index
            ),

            "storage_path":
            str(
                self.storage_path
            ),

            "state":
            "stable"
        }