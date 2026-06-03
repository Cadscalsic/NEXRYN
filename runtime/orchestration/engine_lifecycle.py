# ============================================
# NEXRYN ENGINE LIFECYCLE MANAGER
# ============================================

class EngineLifecycleManager:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.engine_states = {}

    # ========================================
    # REGISTER ENGINE
    # ========================================

    def register(

        self,

        engine_name
    ):

        self.engine_states[engine_name] = {

            "status":
            "registered",

            "executions":
            0,

            "failures":
            0
        }

    # ========================================
    # START ENGINE
    # ========================================

    def start(

        self,

        engine_name
    ):

        if engine_name not in self.engine_states:

            self.register(engine_name)

        self.engine_states[engine_name][

            "status"

        ] = "active"

        self.engine_states[engine_name][

            "executions"

        ] += 1

    # ========================================
    # COMPLETE ENGINE
    # ========================================

    def complete(

        self,

        engine_name
    ):

        if engine_name not in self.engine_states:

            return

        self.engine_states[engine_name][

            "status"

        ] = "completed"

    # ========================================
    # FAIL ENGINE
    # ========================================

    def fail(

        self,

        engine_name
    ):

        if engine_name not in self.engine_states:

            return

        self.engine_states[engine_name][

            "status"

        ] = "failed"

        self.engine_states[engine_name][

            "failures"

        ] += 1

    # ========================================
    # SUSPEND ENGINE
    # ========================================

    def suspend(

        self,

        engine_name
    ):

        if engine_name not in self.engine_states:

            return

        self.engine_states[engine_name][

            "status"

        ] = "suspended"

    # ========================================
    # ENGINE STATUS
    # ========================================

    def status(

        self,

        engine_name
    ):

        return self.engine_states.get(

            engine_name,

            {}
        )

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "registered_engines":

            len(self.engine_states),

            "engines":
            self.engine_states
        }