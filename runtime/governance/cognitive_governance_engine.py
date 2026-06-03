# ============================================
# NEXRYN COGNITIVE GOVERNANCE ENGINE
# ============================================

from datetime import datetime


# ============================================
# COGNITIVE GOVERNANCE ENGINE
# ============================================

class CognitiveGovernanceEngine:

    def __init__(self):

        self.governance_history = []

        self.long_horizon_history = []

    # ============================================
    # COUNT SEMANTIC PENALTIES
    # ============================================

    def count_semantic_penalties(
        self,
        context
    ):

        penalties = 0

        contradictions = []

        for abstraction in context.get(
            "semantic_abstractions",
            []
        ):

            if not isinstance(
                abstraction,
                dict
            ):

                continue

            penalty = abstraction.get(
                "semantic_penalty",
                0
            )

            penalties += penalty

            if penalty:

                contradictions.append({

                    "primitive":
                    abstraction.get(
                        "primitive"
                    ),

                    "semantic_concept":
                    abstraction.get(
                        "semantic_concept"
                    ),

                    "reason":
                    abstraction.get(
                        "semantic_consistency_reason"
                    )
                })

        return penalties, contradictions

    # ============================================
    # BUILD GOVERNANCE ACTIONS
    # ============================================

    def build_governance_actions(
        self,
        signals
    ):

        actions = []

        if signals.get(
            "projected_entropy",
            0
        ) > signals.get(
            "entropy_events",
            0
        ):

            actions.append(
                "preempt_entropy_growth"
            )

        if signals.get(
            "projected_memory_pressure",
            0.0
        ) > 0.75:

            actions.append(
                "preempt_memory_compression"
            )

        if signals.get(
            "ontology_pressure",
            0.0
        ) > 0.65:

            actions.append(
                "compress_ontology"
            )

        if signals.get(
            "semantic_penalties",
            0
        ) > 0:

            actions.append(
                "block_semantic_drift"
            )

        if signals.get(
            "entropy_events",
            0
        ) > 0:

            actions.append(
                "stabilize_memory_population"
            )

        if signals.get(
            "simulation_uncertainty",
            0.0
        ) > 0.45:

            actions.append(
                "increase_targeted_exploration"
            )

        if signals.get(
            "reasoning_overrun",
            False
        ):

            actions.append(
                "throttle_recursive_reasoning"
            )

        if signals.get(
            "memory_pressure",
            0.0
        ) > 0.75:

            actions.append(
                "compress_memory"
            )

        if signals.get(
            "working_memory_pressure",
            0.0
        ) > 0.75:

            actions.append(
                "allocate_attention_window"
            )

            actions.append(
                "decay_low_priority_context"
            )

        if signals.get(
            "attention_saturation",
            0.0
        ) > 0.70:

            actions.append(
                "narrow_semantic_focus_window"
            )

        if not actions:

            actions.append(
                "maintain_stable_execution"
            )

        return actions

    # ============================================
    # BUILD HOMEOSTASIS PROFILE
    # ============================================

    def build_homeostasis_profile(
        self,
        future_state_projection,
        memory_pressure_profile,
        signals
    ):

        stabilization_need = round(
            min(
                future_state_projection.get(
                    "projected_memory_pressure",
                    0.0
                )
                * 0.35
                +
                min(
                    future_state_projection.get(
                        "projected_entropy",
                        0
                    )
                    / 10,
                    1.0
                )
                * 0.35
                +
                signals.get(
                    "ontology_pressure",
                    0.0
                )
                * 0.20
                +
                (
                    0.10
                    if signals.get(
                        "reasoning_overrun",
                        False
                    )
                    else 0.0
                ),
                1.0
            ),
            4
        )

        return {
            "homeostasis_state":
            (
                "protective_stabilization"
                if future_state_projection.get(
                    "future_state"
                ) == "stabilize"
                else "balanced_adaptation"
            ),

            "self_preservation_drive":
            stabilization_need,

            "stability_priority":
            (
                "critical"
                if stabilization_need >= 0.75
                else "high"
                if stabilization_need >= 0.55
                else "normal"
            ),

            "pressure_basis":
            memory_pressure_profile
        }

    # ============================================
    # MEMORY PRESSURE COMPONENTS
    # ============================================

    def build_memory_pressure_profile(
        self,
        context,
        memory_report
    ):

        strategy_population = memory_report.get(
            "strategy_population",
            0
        )

        semantic_graph = context.get(
            "semantic_graph",
            {}
        )

        semantic_nodes = semantic_graph.get(
            "concept_count",
            0
        )

        ontology_hits = semantic_graph.get(
            "ontology_hits",
            0
        )

        compressed_concepts = len(
            semantic_graph.get(
                "compressed_concept_distribution",
                {}
            )
        )

        semantic_edges = len(
            semantic_graph.get(
                "concept_edges",
                []
            )
        )

        episodic_pressure = min(
            context.get(
                "history_size",
                0
            )
            /
            25,
            1.0
        )

        semantic_pressure = min(
            (
                semantic_nodes
                +
                semantic_edges
            )
            /
            40,
            1.0
        )

        working_memory_pressure = min(
            len(context)
            /
            180,
            1.0
        )

        strategy_population_pressure = min(
            strategy_population
            /
            20,
            1.0
        )

        ontology_pressure = min(
            ontology_hits
            /
            max(
                compressed_concepts * 12,
                12
            ),
            1.0
        )

        combined_pressure = round(
            (
                episodic_pressure * 0.20
                +
                semantic_pressure * 0.20
                +
                working_memory_pressure * 0.25
                +
                strategy_population_pressure * 0.25
                +
                ontology_pressure * 0.10
            ),
            4
        )

        return {

            "episodic_pressure":
            round(
                episodic_pressure,
                4
            ),

            "semantic_pressure":
            round(
                semantic_pressure,
                4
            ),

            "working_memory_pressure":
            round(
                working_memory_pressure,
                4
            ),

            "strategy_population_pressure":
            round(
                strategy_population_pressure,
                4
            ),

            "ontology_pressure":
            round(
                ontology_pressure,
                4
            ),

            "combined_pressure":
            combined_pressure
        }

    # ============================================
    # PROJECT FUTURE STATE
    # ============================================

    def project_future_state(
        self,
        signals,
        memory_pressure_profile
    ):

        previous = (
            self.long_horizon_history[-1]
            if self.long_horizon_history
            else {}
        )

        previous_entropy = previous.get(
            "entropy_events",
            signals.get(
                "entropy_events",
                0
            )
        )

        entropy_delta = (
            signals.get(
                "entropy_events",
                0
            )
            -
            previous_entropy
        )

        projected_entropy = max(
            signals.get(
                "entropy_events",
                0
            )
            +
            max(
                entropy_delta,
                0
            ),
            0
        )

        previous_pressure = previous.get(
            "combined_pressure",
            memory_pressure_profile.get(
                "combined_pressure",
                0.0
            )
        )

        pressure_delta = (
            memory_pressure_profile.get(
                "combined_pressure",
                0.0
            )
            -
            previous_pressure
        )

        projected_memory_pressure = min(
            memory_pressure_profile.get(
                "combined_pressure",
                0.0
            )
            +
            max(
                pressure_delta,
                0.0
            ),
            1.0
        )

        long_term_goal_drift = round(
            min(
                signals.get(
                    "semantic_penalties",
                    0
                )
                * 0.20
                +
                signals.get(
                    "simulation_uncertainty",
                    0.0
                )
                * 0.40
                +
                projected_memory_pressure * 0.40,
                1.0
            ),
            4
        )

        projection = {

            "future_state":
            (
                "stabilize"
                if projected_entropy > signals.get(
                    "entropy_events",
                    0
                )
                or projected_memory_pressure > 0.75
                else "continue"
            ),

            "projected_entropy":
            projected_entropy,

            "projected_memory_pressure":
            round(
                projected_memory_pressure,
                4
            ),

            "entropy_delta":
            entropy_delta,

            "pressure_delta":
            round(
                pressure_delta,
                4
            ),

            "long_term_goal_drift":
            long_term_goal_drift
        }

        self.long_horizon_history.append({

            "entropy_events":
            signals.get(
                "entropy_events",
                0
            ),

            "combined_pressure":
            memory_pressure_profile.get(
                "combined_pressure",
                0.0
            ),

            "projection":
            projection
        })

        self.long_horizon_history = (
            self.long_horizon_history[-12:]
        )

        return projection

    # ============================================
    # GOVERN
    # ============================================

    def govern(
        self,
        context
    ):

        if not isinstance(
            context,
            dict
        ):

            context = {}

        semantic_penalties, contradictions = (
            self.count_semantic_penalties(
                context
            )
        )

        memory_report = context.get(
            "memory_report",
            {}
        )

        anticipation = context.get(
            "world_model_anticipation",
            {}
        )

        uncertainty_report = anticipation.get(
            "uncertainty_report",
            {}
        )

        raw_depth = context.get(
            "raw_reasoning_depth",
            0
        )

        depth_limit = context.get(
            "reasoning_depth_limit",
            0
        )

        memory_pressure_profile = (
            self.build_memory_pressure_profile(
                context,
                memory_report
            )
        )

        signals = {

            "semantic_penalties":
            semantic_penalties,

            "semantic_contradictions":
            contradictions,

            "entropy_events":
            memory_report.get(
                "entropy_events",
                0
            ),

            "simulation_uncertainty":
            uncertainty_report.get(
                "simulation_uncertainty",
                0.0
            ),

            "prediction_confidence":
            uncertainty_report.get(
                "prediction_confidence",
                0.0
            ),

            "reasoning_overrun":
            raw_depth > depth_limit
            if depth_limit
            else False,

            "memory_pressure":
            memory_pressure_profile.get(
                "combined_pressure",
                0.0
            ),

            "working_memory_pressure":
            memory_pressure_profile.get(
                "working_memory_pressure",
                0.0
            ),

            "ontology_pressure":
            memory_pressure_profile.get(
                "ontology_pressure",
                0.0
            ),

            "attention_saturation":
            (
                context
                .get(
                    "dynamic_attention_allocation",
                    {}
                )
                .get(
                    "attention_saturation",
                    0.0
                )
            )
        }

        future_state_projection = self.project_future_state(
            signals,
            memory_pressure_profile
        )

        signals[
            "projected_entropy"
        ] = future_state_projection.get(
            "projected_entropy",
            signals.get(
                "entropy_events",
                0
            )
        )

        signals[
            "projected_memory_pressure"
        ] = future_state_projection.get(
            "projected_memory_pressure",
            signals.get(
                "memory_pressure",
                0.0
            )
        )

        cognitive_budget = {

            "reasoning_depth_limit":
            depth_limit,

            "memory_pressure":
            signals[
                "memory_pressure"
            ],

            "memory_pressure_profile":
            memory_pressure_profile,

            "exploration_policy":
            (
                "reduced_preemptively"
                if future_state_projection.get(
                    "future_state"
                ) == "stabilize"
                else "targeted"
                if signals[
                    "simulation_uncertainty"
                ] > 0.45
                else "stabilized"
            ),

            "semantic_guard":
            semantic_penalties == 0
        }

        actions = self.build_governance_actions(
            signals
        )

        homeostasis_profile = self.build_homeostasis_profile(
            future_state_projection,
            memory_pressure_profile,
            signals
        )

        report = {

            "governance":
            "cognitive",

            "executive_state":
            (
                "intervene"
                if actions != [
                    "maintain_stable_execution"
                ]
                else "stable"
            ),

            "cognitive_budget":
            cognitive_budget,

            "signals":
            signals,

            "future_state_projection":
            future_state_projection,

            "long_horizon":
            {
                "multi_episode_events":
                len(
                    self.long_horizon_history
                ),

                "strategic_continuity":
                "active",

                "long_term_goal_drift":
                future_state_projection.get(
                    "long_term_goal_drift",
                    0.0
                )
            },

            "homeostasis":
            homeostasis_profile,

            "actions":
            actions,

            "timestamp":
            str(datetime.utcnow())
        }

        self.governance_history.append(
            report
        )

        return report


# ============================================
# GLOBAL ENGINE
# ============================================

cognitive_governance_engine = (
    CognitiveGovernanceEngine()
)
