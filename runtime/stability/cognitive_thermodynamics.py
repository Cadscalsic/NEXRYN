# ============================================
# NEXRYN COGNITIVE THERMODYNAMICS
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


def _runtime_entropy(context):

    entropy_report = context.get(
        "cognitive_entropy_report",
        {}
    )

    return _clamp(
        entropy_report.get(
            "runtime_entropy",
            context.get(
                "runtime_entropy",
                0.0
            )
        )
    )


class EntropyFieldEngine:

    def __init__(self):

        self.field_history = []

    def map_fields(self, context):

        entropy = _runtime_entropy(
            context
        )

        routing = context.get(
            "predictive_attention_routing_v2_report",
            {}
        )

        fabric = context.get(
            "distributed_semantic_execution_fabric_report",
            {}
        )

        fabric_entropy = fabric.get(
            "entropy_field_regulator",
            {}
        )

        semantic = context.get(
            "semantic_distance_fields_report",
            {}
        )

        concepts = context.get(
            "dynamic_cognitive_swapping_report",
            {}
        )

        routes = _as_list(
            routing.get(
                "rebuilt_routes",
                []
            )
        )

        field = {
            "global_entropy":
            entropy,

            "route_entropy":
            _clamp(
                sum(
                    route.get(
                        "entropy_delta_after",
                        route.get(
                            "entropy_delta_before",
                            0.0
                        )
                    )
                    for route in routes
                )
                /
                max(
                    len(
                        routes
                    ),
                    1
                )
            ),

            "semantic_merge_heat":
            _clamp(
                semantic.get(
                    "average_merge_risk",
                    0.0
                )
            ),

            "concept_pressure":
            _clamp(
                concepts.get(
                    "observed_concept_count",
                    0
                )
                /
                24
            ),

            "thread_heat":
            _clamp(
                fabric_entropy.get(
                    "semantic_heat_after",
                    fabric_entropy.get(
                        "semantic_heat_before",
                        0.0
                    )
                )
            ),
        }

        total_heat = _clamp(
            field["global_entropy"] * 0.35
            +
            field["route_entropy"] * 0.20
            +
            field["semantic_merge_heat"] * 0.15
            +
            field["concept_pressure"] * 0.15
            +
            field["thread_heat"] * 0.15
        )

        report = {
            "system":
            "entropy_field_engine",

            "entropy_fields":
            field,

            "total_semantic_heat":
            total_heat,

            "explosion_risk":
            (
                "critical"
                if total_heat >= 0.78
                else "high"
                if total_heat >= 0.62
                else "contained"
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


class SemanticCoolingSystem:

    def __init__(self):

        self.cooling_history = []

    def cool(self, context, entropy_field_report):

        heat = entropy_field_report.get(
            "total_semantic_heat",
            0.0
        )

        swapping = context.get(
            "dynamic_cognitive_swapping_report",
            {}
        )

        cooling_strength = (
            0.38
            if heat >= 0.78
            else 0.24
            if heat >= 0.62
            else 0.10
        )

        cooled_concepts = [
            item.get(
                "concept"
            )
            for item in swapping.get(
                "latent_concepts",
                []
            )[:12]
        ]

        report = {
            "system":
            "semantic_cooling_system",

            "cooling_strength":
            cooling_strength,

            "semantic_heat_before":
            heat,

            "semantic_heat_after":
            _clamp(
                heat
                -
                cooling_strength
            ),

            "cooled_concepts":
            cooled_concepts,

            "cooling_actions":
            (
                [
                    "freeze_nonessential_combinations",
                    "page_hot_concepts_to_latent",
                    "prefer_compiled_macros",
                    "suppress_branch_duplication",
                ]
                if heat >= 0.78
                else [
                    "page_background_concepts",
                    "prefer_compiled_macros",
                ]
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.cooling_history.append(
            report
        )

        self.cooling_history = (
            self.cooling_history[-32:]
        )

        return report


class AttentionEconomics:

    def __init__(self):

        self.economy_history = []

    def allocate(self, context, cooling_report):

        heat_after = cooling_report.get(
            "semantic_heat_after",
            0.0
        )

        attention = context.get(
            "hierarchical_attention_collapse_report",
            {}
        )

        saturation = attention.get(
            "attention_saturation_after",
            context.get(
                "dynamic_attention_allocation",
                {}
            ).get(
                "attention_saturation",
                0.0
            )
        )

        attention_tax = _clamp(
            saturation * 0.45
            +
            heat_after * 0.55
        )

        report = {
            "system":
            "attention_economics",

            "attention_tax":
            attention_tax,

            "attention_budget":
            {
                "apex_focus":
                _clamp(
                    0.50
                    -
                    attention_tax * 0.12
                ),

                "compiled_macro_execution":
                _clamp(
                    0.28
                    +
                    attention_tax * 0.18
                ),

                "exploration":
                _clamp(
                    0.16
                    -
                    attention_tax * 0.10
                ),

                "background_threads":
                _clamp(
                    0.06
                    -
                    attention_tax * 0.04
                ),
            },

            "market_policy":
            (
                "tax_hot_attention"
                if attention_tax >= 0.50
                else "balanced_attention_market"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.economy_history.append(
            report
        )

        self.economy_history = (
            self.economy_history[-32:]
        )

        return report


class CognitiveEnergyRouter:

    def __init__(self):

        self.routing_history = []

    def route(self, context, attention_report, cooling_report):

        budget = attention_report.get(
            "attention_budget",
            {}
        )

        market = context.get(
            "recursive_budget_market_report",
            {}
        )

        allocations = []

        for item in market.get(
            "allocations",
            []
        ):

            heat_penalty = cooling_report.get(
                "semantic_heat_after",
                0.0
            ) * item.get(
                "cognitive_energy_cost",
                0.0
            )

            routed_energy = _clamp(
                item.get(
                    "expected_utility",
                    0.0
                )
                -
                heat_penalty
                +
                budget.get(
                    "compiled_macro_execution",
                    0.0
                )
                * 0.25
            )

            allocations.append({
                "target":
                item.get(
                    "hypothesis"
                ),

                "routed_energy":
                routed_energy,

                "heat_penalty":
                _clamp(
                    heat_penalty
                ),

                "routing_policy":
                (
                    "execute_compiled"
                    if routed_energy >= 0.50
                    else "latent_defer"
                ),
            })

        report = {
            "system":
            "cognitive_energy_router",

            "energy_routing_mode":
            "heat_aware_cognitive_routing",

            "allocations":
            sorted(
                allocations,
                key=lambda item: item.get(
                    "routed_energy",
                    0.0
                ),
                reverse=True
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


class SemanticHeatDissipation:

    def __init__(self):

        self.dissipation_history = []

    def dissipate(
        self,
        entropy_field_report,
        cooling_report,
        attention_report,
        energy_report
    ):

        heat_before = entropy_field_report.get(
            "total_semantic_heat",
            0.0
        )

        routed_energy = sum(
            item.get(
                "routed_energy",
                0.0
            )
            for item in energy_report.get(
                "allocations",
                []
            )[:4]
        )

        dissipation = _clamp(
            cooling_report.get(
                "cooling_strength",
                0.0
            )
            +
            attention_report.get(
                "attention_budget",
                {}
            ).get(
                "compiled_macro_execution",
                0.0
            )
            * 0.20
            +
            routed_energy / 16
        )

        heat_after = _clamp(
            heat_before
            -
            dissipation
        )

        report = {
            "system":
            "semantic_heat_dissipation",

            "semantic_heat_before":
            heat_before,

            "semantic_heat_after":
            heat_after,

            "dissipation":
            dissipation,

            "cognitive_equilibrium":
            _clamp(
                1.0
                -
                heat_after
            ),

            "thermodynamic_state":
            (
                "cooled"
                if heat_after < 0.62
                else "critical"
                if heat_after >= 0.78
                else "hot_but_regulated"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.dissipation_history.append(
            report
        )

        self.dissipation_history = (
            self.dissipation_history[-32:]
        )

        return report


class CognitiveThermodynamics:

    def __init__(self):

        self.entropy_field_engine = (
            EntropyFieldEngine()
        )

        self.semantic_cooling_system = (
            SemanticCoolingSystem()
        )

        self.attention_economics = (
            AttentionEconomics()
        )

        self.cognitive_energy_router = (
            CognitiveEnergyRouter()
        )

        self.semantic_heat_dissipation = (
            SemanticHeatDissipation()
        )

        self.thermodynamic_history = []

    def run_cycle(self, runtime_context):

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        entropy_field_report = (
            self.entropy_field_engine
            .map_fields(runtime_context)
        )

        cooling_report = (
            self.semantic_cooling_system
            .cool(
                runtime_context,
                entropy_field_report
            )
        )

        attention_report = (
            self.attention_economics
            .allocate(
                runtime_context,
                cooling_report
            )
        )

        energy_report = (
            self.cognitive_energy_router
            .route(
                runtime_context,
                attention_report,
                cooling_report
            )
        )

        dissipation_report = (
            self.semantic_heat_dissipation
            .dissipate(
                entropy_field_report,
                cooling_report,
                attention_report,
                energy_report
            )
        )

        report = {
            "phase":
            "Cognitive Thermodynamics",

            "entropy_field_engine":
            entropy_field_report,

            "semantic_cooling_system":
            cooling_report,

            "attention_economics":
            attention_report,

            "cognitive_energy_router":
            energy_report,

            "semantic_heat_dissipation":
            dissipation_report,

            "thermodynamic_state":
            dissipation_report.get(
                "thermodynamic_state"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        runtime_context[
            "entropy_field_engine_report"
        ] = entropy_field_report

        runtime_context[
            "semantic_cooling_system_report"
        ] = cooling_report

        runtime_context[
            "attention_economics_report"
        ] = attention_report

        runtime_context[
            "cognitive_energy_router_report"
        ] = energy_report

        runtime_context[
            "semantic_heat_dissipation_report"
        ] = dissipation_report

        runtime_context[
            "cognitive_thermodynamics_report"
        ] = report

        self.thermodynamic_history.append(
            report
        )

        self.thermodynamic_history = (
            self.thermodynamic_history[-32:]
        )

        return runtime_context


cognitive_thermodynamics = (
    CognitiveThermodynamics()
)
