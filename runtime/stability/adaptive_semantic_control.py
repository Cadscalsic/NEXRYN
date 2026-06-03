# ============================================
# NEXRYN ADAPTIVE SEMANTIC CONTROL
# ============================================

from datetime import datetime

from runtime.semantics.semantic_ontology import (
    compression_level_for_concept,
)


def _clamp(value, minimum=0.0, maximum=1.0):

    try:

        value = float(value)

    except Exception:

        value = minimum

    return round(
        max(
            minimum,
            min(
                value,
                maximum
            )
        ),
        4
    )


def _as_list(value):

    if isinstance(
        value,
        list
    ):

        return value

    if value is None:

        return []

    return [
        value
    ]


def _concept_from_item(item):

    if isinstance(
        item,
        dict
    ):

        return str(
            item.get(
                "canonical_concept",
                item.get(
                    "semantic_concept",
                    item.get(
                        "concept",
                        item.get(
                            "primitive",
                            item.get(
                                "type",
                                "unknown"
                            )
                        )
                    )
                )
            )
        )

    return str(
        item
    )


def _tokens(concept):

    return {
        token
        for token in str(
            concept
        )
        .lower()
        .replace(
            "-",
            "_"
        )
        .split(
            "_"
        )
        if token
    }


class SemanticDistanceFields:

    def __init__(self):

        self.field_history = []

    def causal_overlap(self, first, second):

        first_level = compression_level_for_concept(
            first
        )

        second_level = compression_level_for_concept(
            second
        )

        matches = 0

        for attribute in [
            "causal_identity",
            "structural_identity",
            "archetypal_identity",
            "topology_signature",
        ]:

            if getattr(
                first_level,
                attribute
            ) == getattr(
                second_level,
                attribute
            ):

                matches += 1

        return _clamp(
            matches / 4
        )

    def semantic_distance(self, first, second):

        first_tokens = _tokens(
            first
        )

        second_tokens = _tokens(
            second
        )

        if not first_tokens and not second_tokens:

            lexical_overlap = 0.0

        else:

            lexical_overlap = (
                len(
                    first_tokens.intersection(
                        second_tokens
                    )
                )
                /
                max(
                    len(
                        first_tokens.union(
                            second_tokens
                        )
                    ),
                    1
                )
            )

        causal = self.causal_overlap(
            first,
            second
        )

        distance = 1.0 - (
            lexical_overlap * 0.45
            +
            causal * 0.55
        )

        return {
            "first":
            first,

            "second":
            second,

            "semantic_distance":
            _clamp(
                distance
            ),

            "concept_proximity":
            _clamp(
                1.0 - distance
            ),

            "causal_overlap":
            causal,

            "merge_risk":
            _clamp(
                distance * 0.65
                +
                (1.0 - causal) * 0.35
            ),
        }

    def collect_concepts(self, context):

        pointer_report = context.get(
            "semantic_pointer_report",
            {}
        )

        pointers = pointer_report.get(
            "pointers",
            []
        )

        concepts = [
            _concept_from_item(
                item
            )
            for item in pointers
        ]

        activation_report = context.get(
            "semantic_activation_report",
            {}
        )

        concepts.extend([
            _concept_from_item(
                item
            )
            for item in activation_report.get(
                "top_activations",
                []
            )
        ])

        concepts.extend([
            _concept_from_item(
                item
            )
            for item in context.get(
                "semantic_abstractions",
                []
            )
        ])

        ordered = []
        seen = set()

        for concept in concepts:

            if concept in seen or concept == "unknown":

                continue

            seen.add(
                concept
            )

            ordered.append(
                concept
            )

        return ordered[:24]

    def build_field(self, context):

        concepts = self.collect_concepts(
            context
        )

        distances = []

        for index, first in enumerate(
            concepts
        ):

            for second in concepts[index + 1:]:

                distances.append(
                    self.semantic_distance(
                        first,
                        second
                    )
                )

        high_risk = [
            item
            for item in distances
            if item.get(
                "merge_risk",
                0.0
            ) >= 0.62
        ]

        report = {
            "system":
            "semantic_distance_fields",

            "concept_count":
            len(
                concepts
            ),

            "distance_count":
            len(
                distances
            ),

            "distances":
            distances[:96],

            "high_risk_merge_pairs":
            high_risk[:24],

            "average_merge_risk":
            _clamp(
                sum(
                    item.get(
                        "merge_risk",
                        0.0
                    )
                    for item in distances
                )
                /
                max(
                    len(
                        distances
                    ),
                    1
                )
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.field_history.append(
            report
        )

        self.field_history = (
            self.field_history[-32:]
        )

        return report


class AdaptiveSemanticCompression:

    def __init__(self):

        self.compression_history = []

    def fold_probability(self, distance_item):

        proximity = distance_item.get(
            "concept_proximity",
            0.0
        )

        causal = distance_item.get(
            "causal_overlap",
            0.0
        )

        risk = distance_item.get(
            "merge_risk",
            1.0
        )

        return _clamp(
            proximity * 0.45
            +
            causal * 0.40
            +
            (1.0 - risk) * 0.15
        )

    def build_fold_plan(self, distance_report):

        fold_plan = []
        aliases = []
        preserved = []

        for distance_item in distance_report.get(
            "distances",
            []
        ):

            probability = self.fold_probability(
                distance_item
            )

            item = dict(
                distance_item
            )

            item[
                "fold_probability"
            ] = probability

            if probability >= 0.72:

                item[
                    "fold_policy"
                ] = "probabilistic_fold"

                fold_plan.append(
                    item
                )

            elif probability >= 0.45:

                item[
                    "fold_policy"
                ] = "probabilistic_alias"

                aliases.append(
                    item
                )

            else:

                item[
                    "fold_policy"
                ] = "preserve_separation"

                preserved.append(
                    item
                )

        report = {
            "system":
            "adaptive_semantic_compression",

            "fold_candidates":
            fold_plan[:24],

            "alias_candidates":
            aliases[:24],

            "preserved_separations":
            preserved[:24],

            "compression_mode":
            "probabilistic_semantic_folding",

            "fold_count":
            len(
                fold_plan
            ),

            "alias_count":
            len(
                aliases
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.compression_history.append(
            report
        )

        self.compression_history = (
            self.compression_history[-32:]
        )

        return report


class ActiveConceptDecay:

    def __init__(self):

        self.activation_state = {}
        self.decay_history = []

    def run_decay(self, context):

        for concept in list(
            self.activation_state.keys()
        ):

            self.activation_state[
                concept
            ] = _clamp(
                self.activation_state[
                    concept
                ]
                - 0.12
            )

            if self.activation_state[
                concept
            ] <= 0.02:

                del self.activation_state[
                    concept
                ]

        activation_report = context.get(
            "semantic_activation_report",
            {}
        )

        reinforced = []

        for item in activation_report.get(
            "top_activations",
            []
        ):

            concept = _concept_from_item(
                item
            )

            strength = item.get(
                "activation_strength",
                0.0
            )

            self.activation_state[
                concept
            ] = _clamp(
                self.activation_state.get(
                    concept,
                    0.0
                )
                +
                strength * 0.35
            )

            reinforced.append(
                concept
            )

        inactive = [
            concept
            for concept, strength in self.activation_state.items()
            if strength < 0.20
        ]

        report = {
            "system":
            "active_concept_decay",

            "active_concept_count":
            len(
                self.activation_state
            ),

            "reinforced_concepts":
            reinforced[:24],

            "decay_candidates":
            inactive[:24],

            "activation_state":
            [
                {
                    "concept":
                    concept,

                    "activation_strength":
                    strength,
                }
                for concept, strength in sorted(
                    self.activation_state.items(),
                    key=lambda item: item[1],
                    reverse=True
                )[:32]
            ],

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.decay_history.append(
            report
        )

        self.decay_history = (
            self.decay_history[-32:]
        )

        return report


class HierarchicalAttentionCollapse:

    def __init__(self):

        self.collapse_history = []

    def build_pyramids(self, context):

        attention_report = context.get(
            "attention_kernel_report",
            {}
        )

        focus = attention_report.get(
            "focus_window",
            []
        )

        saturation = (
            context.get(
                "dynamic_attention_allocation",
                {}
            )
            .get(
                "attention_saturation",
                attention_report.get(
                    "entropy_regulation",
                    {}
                )
                .get(
                    "attention_entropy",
                    0.0
                )
            )
        )

        top = focus[:4]
        middle = focus[4:12]
        base = focus[12:24]

        report = {
            "system":
            "hierarchical_attention_collapse",

            "attention_saturation_before":
            _clamp(
                saturation
            ),

            "attention_saturation_after":
            _clamp(
                saturation * 0.58
            ),

            "nested_attention_pyramids":
            {
                "apex":
                top,

                "middle":
                middle,

                "base":
                base,
            },

            "energy_budget":
            {
                "apex":
                0.50,

                "middle":
                0.32,

                "base":
                0.18,
            },

            "collapse_policy":
            (
                "collapse_to_apex"
                if saturation >= 0.80
                else "tiered_attention"
                if saturation >= 0.50
                else "maintain_pyramid"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.collapse_history.append(
            report
        )

        self.collapse_history = (
            self.collapse_history[-32:]
        )

        return report


class CognitivePredictiveRouting:

    def __init__(self):

        self.routing_history = []

    def collect_routes(self, context):

        routes = []

        for key in [
            "recursive_paths",
            "reasoning_hypotheses",
            "candidate_routes",
        ]:

            for item in _as_list(
                context.get(
                    key,
                    []
                )
            ):

                routes.append({
                    "route":
                    _concept_from_item(
                        item
                    ),

                    "source":
                    key,
                })

        if not routes:

            routes.append({
                "route":
                "default_reasoning_route",

                "source":
                "fallback",
            })

        return routes[:32]

    def score_route(self, route, context):

        entropy_report = context.get(
            "cognitive_entropy_report",
            {}
        )

        entropy = entropy_report.get(
            "runtime_entropy",
            context.get(
                "projected_entropy",
                0.0
            )
        )

        if entropy > 1:

            entropy = entropy / 12

        context_pressure = _clamp(
            len(
                context
            )
            / 160
        )

        route_complexity = _clamp(
            len(
                _tokens(
                    route.get(
                        "route",
                        ""
                    )
                )
            )
            / 8
        )

        entropy_delta = _clamp(
            entropy * 0.45
            +
            context_pressure * 0.35
            +
            route_complexity * 0.20
        )

        collapse_risk = _clamp(
            entropy_delta * 0.70
            +
            context_pressure * 0.30
        )

        return {
            "route":
            route.get(
                "route"
            ),

            "source":
            route.get(
                "source"
            ),

            "entropy_delta":
            entropy_delta,

            "collapse_risk":
            collapse_risk,

            "route_policy":
            (
                "block"
                if collapse_risk >= 0.72
                else "throttle"
                if collapse_risk >= 0.32
                else "allow"
            ),
        }

    def route(self, context):

        scored_routes = [
            self.score_route(
                route,
                context
            )
            for route in self.collect_routes(
                context
            )
        ]

        blocked = [
            route
            for route in scored_routes
            if route.get(
                "route_policy"
            )
            == "block"
        ]

        throttled = [
            route
            for route in scored_routes
            if route.get(
                "route_policy"
            )
            == "throttle"
        ]

        report = {
            "system":
            "cognitive_predictive_routing",

            "routes":
            scored_routes,

            "blocked_routes":
            blocked,

            "throttled_routes":
            throttled,

            "routing_state":
            (
                "unsafe"
                if blocked
                else "guarded"
                if throttled
                else "clear"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.routing_history.append(
            report
        )

        self.routing_history = (
            self.routing_history[-32:]
        )

        return report


class AdaptiveSemanticControl:

    def __init__(self):

        self.semantic_distance_fields = (
            SemanticDistanceFields()
        )

        self.adaptive_semantic_compression = (
            AdaptiveSemanticCompression()
        )

        self.active_concept_decay = (
            ActiveConceptDecay()
        )

        self.hierarchical_attention_collapse = (
            HierarchicalAttentionCollapse()
        )

        self.cognitive_predictive_routing = (
            CognitivePredictiveRouting()
        )

        self.control_history = []

    def run_predictive_routing(self, runtime_context):

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        routing_report = (
            self.cognitive_predictive_routing
            .route(runtime_context)
        )

        runtime_context[
            "cognitive_predictive_routing_report"
        ] = routing_report

        return runtime_context

    def run_semantic_control(self, runtime_context):

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        distance_report = (
            self.semantic_distance_fields
            .build_field(runtime_context)
        )

        compression_report = (
            self.adaptive_semantic_compression
            .build_fold_plan(distance_report)
        )

        decay_report = (
            self.active_concept_decay
            .run_decay(runtime_context)
        )

        attention_report = (
            self.hierarchical_attention_collapse
            .build_pyramids(runtime_context)
        )

        routing_report = (
            self.cognitive_predictive_routing
            .route(runtime_context)
        )

        report = {
            "phase":
            "Adaptive Semantic Control",

            "adaptive_semantic_compression":
            compression_report,

            "semantic_distance_fields":
            distance_report,

            "active_concept_decay":
            decay_report,

            "hierarchical_attention_collapse":
            attention_report,

            "cognitive_predictive_routing":
            routing_report,

            "control_state":
            (
                "guarded"
                if routing_report.get(
                    "routing_state"
                )
                in [
                    "guarded",
                    "unsafe",
                ]
                or attention_report.get(
                    "attention_saturation_before",
                    0.0
                )
                >= 0.70
                else "stable"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        runtime_context[
            "semantic_distance_fields_report"
        ] = distance_report

        runtime_context[
            "adaptive_semantic_compression_report"
        ] = compression_report

        runtime_context[
            "active_concept_decay_report"
        ] = decay_report

        runtime_context[
            "hierarchical_attention_collapse_report"
        ] = attention_report

        runtime_context[
            "cognitive_predictive_routing_report"
        ] = routing_report

        runtime_context[
            "adaptive_semantic_control_report"
        ] = report

        self.control_history.append(
            report
        )

        self.control_history = (
            self.control_history[-32:]
        )

        return runtime_context


adaptive_semantic_control = (
    AdaptiveSemanticControl()
)
