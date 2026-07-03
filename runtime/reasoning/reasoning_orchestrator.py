# ============================================
# NEXRYN REASONING ORCHESTRATOR
# ============================================

from datetime import datetime

from runtime.meta.supervisor import meta_supervisor

# ============================================
# REASONING ENGINES
# ============================================

from runtime.reasoning.spatial_reasoning_engine import (

    spatial_reasoning_engine
)

from runtime.reasoning.spatial_abstraction_engine import (

    spatial_abstraction_engine
)

from runtime.reasoning.analogical_reasoning_engine import (

    analogical_reasoning_engine
)

from runtime.reasoning.causal_reasoning_engine import (

    causal_reasoning_engine
)

from runtime.reasoning.symbolic_reasoning_engine import (

    symbolic_reasoning_engine
)

from runtime.reasoning.recursive_reasoning_engine import (

    recursive_reasoning_engine
)

from runtime.reasoning.hypothesis_arbitration_engine import (

    hypothesis_arbitration_engine
)

from runtime.reasoning.cognitive_pressure_engine import (

    cognitive_pressure_engine
)

from runtime.reasoning.generalization import (

    generalization_engine
)

from runtime.reasoning.transformation_synthesis_engine import (

    transformation_synthesis_engine
)

from runtime.reasoning.color_mapping_engine import (

    color_mapping_engine
)

from runtime.dependency.dependency_activation_bridge import (

    dependency_activation_bridge
)

from runtime.process.process_context_runtime import (

    process_context_runtime
)

from runtime.causal.causal_context_runtime import (

    causal_context_runtime
)

from runtime.dynamic_concepts.dynamic_concept_runtime import (

    dynamic_concept_runtime
)


# ============================================
# REASONING ORCHESTRATOR
# ============================================

class ReasoningOrchestrator:

    def __init__(self):

        # ========================================
        # ORCHESTRATION STATE
        # ========================================

        self.orchestration_state = {

            "orchestration_mode":
            "adaptive_recursive_reasoning",

            "reasoning_routing":
            "enabled",

            "cognitive_balancing":
            "enabled",

            "recursive_coordination":
            "enabled",

            "semantic_reasoning":
            "enabled",

            "executive_alignment":
            "enabled",

            "overload_mitigation":
            "enabled",

            "orchestration_stability":
            "stable",

            "orchestration_cycles":
            0
        }

        # ========================================
        # REASONING HISTORY
        # ========================================

        self.reasoning_history = []

        # ========================================
        # ACTIVE REASONING PATHS
        # ========================================

        self.active_reasoning_paths = []

        # ========================================
        # LOAD HISTORY
        # ========================================

        self.load_history = []

        # ========================================
        # ROUTING HISTORY
        # ========================================

        self.routing_history = []

        # ========================================
        # EXECUTIVE SYNCHRONIZATION
        # ========================================

        self.executive_sync_history = []


                # ========================================
        # REASONING ENGINES
        # ========================================

        self.spatial_reasoner = (
            spatial_reasoning_engine
        )

        self.spatial_abstraction = (
            spatial_abstraction_engine
        )

        self.analogical_reasoner = (
            analogical_reasoning_engine
        )

        self.causal_reasoner = (
            causal_reasoning_engine
        )

        self.symbolic_reasoner = (
            symbolic_reasoning_engine
        )

        self.recursive_reasoner = (
            recursive_reasoning_engine
        )

        self.hypothesis_arbitrator = (
            hypothesis_arbitration_engine
        )

        self.cognitive_pressure = (
            cognitive_pressure_engine
        )

        self.generalization_engine = (
            generalization_engine
        )

        self.transformation_synthesis_engine = (
            transformation_synthesis_engine
        )

        self.color_mapping_engine = (
            color_mapping_engine
        )

        self.dependency_activation_bridge = (
            dependency_activation_bridge
        )

        self.process_context_runtime = (
            process_context_runtime
        )

        self.causal_context_runtime = (
            causal_context_runtime
        )

        self.dynamic_concept_runtime = (
            dynamic_concept_runtime
        )

    # ============================================
    # ANALYZE CONTEXT LOAD
    # ============================================

    def analyze_context_load(

        self,

        runtime_context
    ):

        context_size = len(
            runtime_context
        )

        if context_size < 80:

            load_state = "light"

        elif context_size < 140:

            load_state = "moderate"

        else:

            load_state = "heavy"

        overload_detected = (
            context_size > 160
        )

        load_report = {

            "context_size":
            context_size,

            "load_state":
            load_state,

            "overload_detected":
            overload_detected,

            "analysis_mode":
            "recursive_context_analysis",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.load_history.append(
            load_report
        )

        return load_report

    # ============================================
    # BUILD REASONING ROUTES
    # ============================================

    def build_reasoning_routes(

        self,

        runtime_context
    ):

        reasoning_routes = []

        route_candidates = [

            "recursive_report",
            "inference_report",
            "transformation_report",
            "validation_report",
            "memory_report",
            "goal_report",
            "planner_report",
            "governance_report",
            "research_report",
            "consciousness_report"
        ]

        for route in route_candidates:

            if route in runtime_context:

                reasoning_routes.append({

                    "route":
                    route,

                    "priority":
                    "high",

                    "state":
                    "active"
                })

        pre_budget_route_count = len(
            reasoning_routes
        )

        active_budget = runtime_context.get(
            "current_reasoning_budget"
        )

        max_active_routes = getattr(
            active_budget,
            "max_active_routes",
            None
        )

        if max_active_routes is not None:

            reasoning_routes = reasoning_routes[
                :max(
                    1,
                    int(max_active_routes)
                )
            ]

        routing_report = {

            "routes":
            reasoning_routes,

            "route_count":

            len(
                reasoning_routes
            ),

            "pre_budget_route_count":
            pre_budget_route_count,

            "max_active_routes":
            max_active_routes,

            "routing_mode":
            "semantic_reasoning_routing",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.routing_history.append(
            routing_report
        )

        return routing_report

    # ============================================
    # BALANCE REASONING LOAD
    # ============================================

    def balance_reasoning_load(

        self,

        load_report
    ):

        overload_detected = (
            load_report.get(
                "overload_detected",
                False
            )
        )

        if overload_detected:

            balancing_strategy = {

                "strategy":
                "adaptive_load_suppression",

                "actions": [

                    "reduce_noncritical_contexts",

                    "freeze_low_priority_routes",

                    "prioritize_inference_paths",

                    "compress_recursive_memory"
                ],

                "state":
                "mitigation_active"
            }

        else:

            balancing_strategy = {

                "strategy":
                "stable_recursive_distribution",

                "actions": [

                    "maintain_active_reasoning",

                    "preserve_semantic_routes"
                ],

                "state":
                "stable"
            }

        return balancing_strategy

    # ============================================
    # SYNCHRONIZE EXECUTIVE STATE
    # ============================================

    def synchronize_executive_state(

        self,

        runtime_context
    ):

        executive_report = runtime_context.get(

            "executive_brain_report",
            {}
        )

        executive_summary = (

            executive_report.get(
                "executive_summary",
                {}
            )
        )

        synchronization = {

            "executive_alignment":
            "synchronized",

            "attention_focus":

            executive_summary.get(
                "attention_focus",
                "unknown"
            ),

            "runtime_health":

            executive_summary.get(
                "runtime_health",
                "unknown"
            ),

            "execution_load":

            executive_summary.get(
                "execution_load",
                0
            ),

            "sync_mode":
            "executive_reasoning_alignment",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.executive_sync_history.append(
            synchronization
        )

        return synchronization

    # ============================================
    # BUILD REASONING GRAPH
    # ============================================

    def build_reasoning_graph(

        self,

        routing_report
    ):

        routes = routing_report.get(
            "routes",
            []
        )

        nodes = []
        edges = []

        for index, route in enumerate(
            routes
        ):

            nodes.append({

                "node_id":
                index,

                "reasoning":
                route.get(
                    "route"
                ),

                "state":
                "active"
            })

        for index in range(

            len(nodes) - 1
        ):

            edges.append({

                "source":
                index,

                "target":
                index + 1,

                "relation":
                "reasoning_transition"
            })

        reasoning_graph = {

            "node_count":
            len(nodes),

            "edge_count":
            len(edges),

            "nodes":
            nodes,

            "edges":
            edges,

            "graph_mode":
            "recursive_reasoning_graph",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        return reasoning_graph

    # ============================================
    # BUILD ORCHESTRATION SUMMARY
    # ============================================

    def build_orchestration_summary(

        self,

        load_report,

        routing_report,

        balancing_strategy
    ):

        summary = {

            "load_state":

            load_report.get(
                "load_state"
            ),

            "overload_detected":

            load_report.get(
                "overload_detected"
            ),

            "active_routes":

            routing_report.get(
                "route_count",
                0
            ),

            "balancing_strategy":

            balancing_strategy.get(
                "strategy"
            ),

            "orchestration_state":
            "stable",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        return summary

    # ============================================
    # RUN ORCHESTRATION CYCLE
    # ============================================

    def run_orchestration_cycle(

        self,

        runtime_context
    ):

        if not meta_supervisor.is_action_allowed("reasoning"):
            return {
                "system": "reasoning_orchestrator",
                "status": "blocked_by_meta_supervisor",
                "reasoning_invoked": False,
                "reasoning_depth": 0,
                "active_routes": 0,
                "routes": [],
                "timestamp": str(datetime.utcnow()),
            }

        # ========================================
        # ANALYZE LOAD
        # ========================================

        load_report = (

            self.analyze_context_load(

                runtime_context
            )
        )

        # ========================================
        # BUILD ROUTES
        # ========================================

        routing_report = (

            self.build_reasoning_routes(

                runtime_context
            )
        )

        # ========================================
        # BALANCE LOAD
        # ========================================

        balancing_strategy = (

            self.balance_reasoning_load(

                load_report
            )
        )

        # ========================================
        # EXECUTIVE SYNCHRONIZATION
        # ========================================

        executive_sync = (

            self.synchronize_executive_state(

                runtime_context
            )
        )

        # ========================================
        # BUILD REASONING GRAPH
        # ========================================

        reasoning_graph = (

            self.build_reasoning_graph(

                routing_report
            )
        )

                # ========================================
        # COGNITIVE PRESSURE ANALYSIS
        # ========================================

        pressure_report = (

            self.cognitive_pressure
            .analyze_pressure(

                runtime_context
            )
        )

        # ========================================
        # SPATIAL REASONING
        # ========================================

        spatial_reasoning_report = {}

        spatial_abstraction_report = {}

        input_grid = runtime_context.get(
            "input_grid"
        )

        output_grid = runtime_context.get(
            "output_grid"
        )

        if input_grid is not None and (
            output_grid is not None
        ):

            spatial_hypotheses = (

                self.spatial_reasoner
                .build_spatial_hypotheses(

                    input_grid,

                    output_grid
                )
            )

            spatial_reasoning_report = {

                "hypothesis_count":

                len(
                    spatial_hypotheses
                ),

                "hypotheses":
                spatial_hypotheses
            }

            # ====================================
            # SPATIAL ABSTRACTION
            # ====================================

            spatial_abstraction_report = (

                self.spatial_abstraction
                .build_spatial_abstractions(

                    spatial_hypotheses
                )
            )

        # ========================================
        # ANALOGICAL REASONING
        # ========================================

        task_signature = runtime_context.get(

            "task_signature",

            {}
        )

        analogical_report = (

            self.analogical_reasoner
            .find_similar_experiences(

                task_signature
            )
        )

        transfer_insight = (

            self.analogical_reasoner
            .build_transfer_insight(

                analogical_report
            )
        )

        # ========================================
        # SYMBOLIC REASONING
        # ========================================

        symbolic_report = {}

        if spatial_reasoning_report:

            symbolic_report = (

                self.symbolic_reasoner
                .build_symbolic_report(

                    spatial_reasoning_report.get(

                        "hypotheses",

                        []
                    )
                )
            )

        # ========================================
        # CAUSAL REASONING
        # ========================================

        causal_report = {}

        if spatial_reasoning_report:

            causal_report = (

                self.causal_reasoner
                .build_causal_report(

                    spatial_reasoning_report.get(

                        "hypotheses",

                        []
                    )
                )
            )

        # ========================================
        # ARC GENERALIZATION
        # ========================================

        generalization_report = (
            self.generalization_engine
            .run_cycle(
                runtime_context,
                symbolic_report,
                causal_report,
                analogical_report,
                transfer_insight,
                spatial_reasoning_report,
            )
        )

        # ========================================
        # DEPENDENCY ACTIVATION
        # ========================================

        dependency_activation_report = (
            self.dependency_activation_bridge
            .activate(
                detected_concepts=self._collect_dependency_concepts(
                    runtime_context,
                    spatial_reasoning_report,
                    symbolic_report,
                    causal_report,
                    generalization_report,
                ),
                selected_tools=self._selected_runtime_tools(
                    runtime_context
                ),
                runtime_context={
                    **runtime_context,
                    "spatial_reasoning_report": spatial_reasoning_report,
                    "symbolic_report": symbolic_report,
                    "causal_report": causal_report,
                    "generalization_report": generalization_report,
                },
            )
        )

        # ========================================
        # PROCESS CONTEXT RUNTIME
        # ========================================

        process_context_runtime_report = (
            self.process_context_runtime
            .run(
                input_grid=input_grid,
                output_grid=output_grid,
                detected_concepts=dependency_activation_report.get(
                    "detected_concepts",
                    [],
                ),
                dependency_activation_report=dependency_activation_report,
                runtime_context={
                    **runtime_context,
                    "spatial_reasoning_report": spatial_reasoning_report,
                    "symbolic_report": symbolic_report,
                    "causal_report": causal_report,
                    "generalization_report": generalization_report,
                },
            )
        )

        # ========================================
        # COLOR MAPPING REASONING
        # ========================================

        color_mapping_report = {}

        if input_grid is not None and (
            output_grid is not None
        ):

            color_mapping_report = (
                self.color_mapping_engine
                .analyze(
                    input_grid=input_grid,
                    output_grid=output_grid,
                    concept_report={
                        "symbolic_report": symbolic_report,
                        "causal_report": causal_report,
                        "generalization_report": generalization_report,
                    },
                    runtime_context=runtime_context,
                )
            )

        # ========================================
        # TRANSFORMATION SYNTHESIS
        # ========================================

        transformation_synthesis_report = (
            self.transformation_synthesis_engine
            .synthesize(
                input_grid=input_grid,
                output_grid=output_grid,
                concept_report={
                    "spatial_reasoning_report": spatial_reasoning_report,
                    "symbolic_report": symbolic_report,
                    "causal_report": causal_report,
                    "generalization_report": generalization_report,
                    "color_mapping_report": color_mapping_report,
                },
                semantic_context_report=runtime_context.get(
                    "semantic_context_report",
                    {},
                ),
                reasoning_reports=[
                    spatial_reasoning_report,
                    symbolic_report,
                    causal_report,
                    generalization_report,
                    color_mapping_report,
                ],
                runtime_context=runtime_context,
            )
        )

        # ========================================
        # CAUSAL CONTEXT RUNTIME
        # ========================================

        causal_context_runtime_report = (
            self.causal_context_runtime
            .run(
                input_grid=input_grid,
                output_grid=output_grid,
                process_context_report=process_context_runtime_report,
                dependency_activation_report=dependency_activation_report,
                transformation_report=transformation_synthesis_report,
                color_mapping_report=color_mapping_report,
                runtime_context={
                    **runtime_context,
                    "spatial_reasoning_report": spatial_reasoning_report,
                    "symbolic_report": symbolic_report,
                    "causal_report": causal_report,
                    "generalization_report": generalization_report,
                },
            )
        )

        # ========================================
        # DYNAMIC ARC CONCEPTS RUNTIME
        # ========================================

        dynamic_concept_runtime_report = (
            self.dynamic_concept_runtime
            .run(
                input_grid=input_grid,
                output_grid=output_grid,
                detected_concepts=dependency_activation_report.get(
                    "detected_concepts",
                    [],
                ),
                dependency_activation_report=dependency_activation_report,
                process_context_report=process_context_runtime_report,
                causal_context_report=causal_context_runtime_report,
                transformation_report=transformation_synthesis_report,
                runtime_context={
                    **runtime_context,
                    "spatial_reasoning_report": spatial_reasoning_report,
                    "symbolic_report": symbolic_report,
                    "causal_report": causal_report,
                    "generalization_report": generalization_report,
                },
            )
        )

        # ========================================
        # RECURSIVE REASONING
        # ========================================

        recursive_report = {}

        if spatial_reasoning_report:

            recursive_report = (

                self.recursive_reasoner
                .build_recursive_report(

                    spatial_reasoning_report.get(

                        "hypotheses",

                        []
                    )
                )
            )

        # ========================================
        # HYPOTHESIS ARBITRATION
        # ========================================

        arbitration_report = {}

        if spatial_reasoning_report:

            arbitration_report = (

                self.hypothesis_arbitrator
                .build_arbitration_report(

                    spatial_reasoning_report.get(

                        "hypotheses",

                        []
                    )
                )
            )

        # ========================================
        # BUILD SUMMARY
        # ========================================

        orchestration_summary = (

            self.build_orchestration_summary(

                load_report,

                routing_report,

                balancing_strategy
            )
        )

        # ========================================
        # BUILD REPORT
        # ========================================

        report = {

            "load_report":
            load_report,

            "routing_report":
            routing_report,

            "balancing_strategy":
            balancing_strategy,

            "executive_sync":
            executive_sync,

            "reasoning_graph":
            reasoning_graph,

            # ====================================
            # COGNITIVE PRESSURE
            # ====================================

            "pressure_report":
            pressure_report,

            # ====================================
            # SPATIAL REASONING
            # ====================================

            "spatial_reasoning_report":
            spatial_reasoning_report,

            # ====================================
            # SPATIAL ABSTRACTION
            # ====================================

            "spatial_abstraction_report":
            spatial_abstraction_report,

            # ====================================
            # ANALOGICAL REASONING
            # ====================================

            "analogical_report":
            analogical_report,

            "transfer_insight":
            transfer_insight,

            # ====================================
            # SYMBOLIC REASONING
            # ====================================

            "symbolic_report":
            symbolic_report,

            # ====================================
            # CAUSAL REASONING
            # ====================================

            "causal_report":
            causal_report,

            # ====================================
            # ARC GENERALIZATION
            # ====================================

            "generalization_report":
            generalization_report,

            # ====================================
            # DEPENDENCY ACTIVATION
            # ====================================

            "dependency_activation_report":
            dependency_activation_report,

            "DEPENDENCY_ACTIVATION_REPORT":
            dependency_activation_report.get(
                "DEPENDENCY_ACTIVATION_REPORT",
                {},
            ),

            "dependency_activation_state":
            dependency_activation_report.get(
                "dependency_activation_state"
            ),

            "dependency_activation_reason":
            dependency_activation_report.get(
                "dependency_activation_reason"
            ),

            "dependency_runtime_triggered":
            dependency_activation_report.get(
                "dependency_runtime_triggered",
                False,
            ),

            "dependency_graph_size":
            dependency_activation_report.get(
                "dependency_graph_size",
                0,
            ),

            "dependency_chain_count":
            dependency_activation_report.get(
                "dependency_chain_count",
                0,
            ),

            "dependency_chains_executed":
            dependency_activation_report.get(
                "dependency_chains_executed",
                0,
            ),

            "dependency_chain_depth":
            dependency_activation_report.get(
                "dependency_chain_depth",
                0,
            ),

            "dependency_chain_coverage":
            dependency_activation_report.get(
                "dependency_chain_coverage",
                0.0,
            ),

            "process_context_count":
            dependency_activation_report.get(
                "process_context_count",
                0,
            ),

            "causal_context_count":
            dependency_activation_report.get(
                "causal_context_count",
                0,
            ),

            "activation_success_rate":
            dependency_activation_report.get(
                "activation_success_rate",
                0.0,
            ),

            # ====================================
            # PROCESS CONTEXT RUNTIME
            # ====================================

            "process_context_runtime_report":
            process_context_runtime_report,

            "PROCESS_CONTEXT_REPORT":
            process_context_runtime_report.get(
                "PROCESS_CONTEXT_REPORT",
                {},
            ),

            "process_context_depth":
            process_context_runtime_report.get(
                "process_context_depth",
                0,
            ),

            "process_context_confidence":
            process_context_runtime_report.get(
                "process_context_confidence",
                0.0,
            ),

            "process_simulation_time":
            process_context_runtime_report.get(
                "process_simulation_time",
                0.0,
            ),

            "state_transition_count":
            process_context_runtime_report.get(
                "state_transition_count",
                0,
            ),

            "process_reuse_rate":
            process_context_runtime_report.get(
                "process_reuse_rate",
                0.0,
            ),

            "process_success_rate":
            process_context_runtime_report.get(
                "process_success_rate",
                0.0,
            ),

            # ====================================
            # COLOR MAPPING REASONING
            # ====================================

            "color_mapping_report":
            color_mapping_report,

            "COLOR_MAPPING_REPORT":
            color_mapping_report.get(
                "COLOR_MAPPING_REPORT",
                {},
            ),

            # ====================================
            # TRANSFORMATION SYNTHESIS
            # ====================================

            "transformation_synthesis_report":
            transformation_synthesis_report,

            "TRANSFORMATION_SYNTHESIS_REPORT":
            transformation_synthesis_report.get(
                "TRANSFORMATION_SYNTHESIS_REPORT",
                {},
            ),

            # ====================================
            # CAUSAL CONTEXT RUNTIME
            # ====================================

            "causal_context_runtime_report":
            causal_context_runtime_report,

            "CAUSAL_CONTEXT_REPORT":
            causal_context_runtime_report.get(
                "CAUSAL_CONTEXT_REPORT",
                {},
            ),

            "causal_context_count":
            causal_context_runtime_report.get(
                "causal_context_count",
                0,
            ),

            "causal_context_depth":
            causal_context_runtime_report.get(
                "causal_context_depth",
                0,
            ),

            "causal_inference_time":
            causal_context_runtime_report.get(
                "causal_inference_time",
                0.0,
            ),

            "causal_simulation_time":
            causal_context_runtime_report.get(
                "causal_simulation_time",
                0.0,
            ),

            "causal_success_rate":
            causal_context_runtime_report.get(
                "causal_success_rate",
                0.0,
            ),

            "causal_reuse_rate":
            causal_context_runtime_report.get(
                "causal_reuse_rate",
                0.0,
            ),

            "causal_prediction_gain":
            causal_context_runtime_report.get(
                "causal_prediction_gain",
                0.0,
            ),

            # ====================================
            # DYNAMIC ARC CONCEPTS RUNTIME
            # ====================================

            "dynamic_concept_runtime_report":
            dynamic_concept_runtime_report,

            "DYNAMIC_CONCEPT_REPORT":
            dynamic_concept_runtime_report.get(
                "DYNAMIC_CONCEPT_REPORT",
                {},
            ),

            "dynamic_concept_count":
            dynamic_concept_runtime_report.get(
                "dynamic_concept_count",
                0,
            ),

            "dynamic_simulation_time":
            dynamic_concept_runtime_report.get(
                "dynamic_simulation_time",
                0.0,
            ),

            "dynamic_prediction_gain":
            dynamic_concept_runtime_report.get(
                "dynamic_prediction_gain",
                0.0,
            ),

            "gravity_reasoning_count":
            dynamic_concept_runtime_report.get(
                "gravity_reasoning_count",
                0,
            ),

            "path_reasoning_count":
            dynamic_concept_runtime_report.get(
                "path_reasoning_count",
                0,
            ),

            "propagation_reasoning_count":
            dynamic_concept_runtime_report.get(
                "propagation_reasoning_count",
                0,
            ),

            "multi_step_reasoning_count":
            dynamic_concept_runtime_report.get(
                "multi_step_reasoning_count",
                0,
            ),

            "state_transition_count":
            max(
                process_context_runtime_report.get(
                    "state_transition_count",
                    0,
                ),
                dynamic_concept_runtime_report.get(
                    "state_transition_count",
                    0,
                ),
            ),

            # ====================================
            # RECURSIVE REASONING
            # ====================================

            "recursive_report":
            recursive_report,

            # ====================================
            # HYPOTHESIS ARBITRATION
            # ====================================

            "arbitration_report":
            arbitration_report,

            "orchestration_summary":
            orchestration_summary,

            "orchestration_state":
            self.orchestration_state,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.reasoning_history.append(
            report
        )

        self.orchestration_state[
            "orchestration_cycles"
        ] += 1

        return report

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        latest_cycle = {}

        if self.reasoning_history:

            latest_cycle = (
                self.reasoning_history[-1]
            )

        return {

            "orchestration_state":
            self.orchestration_state,

            "reasoning_cycles":

            len(
                self.reasoning_history
            ),

            "routing_history":

            len(
                self.routing_history
            ),

            "load_history":

            len(
                self.load_history
            ),

            "executive_sync_history":

            len(
                self.executive_sync_history
            ),

            "latest_cycle":
            latest_cycle
        }

    def _collect_dependency_concepts(self, *sources):
        concepts = []
        trigger_concepts = set(
            getattr(
                dependency_activation_bridge,
                "ACTIVATION_RULES",
                {},
            ).keys()
        )

        def visit(value):
            if isinstance(value, str):
                token = value.lower().replace("-", "_").replace(" ", "_")
                if token in trigger_concepts and token not in concepts:
                    concepts.append(token)
            elif isinstance(value, dict):
                for item in value.values():
                    visit(item)
            elif isinstance(value, (list, tuple, set)):
                for item in value:
                    visit(item)

        for source in sources:
            visit(source)
        return concepts

    def _selected_runtime_tools(self, runtime_context):
        tools = set(runtime_context.get("enabled_tools", []) or [])
        selection_report = runtime_context.get("tool_selection_report", {})
        if isinstance(selection_report, dict):
            tools.update(selection_report.get("enabled_tools", []) or [])
            tools.update(selection_report.get("selected_tools", []) or [])
            tools.update(selection_report.get("tools", []) or [])
        requests = runtime_context.get("runtime_tool_requests", {})
        if isinstance(requests, dict):
            tools.update(requests.keys())
        return sorted(tools)


# ============================================
# GLOBAL ORCHESTRATOR
# ============================================

reasoning_orchestrator = (
    ReasoningOrchestrator()
)
