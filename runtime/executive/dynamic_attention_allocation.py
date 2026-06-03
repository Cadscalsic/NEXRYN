# ============================================
# NEXRYN DYNAMIC ATTENTION ALLOCATION RUNTIME
# ============================================

from datetime import datetime


CRITICAL_CONTEXT_KEYS = {
    "input_grid",
    "output_grid",
    "predicted_output",
    "ground_truth_output",
    "evaluation_result",
    "winner_hypothesis",
    "ranked_hypotheses",
    "ranked_primitives",
    "semantic_graph",
    "semantic_abstractions",
    "reasoning_allocation",
    "cognitive_governance_report",
    "world_model_anticipation",
    "latent_reasoning_report",
    "cognitive_failure_memory_report"
}


DECAYABLE_CONTEXT_PREFIXES = (
    "debug",
    "archive",
    "history",
    "trace"
)


# ============================================
# DYNAMIC ATTENTION ALLOCATION RUNTIME
# ============================================

class DynamicAttentionAllocationRuntime:

    def __init__(self):

        self.allocation_history = []

        self.focus_window_size = 24

    # ============================================
    # SCORE CONTEXT KEY
    # ============================================

    def score_context_key(
        self,
        key,
        value,
        signals
    ):

        key = str(
            key
        )

        score = 0.10

        if key in CRITICAL_CONTEXT_KEYS:

            score += 0.70

        if any(
            token in key
            for token in [
                "semantic",
                "reasoning",
                "winner",
                "evaluation",
                "governance",
                "attention",
                "latent",
                "failure"
            ]
        ):

            score += 0.20

        if signals.get(
            "reasoning_overrun",
            False
        ) and "reasoning" in key:

            score += 0.15

        if signals.get(
            "ontology_pressure",
            0.0
        ) > 0.60 and "semantic" in key:

            score += 0.15

        if signals.get(
            "working_memory_pressure",
            0.0
        ) > 0.75:

            if key.startswith(
                DECAYABLE_CONTEXT_PREFIXES
            ):

                score -= 0.25

            if isinstance(
                value,
                list
            ) and len(value) > 16:

                score -= 0.10

            if isinstance(
                value,
                dict
            ) and len(value) > 24:

                score -= 0.10

        return round(
            max(
                min(
                    score,
                    1.0
                ),
                0.0
            ),
            4
        )

    # ============================================
    # BUILD FOCUS WINDOW
    # ============================================

    def build_focus_window(
        self,
        context,
        signals
    ):

        scored_keys = []

        for key, value in context.items():

            scored_keys.append({
                "key":
                key,

                "priority":
                self.score_context_key(
                    key,
                    value,
                    signals
                )
            })

        scored_keys = sorted(
            scored_keys,
            key=lambda item: item.get(
                "priority",
                0.0
            ),
            reverse=True
        )

        focused = scored_keys[
            :self.focus_window_size
        ]

        focused_keys = {
            item.get(
                "key"
            )
            for item in focused
        }

        decayed = [
            item
            for item in scored_keys
            if item.get(
                "key"
            )
            not in focused_keys
        ]

        return focused, decayed

    # ============================================
    # ALLOCATE ATTENTION
    # ============================================

    def allocate(
        self,
        context,
        cognitive_cycle,
        memory_pressure_profile=None
    ):

        if not isinstance(
            context,
            dict
        ):

            context = {}

        memory_pressure_profile = (
            memory_pressure_profile
            or {}
        )

        reasoning = cognitive_cycle.get(
            "reasoning",
            {}
        )

        semantic_graph = context.get(
            "semantic_graph",
            {}
        )

        working_memory_pressure = min(
            len(context)
            /
            180,
            1.0
        )

        signals = {
            "working_memory_pressure":
            round(
                working_memory_pressure,
                4
            ),

            "semantic_pressure":
            memory_pressure_profile.get(
                "semantic_pressure",
                0.0
            ),

            "ontology_pressure":
            memory_pressure_profile.get(
                "ontology_pressure",
                0.0
            ),

            "reasoning_overrun":
            reasoning.get(
                "raw_reasoning_depth",
                0
            )
            >
            reasoning.get(
                "reasoning_depth",
                0
            ),

            "semantic_node_count":
            semantic_graph.get(
                "concept_count",
                0
            )
        }

        focus_window, decayed_context = self.build_focus_window(
            context,
            signals
        )

        saturation_level = round(
            min(
                working_memory_pressure * 0.55
                +
                signals.get(
                    "semantic_pressure",
                    0.0
                )
                * 0.25
                +
                signals.get(
                    "ontology_pressure",
                    0.0
                )
                * 0.20,
                1.0
            ),
            4
        )

        pruning_policy = (
            "aggressive_decay"
            if saturation_level >= 0.80
            else "selective_decay"
            if saturation_level >= 0.60
            else "observe"
        )

        allocation = {
            "runtime":
            "dynamic_attention_allocation",

            "priority_attention":
            focus_window,

            "semantic_focus_window":
            [
                item
                for item in focus_window
                if "semantic" in str(
                    item.get(
                        "key",
                        ""
                    )
                )
            ],

            "context_decay_candidates":
            decayed_context[:24],

            "adaptive_context_pruning":
            {
                "policy":
                pruning_policy,

                "recommended_decay_count":
                len(
                    decayed_context
                ),

                "safe_to_prune":
                [
                    item.get(
                        "key"
                    )
                    for item in decayed_context
                    if item.get(
                        "priority",
                        0.0
                    ) < 0.25
                ][:12]
            },

            "attention_saturation":
            saturation_level,

            "signals":
            signals,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.allocation_history.append(
            allocation
        )

        self.allocation_history = (
            self.allocation_history[-32:]
        )

        return allocation

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        latest = (
            self.allocation_history[-1]
            if self.allocation_history
            else {}
        )

        return {
            "allocation_events":
            len(
                self.allocation_history
            ),

            "latest_saturation":
            latest.get(
                "attention_saturation",
                0.0
            ),

            "latest_policy":
            latest.get(
                "adaptive_context_pruning",
                {}
            ).get(
                "policy",
                "observe"
            ),

            "latest_focus_count":
            len(
                latest.get(
                    "priority_attention",
                    []
                )
            )
        }


# ============================================
# GLOBAL RUNTIME
# ============================================

dynamic_attention_allocation_runtime = (
    DynamicAttentionAllocationRuntime()
)
