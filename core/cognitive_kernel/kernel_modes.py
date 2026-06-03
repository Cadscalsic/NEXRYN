# ============================================
# NEXRYN KERNEL MODES
# ============================================


class KernelModes:

    REASONING = "reasoning_mode"
    STABILIZATION = "stabilization_mode"
    EXPLORATION = "exploration_mode"

    MODE_SUBSYSTEMS = {
        REASONING: [
            "semantic_routing",
            "cognitive_os",
            "causal_prediction",
            "goal_hierarchy",
            "self_model",
            "meta_executive",
            "reasoning",
        ],
        STABILIZATION: [
            "semantic_routing",
            "thermodynamics",
            "immune_system",
            "semantic_os",
            "goal_hierarchy",
            "self_model",
            "meta_executive",
        ],
        EXPLORATION: [
            "semantic_routing",
            "cognitive_os",
            "controlled_novelty",
            "causal_prediction",
            "goal_hierarchy",
            "self_model",
            "meta_executive",
            "reasoning",
        ],
    }

    MODE_DISABLED = {
        REASONING: [
            "controlled_novelty",
            "deep_simulation",
            "sandbox_recursion",
            "distributed_execution",
            "semantic_fabric",
        ],
        STABILIZATION: [
            "controlled_novelty",
            "distributed_execution",
            "semantic_fabric",
            "deep_reasoning",
            "sandbox_recursion",
            "reasoning",
        ],
        EXPLORATION: [
            "distributed_execution",
            "semantic_fabric",
            "deep_simulation",
        ],
    }

    def enabled_for(self, mode):

        return list(
            self.MODE_SUBSYSTEMS.get(
                mode,
                self.MODE_SUBSYSTEMS[self.REASONING],
            )
        )

    def disabled_for(self, mode):

        return list(
            self.MODE_DISABLED.get(
                mode,
                [],
            )
        )
