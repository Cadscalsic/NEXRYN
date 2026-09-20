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

from runtime.budget.runtime_budget_enforcer import (
    runtime_budget_enforcer,
)
from runtime.provenance import (
    build_candidate_origin_report,
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
from runtime.reasoning.object_centric_reasoner import (
    object_centric_reasoner,
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
from runtime.semantics.semantic_ontology import (
    compression_level_for_concept,
    lookup_hypothesis_concept,
    lookup_operator_semantics,
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
from core.scene_graph import (
    GraphReasoner,
)
from runtime.kernel.cognitive_blackboard import (
    cognitive_blackboard_from_context,
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

graph_reasoner = GraphReasoner()

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


TRANSFORMATION_PRIMITIVES = {
    "duplicate_object",
    "expand_object",
    "expand_pattern",
    "grow_topology",
    "replace_color",
    "translate_right",
    "translate_left",
    "translate_up",
    "translate_down",
    "mirror_object",
    "fill_region",
    "reduce_pattern",
}


PRESERVATION_PRIMITIVES = {
    "preserve_objects",
    "preserve_shape",
    "preserve_density",
    "preserve_colors",
    "preserve_topology",
    "preserve_symmetry",
    "preserve_position",
    "preserve_size",
}


FRONTIER_TRANSFORMATION_CONCEPTS = {
    "propagation",
    "density_modulation",
    "growth",
    "topological_growth",
    "topological_change",
    "topological_reasoning",
    "symbolic_remapping",
    "directional_motion",
    "reflection",
    "containment",
    "replication",
    "shape_relation",
    "symmetry_reasoning",
}


SUPPORTING_INVARIANT_CONCEPTS = {
    "object_identity_preservation",
    "shape_preservation",
    "color_preservation",
    "position_preservation",
    "size_preservation",
    "density_preservation",
    "topology_preservation",
    "symmetry_preservation",
}


def _bounded_number(value, default=0.0):

    try:

        return max(
            0.0,
            min(
                1.0,
                float(value)
            )
        )

    except (TypeError, ValueError):

        return default


def transformation_concept_score(
    hypothesis,
    grid_changed=False
):

    if not isinstance(
        hypothesis,
        dict
    ):

        return 0.0

    primitive = hypothesis.get(
        "primitive"
    )

    hypothesis_type = str(
        hypothesis.get(
            "type",
            ""
        )
    )

    semantic_class = str(
        hypothesis.get(
            "semantic_class",
            ""
        )
    )

    grounding = hypothesis.get(
        "geometric_grounding",
        {}
    )

    if not isinstance(
        grounding,
        dict
    ):

        grounding = {}

    try:

        density_delta = abs(
            float(
                grounding.get(
                    "density_delta",
                    0.0
                )
                or 0.0
            )
        )

    except (TypeError, ValueError):

        density_delta = 0.0

    score = (
        _bounded_number(
            hypothesis.get(
                "transformation_salience",
                0.0
            )
        )
        * 0.25
    )

    score += (
        _bounded_number(
            hypothesis.get(
                "explanatory_power",
                0.0
            )
        )
        * 0.25
    )

    score += (
        _bounded_number(
            hypothesis.get(
                "residual_reduction",
                0.0
            )
        )
        * 0.25
    )

    score += (
        _bounded_number(
            hypothesis.get(
                "confidence",
                0.0
            )
        )
        * 0.10
    )

    if primitive in TRANSFORMATION_PRIMITIVES:

        score += 0.30

    if semantic_class and semantic_class != "invariant":

        score += 0.20

    if "change" in hypothesis_type or "transformation" in hypothesis_type:

        score += 0.10

    if density_delta > 0:

        score += min(
            0.20,
            density_delta / 30.0
        )

    if (
        grid_changed
        and
        primitive in PRESERVATION_PRIMITIVES
    ):

        score -= 0.45

    return round(
        max(
            score,
            0.0
        ),
        4
    )


def transformation_candidate_concept(
    hypothesis
):

    if not isinstance(
        hypothesis,
        dict
    ):

        return "generic_transformation"

    primitive = hypothesis.get(
        "primitive"
    )

    operator_semantics = lookup_operator_semantics(
        primitive
    )

    if operator_semantics:

        operator_class = operator_semantics.get(
            "semantic_class"
        )

        operator_concept = operator_semantics.get(
            "semantic_concept",
            "generic_transformation"
        )

        if operator_class != "invariant":

            return operator_concept

    hypothesis_concept = lookup_hypothesis_concept(
        hypothesis.get(
            "type",
            ""
        )
    )

    if hypothesis_concept != "generic_transformation":

        return hypothesis_concept

    return operator_semantics.get(
        "semantic_concept",
        "generic_transformation"
    )


def transformation_candidate_role(
    hypothesis,
    concept,
    score
):

    primitive = hypothesis.get(
        "primitive"
    )

    if score >= 0.55 and concept in FRONTIER_TRANSFORMATION_CONCEPTS:

        return "primary_transformation"

    if concept in FRONTIER_TRANSFORMATION_CONCEPTS:

        return "latent_transformation"

    if primitive in PRESERVATION_PRIMITIVES:

        return "supporting_invariant"

    return "candidate_context"


def build_multi_transformation_graph(
    hypotheses,
    max_nodes=6
):

    nodes = []
    seen = set()

    for hypothesis in hypotheses or []:

        if not isinstance(
            hypothesis,
            dict
        ):

            continue

        score = hypothesis.get(
            "transformation_concept_score",
            0.0
        )

        concept = transformation_candidate_concept(
            hypothesis
        )

        role = transformation_candidate_role(
            hypothesis,
            concept,
            score
        )

        if (
            role == "candidate_context"
            and
            score < 0.25
        ):

            continue

        key = (
            concept,
            role
        )

        if key in seen:

            continue

        seen.add(
            key
        )

        compression_level = compression_level_for_concept(
            concept
        )

        nodes.append({
            "concept": concept,
            "role": role,
            "source_type": hypothesis.get(
                "type"
            ),
            "primitive": hypothesis.get(
                "primitive"
            ),
            "score": score,
            "confidence": hypothesis.get(
                "confidence",
                0.0
            ),
            "compressed_concept": compression_level.local_identity,
            "structural_identity": compression_level.structural_identity,
            "causal_identity": compression_level.causal_identity,
            "archetypal_identity": compression_level.archetypal_identity,
            "topology_signature": compression_level.topology_signature,
        })

    nodes = sorted(
        nodes,
        key=lambda item: (
            2
            if item.get("role") == "primary_transformation"
            else 1
            if item.get("role") == "latent_transformation"
            else 0,
            item.get("score", 0.0),
            item.get("confidence", 0.0),
        ),
        reverse=True,
    )[:max_nodes]

    edges = []

    for index, source in enumerate(
        nodes
    ):

        for target_index in range(
            index + 1,
            len(nodes)
        ):

            target = nodes[target_index]

            if source.get("role") == "primary_transformation":

                relation = (
                    "drives"
                    if target.get("role") == "latent_transformation"
                    else "constrained_by"
                )

            elif target.get("role") == "supporting_invariant":

                relation = "stabilized_by"

            else:

                relation = "co_occurs_with"

            edges.append({
                "source": source.get("concept"),
                "target": target.get("concept"),
                "relation": relation,
                "weight": round(
                    max(
                        source.get("score", 0.0),
                        0.1
                    )
                    *
                    max(
                        target.get("confidence", 0.0),
                        0.1
                    ),
                    4,
                ),
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "primary_transformation_count": sum(
            1
            for node in nodes
            if node.get("role") == "primary_transformation"
        ),
        "latent_transformation_count": sum(
            1
            for node in nodes
            if node.get("role") == "latent_transformation"
        ),
        "supporting_invariant_count": sum(
            1
            for node in nodes
            if node.get("role") == "supporting_invariant"
        ),
    }


def prioritize_transformation_concepts(
    hypotheses,
    grid_changed=False
):

    annotated = []

    for index, hypothesis in enumerate(
        hypotheses or []
    ):

        if not isinstance(
            hypothesis,
            dict
        ):

            continue

        concept_score = transformation_concept_score(
            hypothesis,
            grid_changed=grid_changed
        )

        hypothesis[
            "transformation_concept_score"
        ] = concept_score

        hypothesis[
            "transformation_discovery_state"
        ] = (
            "TRANSFORMATION_CONCEPT_DISCOVERED"
            if concept_score >= 0.55
            else "TRANSFORMATION_CONCEPT_WEAK"
        )

        annotated.append(
            (
                index,
                hypothesis
            )
        )

    return [
        hypothesis
        for index, hypothesis in sorted(
            annotated,
            key=lambda item: (
                item[1].get(
                    "transformation_concept_score",
                    0.0
                ),
                _bounded_number(
                    item[1].get(
                        "confidence",
                        0.0
                    )
                ),
                -item[0],
            ),
            reverse=True
        )
    ]


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

    if task_complexity < 0.20:

        return 1

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

    if task_complexity < 0.20:

        return {
            "allocated_depth_limit": 1,
            "regulated_depth": min(raw_depth, 1),
            "causal_density": 0.0,
            "average_confidence": 0.0,
            "entropy_risk": 0.0,
            "allocation_reason": "low_complexity_transformational_budget"
        }

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

    blackboard = cognitive_blackboard_from_context(
        context
    )

    graph_reasoning = (
        graph_reasoner
        .reason_about_placement(
            input_array,
            output_array,
            operation="duplicate_object"
        )
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

    active_budget = context.get(
        "current_reasoning_budget"
    )

    max_hypotheses = getattr(
        active_budget,
        "max_hypotheses",
        None
    )

    max_active_routes = getattr(
        active_budget,
        "max_active_routes",
        None
    )

    max_reasoning_depth = getattr(
        active_budget,
        "max_reasoning_depth",
        None
    )

    max_semantic_concepts = None

    if task_complexity < 0.20:

        max_hypotheses = (
            min(max_hypotheses, 2)
            if isinstance(max_hypotheses, int)
            else 2
        )

        max_active_routes = (
            min(max_active_routes, 2)
            if isinstance(max_active_routes, int)
            else 2
        )

        max_reasoning_depth = (
            min(max_reasoning_depth, 1)
            if isinstance(max_reasoning_depth, int)
            else 1
        )

        max_semantic_concepts = 3

    if max_reasoning_depth is not None:

        reasoning_depth_limit = min(
            reasoning_depth_limit,
            max(
                1,
                int(max_reasoning_depth)
            )
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

    object_centric_reasoning = (
        object_centric_reasoner
        .reason(
            input_objects=input_objects,
            output_objects=output_objects,
            hypotheses=hypotheses,
        )
    )

    hypotheses = object_centric_reasoning.get(
        "annotated_hypotheses",
        hypotheses,
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
            ),

            context.get(
                "current_meta_decision",
                {}
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

    object_centric_reasoning = (
        object_centric_reasoner
        .reason(
            input_objects=input_objects,
            output_objects=output_objects,
            hypotheses=hypotheses,
        )
    )

    hypotheses = object_centric_reasoning.get(
        "annotated_hypotheses",
        hypotheses,
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

    object_centric_reasoning = (
        object_centric_reasoner
        .reason(
            input_objects=input_objects,
            output_objects=output_objects,
            hypotheses=hypotheses,
        )
    )

    hypotheses = object_centric_reasoning.get(
        "annotated_hypotheses",
        hypotheses,
    )

    executable_hypotheses = (

        filter_executable_hypotheses(
            hypotheses
        )
    )

    grid_changed = not np.array_equal(
        input_array,
        output_array
    )

    executable_hypotheses = prioritize_transformation_concepts(
        executable_hypotheses,
        grid_changed=grid_changed
    )

    multi_transformation_graph = build_multi_transformation_graph(
        executable_hypotheses
    )

    transformation_concept_discovery_report = {
        "system": "transformation_concept_discovery_engine",
        "grid_changed": grid_changed,
        "candidate_count": len(
            executable_hypotheses
        ),
        "discovered_count": sum(
            1
            for hypothesis in executable_hypotheses
            if hypothesis.get(
                "transformation_discovery_state"
            ) == "TRANSFORMATION_CONCEPT_DISCOVERED"
        ),
        "multi_transformation_graph":
        multi_transformation_graph,
        "multi_transformation_node_count":
        multi_transformation_graph.get(
            "node_count",
            0
        ),
        "latent_transformation_count":
        multi_transformation_graph.get(
            "latent_transformation_count",
            0
        ),
        "supporting_invariant_count":
        multi_transformation_graph.get(
            "supporting_invariant_count",
            0
        ),
        "top_transformation_candidates": [
            {
                "type": hypothesis.get(
                    "type"
                ),
                "primitive": hypothesis.get(
                    "primitive"
                ),
                "concept": transformation_candidate_concept(
                    hypothesis
                ),
                "semantic_class": hypothesis.get(
                    "semantic_class"
                ),
                "transformation_concept_score": hypothesis.get(
                    "transformation_concept_score"
                ),
            }
            for hypothesis in executable_hypotheses[:5]
        ],
    }

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

    if max_reasoning_depth is not None:

        regulated_reasoning_depth = min(
            regulated_reasoning_depth,
            max(
                1,
                int(max_reasoning_depth)
            )
        )

        reasoning_depth_limit = min(
            reasoning_depth_limit,
            max(
                1,
                int(max_reasoning_depth)
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

    run_plan = context.get("authoritative_execution_plan")
    run_plan = run_plan if isinstance(run_plan, dict) else {}
    run_id = (
        run_plan.get("run_id")
        or context.get("run_id")
        or context.get("execution_id")
        or "current_run"
    )
    execution_plan_id = run_plan.get("execution_plan_id")
    task_id = context.get("task_path") or context.get("task_id") or "current_task"
    depth_limit_for_events = (
        max(1, int(max_reasoning_depth))
        if max_reasoning_depth is not None
        else regulated_reasoning_depth
    )
    requested_depth = max(raw_reasoning_depth, regulated_reasoning_depth)
    reasoning_depth_lifecycle_records = []
    for depth in range(1, requested_depth + 1):
        reasoning_depth_lifecycle_records.append({
            "run_id": run_id,
            "execution_plan_id": execution_plan_id,
            "task_id": task_id,
            "depth": depth,
            "state": "ATTEMPTED_REASONING_DEPTH",
            "source_stage": "inference_reasoning_depth_gate",
            "source_timestamp": str(datetime.utcnow()),
        })
        if depth <= depth_limit_for_events:
            reasoning_depth_lifecycle_records.append({
                "run_id": run_id,
                "execution_plan_id": execution_plan_id,
                "task_id": task_id,
                "depth": depth,
                "state": "REASONING_DEPTH_ENTRY_AUTHORIZED",
                "source_stage": "inference_reasoning_depth_gate",
                "source_timestamp": str(datetime.utcnow()),
            })
            reasoning_depth_lifecycle_records.append({
                "run_id": run_id,
                "execution_plan_id": execution_plan_id,
                "task_id": task_id,
                "depth": depth,
                "state": "REASONING_DEPTH_EXITED",
                "source_stage": "inference_reasoning_depth_gate",
                "source_timestamp": str(datetime.utcnow()),
            })
        else:
            reasoning_depth_lifecycle_records.append({
                "run_id": run_id,
                "execution_plan_id": execution_plan_id,
                "task_id": task_id,
                "depth": depth,
                "state": "DEPTH_ENTRY_BLOCKED_BY_BUDGET",
                "decision_reason": "maximum_reasoning_depth",
                "source_stage": "inference_reasoning_depth_gate",
                "source_timestamp": str(datetime.utcnow()),
            })

    if task_complexity < 0.20:

        recursive_report[
            "cognitive_complexity"
        ] = "low"

        recursive_report[
            "max_active_routes"
        ] = max_active_routes

        recursive_report[
            "max_semantic_concepts"
        ] = max_semantic_concepts

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

            executable_hypotheses,

            evidence_context=context
        )
    )

    if max_semantic_concepts is not None:

        semantic_abstractions = semantic_abstractions[
            :max_semantic_concepts
        ]

    semantic_graph = (

        semantic_abstraction_engine
        .build_semantic_graph(

            semantic_abstractions
        )
    )

    transformation_causal_graph = (
        semantic_graph.get(
            "transformation_causal_graph",
            {}
        )
    )

    transformation_causal_relations = (
        transformation_causal_graph.get(
            "edges",
            []
        )
        if isinstance(
            transformation_causal_graph,
            dict
        )
        else []
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
                "transformation_salience",
                0.0
            ),

            h.get(
                "explanatory_power",
                0.0
            ),

            h.get(
                "residual_reduction",
                0.0
            ),

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

    pre_budget_hypothesis_count = len(
        ranked_hypotheses
    )

    if max_hypotheses is not None:

        ranked_hypotheses = ranked_hypotheses[
            :max(
                1,
                int(max_hypotheses)
            )
        ]

    executable_hypotheses = ranked_hypotheses

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

    object_centric_arbitration_report = (
        execution_arbitration_report.get(
            "ARBITRATION_REPORT",
            object_centric_reasoning.get(
                "ARBITRATION_REPORT",
                {},
            ),
        )
    )

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

    with blackboard.transaction():

        blackboard.synchronize_from_graph_reasoning(
            graph_reasoning
        )

        blackboard.synchronize_from_world_model(
            anticipation_report
        )

        synthesized_program = (
            blackboard.synthesized_program
            or
            synthesized_program
        )

        execution_plan = (

            planning_engine
            .build_plan(

                synthesized_program
            )
        )

        execution_plan = blackboard.synchronize_execution_plan(
            execution_plan
        )

    blackboard.assert_synchronized()

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

        "TRANSFORMATION_CAUSAL_GRAPH":
        transformation_causal_graph,

        "causal_order":
        (
            transformation_causal_graph.get(
                "causal_order",
                []
            )
            if isinstance(
                transformation_causal_graph,
                dict
            )
            else []
        ),

        "primary_causal_chain":
        (
            transformation_causal_graph.get(
                "primary_causal_chain",
                []
            )
            if isinstance(
                transformation_causal_graph,
                dict
            )
            else []
        ),

        "causal_chains":
        (
            transformation_causal_graph.get(
                "causal_chains",
                []
            )
            if isinstance(
                transformation_causal_graph,
                dict
            )
            else []
        ),

        "causal_relations":
        transformation_causal_relations,

        "causal_relation_count":
        len(
            transformation_causal_relations
        ),

        "OBJECT_CHANGE_REPORT":
        object_centric_reasoning.get(
            "OBJECT_CHANGE_REPORT",
            [],
        ),

        "TRANSFORMATION_SALIENCE_REPORT":
        object_centric_reasoning.get(
            "TRANSFORMATION_SALIENCE_REPORT",
            {},
        ),

        "ARBITRATION_REPORT":
        object_centric_arbitration_report,

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

    selected_route_names = list(
        context.get("enabled_tools", [])
        if isinstance(context.get("enabled_tools", []), (list, tuple, set))
        else []
    )
    if not selected_route_names:
        selected_route_names = list(routing_report.get("active_routes", []) or [])
    route_limit_for_events = (
        max(1, int(max_active_routes))
        if max_active_routes is not None
        else len(selected_route_names)
    )
    route_selection_records = [
        {
            "route_id": str(route),
            "route_source": "governed_tool_route_selection",
            "route_rank": index + 1,
            "route_score": None,
            "route_active_state": False,
        }
        for index, route in enumerate(selected_route_names)
    ]
    route_lifecycle_records = []
    for index, route in enumerate(route_selection_records):
        route_id = route["route_id"]
        if index < route_limit_for_events:
            route_lifecycle_records.append({
                "run_id": run_id,
                "execution_plan_id": execution_plan_id,
                "task_id": task_id,
                "route_id": route_id,
                "state": "ACTIVE_ROUTE",
                "event_id": f"{route_id}:active",
                "source_stage": "inference_route_admission_gate",
                "source_timestamp": str(datetime.utcnow()),
            })
        else:
            route_lifecycle_records.append({
                "run_id": run_id,
                "execution_plan_id": execution_plan_id,
                "task_id": task_id,
                "route_id": route_id,
                "state": "DEFERRED_BY_BUDGET",
                "event_id": f"{route_id}:deferred",
                "decision_reason": "maximum_active_routes",
                "source_stage": "inference_route_admission_gate",
                "source_timestamp": str(datetime.utcnow()),
            })
    for route in route_selection_records[:route_limit_for_events]:
        route_id = route["route_id"]
        route_lifecycle_records.append({
            "run_id": run_id,
            "execution_plan_id": execution_plan_id,
            "task_id": task_id,
            "route_id": route_id,
            "state": "RELEASED_ROUTE",
            "event_id": f"{route_id}:released",
            "source_stage": "inference_route_admission_gate",
            "source_timestamp": str(datetime.utcnow()),
        })

    if max_active_routes is not None:

        active_routes = routing_report.get(
            "active_routes",
            []
        )

        route_limit = max(
            1,
            int(max_active_routes)
        )

        if len(active_routes) > route_limit:

            terminated_routes = active_routes[
                route_limit:
            ]

            active_routes = active_routes[
                :route_limit
            ]

            for route in terminated_routes:

                if route in routing_plan:

                    routing_plan[
                        route
                    ] = False

            routing_report = {

                **routing_report,

                "active_routes":
                active_routes,

                "route_count":
                len(active_routes),

                "routing_plan":
                routing_plan,

                "max_active_routes":
                max_active_routes,

                "terminated_routes":
                terminated_routes,

                "budget_enforced":
                True,
            }

    budget_context = {
        **context,
        "run_id": run_id,
        "task_id": task_id,
        "route_selection_report": {
            "available_routes": route_selection_records,
            "candidate_routes": route_selection_records,
            "active_routes": route_selection_records,
        },
        "route_lifecycle_records": route_lifecycle_records,
        "reasoning_depth_lifecycle_records": reasoning_depth_lifecycle_records,
        "planned_reasoning_depth": requested_depth,
        "available_graph_depth": raw_reasoning_depth,
    }
    receipt_budget = active_budget
    if not isinstance(receipt_budget, dict):
        cognitive_budget_report = context.get("cognitive_budget_report", {})
        if isinstance(cognitive_budget_report, dict):
            receipt_budget = {
                "budget_source": (
                    cognitive_budget_report.get("runtime_budget_source")
                    or cognitive_budget_report.get("budget_source")
                    or "cognitive_budget_report"
                ),
                "max_active_routes": cognitive_budget_report.get("max_active_routes"),
                "max_reasoning_depth": cognitive_budget_report.get("max_reasoning_depth"),
                "max_dependency_depth": cognitive_budget_report.get("max_dependency_depth"),
                "max_hypotheses": cognitive_budget_report.get("max_hypotheses"),
                "active_route_limit_scope": "TASK_CONCURRENT_ACTIVE_ROUTES",
                "reasoning_depth_limit_scope": "TASK_GOVERNED_REASONING_DEPTH",
            }
    runtime_budget_enforcement_report = runtime_budget_enforcer.build_receipt(
        budget=receipt_budget,
        context=budget_context,
        execution_plan_id=execution_plan_id,
        route_records=route_selection_records,
        nodes=[
            {
                "materialization_state": "MATERIALIZED",
            }
            for _ in route_selection_records[:route_limit_for_events]
        ],
    )
    recursive_report["runtime_budget_enforcement_report"] = (
        runtime_budget_enforcement_report
    )
    recursive_report["route_lifecycle_records"] = route_lifecycle_records
    recursive_report["reasoning_depth_lifecycle_records"] = (
        reasoning_depth_lifecycle_records
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

    context[
        "candidate_origin_report"
    ] = build_candidate_origin_report(
        producer_component="inference_stage",
        producer_operation_id="inference_execution",
        candidate_id="current_candidate",
        transformation_source="execution_result",
        prediction_source="execution_result.output_grid",
        source_report=inference_report,
        run_id=context.get("run_id"),
        task_id=context.get("task_id") or context.get("task_path"),
    )

    context[
        "CANDIDATE_ORIGIN_REPORT"
    ] = context[
        "candidate_origin_report"
    ]

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
        "graph_reasoning"
    ] = graph_reasoning

    context[
        "placement_rules"
    ] = blackboard.placement_rules

    context[
        "position_rule"
    ] = blackboard.position_rule

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

    transformation_localization = (
        anticipation_report.get(
            "transformation_localization",
            {},
        )
    )

    context[
        "transformation_localization"
    ] = transformation_localization

    context[
        "localization_ready"
    ] = transformation_localization.get(
        "localization_ready",
        False,
    )

    context[
        "localized_step_count"
    ] = transformation_localization.get(
        "localized_step_count",
        0,
    )

    context[
        "cognitive_blackboard_state"
    ] = blackboard.snapshot()

    context[
        "hypothesis_arbitration_report"
    ] = execution_arbitration_report

    context[
        "OBJECT_CHANGE_REPORT"
    ] = object_centric_reasoning.get(
        "OBJECT_CHANGE_REPORT",
        [],
    )

    context[
        "TRANSFORMATION_SALIENCE_REPORT"
    ] = object_centric_reasoning.get(
        "TRANSFORMATION_SALIENCE_REPORT",
        {},
    )

    context[
        "ARBITRATION_REPORT"
    ] = object_centric_arbitration_report

    context[
        "object_centric_reasoning"
    ] = object_centric_reasoning

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

    context["TRANSFORMATION_CAUSAL_GRAPH"] = (
        transformation_causal_graph
    )

    context["transformation_causal_graph"] = (
        transformation_causal_graph
    )

    context["causal_order"] = (
        transformation_causal_graph.get(
            "causal_order",
            []
        )
        if isinstance(
            transformation_causal_graph,
            dict
        )
        else []
    )

    context["primary_causal_chain"] = (
        transformation_causal_graph.get(
            "primary_causal_chain",
            []
        )
        if isinstance(
            transformation_causal_graph,
            dict
        )
        else []
    )

    context["causal_chains"] = (
        transformation_causal_graph.get(
            "causal_chains",
            []
        )
        if isinstance(
            transformation_causal_graph,
            dict
        )
        else []
    )

    context["causal_relations"] = (
        transformation_causal_relations
    )

    context["transformation_concept_discovery_report"] = (
        transformation_concept_discovery_report
    )

    context["multi_transformation_graph"] = (
        multi_transformation_graph
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

    context["route_lifecycle_records"] = (
        route_lifecycle_records
    )

    context["reasoning_depth_lifecycle_records"] = (
        reasoning_depth_lifecycle_records
    )

    context["runtime_budget_enforcement_report"] = (
        runtime_budget_enforcement_report
    )

    context["RUNTIME_BUDGET_ENFORCEMENT_REPORT"] = (
        runtime_budget_enforcement_report
    )

    context["hypothesis_budget_report"] = {
        "max_hypotheses": max_hypotheses,
        "max_active_routes": max_active_routes,
        "max_semantic_concepts": max_semantic_concepts,
        "pre_budget_hypothesis_count": pre_budget_hypothesis_count,
        "post_budget_hypothesis_count": len(ranked_hypotheses),
        "max_reasoning_depth": max_reasoning_depth,
        "regulated_reasoning_depth": regulated_reasoning_depth,
    }

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
            inference_report,

            transformation_concept_discovery_report=
            transformation_concept_discovery_report
        )

    except Exception:

        pass

    return context
