# ============================================
# NEXRYN COGNITIVE OPERATING SYSTEM LAYER
# ============================================

from datetime import datetime


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


def _concept_name(item):

    if isinstance(
        item,
        dict
    ):

        return str(
            item.get(
                "concept",
                item.get(
                    "canonical_concept",
                    item.get(
                        "semantic_concept",
                        item.get(
                            "route",
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


def _entropy(context):

    entropy_report = context.get(
        "cognitive_entropy_report",
        {}
    )

    return _clamp(
        entropy_report.get(
            "runtime_entropy",
            context.get(
                "runtime_entropy",
                context.get(
                    "projected_entropy",
                    0.0
                )
            )
        )
        /
        (
            12
            if context.get(
                "projected_entropy",
                0.0
            )
            > 1
            and not entropy_report.get(
                "runtime_entropy"
            )
            else 1
        )
    )


class DynamicCognitiveSwapping:

    def __init__(self):

        self.swap_history = []

    def collect_concepts(self, context):

        concepts = []

        decay_report = context.get(
            "active_concept_decay_report",
            {}
        )

        concepts.extend(
            decay_report.get(
                "activation_state",
                []
            )
        )

        activation_report = context.get(
            "semantic_activation_report",
            {}
        )

        concepts.extend(
            activation_report.get(
                "top_activations",
                []
            )
        )

        pointer_report = context.get(
            "semantic_pointer_report",
            {}
        )

        concepts.extend(
            pointer_report.get(
                "pointers",
                []
            )
        )

        ordered = {}

        for item in concepts:

            concept = _concept_name(
                item
            )

            if concept == "unknown":

                continue

            score = 0.20

            if isinstance(
                item,
                dict
            ):

                score = max(
                    item.get(
                        "activation_strength",
                        0.0
                    ),
                    item.get(
                        "reference_count",
                        0
                    )
                    / 10,
                    score
                )

            ordered[concept] = max(
                ordered.get(
                    concept,
                    0.0
                ),
                _clamp(
                    score
                )
            )

        return [
            {
                "concept":
                concept,

                "demand_score":
                score,
            }
            for concept, score in sorted(
                ordered.items(),
                key=lambda item: item[1],
                reverse=True
            )
        ]

    def swap(self, context):

        concepts = self.collect_concepts(
            context
        )

        entropy = _entropy(
            context
        )

        active_limit = (
            5
            if entropy >= 0.80
            else 7
            if entropy >= 0.55
            else 9
        )

        loaded = concepts[:active_limit]
        latent = concepts[active_limit:active_limit + 24]
        paged_out = concepts[active_limit + 24:]

        report = {
            "system":
            "dynamic_cognitive_swapping",

            "virtual_cognition_paging":
            True,

            "active_limit":
            active_limit,

            "loaded_concepts":
            loaded,

            "latent_concepts":
            latent,

            "paged_out_concepts":
            paged_out,

            "loaded_concept_count":
            len(
                loaded
            ),

            "observed_concept_count":
            len(
                concepts
            ),

            "swap_policy":
            (
                "critical_demand_loading"
                if entropy >= 0.80
                else "demand_loading"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.swap_history.append(
            report
        )

        self.swap_history = (
            self.swap_history[-32:]
        )

        return report


class PredictiveAttentionRoutingV2:

    def __init__(self):

        self.routing_history = []

    def compress_route(self, route):

        route_name = str(
            route.get(
                "route",
                "unknown_route"
            )
        )

        parts = [
            part
            for part in route_name
            .replace(
                ":",
                "_"
            )
            .split(
                "_"
            )
            if part
        ]

        return "_".join(
            parts[:3]
        ) or "compressed_route"

    def reroute(self, context, swapping_report):

        routing_report = context.get(
            "cognitive_predictive_routing_report",
            {}
        )

        routes = _as_list(
            routing_report.get(
                "routes",
                []
            )
        )

        if not routes:

            routes = [
                {
                    "route":
                    "default_reasoning_route",

                    "collapse_risk":
                    _entropy(
                        context
                    ),

                    "route_policy":
                    "allow",
                }
            ]

        loaded_names = {
            item.get(
                "concept"
            )
            for item in swapping_report.get(
                "loaded_concepts",
                []
            )
        }

        rebuilt_routes = []

        for route in routes:

            policy = route.get(
                "route_policy",
                "allow"
            )

            compressed = self.compress_route(
                route
            )

            alternate = {
                "original_route":
                route.get(
                    "route"
                ),

                "route_policy_before":
                policy,

                "alternate_route":
                (
                    "low_entropy_"
                    + compressed
                ),

                "uses_loaded_concepts":
                sorted(
                    loaded_names
                )[:6],

                "entropy_delta_before":
                route.get(
                    "entropy_delta",
                    route.get(
                        "collapse_risk",
                        0.0
                    )
                ),

                "entropy_delta_after":
                _clamp(
                    route.get(
                        "entropy_delta",
                        route.get(
                            "collapse_risk",
                            0.0
                        )
                    )
                    * 0.52
                ),

                "collapse_risk_after":
                _clamp(
                    route.get(
                        "collapse_risk",
                        0.0
                    )
                    * 0.48
                ),

                "recursion_compression":
                (
                    "aggressive"
                    if policy == "block"
                    else "moderate"
                    if policy == "throttle"
                    else "light"
                ),

                "route_policy_after":
                (
                    "reroute"
                    if policy in [
                        "block",
                        "throttle",
                    ]
                    else "allow"
                ),
            }

            rebuilt_routes.append(
                alternate
            )

        report = {
            "system":
            "predictive_attention_routing_v2",

            "reroute_cognition":
            True,

            "rebuilt_routes":
            rebuilt_routes,

            "alternate_low_entropy_paths":
            [
                item
                for item in rebuilt_routes
                if item.get(
                    "route_policy_after"
                )
                == "reroute"
            ],

            "dynamic_recursion_compression":
            [
                {
                    "route":
                    item.get(
                        "alternate_route"
                    ),

                    "compression":
                    item.get(
                        "recursion_compression"
                    ),
                }
                for item in rebuilt_routes
            ],

            "routing_state":
            (
                "rerouted"
                if any(
                    item.get(
                        "route_policy_after"
                    )
                    == "reroute"
                    for item in rebuilt_routes
                )
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


class RecursiveBudgetMarket:

    def __init__(self):

        self.market_history = []

    def collect_hypotheses(self, context, routing_report):

        hypotheses = []

        for item in _as_list(
            context.get(
                "reasoning_hypotheses",
                []
            )
        ):

            hypotheses.append(
                item
            )

        if not hypotheses:

            for route in routing_report.get(
                "rebuilt_routes",
                []
            ):

                hypotheses.append({
                    "type":
                    route.get(
                        "alternate_route"
                    ),

                    "confidence":
                    1.0
                    -
                    route.get(
                        "collapse_risk_after",
                        0.0
                    ),
                })

        return hypotheses[:24]

    def score_bid(self, hypothesis, context):

        if isinstance(
            hypothesis,
            dict
        ):

            name = str(
                hypothesis.get(
                    "type",
                    hypothesis.get(
                        "hypothesis",
                        hypothesis.get(
                            "route",
                            "hypothesis"
                        )
                    )
                )
            )

            confidence = hypothesis.get(
                "confidence",
                0.5
            )

        else:

            name = str(
                hypothesis
            )

            confidence = 0.5

        entropy = _entropy(
            context
        )

        complexity = _clamp(
            len(
                [
                    part
                    for part in name.split(
                        "_"
                    )
                    if part
                ]
            )
            / 10
        )

        cost = _clamp(
            0.18
            +
            complexity * 0.42
            +
            entropy * 0.25
        )

        utility = _clamp(
            confidence * 0.55
            +
            (1.0 - entropy) * 0.20
            +
            (1.0 - complexity) * 0.25
        )

        bid = _clamp(
            utility
            -
            cost * 0.45
        )

        return {
            "hypothesis":
            name,

            "confidence":
            _clamp(
                confidence
            ),

            "cognitive_energy_cost":
            cost,

            "expected_utility":
            utility,

            "market_bid":
            bid,
        }

    def allocate(self, context, routing_report):

        bids = [
            self.score_bid(
                hypothesis,
                context
            )
            for hypothesis in self.collect_hypotheses(
                context,
                routing_report
            )
        ]

        ranked = sorted(
            bids,
            key=lambda item: item.get(
                "market_bid",
                0.0
            ),
            reverse=True
        )

        base_budget = (
            7
            if _entropy(
                context
            ) >= 0.80
            else 10
        )

        allocations = []
        remaining = base_budget

        for index, bid in enumerate(
            ranked
        ):

            requested = max(
                1,
                int(
                    round(
                        bid.get(
                            "expected_utility",
                            0.0
                        )
                        * 4
                    )
                )
            )

            granted = (
                min(
                    requested + 1,
                    remaining
                )
                if index == 0
                else min(
                    requested,
                    remaining
                )
            )

            if granted <= 0:

                break

            remaining -= granted

            allocation = dict(
                bid
            )

            allocation[
                "recursion_budget_granted"
            ] = granted

            allocation[
                "market_rank"
            ] = index + 1

            allocations.append(
                allocation
            )

        report = {
            "system":
            "recursive_budget_market",

            "market_mode":
            "cognitive_energy_auction",

            "base_recursion_budget":
            base_budget,

            "remaining_budget":
            remaining,

            "bids":
            ranked,

            "allocations":
            allocations,

            "winner":
            (
                allocations[0]
                if allocations
                else {}
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.market_history.append(
            report
        )

        self.market_history = (
            self.market_history[-32:]
        )

        return report


class CognitiveOperatingSystemLayer:

    def __init__(self):

        self.dynamic_cognitive_swapping = (
            DynamicCognitiveSwapping()
        )

        self.predictive_attention_routing_v2 = (
            PredictiveAttentionRoutingV2()
        )

        self.recursive_budget_market = (
            RecursiveBudgetMarket()
        )

        self.os_history = []

    def run_cycle(self, runtime_context):

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        swapping_report = (
            self.dynamic_cognitive_swapping
            .swap(runtime_context)
        )

        routing_v2_report = (
            self.predictive_attention_routing_v2
            .reroute(
                runtime_context,
                swapping_report
            )
        )

        budget_market_report = (
            self.recursive_budget_market
            .allocate(
                runtime_context,
                routing_v2_report
            )
        )

        report = {
            "phase":
            "Cognitive Operating System Layer",

            "dynamic_cognitive_swapping":
            swapping_report,

            "predictive_attention_routing_v2":
            routing_v2_report,

            "recursive_budget_market":
            budget_market_report,

            "os_state":
            (
                "rerouted_market_control"
                if routing_v2_report.get(
                    "routing_state"
                )
                == "rerouted"
                else "demand_paged"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        runtime_context[
            "dynamic_cognitive_swapping_report"
        ] = swapping_report

        runtime_context[
            "predictive_attention_routing_v2_report"
        ] = routing_v2_report

        runtime_context[
            "recursive_budget_market_report"
        ] = budget_market_report

        runtime_context[
            "cognitive_operating_system_report"
        ] = report

        self.os_history.append(
            report
        )

        self.os_history = (
            self.os_history[-32:]
        )

        return runtime_context


cognitive_operating_system_layer = (
    CognitiveOperatingSystemLayer()
)
