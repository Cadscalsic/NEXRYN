# ============================================
# NEXRYN SEMANTIC ACTIVATION GRAPH
# ============================================

from datetime import datetime


class SemanticActivationGraph:

    def __init__(self):

        self.activation_state = {}
        self.activation_history = []

    def activate(self, concept, strength=1.0):

        if concept is None:

            return 0.0

        concept = str(
            concept
        )

        current = self.activation_state.get(
            concept,
            0.0
        )

        updated = min(
            current + strength,
            1.0
        )

        self.activation_state[
            concept
        ] = updated

        return updated

    def propagate(self, graph):

        nodes = graph.get(
            "concept_nodes",
            []
        )

        edges = graph.get(
            "relations",
            graph.get(
                "edges",
                []
            )
        )

        for node in nodes:

            if isinstance(
                node,
                dict
            ):

                self.activate(
                    node.get(
                        "concept"
                    ),
                    node.get(
                        "confidence",
                        0.5
                    )
                    * 0.25
                )

        for edge in edges:

            if not isinstance(
                edge,
                dict
            ):

                continue

            source = edge.get(
                "source"
            )

            target = edge.get(
                "target"
            )

            strength = edge.get(
                "edge_weight",
                edge.get(
                    "causal_strength",
                    0.25
                )
            )

            if self.activation_state.get(
                source,
                0.0
            ) > 0.25:

                self.activate(
                    target,
                    strength * 0.20
                )

    def decay(self, rate=0.08):

        for concept in list(
            self.activation_state.keys()
        ):

            self.activation_state[
                concept
            ] = max(
                self.activation_state[
                    concept
                ]
                -
                rate,
                0.0
            )

    def suppress(self, concept, amount=0.25):

        if concept in self.activation_state:

            self.activation_state[
                concept
            ] = max(
                self.activation_state[
                    concept
                ]
                -
                amount,
                0.0
            )

    def reinforce(self, concept, amount=0.20):

        return self.activate(
            concept,
            amount
        )

    def compute_temperature(self):

        values = list(
            self.activation_state.values()
        )

        if not values:

            return 0.0

        average = sum(
            values
        ) / len(
            values
        )

        spread = max(
            values
        ) - min(
            values
        )

        return round(
            min(
                average * 0.65
                +
                spread * 0.35,
                1.0
            ),
            4
        )

    def run_cycle(self, context):

        graph = context.get(
            "semantic_graph",
            {}
        )

        pointers = context.get(
            "semantic_pointer_report",
            {}
        )

        self.decay()

        self.propagate(
            graph
        )

        for pointer in pointers.get(
            "pointers",
            []
        ):

            self.reinforce(
                pointer.get(
                    "canonical_concept"
                ),
                min(
                    pointer.get(
                        "reference_count",
                        1
                    )
                    *
                    0.05,
                    0.25
                )
            )

        temperature = self.compute_temperature()

        report = {
            "graph":
            "semantic_activation",

            "activation_count":
            len(
                self.activation_state
            ),

            "top_activations":
            sorted(
                [
                    {
                        "concept":
                        concept,

                        "activation_strength":
                        round(
                            strength,
                            4
                        )
                    }
                    for concept, strength in self.activation_state.items()
                ],
                key=lambda item: item.get(
                    "activation_strength",
                    0.0
                ),
                reverse=True
            )[:12],

            "semantic_temperature":
            temperature,

            "attention_energy":
            round(
                min(
                    temperature * 0.70
                    +
                    len(
                        pointers.get(
                            "pointers",
                            []
                        )
                    )
                    /
                    40,
                    1.0
                ),
                4
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.activation_history.append(
            report
        )

        self.activation_history = (
            self.activation_history[-32:]
        )

        return report


semantic_activation_graph = (
    SemanticActivationGraph()
)
