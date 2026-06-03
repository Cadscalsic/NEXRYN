# ============================================
# NEXRYN WORKING MEMORY
# ============================================

from datetime import datetime


# ============================================
# WORKING MEMORY
# ============================================

class WorkingMemory:

    def __init__(

        self,

        capacity=25
    ):

        self.capacity = capacity

        self.memory_stack = []

        self.memory_state = {

            "memory_type":
            "working_memory",

            "capacity":
            capacity,

            "overflow_protection":
            "enabled",

            "compression":
            "enabled"
        }

    # ============================================
    # STORE
    # ============================================

    def store(

        self,

        key,

        value
    ):

        memory_item = {

            "key":
            key,

            "value":
            value,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.memory_stack.append(
            memory_item
        )

        self.enforce_capacity()

    # ============================================
    # ENFORCE CAPACITY
    # ============================================

    def enforce_capacity(self):

        while len(

            self.memory_stack

        ) > self.capacity:

            self.memory_stack.pop(0)

    # ============================================
    # RETRIEVE
    # ============================================

    def retrieve(

        self,

        key
    ):

        for item in reversed(

            self.memory_stack
        ):

            if item["key"] == key:

                return item["value"]

        return None

    # ============================================
    # RECENT MEMORIES
    # ============================================

    def recent(

        self,

        limit=5
    ):

        return self.memory_stack[-limit:]

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        return {

            "memory_type":
            "working_memory",

            "capacity":
            self.capacity,

            "current_size":
            len(
                self.memory_stack
            ),

            "utilization":
            round(

                len(self.memory_stack)

                /

                self.capacity,

                4
            ),

            "state":
            "stable"
        }