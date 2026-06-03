# =========================================================
# NEXRYN RECURSIVE EXECUTIVE REGULATION
# =========================================================

from datetime import datetime
from dataclasses import dataclass, field

import uuid
import random

MIN_EXPLORATION_RATE = 0.02

MIN_REASONING_DEPTH_LIMIT = 4

MAX_REASONING_DEPTH_LIMIT = 15


# =========================================================
# REGULATION NODE
# =========================================================

@dataclass
class RegulationNode:

    node_id: str

    exploration_rate: float

    mutation_rate: float

    reasoning_depth_limit: int

    uncertainty_level: float

    energy_pressure: float

    regulation_mode: str

    created_at: str = field(

        default_factory=lambda:
        str(datetime.utcnow())
    )


# =========================================================
# META CONTROLLER ENGINE
# =========================================================

class MetaControllerEngine:

    # =====================================================
    # INITIALIZE ENGINE
    # =====================================================

    def __init__(self):

        # =================================================
        # CONTROL STATE
        # =================================================

        self.control_state = {

            "exploration_rate":
            0.30,

            "mutation_rate":
            0.20,

            "reasoning_depth_limit":
            10,

            "cognitive_mode":
            "balanced",

            "executive_regulation":
            "adaptive",

            "uncertainty_governance":
            "enabled",

            "energy_management":
            "active",

            "recovery_protocol":
            "standby"
        }

        self.control_history = []

        self.regulation_graph = []

        self.executive_interventions = []

        self.energy_history = []

        self.policy_memory = []

        self.overload_events = []

        self.recursive_regulation = []

        self.outcome_history = []

    # =====================================================
    # RECORD OUTCOME
    # =====================================================

    def record_outcome(
        self,
        evaluation_result
    ):

        if not isinstance(
            evaluation_result,
            dict
        ):

            evaluation_result = {}

        self.outcome_history.append({

            "success":
            bool(
                evaluation_result.get(
                    "success",
                    False
                )
            ),

            "accuracy":
            evaluation_result.get(
                "accuracy",
                0.0
            ),

            "timestamp":
            str(datetime.utcnow())
        })

        self.outcome_history = (
            self.outcome_history[-10:]
        )

        return self.recent_success_rate()

    # =====================================================
    # RECENT SUCCESS RATE
    # =====================================================

    def recent_success_rate(self):

        if not self.outcome_history:

            return 0.0

        successes = len([

            outcome

            for outcome in self.outcome_history

            if outcome.get(
                "success",
                False
            )
        ])

        return round(
            successes
            /
            len(self.outcome_history),
            4
        )

    # =====================================================
    # ESTIMATE UNCERTAINTY
    # =====================================================

    def estimate_uncertainty(

        self,

        recursive_report
    ):

        complexity = recursive_report.get(
            "cognitive_complexity",
            "low"
        )

        if complexity == "high":

            return 0.75

        elif complexity == "medium":

            return 0.45

        return 0.20

    # =====================================================
    # ESTIMATE ENERGY PRESSURE
    # =====================================================

    def estimate_energy_pressure(

        self,

        recursive_report
    ):

        reasoning_depth = recursive_report.get(
            "reasoning_depth",
            0
        )

        pressure = round(

            min(
                reasoning_depth / 20,
                1.0
            ),

            2
        )

        self.energy_history.append({

            "pressure":
            pressure,

            "timestamp":
            str(datetime.utcnow())
        })

        return pressure

    # =====================================================
    # ADAPT CONTROL
    # =====================================================

    def adapt_control(

        self,

        recursive_report
    ):

        task_complexity = recursive_report.get(
            "task_complexity",
            None
        )

        complexity = recursive_report.get(
            "cognitive_complexity",
            "low"
        )

        mutation_detected = recursive_report.get(
            "mutation_detected",
            False
        )

        exploration_detected = recursive_report.get(
            "exploration_detected",
            False
        )

        uncertainty = (
            self.estimate_uncertainty(
                recursive_report
            )
        )

        energy_pressure = (
            self.estimate_energy_pressure(
                recursive_report
            )
        )

        # =================================================
        # HIGH COMPLEXITY
        # =================================================

        if complexity == "high":

            self.control_state[
                "exploration_rate"
            ] = 0.15

            self.control_state[
                "mutation_rate"
            ] = 0.10

            self.control_state[
                "reasoning_depth_limit"
            ] = 15

            self.control_state[
                "cognitive_mode"
            ] = "focused"

        # =================================================
        # MEDIUM COMPLEXITY
        # =================================================

        elif complexity == "medium":

            self.control_state[
                "exploration_rate"
            ] = 0.25

            self.control_state[
                "mutation_rate"
            ] = 0.20

            self.control_state[
                "reasoning_depth_limit"
            ] = 12

            self.control_state[
                "cognitive_mode"
            ] = "balanced"

        # =================================================
        # LOW COMPLEXITY
        # =================================================

        else:

            self.control_state[
                "exploration_rate"
            ] = 0.40

            self.control_state[
                "mutation_rate"
            ] = 0.35

            self.control_state[
                "reasoning_depth_limit"
            ] = 8

            self.control_state[
                "cognitive_mode"
            ] = "exploratory"

        # =================================================
        # ADAPTIVE DEPTH REGULATION
        # =================================================

        if isinstance(
            task_complexity,
            (int, float)
        ):

            if task_complexity < 0.30:

                self.control_state[
                    "reasoning_depth_limit"
                ] = MIN_REASONING_DEPTH_LIMIT

                self.control_state[
                    "cognitive_mode"
                ] = "minimal_reasoning"

            elif task_complexity > 0.80:

                self.control_state[
                    "reasoning_depth_limit"
                ] = MAX_REASONING_DEPTH_LIMIT

            else:

                self.control_state[
                    "reasoning_depth_limit"
                ] = 8

        # =================================================
        # UNCERTAINTY GOVERNANCE
        # =================================================

        if uncertainty >= 0.70:

            if not (

                isinstance(
                    task_complexity,
                    (int, float)
                )

                and

                task_complexity < 0.30
            ):

                self.control_state[
                    "reasoning_depth_limit"
                ] += 3

            self.control_state[
                "cognitive_mode"
            ] = "stabilization"

        # =================================================
        # ENERGY OVERLOAD
        # =================================================

        if energy_pressure >= 0.80:

            overload = {

                "event_id":
                str(uuid.uuid4()),

                "event":
                "cognitive_overload",

                "severity":
                "high",

                "timestamp":
                str(datetime.utcnow())
            }

            self.overload_events.append(
                overload
            )

            self.control_state[
                "exploration_rate"
            ] *= 0.5

            self.control_state[
                "mutation_rate"
            ] *= 0.5

            self.control_state[
                "recovery_protocol"
            ] = "active"

        # =================================================
        # BOOST EXPLORATION
        # =================================================

        if not exploration_detected:

            self.control_state[
                "exploration_rate"
            ] += 0.05

        # =================================================
        # BOOST MUTATION
        # =================================================

        if not mutation_detected:

            self.control_state[
                "mutation_rate"
            ] += 0.05

        # =================================================
        # SUCCESS STABILIZATION
        # =================================================

        recent_success_rate = (
            self.recent_success_rate()
        )

        if recent_success_rate > 0.90:

            self.control_state[
                "exploration_rate"
            ] = max(
                self.control_state.get(
                    "exploration_rate",
                    0.0
                )
                * 0.5,
                MIN_EXPLORATION_RATE
            )

            self.control_state[
                "mutation_rate"
            ] = max(
                self.control_state.get(
                    "mutation_rate",
                    0.0
                )
                * 0.75,
                0.02
            )

            self.control_state[
                "cognitive_mode"
            ] = "stabilization"

        self.control_state[
            "exploration_rate"
        ] = max(
            self.control_state.get(
                "exploration_rate",
                0.0
            ),
            MIN_EXPLORATION_RATE
        )

        self.control_state[
            "reasoning_depth_limit"
        ] = int(
            min(
                max(
                    self.control_state.get(
                        "reasoning_depth_limit",
                        8
                    ),
                    MIN_REASONING_DEPTH_LIMIT
                ),
                MAX_REASONING_DEPTH_LIMIT
            )
        )

        # =================================================
        # STORE HISTORY
        # =================================================

        self.control_history.append(

            self.control_state.copy()
        )

        return self.control_state

    # =====================================================
    # EXECUTIVE INTERVENTION
    # =====================================================

    def executive_intervention(

        self,

        recursive_report
    ):

        reasoning_depth = recursive_report.get(
            "reasoning_depth",
            0
        )

        intervention = None

        if reasoning_depth >= 18:

            intervention = {

                "intervention_id":
                str(uuid.uuid4()),

                "intervention_type":
                "reduce_recursive_depth",

                "executive_action":
                "stabilize_runtime",

                "timestamp":
                str(datetime.utcnow())
            }

        elif reasoning_depth <= 3:

            intervention = {

                "intervention_id":
                str(uuid.uuid4()),

                "intervention_type":
                "increase_exploration",

                "executive_action":
                "expand_reasoning",

                "timestamp":
                str(datetime.utcnow())
            }

        if intervention:

            self.executive_interventions.append(
                intervention
            )

        return intervention

    # =====================================================
    # RECURSIVE REGULATION
    # =====================================================

    def recursive_regulation_cycle(

        self,

        control_state
    ):

        regulation = {

            "regulation_id":
            str(uuid.uuid4()),

            "control_snapshot":
            control_state.copy(),

            "regulation_depth":

            len(
                self.recursive_regulation
            ) + 1,

            "regulation_state":
            "adaptive_recursive",

            "timestamp":
            str(datetime.utcnow())
        }

        self.recursive_regulation.append(
            regulation
        )

        return regulation

    # =====================================================
    # BUILD REGULATION GRAPH
    # =====================================================

    def build_regulation_graph(

        self,

        control_state,

        uncertainty,

        energy_pressure
    ):

        node = RegulationNode(

            node_id=str(uuid.uuid4()),

            exploration_rate=

            control_state.get(
                "exploration_rate"
            ),

            mutation_rate=

            control_state.get(
                "mutation_rate"
            ),

            reasoning_depth_limit=

            control_state.get(
                "reasoning_depth_limit"
            ),

            uncertainty_level=
            uncertainty,

            energy_pressure=
            energy_pressure,

            regulation_mode=

            control_state.get(
                "cognitive_mode"
            )
        )

        self.regulation_graph.append(
            node
        )

        return node

    # =====================================================
    # CONSOLIDATE CONTROL POLICY
    # =====================================================

    def consolidate_control_policy(

        self,

        control_state
    ):

        policy = {

            "policy_id":
            str(uuid.uuid4()),

            "policy":
            control_state.copy(),

            "policy_type":
            "executive_regulation",

            "timestamp":
            str(datetime.utcnow())
        }

        self.policy_memory.append(
            policy
        )

        return policy

    # =====================================================
    # RUN CONTROL CYCLE
    # =====================================================

    def run_control_cycle(

        self,

        recursive_report
    ):

        uncertainty = (
            self.estimate_uncertainty(
                recursive_report
            )
        )

        energy_pressure = (
            self.estimate_energy_pressure(
                recursive_report
            )
        )

        control_state = (
            self.adapt_control(
                recursive_report
            )
        )

        intervention = (
            self.executive_intervention(
                recursive_report
            )
        )

        recursive_regulation = (

            self.recursive_regulation_cycle(
                control_state
            )
        )

        regulation_graph = (

            self.build_regulation_graph(

                control_state,

                uncertainty,

                energy_pressure
            )
        )

        policy = (

            self.consolidate_control_policy(
                control_state
            )
        )

        return {

            "control_state":
            control_state,

            "uncertainty":
            uncertainty,

            "energy_pressure":
            energy_pressure,

            "intervention":
            intervention,

            "recursive_regulation":
            recursive_regulation,

            "regulation_graph":
            regulation_graph,

            "policy":
            policy,

            "timestamp":
            str(datetime.utcnow())
        }

    # =====================================================
    # GET CONTROL STATE
    # =====================================================

    def get_control_state(self):

        return self.control_state

    # =====================================================
    # BUILD REPORT
    # =====================================================

    def build_report(self):

        return {

            "control_state":
            self.control_state,

            "control_history":
            len(self.control_history),

            "regulation_graph":
            len(self.regulation_graph),

            "executive_interventions":

            len(
                self.executive_interventions
            ),

            "overload_events":
            len(self.overload_events),

            "policy_memory":
            len(self.policy_memory),

            "recursive_regulation":
            len(self.recursive_regulation)
        }

    # =====================================================
    # PRINT CONTROL STATE
    # =====================================================

    def print_control_state(

        self,

        control_state
    ):

        print("\n==================================================")
        print("NEXRYN :: META CONTROLLER")
        print("==================================================\n")

        print(control_state)
