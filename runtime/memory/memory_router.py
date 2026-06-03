# ============================================
# NEXRYN MEMORY ROUTER
# ============================================

from datetime import datetime


# ============================================
# MEMORY ROUTER
# ============================================

class MemoryRouter:

    def __init__(self):

        self.routing_history = []

        self.memory_layers = {

            "working_memory":
            [],

            "episodic_memory":
            [],

            "semantic_memory":
            [],

            "long_term_memory":
            []
        }

    # ============================================
    # ROUTE MEMORY
    # ============================================

    def route_memory(

        self,

        memory_item,

        memory_type="working"
    ):

        routing_table = {

            "working":
            "working_memory",

            "episodic":
            "episodic_memory",

            "semantic":
            "semantic_memory",

            "long_term":
            "long_term_memory"
        }

        target_layer = routing_table.get(

            memory_type,

            "working_memory"
        )

        self.memory_layers[
            target_layer
        ].append(

            memory_item
        )

        routing_report = {

            "memory_type":
            memory_type,

            "target_layer":
            target_layer,

            "memory_size":
            len(

                self.memory_layers[
                    target_layer
                ]
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.routing_history.append(
            routing_report
        )

        return routing_report

    # ============================================
    # GET MEMORY LAYER
    # ============================================

    def get_memory_layer(

        self,

        layer_name
    ):

        return self.memory_layers.get(

            layer_name,

            []
        )

    # ============================================
    # BUILD MEMORY REPORT
    # ============================================

    def build_memory_report(self):

        return {

            "working_memory":
            len(
                self.memory_layers[
                    "working_memory"
                ]
            ),

            "episodic_memory":
            len(
                self.memory_layers[
                    "episodic_memory"
                ]
            ),

            "semantic_memory":
            len(
                self.memory_layers[
                    "semantic_memory"
                ]
            ),

            "long_term_memory":
            len(
                self.memory_layers[
                    "long_term_memory"
                ]
            ),

            "routing_cycles":
            len(
                self.routing_history
            )
        }