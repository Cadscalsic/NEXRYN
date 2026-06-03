# ============================================
# NEXRYN COGNITIVE ACTIVATION MANAGER
# ============================================

from datetime import datetime


# ============================================
# COGNITIVE ACTIVATION MANAGER
# ============================================

class CognitiveActivationManager:

    def __init__(self):

        # ====================================
        # ACTIVE SUBSYSTEMS
        # ====================================

        self.active_systems = []

        self.suppressed_systems = []

        # ====================================
        # COGNITIVE BUDGET
        # ====================================

        self.cognitive_budget = {

            "max_active_systems":
            32,

            "max_recursive_depth":
            4,

            "max_context_load":
            64,

            "activation_mode":
            "adaptive_selective"
        }

        # ====================================
        # ACTIVATION HISTORY
        # ====================================

        self.activation_history = []

        # ====================================
        # SYSTEM PRIORITIES
        # ====================================

        self.system_priorities = {

            "reasoning":
            "critical",

            "memory":
            "critical",

            "execution":
            "critical",

            "governance":
            "high",

            "context":
            "high",

            "repair":
            "high",

            "evolution":
            "medium",

            "meta":
            "medium",

            "society":
            "low",

            "civilization":
            "low",

            "genome":
            "low",

            "consciousness":
            "low"
        }

    # ============================================
    # ESTIMATE TASK COMPLEXITY
    # ============================================

    def estimate_complexity(

        self,

        runtime_context
    ):

        context_size = len(
            runtime_context
        )

        complexity_score = 0

        complexity_score += min(
            context_size / 32,
            4
        )

        if "recursive_report" in runtime_context:

            complexity_score += 1

        if "counterfactual_report" in runtime_context:

            complexity_score += 1

        if "meta_report" in runtime_context:

            complexity_score += 1

        return round(
            complexity_score,
            4
        )

    # ============================================
    # BUILD ACTIVATION PLAN
    # ============================================

    def build_activation_plan(

        self,

        runtime_context
    ):

        complexity = self.estimate_complexity(

            runtime_context
        )

        active_systems = [

            "reasoning",

            "memory",

            "execution"
        ]

        # ====================================
        # MEDIUM COMPLEXITY
        # ====================================

        if complexity >= 2:

            active_systems.extend([

                "governance",

                "context",

                "repair"
            ])

        # ====================================
        # HIGH COMPLEXITY
        # ====================================

        if complexity >= 4:

            active_systems.extend([

                "evolution",

                "meta"
            ])

        # ====================================
        # EXTREME COMPLEXITY
        # ====================================

        if complexity >= 6:

            active_systems.extend([

                "society",

                "civilization",

                "genome",

                "consciousness"
            ])

        suppressed_systems = []

        for system in self.system_priorities:

            if system not in active_systems:

                suppressed_systems.append(
                    system
                )

        return {

            "complexity_score":
            complexity,

            "active_systems":
            active_systems,

            "suppressed_systems":
            suppressed_systems,

            "activation_mode":
            "adaptive_selective",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

    # ============================================
    # APPLY ACTIVATION PLAN
    # ============================================

    def apply_activation_plan(

        self,

        activation_plan
    ):

        self.active_systems = activation_plan.get(

            "active_systems",

            []
        )

        self.suppressed_systems = activation_plan.get(

            "suppressed_systems",

            []
        )

        self.activation_history.append(
            activation_plan
        )

        return {

            "activation_result":
            "success",

            "active_systems":
            len(
                self.active_systems
            ),

            "suppressed_systems":
            len(
                self.suppressed_systems
            ),

            "runtime_efficiency":
            "optimized"
        }

    # ============================================
    # SYSTEM ACTIVE
    # ============================================

    def system_active(

        self,

        system_name
    ):

        return system_name in self.active_systems

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        return {

            "active_systems":
            self.active_systems,

            "suppressed_systems":
            self.suppressed_systems,

            "cognitive_budget":
            self.cognitive_budget,

            "activation_cycles":
            len(
                self.activation_history
            ),

            "activation_state":
            "stable"
        }


# ============================================
# GLOBAL ACTIVATION MANAGER
# ============================================

cognitive_activation_manager = (
    CognitiveActivationManager()
)