# ============================================
# NEXRYN COGNITIVE STATE MANAGER
# ============================================


# ============================================
# COGNITIVE STATE MANAGER
# ============================================

class CognitiveStateManager:

    def __init__(self):

        self.cognitive_state = {

            "hypothesis_count":
            0,

            "top_confidence":
            0.0,

            "goal_state":
            {},

            "recursive_depth":
            0,

            "semantic_concepts":
            0,

            "analogical_matches":
            0,

            "search_complexity":
            0
        }

    # ============================================
    # UPDATE STATE
    # ============================================

    def update_state(

        self,

        state
    ):

        self.cognitive_state.update(
            state
        )

    # ============================================
    # GET STATE
    # ============================================

    def get_state(self):

        return self.cognitive_state

    # ============================================
    # RESET STATE
    # ============================================

    def reset_state(self):

        self.cognitive_state = {

            "hypothesis_count":
            0,

            "top_confidence":
            0.0,

            "goal_state":
            {},

            "recursive_depth":
            0,

            "semantic_concepts":
            0,

            "analogical_matches":
            0,

            "search_complexity":
            0
        }

    # ============================================
    # BUILD STATE REPORT
    # ============================================

    def build_state_report(self):

        return {

            "cognitive_state":
            self.cognitive_state,

            "state_dimensions":
            len(
                self.cognitive_state
            )
        }