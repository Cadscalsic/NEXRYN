# ============================================
# NEXRYN INFERENCE STAGE
# EXECUTABLE COGNITIVE RUNTIME
# STABLE REFACTORED ARCHITECTURE
# ============================================

from datetime import datetime

import numpy as np

# ============================================
# MEMORY
# ============================================

from runtime.memory import (
    persistent_cognitive_memory,
    semantic_experience_index,
    latent_reasoning_reservoir,
    cognitive_failure_memory
)

from runtime.memory.adaptive_memory import (
    AdaptiveMemory
)

# ============================================
# ENGINES
# ============================================

from runtime.engines.hypothesis_engine import (
    HypothesisEngine
)

from runtime.engines.program_synthesis import (
    ProgramSynthesisEngine
)

from runtime.learning.operator_reward_engine import (
    OperatorRewardEngine
)

# ============================================
# PLANNING
# ============================================

from runtime.planning.planning_engine import (
    PlanningEngine
)

# ============================================
# SEARCH
# ============================================

from runtime.search.cognitive_search import (
    CognitiveSearchEngine
)

from runtime.search.search_reinforcement import (
    SearchReinforcementEngine
)

from runtime.search.exploration_engine import (
    ExplorationEngine
)

# ============================================
# HIERARCHY
# ============================================

from runtime.hierarchy.hierarchy_engine import (
    HierarchyEngine
)

# ============================================
# EVOLUTION
# ============================================

from runtime.evolution.strategy_mutation import (
    StrategyMutationEngine
)

# ============================================
# RECURSION
# ============================================

from runtime.recursion.recursive_cognition import (
    RecursiveCognitionEngine
)
from runtime.reasoning.hypothesis_arbitration_engine import (
    HypothesisArbitrationEngine,
)

# ============================================
# META
# ============================================

from runtime.meta.meta_controller import (
    MetaControllerEngine
)

from runtime.meta import (
    adaptive_strategy_injector
)

# ============================================
# SEMANTICS
# ============================================

from runtime.semantics.semantic_abstraction import (
    SemanticAbstractionEngine
)

# ============================================
# ANALOGY
# ============================================

from runtime.analogy.analogical_transfer import (
    AnalogicalTransferEngine
)

# ============================================
# GOALS
# ============================================

from runtime.goals.goal_arbitration import (
    GoalArbitrationEngine
)

# ============================================
# ROUTING
# ============================================

from runtime.routing.dynamic_router import (
    DynamicCognitiveRouter
)

# ============================================
# COGNITION
# ============================================

from runtime.cognition.cognitive_state_manager import (
    CognitiveStateManager
)

# ============================================
# EXECUTIVE
# ============================================

from runtime.executive.attention_controller import (
    AttentionController
)

from runtime.executive.dynamic_attention_allocation import (
    dynamic_attention_allocation_runtime
)

# ============================================
# DEBUG
# ============================================

from runtime.debug.inference_debugger import (
    InferenceDebugger
)

# ============================================
# TEMPORAL MEMORY
# ============================================

from runtime.episodic.temporal_memory import (
    TemporalEpisodicMemory
)

# ============================================
# TRANSFORMS
# ============================================

from runtime.transforms import (

    geometric_reasoning_engine,

    object_delta_engine,

    primitive_discovery_engine,

    primitive_executor,

    topology_engine
)

# ============================================
# WORLD MODEL
# ============================================

from runtime.world import (
    world_model_engine
)
from runtime.execution.execution_integrity_guard import (
    execution_integrity_guard,
)
from runtime.execution.world_model_gate import (
    world_model_gate,
)

# ============================================
# GLOBAL ENGINES
# ============================================

adaptive_memory = AdaptiveMemory()

hypothesis_engine = HypothesisEngine()

program_synthesis_engine = (
    ProgramSynthesisEngine()
)

operator_reward_engine = (
    OperatorRewardEngine()
)

planning_engine = PlanningEngine()

cognitive_search_engine = (
    CognitiveSearchEngine()
)

search_reinforcement_engine = (
    SearchReinforcementEngine()
)

exploration_engine = (
    ExplorationEngine()
)

strategy_mutation_engine = (
    StrategyMutationEngine()
)

meta_controller_engine = (
    MetaControllerEngine()
)

semantic_abstraction_engine = (
    SemanticAbstractionEngine()
)

analogical_transfer_engine = (
    AnalogicalTransferEngine()
)

goal_arbitration_engine = (
    GoalArbitrationEngine()
)

recursive_cognition_engine = (
    RecursiveCognitionEngine()
)

hypothesis_arbitration_engine = (
    HypothesisArbitrationEngine()
)

hierarchy_engine = (
    HierarchyEngine()
)

dynamic_router = (
    DynamicCognitiveRouter()
)

cognitive_state_manager = (
    CognitiveStateManager()
)

attention_controller = (
    AttentionController()
)

inference_debugger = (
    InferenceDebugger()
)

temporal_memory = (
    TemporalEpisodicMemory()
)

# ============================================
# SAFE GRID EXTRACTION
# ============================================

def extract_grid_array(grid_object):

    if hasattr(
        grid_object,
        "grid"
    ):

        return np.array(
            grid_object.grid
        )

    return np.array(grid_object)


# ============================================
# FILTER SEMANTIC DRIFT
# ============================================

def filter_semantic_drift(
    hypotheses
):

    filtered = []

    for hypothesis in hypotheses:

        if not isinstance(
            hypothesis,
            dict
        ):

            continue

        hypothesis_type = str(

            hypothesis.get(
                "type",
                ""
            )
        )

        contextual_depth = (
            hypothesis_type.count(
                "contextual"
            )
        )

        adaptive_depth = (
            hypothesis_type.count(
                "adaptive"
            )
        )

        if contextual_depth > 1:
            continue

        if adaptive_depth > 1:
            continue

        filtered.append(
            hypothesis
        )

    return filtered


# ============================================
# FILTER EXECUTABLE
# ============================================

def filter_executable_hypotheses(
    hypotheses
):

    executable = []

    for hypothesis in hypotheses:

        if not isinstance(
            hypothesis,
            dict
        ):

            continue

        primitive = hypothesis.get(
            "primitive"
        )

        if primitive is None:
            continue

        executable.append(
            hypothesis
        )

    return executable


# ============================================
# SAFE LIST
# ============================================

def safe_list(value):

    if value is None:
        return []

    if not isinstance(
        value,
        list
    ):

        return []

    return value


# ============================================
# ESTIMATE TASK COMPLEXITY
# ============================================

def estimate_task_complexity(
    input_array,
    output_array,
    input_objects,
    output_objects
):

    if input_array is None or output_array is None:

        return 0.5

    total_cells = max(
        int(input_array.size),
        1
    )

    size_factor = min(
        total_cells / 100,
        1.0
    )

    input_colors = set(
        np.unique(input_array).tolist()
    )

    output_colors = set(
        np.unique(output_array).tolist()
    )

    color_delta = len(
        input_colors.symmetric_difference(
            output_colors
        )
    )

    color_factor = min(
        color_delta / 5,
        1.0
    )

    object_delta = abs(
        len(input_objects)
        -
        len(output_objects)
    )

    object_factor = min(
        object_delta / 4,
        1.0
    )

    changed_cells = int(
        np.sum(
            input_array != output_array
        )
    ) if input_array.shape == output_array.shape else total_cells

    change_factor = min(
        changed_cells / total_cells,
        1.0
    )

    shape_factor = 1.0 if (
        input_array.shape != output_array.shape
    ) else 0.0

    complexity = (
        size_factor * 0.15
        +
        color_factor * 0.20
        +
        object_factor * 0.20
        +
        change_factor * 0.35
        +
        shape_factor * 0.10
    )

    return round(
        complexity,
        4
    )


# ============================================
# DEPTH LIMIT FROM COMPLEXITY
# ============================================

def adaptive_depth_limit(
    task_complexity
):

    if task_complexity < 0.30:

        return 4

    if task_complexity > 0.80:

        return 15

    return 8


# ============================================
# DYNAMIC REASONING ALLOCATION
# ============================================

def allocate_reasoning_depth(
    raw_depth,
    base_limit,
    task_complexity,
    hypotheses
):

    causal_density = 0.0

    confidence_scores = []

    entropy_risk = 0.0

    causal_terms = [
        "causal",
        "topology",
        "translation",
        "density",
        "object"
    ]

    for hypothesis in hypotheses:

        if not isinstance(
            hypothesis,
            dict
        ):

            continue

        hypothesis_type = str(
            hypothesis.get(
                "type",
                ""
            )
        )

        primitive = str(
            hypothesis.get(
                "primitive",
                ""
            )
        )

        if any(
            term in hypothesis_type
            or
            term in primitive
            for term in causal_terms
        ):

            causal_density += 1

        confidence_scores.append(
            hypothesis.get(
                "confidence",
                0.0
            )
        )

        if hypothesis.get(
            "mutation_applied",
            False
        ):

            entropy_risk += 0.15

        entropy_risk += min(
            hypothesis_type.count("_") / 20,
            0.20
        )

    hypothesis_count = max(
        len(hypotheses),
        1
    )

    causal_density = min(
        causal_density / hypothesis_count,
        1.0
    )

    average_confidence = 0.0

    if confidence_scores:

        average_confidence = (
            sum(confidence_scores)
            /
            len(confidence_scores)
        )

    entropy_risk = min(
        entropy_risk,
        1.0
    )

    allocated_limit = base_limit

    allocation_reason = "base_limit"

    if average_confidence >= 0.95 and entropy_risk < 0.35:

        allocated_limit = min(
            allocated_limit,
            4
        )

        allocation_reason = "confidence_high_terminate_early"

    if causal_density > 0.65 and task_complexity >= 0.20:

        allocated_limit = max(
            allocated_limit,
            8
        )

        allocation_reason = "causal_density_high"

    if entropy_risk > 0.55:

        allocated_limit = min(
            allocated_limit,
            5
        )

        allocation_reason = "entropy_risk_compress_reasoning"

    allocated_limit = int(
        min(
            max(
                allocated_limit,
                4
            ),
            15
        )
    )

    return {
        "allocated_depth_limit": allocated_limit,
        "regulated_depth": min(
            raw_depth,
            allocated_limit
        ),
        "causal_density": round(causal_density, 4),
        "average_confidence": round(average_confidence, 4),
        "entropy_risk": round(entropy_risk, 4),
        "allocation_reason": allocation_reason
    }


# ============================================
# INFERENCE STAGE
# ============================================

def inference_stage(context):

    print(
        "\n=================================================="
    )

    print(
        "NEXRYN :: INFERENCE STAGE"
    )

    print(
        "==================================================\n"
    )

    # ========================================
    # STAGE REPORT
    # ========================================

    stage_report = {

        "stage":
        "inference",

        "status":
        "running",

        "timestamp":
        str(datetime.utcnow())
    }

    # ========================================
    # SAFE CONTEXT
    # ========================================

    if not isinstance(
        context,
        dict
    ):

        context = {}

    # ========================================
    # LOAD GRIDS
    # ========================================

    input_grid = context.get(
        "input_grid"
    )

    output_grid = context.get(
        "output_grid"
    )

    if input_grid is None:

        raise ValueError(
            "Missing input_grid"
        )

    if output_grid is None:

        raise ValueError(
            "Missing output_grid"
        )

    # ========================================
    # LOAD CONTEXT
    # ========================================

    patterns = safe_list(
        context.get(
            "patterns",
            []
        )
    )

    input_objects = safe_list(
        context.get(
            "input_object_summaries",
            context.get(
                "input_objects",
                []
            )
        )
    )

    output_objects = safe_list(
        context.get(
            "output_object_summaries",
            context.get(
                "output_objects",
                []
            )
        )
    )

    strategy_database = context.get(
        "strategy_database",
        {}
    )

    # ========================================
    # ARRAYS
    # ========================================

    input_array = extract_grid_array(
        input_grid
    )

    output_array = extract_grid_array(
        output_grid
    )

    task_complexity = estimate_task_complexity(
        input_array,
        output_array,
        input_objects,
        output_objects
    )

    reasoning_depth_limit = adaptive_depth_limit(
        task_complexity
    )

    # ========================================
    # GEOMETRIC REASONING
    # ========================================

    geometric_result = (

        geometric_reasoning_engine
        .run_reasoning(

            input_grid=
            input_array,

            output_grid=
            output_array,

            input_objects=
            input_objects,

            output_objects=
            output_objects
        )
    )

    geometric_hypotheses = (

        geometric_result.get(
            "executable_hypotheses",
            []
        )
    )

    # ========================================
    # OBJECT DELTA ANALYSIS
    # ========================================

    delta_result = (

        object_delta_engine
        .analyze_deltas(

            input_objects,

            output_objects
        )
    )

    delta_hypotheses = (

        delta_result.get(
            "executable_hypotheses",
            []
        )
    )

    # ========================================
    # TOPOLOGY ANALYSIS
    # ========================================

    topology_result = (

        topology_engine
        .run_analysis(

            input_array,

            output_array
        )
    )

    # ========================================
    # STORAGE
    # ========================================

    hypotheses = []

    reasoning_trace = []

    # ========================================
    # LOAD GENERATED HYPOTHESES
    # ========================================

    hypotheses.extend(
        geometric_hypotheses
    )

    hypotheses.extend(
        delta_hypotheses
    )

    # ========================================
    # REASONING TRACE
    # ========================================

    for report in geometric_result.get(
        "ranked_reports",
        []
    ):

        reasoning_trace.append(

            report.get(
                "operator",
                "unknown"
            )
        )

    for report in delta_result.get(
        "ranked_reports",
        []
    ):

        reasoning_trace.append(

            report.get(
                "operator",
                "unknown"
            )
        )

    # ========================================
    # MEMORY GUIDANCE
    # ========================================

    similar_experiences = (

        adaptive_memory.retrieve_guidance(
            patterns
        )
    )

    hypotheses = (

        adaptive_memory.adapt_hypotheses(

            hypotheses,

            similar_experiences
        )
    )

    # ========================================
    # STRATEGY INJECTION
    # ========================================

    hypotheses = (

        adaptive_strategy_injector
        .inject_strategies(

            hypotheses,

            context.get(
                "similar_experiences",
                []
            )
        )
    )

    # ========================================
    # REINFORCEMENT
    # ========================================

    hypotheses = (

        search_reinforcement_engine
        .apply_boosts(

            hypotheses,

            strategy_database
        )
    )

    # ========================================
    # EXPLORATION
    # ========================================

    hypotheses = (

        exploration_engine
        .apply_exploration(
            hypotheses
        )
    )

    # ========================================
    # MUTATION
    # ========================================

    hypotheses = (

        strategy_mutation_engine
        .apply_mutation(
            hypotheses
        )
    )

    # ========================================
    # FILTERS
    # ========================================

    hypotheses = (
        filter_semantic_drift(
            hypotheses
        )
    )

    executable_hypotheses = (

        filter_executable_hypotheses(
            hypotheses
        )
    )

    # ========================================
    # HIERARCHY
    # ========================================

    hierarchy = (

        hierarchy_engine
        .build_hierarchy(

            executable_hypotheses
        )
    )

    # ========================================
    # RECURSIVE COGNITION
    # ========================================

    recursive_report = {

        "cognitive_complexity":
        "stable"
    }

    try:

        recursive_report = (

            recursive_cognition_engine
            .analyze_reasoning(

                executable_hypotheses,

                reasoning_trace,

                hierarchy
            )
        )

    except Exception as error:

        print(
            "\nRECURSIVE ERROR:\n"
        )

        print(error)

    raw_reasoning_depth = len(
        reasoning_trace
    )

    reasoning_allocation = allocate_reasoning_depth(
        raw_reasoning_depth,
        reasoning_depth_limit,
        task_complexity,
        executable_hypotheses
    )

    reasoning_depth_limit = reasoning_allocation.get(
        "allocated_depth_limit",
        reasoning_depth_limit
    )

    regulated_reasoning_depth = reasoning_allocation.get(
        "regulated_depth",
        min(
            raw_reasoning_depth,
            reasoning_depth_limit
        )
    )

    recursive_report[
        "raw_reasoning_depth"
    ] = raw_reasoning_depth

    recursive_report[
        "reasoning_depth"
    ] = regulated_reasoning_depth

    recursive_report[
        "reasoning_depth_limit"
    ] = reasoning_depth_limit

    recursive_report[
        "task_complexity"
    ] = task_complexity

    recursive_report[
        "reasoning_allocation"
    ] = reasoning_allocation

    latent_reasoning_event = {}

    if raw_reasoning_depth > regulated_reasoning_depth:

        latent_reasoning_event = (
            latent_reasoning_reservoir
            .store_hidden_reasoning(
                reasoning_trace=reasoning_trace,
                visible_depth=regulated_reasoning_depth,
                reason=reasoning_allocation.get(
                    "allocation_reason",
                    "depth_regulation"
                ),
                context_signals={
                    "task_complexity":
                    task_complexity,

                    "reasoning_depth_limit":
                    reasoning_depth_limit,

                    "raw_reasoning_depth":
                    raw_reasoning_depth
                }
            )
        )

    # ========================================
    # META CONTROL
    # ========================================

    control_state = (

        meta_controller_engine
        .adapt_control(

            recursive_report
        )
    )

    exploration_engine.exploration_rate = (
        control_state.get(
            "exploration_rate",
            exploration_engine.exploration_rate
        )
    )

    strategy_mutation_engine.mutation_rate = (
        control_state.get(
            "mutation_rate",
            strategy_mutation_engine.mutation_rate
        )
    )

    # ========================================
    # GOAL ARBITRATION
    # ========================================

    candidate_goals = []

    for hypothesis in executable_hypotheses:

        candidate_goals.append({

            "goal_type":
            hypothesis.get(
                "type",
                "unknown"
            ),

            "confidence":
            hypothesis.get(
                "confidence",
                0.0
            )
        })

    arbitration_report = (

        goal_arbitration_engine
        .select_goal(
            candidate_goals
        )
    )

    # ========================================
    # SEMANTIC ABSTRACTION
    # ========================================

    semantic_abstractions = (

        semantic_abstraction_engine
        .abstract_hypotheses(

            executable_hypotheses
        )
    )

    semantic_graph = (

        semantic_abstraction_engine
        .build_semantic_graph(

            semantic_abstractions
        )
    )

    # ========================================
    # ANALOGICAL TRANSFER
    # ========================================

    analogies = (

        analogical_transfer_engine
        .find_analogies(
            semantic_graph
        )
    )

    transfer_report = (

        analogical_transfer_engine
        .build_transfer_report(
            analogies
        )
    )

    # ========================================
    # RANK HYPOTHESES
    # ========================================

    for hypothesis in executable_hypotheses:

        if not isinstance(
            hypothesis,
            dict
        ):

            continue

        operator_weight = (

            operator_reward_engine
            .get_operator_weight(
                hypothesis.get(
                    "primitive"
                )
            )
        )

        operator_reward_score = (

            operator_reward_engine
            .get_operator_reward_score(
                hypothesis.get(
                    "primitive"
                )
            )
        )

        primitive = hypothesis.get(
            "primitive"
        )

        grid_changed = not np.array_equal(
            input_array,
            output_array
        )

        if (

            grid_changed

            and

            primitive in [

                "preserve_objects",
                "preserve_shape",
                "preserve_density",
                "preserve_colors",
                "preserve_topology",
                "preserve_symmetry"
            ]
        ):

            operator_weight = 0.0

            operator_reward_score = 0.0

            hypothesis[
                "no_op_penalty"
            ] = True

        base_score = hypothesis.get(
            "execution_score",
            0.0
        )

        immune_memory_penalty = max(
            cognitive_failure_memory.prior_failure_weight(
                hypothesis.get(
                    "type"
                )
            ),
            cognitive_failure_memory.prior_failure_weight(
                primitive
            )
        )

        hypothesis[
            "operator_weight"
        ] = round(
            operator_weight,
            4
        )

        hypothesis[
            "operator_reward_score"
        ] = round(
            operator_reward_score,
            4
        )

        hypothesis[
            "grounded_execution_score"
        ] = round(
            (
                base_score * 0.7
            )
            +
            (
                operator_weight * 0.3
            ),
            4
        )

        hypothesis[
            "immune_memory_penalty"
        ] = immune_memory_penalty

        hypothesis[
            "search_final_score"
        ] = (
            cognitive_search_engine
            .score_hypothesis(
                hypothesis
            )
        )

        hypothesis[
            "search_final_score"
        ] = round(
            max(
                hypothesis.get(
                    "search_final_score",
                    0.0
                )
                -
                (
                    immune_memory_penalty
                    *
                    0.10
                ),
                0.0
            ),
            4
        )

    ranked_hypotheses = sorted(

        executable_hypotheses,

        key=lambda h: (

            h.get(
                "search_final_score",
                0.0
            ),

            h.get(
                "grounded_execution_score",
                0.0
            )
        ),

        reverse=True
    )

    # ========================================
    # WINNER
    # ========================================

    winner_hypothesis = {}

    if ranked_hypotheses:

        winner_hypothesis = (
            ranked_hypotheses[0]
        )

    # ========================================
    # SEARCH
    # ========================================

    search_result = (

        cognitive_search_engine
        .search(
            ranked_hypotheses
        )
    )

    best_path = (
        search_result.get(
            "best_path"
        )
    )

    selected_hypotheses = []

    if best_path:

        selected_hypotheses = (

            best_path.get(
                "hypotheses",
                []
            )
        )

    execution_arbitration_report = (
        hypothesis_arbitration_engine
        .arbitrate_execution_candidates(
            hypotheses=ranked_hypotheses,
            input_grid=input_array,
            target_grid=output_array,
            world_model_engine=world_model_engine,
            program_synthesis_engine=program_synthesis_engine,
        )
    )

    arbitration_winner = execution_arbitration_report.get(
        "winner",
        {},
    )

    if arbitration_winner:

        winner_hypothesis = arbitration_winner.get(
            "hypothesis",
            winner_hypothesis,
        )

        selected_hypotheses = [
            winner_hypothesis
        ]

    arbitrated_program = arbitration_winner.get(
        "program"
    )

    # ========================================
    # PRIMITIVE DISCOVERY
    # ========================================

    primitive_result = (

        primitive_discovery_engine
        .run_discovery(

            geometric_result.get(
                "ranked_reports",
                []
            )

            +

            delta_result.get(
                "ranked_reports",
                []
            )
        )
    )

    ranked_primitives = (

        primitive_result.get(
            "ranked_primitives",
            []
        )
    )

    ranked_primitives = (
        operator_reward_engine
        .apply_operator_weights(
            ranked_primitives
        )
    )

    # ========================================
    # PROGRAM SYNTHESIS
    # ========================================

    synthesized_program = (

        arbitrated_program

        if arbitrated_program

        else

        program_synthesis_engine
        .synthesize(

            ranked_primitives,

            winner_hypothesis=
            winner_hypothesis
        )
    )

    # ========================================
    # WORLD MODEL ANTICIPATION
    # ========================================

    anticipation_report = (

        world_model_engine
        .anticipate_program(

            input_grid=
            input_array,

            target_grid=
            output_array,

            synthesized_program=
            synthesized_program,

            minimum_accuracy=
            0.75
        )
    )

    if not anticipation_report.get(
        "accepted",
        False
    ):

        current_accuracy = (
            anticipation_report
            .get(
                "prediction_report",
                {}
            )
            .get(
                "prediction_accuracy",
                0.0
            )
        )

        alternatives = (
            execution_arbitration_report
            .get(
                "ranked_candidates",
                []
            )
        )

        if alternatives:

            best_world_model_candidate = max(
                alternatives,
                key=lambda candidate:
                candidate.get(
                    "anticipation",
                    {}
                ).get(
                    "prediction_report",
                    {}
                ).get(
                    "prediction_accuracy",
                    0.0
                ),
            )

            alternative_anticipation = (
                best_world_model_candidate.get(
                    "anticipation",
                    {}
                )
            )

            alternative_accuracy = (
                alternative_anticipation
                .get(
                    "prediction_report",
                    {}
                )
                .get(
                    "prediction_accuracy",
                    0.0
                )
            )

            if alternative_accuracy > current_accuracy:

                synthesized_program = (
                    best_world_model_candidate.get(
                        "program",
                        synthesized_program
                    )
                )

                anticipation_report = alternative_anticipation

                winner_hypothesis = (
                    best_world_model_candidate.get(
                        "hypothesis",
                        winner_hypothesis
                    )
                )

                selected_hypotheses = [
                    winner_hypothesis
                ]

    anticipation_uncertainty = (
        anticipation_report
        .get(
            "uncertainty_report",
            {}
        )
        .get(
            "simulation_uncertainty",
            0.0
        )
    )

    if anticipation_uncertainty > 0.45:

        exploration_engine.exploration_rate = min(
            exploration_engine.exploration_rate
            +
            0.10,
            0.50
        )

        control_state[
            "exploration_rate"
        ] = exploration_engine.exploration_rate

        control_state[
            "uncertainty_triggered_exploration"
        ] = True

    # ========================================
    # EXECUTION PLAN
    # ========================================

    execution_plan = (

        planning_engine
        .build_plan(

            synthesized_program
        )
    )

    planned_primitives = (
        execution_integrity_guard
        .primitives_from_plan(
            execution_plan
        )
    )

    world_model_gate_report = (
        world_model_gate.evaluate(
            anticipation_report
        )
    )

    sandbox_execution_result = None

    if world_model_gate_report[
        "sandbox_execution_authorized"
    ]:

        sandbox_execution_result = {

            "execution_mode":
            "isolated_world_model_sandbox",

            "output_grid":
            anticipation_report.get(
                "simulation",
                {}
            ).get(
                "predicted_grid"
            ),

            "execution_trace":
            anticipation_report.get(
                "simulation",
                {}
            ).get(
                "simulation_trace",
                []
            ),

            "persistent_effects_forbidden":
            True
        }

    # ========================================
    # EXECUTABLE PREDICTION
    # ========================================

    if world_model_gate_report[
        "execution_authorized"
    ]:

        execution_result = (

            primitive_executor
            .run_execution(

                input_grid=
                input_array,

                primitives=
                planned_primitives
            )
        )

    else:

        execution_result = {

            "output_grid":
            np.array(
                input_array,
                copy=True
            ),

            "execution_trace":
            [],

            "execution_aborted":
            True,

            "abort_reason":
            world_model_gate_report[
                "gate_state"
            ]
        }

    execution_integrity_report = (
        execution_integrity_guard.evaluate(
            execution_plan,
            execution_result.get(
                "execution_trace",
                []
            ),
            execution_authorized=
            world_model_gate_report[
                "execution_authorized"
            ],
        )
    )

    if (
        world_model_gate_report[
            "execution_authorized"
        ]
        and not execution_integrity_report[
            "integrity_preserved"
        ]
    ):

        execution_result = {

            **execution_result,

            "output_grid":
            np.array(
                input_array,
                copy=True
            ),

            "execution_aborted":
            True,

            "abort_reason":
            "EXECUTION_INTEGRITY_VIOLATION"
        }

    predicted_output = execution_result.get(
        "output_grid"
    )

    if sandbox_execution_result is not None:

        predicted_output = sandbox_execution_result.get(
            "output_grid",
            predicted_output
        )

    # ========================================
    # OPERATOR REWARD GROUNDING
    # ========================================

    operator_reward_report = (

        operator_reward_engine
        .update_operator_weights(

            primitives=
            planned_primitives,

            predicted_output=
            predicted_output,

            target_output=
            output_array
        )
    )

    # ========================================
    # CONFIDENCE
    # ========================================

    confidence_scores = [

        h.get(
            "confidence",
            0.0
        )

        for h in selected_hypotheses
    ]

    global_confidence = 0.0

    if confidence_scores:

        global_confidence = (

            sum(confidence_scores)

            /

            len(confidence_scores)
        )

    # ========================================
    # COGNITIVE PRESSURE
    # ========================================

    cognitive_pressure = round(

        min(

            regulated_reasoning_depth / 25,

            1.0
        ),

        4
    )

    # ========================================
    # INFERENCE REPORT
    # ========================================

    inference_report = {

        "hypothesis_count":
        len(selected_hypotheses),

        "global_confidence":
        round(
            global_confidence,
            4
        ),

        "reasoning_depth":
        regulated_reasoning_depth,

        "raw_reasoning_depth":
        raw_reasoning_depth,

        "reasoning_depth_limit":
        reasoning_depth_limit,

        "task_complexity":
        task_complexity,

        "reasoning_allocation":
        reasoning_allocation,

        "winner_hypothesis":
        winner_hypothesis,

        "program_step_count":
        synthesized_program.get(
            "step_count",
            0
        ),

        "execution_plan_nodes":
        execution_plan.get(
            "node_count",
            0
        ),

        "primitive_count":
        len(
            planned_primitives
        ),

        "discovered_primitive_count":
        len(
            ranked_primitives
        ),

        "world_model_gate":
        world_model_gate_report,

        "execution_integrity":
        execution_integrity_report,

        "sandbox_execution":
        sandbox_execution_result,

        "operator_reward_score":
        operator_reward_report.get(
            "metrics",
            {}
        ).get(
            "reward_score",
            0.0
        ),

        "world_model_anticipation":
        anticipation_report,

        "hypothesis_arbitration":
        execution_arbitration_report,

        "cognitive_pressure":
        cognitive_pressure
    }

    # ========================================
    # COGNITIVE STATE
    # ========================================

    cognitive_state_manager.update_state({

        "reasoning_depth":
        regulated_reasoning_depth,

        "hypothesis_count":
        len(selected_hypotheses),

        "top_confidence":
        global_confidence,

        "cognitive_complexity":
        recursive_report.get(
            "cognitive_complexity",
            "stable"
        )
    })

    cognitive_state = (
        cognitive_state_manager
        .get_state()
    )

    # ========================================
    # ROUTING
    # ========================================

    routing_plan = (

        dynamic_router
        .build_routing_plan(
            cognitive_state
        )
    )

    routing_report = (

        dynamic_router
        .build_routing_report(
            routing_plan
        )
    )

    # ========================================
    # ATTENTION
    # ========================================

    cognitive_cycle = {

        "reasoning":
        recursive_report,

        "goals":
        arbitration_report,

        "semantics":
        semantic_graph,

        "routing":
        routing_report,

        "execution":
        execution_plan
    }

    attention_plan = (

        attention_controller
        .build_attention_plan(
            cognitive_cycle
        )
    )

    attention_controller.store_attention_event(
        attention_plan
    )

    attention_report = (

        attention_controller
        .build_attention_report()
    )

    executive_summary = (

        attention_controller
        .build_executive_summary()
    )

    overload_state = (

        attention_controller
        .detect_overload(
            cognitive_cycle
        )
    )

    dynamic_attention_allocation = (
        dynamic_attention_allocation_runtime
        .allocate(
            context=context,
            cognitive_cycle=cognitive_cycle,
            memory_pressure_profile=(
                context
                .get(
                    "cognitive_governance_report",
                    {}
                )
                .get(
                    "cognitive_budget",
                    {}
                )
                .get(
                    "memory_pressure_profile",
                    {}
                )
            )
        )
    )

    dynamic_attention_report = (
        dynamic_attention_allocation_runtime
        .build_report()
    )

    # ========================================
    # TEMPORAL MEMORY
    # ========================================

    temporal_memory.store_episode(

        cognitive_cycle=
        cognitive_cycle,

        evaluation_result=
        inference_report
    )

    # ========================================
    # SEMANTIC INDEX
    # ========================================

    semantic_experience_index.index_experience(
        context
    )

    context[
        "semantic_index_report"
    ] = (

        semantic_experience_index
        .build_report()
    )

    # ========================================
    # OUTPUT STORAGE
    # ========================================

    context[
        "ground_truth_output"
    ] = output_array

    context[
        "predicted_output"
    ] = predicted_output

    # ========================================
    # STORE TRANSFORM REPORTS
    # ========================================

    context[
        "geometric_result"
    ] = geometric_result

    context[
        "delta_result"
    ] = delta_result

    context[
        "topology_result"
    ] = topology_result

    context[
        "primitive_result"
    ] = primitive_result

    context[
        "execution_result"
    ] = execution_result

    context[
        "sandbox_execution_result"
    ] = sandbox_execution_result

    context[
        "world_model_gate_report"
    ] = world_model_gate_report

    context[
        "execution_integrity_report"
    ] = execution_integrity_report

    context[
        "planned_primitives"
    ] = planned_primitives

    context[
        "ranked_primitives"
    ] = ranked_primitives

    context[
        "operator_reward_report"
    ] = operator_reward_report

    context[
        "world_model_anticipation"
    ] = anticipation_report

    context[
        "hypothesis_arbitration_report"
    ] = execution_arbitration_report

    context[
        "operator_weights"
    ] = (

        operator_reward_engine
        .build_report()
    )

    context[
        "latent_reasoning_event"
    ] = latent_reasoning_event

    context[
        "latent_reasoning_report"
    ] = (
        latent_reasoning_reservoir
        .build_report()
    )

    context[
        "cognitive_failure_memory_report"
    ] = (
        cognitive_failure_memory
        .build_report()
    )

    # ========================================
    # STORE CONTEXT
    # ========================================

    context["hypotheses"] = (
        selected_hypotheses
    )

    context["ranked_hypotheses"] = (
        ranked_hypotheses
    )

    context["winner_hypothesis"] = (
        winner_hypothesis
    )

    context["hierarchy"] = hierarchy

    context["recursive_report"] = (
        recursive_report
    )

    context["semantic_abstractions"] = (
        semantic_abstractions
    )

    context["semantic_graph"] = (
        semantic_graph
    )

    context["analogies"] = analogies

    context["transfer_report"] = (
        transfer_report
    )

    context["control_state"] = (
        control_state
    )

    context["cognitive_state"] = (
        cognitive_state
    )

    context["routing_plan"] = (
        routing_plan
    )

    context["routing_report"] = (
        routing_report
    )

    context["cognitive_cycle"] = (
        cognitive_cycle
    )

    context["search_result"] = (
        search_result
    )

    context["best_path"] = (
        best_path
    )

    context["synthesized_program"] = (
        synthesized_program
    )

    context["execution_plan"] = (
        execution_plan
    )

    context["reasoning_trace"] = (
        reasoning_trace
    )

    context["raw_reasoning_depth"] = (
        raw_reasoning_depth
    )

    context["regulated_reasoning_depth"] = (
        regulated_reasoning_depth
    )

    context["reasoning_depth_limit"] = (
        reasoning_depth_limit
    )

    context["task_complexity"] = (
        task_complexity
    )

    context["reasoning_allocation"] = (
        reasoning_allocation
    )

    context["inference_report"] = (
        inference_report
    )

    context["attention_plan"] = (
        attention_plan
    )

    context["attention_report"] = (
        attention_report
    )

    context["dynamic_attention_allocation"] = (
        dynamic_attention_allocation
    )

    context["dynamic_attention_report"] = (
        dynamic_attention_report
    )

    context["executive_summary"] = (
        executive_summary
    )

    context["overload_state"] = (
        overload_state
    )

    context["cognitive_pressure"] = (
        cognitive_pressure
    )

    context[
        "inference_stage_report"
    ] = stage_report

    context[
        "inference_complete"
    ] = True

    # ========================================
    # LEARNING
    # ========================================

    adaptive_memory.learn(
        context
    )

    # ========================================
    # DEBUG DISPLAY
    # ========================================

    try:

        inference_debugger.display(

            hypotheses=
            selected_hypotheses,

            control_state=
            control_state,

            recursive_report=
            recursive_report,

            arbitration_report=
            arbitration_report,

            semantic_abstractions=
            semantic_abstractions,

            semantic_graph=
            semantic_graph,

            search_result=
            search_result,

            synthesized_program=
            synthesized_program,

            execution_plan=
            execution_plan,

            inference_report=
            inference_report
        )

    except Exception:

        pass

    return context
