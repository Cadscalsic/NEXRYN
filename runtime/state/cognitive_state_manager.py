# ============================================
# NEXRYN COGNITIVE STATE MANAGER
# ============================================

from datetime import datetime


# ============================================
# COGNITIVE STATE MANAGER
# ============================================

class CognitiveStateManager:

    def __init__(self):

        # ====================================
        # CORE COGNITIVE STATE
        # ====================================

        self.state = {

            "cognitive_mode":
            "idle",

            "active_goal":
            None,

            "confidence":
            0.0,

            "attention_focus":
            None,

            "reasoning_depth":
            0,

            "exploration_active":
            False,

            "mutation_active":
            False,

            "search_active":
            False,

            "self_improvement_active":
            False,

            "semantic_context":
            [],

            "active_concepts":
            [],

            "runtime_cycle":
            0,

            "cognitive_pressure":
            0.0,

            "activation_state":
            "stable",

            "governance_state":
            "stable",

            "runtime_health":
            "healthy"
        }

        # ====================================
        # STATE HISTORY
        # ====================================

        self.state_history = []

        # ====================================
        # TRANSITION HISTORY
        # ====================================

        self.transition_history = []

    # ============================================
    # UPDATE FROM CONTROL SIGNALS
    # ============================================

    def update_from_control_signals(

        self,

        control_signals
    ):

        self.state[
            "cognitive_mode"
        ] = control_signals.get(

            "cognitive_mode",

            "idle"
        )

        self.state[
            "confidence"
        ] = control_signals.get(

            "confidence",

            0.0
        )

        self.state[
            "exploration_active"
        ] = control_signals.get(

            "requires_mutation",

            False
        )

        self.state[
            "mutation_active"
        ] = control_signals.get(

            "requires_mutation",

            False
        )

        self.state[
            "search_active"
        ] = control_signals.get(

            "requires_search",

            False
        )

        self.state[
            "self_improvement_active"
        ] = control_signals.get(

            "self_improvement",

            False
        )

        self.register_transition(
            "control_signal_update"
        )

    # ============================================
    # UPDATE ACTIVE GOAL
    # ============================================

    def update_goal(

        self,

        selected_goal
    ):

        self.state[
            "active_goal"
        ] = selected_goal

        self.register_transition(
            "goal_update"
        )

    # ============================================
    # UPDATE REASONING DEPTH
    # ============================================

    def update_reasoning_depth(

        self,

        reasoning_trace
    ):

        depth = len(
            reasoning_trace
        )

        self.state[
            "reasoning_depth"
        ] = depth

        # ====================================
        # COGNITIVE PRESSURE
        # ====================================

        self.state[
            "cognitive_pressure"
        ] = round(

            min(
                depth / 10,
                1.0
            ),

            4
        )

        # ====================================
        # ACTIVATION STATE
        # ====================================

        if depth > 8:

            self.state[
                "activation_state"
            ] = "high_load"

        elif depth > 4:

            self.state[
                "activation_state"
            ] = "moderate_load"

        else:

            self.state[
                "activation_state"
            ] = "stable"

        self.register_transition(
            "reasoning_depth_update"
        )

    # ============================================
    # UPDATE SEMANTIC CONTEXT
    # ============================================

    def update_semantic_context(

        self,

        semantic_graph
    ):

        concepts = []

        for node in semantic_graph.get(

            "concept_nodes",

            []
        ):

            concept = node.get(
                "concept"
            )

            if concept is not None:

                concepts.append(
                    concept
                )

        self.state[
            "semantic_context"
        ] = concepts

        self.state[
            "active_concepts"
        ] = concepts

        self.register_transition(
            "semantic_context_update"
        )

    # ============================================
    # ADVANCE RUNTIME CYCLE
    # ============================================

    def advance_cycle(self):

        self.state[
            "runtime_cycle"
        ] += 1

        self.register_transition(
            "runtime_cycle_advance"
        )

    # ============================================
    # UPDATE ATTENTION
    # ============================================

    def update_attention_focus(

        self,

        focus
    ):

        self.state[
            "attention_focus"
        ] = focus

        self.register_transition(
            "attention_update"
        )

    # ============================================
    # REGISTER TRANSITION
    # ============================================

    def register_transition(

        self,

        transition_type
    ):

        self.transition_history.append({

            "transition":
            transition_type,

            "timestamp":
            str(
                datetime.utcnow()
            )
        })

    # ============================================
    # HEALTH CHECK
    # ============================================

    def health_check(self):

        healthy = True

        if self.state[
            "cognitive_pressure"
        ] > 0.9:

            healthy = False

            self.state[
                "runtime_health"
            ] = "overloaded"

        return {

            "healthy":
            healthy,

            "runtime_health":
            self.state[
                "runtime_health"
            ],

            "pressure":
            self.state[
                "cognitive_pressure"
            ]
        }

    # ============================================
    # BUILD STATE REPORT
    # ============================================

    def build_state_report(self):

        return {

            "mode":
            self.state[
                "cognitive_mode"
            ],

            "confidence":
            self.state[
                "confidence"
            ],

            "reasoning_depth":
            self.state[
                "reasoning_depth"
            ],

            "active_concepts":
            self.state[
                "active_concepts"
            ],

            "exploration":
            self.state[
                "exploration_active"
            ],

            "search":
            self.state[
                "search_active"
            ],

            "runtime_cycle":
            self.state[
                "runtime_cycle"
            ],

            "cognitive_pressure":
            self.state[
                "cognitive_pressure"
            ],

            "activation_state":
            self.state[
                "activation_state"
            ],

            "runtime_health":
            self.state[
                "runtime_health"
            ],

            "transition_count":
            len(
                self.transition_history
            )
        }

    # ============================================
    # GET FULL STATE
    # ============================================

    def get_state(self):

        return self.state

    # ============================================
    # BUILD FULL REPORT
    # ============================================

    def build_full_report(self):

        return {

            "state":
            self.state,

            "health":
            self.health_check(),

            "transitions":
            len(
                self.transition_history
            ),

            "manager_state":
            "stable"
        }