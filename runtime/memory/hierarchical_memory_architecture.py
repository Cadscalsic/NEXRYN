# ============================================
# NEXRYN HIERARCHICAL MEMORY ARCHITECTURE
# ============================================

from datetime import datetime


MEMORY_LAYER_KEYS = {
    "working_memory": [
        "input_grid",
        "output_grid",
        "predicted_output",
        "winner_hypothesis",
        "execution_plan",
        "evaluation_result"
    ],
    "semantic_memory": [
        "semantic_graph",
        "semantic_abstractions",
        "semantic_index_report",
        "operator_weights"
    ],
    "episodic_memory": [
        "recent_episodes",
        "temporal_report",
        "evaluation_history",
        "execution_trace"
    ],
    "ontology_memory": [
        "semantic_graph",
        "cognitive_failure_memory_report",
        "operator_reward_report"
    ],
    "immune_memory": [
        "cognitive_failure_memory_report",
        "cognitive_failure_memory_events",
        "failure_summary",
        "rejected_hypotheses"
    ],
    "latent_memory": [
        "latent_reasoning_report",
        "latent_reasoning_event",
        "latent_reasoning_reactivation"
    ]
}


MEMORY_LAYER_BUDGETS = {
    "working_memory": 24,
    "semantic_memory": 48,
    "episodic_memory": 32,
    "ontology_memory": 36,
    "immune_memory": 24,
    "latent_memory": 16
}


def estimate_payload_size(value):

    if value is None:

        return 0

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
            dict
        )
    ):

        return len(
            value
        )

    return 1


class HierarchicalMemoryArchitecture:

    def __init__(self):

        self.architecture_history = []

    def build_layer(
        self,
        context,
        layer_name,
        keys
    ):

        present = []
        missing = []

        for key in keys:

            if key in context:

                present.append(
                    key
                )

            else:

                missing.append(
                    key
                )

        payload_size = sum(
            estimate_payload_size(
                context.get(
                    key
                )
            )
            for key in present
        )

        coverage_pressure = (
            len(present)
            /
            max(
                len(keys),
                1
            )
        )

        payload_budget = (
            MEMORY_LAYER_BUDGETS.get(
                layer_name,
                32
            )
        )

        payload_pressure = min(
            payload_size
            /
            payload_budget,
            1.0
        )

        pressure = round(
            min(
                coverage_pressure * 0.35
                +
                payload_pressure * 0.65,
                1.0
            ),
            4
        )

        return {
            "layer":
            layer_name,

            "present_keys":
            present,

            "missing_keys":
            missing,

            "payload_size":
            payload_size,

            "payload_budget":
            payload_budget,

            "coverage_pressure":
            round(
                coverage_pressure,
                4
            ),

            "payload_pressure":
            round(
                payload_pressure,
                4
            ),

            "pressure":
            pressure,

            "state":
            (
                "saturated"
                if pressure >= 0.85
                else "active"
                if pressure >= 0.35
                else "underfilled"
            )
        }

    def build_architecture(
        self,
        context
    ):

        if not isinstance(
            context,
            dict
        ):

            context = {}

        layers = {
            layer_name:
            self.build_layer(
                context,
                layer_name,
                keys
            )
            for layer_name, keys in MEMORY_LAYER_KEYS.items()
        }

        layer_pressures = [
            layer.get(
                "pressure",
                0.0
            )
            for layer in layers.values()
        ]

        combined_pressure = 0.0

        if layer_pressures:

            combined_pressure = round(
                sum(layer_pressures)
                /
                len(layer_pressures),
                4
            )

        routing_policy = {
            "working_memory":
            "protect_current_task",

            "semantic_memory":
            "compress_by_concept_identity",

            "episodic_memory":
            "retain_recent_success_failure_pairs",

            "ontology_memory":
            "preserve_multi_resolution_identity",

            "immune_memory":
            "penalize_repeated_collapse_sources",

            "latent_memory":
            "reactivate_on_failure_or_uncertainty"
        }

        report = {
            "architecture":
            "hierarchical_memory",

            "layers":
            layers,

            "combined_memory_pressure":
            combined_pressure,

            "routing_policy":
            routing_policy,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.architecture_history.append(
            report
        )

        self.architecture_history = (
            self.architecture_history[-32:]
        )

        return report

    def build_report(self):

        latest = (
            self.architecture_history[-1]
            if self.architecture_history
            else {}
        )

        return {
            "architecture_cycles":
            len(
                self.architecture_history
            ),

            "latest_combined_pressure":
            latest.get(
                "combined_memory_pressure",
                0.0
            ),

            "latest_layers":
            list(
                latest.get(
                    "layers",
                    {}
                ).keys()
            )
        }


hierarchical_memory_architecture = (
    HierarchicalMemoryArchitecture()
)
