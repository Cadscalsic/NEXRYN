# ============================================
# RUNTIME AWARENESS SYSTEM
# ============================================

class RuntimeAwareness:

    def __init__(self):

        self.live_state = {

            "current_stage":
            None,

            "previous_stage":
            None,

            "completed_stages":
            [],

            "failed_stages":
            [],

            "runtime_health":
            "stable",

            "cognitive_load":
            0.0,

            "execution_cycles":
            0
        }

    # ========================================
    # UPDATE ACTIVE STAGE
    # ========================================

    def update_stage(

        self,

        stage_name
    ):

        self.live_state[
            "previous_stage"
        ] = self.live_state.get(
            "current_stage"
        )

        self.live_state[
            "current_stage"
        ] = stage_name

    # ========================================
    # COMPLETE STAGE
    # ========================================

    def complete_stage(

        self,

        stage_name
    ):

        # ====================================
        # REGISTER COMPLETED STAGE
        # ====================================

        self.live_state[
            "completed_stages"
        ].append(
            stage_name
        )

        # ====================================
        # FINAL EXECUTION CYCLE
        # ====================================

        if stage_name == "self_improvement_stage":

            self.live_state[
                "execution_cycles"
            ] += 1

        # ====================================
        # UPDATE HEALTH
        # ====================================

        self.live_state[
            "runtime_health"
        ] = "stable"
    # ========================================
    # FAIL STAGE
    # ========================================

    def fail_stage(

        self,

        stage_name
    ):

        self.live_state[
            "failed_stages"
        ].append(stage_name)

        self.live_state[
            "runtime_health"
        ] = "degraded"

    # ========================================
    # UPDATE LOAD
    # ========================================

    def update_load(

        self,

        load
    ):

        self.live_state[
            "cognitive_load"
        ] = round(
            load,
            4
        )

    # ========================================
    # REGISTER EXECUTION CYCLE
    # ========================================

    def register_cycle(self):

        self.live_state[
            "execution_cycles"
        ] += 1

    # ========================================
    # BUILD LIVE REPORT
    # ========================================

    def build_report(self):

        return self.live_state