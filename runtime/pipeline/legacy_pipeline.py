# ============================================
# NEXRYN ADAPTIVE COGNITIVE PIPELINE
# REFACTORED STABLE ARCHITECTURE
# ============================================

from datetime import datetime
import hashlib
import json
import time

# ============================================
# CORE
# ============================================

from runtime.kernel.runtime_kernel import RuntimeKernel
from runtime.state.runtime_state import RuntimeState
from runtime.scheduler.runtime_scheduler import RuntimeScheduler
from runtime.dependency import (
    DependencyChainExecutor,
    DependencyActivationTrace,
    dependency_activation_manager,
    dependency_activation_enforcer,
)
from runtime.context.context_integrity_guard import context_integrity_guard
from runtime.process import ProcessSemanticEngine

# ============================================
# GOVERNANCE
# ============================================

from runtime.governance import (
    runtime_governor,
    strategic_governor,
    strategy_garbage_collector,
    runtime_stability_manager,
    lineage_pruning_engine,
    governance_memory_balancer,
    cognitive_resource_allocator,
    recursive_governance_controller,
    cognitive_governance_engine,
    cognitive_identity_layer,
    governance_cache
)
from runtime.governance.locked_truth_fastpath import LockedTruthFastPath

from runtime.learning.saturation_detector import saturation_detector
from runtime.learning.saturation_controller import (
    learning_saturation_controller,
)
from runtime.reporting import CompactReportBuilder
from runtime.cache import CacheManager, concept_lifecycle_cache
from runtime.observability import (
    build_runtime_topology_observation_report,
    context_delta as build_topology_context_delta,
    persist_runtime_topology_observation_report,
)
from runtime.planning.execution_profile import build_execution_profile
from runtime.provenance import build_candidate_origin_report
from runtime.truth import (
    truth_lifecycle_synchronizer,
    promotion_engine,
    truth_eligibility_engine,
    truth_candidate_engine,
    truth_commit_engine,
    truth_registry,
    contextual_truth_engine,
)
from runtime.cognition import AdaptiveReuseEngine
from runtime.profiling.metric_bridge import runtime_metric_bridge
from runtime.telemetry import (
    MetricIntegrityValidator,
    RuntimeTelemetryValidator,
    metric_authority_registry,
)

# ============================================
# MEMORY
# ============================================

from runtime.memory import (
    WorkingMemory,
    EpisodicMemory,
    SemanticMemory,
    LongTermMemory,
    PersistentCognitiveMemory,
    persistent_cognitive_memory,
    memory_consolidation_engine,
    hierarchical_memory_compression,
    memory_retrieval_engine,
    semantic_memory_retriever,
    semantic_cluster_engine,
    MemoryManager,
    MemoryRouter,
    semantic_experience_index,
    hierarchical_memory_architecture,
    memory_compression_runtime,
    horizon_memory_manager
)

from runtime.attention import (
    attention_kernel
)

# ============================================
# CONTEXT
# ============================================

from runtime.context import (
    context_manager,
    context_governor,
    context_delta_engine,
    context_bus,
    context_layer_manager,
    context_router,
    context_importance_engine,
    context_compression_engine,
    context_pruning_engine,
    context_decay_engine,
    context_state_hasher,
    recursive_depth_governor,
    recursive_loop_detector,
    cognitive_budget_manager,
    context_health_monitor,
    semantic_context_graph,
    semantic_context_retriever,
    hierarchical_context_consolidator,
    context_consolidation_engine,
    context_registry,
    context_reuse_engine,
    semantic_context_builder,
    context_hierarchy_engine
)

# ============================================
# SYNTHESIS
# ============================================

from runtime.synthesis import (
    program_synthesis_engine,
    execution_plan_builder,
    adaptive_execution_engine
)

# ============================================
# REASONING
# ============================================

from runtime.reasoning import (
    reasoning_orchestrator,
    spatial_translation_engine,
    spatial_reasoning_engine,
    spatial_abstraction_engine,
    analogical_reasoning_engine,
    causal_reasoning_engine,
    symbolic_reasoning_engine,
    recursive_reasoning_engine,
    hypothesis_arbitration_engine,
    cognitive_pressure_engine
)
from runtime.reasoning.dependency_activation_policy import (
    explain_dependency_link_usage,
)
from runtime.reasoning.truth_activation_policy import evaluate_truth_activation

# ============================================
# EXECUTIVE
# ============================================

from runtime.executive.executive_brain import ExecutiveBrain

from runtime.executive import (
    executive_arbitration_runtime,
    cognitive_attention_router,
    adaptive_executive_hierarchy,
    cognitive_scheduler
)

# ============================================
# OPTIMIZATION
# ============================================

from runtime.optimization import (
    autonomous_self_optimizer,
    cognitive_load_balancer,
    recursive_depth_regulator,
    semantic_energy_manager,
    adaptive_exploration_controller,
    runtime_stability_monitor,
    optimization_policy_engine,
    self_regulation_engine,
    optimization_feedback_loop
)

from runtime.optimization import (
    cognitive_energy_economy
)

from runtime.semantics import (
    safe_concept_folding_engine,
    semantic_pointer_system,
    concept_schema_validator,
)

from runtime.semantic import (
    semantic_activation_graph
)

from runtime.identity import (
    identity_core
)

from runtime.latent import (
    latent_reservoir
)

from runtime.entropy import (
    cognitive_entropy_engine
)

from core.goals import (
    goal_manager
)

from core.governance_compression import (
    governance_kernel
)

from core.epistemic_decision_engine import (
    epistemic_decision_engine
)
from runtime.cross_task_replication_collector import (
    CrossTaskReplicationCollector,
)

from runtime.semantic_drift_monitor import (
    semantic_drift_monitor
)

from core.cognitive_health import (
    cognitive_physician_engine
)

from core.cognitive_pharmacy import (
    cognitive_pharmacy_engine
)

from core.cognitive_genetics import (
    cognitive_dna_engine
)

from core.governance import (
    constitutional_runtime
)

from core.civilization import (
    constitutional_memory,
    semantic_court,
    civilizational_policy_engine,
    identity_continuity_engine,
    cognitive_immune_engine,
    semantic_citizenship_registry,
    constitutional_rehearsal_engine,
    semantic_homeostasis,
    meta_constitution
)

from core.cognitive_kernel import (
    cognitive_kernel_scheduler
)

from core.concept_lifecycle import (
    concept_lifecycle_manager
)

from core.events import (
    cognitive_event_bus
)

from core.immunity import (
    cognitive_immune_system_v2
)

from core.cognitive_security import (
    semantic_firewall
)

from core.trust_system import (
    adaptive_permissioning
)

from core.rehearsal import (
    causal_rehearsal
)

from core.semantic_legitimacy import (
    semantic_legitimacy_engine
)

from core.constructive_reasoning import (
    adaptive_discovery
)

from core.evolutionary_memory import (
    evolutionary_memory
)

from core.evolutionary_graveyard import (
    evolutionary_graveyard
)

from core.truth_graveyard_synchronization import (
    truth_graveyard_synchronizer
)

from core.ontological_stability import (
    ontological_boundary_system
)

from core.existential_economics import (
    cognitive_existential_economics
)

from core.existential_homeostasis import (
    existential_homeostasis_system
)

from core.existential_pressure import (
    existential_pressure_management
)

from core.adaptive_equilibrium import (
    adaptive_equilibrium_architecture
)

from core.hybrid_governance import (
    hybrid_governance_architecture
)

from core.recursive_reflective_governance import (
    recursive_reflective_governance
)

from core.existential_governance import (
    existential_governance_core
)

from core.judicial_cognition import (
    judicial_cognitive_runtime
)

from core.cognitive_constitution import (
    cognitive_constitution_layer
)

from core.ecology import (
    cognitive_ecology
)

from core.homeostasis import (
    cognitive_homeostasis
)

from core.cognition import (
    entropy_regulator,
    concept_fusion_engine,
    stability_field,
    identity_reasoner,
    concept_lineage,
    recursive_guardian,
    cognitive_immune_system,
    semantic_physics,
    semantic_field_dynamics,
    semantic_spine
)

from core.natural_selection import (
    cognitive_natural_selection
)

from core.extinction_engine import (
    extinction_engine
)

from core.evolution import (
    trait_recovery_engine
)

from core.identity import (
    identity_stability_core,
    identity_continuity_guardian,
    cognitive_spine_stabilizer
)

from core.memory import (
    memory_compression_layer
)

from core.sandbox import (
    evolution_sandbox
)

from core.reality import (
    cognitive_physics_engine
)

from core.metacognition import (
    meta_cognitive_executive
)

from core.self_model import (
    recursive_self_model
)

from core.semantic_os import (
    semantic_operating_system
)

from core.world_model import (
    causal_world_simulator
)

from runtime.stability import (
    cognitive_stability_infrastructure,
    adaptive_semantic_control,
    controlled_safe_novelty,
    cognitive_operating_system_layer,
    distributed_cognitive_execution,
    distributed_semantic_execution_fabric,
    cognitive_thermodynamics
)

# ============================================
# PLANNING
# ============================================

from runtime.planning import (
    planning_engine,
    autonomous_runtime_planner,
    autonomous_cognitive_planner,
    task_complexity_analyzer,
    cognitive_cost_estimator,
    runtime_profile_manager,
    cognitive_budget_engine,
    tool_selection_engine,
    early_exit_controller,
    CognitiveCacheManager,
    cognitive_cache_manager,
    cache_invalidation_engine,
    performance_optimizer,
    runtime_metrics_collector,
    runtime_finalization_optimizer
)

from runtime.routing import (
    pre_reasoning_router,
)
from runtime.budget.deep_mode_budget_manager import (
    deep_mode_budget_manager,
)

from runtime.profiling import (
    performance_reporter,
    telemetry,
)

from runtime.self_repair import (
    self_repair_engine,
)

from runtime.security import (
    execution_authority_guard,
    security_reporter,
)

from runtime.execution import (
    execution_dispatcher,
    execution_planner,
)

from runtime.world_governance import (
    cognitive_budget_controller,
    incentive_reporter,
    world_governance_kernel,
)

from runtime.knowledge_optimization import (
    knowledge_reuse_gate,
    knowledge_optimization_reporter,
    strategy_reuse_engine as knowledge_strategy_reuse_engine,
)

# ============================================
# META
# ============================================

from runtime.meta import (
    meta_cognition_engine,
    meta_selection_engine,
    meta_controller_engine,
    meta_supervisor,
    self_rewrite_engine,
    cognitive_genome,
    cognitive_ecosystem,
    cognitive_society,
    civilization_engine,
    consciousness_engine,
    curiosity_engine,
    discovery_engine,
    abstraction_engine,
    knowledge_expansion_engine,
    autonomous_research_engine,
    adaptive_strategy_injector
)

from runtime.motivation import (
    motivation_system
)

# ============================================
# STAGES
# ============================================

from runtime.stages import (
    task_loading_stage,
    grid_analysis_stage,
    object_detection_stage,
    pattern_rule_stage,
    inference_stage,
    transformation_stage,
    evaluation_stage,
    self_improvement_stage,
    NEXRYN_STAGE_SEQUENCE,
    NEXRYN_STAGE_PRIORITIES,
    NEXRYN_STAGE_CATEGORIES,
    NEXRYN_STAGE_GOVERNANCE
)


# ============================================
# PIPELINE
# ============================================

class AdaptiveCognitivePipeline:

    # ========================================
    # INITIALIZATION
    # ========================================

    def __init__(self, epistemic_engine=None):

        self.runtime = RuntimeState()
        self.kernel = RuntimeKernel()
        self.scheduler = RuntimeScheduler()
        self.dependency_chain_executor = DependencyChainExecutor()
        self.process_semantic_engine = ProcessSemanticEngine()
        self.task_complexity_analyzer = task_complexity_analyzer
        self.cognitive_cost_estimator = cognitive_cost_estimator
        self.runtime_profile_manager = runtime_profile_manager
        self.cognitive_budget_engine = cognitive_budget_engine
        self.tool_selection_engine = tool_selection_engine
        self.early_exit_controller = early_exit_controller
        self.cognitive_cache_manager = CognitiveCacheManager()
        self.adaptive_cache_manager = CacheManager(auto_migrate=False)
        self.adaptive_reuse_engine = AdaptiveReuseEngine(
            cache_manager=self.adaptive_cache_manager,
        )
        self.governance_cache = governance_cache
        self.locked_truth_fastpath = LockedTruthFastPath()
        self.learning_saturation_detector = saturation_detector
        self.cache_invalidation_engine = cache_invalidation_engine
        self.performance_optimizer = performance_optimizer
        self.runtime_metrics_collector = runtime_metrics_collector
        self.runtime_finalization_optimizer = runtime_finalization_optimizer
        self.performance_reporter = performance_reporter
        self.compact_report_builder = CompactReportBuilder()
        self.pre_reasoning_router = pre_reasoning_router
        self.context_registry = context_registry
        self.context_reuse_engine = context_reuse_engine
        self.context_reuse_engine.context_registry = self.context_registry
        self.context_reuse_engine.cache_manager = self.adaptive_cache_manager
        self.semantic_context_builder = semantic_context_builder
        self.context_hierarchy_engine = context_hierarchy_engine
        self.contextual_truth_engine = contextual_truth_engine
        self.promotion_engine = promotion_engine
        self.truth_eligibility_engine = truth_eligibility_engine
        self.truth_candidate_engine = truth_candidate_engine
        self.truth_commit_engine = truth_commit_engine
        self.truth_registry = truth_registry
        self.telemetry = telemetry
        self.self_repair_engine = self_repair_engine
        self.execution_authority_guard = execution_authority_guard
        self.security_reporter = security_reporter
        self.world_governance_kernel = world_governance_kernel
        self.cognitive_budget_controller = cognitive_budget_controller
        self.incentive_reporter = incentive_reporter
        self.knowledge_reuse_gate = knowledge_reuse_gate
        self.knowledge_strategy_reuse_engine = knowledge_strategy_reuse_engine
        self.knowledge_optimization_reporter = knowledge_optimization_reporter
        self.profiling_enabled = False
        self.profile_level = "minimal"
        self.requested_budget_mode = None
        self.run_scoped_budget_authority_context = {}
        self.execution_profile = build_execution_profile("adaptive")
        self.post_success_mode = "fast"
        self.cached_pipeline_result = None
        self.reasoning_budget = self._default_reasoning_budget()
        self.dependency_chain_cache = {}
        self.process_semantic_cache = {}
        self.performance_counters = self._new_performance_counters()

        # ====================================
        # EXECUTION STATE
        # ====================================

        self.runtime_safe_mode = False
        self.runtime_initialized = True
        self.runtime_failure_count = 0
        self.runtime_recovery_cycles = 0

        self.stage_execution_history = []
        self.completed_stages = []
        self.failed_stages = []

        # ====================================
        # MEMORY
        # ====================================

        self.working_memory = WorkingMemory()
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        self.long_term_memory = LongTermMemory()

        self.persistent_memory = (
            persistent_cognitive_memory
        )

        self.memory_consolidation_engine = (
            memory_consolidation_engine
        )

        self.hierarchical_memory_compression = (
            hierarchical_memory_compression
        )

        self.memory_retrieval_engine = (
            memory_retrieval_engine
        )

        self.semantic_memory_retriever = (
            semantic_memory_retriever
        )

        self.semantic_cluster_engine = (
            semantic_cluster_engine
        )

        self.hierarchical_memory_architecture = (
            hierarchical_memory_architecture
        )

        self.memory_compression_runtime = (
            memory_compression_runtime
        )

        self.horizon_memory_manager = (
            horizon_memory_manager
        )

        self.attention_kernel = (
            attention_kernel
        )

        self.memory_manager = MemoryManager()
        self.memory_router = MemoryRouter()

        # ====================================
        # CONTEXT
        # ====================================

        self.context_manager = context_manager
        self.context_governor = context_governor
        self.context_delta_engine = context_delta_engine
        self.context_bus = context_bus
        self.context_layer_manager = context_layer_manager
        self.context_router = context_router
        self.context_importance_engine = context_importance_engine
        self.context_compression_engine = context_compression_engine
        self.context_pruning_engine = context_pruning_engine
        self.context_decay_engine = context_decay_engine
        self.context_state_hasher = context_state_hasher
        self.recursive_depth_governor = recursive_depth_governor
        self.recursive_loop_detector = recursive_loop_detector
        self.cognitive_budget_manager = cognitive_budget_manager
        self.context_health_monitor = context_health_monitor
        self.semantic_context_graph = semantic_context_graph
        self.semantic_context_retriever = semantic_context_retriever
        self.hierarchical_context_consolidator = (
            hierarchical_context_consolidator
        )
        self.context_consolidation_engine = (
            context_consolidation_engine
        )

        # ====================================
        # REASONING
        # ====================================

        self.reasoning_orchestrator = (
            reasoning_orchestrator
        )

        self.spatial_translation_engine = (
            spatial_translation_engine
        )

        self.spatial_reasoning_engine = (
            spatial_reasoning_engine
        )

        self.spatial_abstraction_engine = (
            spatial_abstraction_engine
        )

        self.analogical_reasoning_engine = (
            analogical_reasoning_engine
        )

        self.causal_reasoning_engine = (
            causal_reasoning_engine
        )

        self.symbolic_reasoning_engine = (
            symbolic_reasoning_engine
        )

        self.recursive_reasoning_engine = (
            recursive_reasoning_engine
        )

        self.hypothesis_arbitration_engine = (
            hypothesis_arbitration_engine
        )

        self.cognitive_pressure_engine = (
            cognitive_pressure_engine
        )

        # ====================================
        # SYNTHESIS
        # ====================================

        self.program_synthesis_engine = (
            program_synthesis_engine
        )

        self.execution_plan_builder = (
            execution_plan_builder
        )

        self.adaptive_execution_engine = (
            adaptive_execution_engine
        )

        # ====================================
        # GOVERNANCE
        # ====================================

        self.runtime_governor = runtime_governor
        self.strategic_governor = strategic_governor

        self.strategy_garbage_collector = (
            strategy_garbage_collector
        )

        self.runtime_stability_manager = (
            runtime_stability_manager
        )

        self.lineage_pruning_engine = (
            lineage_pruning_engine
        )

        self.governance_memory_balancer = (
            governance_memory_balancer
        )

        self.cognitive_resource_allocator = (
            cognitive_resource_allocator
        )

        self.recursive_governance_controller = (
            recursive_governance_controller
        )

        self.cognitive_governance_engine = (
            cognitive_governance_engine
        )

        self.cognitive_identity_layer = (
            cognitive_identity_layer
        )

        # ====================================
        # EXECUTIVE
        # ====================================

        self.executive_brain = ExecutiveBrain()

        self.executive_arbitration_runtime = (
            executive_arbitration_runtime
        )

        self.cognitive_attention_router = (
            cognitive_attention_router
        )

        self.adaptive_executive_hierarchy = (
            adaptive_executive_hierarchy
        )

        self.cognitive_scheduler = (
            cognitive_scheduler
        )

        # ====================================
        # OPTIMIZATION
        # ====================================

        self.autonomous_self_optimizer = (
            autonomous_self_optimizer
        )

        self.cognitive_load_balancer = (
            cognitive_load_balancer
        )

        self.recursive_depth_regulator = (
            recursive_depth_regulator
        )

        self.semantic_energy_manager = (
            semantic_energy_manager
        )

        self.adaptive_exploration_controller = (
            adaptive_exploration_controller
        )

        self.runtime_stability_monitor = (
            runtime_stability_monitor
        )

        self.optimization_policy_engine = (
            optimization_policy_engine
        )

        self.self_regulation_engine = (
            self_regulation_engine
        )

        self.optimization_feedback_loop = (
            optimization_feedback_loop
        )

        self.cognitive_energy_economy = (
            cognitive_energy_economy
        )

        self.safe_concept_folding_engine = (
            safe_concept_folding_engine
        )

        self.semantic_pointer_system = (
            semantic_pointer_system
        )

        self.semantic_activation_graph = (
            semantic_activation_graph
        )

        self.identity_core = (
            identity_core
        )

        self.latent_reservoir = (
            latent_reservoir
        )

        self.cognitive_entropy_engine = (
            cognitive_entropy_engine
        )

        self.cognitive_stability_infrastructure = (
            cognitive_stability_infrastructure
        )

        self.adaptive_semantic_control = (
            adaptive_semantic_control
        )

        self.controlled_safe_novelty = (
            controlled_safe_novelty
        )

        self.cognitive_operating_system_layer = (
            cognitive_operating_system_layer
        )

        self.distributed_cognitive_execution = (
            distributed_cognitive_execution
        )

        self.distributed_semantic_execution_fabric = (
            distributed_semantic_execution_fabric
        )

        self.cognitive_thermodynamics = (
            cognitive_thermodynamics
        )

        self.cognitive_kernel_scheduler = (
            cognitive_kernel_scheduler
        )

        self.cognitive_event_bus = (
            cognitive_event_bus
        )

        self.identity_stability_core = (
            identity_stability_core
        )

        self.identity_continuity_guardian = (
            identity_continuity_guardian
        )

        self.cognitive_spine_stabilizer = (
            cognitive_spine_stabilizer
        )

        self.semantic_physics = (
            semantic_physics
        )

        self.semantic_field_dynamics = (
            semantic_field_dynamics
        )

        self.semantic_spine = (
            semantic_spine
        )

        self.memory_compression_layer = (
            memory_compression_layer
        )

        self.evolution_sandbox = (
            evolution_sandbox
        )

        self.cognitive_physics_engine = (
            cognitive_physics_engine
        )

        self.concept_lifecycle_manager = (
            concept_lifecycle_manager
        )

        self.governance_kernel = (
            governance_kernel
        )

        self.epistemic_decision_engine = (
            epistemic_engine
            or epistemic_decision_engine
        )

        cognition_layer = (
            self.epistemic_decision_engine
            .cognition_layer
        )

        self.cross_task_replication_collector = (
            CrossTaskReplicationCollector(
                cognition_layer.knowledge_replication_ledger,
                cognition_layer.evidence_registry,
                cognition_layer.knowledge_generalization_engine,
            )
        )

        self.semantic_drift_monitor = (
            semantic_drift_monitor
        )

        self.cognitive_physician_engine = (
            cognitive_physician_engine
        )

        self.cognitive_pharmacy_engine = (
            cognitive_pharmacy_engine
        )

        self.cognitive_dna_engine = (
            cognitive_dna_engine
        )

        self.goal_manager = (
            goal_manager
        )

        self.constitutional_runtime = (
            constitutional_runtime
        )

        self.constitutional_memory = (
            constitutional_memory
        )

        self.semantic_court = (
            semantic_court
        )

        self.civilizational_policy_engine = (
            civilizational_policy_engine
        )

        self.identity_continuity_engine = (
            identity_continuity_engine
        )

        self.cognitive_immune_engine = (
            cognitive_immune_engine
        )

        self.semantic_citizenship_registry = (
            semantic_citizenship_registry
        )

        self.constitutional_rehearsal_engine = (
            constitutional_rehearsal_engine
        )

        self.semantic_homeostasis = (
            semantic_homeostasis
        )

        self.meta_constitution = (
            meta_constitution
        )

        self.recursive_self_model = (
            recursive_self_model
        )

        self.meta_cognitive_executive = (
            meta_cognitive_executive
        )

        self.causal_world_simulator = (
            causal_world_simulator
        )

        self.cognitive_immune_system_v2 = (
            cognitive_immune_system_v2
        )

        self.semantic_firewall = (
            semantic_firewall
        )

        self.adaptive_permissioning = (
            adaptive_permissioning
        )

        self.causal_rehearsal = (
            causal_rehearsal
        )

        self.semantic_legitimacy_engine = (
            semantic_legitimacy_engine
        )

        self.adaptive_discovery = (
            adaptive_discovery
        )

        self.evolutionary_memory = (
            evolutionary_memory
        )

        self.evolutionary_graveyard = (
            evolutionary_graveyard
        )

        self.truth_graveyard_synchronizer = (
            truth_graveyard_synchronizer
        )

        self.ontological_boundary_system = (
            ontological_boundary_system
        )

        self.cognitive_existential_economics = (
            cognitive_existential_economics
        )

        self.existential_homeostasis_system = (
            existential_homeostasis_system
        )

        self.existential_pressure_management = (
            existential_pressure_management
        )

        self.adaptive_equilibrium_architecture = (
            adaptive_equilibrium_architecture
        )

        self.hybrid_governance_architecture = (
            hybrid_governance_architecture
        )

        self.recursive_reflective_governance = (
            recursive_reflective_governance
        )

        self.existential_governance_core = (
            existential_governance_core
        )

        self.judicial_cognitive_runtime = (
            judicial_cognitive_runtime
        )

        self.cognitive_constitution_layer = (
            cognitive_constitution_layer
        )

        self.cognitive_ecology = (
            cognitive_ecology
        )

        self.cognitive_homeostasis = (
            cognitive_homeostasis
        )

        self.entropy_regulator = (
            entropy_regulator
        )

        self.concept_fusion_engine = (
            concept_fusion_engine
        )

        self.stability_field = (
            stability_field
        )

        self.identity_reasoner = (
            identity_reasoner
        )

        self.concept_lineage = (
            concept_lineage
        )

        self.recursive_guardian = (
            recursive_guardian
        )

        self.cognitive_immune_system = (
            cognitive_immune_system
        )

        self.cognitive_natural_selection = (
            cognitive_natural_selection
        )

        self.extinction_engine = (
            extinction_engine
        )

        self.trait_recovery_engine = (
            trait_recovery_engine
        )

        self.semantic_operating_system = (
            semantic_operating_system
        )

        # ====================================
        # PLANNING
        # ====================================

        self.planning_engine = planning_engine

        self.autonomous_runtime_planner = (
            autonomous_runtime_planner
        )

        self.autonomous_cognitive_planner = (
            autonomous_cognitive_planner
        )

        # ====================================
        # META
        # ====================================

        self.meta_cognition_engine = (
            meta_cognition_engine
        )

        self.meta_selection_engine = (
            meta_selection_engine
        )

        self.meta_controller_engine = (
            meta_controller_engine
        )
        self.meta_supervisor = (
            meta_supervisor
        )

        self.self_rewrite_engine = (
            self_rewrite_engine
        )

        self.cognitive_genome = cognitive_genome
        self.cognitive_ecosystem = cognitive_ecosystem
        self.cognitive_society = cognitive_society
        self.civilization_engine = civilization_engine
        self.consciousness_engine = consciousness_engine
        self.curiosity_engine = curiosity_engine
        self.discovery_engine = discovery_engine
        self.abstraction_engine = abstraction_engine

        self.knowledge_expansion_engine = (
            knowledge_expansion_engine
        )

        self.autonomous_research_engine = (
            autonomous_research_engine
        )

        self.adaptive_strategy_injector = (
            adaptive_strategy_injector
        )

        # ====================================
        # PIPELINE STATE
        # ====================================

        self.pipeline_state = {
            "runtime_status": "initialized",
            "execution_cycles": 0,
            "runtime_health": "stable",
            "last_execution": None
        }

        self.register_default_stages()

    # ========================================
    # REGISTER STAGES
    # ========================================

    def register_default_stages(self):

        self.pipeline_stages = []

        for stage_callable in NEXRYN_STAGE_SEQUENCE:

            stage_function_name = (
                stage_callable.__name__
            )

            stage_name = (
                stage_function_name
                .replace(
                    "_stage",
                    ""
                )
            )

            self.pipeline_stages.append({

                "stage_name":
                stage_name,

                "callable":
                stage_callable,

                "function_name":
                stage_function_name,

                "priority":
                NEXRYN_STAGE_PRIORITIES.get(
                    stage_function_name,
                    "medium"
                ),

                "category":
                NEXRYN_STAGE_CATEGORIES.get(
                    stage_function_name,
                    "runtime"
                )
            })

    # ========================================
    # NORMALIZE CONTEXT
    # ========================================

    def normalize_runtime_context(
        self,
        runtime_context
    ):

        if runtime_context is None:
            runtime_context = {}

        if not isinstance(runtime_context, dict):
            runtime_context = {}

        protected_lists = [
            "execution_trace",
            "reasoning_hypotheses",
            "lineage_history",
            "recursive_paths"
        ]

        for key in protected_lists:

            value = runtime_context.get(key, [])

            if value is None:
                value = []

            if not isinstance(value, list):
                value = []

            runtime_context[key] = value

        return runtime_context

    # ========================================
    # REASONING BUDGETS
    # ========================================

    def _default_reasoning_budget(self):

        return {
            "mode": "adaptive",
            "execution_profile": "adaptive",
            "cognitive_pipeline": "adaptive",
            "pipeline_name": "adaptive",
            "max_chain_depth": 8,
            "max_dependency_depth": 8,
            "max_reasoning_depth": 6,
            "max_hypotheses": 6,
            "max_active_routes": 6,
            "max_contexts": 8,
            "MAX_CONTEXT_SEARCH_RESULTS": 8,
            "MAX_REUSE_ATTEMPTS": 3,
            "MAX_TRUTH_VALIDATIONS": 24,
            "MAX_CONTEXT_EXPANSION_DEPTH": 2,
            "max_concepts": None,
            "telemetry_enabled": True,
            "cache_dependencies": True,
            "explanation_enabled": True,
            "process_semantics_enabled": True,
            "temporal_reasoning_enabled": False,
            "full_governance_enabled": False,
            "report_level": "normal",
        }

    def _new_performance_counters(self):

        return {
            "task_start": None,
            "module_timings": [],
            "concepts_processed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "dependency_chains_executed": 0,
            "explanation_paths_generated": 0,
            "total_tasks": 1,
            "reasoning_executions": 0,
            "reasoning_avoided": 0,
            "governance_executions": 0,
            "governance_skips": 0,
            "locked_truth_fastpath_hits": 0,
            "locked_truth_fastpath_misses": 0,
            "governance_revalidations_skipped": 0,
            "dependency_snapshot_hits": 0,
            "dependency_snapshot_misses": 0,
            "dependency_executor_cache_hits": 0,
            "dependency_executor_cache_misses": 0,
            "dependency_reasoning_skipped": 0,
            "dependency_activation_attempted": 0,
            "dependency_activation_successful": 0,
            "dependency_activation_blocked": 0,
            "dependency_chain_generation_attempted": 0,
            "dependency_chain_generation_successful": 0,
            "dependency_chain_generation_failed": 0,
            "process_dependency_links_used": 0,
            "process_dependency_links_skipped": 0,
            "dependency_snapshot_store_count": 0,
            "truth_hits": 0,
            "truth_misses": 0,
            "strategy_hits": 0,
            "strategy_misses": 0,
            "program_hits": 0,
            "program_misses": 0,
            "context_hits": 0,
            "context_misses": 0,
            "context_lookup_count": 0,
            "context_reuse_attempts": 0,
            "context_reuse_successes": 0,
            "world_model_hits": 0,
            "world_model_misses": 0,
            "semantic_hits": 0,
            "semantic_misses": 0,
            "adaptive_reuse_evaluations": 0,
            "compact_reports_generated": 0,
            "heavy_keys_removed": 0,
            "arrays_summarized": 0,
            "repeated_reports_collapsed": 0,
            "final_context_size_estimate_before": 0,
            "final_context_size_estimate_after": 0,
            "pre_reasoning_router_enabled": True,
            "task_profiles_generated": 0,
            "selective_execution_enabled": True,
            "layers_enabled_count": 0,
            "layers_disabled_count": 0,
            "layers_deferred_count": 0,
            "full_stack_avoided": False,
            "estimated_layers_skipped": 0,
            "estimated_runtime_saved": 0.0,
            "estimated_compute_saved": 0.0,
            "skipped_reports_count": 0,
            "premature_reports_prevented": 0,
            "context_created": 0,
            "context_registered": 0,
            "context_consumed": 0,
            "context_lost": 0,
            "promotion_started": 0,
            "promotion_completed": 0,
            "promotion_skipped": 0,
            "candidate_generated": 0,
            "candidate_rejected": 0,
            "truth_committed": 0,
            "truth_rejected": 0,
            "context_count": 0,
            "registered_context_count": 0,
            "semantic_context_count": 0,
            "process_context_count": 0,
            "causal_context_count": 0,
            "world_context_count": 0,
            "promotion_evaluations": 0,
            "promotion_score_total": 0.0,
            "promotion_success_count": 0,
            "candidate_count": 0,
            "candidate_evaluations": 0,
            "truth_commit_count": 0,
            "truth_commit_evaluations": 0,
            "context_confidence_total": 0.0,
        }

    def configure_reasoning_budget(
        self,
        mode=None,
        max_chain_depth=None,
        max_concepts=None,
        telemetry_enabled=None,
        cache_dependencies=None,
        report_level=None,
    ):

        mode = (mode or self.reasoning_budget.get("mode") or "adaptive")
        mode = str(mode).lower()
        if mode not in {"fast", "adaptive", "deep", "full"}:
            mode = "adaptive"
        self.execution_profile = build_execution_profile(
            mode,
            report_level=report_level,
        )

        mode_defaults = {
            "fast": {
                "telemetry_enabled": False,
                "cache_dependencies": True,
                "report_level": "minimal",
                "max_concepts": 5,
                "governance_budget_seconds": 5,
                "full_governance": False,
            },
            "adaptive": {
                "telemetry_enabled": True,
                "cache_dependencies": True,
                "report_level": "normal",
                "max_chain_depth": 4,
                "max_dependency_depth": 4,
                "max_concepts": 8,
                "governance_budget_seconds": 10,
                "full_governance": False,
            },
            "deep": {
                "telemetry_enabled": True,
                "cache_dependencies": True,
                "report_level": "full",
                "max_chain_depth": 6,
                "max_dependency_depth": 6,
                "max_concepts": 12,
                "governance_budget_seconds": 20,
                "full_governance": False,
            },
            "full": {
                "telemetry_enabled": True,
                "cache_dependencies": True,
                "report_level": "full",
                "max_chain_depth": 6,
                "max_dependency_depth": 6,
                "max_concepts": 12,
                "governance_budget_seconds": 20,
                "full_governance": False,
            },
        }[mode]
        mode_defaults.update(self.execution_profile.as_budget_defaults())

        budget = {
            **self._default_reasoning_budget(),
            **mode_defaults,
            "mode": mode,
        }
        if max_chain_depth is not None:
            budget["max_chain_depth"] = max(1, int(max_chain_depth))
            budget["max_dependency_depth"] = max(1, int(max_chain_depth))
        if max_concepts is not None:
            budget["max_concepts"] = max(1, int(max_concepts))
        if telemetry_enabled is not None:
            budget["telemetry_enabled"] = bool(telemetry_enabled)
        if cache_dependencies is not None:
            budget["cache_dependencies"] = bool(cache_dependencies)
        if report_level is not None:
            report_level = str(report_level).lower()
            if report_level in {"minimal", "normal", "full", "debug", "audit"}:
                budget["report_level"] = report_level
        if mode in {"deep", "full"}:
            budget = deep_mode_budget_manager.constrain_reasoning_budget(
                budget,
            )

        self.reasoning_budget = budget
        return dict(self.reasoning_budget)

    def _start_performance_cycle(self):

        self.performance_counters = self._new_performance_counters()
        self.performance_counters["task_start"] = time.perf_counter()

    def _record_module_timing(self, module_name, started_at):

        elapsed = round(time.perf_counter() - started_at, 4)
        self.performance_counters["module_timings"].append({
            "module": module_name,
            "seconds": elapsed,
        })
        self.telemetry.record(
            "stage",
            module_name,
            elapsed,
        )

    def _sync_pre_reasoning_metrics(self, execution_plan=None):

        router_report = self.pre_reasoning_router.report()
        metric_keys = [
            "pre_reasoning_router_enabled",
            "task_profiles_generated",
            "selective_execution_enabled",
            "layers_enabled_count",
            "layers_disabled_count",
            "layers_deferred_count",
            "full_stack_avoided",
            "estimated_layers_skipped",
            "estimated_runtime_saved",
            "skipped_reports_count",
            "premature_reports_prevented",
            "dependency_activation_attempted",
            "dependency_activation_successful",
            "dependency_activation_blocked",
        ]
        for key in metric_keys:
            if key in router_report:
                self.performance_counters[key] = router_report[key]
        if isinstance(execution_plan, dict):
            self.performance_counters["layers_enabled_count"] = len(
                execution_plan.get("enabled_layers", [])
            )
            self.performance_counters["layers_disabled_count"] = len(
                execution_plan.get("disabled_layers", [])
            )
            self.performance_counters["layers_deferred_count"] = len(
                execution_plan.get("deferred_layers", [])
            )

    def _execution_plan(self, runtime_context=None):

        runtime_context = (
            runtime_context
            if isinstance(runtime_context, dict)
            else self.runtime.get_context()
        )
        plan = runtime_context.get("pre_reasoning_execution_plan")
        if not isinstance(plan, dict):
            plan = runtime_context.get("execution_plan", {})
        return plan if isinstance(plan, dict) else {}

    def _layer_allowed(self, layer_name, runtime_context=None):

        runtime_context = (
            runtime_context
            if isinstance(runtime_context, dict)
            else self.runtime.get_context()
        )
        plan = self._execution_plan(runtime_context)
        if not plan:
            return True
        return self.pre_reasoning_router.should_run(
            layer_name,
            runtime_context.get("pre_reasoning_task_profile"),
            runtime_context,
        )

    def _router_skipped_report(self, layer_name, runtime_context=None, reason=None):

        plan = self._execution_plan(runtime_context)
        report = self.pre_reasoning_router.skipped_report(
            layer_name,
            plan=plan,
            reason=reason,
        )
        self._sync_pre_reasoning_metrics(plan)
        return report

    def _dependency_reasoning_requested(self, runtime_context=None):

        runtime_context = (
            runtime_context
            if isinstance(runtime_context, dict)
            else self.runtime.get_context()
        )
        runtime_tool_requests = runtime_context.get(
            "runtime_tool_requests",
            {},
        )
        dependency_request = (
            runtime_tool_requests.get("dependency_reasoning", {})
            if isinstance(runtime_tool_requests, dict)
            else {}
        )
        tool_selection_report = runtime_context.get(
            "tool_selection_report",
            {},
        )
        enabled_tools = set(runtime_context.get("enabled_tools", []) or [])
        if isinstance(tool_selection_report, dict):
            enabled_tools.update(
                tool_selection_report.get("enabled_tools", []) or []
            )

        return (
            dependency_request.get("request_state") == "REQUESTED"
            or "dependency_reasoning" in enabled_tools
        )

    def _build_pre_reasoning_execution_plan(self, runtime_context):

        module_start = time.perf_counter()
        task_profile = self.pre_reasoning_router.analyze_task(
            runtime_context,
            runtime_context,
        )
        router_context = {
            **runtime_context,
            "requested_mode": self.requested_budget_mode
            or self.reasoning_budget.get("mode"),
            "audit_sections_requested": self.reasoning_budget.get(
                "audit_sections_requested",
                [],
            ),
        }
        execution_plan = (
            self.pre_reasoning_router
            .build_execution_plan(task_profile, router_context)
        )
        runtime_context["pre_reasoning_task_profile"] = task_profile
        runtime_context["task_profile"] = task_profile
        runtime_context["pre_reasoning_execution_plan"] = execution_plan
        runtime_context["execution_plan"] = execution_plan
        if execution_plan.get("dependency_reasoning_enabled"):
            runtime_context["runtime_tool_requests"] = {
                **runtime_context.get("runtime_tool_requests", {}),
                "dependency_reasoning": {
                    "tool_name": "dependency_reasoning",
                    "request_state": "REQUESTED",
                    "requested_by": "pre_reasoning_router",
                    "activation_state": "DEPENDENCY_REQUIRED",
                    "reason": execution_plan.get(
                        "dependency_activation_reason",
                    ),
                    "matched_signals": (
                        execution_plan.get(
                            "dependency_activation_policy",
                            {},
                        ).get("matched_signals", [])
                    ),
                },
            }
            runtime_context["enabled_tools"] = sorted(
                set(runtime_context.get("enabled_tools", []) or [])
                | {"dependency_reasoning"}
            )
            runtime_context["dependency_lifecycle_report"] = {
                **runtime_context.get("dependency_lifecycle_report", {}),
                "system": "dependency_runtime",
                "report_state": "pending",
                "dependency_activation_state": "REQUESTED",
                "dependency_requested_by": "pre_reasoning_router",
                "dependency_activation_reason":
                execution_plan.get("dependency_activation_reason"),
                "dependency_chains_executed": 0,
                "dependency_outputs_generated": 0,
            }
        runtime_context["pre_reasoning_router_report"] = (
            self.pre_reasoning_router.report()
        )
        self._sync_pre_reasoning_metrics(execution_plan)
        self._record_module_timing(
            "pre_reasoning_router",
            module_start,
        )
        return execution_plan

    def _build_execution_planner_context(
        self,
        runtime_context,
        reasoning_budget=None,
    ):

        runtime_context = runtime_context if isinstance(runtime_context, dict) else {}
        tool_selection_report = runtime_context.get("tool_selection_report", {})
        if not isinstance(tool_selection_report, dict):
            tool_selection_report = {}
        enabled_tools = sorted(
            set(runtime_context.get("enabled_tools", []) or [])
            | set(tool_selection_report.get("enabled_tools", []) or [])
            | set(tool_selection_report.get("selected_tools", []) or [])
        )
        attribution_report = runtime_context.get(
            "semantic_attribution_report",
            {},
        )
        if not isinstance(attribution_report, dict):
            attribution_report = {}
        introspection_report = runtime_context.get("introspection_report", {})
        if not isinstance(introspection_report, dict):
            introspection_report = {}
        attributed_concepts = list(
            dict.fromkeys(
                list(attribution_report.get("attributed_concepts", []) or [])
                + list(introspection_report.get("attributed_concepts", []) or [])
            )
        )
        active_routes = (
            introspection_report.get("active_routes")
            or len(enabled_tools)
        )
        plan_result = execution_planner.plan(
            enabled_tools=enabled_tools,
            attributed_concepts=attributed_concepts,
            semantic_contexts=runtime_context.get(
                "semantic_context_report",
                runtime_context.get("semantic_contexts"),
            ),
            truth_candidates=runtime_context.get(
                "truth_candidate_report",
                runtime_context.get("truth_candidates"),
            ),
            active_routes=active_routes,
            runtime_budget=(
                reasoning_budget
                or runtime_context.get("current_reasoning_budget")
            ),
            task_profile=runtime_context.get(
                "pre_reasoning_task_profile",
                runtime_context.get("task_profile"),
            ),
            runtime_context=runtime_context,
        )
        planner_report = plan_result.get("EXECUTION_PLAN_REPORT", {})
        generated_plan = plan_result.get("execution_plan", {})
        canonical_plan = plan_result.get("canonical_execution_plan", {})
        existing_plan = self._execution_plan(runtime_context)
        runtime_context["planner_execution_plan"] = generated_plan
        runtime_context["canonical_execution_plan"] = canonical_plan
        runtime_context["CANONICAL_EXECUTION_PLAN_REPORT"] = canonical_plan
        runtime_context["EXECUTION_PLAN_RUNTIME_HANDOFF"] = (
            execution_planner.consume_finalized_plan(
                canonical_plan,
                runtime_context=runtime_context,
            )
        )
        runtime_context["EXECUTION_PLAN_REPORT"] = planner_report
        runtime_context["execution_plan_report"] = planner_report
        runtime_context["execution_graph"] = plan_result.get(
            "execution_graph",
            {},
        )
        runtime_context["execution_nodes"] = plan_result.get(
            "execution_nodes",
            [],
        )
        runtime_context["dependency_execution_nodes"] = generated_plan.get(
            "dependency_nodes",
            [],
        )
        runtime_context["process_execution_nodes"] = generated_plan.get(
            "process_nodes",
            [],
        )
        runtime_context["causal_execution_nodes"] = generated_plan.get(
            "causal_nodes",
            [],
        )
        runtime_context["blocked_execution_nodes"] = generated_plan.get(
            "blocked_nodes",
            [],
        )
        runtime_context["deferred_execution_nodes"] = generated_plan.get(
            "deferred_nodes",
            [],
        )
        runtime_context["execution_order"] = generated_plan.get(
            "execution_order",
            [],
        )
        if isinstance(existing_plan, dict):
            runtime_context["execution_plan"] = {
                **existing_plan,
                "planner_execution_plan": generated_plan,
                "execution_nodes": generated_plan.get("execution_nodes", []),
                "nodes": generated_plan.get("execution_nodes", []),
                "dependency_nodes": generated_plan.get("dependency_nodes", []),
                "process_nodes": generated_plan.get("process_nodes", []),
                "causal_nodes": generated_plan.get("causal_nodes", []),
                "blocked_nodes": generated_plan.get("blocked_nodes", []),
                "deferred_nodes": generated_plan.get("deferred_nodes", []),
                "pruning_log": generated_plan.get("pruning_log", []),
                "execution_order": generated_plan.get("execution_order", []),
                "execution_planner_integrated": True,
            }
        runtime_context["runtime_tool_requests"] = {
            **runtime_context.get("runtime_tool_requests", {}),
            **plan_result.get("dependency_requests", {}),
            **plan_result.get("process_requests", {}),
            **plan_result.get("causal_requests", {}),
        }
        self._attach_planner_lifecycle_reports(runtime_context, plan_result)
        return runtime_context

    def _dispatch_execution_plan_context(
        self,
        runtime_context,
        reasoning_budget=None,
    ):

        runtime_context = runtime_context if isinstance(runtime_context, dict) else {}
        dispatch_result = execution_dispatcher.dispatch(
            execution_plan=runtime_context.get(
                "planner_execution_plan",
                runtime_context.get("execution_plan", {}),
            ),
            runtime_context=runtime_context,
            runtime_budget=(
                reasoning_budget
                or runtime_context.get("current_reasoning_budget")
            ),
        )
        dispatch_report = dispatch_result.get(
            "EXECUTION_DISPATCH_REPORT",
            {},
        )
        runtime_updates = dispatch_result.get("runtime_updates", {})
        if isinstance(runtime_updates, dict):
            runtime_context.update(runtime_updates)

        dispatched_plan = dispatch_result.get("dispatched_execution_plan", {})
        if isinstance(dispatched_plan, dict):
            runtime_context["dispatched_execution_plan"] = dispatched_plan
            runtime_context["execution_plan"] = {
                **self._execution_plan(runtime_context),
                "dispatched_execution_plan": dispatched_plan,
                "execution_nodes": dispatched_plan.get("execution_nodes", []),
                "nodes": dispatched_plan.get("nodes", []),
                "execution_dispatcher_integrated": True,
            }
        runtime_context["EXECUTION_DISPATCH_REPORT"] = dispatch_report
        runtime_context["execution_dispatch_report"] = dispatch_report
        runtime_context["execution_dispatch_runtime_results"] = (
            dispatch_result.get("runtime_results", {})
        )
        self._sync_dispatcher_runtime_metrics(runtime_context, dispatch_report)
        return runtime_context

    def _sync_dispatcher_runtime_metrics(
        self,
        runtime_context,
        dispatch_report,
    ):

        dependency_report = runtime_context.get(
            "dependency_lifecycle_report",
            {},
        )
        if isinstance(dependency_report, dict):
            chains = dependency_report.get("dependency_chains_executed", 0)
            try:
                chains = int(chains or 0)
            except (TypeError, ValueError):
                chains = 0
            if chains > 0:
                self.performance_counters["dependency_activation_attempted"] += 1
                self.performance_counters["dependency_chain_generation_attempted"] += (
                    chains
                )
                self.performance_counters["dependency_chain_generation_successful"] += (
                    chains
                )
                self.performance_counters["dependency_chains_executed"] += chains
            elif (
                isinstance(dispatch_report, dict)
                and dispatch_report.get("dependency_runtime_called")
            ):
                self.performance_counters["dependency_activation_attempted"] += 1
                self.performance_counters["dependency_chain_generation_failed"] += 1

        process_report = runtime_context.get(
            "process_context_runtime_report",
            runtime_context.get("process_context_report", {}),
        )
        if isinstance(process_report, dict):
            process_count = process_report.get("process_context_count", 0)
            try:
                process_count = int(process_count or 0)
            except (TypeError, ValueError):
                process_count = 0
            self.performance_counters["process_context_count"] = max(
                self.performance_counters.get("process_context_count", 0),
                process_count,
            )

        causal_report = runtime_context.get(
            "causal_context_runtime_report",
            runtime_context.get("causal_context_report", {}),
        )
        if isinstance(causal_report, dict):
            causal_count = causal_report.get("causal_context_count", 0)
            try:
                causal_count = int(causal_count or 0)
            except (TypeError, ValueError):
                causal_count = 0
            self.performance_counters["causal_context_count"] = max(
                self.performance_counters.get("causal_context_count", 0),
                causal_count,
            )

    def _attach_planner_lifecycle_reports(self, runtime_context, plan_result):

        planner_report = plan_result.get("EXECUTION_PLAN_REPORT", {})
        dependency_requests = plan_result.get("dependency_requests", {})
        process_requests = plan_result.get("process_requests", {})
        causal_requests = plan_result.get("causal_requests", {})
        if dependency_requests:
            request = dependency_requests.get("dependency_reasoning", {})
            runtime_context["dependency_lifecycle_report"] = {
                **runtime_context.get("dependency_lifecycle_report", {}),
                "system": "dependency_runtime",
                "report_state": "pending",
                "dependency_activation_state": request.get(
                    "activation_state",
                    "REQUESTED",
                ),
                "dependency_requested_by": "execution_planner",
                "dependency_activation_reason": request.get("reason"),
                "dependency_execution_node_created": True,
                "dependency_chains_executed": 0,
                "dependency_outputs_generated": 0,
            }
        if process_requests:
            request = process_requests.get("process_semantics", {})
            runtime_context["process_execution_request_report"] = {
                "system": "process_semantic_execution",
                "report_state": "pending",
                "process_activation_state": request.get(
                    "activation_state",
                    "REQUESTED",
                ),
                "process_requested_by": "execution_planner",
                "process_stage_created": bool(
                    planner_report.get("process_nodes")
                ),
                "process_context_count": 0,
                "reason": request.get("reason"),
            }
        if causal_requests:
            request = causal_requests.get("causal_validation", {})
            runtime_context["causal_execution_request_report"] = {
                "system": "causal_validation_execution",
                "report_state": "pending",
                "causal_activation_state": request.get(
                    "activation_state",
                    "REQUESTED",
                ),
                "causal_requested_by": "execution_planner",
                "causal_stage_created": bool(
                    planner_report.get("causal_nodes")
                ),
                "causal_context_count": 0,
                "reason": request.get("reason"),
            }

    def _stable_hash(self, payload):

        try:
            encoded = json.dumps(
                payload,
                sort_keys=True,
                default=str,
            )
        except TypeError:
            encoded = str(payload)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _runtime_signature(self, runtime_context):

        task_path = runtime_context.get("task_path")
        candidates = runtime_context.get("arc_replication_candidates", [])
        task_batch = [
            task_path,
            *[
                item.get("task_path")
                for item in candidates
                if isinstance(item, dict)
            ],
        ]
        return self._stable_hash(task_batch)

    def _concept_state_for(self, concept, runtime_context):

        lifecycle = runtime_context.get("concept_lifecycle_report", {})
        if isinstance(lifecycle, dict):
            for item in lifecycle.get("concepts", []):
                if item.get("concept") == concept:
                    return item.get("state", "unknown")
        concept_states = runtime_context.get("concept_states", {})
        if isinstance(concept_states, dict):
            return concept_states.get(concept, "unknown")
        return "unknown"

    def _dependency_memory_signature(self):

        memory = self.dependency_chain_executor.memory
        try:
            links = [link.as_dict() for link in memory.all_links()]
        except Exception:
            links = []
        return self._stable_hash({
            "links_loaded": getattr(memory, "links_loaded", 0),
            "links": links,
        })

    def _cache_metadata(self, runtime_context):

        evidence_hash = self._runtime_signature(runtime_context)
        dependency_hash = self._dependency_memory_signature()
        context_hash = (
            self.cognitive_cache_manager
            .stable_context_hash(runtime_context)
        )
        return {
            "evidence_hash": evidence_hash,
            "dependency_hash": dependency_hash,
            "context_hash": context_hash,
            "concept_version_hash": (
                self.cognitive_cache_manager.concept_version_hash(
                    evidence_hash,
                    dependency_hash,
                    context_hash,
                )
            ),
            "governance_threshold_hash": self._stable_hash({
                "mode": self.reasoning_budget.get("mode"),
                "report_level": self.reasoning_budget.get("report_level"),
            }),
            "runtime_version": "nexryn-alpha-1.4.5",
        }

    def _save_cognitive_cache(self):

        started_at = time.perf_counter()
        max_seconds = (
            3
            if self.reasoning_budget.get("mode") == "fast"
            else None
        )
        legacy_count = 0
        if max_seconds is None or time.perf_counter() - started_at < max_seconds:
            legacy_count = self.cognitive_cache_manager.save()
        if max_seconds is None or time.perf_counter() - started_at < max_seconds:
            self.adaptive_cache_manager.flush()
        else:
            context = self.runtime.get_context()
            context["cache_save_deferred"] = True
            context["cache_save_warning"] = (
                "cache_save_deferred_due_to_finalization_budget"
            )
            self.runtime.bulk_update_context(context)
        return legacy_count

    def _artifact_cache_key(
        self,
        runtime_context,
        artifact_type,
        concept_signature=None,
    ):

        metadata = self._cache_metadata(runtime_context)
        task_report = runtime_context.get(
            "task_complexity_report",
            {},
        )
        task_signature = task_report.get(
            "task_signature",
            self._runtime_signature(runtime_context),
        )
        concept_version_hash = (
            self.cognitive_cache_manager.concept_version_hash(
                metadata["evidence_hash"],
                metadata["dependency_hash"],
                metadata["context_hash"],
            )
        )
        return self.cognitive_cache_manager.build_key(
            task_signature=task_signature,
            concept_signature=concept_signature,
            dependency_hash=metadata["dependency_hash"],
            evidence_hash=metadata["evidence_hash"],
            context_hash=metadata["context_hash"],
            concept_version_hash=concept_version_hash,
            runtime_version=metadata["runtime_version"],
            artifact_type=artifact_type,
        )

    def _pipeline_result_cache_key(
        self,
        runtime_context,
    ):

        task_report = runtime_context.get(
            "task_complexity_report",
            {},
        )
        task_signature = task_report.get(
            "task_signature",
            self._runtime_signature(runtime_context),
        )
        evidence_hash = self._runtime_signature(runtime_context)
        dependency_hash = self._dependency_memory_signature()
        context_hash = self.cognitive_cache_manager.stable_hash({
            "task_signature": task_signature,
            "task_path": runtime_context.get("task_path"),
            "arc_replication_candidates":
            runtime_context.get("arc_replication_candidates", []),
            "input_grid": runtime_context.get("input_grid"),
            "output_grid": runtime_context.get("output_grid"),
        })
        concept_version_hash = (
            self.cognitive_cache_manager.concept_version_hash(
                evidence_hash,
                dependency_hash,
                context_hash,
            )
        )
        return self.cognitive_cache_manager.build_key(
            task_signature=task_signature,
            concept_signature="pipeline_result",
            dependency_hash=dependency_hash,
            evidence_hash=evidence_hash,
            context_hash=context_hash,
            concept_version_hash=concept_version_hash,
            runtime_version="nexryn-alpha-1.4.7",
            artifact_type="pipeline_result",
        )

    def _dependency_cache_key(self, concept, runtime_context):

        return self._stable_hash({
            "concept": concept,
            "concept_state": self._concept_state_for(
                concept,
                runtime_context,
            ),
            "memory_signature": self._dependency_memory_signature(),
            "task_batch_signature": self._runtime_signature(runtime_context),
            "max_chain_depth": self.reasoning_budget["max_chain_depth"],
        })

    def performance_report(self):

        started = self.performance_counters.get("task_start")
        total_runtime_seconds = (
            round(time.perf_counter() - started, 4)
            if started is not None
            else 0.0
        )
        slowest_modules = sorted(
            self.performance_counters.get("module_timings", []),
            key=lambda item: item.get("seconds", 0.0),
            reverse=True,
        )[:5]
        module_timings = list(self.performance_counters.get("module_timings", []))
        timing_bridge = runtime_metric_bridge.synchronize(
            {
                "total_runtime_seconds": total_runtime_seconds,
                "module_timings": module_timings,
            },
            module_timings=module_timings,
        )
        cache_metrics = self.cognitive_cache_manager.metrics()
        adaptive_cache_report = self.adaptive_cache_manager.report()
        adaptive_reuse_report = self.adaptive_reuse_engine.report()
        context_reuse_report = self.context_reuse_engine.report()
        dependency_executor_cache_report = (
            self.dependency_chain_executor.cache_report()
        )
        local_cache_total = (
            self.performance_counters["cache_hits"]
            + self.performance_counters["cache_misses"]
        )
        local_cache_hit_rate = (
            self.performance_counters["cache_hits"] / local_cache_total
            if local_cache_total
            else 0.0
        )
        runtime_context = self.runtime.get_context()
        dependency_depth = runtime_context.get(
            "dependency_chain_depth",
            0,
        )
        dependency_coverage = runtime_context.get(
            "dependency_chain_coverage",
            0.0,
        )
        dependency_time = round(
            sum(
                float(item.get("seconds", 0.0) or 0.0)
                for item in module_timings
                if isinstance(item, dict)
                and item.get("module") == "dependency_reasoning"
            ),
            4,
        )
        dependency_state = self._dependency_activation_state(
            dependency_time,
            requested=self._dependency_reasoning_requested(runtime_context),
        )
        introspection_report = runtime_context.get(
            "introspection_report",
            {},
        )
        if not isinstance(introspection_report, dict):
            introspection_report = {}
        dependency_activation_trace = runtime_context.get(
            "DEPENDENCY_ACTIVATION_TRACE",
            {},
        )
        dependency_lifecycle_report = runtime_context.get(
            "dependency_lifecycle_report",
            {},
        )
        if (
            dependency_time <= 0
            and isinstance(dependency_lifecycle_report, dict)
        ):
            try:
                dependency_time = round(
                    float(
                        dependency_lifecycle_report.get(
                            "dependency_time",
                            0.0,
                        )
                        or 0.0
                    ),
                    4,
                )
            except (TypeError, ValueError):
                dependency_time = 0.0
        lifecycle_cost = round(
            sum(
                float(item.get("seconds", 0.0) or 0.0)
                for item in module_timings
                if isinstance(item, dict)
                and item.get("module") in {
                    "concept_lifecycle_report",
                    "concept_lifecycle",
                    "knowledge_concept_lifecycle_report",
                }
            ),
            4,
        )
        lifecycle_cache_report = concept_lifecycle_cache.report()
        process_context_count = (
            runtime_context.get("process_context_registry_report", {})
            if isinstance(
                runtime_context.get("process_context_registry_report"),
                dict,
            )
            else {}
        ).get(
            "process_context_count",
            self.performance_counters.get("process_context_count", 0),
        )
        base_report = {
            "system": "runtime_reasoning_budget",
            "mode": self.reasoning_budget["mode"],
            "execution_time": total_runtime_seconds,
            "total_runtime_seconds": total_runtime_seconds,
            **timing_bridge,
            "concepts_processed":
            self.performance_counters["concepts_processed"],
            "cache_hits": self.performance_counters["cache_hits"],
            "cache_misses": self.performance_counters["cache_misses"],
            "cache_hit_rate": round(local_cache_hit_rate, 4),
            "local_cache_hits": self.performance_counters["cache_hits"],
            "local_cache_misses": self.performance_counters["cache_misses"],
            "manager_cache_hits": cache_metrics.cache_hits,
            "manager_cache_misses": cache_metrics.cache_misses,
            "manager_cache_hit_rate": cache_metrics.hit_rate,
            "dependency_chains_executed":
            self.performance_counters["dependency_chains_executed"],
            "dependency_chain_depth": dependency_depth,
            "dependency_chain_coverage": dependency_coverage,
            "dependency_activation_state": dependency_state,
            "dependency_activation_reason": (
                dependency_activation_trace.get("dependency_activation_reason")
                or dependency_lifecycle_report.get(
                    "dependency_activation_reason",
                )
            ),
            "dependency_skip_reason": (
                dependency_activation_trace.get("dependency_skip_reason")
                or dependency_lifecycle_report.get("dependency_skip_reason")
            ),
            "dependency_usage_rate":
            dependency_activation_trace.get("dependency_usage_rate", 0.0),
            "metric_reconciliation_report": (
                self._metric_reconciliation_report(
                    runtime_context,
                    introspection_report,
                    dependency_state,
                    dependency_time,
                )
            ),
            "dependency_time": dependency_time,
            "dependency_reasoning_time_seconds": dependency_time,
            "dependency_executor_cache_hits":
            self.performance_counters["dependency_executor_cache_hits"],
            "dependency_executor_cache_misses":
            self.performance_counters["dependency_executor_cache_misses"],
            "dependency_executor_cache_report":
            dependency_executor_cache_report,
            "concept_lifecycle_cost": lifecycle_cost,
            "concept_lifecycle_cache_hits":
            lifecycle_cache_report.get("concept_lifecycle_cache_hits", 0),
            "concept_lifecycle_cache_report": lifecycle_cache_report,
            "explanation_paths_generated":
            self.performance_counters["explanation_paths_generated"],
            "telemetry_enabled":
            self.reasoning_budget["telemetry_enabled"],
            "report_level": self.reasoning_budget["report_level"],
            "max_chain_depth": self.reasoning_budget["max_chain_depth"],
            "max_concepts": self.reasoning_budget["max_concepts"],
            "cache_dependencies":
            self.reasoning_budget["cache_dependencies"],
            "slowest_modules": slowest_modules,
            "module_timings":
            module_timings,
            "cache_metrics":
            self.cognitive_cache_manager.build_report(),
            "adaptive_cache_layer":
            adaptive_cache_report,
            "adaptive_reuse_engine":
            adaptive_reuse_report,
            "context_reuse_report":
            context_reuse_report,
            "cache_metric_authority":
            adaptive_cache_report,
            "reuse_metric_authority":
            adaptive_reuse_report,
            "truth_hits": max(
                adaptive_cache_report["truth_hits"],
                adaptive_reuse_report["truth_hits"],
            ),
            "truth_misses": max(
                adaptive_cache_report["truth_misses"],
                adaptive_reuse_report["truth_misses"],
            ),
            "strategy_hits": max(
                adaptive_cache_report["strategy_hits"],
                adaptive_reuse_report["strategy_hits"],
            ),
            "strategy_misses": max(
                adaptive_cache_report["strategy_misses"],
                adaptive_reuse_report["strategy_misses"],
            ),
            "program_hits": max(
                adaptive_cache_report["program_hits"],
                adaptive_reuse_report["program_hits"],
            ),
            "program_misses": max(
                adaptive_cache_report["program_misses"],
                adaptive_reuse_report["program_misses"],
            ),
            "context_hits": max(
                adaptive_cache_report["context_hits"],
                adaptive_reuse_report["context_hits"],
                self.performance_counters["context_hits"],
            ),
            "context_misses": max(
                adaptive_cache_report["context_misses"],
                adaptive_reuse_report["context_misses"],
                self.performance_counters["context_misses"],
            ),
            "world_model_hits": max(
                adaptive_cache_report["world_model_hits"],
                adaptive_reuse_report["world_model_hits"],
            ),
            "world_model_misses": max(
                adaptive_cache_report["world_model_misses"],
                adaptive_reuse_report["world_model_misses"],
            ),
            "semantic_hits": adaptive_cache_report["semantic_hits"],
            "semantic_misses": adaptive_cache_report["semantic_misses"],
            "adaptive_reuse_rate": adaptive_cache_report["reuse_rate"],
            "reuse_rate": max(
                adaptive_cache_report["reuse_rate"],
                context_reuse_report["reuse_rate"],
            ),
            "strategy_reuse_rate": round(
                max(
                    adaptive_cache_report["strategy_hits"],
                    adaptive_reuse_report["strategy_hits"],
                )
                / max(
                    max(
                        adaptive_cache_report["strategy_hits"],
                        adaptive_reuse_report["strategy_hits"],
                    )
                    + max(
                        adaptive_cache_report["strategy_misses"],
                        adaptive_reuse_report["strategy_misses"],
                    ),
                    1,
                ),
                4,
            ),
            "estimated_compute_saved":
            max(
                adaptive_cache_report["estimated_compute_saved"],
                adaptive_reuse_report["estimated_compute_saved"],
            ),
            "estimated_runtime_saved":
            max(
                adaptive_cache_report["estimated_runtime_saved"],
                adaptive_reuse_report["estimated_runtime_saved"],
            ),
            "adaptive_cache_size": adaptive_cache_report["cache_size"],
            "cache_compaction_ratio":
            adaptive_cache_report["compaction_ratio"],
            "pre_reasoning_router_enabled":
            self.performance_counters["pre_reasoning_router_enabled"],
            "pre_reasoning_execution_plan":
            runtime_context.get("pre_reasoning_execution_plan", {}),
            "task_profiles_generated":
            self.performance_counters["task_profiles_generated"],
            "selective_execution_enabled":
            self.performance_counters["selective_execution_enabled"],
            "layers_enabled_count":
            self.performance_counters["layers_enabled_count"],
            "layers_disabled_count":
            self.performance_counters["layers_disabled_count"],
            "layers_deferred_count":
            self.performance_counters["layers_deferred_count"],
            "full_stack_avoided":
            self.performance_counters["full_stack_avoided"],
            "estimated_layers_skipped":
            self.performance_counters["estimated_layers_skipped"],
            "estimated_runtime_saved":
            max(
                self.performance_counters["estimated_runtime_saved"],
                adaptive_reuse_report["estimated_runtime_saved"],
                adaptive_cache_report["estimated_runtime_saved"],
            ),
            "estimated_compute_saved":
            max(
                self.performance_counters["estimated_compute_saved"],
                adaptive_reuse_report["estimated_compute_saved"],
                adaptive_cache_report["estimated_compute_saved"],
            ),
            "skipped_reports_count":
            self.performance_counters["skipped_reports_count"],
            "premature_reports_prevented":
            self.performance_counters["premature_reports_prevented"],
            "context_count":
            self.performance_counters["context_count"],
            "registered_context_count":
            self.performance_counters["registered_context_count"],
            "semantic_context_count":
            self.performance_counters["semantic_context_count"],
            "process_context_count":
            process_context_count,
            "causal_context_count":
            self.performance_counters["causal_context_count"],
            "world_context_count":
            self.performance_counters["world_context_count"],
            "promotion_evaluations":
            self.performance_counters["promotion_evaluations"],
            "promotion_success_rate":
            round(
                self.performance_counters["promotion_success_count"]
                / max(self.performance_counters["promotion_evaluations"], 1),
                4,
            ),
            "candidate_count":
            self.performance_counters["candidate_count"],
            "candidate_generation_rate":
            round(
                self.performance_counters["candidate_generated"]
                / max(self.performance_counters["candidate_evaluations"], 1),
                4,
            ),
            "truth_commit_count":
            self.performance_counters["truth_commit_count"],
            "committed_count":
            self.performance_counters["truth_commit_count"],
            "truth_commit_rate":
            round(
                self.performance_counters["truth_commit_count"]
                / max(self.performance_counters["truth_commit_evaluations"], 1),
                4,
            ),
            "average_promotion_score":
            round(
                self.performance_counters["promotion_score_total"]
                / max(self.performance_counters["promotion_evaluations"], 1),
                4,
            ),
            "average_context_confidence":
            round(
                self.performance_counters["context_confidence_total"]
                / max(self.performance_counters["registered_context_count"], 1),
                4,
            ),
            "context_created":
            self.performance_counters["context_created"],
            "context_lookup_count":
            context_reuse_report["context_lookup_count"],
            "context_reuse_attempts":
            self.performance_counters["context_reuse_attempts"],
            "context_reuse_successes":
            self.performance_counters["context_reuse_successes"],
            "context_registered":
            self.performance_counters["context_registered"],
            "context_consumed":
            self.performance_counters["context_consumed"],
            "context_lost":
            self.performance_counters["context_lost"],
            "promotion_started":
            self.performance_counters["promotion_started"],
            "promotion_completed":
            self.performance_counters["promotion_completed"],
            "promotion_skipped":
            self.performance_counters["promotion_skipped"],
            "candidate_generated":
            self.performance_counters["candidate_generated"],
            "candidate_rejected":
            self.performance_counters["candidate_rejected"],
            "truth_committed":
            self.performance_counters["truth_committed"],
            "truth_rejected":
            self.performance_counters["truth_rejected"],
            "early_exit_triggered":
            self.runtime.early_exit_triggered,
            "new_reasoning":
            self.performance_counters["reasoning_executions"],
            "total_tasks":
            self.performance_counters["total_tasks"],
            "reasoning_avoidance_count":
            self.performance_counters["reasoning_avoided"],
            "reasoning_avoidance_ratio":
            round(
                self.performance_counters["reasoning_avoided"]
                / max(self.performance_counters["total_tasks"], 1),
                4,
            ),
            "cognition_reuse_ratio":
            round(local_cache_hit_rate, 4),
            "governance_skip_count":
            self.performance_counters["governance_skips"],
            "locked_truth_fastpath_hits":
            self.performance_counters["locked_truth_fastpath_hits"],
            "locked_truth_fastpath_misses":
            self.performance_counters["locked_truth_fastpath_misses"],
            "governance_revalidations_skipped":
            self.performance_counters["governance_revalidations_skipped"],
            "dependency_snapshot_hits":
            self.performance_counters["dependency_snapshot_hits"],
            "dependency_snapshot_misses":
            self.performance_counters["dependency_snapshot_misses"],
            "dependency_reasoning_skipped":
            self.performance_counters["dependency_reasoning_skipped"],
            "dependency_activation_attempted":
            self.performance_counters["dependency_activation_attempted"],
            "dependency_activation_successful":
            self.performance_counters["dependency_activation_successful"],
            "dependency_activation_blocked":
            self.performance_counters["dependency_activation_blocked"],
            "dependency_chain_generation_attempted":
            self.performance_counters["dependency_chain_generation_attempted"],
            "dependency_chain_generation_successful":
            self.performance_counters["dependency_chain_generation_successful"],
            "dependency_chain_generation_failed":
            self.performance_counters["dependency_chain_generation_failed"],
            "process_dependency_links_used":
            self.performance_counters["process_dependency_links_used"],
            "process_dependency_links_skipped":
            self.performance_counters["process_dependency_links_skipped"],
            "dependency_snapshot_store_count":
            self.performance_counters["dependency_snapshot_store_count"],
            "compact_reports_generated":
            self.performance_counters["compact_reports_generated"],
            "heavy_keys_removed":
            self.performance_counters["heavy_keys_removed"],
            "arrays_summarized":
            self.performance_counters["arrays_summarized"],
            "repeated_reports_collapsed":
            self.performance_counters["repeated_reports_collapsed"],
            "final_context_size_estimate_before":
            self.performance_counters[
                "final_context_size_estimate_before"
            ],
            "final_context_size_estimate_after":
            self.performance_counters[
                "final_context_size_estimate_after"
            ],
            "governance_execution_count":
            self.performance_counters["governance_executions"],
            "governance_skip_ratio":
            round(
                self.performance_counters["governance_skips"]
                / max(
                    self.performance_counters["governance_skips"]
                    + self.performance_counters["governance_executions"],
                    1,
                ),
                4,
            ),
            "reused_concepts":
            list(self.runtime.reused_concepts),
            "recomputed_concepts":
            list(self.runtime.invalidated_concepts),
        }
        return self._finalize_observability_report(
            base_report,
            adaptive_cache_report,
            adaptive_reuse_report,
            context_reuse_report,
        )

    def _metric_reconciliation_report(
        self,
        runtime_context,
        introspection_report,
        dependency_state,
        dependency_time,
    ):

        runtime_context = (
            runtime_context
            if isinstance(runtime_context, dict)
            else {}
        )
        introspection_report = (
            introspection_report
            if isinstance(introspection_report, dict)
            else {}
        )
        dependency_executed = self.performance_counters.get(
            "dependency_chains_executed",
            0,
        )
        dependency_depth = runtime_context.get(
            "dependency_chain_depth",
            0,
        )
        dependency_requested = self._dependency_reasoning_requested(
            runtime_context,
        )
        inferred_depth = int(
            introspection_report.get("reasoning_depth", 0) or 0
        )
        inferred_routes = int(
            introspection_report.get("active_routes", 0) or 0
        )
        inferred_nodes = int(
            introspection_report.get("execution_nodes", 0) or 0
        )
        attributed = list(
            introspection_report.get("attributed_concepts", []) or []
        )
        dependency_concepts = self._dependency_reasoning_concepts(
            runtime_context,
        )
        mismatch = (
            (inferred_depth > 0 or inferred_routes > 0 or inferred_nodes > 0)
            and dependency_executed <= 0
            and dependency_depth <= 0
        )
        reason = "metrics_reconciled"
        if mismatch:
            reason = (
                "introspection_measures_pipeline_activity_while_performance_"
                "measures_executed_dependency_runtime"
            )

        return {
            "system": "metric_reconciliation",
            "report_state": "final",
            "metric_reconciliation_state": (
                "MISMATCH_EXPLAINED" if mismatch else "CONSISTENT"
            ),
            "introspection_metric_source": "pipeline_activity_inference",
            "performance_metric_source": "dependency_runtime_counters",
            "introspection_reasoning_depth": inferred_depth,
            "introspection_route_count": inferred_routes,
            "introspection_execution_nodes": inferred_nodes,
            "dependency_requested": dependency_requested,
            "dependency_activation_state": dependency_state,
            "dependency_chains_executed": dependency_executed,
            "dependency_chain_depth": dependency_depth,
            "dependency_reasoning_time_seconds": dependency_time,
            "attributed_concepts": attributed,
            "dependency_runnable_concepts": dependency_concepts,
            "reconciliation_reason": reason,
        }

    def _build_execution_layer_audit_report(self, runtime_context=None):

        runtime_context = (
            runtime_context
            if isinstance(runtime_context, dict)
            else self.runtime.get_context()
        )
        runtime_context = (
            runtime_context
            if isinstance(runtime_context, dict)
            else {}
        )
        tool_selection_report = runtime_context.get(
            "tool_selection_report",
            {},
        )
        if not isinstance(tool_selection_report, dict):
            tool_selection_report = {}
        selected_tools = sorted(
            set(runtime_context.get("enabled_tools", []) or [])
            | set(tool_selection_report.get("enabled_tools", []) or [])
            | set(tool_selection_report.get("selected_tools", []) or [])
        )
        execution_plan = self._execution_plan(runtime_context)
        enabled_layers = list(execution_plan.get("enabled_layers", []) or [])
        disabled_layers = list(execution_plan.get("disabled_layers", []) or [])
        deferred_layers = list(execution_plan.get("deferred_layers", []) or [])
        skip_reasons = execution_plan.get("skip_reasons", {})
        if not isinstance(skip_reasons, dict):
            skip_reasons = {}

        introspection_report = runtime_context.get(
            "introspection_report",
            {},
        )
        if not isinstance(introspection_report, dict):
            introspection_report = {}
        planner_report = runtime_context.get("EXECUTION_PLAN_REPORT", {})
        if not isinstance(planner_report, dict):
            planner_report = runtime_context.get("execution_plan_report", {})
        if not isinstance(planner_report, dict):
            planner_report = {}
        active_routes = int(
            introspection_report.get("active_routes", 0)
            or planner_report.get("active_routes", 0)
            or len(selected_tools)
        )
        execution_nodes = int(
            planner_report.get("execution_nodes", 0)
            or introspection_report.get("execution_nodes", 0)
            or self._inferred_execution_node_count(runtime_context)
        )
        runtime_tool_requests = runtime_context.get(
            "runtime_tool_requests",
            {},
        )
        if not isinstance(runtime_tool_requests, dict):
            runtime_tool_requests = {}

        dependency_tool_selected = "dependency_reasoning" in selected_tools
        process_tool_selected = "process_semantics" in selected_tools
        causal_tool_selected = "causal_validation" in selected_tools
        dependency_request = runtime_tool_requests.get(
            "dependency_reasoning",
            {},
        )
        dependency_activation_request_created = (
            isinstance(dependency_request, dict)
            and dependency_request.get("request_state") == "REQUESTED"
        )
        dependency_time = self._module_time("dependency_reasoning")
        dependency_activation_state = self._dependency_activation_state(
            dependency_time,
            requested=dependency_activation_request_created,
        )
        lifecycle_report = runtime_context.get(
            "dependency_lifecycle_report",
            {},
        )
        if isinstance(lifecycle_report, dict):
            dependency_activation_state = lifecycle_report.get(
                "dependency_activation_state",
                dependency_activation_state,
            )

        process_stage_created = bool(planner_report.get("process_nodes")) or self._stage_created(
            "process_semantics",
            runtime_context,
        )
        causal_stage_created = bool(planner_report.get("causal_nodes")) or self._stage_created(
            "causal_validation",
            runtime_context,
        )
        route_to_node_mapping = self._route_to_node_mapping(
            selected_tools,
            enabled_layers,
            runtime_context,
            planner_report,
        )
        pruned_routes = self._pruned_routes(
            selected_tools,
            route_to_node_mapping,
            skip_reasons,
            active_routes,
            execution_nodes,
        )
        missing_execution_nodes = [
            route
            for route, mapping in route_to_node_mapping.items()
            if mapping.get("execution_node_created") is not True
        ]
        budget_blocks = self._execution_layer_budget_blocks(
            selected_tools,
            runtime_context,
        )
        selective_execution_blocks = (
            self._selective_execution_blocks(
                selected_tools,
                enabled_layers,
                disabled_layers,
                deferred_layers,
                skip_reasons,
            )
        )

        silent_drop_detected = False
        suspected_breakpoint = "none_detected"
        if dependency_tool_selected and not dependency_activation_request_created:
            silent_drop_detected = True
            suspected_breakpoint = "tool_selection_to_execution_plan"
        if process_tool_selected and not process_stage_created:
            silent_drop_detected = True
            if suspected_breakpoint == "none_detected":
                suspected_breakpoint = "tool_selection_to_runtime_stage"
        if causal_tool_selected and not causal_stage_created:
            silent_drop_detected = True
            if suspected_breakpoint == "none_detected":
                suspected_breakpoint = "tool_selection_to_runtime_stage"
        if active_routes > execution_nodes and pruned_routes:
            silent_drop_detected = True
            if suspected_breakpoint == "none_detected":
                suspected_breakpoint = "route_to_execution_node_compilation"

        return {
            "system": "execution_layer_audit",
            "report_state": "final",
            "EXECUTION_LAYER_AUDIT_REPORT": True,
            "selected_tools": selected_tools,
            "enabled_layers": sorted(enabled_layers),
            "disabled_layers": sorted(disabled_layers),
            "deferred_layers": sorted(deferred_layers),
            "active_routes": active_routes,
            "execution_nodes": execution_nodes,
            "route_to_node_mapping": route_to_node_mapping,
            "pruned_routes": pruned_routes,
            "missing_execution_nodes": missing_execution_nodes,
            "dependency_tool_selected": dependency_tool_selected,
            "dependency_activation_request_created":
            dependency_activation_request_created,
            "dependency_activation_state": dependency_activation_state,
            "process_tool_selected": process_tool_selected,
            "process_stage_created": process_stage_created,
            "causal_tool_selected": causal_tool_selected,
            "causal_stage_created": causal_stage_created,
            "budget_blocks": budget_blocks,
            "selective_execution_blocks": selective_execution_blocks,
            "silent_drop_detected": silent_drop_detected,
            "suspected_breakpoint": suspected_breakpoint,
            "recommended_next_fix":
            self._execution_layer_recommended_next_fix(
                suspected_breakpoint,
                budget_blocks,
                selective_execution_blocks,
            ),
        }

    def _attach_execution_layer_audit_report(self, runtime_context):

        runtime_context = runtime_context if isinstance(runtime_context, dict) else {}
        report = self._build_execution_layer_audit_report(runtime_context)
        runtime_context["EXECUTION_LAYER_AUDIT_REPORT"] = report
        runtime_context["execution_layer_audit_report"] = dict(report)
        return runtime_context

    def _inferred_execution_node_count(self, runtime_context):

        return len([
            key
            for key in (
                "predicted_output",
                "prediction_report",
                "evaluation_result",
                "residual_analysis",
            )
            if runtime_context.get(key) is not None
        ])

    def _module_time(self, module_name):

        return round(
            sum(
                float(item.get("seconds", 0.0) or 0.0)
                for item in self.performance_counters.get(
                    "module_timings",
                    [],
                )
                if isinstance(item, dict)
                and item.get("module") == module_name
            ),
            4,
        )

    def _stage_created(self, tool_name, runtime_context):

        layer_name = {
            "process_semantics": "process_semantic_synthesis",
            "causal_validation": "causal_validation",
        }.get(tool_name, tool_name)
        stage_names = set(self.completed_stages) | {
            item.get("stage")
            for item in self.stage_execution_history
            if isinstance(item, dict)
        }
        return layer_name in stage_names

    def _route_to_node_mapping(
        self,
        selected_tools,
        enabled_layers,
        runtime_context,
        planner_report=None,
    ):

        layer_aliases = {
            "dependency_reasoning": "dependency_reasoning",
            "process_semantics": "process_semantic_synthesis",
            "causal_validation": "causal_validation",
            "truth_governance": "truth_candidate",
            "identity_governance": "deep_governance",
            "object_tracking": "object_detection",
            "spatial_reasoning": "inference",
            "color_mapping": "transformation_solver",
        }
        planner_report = planner_report if isinstance(planner_report, dict) else {}
        planner_node_items = []
        for key in (
            "generated_execution_nodes",
            "dependency_nodes",
            "process_nodes",
            "causal_nodes",
            "blocked_nodes",
            "deferred_nodes",
        ):
            planner_node_items.extend(planner_report.get(key, []) or [])
        planner_nodes = {
            node.get("originating_tool"): node
            for node in planner_node_items
            if isinstance(node, dict)
        }
        execution_node_keys = {
            "predicted_output": "prediction_output_node",
            "prediction_report": "prediction_report_node",
            "evaluation_result": "evaluation_node",
            "residual_analysis": "residual_analysis_node",
        }
        available_nodes = [
            node_name
            for key, node_name in execution_node_keys.items()
            if runtime_context.get(key) is not None
        ]
        mapping = {}
        for index, tool_name in enumerate(selected_tools):
            layer_name = layer_aliases.get(tool_name)
            planner_node = planner_nodes.get(tool_name, {})
            node_name = (
                planner_node.get("node_id")
                or (
                    available_nodes[index]
                    if index < len(available_nodes)
                    else None
                )
            )
            mapping[tool_name] = {
                "mapped_layer": layer_name,
                "layer_enabled": layer_name in set(enabled_layers),
                "execution_node": node_name,
                "execution_node_created": node_name is not None,
                "planner_status": planner_node.get("status"),
            }
        return mapping

    def _pruned_routes(
        self,
        selected_tools,
        route_to_node_mapping,
        skip_reasons,
        active_routes,
        execution_nodes,
    ):

        if active_routes <= execution_nodes:
            return []
        pruned = []
        for route in selected_tools:
            mapping = route_to_node_mapping.get(route, {})
            if mapping.get("execution_node_created") is True:
                continue
            layer_name = mapping.get("mapped_layer")
            reason = skip_reasons.get(layer_name)
            pruned.append({
                "route": route,
                "mapped_layer": layer_name,
                "reason": reason,
                "pruned_without_reason": reason is None,
            })
        return pruned

    def _execution_layer_budget_blocks(self, selected_tools, runtime_context):

        budget_report = runtime_context.get("cognitive_budget_report", {})
        if not isinstance(budget_report, dict):
            budget_report = {}
        blocks = []
        if (
            "dependency_reasoning" in selected_tools
            and int(budget_report.get("max_dependency_depth", 1) or 0) <= 0
        ):
            blocks.append({
                "tool": "dependency_reasoning",
                "state": "BLOCKED_BY_BUDGET",
                "reason": "max_dependency_depth<=0",
            })
        if (
            "process_semantics" in selected_tools
            and budget_report.get("process_semantics_enabled") is False
        ):
            blocks.append({
                "tool": "process_semantics",
                "state": "BLOCKED_BY_BUDGET",
                "reason": "process_semantics_enabled=False",
            })
        if (
            selected_tools
            and int(budget_report.get("max_active_routes", 1) or 0) <= 0
        ):
            for tool in selected_tools:
                blocks.append({
                    "tool": tool,
                    "state": "BLOCKED_BY_BUDGET",
                    "reason": "max_active_routes<=0",
                })
        return blocks

    def _selective_execution_blocks(
        self,
        selected_tools,
        enabled_layers,
        disabled_layers,
        deferred_layers,
        skip_reasons,
    ):

        layer_aliases = {
            "dependency_reasoning": "dependency_reasoning",
            "process_semantics": "process_semantic_synthesis",
            "causal_validation": "causal_validation",
            "truth_governance": "truth_candidate",
        }
        blocks = []
        enabled = set(enabled_layers)
        disabled = set(disabled_layers)
        deferred = set(deferred_layers)
        for tool, layer in layer_aliases.items():
            if tool not in selected_tools or layer in enabled:
                continue
            if layer in disabled or layer in deferred:
                blocks.append({
                    "tool": tool,
                    "layer": layer,
                    "state": "BLOCKED_BY_SELECTIVE_EXECUTION",
                    "reason": (
                        skip_reasons.get(layer)
                        or (
                            "deferred_by_selective_execution"
                            if layer in deferred
                            else "disabled_by_selective_execution"
                        )
                    ),
                })
        return blocks

    def _execution_layer_recommended_next_fix(
        self,
        suspected_breakpoint,
        budget_blocks,
        selective_execution_blocks,
    ):

        if budget_blocks:
            return "surface_budget_block_before_runtime_execution"
        if selective_execution_blocks:
            return "surface_selective_execution_block_before_runtime_execution"
        if suspected_breakpoint == "tool_selection_to_execution_plan":
            return "add_intent_compiler_from_selected_tools_to_runtime_tool_requests"
        if suspected_breakpoint == "tool_selection_to_runtime_stage":
            return "add_stage_compiler_or_explicit_non_stage_diagnostic_for_selected_tools"
        if suspected_breakpoint == "route_to_execution_node_compilation":
            return "map_active_routes_to_execution_nodes_or_record_prune_reasons"
        return "no_execution_layer_drop_detected"

    def _dependency_activation_state(self, dependency_time, requested=False):

        attempted = self.performance_counters.get(
            "dependency_activation_attempted",
            0,
        )
        executed = self.performance_counters.get(
            "dependency_chains_executed",
            0,
        )
        skipped = self.performance_counters.get(
            "dependency_reasoning_skipped",
            0,
        )
        failed = self.performance_counters.get(
            "dependency_chain_generation_failed",
            0,
        )
        successful = self.performance_counters.get(
            "dependency_chain_generation_successful",
            0,
        )
        if executed > 0:
            return "COMPLETED"
        if attempted <= 0 and skipped <= 0 and failed <= 0 and successful <= 0:
            return "REQUESTED" if requested else "NOT_REQUESTED"
        if skipped > 0 and executed <= 0:
            return "SKIPPED"
        if failed > 0 and successful <= 0:
            return "FAILED"
        if successful > 0 and executed <= 0:
            return "SKIPPED"
        if attempted > 0:
            return "REQUESTED"
        return "REQUESTED" if requested else "NOT_REQUESTED"

    def _finalize_observability_report(
        self,
        base_report,
        adaptive_cache_report,
        adaptive_reuse_report,
        context_reuse_report,
    ):

        sources = {
            "dependency_runtime": {
                "dependency_chains_executed":
                base_report.get("dependency_chains_executed", 0),
                "dependency_chain_depth":
                base_report.get("dependency_chain_depth", 0),
                "dependency_chain_coverage":
                base_report.get("dependency_chain_coverage", 0.0),
                "dependency_reasoning_skipped":
                base_report.get("dependency_reasoning_skipped", 0),
                "dependency_activation_state":
                base_report.get("dependency_activation_state"),
                "dependency_time": base_report.get("dependency_time", 0.0),
                "dependency_executor_cache_hits":
                base_report.get("dependency_executor_cache_hits", 0),
                "dependency_executor_cache_misses":
                base_report.get("dependency_executor_cache_misses", 0),
            },
            "context_registry": {
                "context_count": base_report.get("context_count", 0),
                "registered_context_count":
                base_report.get("registered_context_count", 0),
            "semantic_context_count":
            base_report.get("semantic_context_count", 0),
            "process_context_count":
            base_report.get("process_context_count", 0),
                "context_created": base_report.get("context_created", 0),
                "context_registered": base_report.get("context_registered", 0),
                "context_consumed": base_report.get("context_consumed", 0),
                "context_lost": base_report.get("context_lost", 0),
            },
            "truth_candidate_engine": {
                "candidate_count": base_report.get("candidate_count", 0),
                "candidate_generated": base_report.get("candidate_generated", 0),
                "candidate_rejected": base_report.get("candidate_rejected", 0),
            },
            "truth_commit_engine": {
                "committed_count": base_report.get("truth_commit_count", 0),
                "truth_commit_count": base_report.get("truth_commit_count", 0),
                "truth_committed": base_report.get("truth_committed", 0),
                "truth_rejected": base_report.get("truth_rejected", 0),
            },
            "adaptive_reuse_engine": adaptive_reuse_report,
            "context_reuse_engine": context_reuse_report,
            "adaptive_cache_manager": adaptive_cache_report,
            "local_runtime_cache": {
                "cache_hits": base_report.get("cache_hits", 0),
                "cache_misses": base_report.get("cache_misses", 0),
                "cache_hit_rate": base_report.get("cache_hit_rate", 0.0),
            },
        }
        report = metric_authority_registry.reconcile(
            base_report,
            sources,
        )
        integrity_report = MetricIntegrityValidator().validate(report)
        observability_report = RuntimeTelemetryValidator().validate(report)
        report["metric_integrity_report"] = integrity_report
        report["runtime_observability_report"] = observability_report
        report["OBSERVABILITY_DASHBOARD"] = {
            "metric_consistency_score":
            observability_report["metric_consistency_score"],
            "dependency_integrity_score":
            observability_report["dependency_integrity_score"],
            "context_integrity_score":
            observability_report["context_integrity_score"],
            "truth_integrity_score":
            observability_report["truth_integrity_score"],
            "cache_integrity_score":
            observability_report["cache_integrity_score"],
            "reuse_integrity_score":
            observability_report["reuse_integrity_score"],
            "telemetry_health_score":
            observability_report["telemetry_health_score"],
            "contradictions":
            observability_report["contradictions"],
        }
        return report

    def attach_performance_intelligence(
        self,
        runtime_context,
    ):

        if not isinstance(runtime_context, dict):
            runtime_context = {}

        runtime_context = self._attach_execution_layer_audit_report(
            runtime_context,
        )

        performance_report = runtime_context.get(
            "performance_report",
            self.performance_report(),
        )

        runtime_context[
            "performance_report"
        ] = performance_report

        intelligence_report = (
            self.performance_reporter
            .build_report(
                runtime_context=runtime_context,
                performance_report=performance_report,
                profile_level=self.profile_level,
            )
        )

        runtime_context[
            "PERFORMANCE_REPORT"
        ] = intelligence_report
        runtime_context[
            "performance_intelligence_report"
        ] = intelligence_report
        runtime_context[
            "SECURITY_REPORT"
        ] = self.security_reporter.build_report()
        runtime_context[
            "security_report"
        ] = runtime_context[
            "SECURITY_REPORT"
        ]

        self.telemetry.record(
            "runtime",
            "total_runtime_seconds",
            performance_report.get("total_runtime_seconds", 0.0),
        )

        return runtime_context

    def _compact_final_context(self, context):

        level = self.reasoning_budget.get("report_level", "normal")
        context = self._attach_execution_layer_audit_report(context)
        if level == "full":
            return context

        context = context if isinstance(context, dict) else {}
        if (
            context.get("episode_completed") is True
            and context.get("shutdown_mode", "fast") == "fast"
        ):
            context = self.compact_report_builder.purge_heavy_objects(
                context,
            )

        compacted = self.compact_report_builder.compact_context(
            context,
            level=level,
        )
        report = compacted.get("compact_report", {})
        self.performance_counters["compact_reports_generated"] = (
            report.get("compact_reports_generated", 0)
        )
        self.performance_counters["heavy_keys_removed"] = (
            report.get("heavy_keys_removed", 0)
        )
        self.performance_counters["arrays_summarized"] = (
            report.get("arrays_summarized", 0)
        )
        self.performance_counters["repeated_reports_collapsed"] = (
            report.get("repeated_reports_collapsed", 0)
        )
        self.performance_counters[
            "final_context_size_estimate_before"
        ] = report.get("final_context_size_estimate_before", 0)
        self.performance_counters[
            "final_context_size_estimate_after"
        ] = report.get("final_context_size_estimate_after", 0)
        compacted["performance_report"] = (
            self.compact_report_builder.compact_performance_report(
                self.performance_report(),
            )
        )
        return compacted

    def _ensure_prediction_before_evaluation(self, runtime_context):

        runtime_context = (
            runtime_context
            if isinstance(runtime_context, dict)
            else {}
        )

        if runtime_context.get("predicted_output") is not None:
            runtime_context["prediction_pipeline_report"] = {
                "status": "prediction_available",
                "prediction_source": "upstream_stage",
                "inference_stage_status": (
                    runtime_context
                    .get("inference_stage_report", {})
                    .get("status")
                ),
                "transformation_stage_status": (
                    runtime_context
                    .get("transformation_stage_report", {})
                    .get("status")
                ),
            }
            return runtime_context

        input_grid = runtime_context.get("input_grid")
        if hasattr(input_grid, "grid"):
            predicted_output = input_grid.grid.copy()
        else:
            predicted_output = input_grid

        prediction_pipeline_report = {
            "status": "fallback_prediction_produced",
            "prediction_source": "identity_baseline",
            "reason": "predicted_output_missing_before_evaluation",
            "success_state": "PREDICTION_FALLBACK_IDENTITY",
            "inference_stage_status": (
                runtime_context
                .get("inference_stage_report", {})
                .get("status")
            ),
            "transformation_stage_status": (
                runtime_context
                .get("transformation_stage_report", {})
                .get("status")
            ),
            "reasoning_report_status": (
                runtime_context
                .get("reasoning_report", {})
                .get("status")
            ),
            "transformation_report_status": (
                runtime_context
                .get("transformation_report", {})
                .get("status")
            ),
            "pipeline_disconnect_detected": True,
        }

        if predicted_output is None:
            prediction_pipeline_report.update({
                "status": "prediction_unavailable",
                "prediction_source": None,
                "reason": "input_grid_missing_before_evaluation",
            })
            runtime_context[
                "prediction_pipeline_report"
            ] = prediction_pipeline_report
            return runtime_context

        runtime_context["predicted_output"] = predicted_output
        runtime_context["candidate_origin_report"] = build_candidate_origin_report(
            producer_component="legacy_pipeline_prediction_guard",
            producer_operation_id="identity_baseline_fallback",
            candidate_id="current_candidate",
            transformation_source="input_grid",
            prediction_source="identity_baseline",
            source_report=prediction_pipeline_report,
            run_id=runtime_context.get("run_id"),
            task_id=runtime_context.get("task_id") or runtime_context.get("task_path"),
        )
        runtime_context["CANDIDATE_ORIGIN_REPORT"] = (
            runtime_context["candidate_origin_report"]
        )
        runtime_context["prediction_pipeline_report"] = (
            prediction_pipeline_report
        )
        runtime_context["prediction_fallback_used"] = True
        runtime_context["prediction_fallback_reason"] = (
            "predicted_output_missing_before_evaluation"
        )
        runtime_context["success_state"] = "PREDICTION_FALLBACK_IDENTITY"
        return runtime_context

    def run_safe_self_repair_cycle(
        self,
        runtime_context,
        trigger="runtime_check",
    ):

        if not isinstance(runtime_context, dict):
            runtime_context = {}

        repair_report = (
            self.self_repair_engine
            .run_operational_repair_cycle(runtime_context)
        )
        repaired_context = repair_report.pop(
            "runtime_context",
            runtime_context,
        )
        if not isinstance(repaired_context, dict):
            repaired_context = runtime_context

        repair_report[
            "trigger"
        ] = trigger
        repaired_context[
            "SELF_REPAIR_REPORT"
        ] = repair_report
        repaired_context[
            "self_repair_report"
        ] = repair_report
        repaired_context[
            "self_repair_state"
        ] = {
            "anomaly_count": len(
                repair_report.get("anomalies_detected", [])
            ),
            "repair_count": len(
                repair_report.get("repairs_executed", [])
            ),
            "trigger": trigger,
        }
        repaired_context[
            "SECURITY_REPORT"
        ] = self.security_reporter.build_report()
        repaired_context[
            "security_report"
        ] = repaired_context[
            "SECURITY_REPORT"
        ]

        self.runtime.bulk_update_context(repaired_context)
        self.telemetry.record(
            "self_repair",
            "anomalies_detected",
            len(repair_report.get("anomalies_detected", [])),
        )
        return repaired_context

    # ========================================
    # PREPARE TASK RUN
    # ========================================

    def prepare_task_run(self):

        self.runtime = RuntimeState()
        self.run_scoped_budget_authority_context = {}
        self.stage_execution_history = []
        self.completed_stages = []
        self.failed_stages = []
        self.cached_pipeline_result = None
        self.dependency_chain_executor.clear_shared_cache()
        self.meta_supervisor.reset_episode()
        self.pre_reasoning_router.reset()
        self.adaptive_reuse_engine = AdaptiveReuseEngine(
            cache_manager=self.adaptive_cache_manager,
        )
        self._start_performance_cycle()

    # ========================================
    # BOOT RUNTIME
    # ========================================

    def boot_runtime(self):

        runtime_context = (
            self.runtime.get_context()
        )

        runtime_context = (
            self.normalize_runtime_context(
                runtime_context
            )
        )

        runtime_context[
            "runtime_boot"
        ] = {
            "boot_state": "completed",
            "timestamp": str(datetime.utcnow())
        }

        world_governance_report = (
            self.world_governance_kernel
            .build_report()
        )

        runtime_context[
            "WORLD_GOVERNANCE_REPORT"
        ] = world_governance_report.get(
            "WORLD_GOVERNANCE_REPORT",
            {},
        )

        runtime_context[
            "world_governance_report"
        ] = world_governance_report

        task_budget = (
            self.cognitive_budget_controller
            .assign_budget(runtime_context)
        )
        runtime_context[
            "task_budget"
        ] = task_budget.as_dict()

        knowledge_reuse_report = (
            self.knowledge_strategy_reuse_engine
            .find_reusable_strategy(
                runtime_context,
                runtime_context,
            )
        )
        knowledge_reuse_gate_report = (
            self.knowledge_reuse_gate
            .evaluate(
                runtime_context,
                knowledge_reuse_report,
            )
        )
        knowledge_optimization_report = (
            self.knowledge_optimization_reporter
            .build_report(
                {
                    **knowledge_reuse_report,
                    "thinking_avoidance_rate":
                    1.0
                    if knowledge_reuse_gate_report.get(
                        "skip_deep_reasoning"
                    )
                    else 0.0,
                }
            )
        )
        runtime_context[
            "knowledge_reuse_report"
        ] = knowledge_reuse_report
        runtime_context[
            "knowledge_reuse_gate_report"
        ] = knowledge_reuse_gate_report
        runtime_context[
            "KNOWLEDGE_OPTIMIZATION_REPORT"
        ] = knowledge_optimization_report.get(
            "KNOWLEDGE_OPTIMIZATION_REPORT",
            {},
        )
        incentive_boot_report = (
            self.incentive_reporter
            .build_report()
        )
        runtime_context[
            "CONSTITUTIONAL_INCENTIVE_REPORT"
        ] = incentive_boot_report.get(
            "CONSTITUTIONAL_INCENTIVE_REPORT",
            {},
        )
        runtime_context[
            "COGNITIVE_ECONOMY_REPORT"
        ] = incentive_boot_report.get(
            "COGNITIVE_ECONOMY_REPORT",
            {},
        )

        self.semantic_memory_retriever.index_memory(
            runtime_context
        )

        cluster_report = (
            self.semantic_cluster_engine
            .cluster_memory(runtime_context)
        )

        runtime_context[
            "semantic_cluster_report"
        ] = cluster_report

        delta_snapshot = (
            self.context_delta_engine
            .detect_changes(runtime_context)
        )

        runtime_context[
            "context_delta_snapshot"
        ] = delta_snapshot

        self.runtime.bulk_update_context(
            runtime_context
        )

        return runtime_context

    # ========================================
    # STAGE EXECUTION
    # ========================================

    def _deep_task_budget_exceeded_report(self, runtime_context, next_stage=None):

        if self.reasoning_budget.get("mode") != "deep":
            return None
        deep_budget = self.reasoning_budget.get("deep_budget", {})
        elapsed = round(
            time.perf_counter()
            - self.performance_counters.get("task_start", time.perf_counter()),
            4,
        )
        if not deep_mode_budget_manager.task_budget_exceeded(
            elapsed,
            deep_budget,
        ):
            return None
        report = {
            "system": "deep_mode_task_guard",
            "warning": "TASK_RUNTIME_BUDGET_EXCEEDED",
            "task_runtime_seconds": elapsed,
            "max_task_runtime_seconds":
            deep_budget.get("max_task_runtime_seconds", 30.0),
            "next_stage_deferred": next_stage,
            "partial_diagnostics_saved": True,
        }
        runtime_context["TASK_RUNTIME_BUDGET_EXCEEDED"] = report
        runtime_context["task_runtime_budget_exceeded"] = True
        runtime_context["termination_reason"] = "TASK_RUNTIME_BUDGET_EXCEEDED"
        runtime_context["incomplete_due_to_budget"] = True
        return report

    def _attach_stage_context_observation(
        self,
        stage_report,
        before_context,
        after_context,
        sequence,
    ):

        try:
            delta = build_topology_context_delta(
                before_context,
                after_context,
            )
        except Exception as error:
            delta = {
                "context_delta_status": "UNAVAILABLE",
                "context_delta_error": repr(error),
                "context_keys_before": [],
                "context_keys_after": [],
                "context_keys_added": [],
                "context_keys_removed": [],
                "context_keys_changed": [],
            }

        stage_report.update({
            "entry_sequence": sequence,
            "exit_sequence": sequence,
            **delta,
            "emitted_artifact_types": self._stage_emitted_artifact_types(
                after_context,
            ),
        })
        return stage_report

    def _stage_emitted_artifact_types(self, runtime_context):

        if not isinstance(runtime_context, dict):
            return []
        emitted = []
        for key, artifact_type in (
            ("current_candidate", "candidate"),
            ("predicted_output", "prediction"),
            ("evaluation_result", "evaluation"),
            ("evaluation_report", "evaluation"),
            ("CURRENT_CANDIDATE_ORIGIN_REPORT", "candidate_origin"),
            ("RUNTIME_BUDGET_ENFORCEMENT_REPORT", "budget"),
            ("runtime_budget_enforcement_report", "budget"),
            ("ACTIVE_RUNTIME_REACHABILITY_AUDIT", "reachability_audit"),
            ("active_runtime_reachability_audit", "reachability_audit"),
        ):
            if key in runtime_context:
                emitted.append(artifact_type)
        return sorted(set(emitted))

    def _attach_runtime_topology_observation(
        self,
        runtime_context,
        execution_trace=None,
        *,
        write_artifact=True,
    ):

        runtime_context = runtime_context if isinstance(runtime_context, dict) else {}
        trace = (
            execution_trace
            if isinstance(execution_trace, list)
            else runtime_context.get("execution_trace", [])
        )
        try:
            report = build_runtime_topology_observation_report(
                runtime_context=runtime_context,
                execution_trace=trace,
                pipeline_stages=self.pipeline_stages,
                execution_mode=(
                    self.reasoning_budget.get("mode")
                    if isinstance(self.reasoning_budget, dict)
                    else None
                ),
                report_level=(
                    self.reasoning_budget.get("report_level")
                    if isinstance(self.reasoning_budget, dict)
                    else None
                ),
                expected_run_id=runtime_context.get("run_id"),
            )
            runtime_context[
                "RUNTIME_TOPOLOGY_OBSERVATION_REPORT"
            ] = report
            runtime_context[
                "runtime_topology_observation_report"
            ] = report
            if write_artifact:
                write_report = persist_runtime_topology_observation_report(
                    report,
                )
                runtime_context[
                    "RUNTIME_TOPOLOGY_OBSERVATION_WRITE_REPORT"
                ] = write_report
                runtime_context[
                    "runtime_topology_observation_write_report"
                ] = write_report
            return runtime_context
        except Exception as error:
            runtime_context[
                "RUNTIME_TOPOLOGY_OBSERVATION_REPORT"
            ] = {
                "schema_version": "1.0",
                "report_type": "RUNTIME_TOPOLOGY_OBSERVATION_REPORT",
                "authority": "OBSERVATION_ONLY",
                "behavioral_authority": "NONE",
                "observation_failure_preserves_task_execution": True,
                "observation_error": repr(error),
            }
            return runtime_context

    def run_stage_cycle(self):

        stage_cycle_start = time.perf_counter()
        runtime_context = (
            self.runtime.get_context()
        )

        execution_trace = []
        stage_sequence = 0

        for stage in self.pipeline_stages:

            stage_name = stage.get(
                "stage_name"
            )
            stage_sequence += 1

            budget_report = self._deep_task_budget_exceeded_report(
                runtime_context,
                next_stage=stage_name,
            )
            if budget_report:
                execution_trace.append({
                    "stage_name": stage_name,
                    "status": "deferred",
                    "reason": "TASK_RUNTIME_BUDGET_EXCEEDED",
                })
                break

            stage_callable = stage.get(
                "callable"
            )

            stage_report = {
                "stage_name": stage_name,
                "status": "initialized"
            }
            stage_context_before = dict(runtime_context)

            failure_error = None

            try:

                stage_layer = {
                    "task_loading": "task_loader",
                    "grid_analysis": "grid_analysis",
                    "object_detection": "object_detection",
                    "pattern_rule": "pattern_rule",
                    "inference": "inference",
                    "transformation": "transformation_solver",
                    "evaluation": "evaluation",
                    "self_improvement": "self_improvement",
                }.get(stage_name, stage_name)

                if not self._layer_allowed(
                    stage_layer,
                    runtime_context,
                ):

                    skipped = self._router_skipped_report(
                        stage_layer,
                        runtime_context,
                    )
                    stage_report[
                        "status"
                    ] = "skipped"
                    stage_report[
                        "report_state"
                    ] = "skipped"
                    stage_report[
                        "reason"
                    ] = skipped["skip_reason"]
                    runtime_context[
                        f"{stage_name}_report"
                    ] = skipped
                    stage_report = self._attach_stage_context_observation(
                        stage_report,
                        stage_context_before,
                        runtime_context,
                        stage_sequence,
                    )
                    execution_trace.append(
                        stage_report
                    )
                    self.stage_execution_history.append(
                        stage_report
                    )
                    continue

                supervisor_action = {
                    "inference": "reasoning",
                    "transformation": "program_synthesis",
                    "self_improvement": "self_improvement",
                }.get(stage_name)

                if (
                    supervisor_action is not None
                    and not self.meta_supervisor.is_action_allowed(
                        supervisor_action
                    )
                ):

                    stage_report[
                        "status"
                    ] = "skipped"
                    stage_report[
                        "reason"
                    ] = "blocked_by_meta_supervisor"
                    stage_report[
                        "cognitive_directive"
                    ] = (
                        self.meta_supervisor.current_directive.as_report()
                        if self.meta_supervisor.current_directive is not None
                        else {}
                    )
                    stage_report = self._attach_stage_context_observation(
                        stage_report,
                        stage_context_before,
                        runtime_context,
                        stage_sequence,
                    )
                    execution_trace.append(
                        stage_report
                    )
                    self.stage_execution_history.append(
                        stage_report
                    )
                    continue

                if (
                    stage_name == "self_improvement"
                    and not self.runtime.is_meta_action_enabled(
                        "RUN_SELF_IMPROVEMENT"
                    )
                ):

                    stage_report[
                        "status"
                    ] = "skipped"
                    stage_report[
                        "reason"
                    ] = "meta_decision_disabled_self_improvement"
                    stage_report = self._attach_stage_context_observation(
                        stage_report,
                        stage_context_before,
                        runtime_context,
                        stage_sequence,
                    )
                    execution_trace.append(
                        stage_report
                    )
                    self.stage_execution_history.append(
                        stage_report
                    )
                    continue

                self.runtime.set_stage(
                    stage_name
                )

                if stage_name == "grid_analysis":
                    context_integrity_guard.require(
                        runtime_context,
                        "grid_analysis",
                        ("input_grid", "output_grid"),
                    )

                if stage_name == "evaluation":
                    runtime_context = (
                        self._ensure_dependency_context_before_evaluation(
                            runtime_context,
                        )
                    )
                    runtime_context = (
                        self._ensure_prediction_before_evaluation(
                            runtime_context,
                        )
                    )

                runtime_context = (
                    stage_callable(runtime_context)
                )

                if not isinstance(runtime_context, dict):
                    runtime_context = {}
                preserved_context = {
                    **self.runtime.get_context(),
                    **self.run_scoped_budget_authority_context,
                }
                for authority_key in (
                    "authoritative_execution_plan",
                    "authoritative_execution_plan_reference",
                    "experimental_budget_request",
                    "experimental_budget_grant",
                ):
                    if (
                        authority_key in preserved_context
                        and authority_key not in runtime_context
                    ):
                        runtime_context[authority_key] = preserved_context[
                            authority_key
                        ]

                stage_report[
                    "status"
                ] = "completed"

                self.completed_stages.append(
                    stage_name
                )

                self.runtime.complete_stage(
                    stage_name
                )
                stage_report = self._attach_stage_context_observation(
                    stage_report,
                    stage_context_before,
                    runtime_context,
                    stage_sequence,
                )

                if stage_name == "task_loading":

                    self.run_task_recognition(
                        runtime_context
                    )

                    self._build_pre_reasoning_execution_plan(
                        runtime_context
                    )

                    memory_decision = (
                        self.run_memory_lookup_and_change_detection(
                            runtime_context
                        )
                    )

                    cached_result = memory_decision.get(
                        "cached_result"
                    )

                    if cached_result is not None:

                        runtime_context.update(cached_result)
                        runtime_context[
                            "pipeline_cache_hit"
                        ] = True
                        self.cached_pipeline_result = runtime_context
                        execution_trace.append(
                            stage_report
                        )
                        self.stage_execution_history.append(
                            stage_report
                        )
                        break

                    self.allocate_cognitive_budget_after_memory_lookup(
                        runtime_context
                    )

                if (
                    stage_name == "evaluation"
                ):

                    if (
                        runtime_context.get(
                            "fast_minimal_evaluation_closure",
                            {},
                        ).get("enabled") is True
                    ):

                        stage_report[
                            "fast_minimal_evaluation_closure"
                        ] = True
                        stage_report[
                            "post_evaluation_work_skipped"
                        ] = True
                        execution_trace.append(
                            stage_report
                        )
                        self.stage_execution_history.append(
                            stage_report
                        )
                        break

                    if runtime_context.get("episode_completed") is True:
                        runtime_context[
                            "post_success_isolation"
                        ] = {
                            "enabled": True,
                            "disabled_operations": [
                                "context_discovery",
                                "concept_promotion",
                                "truth_validation",
                                "governance_reanalysis",
                                "architecture_scans",
                                "strategy_search",
                                "deep_reasoning",
                            ],
                            "allowed_operations": [
                                "memory_commit",
                                "reward_commit",
                                "minimal_reporting",
                                "resource_cleanup",
                                "shutdown",
                            ],
                        }
                    else:
                        self.run_motivation_cycle(runtime_context)
                        runtime_context = self.runtime.get_context()
                        runtime_context = self.run_safe_self_repair_cycle(
                            runtime_context,
                            trigger="after_evaluation",
                        )

                    runtime_context = (
                        self.run_dependency_context_activation_audit_cycle(
                            runtime_context,
                        )
                    )

                if (
                    stage_name == "evaluation"
                    and (
                        self.run_meta_decision_cycle(runtime_context)
                        .get("action") == "STOP_AFTER_SUCCESS"
                    )
                    and self._terminal_success_shutdown_allowed(
                        runtime_context
                    )
                ):

                    runtime_context = self._record_minimal_success(
                        runtime_context
                    )
                    success_state = (
                        self._first_context_mapping(
                            runtime_context,
                            ["evaluation_result", "evaluation_report"],
                        ).get("success_state")
                    )
                    termination_reason = runtime_context.get(
                        "termination_reason",
                        "EXACT_SUCCESS"
                    )
                    shutdown_mode = runtime_context.get(
                        "shutdown_mode",
                        "fast"
                    )
                    runtime_context[
                        "post_success_shutdown"
                    ] = {
                        "enabled": True,
                        "mode": shutdown_mode,
                        "success_state": success_state,
                        "episode_completed": True,
                        "termination_reason": termination_reason,
                        "self_improvement_skipped": True,
                        "strategy_evolution_skipped": True,
                        "deep_introspection_skipped": True,
                        "curiosity_expansion_skipped": True,
                        "reward_optimization_skipped": True,
                        "governance_rehearsal_skipped": True,
                        "failure_memory_update_skipped": True,
                        "deep_validation_skipped": (
                            shutdown_mode == "fast"
                        ),
                        "temporal_promotion_checks_skipped": (
                            shutdown_mode == "fast"
                        ),
                        "full_memory_report_skipped": (
                            shutdown_mode == "fast"
                        ),
                        "reason": termination_reason,
                        "timestamp": str(datetime.utcnow()),
                    }
                    execution_trace.append(
                        stage_report
                    )
                    self.stage_execution_history.append(
                        stage_report
                    )
                    break

            except Exception as error:

                failure_error = error

                stage_report[
                    "status"
                ] = "failed"

                stage_report[
                    "error"
                ] = repr(error)

                self.failed_stages.append(
                    stage_name
                )

                self.runtime.fail_stage(
                    stage_name
                )
                stage_report = self._attach_stage_context_observation(
                    stage_report,
                    stage_context_before,
                    runtime_context,
                    stage_sequence,
                )

            execution_trace.append(
                stage_report
            )

            self.stage_execution_history.append(
                stage_report
            )

            if stage_report[
                "status"
            ] == "failed":

                self._record_module_timing(
                    "stage_cycle",
                    stage_cycle_start,
                )
                raise RuntimeError(
                    f"Pipeline stage failed: {stage_name}"
                ) from failure_error

            budget_report = self._deep_task_budget_exceeded_report(
                runtime_context,
                next_stage="next_stage",
            )
            if budget_report:
                break

        runtime_context[
            "execution_trace"
        ] = execution_trace
        runtime_context = self._attach_runtime_topology_observation(
            runtime_context,
            execution_trace,
        )

        self.runtime.bulk_update_context(
            runtime_context
        )
        self._record_module_timing(
            "stage_cycle",
            stage_cycle_start,
        )
        return runtime_context

    def run_dependency_context_activation_audit_cycle(
        self,
        runtime_context=None,
    ):

        runtime_context = (
            runtime_context
            if isinstance(runtime_context, dict)
            else self.runtime.get_context()
        )
        activation_report = dict(
            runtime_context.get(
                "dependency_context_activation_report",
                {},
            )
            or {}
        )

        dependency_chains = runtime_context.get(
            "process_dependency_chains",
            {},
        )
        dependency_ready = (
            isinstance(dependency_chains, dict)
            and bool(dependency_chains)
        )
        if not dependency_ready:
            self.run_dependency_reasoning_cycle()
            runtime_context = self.runtime.get_context()
            dependency_chains = runtime_context.get(
                "process_dependency_chains",
                {},
            )
            dependency_ready = (
                isinstance(dependency_chains, dict)
                and bool(dependency_chains)
            )
            activation_report["dependency_runtime_invoked"] = True
        else:
            activation_report["dependency_runtime_invoked"] = False

        process_semantic_report = runtime_context.get(
            "process_semantic_report",
            {},
        )
        process_semantic_ready = (
            isinstance(process_semantic_report, dict)
            and process_semantic_report.get("report_state") == "final"
            and not process_semantic_report.get("skipped")
        )
        if dependency_ready and not process_semantic_ready:
            self.run_process_semantic_cycle()
            runtime_context = self.runtime.get_context()
            activation_report["process_semantic_runtime_invoked"] = True
        else:
            activation_report["process_semantic_runtime_invoked"] = False

        semantic_context_report = runtime_context.get(
            "semantic_context_report",
            {},
        )
        context_ready = (
            isinstance(semantic_context_report, dict)
            and int(
                semantic_context_report.get(
                    "semantic_context_count",
                    semantic_context_report.get("result_count", 0),
                )
                or 0
            ) > 0
        )
        if dependency_ready and not context_ready:
            self.run_context_truth_advancement_cycle()
            runtime_context = self.runtime.get_context()
            activation_report["context_truth_runtime_invoked"] = True
        else:
            activation_report["context_truth_runtime_invoked"] = False

        activation_report.update({
            "system": "dependency_context_activation_audit",
            "report_state": "final",
            "semantic_concepts_available": bool(
                runtime_context.get("semantic_abstractions")
                or runtime_context.get("epistemic_hypotheses")
                or runtime_context.get("prioritized_concepts")
            ),
            "dependency_chains_available": dependency_ready,
            "context_count": self.performance_counters.get(
                "context_count",
                0,
            ),
            "dependency_chains_executed": self.performance_counters.get(
                "dependency_chains_executed",
                0,
            ),
            "cache_hits": self.performance_counters.get("cache_hits", 0),
            "cache_misses": self.performance_counters.get("cache_misses", 0),
        })
        runtime_context[
            "dependency_context_activation_report"
        ] = activation_report
        self.runtime.bulk_update_context(runtime_context)
        return runtime_context

    def _ensure_dependency_context_before_evaluation(
        self,
        runtime_context,
    ):

        runtime_context = (
            runtime_context
            if isinstance(runtime_context, dict)
            else self.runtime.get_context()
        )
        dependency_report = runtime_context.get(
            "dependency_reasoning_report",
            {},
        )
        dependency_chains = runtime_context.get(
            "process_dependency_chains",
            {},
        )
        dependency_ready = (
            isinstance(dependency_chains, dict)
            and bool(dependency_chains)
        )
        dependency_report_final = (
            isinstance(dependency_report, dict)
            and dependency_report.get("report_state") in {"final", "skipped"}
        )
        dependency_requested = (
            self._dependency_reasoning_requested(runtime_context)
            or self.runtime.is_tool_enabled("dependency_reasoning")
            or bool(
                runtime_context.get("semantic_abstractions")
                or runtime_context.get("epistemic_hypotheses")
                or runtime_context.get("prioritized_concepts")
            )
        )

        if dependency_requested:
            runtime_context["runtime_tool_requests"] = {
                **runtime_context.get("runtime_tool_requests", {}),
                "dependency_reasoning": {
                    "tool_name": "dependency_reasoning",
                    "request_state": "REQUESTED",
                    "requested_by": "pre_evaluation_barrier",
                },
            }
            runtime_context["dependency_lifecycle_report"] = {
                **runtime_context.get("dependency_lifecycle_report", {}),
                "system": "dependency_runtime",
                "report_state": "pending",
                "dependency_activation_state": "REQUESTED",
                "dependency_requested_by": "pre_evaluation_barrier",
                "dependency_chains_executed": 0,
                "dependency_outputs_generated": 0,
            }

        activation_report = {
            "system": "dependency_context_pre_evaluation_barrier",
            "report_state": "final",
            "stage": "before_evaluation",
            "dependency_requested": dependency_requested,
            "dependency_runtime_invoked": False,
            "process_semantic_runtime_invoked": False,
            "context_truth_runtime_invoked": False,
        }

        if dependency_requested and (
            not dependency_report_final or not dependency_ready
        ):
            self.run_dependency_reasoning_cycle()
            runtime_context = self.runtime.get_context()
            dependency_chains = runtime_context.get(
                "process_dependency_chains",
                {},
            )
            dependency_ready = (
                isinstance(dependency_chains, dict)
                and bool(dependency_chains)
            )
            activation_report["dependency_runtime_invoked"] = True

        process_semantic_report = runtime_context.get(
            "process_semantic_report",
            {},
        )
        process_semantic_ready = (
            isinstance(process_semantic_report, dict)
            and process_semantic_report.get("report_state") == "final"
            and not process_semantic_report.get("skipped")
        )
        if dependency_ready and not process_semantic_ready:
            self.run_process_semantic_cycle()
            runtime_context = self.runtime.get_context()
            activation_report["process_semantic_runtime_invoked"] = True

        semantic_context_report = runtime_context.get(
            "semantic_context_report",
            {},
        )
        semantic_context_ready = (
            isinstance(semantic_context_report, dict)
            and int(
                semantic_context_report.get(
                    "semantic_context_count",
                    semantic_context_report.get("result_count", 0),
                )
                or 0
            ) > 0
        )
        if dependency_ready and not semantic_context_ready:
            self.run_context_truth_advancement_cycle()
            runtime_context = self.runtime.get_context()
            activation_report["context_truth_runtime_invoked"] = True

        registry_contexts = (
            self.context_registry.all_contexts()
            if hasattr(self.context_registry, "all_contexts")
            else []
        )
        activation_report.update({
            "dependency_chains_available": dependency_ready,
            "process_context_count": sum(
                1
                for context in registry_contexts
                if context.get("context_type") == "PROCESS_CONTEXT"
            ),
            "semantic_context_count": sum(
                1
                for context in registry_contexts
                if context.get("context_type") == "SEMANTIC_CONTEXT"
            ),
            "context_count": len(registry_contexts),
            "dependency_chains_executed":
            self.performance_counters.get("dependency_chains_executed", 0),
        })
        runtime_context[
            "dependency_context_pre_evaluation_barrier"
        ] = activation_report
        runtime_context[
            "dependency_context_activation_report"
        ] = {
            **runtime_context.get("dependency_context_activation_report", {}),
            **activation_report,
        }
        self.runtime.bulk_update_context(runtime_context)
        return runtime_context

    def _first_context_mapping(self, runtime_context, keys):

        for key in keys:
            value = runtime_context.get(key)
            if isinstance(value, dict):
                return value
        return {}

    def _identity_governance_stable(self, runtime_context):

        stable_states = {
            "IDENTITY_GOVERNANCE_STABLE",
            "STABLE",
            "stable",
        }
        candidate_sources = [
            runtime_context,
            runtime_context.get("identity_governance_report", {}),
            runtime_context.get("cognitive_identity_report", {}),
            runtime_context.get("identity_stability_report", {}),
            runtime_context.get("truth_commitment_report", {}),
            runtime_context.get("governance_report", {}),
        ]

        for source in candidate_sources:
            if not isinstance(source, dict):
                continue
            state = source.get("identity_governance_state")
            if state in stable_states:
                return True
            if source.get("identity_stable") is True:
                return True

        for commitment in runtime_context.get("truth_commitments", []):
            if not isinstance(commitment, dict):
                continue
            metadata = commitment.get("metadata", {})
            state = commitment.get(
                "identity_governance_state",
                metadata.get("identity_governance_state")
                if isinstance(metadata, dict)
                else None,
            )
            if state in stable_states:
                return True

        return False

    def _exact_success_shutdown_allowed(self, runtime_context):

        evaluation_result = self._first_context_mapping(
            runtime_context,
            ["evaluation_result", "evaluation_report"],
        )
        transformation_report = self._first_context_mapping(
            runtime_context,
            ["transformation_report", "transformation_stage_report"],
        )
        gate_report = self._first_context_mapping(
            runtime_context,
            ["world_model_gate_report"],
        ) or transformation_report.get("world_model_gate", {})
        integrity_report = self._first_context_mapping(
            runtime_context,
            ["execution_integrity_report"],
        ) or transformation_report.get("execution_integrity", {})

        return (
            evaluation_result.get("exact_success") is True
            and evaluation_result.get("difference_count") == 0
            and integrity_report.get("integrity_preserved") is True
            and gate_report.get("execution_authorized") is True
            and self._identity_governance_stable(runtime_context)
        )

    def _terminal_success_shutdown_allowed(self, runtime_context):

        evaluation_result = self._first_context_mapping(
            runtime_context,
            ["evaluation_result", "evaluation_report"],
        )
        transformation_report = self._first_context_mapping(
            runtime_context,
            ["transformation_report", "transformation_stage_report"],
        )
        gate_report = self._first_context_mapping(
            runtime_context,
            ["world_model_gate_report"],
        ) or transformation_report.get("world_model_gate", {})
        integrity_report = self._first_context_mapping(
            runtime_context,
            ["execution_integrity_report"],
        ) or transformation_report.get("execution_integrity", {})
        success_state = evaluation_result.get(
            "success_state",
            runtime_context.get("success_state"),
        )

        terminal_success = (
            self._exact_success_shutdown_allowed(runtime_context)
            or (
                success_state == "SUCCESS_WITH_RESIDUALS"
                and evaluation_result.get("episode_completed") is True
                and evaluation_result.get("failure_detected") is False
                and gate_report.get("execution_authorized") is True
                and integrity_report.get("integrity_preserved") is True
                and self._identity_governance_stable(runtime_context)
            )
            or (
                success_state == "LEARNING_PROGRESS"
                and evaluation_result.get("episode_completed") is True
                and evaluation_result.get("retry_allowed") is False
                and evaluation_result.get("failure_detected") is False
            )
        )

        return bool(terminal_success)

    def _record_minimal_success(self, runtime_context):

        metadata = self._cache_metadata(runtime_context)
        task_report = runtime_context.get(
            "task_complexity_report",
            {},
        )
        evaluation_result = runtime_context.get(
            "evaluation_result",
            {},
        )
        transformation_localization = runtime_context.get(
            "transformation_localization",
            {},
        )
        localized_program = transformation_localization.get(
            "localized_program",
            runtime_context.get("synthesized_program"),
        ) if isinstance(transformation_localization, dict) else (
            runtime_context.get("synthesized_program")
        )

        success_record = {
            "task_signature": task_report.get(
                "task_signature",
                self._runtime_signature(runtime_context),
            ),
            "winning_strategy": runtime_context.get(
                "winner_hypothesis",
                runtime_context.get("best_hypothesis"),
            ),
            "localized_program": localized_program,
            "prediction_accuracy": evaluation_result.get(
                "accuracy",
                runtime_context.get("prediction_accuracy"),
            ),
            "success_state": evaluation_result.get(
                "success_state",
                runtime_context.get("success_state"),
            ),
            "residual_analysis": runtime_context.get(
                "residual_analysis",
            ),
            "timestamp": str(datetime.utcnow()),
            "concept_version_hash": metadata.get("concept_version_hash"),
        }

        runtime_context[
            "minimal_success_record"
        ] = success_record
        runtime_context[
            "post_success_minimal_record_stored"
        ] = True
        return runtime_context

    def build_meta_layer_audit_report(self):

        active_imports = {
            "meta_controller.py": [
                "runtime.pipeline",
                "runtime.stages.inference",
            ],
            "meta_selection_engine.py": ["runtime.pipeline"],
            "adaptive_strategy_injector.py": [
                "runtime.pipeline",
                "runtime.stages.inference",
            ],
            "discovery_engine.py": ["runtime.pipeline"],
            "curiosity_engine.py": ["runtime.pipeline"],
            "abstraction_engine.py": ["runtime.pipeline"],
            "meta_cognition_engine.py": ["runtime.pipeline"],
            "knowledge_expansion_engine.py": ["runtime.pipeline"],
            "autonomous_research_engine.py": ["runtime.pipeline"],
            "cognitive_ecosystem.py": ["runtime.pipeline"],
            "cognitive_genome.py": ["runtime.pipeline"],
            "cognitive_society.py": ["runtime.pipeline"],
            "consciousness_engine.py": ["runtime.pipeline"],
            "civilization_engine.py": ["runtime.pipeline"],
            "self_rewrite_engine.py": ["runtime.pipeline"],
        }
        executed = {
            "meta_controller.py",
            "adaptive_strategy_injector.py",
        }
        affects = {
            "meta_controller.py": [
                "reasoning_depth",
                "active_routes",
                "strategy_evolution",
                "self_improvement",
                "shutdown/finalization",
            ],
            "adaptive_strategy_injector.py": [
                "active_routes",
                "strategy_evolution",
                "hypothesis_count",
                "memory_usage",
            ],
        }
        priority_3 = {
            "autonomous_research_engine.py",
            "cognitive_ecosystem.py",
            "cognitive_genome.py",
            "cognitive_society.py",
            "consciousness_engine.py",
            "civilization_engine.py",
            "self_rewrite_engine.py",
        }

        report = []
        for file_name in sorted(active_imports):
            active = file_name in executed
            affected = set(affects.get(file_name, []))
            report.append({
                "file": file_name,
                "imported_by": active_imports[file_name],
                "active_in_runtime": active,
                "affects_reasoning_depth":
                "reasoning_depth" in affected,
                "affects_active_routes":
                "active_routes" in affected,
                "affects_shutdown":
                "shutdown/finalization" in affected,
                "affects_self_improvement":
                "self_improvement" in affected,
                "affects_strategy_evolution":
                "strategy_evolution" in affected,
                "legacy_risk": (
                    "high"
                    if active
                    else "medium"
                    if file_name not in priority_3
                    else "experimental_legacy"
                ),
                "recommended_action": (
                    "rehabilitated_as_meta_executive_controller"
                    if file_name == "meta_controller.py"
                    else "gate_with_meta_decision"
                    if active
                    else "mark_experimental_legacy_until_executed"
                    if file_name in priority_3
                    else "wrap_before_future_execution"
                ),
                "executed_during_adaptive_main": active,
                "consumes_modern_signals": (
                    file_name == "meta_controller.py"
                ),
                "ignores_modern_constraints": (
                    file_name != "meta_controller.py"
                ),
            })

        return {
            "system": "META_LAYER_AUDIT_REPORT",
            "scope": "runtime/meta",
            "files": report,
            "summary": {
                "active_meta_files": len(executed),
                "imported_meta_files": len(active_imports),
                "priority_3_marked_experimental": len(priority_3),
            },
            "timestamp": str(datetime.utcnow()),
        }

    def _apply_meta_decision_to_budget(
        self,
        decision_report,
        reasoning_budget=None,
    ):

        if not isinstance(decision_report, dict):
            return reasoning_budget

        max_depth = decision_report.get("max_reasoning_depth")
        max_routes = decision_report.get("max_active_routes")

        if max_depth is not None:
            max_depth = max(0, int(max_depth))
            self.reasoning_budget[
                "max_reasoning_depth"
            ] = max_depth
            self.reasoning_budget[
                "max_chain_depth"
            ] = min(
                self.reasoning_budget.get("max_chain_depth", max_depth),
                max(1, max_depth or 1),
            )
            self.reasoning_budget[
                "max_dependency_depth"
            ] = min(
                self.reasoning_budget.get(
                    "max_dependency_depth",
                    max_depth,
                ),
                max(1, max_depth or 1),
            )
            if reasoning_budget is not None:
                reasoning_budget.max_reasoning_depth = max_depth
                reasoning_budget.max_dependency_depth = min(
                    reasoning_budget.max_dependency_depth,
                    max(1, max_depth or 1),
                )

        if max_routes is not None:
            max_routes = max(0, int(max_routes))
            self.reasoning_budget[
                "max_active_routes"
            ] = max_routes
            self.reasoning_budget[
                "max_concepts"
            ] = min(
                self.reasoning_budget.get("max_concepts", max_routes),
                max(1, max_routes or 1),
            )
            if reasoning_budget is not None:
                reasoning_budget.max_active_routes = max_routes
                reasoning_budget.max_hypotheses = min(
                    reasoning_budget.max_hypotheses,
                    max(1, max_routes or 1),
                )

        if decision_report.get("enable_governance") is False:
            self.reasoning_budget[
                "full_governance_enabled"
            ] = False

        if decision_report.get("shutdown_mode") == "fast":
            self.post_success_mode = "fast"

        return reasoning_budget

    def run_meta_decision_cycle(
        self,
        runtime_context,
    ):

        decision = self.meta_controller_engine.decide(
            runtime_context=runtime_context,
            task_profile=self.runtime.current_task_profile,
            reasoning_budget=self.runtime.current_reasoning_budget,
            tool_selection=runtime_context.get("tool_selection"),
            cache_status=runtime_context.get("memory_lookup_report"),
            localization_status=runtime_context.get(
                "transformation_localization"
            ),
            world_model_report=runtime_context.get(
                "world_model_gate_report"
            ),
            evaluation_report=runtime_context.get("evaluation_result"),
            governance_status=runtime_context.get("governance_report"),
        )
        decision_report = self.runtime.apply_meta_decision(decision)
        self._apply_meta_decision_to_budget(
            decision_report,
            self.runtime.current_reasoning_budget,
        )
        runtime_context.update(self.runtime.get_context())
        runtime_context[
            "meta_layer_audit_report"
        ] = self.build_meta_layer_audit_report()
        runtime_context[
            "META_LAYER_AUDIT_REPORT"
        ] = runtime_context[
            "meta_layer_audit_report"
        ]
        runtime_context[
            "META_EXECUTIVE_REPORT"
        ] = runtime_context.get(
            "meta_executive_report",
            decision_report,
        )
        self.runtime.bulk_update_context(runtime_context)
        return decision_report

    def run_meta_supervisor_cycle(
        self,
        runtime_context,
    ):

        if not isinstance(runtime_context, dict):
            runtime_context = {}

        directive = self.meta_supervisor.supervise(runtime_context)

        runtime_context = self.meta_supervisor.apply_to_context(
            runtime_context
        )

        if directive.action in {
            "REUSE_EXECUTABLE_PROGRAM",
            "STOP_COGNITION",
        }:

            self.reasoning_budget[
                "max_reasoning_depth"
            ] = 0
            self.reasoning_budget[
                "max_active_routes"
            ] = 0

            if self.runtime.current_reasoning_budget is not None:
                self.runtime.current_reasoning_budget.max_reasoning_depth = 0
                self.runtime.current_reasoning_budget.max_active_routes = 0

        if directive.allow_governance is False:
            self.reasoning_budget[
                "full_governance_enabled"
            ] = False

        if directive.shutdown_mode == "fast":
            self.post_success_mode = "fast"

        self.runtime.bulk_update_context(runtime_context)
        return directive.as_report()

    def run_motivation_cycle(
        self,
        runtime_context,
    ):

        reports = motivation_system.evaluate(runtime_context)
        runtime_context.update(reports)
        motivation_report = reports.get("motivation_report", {})
        if isinstance(motivation_report, dict):
            runtime_context[
                "exploration_drive"
            ] = motivation_report.get("exploration_drive")
            runtime_context[
                "failure_tolerance"
            ] = motivation_report.get("failure_tolerance")
            runtime_context[
                "curiosity_balance"
            ] = motivation_report.get("curiosity_balance")

        self.runtime.bulk_update_context(runtime_context)
        return reports

    # ========================================
    # TASK COMPLEXITY ANALYSIS
    # ========================================

    def run_task_recognition(
        self,
        runtime_context
    ):

        task_profile = (
            self.task_complexity_analyzer
            .analyze(runtime_context)
        )

        cognitive_cost = (
            self.cognitive_cost_estimator
            .estimate(task_profile)
        )

        task_profile.estimated_cost = (
            cognitive_cost.total_cost
        )

        task_signature = (
            self.task_complexity_analyzer
            .last_task_signature
        )

        profile_observation = (
            self.runtime_profile_manager
            .record(
                task_profile,
                cognitive_cost,
                task_signature=task_signature
            )
        )

        task_complexity_report = (
            self.task_complexity_analyzer
            .build_report(
                task_profile,
                task_signature=task_signature
            )
        )

        cognitive_cost_report = (
            self.cognitive_cost_estimator
            .build_report(cognitive_cost)
        )

        runtime_context[
            "current_task_profile"
        ] = task_profile

        runtime_context[
            "current_cognitive_cost"
        ] = cognitive_cost

        runtime_context[
            "task_complexity_report"
        ] = task_complexity_report

        runtime_context[
            "cognitive_cost_report"
        ] = cognitive_cost_report

        runtime_context[
            "runtime_profile_observation"
        ] = profile_observation

        runtime_context[
            "runtime_profile_manager_report"
        ] = (
            self.runtime_profile_manager
            .build_report()
        )

        runtime_context[
            "task_recognition_report"
        ] = {
            "recognition_state": "completed",
            "task_signature": task_signature,
            "complexity": task_profile.complexity,
            "historical_similarity":
            task_profile.historical_similarity,
            "question_order": [
                "Have I seen this before?",
                "Has anything important changed?",
                "Can I safely reuse prior cognition?",
                "Do I need validation?",
                "Do I need reasoning?",
            ],
        }

        self.runtime.set_observational_profile(
            task_profile=task_profile,
            cognitive_cost=cognitive_cost
        )

        return {
            "task_profile": task_profile,
            "cognitive_cost": cognitive_cost,
            "task_complexity_report": task_complexity_report,
            "cognitive_cost_report": cognitive_cost_report,
            "task_recognition_report":
            runtime_context["task_recognition_report"],
        }

    def allocate_cognitive_budget_after_memory_lookup(
        self,
        runtime_context
    ):

        if isinstance(runtime_context, dict):
            runtime_context.update(self.run_scoped_budget_authority_context)

        task_profile = runtime_context.get(
            "current_task_profile"
        )

        cognitive_cost = runtime_context.get(
            "current_cognitive_cost"
        )

        if task_profile is None or cognitive_cost is None:

            recognition = self.run_task_recognition(
                runtime_context
            )
            task_profile = recognition["task_profile"]
            cognitive_cost = recognition["cognitive_cost"]

        task_complexity_report = runtime_context.get(
            "task_complexity_report",
            {},
        )

        cognitive_cost_report = runtime_context.get(
            "cognitive_cost_report",
            {},
        )

        reasoning_budget = (
            self.cognitive_budget_engine
            .allocate(
                task_profile=task_profile,
                cognitive_cost=cognitive_cost,
                requested_mode=self.requested_budget_mode
            )
        )

        from runtime.search.adaptive_search_policy import (
            adaptive_search_policy_engine,
        )

        adaptive_search_policy_report = (
            adaptive_search_policy_engine.plan(
                task_analysis=task_profile,
                performance_report=runtime_context.get(
                    "performance_report",
                    {},
                ),
            )
        )
        adaptive_search_policy_engine.apply_budget(
            reasoning_budget,
            adaptive_search_policy_report,
        )
        from runtime.budget.experimental_budget_authority import (
            resolve_runtime_budget_authority,
        )

        budget_authority_resolution = resolve_runtime_budget_authority(
            normal_budget=reasoning_budget,
            runtime_context=runtime_context,
        )
        reasoning_budget = budget_authority_resolution["budget"]
        runtime_context["runtime_budget_binding"] = (
            budget_authority_resolution["binding"]
        )
        runtime_context["RUNTIME_BUDGET_BINDING"] = (
            budget_authority_resolution["binding"]
        )
        runtime_context["experimental_budget_grant_applied"] = (
            budget_authority_resolution.get("grant_applied") is True
        )
        runtime_context["adaptive_search_policy_report"] = (
            adaptive_search_policy_report
        )
        runtime_context["ADAPTIVE_SEARCH_POLICY_REPORT"] = (
            adaptive_search_policy_report
        )

        tool_selection = (
            self.tool_selection_engine
            .select(
                task_profile=task_profile,
                reasoning_budget=reasoning_budget
            )
        )

        cognitive_budget_report = (
            self.cognitive_budget_engine
            .build_report(reasoning_budget)
        )

        tool_selection_report = (
            self.tool_selection_engine
            .build_report(tool_selection)
        )

        self.reasoning_budget.update(
            self.cognitive_budget_engine
            .as_legacy_pipeline_budget(reasoning_budget)
        )

        runtime_context[
            "current_reasoning_budget"
        ] = reasoning_budget

        runtime_context[
            "cognitive_budget_report"
        ] = cognitive_budget_report

        runtime_context[
            "tool_selection"
        ] = tool_selection

        runtime_context[
            "tool_selection_report"
        ] = tool_selection_report

        runtime_context[
            "budget_allocation_after_memory_lookup"
        ] = True

        runtime_context[
            "memory_decision_before_budget"
        ] = runtime_context.get(
            "cognitive_execution_decision",
            {},
        )

        self.runtime.bulk_update_context(
            runtime_context
        )

        self.runtime.apply_reasoning_budget(
            reasoning_budget
        )

        self.runtime.apply_tool_selection(
            tool_selection
        )

        synchronized_context = dict(
            self.runtime.get_context()
        )
        runtime_context.update(
            synchronized_context
        )

        runtime_context = self._build_execution_planner_context(
            runtime_context,
            reasoning_budget=reasoning_budget,
        )

        runtime_context = self._dispatch_execution_plan_context(
            runtime_context,
            reasoning_budget=reasoning_budget,
        )

        self.runtime.bulk_update_context(
            runtime_context
        )

        meta_decision_report = self.run_meta_decision_cycle(
            runtime_context
        )
        budget_authority_resolution = resolve_runtime_budget_authority(
            normal_budget=reasoning_budget,
            runtime_context=runtime_context,
        )
        reasoning_budget = budget_authority_resolution["budget"]
        runtime_context["runtime_budget_binding"] = (
            budget_authority_resolution["binding"]
        )
        runtime_context["RUNTIME_BUDGET_BINDING"] = (
            budget_authority_resolution["binding"]
        )
        runtime_context["experimental_budget_grant_applied"] = (
            budget_authority_resolution.get("grant_applied") is True
        )
        self.reasoning_budget.update(
            self.cognitive_budget_engine
            .as_legacy_pipeline_budget(reasoning_budget)
        )
        self.runtime.apply_reasoning_budget(
            reasoning_budget
        )

        cognitive_budget_report = (
            self.cognitive_budget_engine
            .build_report(reasoning_budget)
        )
        budget_binding = runtime_context.get("runtime_budget_binding", {})
        if isinstance(budget_binding, dict):
            cognitive_budget_report.update({
                "runtime_budget_source": budget_binding.get("budget_source"),
                "budget_source": budget_binding.get("budget_source"),
                "runtime_budget_binding_state": budget_binding.get(
                    "binding_state"
                ),
                "experiment_id": budget_binding.get("experiment_id"),
                "effective_max_active_routes": budget_binding.get(
                    "effective_max_active_routes"
                ),
                "effective_max_reasoning_depth": budget_binding.get(
                    "effective_max_reasoning_depth"
                ),
                "effective_max_dependency_depth": budget_binding.get(
                    "effective_max_dependency_depth"
                ),
                "effective_max_hypotheses": budget_binding.get(
                    "effective_max_hypotheses"
                ),
            })
        runtime_context[
            "cognitive_budget_report"
        ] = cognitive_budget_report

        print(
            "\nTASK COMPLEXITY REPORT:\n"
        )
        print(task_complexity_report)

        print(
            "\nCOGNITIVE COST REPORT:\n"
        )
        print(cognitive_cost_report)

        print(
            "\nCOGNITIVE BUDGET REPORT:\n"
        )
        print(cognitive_budget_report)

        print(
            "\nTOOL SELECTION REPORT:\n"
        )
        print(tool_selection_report)

        return {
            "task_profile": task_profile,
            "cognitive_cost": cognitive_cost,
            "task_complexity_report": task_complexity_report,
            "cognitive_cost_report": cognitive_cost_report,
            "reasoning_budget": reasoning_budget,
            "tool_selection": tool_selection,
            "cognitive_budget_report": cognitive_budget_report,
            "tool_selection_report": tool_selection_report,
            "meta_decision_report": meta_decision_report,
            "adaptive_search_policy_report":
            adaptive_search_policy_report,
        }

    def run_task_complexity_analysis(
        self,
        runtime_context
    ):

        recognition = self.run_task_recognition(
            runtime_context
        )
        allocation = self.allocate_cognitive_budget_after_memory_lookup(
            runtime_context
        )
        return {
            **recognition,
            **allocation,
        }

    def run_memory_lookup_and_change_detection(
        self,
        runtime_context
    ):

        metadata = self._cache_metadata(runtime_context)
        pipeline_cache_key = self._pipeline_result_cache_key(
            runtime_context
        )
        cached_result = self.lookup_cached_pipeline_result(
            runtime_context
        )
        stable_truth_exists = bool(
            runtime_context.get("reusable_truth_commitments")
            or runtime_context.get("truth_commitments")
        )
        concept_version_hash_unchanged = bool(
            metadata.get("concept_version_hash")
            and metadata.get("concept_version_hash")
            in self.runtime.concept_version_hashes.values()
        )
        partial_match = (
            False
            if cached_result is not None
            else self._partial_memory_match_exists(
                runtime_context,
                metadata,
            )
        )

        if cached_result is not None:

            decision = "reuse_cached_result"
            reasoning_required = False
            validation_required = False
            self.performance_counters["reasoning_avoided"] += 1

        elif stable_truth_exists and concept_version_hash_unchanged:

            decision = "reuse_cached_result"
            reasoning_required = False
            validation_required = False
            self.performance_counters["reasoning_avoided"] += 1

        elif partial_match:

            decision = "validate_cached_result"
            reasoning_required = True
            validation_required = True

        else:

            decision = "execute_reasoning"
            reasoning_required = True
            validation_required = False

        memory_lookup_report = {
            "system": "memory_first_runtime",
            "pipeline_cache_key": pipeline_cache_key,
            "exact_cache_hit": cached_result is not None,
            "partial_match_exists": partial_match,
            "stable_truth_exists": stable_truth_exists,
            "concept_version_hash":
            metadata.get("concept_version_hash"),
            "concept_version_hash_unchanged":
            concept_version_hash_unchanged,
        }

        change_detection_report = {
            "system": "memory_first_change_detection",
            "evidence_hash": metadata.get("evidence_hash"),
            "dependency_hash": metadata.get("dependency_hash"),
            "context_hash": metadata.get("context_hash"),
            "concept_version_hash":
            metadata.get("concept_version_hash"),
            "important_change_detected":
            not concept_version_hash_unchanged
            and cached_result is None,
        }

        execution_decision = {
            "decision": decision,
            "reasoning_required": reasoning_required,
            "validation_required": validation_required,
            "governance_required": reasoning_required,
            "cached_result_available": cached_result is not None,
            "reasoning_is_fallback": True,
            "decision_order": [
                "Task Recognition",
                "Memory Lookup",
                "Change Detection",
                "Cognitive Budget Allocation",
                "Tool Selection",
                "Validation",
                "Reasoning if required",
            ],
        }

        runtime_context[
            "memory_lookup_report"
        ] = memory_lookup_report
        runtime_context[
            "change_detection_report"
        ] = change_detection_report
        runtime_context[
            "cognitive_execution_decision"
        ] = execution_decision

        return {
            "cached_result": cached_result,
            "memory_lookup_report": memory_lookup_report,
            "change_detection_report": change_detection_report,
            "cognitive_execution_decision": execution_decision,
        }

    def _partial_memory_match_exists(
        self,
        runtime_context,
        metadata,
    ):

        concepts = self._governance_reuse_concepts(
            runtime_context
        )
        if not concepts:
            concepts = [
                "process_semantics"
            ]

        for concept in concepts:

            cache_key = self.cognitive_cache_manager.concept_key(
                concept_name=concept,
                evidence_hash=metadata["evidence_hash"],
                dependency_hash=metadata["dependency_hash"],
                context_hash=metadata["context_hash"],
                runtime_version=metadata["runtime_version"],
            )
            entry = self.cognitive_cache_manager.lookup_concept(
                cache_key
            )
            if entry is not None:
                self.runtime.record_cache_hit(concept)
                self.performance_counters["cache_hits"] += 1
                return True

        return False

    def lookup_cached_pipeline_result(
        self,
        runtime_context
    ):

        cache_key = self._pipeline_result_cache_key(
            runtime_context
        )
        cached_result = self.cognitive_cache_manager.lookup(
            cache_key
        )

        if not isinstance(cached_result, dict):
            self.performance_counters["cache_misses"] += 1
            return None

        if not cached_result.get(
            "cache_safety_complete",
            False,
        ):
            self.performance_counters["cache_misses"] += 1
            return None

        self.performance_counters["cache_hits"] += 1
        cached_result[
            "pipeline_cache_report"
        ] = {
            "cache_state": "hit",
            "cache_key": cache_key,
            "safety_replay": True,
            "memory_first_reuse": True,
        }
        return cached_result

    def store_pipeline_result(
        self,
        runtime_context
    ):

        if not isinstance(runtime_context, dict):
            return None

        safety_complete = bool(
            runtime_context.get("governance_report")
            or runtime_context.get("cognitive_governance_report")
        )

        if not safety_complete:
            return None

        cache_key = self._pipeline_result_cache_key(
            runtime_context
        )
        runtime_context[
            "cache_safety_complete"
        ] = True
        self.cognitive_cache_manager.store(
            cache_key,
            runtime_context,
            metadata=self._cache_metadata(runtime_context),
        )
        return {
            "cache_state": "stored",
            "cache_key": cache_key,
            "cache_safety_complete": True,
        }

    # ========================================
    # REASONING
    # ========================================

    def run_reasoning_cycle(self):

        runtime_context = (
            self.runtime.get_context()
        )

        if not self._layer_allowed(
            "inference",
            runtime_context,
        ):

            runtime_context[
                "reasoning_report"
            ] = {
                **self._router_skipped_report(
                    "inference",
                    runtime_context,
                ),
                "system": "reasoning_orchestrator",
                "reasoning_invoked": False,
                "reasoning_depth": 0,
                "active_routes": 0,
            }
            self.runtime.bulk_update_context(runtime_context)
            return

        if not self.meta_supervisor.is_action_allowed("reasoning"):
            runtime_context[
                "reasoning_report"
            ] = {
                "system": "reasoning_orchestrator",
                "report_state": "skipped",
                "skipped": True,
                "status": "blocked_by_meta_supervisor",
                "reasoning_invoked": False,
                "reasoning_depth": 0,
                "active_routes": 0,
            }
            self.runtime.bulk_update_context(runtime_context)
            return

        cognitive_kernel_report = (
            self.cognitive_kernel_scheduler
            .run_cycle(runtime_context)
        )

        runtime_context[
            "cognitive_kernel_report"
        ] = cognitive_kernel_report

        enabled_subsystems = set(
            cognitive_kernel_report.get(
                "enabled_subsystems",
                []
            )
        )

        active_mode = cognitive_kernel_report.get(
            "active_mode",
            "reasoning_mode"
        )

        def skipped_report(system_name):

            return {
                "system":
                system_name,

                "status":
                "skipped_by_kernel_mode",

                "active_mode":
                active_mode
            }

        if "semantic_routing" in enabled_subsystems:

            runtime_context = (
                self.adaptive_semantic_control
                .run_predictive_routing(runtime_context)
            )

        else:

            runtime_context[
                "cognitive_predictive_routing_report"
            ] = skipped_report(
                "cognitive_predictive_routing"
            )

        if "cognitive_os" in enabled_subsystems:

            runtime_context = (
                self.cognitive_operating_system_layer
                .run_cycle(runtime_context)
            )

        else:

            runtime_context[
                "cognitive_operating_system_report"
            ] = skipped_report(
                "cognitive_operating_system_layer"
            )

        if "distributed_execution" in enabled_subsystems:

            runtime_context = (
                self.distributed_cognitive_execution
                .run_cycle(runtime_context)
            )

        else:

            runtime_context[
                "distributed_cognitive_execution_report"
            ] = skipped_report(
                "distributed_cognitive_execution"
            )

        if "semantic_fabric" in enabled_subsystems:

            runtime_context = (
                self.distributed_semantic_execution_fabric
                .run_cycle(runtime_context)
            )

        else:

            runtime_context[
                "distributed_semantic_execution_fabric_report"
            ] = skipped_report(
                "distributed_semantic_execution_fabric"
            )

        if "thermodynamics" in enabled_subsystems:

            runtime_context = (
                self.cognitive_thermodynamics
                .run_cycle(runtime_context)
            )

        else:

            runtime_context[
                "cognitive_thermodynamics_report"
            ] = skipped_report(
                "cognitive_thermodynamics"
            )

        if "causal_prediction" in enabled_subsystems:

            causal_world_simulation_report = (
                self.causal_world_simulator
                .run_cycle(runtime_context)
            )

        else:

            causal_world_simulation_report = (
                skipped_report(
                    "causal_world_simulator"
                )
            )

        runtime_context[
            "causal_world_simulation_report"
        ] = causal_world_simulation_report

        if "immune_system" in enabled_subsystems:

            cognitive_immune_system_report = (
                self.cognitive_immune_system_v2
                .run_cycle(runtime_context)
            )

        else:

            cognitive_immune_system_report = (
                skipped_report(
                    "cognitive_immune_system_v2"
                )
            )

        runtime_context[
            "cognitive_immune_system_v2_report"
        ] = cognitive_immune_system_report

        if "semantic_os" in enabled_subsystems:

            semantic_operating_system_report = (
                self.semantic_operating_system
                .run_cycle(runtime_context)
            )

        else:

            semantic_operating_system_report = (
                skipped_report(
                    "semantic_operating_system"
                )
            )

        runtime_context[
            "semantic_operating_system_report"
        ] = semantic_operating_system_report

        identity_stability_report = (
            self.identity_stability_core
            .run_cycle(runtime_context)
        )

        runtime_context[
            "identity_stability_report"
        ] = identity_stability_report

        cognitive_event_bus_report = (
            self.cognitive_event_bus
            .run_cycle(runtime_context)
        )

        runtime_context[
            "cognitive_event_bus_report"
        ] = cognitive_event_bus_report

        if "goal_hierarchy" in enabled_subsystems:

            goal_hierarchy_report = (
                self.goal_manager
                .run_cycle(runtime_context)
            )

        else:

            goal_hierarchy_report = (
                skipped_report(
                    "goal_hierarchy"
                )
            )

        runtime_context[
            "goal_hierarchy_report"
        ] = goal_hierarchy_report

        if "self_model" in enabled_subsystems:

            recursive_self_model_report = (
                self.recursive_self_model
                .run_cycle(runtime_context)
            )

        else:

            recursive_self_model_report = (
                skipped_report(
                    "recursive_self_model"
                )
            )

        runtime_context[
            "recursive_self_model_report"
        ] = recursive_self_model_report

        if "meta_executive" in enabled_subsystems:

            meta_cognitive_executive_report = (
                self.meta_cognitive_executive
                .run_cycle(runtime_context)
            )

        else:

            meta_cognitive_executive_report = (
                skipped_report(
                    "meta_cognitive_executive"
                )
            )

        runtime_context[
            "meta_cognitive_executive_report"
        ] = meta_cognitive_executive_report

        if "reasoning" in enabled_subsystems:

            reasoning_report = (
                self.reasoning_orchestrator
                .run_orchestration_cycle(
                    runtime_context
                )
            )

        else:

            reasoning_report = (
                skipped_report(
                    "reasoning_orchestrator"
                )
            )

        runtime_context[
            "reasoning_report"
        ] = reasoning_report

        self.runtime.bulk_update_context(
            runtime_context
        )

    # ========================================
    # DEPENDENCY REASONING
    # ========================================

    def run_dependency_reasoning_cycle(self):

        module_start = time.perf_counter()
        runtime_context = (
            self.runtime.get_context()
        )
        links_loaded = (
            self.dependency_chain_executor
            .memory
            .links_loaded
        )
        activation_decision = dependency_activation_manager.evaluate(
            runtime_context,
            runtime_context.get(
                "pre_reasoning_task_profile",
                runtime_context.get("task_profile", {}),
            ),
            links_loaded=links_loaded,
        )
        runtime_context["dependency_activation_manager_report"] = (
            activation_decision
        )
        runtime_context["dependency_activation_reason"] = (
            activation_decision.get("dependency_activation_reason")
        )
        detected_dependency_concepts = list(
            activation_decision.get("matched_signals", []) or []
        )
        for report_key in (
            "semantic_attribution_report",
            "introspection_report",
        ):
            report = runtime_context.get(report_key, {})
            if isinstance(report, dict):
                detected_dependency_concepts.extend(
                    report.get("attributed_concepts", []) or []
                )
                detected_dependency_concepts.extend(
                    report.get("concepts", []) or []
                )
        for item in runtime_context.get("semantic_abstractions", []) or []:
            if isinstance(item, dict):
                detected_dependency_concepts.append(item.get("concept"))
            else:
                detected_dependency_concepts.append(item)
        activation_trace = DependencyActivationTrace()
        activation_trace.detect_concepts(detected_dependency_concepts)
        enforcement = dependency_activation_enforcer.enforce(
            detected_dependency_concepts,
            runtime_context,
            trace=activation_trace,
        )
        runtime_context = enforcement["runtime_context"]
        activation_trace = enforcement["trace"]
        runtime_context["dependency_activation_enforcer_report"] = {
            key: value
            for key, value in enforcement.items()
            if key not in {"runtime_context", "trace"}
        }
        if activation_decision.get("activation_state") in {
            "DEPENDENCY_REQUIRED",
            "DEPENDENCY_RECOMMENDED",
        }:
            runtime_context = dependency_activation_manager.promote_request(
                runtime_context,
                activation_decision,
            )
            self.runtime.bulk_update_context(runtime_context)
        dependency_requested = self._dependency_reasoning_requested(
            runtime_context
        )
        if dependency_requested:
            runtime_context["dependency_lifecycle_report"] = {
                **runtime_context.get("dependency_lifecycle_report", {}),
                "system": "dependency_runtime",
                "report_state": "running",
                "dependency_activation_state": "EXECUTING",
                "dependency_requested_by": "tool_selection",
                "dependency_chains_executed": 0,
                "dependency_outputs_generated": 0,
            }
            runtime_context["dependency_runtime_requested"] = True

        if (
            not dependency_requested
            and not self._layer_allowed(
            "dependency_reasoning",
            runtime_context,
            )
        ):

            skipped = self._router_skipped_report(
                "dependency_reasoning",
                runtime_context,
            )
            link_usage = explain_dependency_link_usage({
                "process_dependency_links_loaded": links_loaded,
                "process_dependency_links_used": 0,
            })
            self.performance_counters["dependency_activation_attempted"] += int(
                links_loaded > 0
            )
            self.performance_counters["dependency_activation_blocked"] += int(
                links_loaded > 0
            )
            self.performance_counters["dependency_reasoning_skipped"] += 1
            self.performance_counters["process_dependency_links_skipped"] += (
                link_usage["dependency_links_skipped"]
            )
            dependency_time = round(time.perf_counter() - module_start, 4)
            skip_report = activation_trace.skip_report(
                requested_tool="dependency_reasoning",
                activation_attempted=bool(
                    link_usage["dependency_activation_attempted"]
                ),
                activation_blocked=bool(
                    link_usage["dependency_activation_blocked"]
                ),
                block_reason=skipped.get("skip_reason"),
                blocking_module="legacy_pipeline.run_dependency_reasoning_cycle",
                blocking_condition="layer_not_allowed",
            )
            activation_trace.exit_runtime(
                "dependency_reasoning",
                executed=False,
                failure=skipped.get("skip_reason"),
            )
            missing_warning = activation_trace.assert_requested_when_concepts_exist()
            runtime_context[
                "dependency_reasoning_report"
            ] = {
                **skipped,
                **link_usage,
                "reasoning_invoked": False,
                "dependency_activation_state": "SKIPPED",
                "dependency_time": dependency_time,
                "dependency_activation_reason":
                runtime_context.get("dependency_activation_reason")
                or skipped.get("activation_rule"),
                "dependency_chain_generation_attempted": False,
                "dependency_chain_generation_successful": False,
                "dependency_chain_generation_failed": False,
                "dependency_chain_failure_reason":
                skipped.get("skip_reason"),
                "DEPENDENCY_SKIP_REPORT": skip_report,
                "DEPENDENCY_ACTIVATION_TRACE_REPORT":
                activation_trace.report(),
                "DEPENDENCY_ACTIVATION_MISSING": missing_warning,
            }
            runtime_context[
                "process_dependency_chains"
            ] = {}
            runtime_context[
                "dependency_execution_trace"
            ] = [{
                "reasoning_invoked": False,
                "operator_available": True,
                **link_usage,
                "bypass_reason": skipped.get("skip_reason"),
            }]
            runtime_context["DEPENDENCY_ACTIVATION_TRACE"] = {
                "system": "dependency_activation_trace",
                "requested": dependency_requested,
                "selected": False,
                "executed": False,
                "skipped": True,
                "blocked": bool(link_usage["dependency_activation_blocked"]),
                "unused": links_loaded,
                "activation_state": "DEPENDENCY_NOT_REQUIRED",
                "dependency_activation_reason":
                runtime_context.get("dependency_activation_reason"),
                "dependency_skip_reason": skipped.get("skip_reason"),
                "process_dependency_links_loaded": links_loaded,
                "process_dependency_links_used": 0,
            }
            runtime_context["DEPENDENCY_SKIP_REPORT"] = skip_report
            runtime_context["DEPENDENCY_ACTIVATION_TRACE_REPORT"] = (
                activation_trace.report()
            )
            if missing_warning:
                runtime_context["DEPENDENCY_ACTIVATION_MISSING"] = missing_warning
            runtime_context[
                "dependency_lifecycle_report"
            ] = {
                "system": "dependency_runtime",
                "report_state": "final",
                "dependency_activation_state": "SKIPPED",
                "dependency_time": dependency_time,
                "dependency_chains_executed": 0,
                "dependency_outputs_generated": 0,
                "skip_reason": skipped.get("skip_reason"),
                "dependency_activation_reason":
                runtime_context.get("dependency_activation_reason"),
            }
            self.runtime.bulk_update_context(
                runtime_context
            )
            self._record_module_timing(
                "dependency_reasoning",
                module_start,
            )
            return

        if (
            not dependency_requested
            and not self.runtime.is_tool_enabled(
            "dependency_reasoning"
            )
        ):

            self.performance_counters["dependency_reasoning_skipped"] += 1
            dependency_time = round(time.perf_counter() - module_start, 4)
            runtime_context[
                "dependency_reasoning_report"
            ] = {
                "system": "dependency_execution_pipeline",
                "report_state": "skipped",
                "skipped": True,
                "operator_available": True,
                "reasoning_invoked": False,
                "dependency_activation_state": "SKIPPED",
                "dependency_time": dependency_time,
                "bypass_reason": "disabled_by_tool_selection",
                "max_chain_depth":
                self.reasoning_budget["max_chain_depth"],
                "telemetry_enabled":
                self.reasoning_budget["telemetry_enabled"],
                "report_level":
                self.reasoning_budget["report_level"],
            }
            link_usage = explain_dependency_link_usage({
                "process_dependency_links_loaded":
                self.dependency_chain_executor.memory.links_loaded,
                "process_dependency_links_used": 0,
            })
            runtime_context["dependency_reasoning_report"].update({
                **link_usage,
                "dependency_activation_reason":
                runtime_context.get("dependency_activation_reason"),
                "dependency_chain_generation_attempted": False,
                "dependency_chain_generation_successful": False,
                "dependency_chain_generation_failed": False,
                "dependency_chain_failure_reason":
                "disabled_by_tool_selection",
            })
            skip_report = activation_trace.skip_report(
                requested_tool="dependency_reasoning",
                activation_attempted=bool(
                    link_usage["dependency_activation_attempted"]
                ),
                activation_blocked=True,
                block_reason="disabled_by_tool_selection",
                blocking_module="legacy_pipeline.run_dependency_reasoning_cycle",
                blocking_condition="tool_not_requested_or_enabled",
            )
            activation_trace.exit_runtime(
                "dependency_reasoning",
                executed=False,
                failure="disabled_by_tool_selection",
            )
            missing_warning = activation_trace.assert_requested_when_concepts_exist()
            runtime_context["dependency_reasoning_report"].update({
                "DEPENDENCY_SKIP_REPORT": skip_report,
                "DEPENDENCY_ACTIVATION_TRACE_REPORT":
                activation_trace.report(),
                "DEPENDENCY_ACTIVATION_MISSING": missing_warning,
            })

            runtime_context[
                "process_dependency_chains"
            ] = {}

            runtime_context[
                "dependency_execution_trace"
            ] = []
            runtime_context["DEPENDENCY_ACTIVATION_TRACE"] = {
                "system": "dependency_activation_trace",
                "requested": dependency_requested,
                "selected": False,
                "executed": False,
                "skipped": True,
                "blocked": bool(link_usage["dependency_activation_blocked"]),
                "unused": link_usage["dependency_links_skipped"],
                "activation_state":
                activation_decision.get("activation_state"),
                "dependency_activation_reason":
                runtime_context.get("dependency_activation_reason"),
                "dependency_skip_reason": "disabled_by_tool_selection",
                "process_dependency_links_loaded":
                link_usage["process_dependency_links_loaded"],
                "process_dependency_links_used": 0,
            }
            runtime_context["DEPENDENCY_SKIP_REPORT"] = skip_report
            runtime_context["DEPENDENCY_ACTIVATION_TRACE_REPORT"] = (
                activation_trace.report()
            )
            if missing_warning:
                runtime_context["DEPENDENCY_ACTIVATION_MISSING"] = missing_warning
            runtime_context[
                "dependency_lifecycle_report"
            ] = {
                "system": "dependency_runtime",
                "report_state": "final",
                "dependency_activation_state": "SKIPPED",
                "dependency_time": dependency_time,
                "dependency_chains_executed": 0,
                "dependency_outputs_generated": 0,
                "skip_reason": "disabled_by_tool_selection",
                "dependency_activation_reason":
                runtime_context.get("dependency_activation_reason"),
            }

            self.runtime.bulk_update_context(
                runtime_context
            )
            self._record_module_timing(
                "dependency_reasoning",
                module_start,
            )
            return

        runtime_context["dependency_runtime_requested"] = True
        runtime_context["dependency_lifecycle_report"] = {
            **runtime_context.get("dependency_lifecycle_report", {}),
            "system": "dependency_runtime",
            "report_state": "running",
            "dependency_activation_state": "EXECUTING",
            "dependency_requested_by": "runtime_execution",
            "dependency_chains_executed": 0,
            "dependency_outputs_generated": 0,
        }

        concepts = self._dependency_reasoning_concepts(
            runtime_context
        )
        activation_trace.enter_runtime(
            "dependency_reasoning",
            concepts,
        )
        attribution_report = runtime_context.get(
            "semantic_attribution_report",
            {},
        )
        if not isinstance(attribution_report, dict):
            attribution_report = {}
        runtime_context["dependency_activation_bridge_report"] = {
            "system": "dependency_activation_bridge",
            "report_state": "active",
            "bridge_source": "concept_attribution",
            "attributed_concepts": list(
                attribution_report.get("attributed_concepts", []) or []
            ),
            "dependency_runnable_concepts": list(concepts),
            "dependency_runtime_requested": dependency_requested,
            "dependency_activation_state": (
                activation_decision.get("activation_state")
            ),
        }
        max_concepts = self.reasoning_budget.get("max_concepts")
        if max_concepts is not None:
            concepts = concepts[:max_concepts]
            runtime_context["dependency_activation_bridge_report"][
                "selected_dependency_concepts"
            ] = list(concepts)

        dependency_reports = {}
        dependency_traces = []
        self.performance_counters["dependency_activation_attempted"] += int(
            self.dependency_chain_executor.memory.links_loaded > 0
        )

        for concept in concepts:
            self.performance_counters[
                "dependency_chain_generation_attempted"
            ] += 1

            cache_key = self._dependency_cache_key(
                concept,
                runtime_context,
            )
            adaptive_dependency_key = self.adaptive_cache_manager.key(
                "dependency_snapshot",
                concept=concept,
                context_signature=self._runtime_signature(runtime_context),
                dependency_signature=self._dependency_memory_signature(),
            )
            adaptive_dependency_snapshot = (
                self.adaptive_cache_manager.get(
                    "dependency_snapshot",
                    key=adaptive_dependency_key,
                    context=runtime_context,
                )
            )
            if isinstance(adaptive_dependency_snapshot, dict):
                report = {
                    **adaptive_dependency_snapshot,
                    "system": "dependency_chain_executor",
                    "concept": concept,
                    "cache_hit": True,
                    "dependency_snapshot_reused": True,
                    "dependency_reasoning_skipped": True,
                    "chain": adaptive_dependency_snapshot.get(
                        "explanation_path_summary",
                        [],
                    ),
                    "resolved_dependency_chain":
                    adaptive_dependency_snapshot.get(
                        "explanation_path_summary",
                        [],
                    ),
                    "process_dependency_links_loaded":
                    adaptive_dependency_snapshot.get(
                        "process_dependency_links_loaded",
                        adaptive_dependency_snapshot.get(
                            "links_loaded",
                            self.dependency_chain_executor.memory.links_loaded,
                        ),
                    ),
                    "process_dependency_links_used":
                    adaptive_dependency_snapshot.get(
                        "process_dependency_links_used",
                        adaptive_dependency_snapshot.get("links_used", 0),
                    ),
                }
                link_usage = explain_dependency_link_usage(report)
                report.update({
                    **link_usage,
                    "dependency_skip_reason":
                    link_usage.get("dependency_skip_reason")
                    or "dependency_snapshot_reused",
                    "dependency_activation_reason":
                    runtime_context.get(
                        "pre_reasoning_execution_plan",
                        {},
                    ).get("dependency_activation_reason"),
                })
                self.runtime.record_cache_hit(concept)
                self.performance_counters["cache_hits"] += 1
                self.performance_counters["dependency_snapshot_hits"] += 1
                self.performance_counters["dependency_reasoning_skipped"] += 1
                self.performance_counters["process_dependency_links_used"] += (
                    link_usage["process_dependency_links_used"]
                )
                self.performance_counters["process_dependency_links_skipped"] += (
                    link_usage["dependency_links_skipped"]
                )
                self.performance_counters["concepts_processed"] += 1
                dependency_reports[concept] = report
                dependency_traces.append({
                    "concept": concept,
                    "cache_hit": True,
                    "adaptive_cache_reused": True,
                    "dependency_reasoning_skipped": True,
                    "dependency_activation_reason":
                    report.get("dependency_activation_reason"),
                    "process_dependency_links_used":
                    link_usage["process_dependency_links_used"],
                    "dependency_links_skipped":
                    link_usage["dependency_links_skipped"],
                    "dependency_skip_reason":
                    link_usage["dependency_skip_reason"],
                })
                continue

            cache_hit = (
                self.reasoning_budget.get("cache_dependencies", False)
                and cache_key in self.dependency_chain_cache
            )
            if cache_hit:
                report = dict(self.dependency_chain_cache[cache_key])
                report["cache_hit"] = True
                self.performance_counters["cache_hits"] += 1
            else:
                metadata = self._cache_metadata(runtime_context)
                concept_cache_key = (
                    self.cognitive_cache_manager
                    .concept_key(
                        concept_name=concept,
                        evidence_hash=metadata["evidence_hash"],
                        dependency_hash=metadata["dependency_hash"],
                        context_hash=metadata["context_hash"],
                        runtime_version=metadata["runtime_version"],
                    )
                )
                concept_version_hash = (
                    self.cognitive_cache_manager
                    .concept_version_hash(
                        metadata["evidence_hash"],
                        metadata["dependency_hash"],
                        metadata["context_hash"],
                    )
                )
                self.runtime.is_concept_stable(
                    concept,
                    concept_version_hash,
                )
                metadata["concept_version_hash"] = concept_version_hash
                concept_entry = (
                    self.cognitive_cache_manager
                    .lookup_concept(concept_cache_key)
                )

                if (
                    concept_entry is not None
                    and concept_entry.dependency_chain is not None
                ):
                    report = {
                        "system": "dependency_chain_executor",
                        "concept": concept,
                        "resolved_dependency_chain":
                        concept_entry.dependency_chain,
                        "chain": concept_entry.dependency_chain,
                        "dependency_chain_depth":
                        len(concept_entry.dependency_chain),
                        "dependency_explanation":
                        {
                            "explanation_path":
                            concept_entry.explanation_path or []
                        },
                        "dependency_explanation_quality": 1.0,
                        "explanation_quality": 1.0,
                        "cache_hit": True,
                        "concept_version_hash":
                        concept_version_hash,
                    }
                    self.runtime.record_cache_hit(concept)
                    self.performance_counters["cache_hits"] += 1
                else:
                    self.runtime.record_cache_miss(concept)
                    artifact_key = self._artifact_cache_key(
                        runtime_context,
                        artifact_type="dependency_chain",
                        concept_signature=concept,
                    )

                    def compute_dependency():

                        computed_report = (
                            self.dependency_chain_executor
                            .execute(
                            concept,
                            max_depth=self.reasoning_budget[
                                "max_dependency_depth"
                            ],
                        )
                        )
                        if computed_report.get("dependency_cache_hit"):
                            self.performance_counters[
                                "dependency_executor_cache_hits"
                            ] += 1
                            self.performance_counters[
                                "dependency_reasoning_skipped"
                            ] += 1
                        else:
                            self.performance_counters[
                                "dependency_executor_cache_misses"
                            ] += 1
                            self.performance_counters[
                                "dependency_chains_executed"
                            ] += 1
                        return computed_report

                    report, optimization_report = (
                        self.performance_optimizer
                        .lookup_or_compute(
                            self.cognitive_cache_manager,
                            artifact_key,
                            compute_dependency,
                            metadata=metadata,
                        )
                    )
                    report["cache_hit"] = (
                        optimization_report.get("cache_state") == "hit"
                    )
                    report["concept_version_hash"] = (
                        concept_version_hash
                    )
                    if report["cache_hit"]:
                        self.performance_counters["cache_hits"] += 1
                    else:
                        self.performance_counters["cache_misses"] += 1
                    self.cognitive_cache_manager.store_concept(
                        concept_cache_key,
                        dependency_chain=report.get(
                            "resolved_dependency_chain",
                            report.get("chain", []),
                        ),
                        explanation_path=report.get(
                            "dependency_explanation",
                            {},
                        ).get("explanation_path", []),
                        truth_commit_result=runtime_context.get(
                            "truth_commitments",
                            {},
                        ),
                    )
                if self.reasoning_budget.get(
                    "cache_dependencies",
                    False,
                ):
                    self.dependency_chain_cache[cache_key] = dict(report)
                if not report.get("cache_hit"):
                    snapshot = {
                        "concept": concept,
                        "snapshot_state": "ACTIVE",
                        "truth_state": runtime_context.get(
                            "final_commit_state",
                            "LOCKED_TRUTH_PRESERVED",
                        ),
                        "dependency_chain_depth": report.get(
                            "dependency_chain_depth",
                            len(report.get("chain", [])),
                        ),
                        "dependency_chain_coverage": report.get(
                            "dependency_chain_coverage",
                            report.get("coverage", 0.0),
                        ),
                        "dependency_coherence": report.get(
                            "dependency_coherence",
                            report.get("dependency_coherence_average", 0.0),
                        ),
                        "links_loaded": report.get(
                            "process_dependency_links_loaded",
                            0,
                        ),
                        "links_used": report.get(
                            "process_dependency_links_used",
                            len(report.get("chain", [])),
                        ),
                        "explanation_path_summary": [
                            str(item)
                            for item in report.get("chain", [])[:8]
                        ],
                        "dependency_signature":
                        self._dependency_memory_signature(),
                        "identity_runtime_state": runtime_context.get(
                            "identity_runtime_state",
                        ),
                        "identity_runtime_ready": runtime_context.get(
                            "identity_runtime_ready",
                        ),
                        "contextual_truth_supported": runtime_context.get(
                            "contextual_truth_supported",
                        ),
                        "reuse_count": 0,
                    }
                    self.adaptive_cache_manager.put(
                        "dependency_snapshot",
                        key=adaptive_dependency_key,
                        value=snapshot,
                        metadata={
                            "concept": concept,
                            "identity_runtime_state":
                            runtime_context.get("identity_runtime_state"),
                            "identity_runtime_ready":
                            runtime_context.get("identity_runtime_ready"),
                            "context_compatibility":
                            runtime_context.get("context_compatibility", 1.0),
                        },
                    )
                    self.performance_counters[
                        "dependency_snapshot_store_count"
                    ] += 1
                cache_hit = bool(report.get("cache_hit", False))

            if "process_dependency_links_loaded" not in report:
                report["process_dependency_links_loaded"] = (
                    report.get("links_loaded")
                    or self.dependency_chain_executor.memory.links_loaded
                )
            if "process_dependency_links_used" not in report:
                report["process_dependency_links_used"] = (
                    report.get("links_used")
                    or len(report.get("resolved_dependency_chain", []))
                    or len(report.get("chain", []))
                )
            if (
                report.get("process_dependency_links_used", 0) <= 0
                and report.get("dependency_chain_depth", 0) > 0
            ):
                report["process_dependency_links_used"] = min(
                    report.get("process_dependency_links_loaded", links_loaded),
                    max(
                        int(report.get("dependency_chain_depth", 0) or 0),
                        len(report.get("resolved_dependency_chain", [])),
                        len(report.get("chain", [])),
                    ),
                )
            link_usage = explain_dependency_link_usage(report)
            report.update({
                **link_usage,
                "dependency_activation_reason":
                runtime_context.get("dependency_activation_reason")
                or
                runtime_context.get(
                    "pre_reasoning_execution_plan",
                    {},
                ).get("dependency_activation_reason"),
                "dependency_chain_generation_attempted": True,
                "dependency_chain_generation_successful":
                report.get("dependency_chain_depth", 0) > 0,
                "dependency_chain_generation_failed":
                report.get("dependency_chain_depth", 0) <= 0,
                "dependency_chain_failure_reason":
                (
                    None
                    if report.get("dependency_chain_depth", 0) > 0
                    else link_usage.get("dependency_skip_reason")
                ),
            })
            self.performance_counters["process_dependency_links_used"] += (
                link_usage["process_dependency_links_used"]
            )
            self.performance_counters["process_dependency_links_skipped"] += (
                link_usage["dependency_links_skipped"]
            )
            if link_usage["dependency_activation_successful"]:
                self.performance_counters[
                    "dependency_activation_successful"
                ] += 1
                self.performance_counters[
                    "dependency_chain_generation_successful"
                ] += 1
            else:
                self.performance_counters[
                    "dependency_activation_blocked"
                ] += 1
                self.performance_counters[
                    "dependency_chain_generation_failed"
                ] += 1

            dependency_reports[concept] = report
            self.performance_counters["concepts_processed"] += 1

            trace = {
                "concept": concept,
                "cache_hit": cache_hit,
                "dependency_activation_attempted":
                link_usage["dependency_activation_attempted"],
                "dependency_activation_successful":
                link_usage["dependency_activation_successful"],
                "dependency_activation_blocked":
                link_usage["dependency_activation_blocked"],
                "dependency_activation_reason":
                report.get("dependency_activation_reason"),
                "dependency_links_skipped":
                link_usage["dependency_links_skipped"],
                "dependency_skip_reason":
                link_usage["dependency_skip_reason"],
                "memory_loaded": (
                    report.get(
                        "process_dependency_links_loaded",
                        0,
                    ) > 0
                ),
                "operator_available": True,
                "reasoning_invoked": True,
                "bypass_reason": None,
                "process_dependency_links_used":
                report.get("process_dependency_links_used", 0),
                "dependency_chain_depth":
                report.get("dependency_chain_depth", 0),
                "dependency_chain_coverage":
                report.get("dependency_chain_coverage", 0.0),
            }
            if self.reasoning_budget.get("telemetry_enabled", True):
                trace["dependency_explanation_quality"] = report.get(
                    "dependency_explanation_quality",
                    report.get("explanation_quality", 0.0),
                )
                trace["resolved_dependency_chain"] = report.get(
                    "resolved_dependency_chain",
                    report.get("chain", []),
                )
                if trace["resolved_dependency_chain"]:
                    self.performance_counters[
                        "explanation_paths_generated"
                    ] += 1
            dependency_traces.append(trace)

        if dependency_reports:

            primary_concept = concepts[0]
            primary_report = dependency_reports[primary_concept]

            runtime_context[
                "process_dependency_memory"
            ] = primary_report

            runtime_context[
                "dependency_chain_depth"
            ] = primary_report.get(
                "dependency_chain_depth",
                0,
            )

            runtime_context[
                "dependency_chain_coverage"
            ] = primary_report.get(
                "dependency_chain_coverage",
                0.0,
            )

            runtime_context[
                "dependency_explanation_quality"
            ] = primary_report.get(
                "dependency_explanation_quality",
                primary_report.get("explanation_quality", 0.0),
            )

            runtime_context[
                "dependency_coherence_average"
            ] = primary_report.get(
                "dependency_coherence_average",
                primary_report.get(
                    "dependency_coherence",
                    0.0,
                ),
            )

            runtime_context[
                "telemetry_enabled"
            ] = self.reasoning_budget.get(
                "telemetry_enabled",
                True,
            )

            telemetry_reduction = (
                self.cognitive_budget_engine
                .reduce_telemetry_if_saturated(
                    self.runtime.current_reasoning_budget,
                    runtime_context,
                )
            )
            runtime_context[
                "dynamic_telemetry_report"
            ] = telemetry_reduction
            self.reasoning_budget[
                "telemetry_enabled"
            ] = telemetry_reduction["telemetry_enabled"]
            self.reasoning_budget[
                "report_level"
            ] = (
                getattr(
                    self.runtime.current_reasoning_budget,
                    "report_level",
                    self.reasoning_budget.get("report_level", "normal"),
                )
            )

        runtime_context[
            "process_dependency_chains"
        ] = dependency_reports

        runtime_context[
            "dependency_execution_trace"
        ] = (
            dependency_traces
            if self.reasoning_budget.get("telemetry_enabled", True)
            else [
                {
                    "concept": item["concept"],
                    "cache_hit": item.get("cache_hit", False),
                    "reasoning_invoked": item.get(
                        "reasoning_invoked",
                        not item.get("cache_hit", False),
                    ),
                    "dependency_chain_depth":
                    item.get("dependency_chain_depth", 0),
                }
                for item in dependency_traces
            ]
        )
        dependency_time = round(time.perf_counter() - module_start, 4)
        dependency_lifecycle_state = self._dependency_activation_state(
            dependency_time,
            requested=dependency_requested,
        )
        if dependency_reports:
            activation_trace.exit_runtime(
                "dependency_reasoning",
                executed=True,
            )
        else:
            activation_trace.skip_report(
                requested_tool="dependency_reasoning",
                activation_attempted=bool(dependency_requested),
                activation_blocked=True,
                block_reason="no_dependency_concepts_available",
                blocking_module="legacy_pipeline.run_dependency_reasoning_cycle",
                blocking_condition="empty_dependency_concept_selection",
            )
            activation_trace.exit_runtime(
                "dependency_reasoning",
                executed=False,
                failure="no_dependency_concepts_available",
            )
        missing_warning = activation_trace.assert_requested_when_concepts_exist()
        runtime_context[
            "DEPENDENCY_EXECUTION_TRACE"
        ] = runtime_context["dependency_execution_trace"]
        loaded_total = (
            self.dependency_chain_executor
            .memory
            .links_loaded
        )
        used_total = self.performance_counters[
            "process_dependency_links_used"
        ]
        runtime_context["DEPENDENCY_ACTIVATION_TRACE"] = {
            "system": "dependency_activation_trace",
            "requested": dependency_requested,
            "selected": bool(concepts),
            "executed": bool(dependency_reports),
            "skipped": not bool(dependency_reports),
            "blocked": loaded_total > 0 and used_total <= 0,
            "unused": max(loaded_total - used_total, 0),
            "activation_state": (
                "DEPENDENCY_COMPLETED"
                if dependency_reports
                else activation_decision.get("activation_state")
            ),
            "dependency_activation_reason":
            runtime_context.get("dependency_activation_reason"),
            "dependency_skip_reason": (
                None
                if dependency_reports
                else "no_dependency_concepts_available"
            ),
            "process_dependency_links_loaded": loaded_total,
            "process_dependency_links_used": used_total,
            "dependency_usage_rate": (
                round(used_total / loaded_total, 4)
                if loaded_total
                else 0.0
            ),
        }
        runtime_context["DEPENDENCY_ACTIVATION_TRACE_REPORT"] = (
            activation_trace.report()
        )
        if activation_trace.skip_reasons:
            runtime_context["DEPENDENCY_SKIP_REPORT"] = (
                activation_trace.skip_reasons[-1]
            )
        if missing_warning:
            runtime_context["DEPENDENCY_ACTIVATION_MISSING"] = missing_warning
        runtime_context[
            "dependency_lifecycle_report"
        ] = {
            "system": "dependency_runtime",
            "report_state": "final",
            "dependency_activation_state": dependency_lifecycle_state,
            "dependency_lifecycle_states": [
                "NOT_REQUESTED",
                "REQUESTED",
                "ACTIVATED",
                "EXECUTING",
                "COMPLETED",
                "FAILED",
                "SKIPPED",
            ],
            "dependency_chains_executed":
            self.performance_counters["dependency_chains_executed"],
            "dependency_chain_generation_attempted":
            self.performance_counters["dependency_chain_generation_attempted"],
            "dependency_chain_generation_successful":
            self.performance_counters["dependency_chain_generation_successful"],
            "dependency_chain_generation_failed":
            self.performance_counters["dependency_chain_generation_failed"],
            "dependency_time": dependency_time,
            "dependency_outputs_generated": len(dependency_reports),
            "dependency_activation_reason":
            runtime_context.get("dependency_activation_reason"),
            "dependency_skip_reason":
            runtime_context["DEPENDENCY_ACTIVATION_TRACE"].get(
                "dependency_skip_reason"
            ),
            "dependency_usage_rate":
            runtime_context["DEPENDENCY_ACTIVATION_TRACE"].get(
                "dependency_usage_rate",
            ),
            "DEPENDENCY_ACTIVATION_TRACE_REPORT":
            runtime_context["DEPENDENCY_ACTIVATION_TRACE_REPORT"],
            "DEPENDENCY_SKIP_REPORT":
            runtime_context.get("DEPENDENCY_SKIP_REPORT"),
            "DEPENDENCY_ACTIVATION_MISSING":
            runtime_context.get("DEPENDENCY_ACTIVATION_MISSING"),
            "downstream_consumers": [
                "context_truth_advancement",
                "promotion_engine",
                "truth_candidate_engine",
                "truth_commit_engine",
            ],
        }

        runtime_context[
            "dependency_reasoning_report"
        ] = {
            "system": "dependency_execution_pipeline",
            "report_state": "final",
            "operator_available": True,
            "memory_loaded": (
                self.dependency_chain_executor
                .memory
                .links_loaded > 0
            ),
            "concepts": concepts,
            "reasoning_invoked": bool(dependency_reports),
            "max_chain_depth":
            self.reasoning_budget["max_dependency_depth"],
            "max_concepts":
            self.reasoning_budget["max_concepts"],
            "cache_dependencies":
            self.reasoning_budget["cache_dependencies"],
            "cache_hits":
            self.performance_counters["cache_hits"],
            "cache_misses":
            self.performance_counters["cache_misses"],
            "telemetry_enabled":
            self.reasoning_budget["telemetry_enabled"],
            "report_level":
            self.reasoning_budget["report_level"],
            "bypass_reason": (
                None
                if dependency_reports
                else "no_dependency_concepts_available"
            ),
            "dependency_activation_attempted":
            self.performance_counters["dependency_activation_attempted"] > 0,
            "dependency_activation_successful":
            self.performance_counters["dependency_activation_successful"] > 0,
            "dependency_activation_blocked":
            (
                self.performance_counters["dependency_activation_blocked"] > 0
                and self.performance_counters[
                    "dependency_activation_successful"
                ] == 0
            ),
            "dependency_activation_reason":
            runtime_context.get("dependency_activation_reason")
            or runtime_context.get(
                "pre_reasoning_execution_plan",
                {},
            ).get("dependency_activation_reason"),
            "dependency_chain_generation_attempted":
            self.performance_counters[
                "dependency_chain_generation_attempted"
            ] > 0,
            "dependency_chain_generation_successful":
            self.performance_counters[
                "dependency_chain_generation_successful"
            ] > 0,
            "dependency_chain_generation_failed":
            (
                self.performance_counters[
                    "dependency_chain_generation_failed"
                ] > 0
                and self.performance_counters[
                    "dependency_chain_generation_successful"
                ] == 0
            ),
            "dependency_chain_failure_reason":
            (
                None
                if self.performance_counters[
                    "dependency_chain_generation_successful"
                ] > 0
                else "no_dependency_concepts_available"
            ),
            "process_dependency_links_used":
            self.performance_counters["process_dependency_links_used"],
            "process_dependency_links_skipped":
            self.performance_counters["process_dependency_links_skipped"],
            "dependency_usage_rate":
            runtime_context["DEPENDENCY_ACTIVATION_TRACE"].get(
                "dependency_usage_rate",
            ),
            "dependency_activation_state":
            dependency_lifecycle_state,
            "dependency_time":
            dependency_time,
            "DEPENDENCY_ACTIVATION_TRACE_REPORT":
            runtime_context["DEPENDENCY_ACTIVATION_TRACE_REPORT"],
            "DEPENDENCY_SKIP_REPORT":
            runtime_context.get("DEPENDENCY_SKIP_REPORT"),
            "DEPENDENCY_ACTIVATION_MISSING":
            runtime_context.get("DEPENDENCY_ACTIVATION_MISSING"),
        }

        self.runtime.bulk_update_context(
            runtime_context
        )
        self._record_module_timing(
            "dependency_reasoning",
            module_start,
        )

    # ========================================
    # PROCESS SEMANTICS
    # ========================================

    def run_process_semantic_cycle(self):

        module_start = time.perf_counter()
        runtime_context = (
            self.runtime.get_context()
        )

        if not self._layer_allowed(
            "process_semantic_synthesis",
            runtime_context,
        ):

            skipped = self._router_skipped_report(
                "process_semantic_synthesis",
                runtime_context,
            )
            runtime_context[
                "process_semantic_report"
            ] = {
                **skipped,
                "reasoning_invoked": False,
                "context_discovery_invoked": False,
            }
            runtime_context[
                "process_semantic_models"
            ] = {}
            runtime_context[
                "dependency_completeness_audit"
            ] = {}
            self.runtime.bulk_update_context(runtime_context)
            self._record_module_timing(
                "process_semantic_synthesis",
                module_start,
            )
            return

        if not self.meta_supervisor.is_action_allowed("context_discovery"):
            runtime_context[
                "process_semantic_report"
            ] = {
                "system": "process_semantic_engine",
                "status": "blocked_by_meta_supervisor",
                "reasoning_invoked": False,
                "context_discovery_invoked": False,
            }
            runtime_context[
                "process_semantic_models"
            ] = {}
            runtime_context[
                "dependency_completeness_audit"
            ] = {}
            self.runtime.bulk_update_context(runtime_context)
            self._record_module_timing(
                "process_semantic_synthesis",
                module_start,
            )
            return

        if not self.runtime.is_tool_enabled(
            "process_semantics"
        ):

            runtime_context[
                "process_semantic_report"
            ] = {
                "system": "process_semantic_engine",
                "report_state": "skipped",
                "skipped": True,
                "reasoning_invoked": False,
                "bypass_reason": "disabled_by_tool_selection",
                "report_level": self.reasoning_budget["report_level"],
            }

            runtime_context[
                "process_semantic_models"
            ] = {}

            runtime_context[
                "dependency_completeness_audit"
            ] = {}

            self.runtime.bulk_update_context(
                runtime_context
            )
            self._record_module_timing(
                "process_semantic_synthesis",
                module_start,
            )
            return

        dependency_contexts = runtime_context.get(
            "process_dependency_chains",
            {},
        )

        cache_key = self._stable_hash({
            "dependency_contexts": dependency_contexts,
            "task_batch_signature": self._runtime_signature(
                runtime_context,
            ),
            "report_level": self.reasoning_budget["report_level"],
        })
        cache_hit = (
            self.reasoning_budget.get("cache_dependencies", False)
            and cache_key in self.process_semantic_cache
        )
        if cache_hit:
            report = dict(self.process_semantic_cache[cache_key])
            report["cache_hit"] = True
            self.performance_counters["cache_hits"] += 1
        else:
            metadata = self._cache_metadata(runtime_context)
            adaptive_context_key = self.adaptive_cache_manager.key(
                "context",
                concept="process_semantics",
                context_signature=cache_key,
                dependency_signature=metadata["dependency_hash"],
            )
            adaptive_context = self.adaptive_cache_manager.get(
                "context",
                key=adaptive_context_key,
                context=runtime_context,
            )
            if isinstance(adaptive_context, dict):
                report = dict(adaptive_context)
                report["cache_hit"] = True
                report["adaptive_context_reused"] = True
                self.runtime.record_cache_hit("process_semantics")
                self.performance_counters["cache_hits"] += 1
                self.performance_counters["context_hits"] += 1
                if self.reasoning_budget.get("cache_dependencies", False):
                    self.process_semantic_cache[cache_key] = dict(report)
            else:
                self.performance_counters["context_misses"] += 1
                report = None
            if report is not None:
                runtime_context["process_semantic_report"] = report
                runtime_context["process_semantic_models"] = report.get(
                    "process_semantic_models",
                    {},
                )
                runtime_context["process_context_registry_report"] = (
                    self._register_process_semantic_contexts(
                        runtime_context["process_semantic_models"],
                    )
                )
                self.runtime.bulk_update_context(runtime_context)
                return
            process_concept_key = (
                self.cognitive_cache_manager
                .concept_key(
                    concept_name="process_semantics",
                    evidence_hash=metadata["evidence_hash"],
                    dependency_hash=metadata["dependency_hash"],
                    context_hash=metadata["context_hash"],
                    runtime_version=metadata["runtime_version"],
                )
            )
            process_entry = (
                self.cognitive_cache_manager
                .lookup_concept(process_concept_key)
            )
            if (
                process_entry is not None
                and process_entry.process_semantic_model is not None
            ):
                report = dict(process_entry.process_semantic_model)
                report["cache_hit"] = True
                self.runtime.record_cache_hit("process_semantics")
                self.performance_counters["cache_hits"] += 1
                if self.reasoning_budget.get("cache_dependencies", False):
                    self.process_semantic_cache[cache_key] = dict(report)
            else:
                self.runtime.record_cache_miss("process_semantics")
                artifact_key = self._artifact_cache_key(
                    runtime_context,
                    artifact_type="process_semantic_models",
                )

                def compute_process_semantics():

                    return (
                        self.process_semantic_engine
                        .synthesize_all(dependency_contexts)
                    )

                report, optimization_report = (
                    self.performance_optimizer
                    .lookup_or_compute(
                        self.cognitive_cache_manager,
                        artifact_key,
                        compute_process_semantics,
                        metadata=metadata,
                    )
                )
                report["cache_hit"] = (
                    optimization_report.get("cache_state") == "hit"
                )
                if report["cache_hit"]:
                    self.performance_counters["cache_hits"] += 1
                else:
                    self.performance_counters["cache_misses"] += 1
                self.cognitive_cache_manager.store_concept(
                    process_concept_key,
                    validated_contexts=[
                        "process_dependency_chains"
                    ],
                    process_semantic_model=report,
                )
                self.adaptive_cache_manager.put(
                    "context",
                    key=adaptive_context_key,
                    value=report,
                    metadata={
                        "concept": "process_semantics",
                        "identity_runtime_state":
                        runtime_context.get("identity_runtime_state"),
                        "identity_runtime_ready":
                        runtime_context.get("identity_runtime_ready"),
                        "context_compatibility":
                        runtime_context.get("context_compatibility", 1.0),
                    },
                )
                if self.reasoning_budget.get("cache_dependencies", False):
                    self.process_semantic_cache[cache_key] = dict(report)

        runtime_context[
            "process_semantic_report"
        ] = report

        runtime_context[
            "process_semantic_models"
        ] = report.get(
            "process_semantic_models",
            {},
        )

        process_registry_report = self._register_process_semantic_contexts(
            runtime_context["process_semantic_models"],
        )
        runtime_context[
            "process_context_registry_report"
        ] = process_registry_report

        runtime_context[
            "dependency_completeness_audit"
        ] = (
            self.process_semantic_engine
            .dependency_completeness_audit()
        )

        self.runtime.bulk_update_context(
            runtime_context
        )
        self._record_module_timing(
            "process_semantic_synthesis",
            module_start,
        )

    def _register_process_semantic_contexts(
        self,
        process_models,
    ):

        process_models = (
            process_models
            if isinstance(process_models, dict)
            else {}
        )
        process_contexts = []
        for concept, model in process_models.items():
            if not isinstance(model, dict):
                continue
            if not (
                model.get("process_semantic_model_generated")
                or model.get("process_context_generated")
            ):
                continue
            process_contexts.append({
                **model,
                "context_id": (
                    model.get("context_id")
                    or model.get("context_name")
                    or f"process_context:{concept}"
                ),
                "context_type": "PROCESS_CONTEXT",
                "concept": model.get("concept", concept),
                "confidence": model.get(
                    "confidence",
                    model.get("process_context_strength", 0.86),
                ),
                "source": "process_semantic_synthesis",
                "dependency_source": "process_dependency_chains",
            })

        registration_report = self.context_registry.register_batch(
            process_contexts,
            source="process_semantic_synthesis",
        )
        registered = registration_report.get("registered_contexts", [])
        self.performance_counters["process_context_count"] = len([
            context
            for context in self.context_registry.all_contexts()
            if context.get("context_type") == "PROCESS_CONTEXT"
        ])
        return {
            **registration_report,
            "system": "process_context_registry",
            "process_context_count": len(registered),
            "process_contexts": registered,
        }

    def _derive_nonsemantic_contexts(
        self,
        semantic_contexts,
        runtime_context,
    ):

        derived_contexts = []
        process_registry = runtime_context.get(
            "process_context_registry_report",
            {},
        )
        registered_process_contexts = (
            process_registry.get("process_contexts", [])
            if isinstance(process_registry, dict)
            else []
        )
        process_by_concept = {
            str(context.get("concept")): context
            for context in registered_process_contexts
            if isinstance(context, dict) and context.get("concept")
        }
        for context in semantic_contexts:
            if not isinstance(context, dict):
                continue

            concept = context.get("concept", "runtime_context")
            process_context = context.get("process_context", {})
            dependency_chain = context.get("dependency_chain", [])
            dependency_report = self._dependency_report_for_context(
                concept,
                dependency_chain,
                runtime_context,
            )
            if not process_context:
                process_context = process_by_concept.get(str(concept), {})
            if not process_context:
                process_context = self._process_context_from_dependency(
                    concept,
                    dependency_report,
                    context,
                )
            if isinstance(process_context, dict) and process_context:
                derived_contexts.append({
                    **process_context,
                    "context_id": (
                        process_context.get("context_id")
                        or process_context.get("context_name")
                        or f"process_context:{concept}"
                    ),
                    "context_type": "PROCESS_CONTEXT",
                    "concept": process_context.get("concept", concept),
                    "confidence": process_context.get(
                        "confidence",
                        process_context.get(
                            "process_context_strength",
                            context.get("confidence", 0.0),
                        ),
                    ),
                    "source": "semantic_context_builder.process_context",
                    "source_semantic_context": context.get("context_id"),
                    "dependency_chain": dependency_chain,
                    "dependency_context_bridge": True,
                })

            causal_score = context.get("causal_score")
            try:
                causal_confidence = float(causal_score)
            except (TypeError, ValueError):
                causal_confidence = 0.0
            if causal_confidence <= 0.0:
                causal_confidence = self._causal_confidence_from_dependency(
                    dependency_report,
                    process_context,
                )
            if causal_confidence > 0.0:
                derived_contexts.append({
                    "context_id": f"causal_context:{concept}",
                    "context_type": "CAUSAL_CONTEXT",
                    "concept": concept,
                    "confidence": round(causal_confidence, 4),
                    "causal_score": round(causal_confidence, 4),
                    "dependency_chain": dependency_chain,
                    "process_context": process_context,
                    "source": "dependency_process_context_bridge.causal",
                    "source_semantic_context": context.get("context_id"),
                    "dependency_context_bridge": True,
                })

            world_context = context.get("world_context", {})
            if not world_context:
                world_context = runtime_context.get("world_model_report", {})
            if not world_context:
                world_context = self._world_context_from_dependency(
                    concept,
                    dependency_report,
                    runtime_context,
                )
            if isinstance(world_context, dict) and world_context:
                world_confidence = (
                    world_context.get("confidence")
                    or world_context.get("world_confidence")
                    or world_context.get("stability_score")
                    or context.get("stability_score")
                    or context.get("confidence")
                    or 0.0
                )
                derived_contexts.append({
                    **world_context,
                    "context_id": (
                        world_context.get("context_id")
                        or world_context.get("context_name")
                        or f"world_context:{concept}"
                    ),
                    "context_type": "WORLD_CONTEXT",
                    "concept": world_context.get("concept", concept),
                    "confidence": world_confidence,
                    "source": "dependency_process_context_bridge.world",
                    "source_semantic_context": context.get("context_id"),
                    "dependency_chain": dependency_chain,
                    "dependency_context_bridge": True,
                })

        return derived_contexts

    def _dependency_report_for_context(
        self,
        concept,
        dependency_chain,
        runtime_context,
    ):

        dependency_chains = runtime_context.get("process_dependency_chains", {})
        if isinstance(dependency_chains, dict):
            report = dependency_chains.get(str(concept))
            if isinstance(report, dict):
                return report
        if isinstance(dependency_chain, dict):
            return dependency_chain
        return {
            "concept": concept,
            "resolved_dependency_chain": list(dependency_chain or []),
            "dependency_chain_depth": len(list(dependency_chain or [])),
            "dependency_chain_coverage": (
                1.0 if dependency_chain else 0.0
            ),
        }

    def _process_context_from_dependency(
        self,
        concept,
        dependency_report,
        semantic_context,
    ):

        if not isinstance(dependency_report, dict):
            return {}
        chain = (
            dependency_report.get("resolved_dependency_chain")
            or dependency_report.get("chain")
            or semantic_context.get("dependency_chain", [])
            or []
        )
        depth = int(dependency_report.get("dependency_chain_depth", 0) or 0)
        coverage = float(
            dependency_report.get("dependency_chain_coverage", 0.0) or 0.0
        )
        if not chain and depth <= 0 and coverage <= 0.0:
            return {}
        confidence = max(
            float(semantic_context.get("confidence", 0.0) or 0.0),
            float(dependency_report.get("dependency_coherence", 0.0) or 0.0),
            float(
                dependency_report.get(
                    "dependency_coherence_average",
                    0.0,
                )
                or 0.0
            ),
            coverage,
            min(1.0, depth / 4.0) if depth else 0.0,
        )
        return {
            "context_id": f"process_context:{concept}",
            "context_name": f"{concept}_process_context",
            "context_type": "PROCESS_CONTEXT",
            "concept": concept,
            "confidence": round(min(1.0, confidence), 4),
            "process_context_strength": round(min(1.0, confidence), 4),
            "dependency_chain": list(chain),
            "dependency_chain_depth": depth or len(chain),
            "dependency_chain_coverage": coverage,
            "preconditions": [
                {"state": "dependency_chain_available", "satisfied": True},
            ],
            "transitions": [
                {
                    "from": chain[index],
                    "to": chain[index + 1],
                    "transition": "depends_on",
                    "confidence": round(min(1.0, confidence), 4),
                }
                for index in range(max(len(chain) - 1, 0))
            ],
            "expected_outcomes": [
                {"state": "semantic_context_grounded_by_process"},
            ],
            "process_context_generated": True,
            "process_context_ready": True,
            "source": "dependency_process_context_bridge",
        }

    def _causal_confidence_from_dependency(
        self,
        dependency_report,
        process_context,
    ):

        if not isinstance(dependency_report, dict):
            return 0.0
        depth = int(dependency_report.get("dependency_chain_depth", 0) or 0)
        coverage = float(
            dependency_report.get("dependency_chain_coverage", 0.0) or 0.0
        )
        coherence = max(
            float(dependency_report.get("dependency_coherence", 0.0) or 0.0),
            float(
                dependency_report.get(
                    "dependency_coherence_average",
                    0.0,
                )
                or 0.0
            ),
        )
        if depth <= 0 and coverage <= 0.0 and coherence <= 0.0:
            return 0.0
        process_bonus = 0.08 if process_context else 0.0
        return round(
            min(
                1.0,
                max(coverage, coherence, min(1.0, depth / 4.0))
                + process_bonus,
            ),
            4,
        )

    def _world_context_from_dependency(
        self,
        concept,
        dependency_report,
        runtime_context,
    ):

        if not isinstance(dependency_report, dict):
            return {}
        depth = int(dependency_report.get("dependency_chain_depth", 0) or 0)
        coverage = float(
            dependency_report.get("dependency_chain_coverage", 0.0) or 0.0
        )
        task_id = str(runtime_context.get("task_id", "") or "").lower()
        structural_world_signal = any(
            signal in f"{task_id} {concept} {dependency_report}".lower()
            for signal in (
                "gravity",
                "falling",
                "support",
                "physics",
                "collision",
                "world",
                "state_transition",
                "motion",
                "position",
            )
        )
        if not structural_world_signal and depth <= 0 and coverage <= 0.0:
            return {}
        confidence = max(coverage, min(1.0, depth / 4.0), 0.72)
        return {
            "context_id": f"world_context:{concept}",
            "context_type": "WORLD_CONTEXT",
            "concept": concept,
            "world_state": "dependency_grounded_process_world",
            "world_confidence": round(confidence, 4),
            "confidence": round(confidence, 4),
            "dependency_chain_depth": depth,
            "dependency_chain_coverage": coverage,
            "source": "dependency_process_context_bridge",
        }

    def _context_type_counts(self, contexts):

        counts = {
            "SEMANTIC_CONTEXT": 0,
            "PROCESS_CONTEXT": 0,
            "CAUSAL_CONTEXT": 0,
            "WORLD_CONTEXT": 0,
        }
        for context in contexts:
            if not isinstance(context, dict):
                continue
            context_type = str(
                context.get("context_type")
                or "SEMANTIC_CONTEXT"
            )
            if context_type in counts:
                counts[context_type] += 1
        return counts

    # ========================================
    # CONTEXT -> PROMOTION -> TRUTH
    # ========================================

    def run_context_truth_advancement_cycle(self):

        module_start = time.perf_counter()
        runtime_context = self.runtime.get_context()

        if not (
            self.meta_supervisor.is_action_allowed("context_discovery")
            and self._layer_allowed("context_discovery", runtime_context)
        ):
            skipped = self._router_skipped_report(
                "context_discovery",
                runtime_context,
            )
            for key, system in (
                ("context_discovery_report", "context_discovery"),
                ("semantic_context_report", "semantic_context_builder"),
                ("context_hierarchy_report", "context_hierarchy_engine"),
                ("contextual_truth_report", "contextual_truth_engine"),
                ("truth_candidate_report", "truth_candidate_engine"),
                ("truth_commit_report", "truth_commit_engine"),
            ):
                runtime_context[key] = {
                    **skipped,
                    "system": system,
                }
            self.performance_counters["promotion_skipped"] += 1
            self.runtime.bulk_update_context(runtime_context)
            self._record_module_timing(
                "context_truth_advancement",
                module_start,
            )
            return

        dependency_chains = runtime_context.get("process_dependency_chains", {})
        if not isinstance(dependency_chains, dict) or not dependency_chains:
            empty_reason = "no_dependency_chains_available"
            runtime_context["context_discovery_report"] = {
                "system": "context_discovery",
                "report_state": "final",
                "contexts_discovered": 0,
                "contexts_registered": 0,
                "contexts_rejected": 0,
                "rejection_reasons": [],
                "result_count": 0,
                "reason": empty_reason,
            }
            runtime_context["semantic_context_report"] = {
                "system": "semantic_context_builder",
                "report_state": "final",
                "result_count": 0,
                "semantic_contexts": [],
                "reason": empty_reason,
            }
            runtime_context["context_hierarchy_report"] = (
                self.context_hierarchy_engine.build([])
            )
            runtime_context["contextual_truth_report"] = {
                "system": "contextual_truth_engine",
                "report_state": "final",
                "result_count": 0,
                "contextual_truth_reports": [],
                "reason": empty_reason,
            }
            runtime_context["truth_candidate_report"] = {
                "system": "truth_candidate_engine",
                "report_state": "final",
                "result_count": 0,
                "truth_candidates": [],
                "reason": empty_reason,
            }
            runtime_context["truth_commit_report"] = {
                "system": "truth_commit_engine",
                "report_state": "final",
                "result_count": 0,
                "committed_truths": [],
                "probationary_truths": [],
                "rejected_truths": [],
                "reason": empty_reason,
            }
            self.performance_counters["promotion_skipped"] += 1
            self.runtime.bulk_update_context(runtime_context)
            self._record_module_timing(
                "context_truth_advancement",
                module_start,
            )
            return

        max_context_search_results = int(
            self.reasoning_budget.get("MAX_CONTEXT_SEARCH_RESULTS", 8) or 8
        )
        max_reuse_attempts = int(
            self.reasoning_budget.get("MAX_REUSE_ATTEMPTS", 3) or 3
        )
        runtime_context["MAX_TRUTH_VALIDATIONS"] = self.reasoning_budget.get(
            "MAX_TRUTH_VALIDATIONS",
            24,
        )
        runtime_context["MAX_CONTEXT_EXPANSION_DEPTH"] = (
            self.reasoning_budget.get("MAX_CONTEXT_EXPANSION_DEPTH", 2)
        )
        self.context_reuse_engine.max_results = max(1, max_context_search_results)
        self.context_reuse_engine.max_attempts = max(1, max_reuse_attempts)
        reused_contexts = []
        missing_dependency_chains = {}
        context_reuse_reports = []
        for concept, dependency_report in dependency_chains.items():
            self.performance_counters["context_reuse_attempts"] += 1
            reuse_report = self.context_reuse_engine.reuse_context(
                {
                    "concept": concept,
                    "context_type": "SEMANTIC_CONTEXT",
                    "dependency_report": dependency_report,
                },
                registry=self.context_registry,
                cache_manager=self.adaptive_cache_manager,
            )
            context_reuse_reports.append(reuse_report)
            reused = reuse_report.get("reused_contexts", [])
            if reused:
                reused_contexts.extend(reused)
                self.performance_counters["context_reuse_successes"] += 1
                self.performance_counters["cache_hits"] += 1
                self.performance_counters["context_hits"] += 1
            else:
                missing_dependency_chains[concept] = dependency_report
                self.performance_counters["cache_misses"] += 1
                self.performance_counters["context_misses"] += 1

        if missing_dependency_chains:
            semantic_report = self.semantic_context_builder.build_batch(
                missing_dependency_chains,
                runtime_context=runtime_context,
            )
            created_contexts = self._reuse_or_store_semantic_contexts(
                semantic_report.get("semantic_contexts", []),
                missing_dependency_chains,
                runtime_context,
            )
        else:
            semantic_report = {
                "system": "semantic_context_builder",
                "report_state": "final",
                "result_count": 0,
                "semantic_contexts": [],
                "contexts_discovered": 0,
                "reason": "all_contexts_reused_before_creation",
            }
            created_contexts = []
        semantic_contexts = [*reused_contexts, *created_contexts]
        semantic_report = {
            **semantic_report,
            "semantic_contexts": semantic_contexts,
            "contexts_discovered": len(semantic_contexts),
            "contexts_reused": len(reused_contexts),
            "context_reuse_reports": context_reuse_reports,
            "result_count": len(semantic_contexts),
        }
        registration_report = self.context_registry.register_batch(
            semantic_contexts,
            source="context_truth_advancement",
        )
        registered_semantic_contexts = registration_report.get(
            "registered_contexts",
            [],
        )
        typed_contexts = self._derive_nonsemantic_contexts(
            semantic_contexts,
            runtime_context,
        )
        typed_registration_report = self.context_registry.register_batch(
            typed_contexts,
            source="context_truth_advancement.typed_contexts",
        )
        registered_typed_contexts = typed_registration_report.get(
            "registered_contexts",
            [],
        )
        registered_contexts = self.context_registry.all_contexts()
        hierarchy_report = self.context_hierarchy_engine.build(registered_contexts)
        type_counts = self._context_type_counts(registered_contexts)

        context_discovery_report = {
            "system": "context_discovery",
            "report_state": "final",
            "contexts_discovered": semantic_report.get("contexts_discovered", 0),
            "contexts_registered": registration_report.get(
                "contexts_registered",
                0,
            ),
            "contexts_rejected": (
                semantic_report.get("contexts_rejected", 0)
                + registration_report.get("contexts_rejected", 0)
                + typed_registration_report.get("contexts_rejected", 0)
            ),
            "rejection_reasons": (
                list(semantic_report.get("rejection_reasons", []))
                + list(registration_report.get("rejection_reasons", []))
                + list(typed_registration_report.get("rejection_reasons", []))
            ),
            "registered_contexts": registered_contexts,
            "result_count": len(registered_contexts),
            "reason": (
                None
                if registered_contexts
                else semantic_report.get("reason", "no_eligible_inputs")
            ),
        }
        runtime_context["context_discovery_report"] = context_discovery_report
        runtime_context["context_registry_report"] = self.context_registry.report()
        runtime_context["typed_context_registry_report"] = {
            **typed_registration_report,
            "system": "typed_context_registry",
            "typed_contexts": registered_typed_contexts,
            "process_context_count": type_counts["PROCESS_CONTEXT"],
            "causal_context_count": type_counts["CAUSAL_CONTEXT"],
            "world_context_count": type_counts["WORLD_CONTEXT"],
        }
        runtime_context["context_chain_report"] = {
            "system": "context_chain_report",
            "report_state": "final",
            "chain": [
                "Concept",
                "Dependency",
                "Process Context",
                "Causal Context",
                "World Context",
                "Semantic Context",
            ],
            "dependency_context_count": len(dependency_chains),
            "process_context_count": type_counts["PROCESS_CONTEXT"],
            "causal_context_count": type_counts["CAUSAL_CONTEXT"],
            "world_context_count": type_counts["WORLD_CONTEXT"],
            "semantic_context_count": type_counts["SEMANTIC_CONTEXT"],
            "semantic_contexts_grounded_by_process": (
                type_counts["SEMANTIC_CONTEXT"] > 0
                and type_counts["PROCESS_CONTEXT"] > 0
            ),
            "semantic_bypass_detected": (
                type_counts["SEMANTIC_CONTEXT"] > 0
                and type_counts["PROCESS_CONTEXT"] == 0
            ),
        }
        runtime_context["causal_validation_reports"] = {
            context.get("context_id"): context
            for context in registered_contexts
            if context.get("context_type") == "CAUSAL_CONTEXT"
        }
        runtime_context["world_context_reports"] = {
            context.get("context_id"): context
            for context in registered_contexts
            if context.get("context_type") == "WORLD_CONTEXT"
        }
        runtime_context["semantic_context_report"] = {
            **semantic_report,
            "contexts_registered": len(registered_contexts),
            "semantic_context_count": len(semantic_contexts),
            "reason": (
                None
                if semantic_contexts
                else semantic_report.get("reason", "no_eligible_inputs")
            ),
        }
        runtime_context["context_hierarchy_report"] = hierarchy_report

        self.performance_counters["context_created"] += len(created_contexts)
        self.performance_counters["context_registered"] += len(
            registered_semantic_contexts
        ) + len(registered_typed_contexts)
        self.performance_counters["context_lost"] += max(
            (
                len(semantic_contexts)
                + len(typed_contexts)
                - len(registered_semantic_contexts)
                - len(registered_typed_contexts)
            ),
            0,
        )
        self.performance_counters["context_count"] = len(registered_contexts)
        self.performance_counters["registered_context_count"] = len(
            registered_contexts
        )
        self.performance_counters["semantic_context_count"] = (
            type_counts["SEMANTIC_CONTEXT"]
        )
        self.performance_counters["process_context_count"] = (
            type_counts["PROCESS_CONTEXT"]
        )
        self.performance_counters["causal_context_count"] = (
            type_counts["CAUSAL_CONTEXT"]
        )
        self.performance_counters["world_context_count"] = (
            type_counts["WORLD_CONTEXT"]
        )
        self.performance_counters["context_confidence_total"] += sum(
            float(context.get("confidence", 0.0) or 0.0)
            for context in registered_contexts
        )

        contextual_truth_reports = []
        promotion_reports = []
        eligibility_reports = []
        candidate_reports = []
        truth_candidates = []
        concepts = list(dependency_chains)
        for concept in concepts:
            concept_contexts = [
                context
                for context in registered_contexts
                if context.get("concept") == concept
            ]
            if not concept_contexts:
                self.performance_counters["context_lost"] += 1
            self.performance_counters["context_consumed"] += len(concept_contexts)
            contextual_report = self.contextual_truth_engine.evaluate(
                concept,
                concept_contexts,
                runtime_context=runtime_context,
            )
            contextual_truth_reports.append(contextual_report)
            promotion_context = {
                **runtime_context,
                "contextual_truth_supported":
                contextual_report.get("contextual_truth_supported", False),
                "contextual_truth_confidence":
                contextual_report.get("contextual_truth_confidence", 0.0),
            }
            self.performance_counters["promotion_started"] += 1
            promotion_report = self.promotion_engine.evaluate(
                concept,
                dependency_report=dependency_chains.get(concept, {}),
                contexts=concept_contexts,
                runtime_context=promotion_context,
            )
            promotion_reports.append(promotion_report)
            self.performance_counters["promotion_completed"] += 1
            self.performance_counters["promotion_evaluations"] += 1
            self.performance_counters["promotion_score_total"] += float(
                promotion_report.get("promotion_score", 0.0) or 0.0
            )
            if promotion_report.get("candidate_ready") is True:
                self.performance_counters["promotion_success_count"] += 1
            eligibility_report = self.truth_eligibility_engine.evaluate_eligibility(
                concept,
                promotion_report=promotion_report,
                contexts=concept_contexts,
                runtime_context=promotion_context,
            )
            eligibility_reports.append(eligibility_report)
            candidate_report = self.truth_candidate_engine.generate(
                concept,
                promotion_report=promotion_report,
                eligibility_report=eligibility_report,
                contexts=concept_contexts,
            )
            candidate_reports.append(candidate_report)
            self.performance_counters["candidate_evaluations"] += 1
            if candidate_report.get("candidate_generated"):
                self.performance_counters["candidate_generated"] += 1
            if candidate_report.get("candidate_rejected"):
                self.performance_counters["candidate_rejected"] += 1
            for candidate in candidate_report.get("truth_candidates", []):
                if isinstance(candidate, dict):
                    candidate["supporting_contexts"] = concept_contexts
                    candidate["supporting_dependencies"] = [
                        dependency_chains.get(concept, {})
                    ]
                    candidate["supporting_tasks"] = runtime_context.get(
                        "task_ids",
                        runtime_context.get("selected_task_files", []),
                    )
                    candidate["cross_task_stability"] = max(
                        [
                            float(context.get("stability_score", 0.0) or 0.0)
                            for context in concept_contexts
                        ]
                        or [candidate.get("candidate_confidence", 0.0)]
                    )
                    candidate["context_strength"] = candidate.get(
                        "context_support",
                        0.0,
                    )
                    candidate["dependency_confidence"] = candidate.get(
                        "dependency_support",
                        0.0,
                    )
                    candidate["causal_validation_score"] = candidate.get(
                        "causal_support",
                        0.0,
                    )
                    candidate["contradiction_rate"] = candidate.get(
                        "contradiction_score",
                        0.0,
                    )
                    truth_candidates.append(candidate)

        commit_report = self.truth_commit_engine.commit(
            truth_candidates,
            runtime_context=runtime_context,
        )
        truth_registry_report = self.truth_registry.register_batch(
            commit_report.get("committed_truths", []),
            source="truth_commit_engine",
        )
        for truth in truth_registry_report.get("registered_truths", []):
            truth_key = self.adaptive_cache_manager.key(
                "truth",
                concept=truth.get("concept", truth.get("truth_name", "truth")),
                truth_signature=self._stable_hash(truth),
            )
            stored_truth = self.adaptive_cache_manager.put(
                "truth",
                key=truth_key,
                value=truth,
                metadata={
                    "concept": truth.get("concept"),
                    "truth_id": truth.get("truth_id"),
                    "final_commit_state": "COMMITTED_TRUTH",
                },
            )
            if stored_truth is not None:
                self.performance_counters["truth_hits"] += 1
        self.performance_counters["candidate_count"] += len(truth_candidates)
        self.performance_counters["truth_commit_evaluations"] += 1
        self.performance_counters["truth_commit_count"] += len(
            commit_report.get("committed_truths", [])
        )
        if commit_report.get("truth_committed"):
            self.performance_counters["truth_committed"] += len(
                commit_report.get("committed_truths", [])
            )
        if commit_report.get("truth_rejected"):
            self.performance_counters["truth_rejected"] += len(
                commit_report.get("rejected_truths", [])
            )

        runtime_context["contextual_truth_report"] = {
            "system": "contextual_truth_engine",
            "report_state": "final",
            "result_count": len(contextual_truth_reports),
            "contextual_truth_reports": contextual_truth_reports,
            "contextual_truth_supported": any(
                report.get("contextual_truth_supported")
                for report in contextual_truth_reports
            ),
            "reason": (
                None
                if contextual_truth_reports
                else "no_registered_contexts"
            ),
        }
        runtime_context["promotion_report"] = {
            "system": "promotion_engine",
            "report_state": "final",
            "result_count": len(promotion_reports),
            "promotion_reports": promotion_reports,
            "promotion_score": (
                promotion_reports[0].get("promotion_score")
                if promotion_reports
                else None
            ),
            "candidate_ready": (
                promotion_reports[0].get("candidate_ready")
                if promotion_reports
                else None
            ),
            "reason": None if promotion_reports else "no_eligible_inputs",
        }
        runtime_context["truth_eligibility_report"] = {
            "system": "truth_eligibility_engine",
            "report_state": "final",
            "result_count": len(eligibility_reports),
            "eligibility_reports": eligibility_reports,
            "eligible_for_truth_candidate": (
                eligibility_reports[0].get("eligible_for_truth_candidate")
                if eligibility_reports
                else None
            ),
            "reason": None if eligibility_reports else "no_eligible_inputs",
        }
        truth_activation = evaluate_truth_activation(
            context_count=len(registered_contexts),
            dependency_chain_coverage=max(
                [
                    float(
                        report.get("dependency_chain_coverage", 0.0)
                        or 0.0
                    )
                    for report in dependency_chains.values()
                    if isinstance(report, dict)
                ]
                or [0.0]
            ),
            promotion_score=(
                promotion_reports[0].get("promotion_score")
                if promotion_reports
                else None
            ),
            candidate_valid=bool(truth_candidates),
        )
        runtime_context["truth_candidate_report"] = {
            "system": "truth_candidate_engine",
            "report_state": "final",
            "result_count": len(truth_candidates),
            "truth_candidates": truth_candidates,
            "candidate_reports": candidate_reports,
            "candidate_ready": (
                promotion_reports[0].get("candidate_ready")
                if promotion_reports
                else False
            ),
            "promotion_score": (
                promotion_reports[0].get("promotion_score")
                if promotion_reports
                else 0.0
            ),
            "eligible_for_truth_candidate": (
                eligibility_reports[0].get("eligible_for_truth_candidate")
                if eligibility_reports
                else False
            ),
            "truth_activation_policy": truth_activation,
            "reason": (
                None
                if truth_candidates
                else "no_candidate_met_promotion_and_eligibility_gates"
            ),
        }
        runtime_context["truth_activation_policy"] = truth_activation
        runtime_context["truth_candidate_evaluations"] = candidate_reports
        runtime_context["truth_commit_report"] = commit_report
        runtime_context["TRUTH COMMIT REPORT"] = {
            "truth_candidate": commit_report.get("truth_candidate"),
            "commit_score": commit_report.get("commit_score"),
            "commit_ready": commit_report.get("commit_ready"),
            "commit_reason": commit_report.get("commit_reason"),
            "commit_blockers": commit_report.get("commit_blockers", []),
            "supporting_contexts": [
                context.get("context_id")
                for truth in commit_report.get("committed_truths", [])
                for context in truth.get("supporting_contexts", [])
                if isinstance(context, dict)
            ],
            "supporting_dependencies": [
                dependency
                for truth in commit_report.get("committed_truths", [])
                for dependency in truth.get("supporting_dependencies", [])
            ],
        }
        runtime_context["truth_commit_evaluations"] = commit_report
        runtime_context["truth_registry_report"] = truth_registry_report
        runtime_context["truth_commitments"] = (
            commit_report.get("committed_truths", [])
            + commit_report.get("probationary_truths", [])
        )
        runtime_context["CONTEXT_LINEAGE_GRAPH"] = {
            "system": "context_lineage_graph",
            "report_state": "final",
            "contexts": [
                {
                    "context_id": context.get("context_id"),
                    "concept": context.get("concept"),
                    "origin": context.get(
                        "origin",
                        context.get("source", "semantic_context_builder"),
                    ),
                    "source_concept": context.get("concept"),
                    "source_dependency_chain": (
                        dependency_chains.get(context.get("concept"), {})
                        if isinstance(dependency_chains, dict)
                        else {}
                    ),
                    "source_observation": context.get("source_observation"),
                    "source_process_context": context.get("process_context"),
                    "source_semantic_context": (
                        context
                        if context.get("context_type") == "SEMANTIC_CONTEXT"
                        else None
                    ),
                    "registration_stage": "context_truth_advancement",
                    "consumer_stages": [
                        "contextual_truth_engine",
                        "promotion_engine",
                        "truth_candidate_engine",
                    ],
                }
                for context in registered_contexts
                if isinstance(context, dict)
            ],
            "dependency_backed_context_count": sum(
                1
                for context in registered_contexts
                if isinstance(context, dict)
                and isinstance(dependency_chains, dict)
                and bool(dependency_chains.get(context.get("concept")))
            ),
            "independent_context_count": sum(
                1
                for context in registered_contexts
                if isinstance(context, dict)
                and (
                    not isinstance(dependency_chains, dict)
                    or not dependency_chains.get(context.get("concept"))
                )
            ),
        }
        runtime_context["TRUTH_LINEAGE_GRAPH"] = {
            "system": "truth_lineage_graph",
            "report_state": "final",
            "candidates": [
                {
                    "concept": candidate.get("concept"),
                    "evidence": candidate.get("supporting_tasks", []),
                    "supporting_contexts": [
                        context.get("context_id")
                        for context in candidate.get("supporting_contexts", [])
                        if isinstance(context, dict)
                    ],
                    "supporting_dependency_chains":
                    candidate.get("supporting_dependencies", []),
                    "promotion_engine": "promotion_engine",
                    "candidate_state": candidate.get("candidate_state"),
                }
                for candidate in truth_candidates
                if isinstance(candidate, dict)
            ],
            "committed_truths": [
                {
                    "concept": truth.get("concept"),
                    "truth_state": truth.get("truth_state"),
                    "evidence": truth.get("supporting_tasks", []),
                    "supporting_contexts": [
                        context.get("context_id")
                        for context in truth.get("supporting_contexts", [])
                        if isinstance(context, dict)
                    ],
                    "supporting_dependency_chains":
                    truth.get("supporting_dependencies", []),
                    "promotion_engine": "truth_commit_engine",
                }
                for truth in commit_report.get("committed_truths", [])
                if isinstance(truth, dict)
            ],
        }
        truth_bypasses = []
        for truth in commit_report.get("committed_truths", []):
            if not isinstance(truth, dict):
                continue
            if not truth.get("supporting_dependencies"):
                truth_bypasses.append({
                    "concept": truth.get("concept"),
                    "bypass": "missing_dependency_support",
                })
            if not truth.get("supporting_contexts"):
                truth_bypasses.append({
                    "concept": truth.get("concept"),
                    "bypass": "missing_context_support",
                })
            if float(truth.get("causal_validation_score", 0.0) or 0.0) <= 0.0:
                truth_bypasses.append({
                    "concept": truth.get("concept"),
                    "bypass": "missing_causal_support",
                })
            if not truth.get("commit_ready"):
                truth_bypasses.append({
                    "concept": truth.get("concept"),
                    "bypass": "missing_promotion_evaluation",
                })
        runtime_context["TRUTH_BYPASS_REPORT"] = {
            "system": "truth_bypass_detector",
            "report_state": "final",
            "bypass_detected": bool(truth_bypasses),
            "bypasses": truth_bypasses,
        }
        runtime_context["context_truth_pipeline_telemetry"] = {
            "context_created": self.performance_counters["context_created"],
            "context_lookup_count": self.context_reuse_engine.lookup_count,
            "context_reuse_attempts":
            self.performance_counters["context_reuse_attempts"],
            "context_reuse_successes":
            self.performance_counters["context_reuse_successes"],
            "context_registered": self.performance_counters["context_registered"],
            "context_consumed": self.performance_counters["context_consumed"],
            "context_lost": self.performance_counters["context_lost"],
            "promotion_started": self.performance_counters["promotion_started"],
            "promotion_completed": self.performance_counters["promotion_completed"],
            "promotion_skipped": self.performance_counters["promotion_skipped"],
            "candidate_generated": self.performance_counters["candidate_generated"],
            "candidate_rejected": self.performance_counters["candidate_rejected"],
            "truth_committed": self.performance_counters["truth_committed"],
            "truth_rejected": self.performance_counters["truth_rejected"],
        }
        runtime_context["context_reuse_report"] = self.context_reuse_engine.report()
        runtime_context["CONTEXT REUSE REPORT"] = runtime_context[
            "context_reuse_report"
        ]

        self.runtime.bulk_update_context(runtime_context)
        self._record_module_timing(
            "context_truth_advancement",
            module_start,
        )

    def _dependency_reasoning_concepts(self, runtime_context):

        concepts = []

        def add(value):

            if value is None:
                return

            concept = str(value).strip()
            concept = (
                concept
                .lower()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if concept and concept not in concepts:
                concepts.append(concept)

        def add_from_mapping(item):

            for key in (
                "concept",
                "concept_id",
                "semantic_key",
                "process_family",
                "name",
                "type",
                "label",
                "abstraction_type",
                "invariant",
                "property",
            ):
                add(item.get(key))

            for key in (
                "concepts",
                "semantic_concepts",
                "suspected_concepts",
                "prioritized_concepts",
                "required_capabilities",
                "tags",
            ):
                values = item.get(key)
                if isinstance(values, (list, tuple, set)):
                    for value in values:
                        add(value)

        for item in runtime_context.get(
            "epistemic_hypotheses",
            [],
        ):

            if isinstance(item, dict):
                add_from_mapping(item)

        for item in runtime_context.get(
            "semantic_abstractions",
            [],
        ):

            if isinstance(item, dict):
                add_from_mapping(item)
            else:
                add(item)

        for concept in runtime_context.get(
            "prioritized_concepts",
            [],
        ):

            add(concept)

        for report_key in (
            "semantic_attribution_report",
            "introspection_report",
        ):

            report = runtime_context.get(report_key, {})
            if not isinstance(report, dict):
                continue
            for concept in report.get("attributed_concepts", []) or []:
                add(concept)
            for concept in report.get("concepts", []) or []:
                add(concept)
            evidence = report.get("semantic_attribution_evidence", {})
            if isinstance(evidence, dict):
                for concept in evidence.keys():
                    add(concept)

        memory_report = (
            self.dependency_chain_executor
            .memory
            .report()
        )
        available_processes = sorted(
            memory_report.get("process_families", [])
        )
        available_concepts = set(available_processes)
        for link in self.dependency_chain_executor.memory.all_links():
            available_concepts.add(str(link.source))
            available_concepts.add(str(link.target))

        if not concepts:

            for concept in available_processes:
                add(concept)

        expanded_concepts = []
        for concept in concepts:
            if concept not in expanded_concepts:
                expanded_concepts.append(concept)
            for alias in self._dependency_concept_aliases(
                concept,
                available_concepts,
            ):
                if alias not in expanded_concepts:
                    expanded_concepts.append(alias)

        runnable_concepts = [
            concept
            for concept in expanded_concepts
            if concept in available_concepts
        ]

        if not runnable_concepts:

            runnable_concepts = available_processes

        return self._prioritize_dependency_concepts(
            runnable_concepts,
            runtime_context,
        )

    def _prioritize_dependency_concepts(self, concepts, runtime_context):

        concepts = list(dict.fromkeys(concepts or []))
        if not concepts:
            return concepts

        signal_text = " ".join(
            str(value)
            for value in [
                runtime_context.get("task_id"),
                runtime_context.get("task_path"),
                runtime_context.get("task_file"),
                runtime_context.get("semantic_attribution_report"),
                runtime_context.get("introspection_report"),
            ]
            if value not in (None, "")
        ).lower()
        priority_groups = []
        if "gravity" in signal_text:
            priority_groups.append([
                "gravity",
                "directional_motion",
                "propagation",
            ])
        if "path_finding" in signal_text or "route_completion" in signal_text:
            priority_groups.append([
                "path_finding",
                "route_completion",
                "reachability",
                "path_construction",
            ])
        if (
            "color_mapping" in signal_text
            or "color_elimination" in signal_text
            or "color_introduction" in signal_text
            or "symbolic_remapping" in signal_text
        ):
            priority_groups.append([
                "symbolic_remapping",
                "color_preservation",
            ])

        prioritized = []
        for group in priority_groups:
            for concept in group:
                if concept in concepts and concept not in prioritized:
                    prioritized.append(concept)

        for concept in concepts:
            if concept not in prioritized:
                prioritized.append(concept)

        return prioritized

    def _dependency_concept_aliases(self, concept, available_concepts):

        aliases = []
        concept = str(concept or "").strip().lower()
        if not concept:
            return aliases

        explicit_aliases = {
            "path_finding": (
                "path_finding",
                "reachability",
                "route_completion",
                "path_construction",
            ),
            "route_completion": (
                "route_completion",
                "path_finding",
                "path_construction",
            ),
            "reachability": (
                "reachability",
                "path_finding",
            ),
            "path_construction": (
                "path_construction",
                "path_finding",
                "route_completion",
            ),
            "reachable_nodes": (
                "reachability",
                "path_finding",
            ),
            "best_path": (
                "path_finding",
                "route_completion",
            ),
            "color_mapping": (
                "symbolic_remapping",
                "color_preservation",
            ),
            "color_elimination": (
                "symbolic_remapping",
            ),
            "color_introduction": (
                "symbolic_remapping",
            ),
            "symbolic_remapping": (
                "symbolic_remapping",
            ),
            "mapping_rule": (
                "symbolic_remapping",
            ),
            "palette_mapping": (
                "symbolic_remapping",
            ),
            "bridge_creation": (
                "topological_growth",
                "growth",
                "propagation",
            ),
            "component_connection": (
                "topological_growth",
                "connectivity_preservation",
                "growth",
            ),
            "connectivity_change": (
                "topological_growth",
                "growth",
            ),
            "topology_change": (
                "topological_growth",
                "growth",
                "topology_preservation",
            ),
            "transformation_sequence": (
                "propagation",
                "directional_motion",
            ),
            "gravity": (
                "gravity",
                "directional_motion",
                "propagation",
            ),
            "falling": (
                "gravity",
                "directional_motion",
            ),
            "support": (
                "gravity",
                "topology_preservation",
                "position_preservation",
            ),
            "physics": (
                "gravity",
                "directional_motion",
                "propagation",
            ),
            "collision": (
                "gravity",
                "position_preservation",
                "topology_preservation",
            ),
            "rest_state": (
                "gravity",
            ),
        }

        for alias in explicit_aliases.get(concept, ()):
            if alias in available_concepts:
                aliases.append(alias)

        if concept.endswith("_preservation"):
            base = concept[: -len("_preservation")]
            if base in available_concepts:
                aliases.append(base)

        for available in sorted(available_concepts):
            available = str(available)
            if (
                available
                and available != concept
                and (
                    available in concept
                    or concept in available
                )
            ):
                aliases.append(available)

        return aliases

    def _semantic_context_cache_key(
        self,
        context,
        dependency_chains,
        runtime_context,
    ):

        concept = context.get("concept", "runtime_concept")
        payload = {
            "context": context,
            "dependency_chain": dependency_chains.get(concept, {}),
        }
        return self.adaptive_cache_manager.key(
            "context",
            concept=concept,
            context_signature=hashlib.sha1(
                json.dumps(
                    payload,
                    sort_keys=True,
                    default=str,
                ).encode("utf-8")
            ).hexdigest(),
        )

    def _reuse_or_store_semantic_contexts(
        self,
        semantic_contexts,
        dependency_chains,
        runtime_context,
    ):

        reusable_contexts = []
        for context in semantic_contexts:
            if not isinstance(context, dict):
                continue

            cache_key = self._semantic_context_cache_key(
                context,
                dependency_chains,
                runtime_context,
            )
            cached_context = self.adaptive_cache_manager.get(
                "context",
                key=cache_key,
                context=runtime_context,
            )
            if isinstance(cached_context, dict):
                cached_context = {
                    **cached_context,
                    "cache_hit": True,
                    "context_cache_reused": True,
                }
                self.performance_counters["cache_hits"] += 1
                self.performance_counters["context_hits"] += 1
                reusable_contexts.append(cached_context)
                continue

            self.performance_counters["cache_misses"] += 1
            self.performance_counters["context_misses"] += 1
            self.adaptive_cache_manager.put(
                "context",
                key=cache_key,
                value=context,
                metadata={
                    "concept": context.get("concept"),
                    "context_id": context.get("context_id"),
                    "context_type": context.get("context_type"),
                },
            )
            reusable_contexts.append(context)

        return reusable_contexts

    # ========================================
    # GOVERNANCE
    # ========================================

    def _governance_reuse_concepts(self, runtime_context):

        concepts = []

        def add(concept):
            if concept and concept not in concepts:
                concepts.append(str(concept))

        for concept in self._dependency_reasoning_concepts(
            runtime_context
        ):
            add(concept)

        for truth in runtime_context.get(
            "reusable_truth_commitments",
            [],
        ):
            if isinstance(truth, dict):
                add(truth.get("concept"))

        for truth in runtime_context.get(
            "truth_commitments",
            [],
        ):
            if isinstance(truth, dict):
                add(truth.get("concept"))

        return concepts

    def _governance_cache_key(
        self,
        concept,
        metadata,
    ):

        return self.cognitive_cache_manager.concept_key(
            concept_name=concept,
            evidence_hash=metadata["evidence_hash"],
            dependency_hash=metadata["dependency_hash"],
            context_hash=metadata["context_hash"],
            runtime_version=metadata["runtime_version"],
        )

    def _truth_records_for_governance(self, runtime_context):

        records = []

        def add_many(items):
            for item in items or []:
                if isinstance(item, dict):
                    records.append(item)

        add_many(runtime_context.get("truth_commitments", []))
        add_many(runtime_context.get("reusable_truth_commitments", []))
        truth_registry_report = runtime_context.get(
            "truth_registry_report",
            {},
        )
        if isinstance(truth_registry_report, dict):
            add_many(truth_registry_report.get("active_truth_objects", []))
            add_many(truth_registry_report.get("truth_objects", []))

        by_concept = {}
        for record in records:
            concept = (
                record.get("concept")
                or record.get("concept_name")
                or record.get("truth")
            )
            if concept:
                by_concept[str(concept)] = record

        return list(by_concept.values())

    def _deep_get(self, value, keys, default=None):

        if not isinstance(keys, (list, tuple)):
            keys = [keys]

        def walk(item, key):
            if isinstance(item, dict):
                if key in item:
                    return item[key]
                for nested in item.values():
                    found = walk(nested, key)
                    if found is not None:
                        return found
            if isinstance(item, list):
                for nested in item:
                    found = walk(nested, key)
                    if found is not None:
                        return found
            return None

        for key in keys:
            found = walk(value, key)
            if found is not None:
                return found

        return default

    def _truth_field(
        self,
        record,
        runtime_context,
        keys,
        default=None,
    ):

        value = self._deep_get(record, keys, None)
        if value is not None:
            return value
        return self._deep_get(runtime_context, keys, default)

    def _locked_truth_profile(self, record, runtime_context):

        concept = (
            record.get("concept")
            or record.get("concept_name")
            or record.get("truth")
            or "unknown_concept"
        )
        final_commit_state = self._truth_field(
            record,
            runtime_context,
            "final_commit_state",
        )
        identity_runtime_state = self._truth_field(
            record,
            runtime_context,
            "identity_runtime_state",
        )
        identity_runtime_continuity = float(
            self._truth_field(
                record,
                runtime_context,
                [
                    "identity_runtime_continuity",
                    "identity_continuity",
                ],
                0.0,
            )
            or 0.0
        )
        contextual_truth_supported = (
            self._truth_field(
                record,
                runtime_context,
                "contextual_truth_supported",
                False,
            )
            is True
        )
        recovery_state = self._truth_field(
            record,
            runtime_context,
            "recovery_state",
        )
        contradiction_review_required = (
            self._truth_field(
                record,
                runtime_context,
                "contradiction_review_required",
                False,
            )
            is True
        )
        contradiction_gap = float(
            self._truth_field(
                record,
                runtime_context,
                "contradiction_gap",
                0.0,
            )
            or 0.0
        )
        contextual_truth_score = float(
            self._truth_field(
                record,
                runtime_context,
                [
                    "contextual_truth_score",
                    "context_confidence",
                ],
                0.0,
            )
            or 0.0
        )

        qualifies = (
            final_commit_state == "LOCKED_TRUTH_PRESERVED"
            and identity_runtime_state == "IDENTITY_RUNTIME_STABLE"
            and identity_runtime_continuity >= 0.90
            and contextual_truth_supported is True
            and recovery_state == "STABLE_SEMANTIC_SPINE"
            and contradiction_review_required is False
            and contradiction_gap == 0.0
        )

        return {
            "concept_name": str(concept),
            "record": record,
            "final_commit_state": final_commit_state,
            "identity_runtime_state": identity_runtime_state,
            "identity_runtime_continuity":
            identity_runtime_continuity,
            "contextual_truth_supported":
            contextual_truth_supported,
            "contextual_truth_score": contextual_truth_score,
            "recovery_state": recovery_state,
            "contradiction_review_required":
            contradiction_review_required,
            "contradiction_gap": contradiction_gap,
            "locked_truth": qualifies,
        }

    def _build_locked_truth_report(
        self,
        profile,
        cache_hit,
        cache_reason,
        integrity_verified,
    ):

        validation_skipped = [
            "contradiction_review",
            "context_discovery",
            "context_hierarchy_generation",
            "semantic_context_reconstruction",
            "causal_validation",
            "truth_candidate_evaluation",
            "truth_commit_review",
        ] if cache_hit and integrity_verified else []

        return {
            "concept_name": profile["concept_name"],
            "truth_validation_mode":
            "CACHE_REUSE"
            if cache_hit and integrity_verified
            else "FULL_VALIDATION",
            "cache_hit": bool(cache_hit),
            "cache_reason": cache_reason,
            "integrity_verified": bool(integrity_verified),
            "validation_skipped": validation_skipped,
            "use_cached_truth": bool(cache_hit),
            "integrity_check_only":
            bool(cache_hit and integrity_verified),
        }

    def _apply_learning_saturation(
        self,
        runtime_context,
        concept_name=None,
    ):

        if concept_name is None:
            concepts = self._governance_reuse_concepts(runtime_context)
            concept_name = concepts[0] if concepts else "runtime"

        detector_context = dict(runtime_context)
        detector_context["transfer_reliability"] = (
            detector_context.get("transfer_reliability")
            or self._deep_get(
                runtime_context,
                "transfer_reliability",
                0.0,
            )
        )
        detector_context["recovery_streak"] = (
            detector_context.get("recovery_streak")
            or self._deep_get(
                runtime_context,
                "recovery_streak",
                0,
            )
        )
        detector_context["contradiction_gap"] = (
            detector_context.get("contradiction_gap")
            if detector_context.get("contradiction_gap") is not None
            else self._deep_get(
                runtime_context,
                "contradiction_gap",
                0.0,
            )
        )
        detector_context["contextual_truth_supported"] = (
            detector_context.get("contextual_truth_supported")
            if detector_context.get("contextual_truth_supported")
            is not None
            else self._deep_get(
                runtime_context,
                "contextual_truth_supported",
                False,
            )
        )

        report = self.learning_saturation_detector.evaluate(
            concept_name,
            detector_context,
        )
        saturated_context = learning_saturation_controller.apply(
            detector_context,
            concept_name,
        )
        runtime_context.update(saturated_context)
        runtime_context = truth_lifecycle_synchronizer.synchronize(
            concept_name=concept_name,
            runtime_context=runtime_context,
            learning_report=report,
        )

        return runtime_context

    def _stable_governance_reuse_allowed(
        self,
        runtime_context,
        cached_context,
    ):

        truth_state = (
            cached_context.get("final_commit_state")
            or runtime_context.get("final_commit_state")
            or cached_context.get("finalization_report", {}).get(
                "final_commit_state"
            )
        )
        identity_continuity = float(
            cached_context.get(
                "identity_runtime_continuity",
                runtime_context.get("identity_runtime_continuity", 0.0),
            ) or 0.0
        )
        context_strength = float(
            cached_context.get(
                "context_strength",
                runtime_context.get("context_strength", 0.0),
            ) or 0.0
        )

        return (
            truth_state == "LOCKED_TRUTH_PRESERVED"
            and identity_continuity >= 0.95
            and context_strength >= 0.90
            and runtime_context.get("evidence_saturated") is True
        )

    def _lookup_cached_governance_context(
        self,
        runtime_context,
        metadata,
    ):

        records = self._truth_records_for_governance(runtime_context)
        if not records:
            return None

        locked_reports = []
        reused_concepts = []
        for record in records:
            profile = self._locked_truth_profile(
                record,
                runtime_context,
            )
            if not profile["locked_truth"]:
                locked_reports.append(
                    self._build_locked_truth_report(
                        profile,
                        cache_hit=False,
                        cache_reason="locked_truth_qualification_failed",
                        integrity_verified=False,
                    )
                )
                return None

            snapshot, cache_reason = self.governance_cache.lookup(
                profile["concept_name"],
                runtime_context,
                record,
            )
            cache_hit = snapshot is not None
            if not cache_hit:
                self.runtime.record_cache_miss(profile["concept_name"])
                self.performance_counters["cache_misses"] += 1
                locked_reports.append(
                    self._build_locked_truth_report(
                        profile,
                        cache_hit=False,
                        cache_reason=cache_reason,
                        integrity_verified=False,
                    )
                )
                return None

            reused_concepts.append(profile["concept_name"])
            self.runtime.record_cache_hit(profile["concept_name"])
            self.performance_counters["cache_hits"] += 1
            self.governance_cache.add_time_saved(
                runtime_context.get(
                    "last_governance_cycle_seconds",
                    30.0,
                )
            )
            locked_reports.append(
                self._build_locked_truth_report(
                    profile,
                    cache_hit=True,
                    cache_reason=cache_reason,
                    integrity_verified=True,
                )
            )

        cached_context = dict(runtime_context or {})
        cached_context["truth_validation_mode"] = "CACHE_REUSE"
        cached_context["use_cached_truth"] = True
        cached_context["integrity_check_only"] = True
        cached_context["LOCKED_TRUTH_REPORT"] = locked_reports
        cached_context["locked_truth_report"] = locked_reports
        cached_context["governance_cache_report"] = {
            **self.governance_cache.build_report(),
            "cache_state": "hit",
            "reused_concepts": reused_concepts,
            "skipped_governance": True,
            "reason": "locked_truth_integrity_verified",
            "truth_validation_mode": "CACHE_REUSE",
        }
        cached_context["governance_report"] = {
            "status": "skipped_by_locked_truth_fast_path",
            "truth_validation_mode": "CACHE_REUSE",
            "integrity_verified": True,
            "reused_concepts": reused_concepts,
        }
        cached_context["cognitive_governance_report"] = {
            "status": "integrity_only",
            "truth_validation_mode": "CACHE_REUSE",
            "validation_skipped":
            locked_reports[0].get("validation_skipped", [])
            if locked_reports
            else [],
        }
        cached_context["GOVERNANCE_CACHE_REPORT"] = (
            cached_context["governance_cache_report"]
        )
        cached_context["governance_reuse_skipped"] = True
        cached_context = self._apply_learning_saturation(
            cached_context,
            reused_concepts[0] if reused_concepts else None,
        )
        return self._cleanup_truth_commit_reasons(cached_context)

    def _lookup_locked_truth_fastpath_context(self, runtime_context):

        records = self._truth_records_for_governance(runtime_context)
        if not records:
            return None

        reports = []
        reused_concepts = []
        for record in records:
            concept = (
                record.get("concept")
                or record.get("concept_name")
                or record.get("truth")
                or "unknown_concept"
            )
            fastpath_context = {
                **runtime_context,
                "truth_commit_report": record,
            }
            report = self.locked_truth_fastpath.evaluate(
                str(concept),
                fastpath_context,
            )
            reports.append(report)
            if not report["fastpath_active"]:
                self.performance_counters[
                    "locked_truth_fastpath_misses"
                ] += 1
                return None

            reused_concepts.append(str(concept))

        self.performance_counters["locked_truth_fastpath_hits"] += len(
            reports
        )
        self.performance_counters[
            "governance_revalidations_skipped"
        ] += len(reports)
        self.performance_counters["governance_skips"] += 1

        fastpath_context = dict(runtime_context or {})
        fastpath_context["locked_truth_fastpath_report"] = (
            reports[0] if len(reports) == 1 else reports
        )
        fastpath_context["truth_validation_mode"] = "FASTPATH_REUSE"
        fastpath_context["use_cached_truth"] = True
        fastpath_context["integrity_check_only"] = True
        fastpath_context["governance_reuse_skipped"] = True
        fastpath_context["governance_report"] = {
            "status": "skipped_by_locked_truth_fastpath",
            "truth_validation_mode": "FASTPATH_REUSE",
            "reused_concepts": reused_concepts,
        }
        fastpath_context["cognitive_governance_report"] = {
            "status": "skipped_by_locked_truth_fastpath",
            "truth_validation_mode": "FASTPATH_REUSE",
            "validation_skipped":
            reports[0].get("skipped_modules", []) if reports else [],
        }
        fastpath_context["governance_cache_report"] = {
            **self.governance_cache.build_report(),
            "cache_state": "locked_truth_fastpath",
            "reused_concepts": reused_concepts,
            "skipped_governance": True,
            "reason": "locked_truth_preserved_and_identity_stable",
        }
        return self._cleanup_truth_commit_reasons(fastpath_context)

    def _lookup_local_governance_cache_context(
        self,
        runtime_context,
        metadata,
    ):

        concepts = self._governance_reuse_concepts(runtime_context)
        for concept in concepts:
            cache_key = self._governance_cache_key(concept, metadata)
            entry = self.cognitive_cache_manager.lookup_concept(cache_key)
            if entry is None or not isinstance(
                entry.truth_commit_result,
                dict,
            ):
                continue

            cached_context = dict(entry.truth_commit_result)
            cached_context["truth_validation_mode"] = "CACHE_REUSE"
            cached_context["use_cached_truth"] = True
            cached_context["integrity_check_only"] = True
            cached_context["governance_reuse_skipped"] = True
            cached_context["governance_cache_report"] = {
                **self.governance_cache.build_report(),
                "cache_state": "hit",
                "reused_concepts": [concept],
                "skipped_governance": True,
                "reason": "local_governance_cache_hit",
                "truth_validation_mode": "CACHE_REUSE",
            }
            cached_context["governance_report"] = cached_context.get(
                "governance_report",
                {},
            ) or {
                "status": "skipped_by_local_governance_cache",
                "truth_validation_mode": "CACHE_REUSE",
                "reused_concepts": [concept],
            }
            cached_context["cognitive_governance_report"] = {
                "status": "integrity_only",
                "truth_validation_mode": "CACHE_REUSE",
            }
            cached_context["GOVERNANCE_CACHE_REPORT"] = (
                cached_context["governance_cache_report"]
            )
            self.runtime.record_cache_hit(concept)
            self.performance_counters["cache_hits"] += 1
            self.performance_counters["governance_skips"] += 1
            self.performance_counters[
                "governance_revalidations_skipped"
            ] += 1
            return self._cleanup_truth_commit_reasons(cached_context)

        return None

    def _store_governance_context(
        self,
        runtime_context,
        metadata,
    ):

        records = self._truth_records_for_governance(runtime_context)
        if not records:
            return {
                "cache_state": "skipped",
                "reason": "no_governance_concepts",
                "stored_concepts": [],
            }

        stored = []
        locked_reports = []
        for record in records:
            profile = self._locked_truth_profile(
                record,
                runtime_context,
            )
            if not profile["locked_truth"]:
                locked_reports.append(
                    self._build_locked_truth_report(
                        profile,
                        cache_hit=False,
                        cache_reason="stored_after_full_validation_pending",
                        integrity_verified=False,
                    )
                )
                continue

            concept = profile["concept_name"]
            cache_key = self._governance_cache_key(
                concept,
                metadata,
            )
            self.cognitive_cache_manager.store_concept(
                cache_key,
                truth_commit_result=runtime_context,
            )
            self.governance_cache.store(
                concept,
                runtime_context,
                record,
                profile["final_commit_state"],
                profile["identity_runtime_continuity"],
                profile["contextual_truth_score"],
            )
            stored.append(concept)
            locked_reports.append(
                self._build_locked_truth_report(
                    profile,
                    cache_hit=False,
                    cache_reason="snapshot_stored_after_full_validation",
                    integrity_verified=True,
                )
            )

        report = {
            **self.governance_cache.build_report(),
            "cache_state": "stored",
            "stored_concepts": stored,
            "cache_entry_count": len(stored),
            "truth_validation_mode": "FULL_VALIDATION",
        }
        runtime_context["LOCKED_TRUTH_REPORT"] = locked_reports
        runtime_context["locked_truth_report"] = locked_reports
        runtime_context["GOVERNANCE_CACHE_REPORT"] = report
        runtime_context = self._apply_learning_saturation(
            runtime_context,
            stored[0] if stored else None,
        )
        return report

    def _cleanup_truth_commit_reasons(self, runtime_context):
        concepts = self._governance_reuse_concepts(runtime_context)
        concept_name = concepts[0] if concepts else "runtime"
        return truth_lifecycle_synchronizer.synchronize(
            concept_name=concept_name,
            runtime_context=runtime_context,
            learning_report=runtime_context.get(
                "learning_saturation_report",
                {},
            ),
        )

    def _apply_dynamic_telemetry_reduction(
        self,
        runtime_context,
    ):

        cache_report = self.cognitive_cache_manager.build_report()
        stable_reuse = bool(
            runtime_context.get(
                "governance_cache_report",
                {},
            ).get("reused_concepts")
        )
        if (
            runtime_context.get("evidence_saturated") is True
            and cache_report.get("cache_hit_rate", 0.0) > 0.80
            and stable_reuse
        ):
            self.reasoning_budget["telemetry_enabled"] = False
            self.reasoning_budget["report_level"] = "summary"
            runtime_context["telemetry_enabled"] = False
            runtime_context["dynamic_telemetry_report"] = {
                "telemetry_reduced": True,
                "telemetry_enabled": False,
                "reason": "stable_cached_truth_reuse",
                "cache_hit_rate": cache_report.get(
                    "cache_hit_rate",
                    0.0,
                ),
            }

        return runtime_context

    def run_governance_cycle(self):

        governance_started_at = time.perf_counter()
        runtime_context = (
            self.runtime.get_context()
        )
        governance_budget = self.reasoning_budget.get(
            "governance_budget_seconds"
        )
        if not self._layer_allowed(
            "deep_governance",
            runtime_context,
        ):

            skipped = self._router_skipped_report(
                "deep_governance",
                runtime_context,
            )
            runtime_context[
                "governance_report"
            ] = {
                **skipped,
                "governance_invoked": False,
            }
            runtime_context[
                "cognitive_governance_report"
            ] = {
                **skipped,
                "system": "cognitive_governance",
                "governance_invoked": False,
            }
            runtime_context[
                "governance_cache_report"
            ] = {
                "system": "governance_cache",
                "report_state": "skipped",
                "skipped_governance": True,
                "reason": skipped["skip_reason"],
            }
            runtime_context[
                "governance_reuse_skipped"
            ] = True
            self.performance_counters["governance_skips"] += 1
            self.runtime.bulk_update_context(runtime_context)
            return

        if not self.meta_supervisor.is_action_allowed("governance"):
            runtime_context[
                "governance_report"
            ] = {
                "status": "blocked_by_meta_supervisor",
                "governance_invoked": False,
                "reason": runtime_context.get(
                    "cognitive_directive",
                    {},
                ).get("reason"),
            }
            runtime_context[
                "cognitive_governance_report"
            ] = {
                "status": "blocked_by_meta_supervisor",
                "governance_invoked": False,
            }
            runtime_context[
                "governance_cache_report"
            ] = {
                "cache_state": "meta_supervisor_reuse",
                "skipped_governance": True,
                "reason": runtime_context.get(
                    "cognitive_directive",
                    {},
                ).get("reason"),
            }
            runtime_context[
                "governance_reuse_skipped"
            ] = True
            self.performance_counters["governance_skips"] += 1
            self.runtime.bulk_update_context(runtime_context)
            return

        governance_cache_metadata = self._cache_metadata(
            runtime_context
        )
        fastpath_governance_context = (
            self._lookup_locked_truth_fastpath_context(
                runtime_context,
            )
        )
        if fastpath_governance_context is not None:
            self.runtime.bulk_update_context(
                fastpath_governance_context
            )
            return

        cached_governance_context = (
            self._lookup_cached_governance_context(
                runtime_context,
                governance_cache_metadata,
            )
        )
        if cached_governance_context is None:
            cached_governance_context = (
                self._lookup_local_governance_cache_context(
                    runtime_context,
                    governance_cache_metadata,
                )
            )
        if cached_governance_context is not None:
            cached_governance_context = (
                self._apply_dynamic_telemetry_reduction(
                    cached_governance_context
                )
            )
            if not cached_governance_context.get(
                "governance_reuse_skipped"
            ):
                self.performance_counters["governance_skips"] += 1
            self.performance_counters[
                "locked_truth_fastpath_hits"
            ] += len(
                cached_governance_context.get(
                    "locked_truth_report",
                    [],
                )
            )
            self.performance_counters[
                "governance_revalidations_skipped"
            ] += (
                0
                if cached_governance_context.get(
                    "governance_cache_report",
                    {},
                ).get("reason") == "local_governance_cache_hit"
                else 1
            )
            self.runtime.bulk_update_context(
                cached_governance_context
            )
            return

        self.performance_counters["governance_executions"] += 1
        runtime_context["truth_validation_mode"] = "FULL_VALIDATION"
        runtime_context["use_cached_truth"] = False
        runtime_context["integrity_check_only"] = False

        concept_schema_validation_report = {
            "system": "concept_contract_layer",
            "phase": "7.5",
            "semantic_abstractions":
            concept_schema_validator.normalize_items(
                runtime_context.get("semantic_abstractions", []),
                record_type="semantic_abstraction",
            ),
            "truth_commitments":
            concept_schema_validator.normalize_items(
                runtime_context.get("truth_commitments", []),
                record_type="truth_commitment",
            ),
        }
        runtime_context["semantic_abstractions"] = (
            concept_schema_validation_report[
                "semantic_abstractions"
            ]["normalized_items"]
        )
        runtime_context["truth_commitments"] = (
            concept_schema_validation_report[
                "truth_commitments"
            ]["normalized_items"]
        )
        runtime_context[
            "concept_schema_validation_report"
        ] = concept_schema_validation_report

        governance_report = (
            self.runtime_governor
            .govern(runtime_context)
        )

        runtime_context[
            "governance_report"
        ] = governance_report

        cognitive_governance_report = (
            self.cognitive_governance_engine
            .govern(runtime_context)
        )

        runtime_context[
            "cognitive_governance_report"
        ] = cognitive_governance_report

        elapsed = time.perf_counter() - governance_started_at
        if (
            governance_budget is not None
            and (
                elapsed >= governance_budget
                or not self.reasoning_budget.get("full_governance", False)
            )
        ):
            budget_exceeded = elapsed >= governance_budget
            runtime_context["governance_budget_seconds"] = governance_budget
            runtime_context["governance_budget_exceeded"] = budget_exceeded
            runtime_context["governance_deferred"] = True
            runtime_context["recommended_next_step"] = (
                "resume_governance_later"
            )
            runtime_context["governance_report"] = {
                **runtime_context.get("governance_report", {}),
                "governance_budget_seconds": governance_budget,
                "governance_budget_exceeded": budget_exceeded,
                "governance_deferred": True,
                "optional_governance_skipped": True,
                "recommended_next_step": "resume_governance_later",
            }
            runtime_context["governance_cache_report"] = {
                "cache_state": "bounded_governance",
                "skipped_governance": True,
                "reason": "optional_governance_deferred",
                "governance_budget_seconds": governance_budget,
                "governance_budget_exceeded": budget_exceeded,
            }
            self.runtime.bulk_update_context(runtime_context)
            return

        hierarchical_memory_report = (
            self.hierarchical_memory_architecture
            .build_architecture(runtime_context)
        )

        runtime_context[
            "hierarchical_memory_architecture_report"
        ] = hierarchical_memory_report

        rejected_merges = []

        memory_report = runtime_context.get(
            "memory_report",
            {}
        )

        if isinstance(
            memory_report,
            dict
        ):

            rejected_merges = runtime_context.get(
                "rejected_merges",
                []
            )

        safe_concept_folding_report = (
            self.safe_concept_folding_engine
            .analyze_rejected_merges(
                rejected_merges
            )
        )

        runtime_context[
            "safe_concept_folding_report"
        ] = safe_concept_folding_report

        semantic_pointer_report = (
            self.semantic_pointer_system
            .build_pointers(runtime_context)
        )

        runtime_context[
            "semantic_pointer_report"
        ] = semantic_pointer_report

        semantic_activation_report = (
            self.semantic_activation_graph
            .run_cycle(runtime_context)
        )

        runtime_context[
            "semantic_activation_report"
        ] = semantic_activation_report

        cognitive_entropy_report = (
            self.cognitive_entropy_engine
            .run_cycle(runtime_context)
        )

        runtime_context[
            "cognitive_entropy_report"
        ] = cognitive_entropy_report

        cognitive_energy_economy_report = (
            self.cognitive_energy_economy
            .compute_energy_budget(
                runtime_context
            )
        )

        runtime_context[
            "cognitive_energy_economy_report"
        ] = cognitive_energy_economy_report

        memory_compression_runtime_report = (
            self.memory_compression_runtime
            .build_plan(runtime_context)
        )

        runtime_context[
            "memory_compression_runtime_report"
        ] = memory_compression_runtime_report

        attention_kernel_report = (
            self.attention_kernel
            .run_cycle(runtime_context)
        )

        runtime_context[
            "attention_kernel_report"
        ] = attention_kernel_report

        cognitive_attention_router_report = (
            self.cognitive_attention_router
            .route(runtime_context)
        )

        runtime_context[
            "cognitive_attention_router_report"
        ] = cognitive_attention_router_report

        runtime_context = (
            self.adaptive_semantic_control
            .run_semantic_control(runtime_context)
        )

        adaptive_semantic_control_report = (
            runtime_context.get(
                "adaptive_semantic_control_report",
                {}
            )
        )

        cognitive_identity_report = (
            self.cognitive_identity_layer
            .evaluate(runtime_context)
        )

        runtime_context[
            "cognitive_identity_report"
        ] = cognitive_identity_report

        latent_reservoir_report = (
            self.latent_reservoir
            .run_cycle(runtime_context)
        )

        runtime_context[
            "latent_reservoir_report"
        ] = latent_reservoir_report

        cognitive_scheduler_report = (
            self.cognitive_scheduler
            .rebalance_runtime(runtime_context)
        )

        runtime_context[
            "cognitive_scheduler_report"
        ] = cognitive_scheduler_report

        executive_arbitration_report = (
            self.executive_arbitration_runtime
            .arbitrate(runtime_context)
        )

        runtime_context[
            "executive_arbitration_report"
        ] = executive_arbitration_report

        identity_core_report = (
            self.identity_core
            .protect_cognitive_continuity(runtime_context)
        )

        runtime_context[
            "identity_core_report"
        ] = identity_core_report

        identity_stability_report = (
            self.identity_stability_core
            .run_cycle(runtime_context)
        )

        runtime_context[
            "identity_stability_report"
        ] = identity_stability_report

        horizon_memory_report = (
            self.horizon_memory_manager
            .run_cycle(runtime_context)
        )

        runtime_context[
            "horizon_memory_report"
        ] = horizon_memory_report

        adaptive_executive_hierarchy_report = (
            self.adaptive_executive_hierarchy
            .build_hierarchy(runtime_context)
        )

        runtime_context[
            "adaptive_executive_hierarchy_report"
        ] = adaptive_executive_hierarchy_report

        runtime_context = (
            self.cognitive_stability_infrastructure
            .run_cycle(runtime_context)
        )

        runtime_context = (
            self.controlled_safe_novelty
            .run_cycle(runtime_context)
        )

        cognitive_physics_report = (
            self.cognitive_physics_engine
            .run_cycle(runtime_context)
        )

        runtime_context[
            "cognitive_physics_report"
        ] = cognitive_physics_report

        semantic_firewall_report = (
            self.semantic_firewall
            .run_cycle(runtime_context)
        )

        runtime_context[
            "semantic_firewall_report"
        ] = semantic_firewall_report

        causal_rehearsal_report = (
            self.causal_rehearsal
            .run_cycle(runtime_context)
        )

        runtime_context[
            "causal_rehearsal_report"
        ] = causal_rehearsal_report

        constructive_reasoning_report = (
            self.adaptive_discovery
            .run_cycle(runtime_context)
        )

        runtime_context[
            "constructive_reasoning_report"
        ] = constructive_reasoning_report

        evolutionary_memory_report = (
            self.evolutionary_memory
            .run_cycle(runtime_context)
        )

        runtime_context[
            "evolutionary_memory_report"
        ] = evolutionary_memory_report

        cognitive_ecology_report = (
            self.cognitive_ecology
            .run_cycle(runtime_context)
        )

        runtime_context[
            "cognitive_ecology_report"
        ] = cognitive_ecology_report

        cognitive_homeostasis_report = (
            self.cognitive_homeostasis
            .run_cycle(runtime_context)
        )

        runtime_context[
            "cognitive_homeostasis_report"
        ] = cognitive_homeostasis_report

        entropy_regulator_report = (
            self.entropy_regulator
            .run_cycle(runtime_context)
        )

        runtime_context[
            "entropy_regulator_report"
        ] = entropy_regulator_report

        identity_continuity_guardian_report = (
            self.identity_continuity_guardian
            .run_cycle(runtime_context)
        )

        runtime_context[
            "identity_continuity_guardian_report"
        ] = identity_continuity_guardian_report

        semantic_drift_monitor_report = (
            self.semantic_drift_monitor
            .measure(runtime_context)
        )

        runtime_context[
            "semantic_drift_monitor_report"
        ] = semantic_drift_monitor_report

        cognitive_natural_selection_report = (
            self.cognitive_natural_selection
            .run_cycle(runtime_context)
        )

        runtime_context[
            "cognitive_natural_selection_report"
        ] = cognitive_natural_selection_report

        epistemic_cognition_report = (
            self.epistemic_decision_engine
            .run_cycle(runtime_context)
        )

        runtime_context[
            "epistemic_cognition_report"
        ] = epistemic_cognition_report
        dependency_snapshot_report = epistemic_cognition_report.get(
            "dependency_snapshot_cache",
            {},
        )
        if isinstance(dependency_snapshot_report, dict):
            self.performance_counters["dependency_snapshot_hits"] = (
                dependency_snapshot_report.get(
                    "dependency_snapshot_hits",
                    0,
                )
            )
            self.performance_counters["dependency_snapshot_misses"] = (
                dependency_snapshot_report.get(
                    "dependency_snapshot_misses",
                    0,
                )
            )
            self.performance_counters["dependency_reasoning_skipped"] = (
                dependency_snapshot_report.get(
                    "dependency_reasoning_skipped",
                    0,
                )
            )
            self.performance_counters[
                "dependency_snapshot_store_count"
            ] = dependency_snapshot_report.get(
                "dependency_snapshot_store_count",
                0,
            )

        runtime_context[
            "active_beliefs"
        ] = epistemic_cognition_report.get(
            "beliefs",
            [],
        )

        runtime_context[
            "truth_commitments"
        ] = epistemic_cognition_report.get(
            "truth_commitments",
            [],
        )

        runtime_context[
            "truth_commitment_layer_report"
        ] = epistemic_cognition_report.get(
            "truth_commitment_layer",
            {},
        )

        runtime_context[
            "truth_registry_report"
        ] = epistemic_cognition_report.get(
            "truth_registry",
            {},
        )

        runtime_context[
            "provisional_truth_registry_report"
        ] = epistemic_cognition_report.get(
            "provisional_truth_registry",
            {},
        )

        runtime_context[
            "provisional_truth_commit_engine_report"
        ] = epistemic_cognition_report.get(
            "provisional_truth_commit_engine",
            {},
        )

        runtime_context[
            "truth_retrieval_engine_report"
        ] = epistemic_cognition_report.get(
            "truth_retrieval_engine",
            {},
        )

        runtime_context[
            "truth_lineage_graph_report"
        ] = epistemic_cognition_report.get(
            "truth_lineage_graph",
            {},
        )

        runtime_context[
            "truth_reinforcement_engine_report"
        ] = epistemic_cognition_report.get(
            "truth_reinforcement_engine",
            {},
        )

        runtime_context[
            "reusable_truth_commitments"
        ] = epistemic_cognition_report.get(
            "reusable_truth_commitments",
            [],
        )

        runtime_context[
            "epistemic_verdict_report"
        ] = epistemic_cognition_report.get(
            "epistemic_verdict_engine",
            {},
        )

        runtime_context[
            "epistemic_promotion_report"
        ] = epistemic_cognition_report.get(
            "epistemic_promotion_engine",
            {},
        )

        runtime_context[
            "epistemic_trial_report"
        ] = runtime_context[
            "epistemic_promotion_report"
        ].get(
            "epistemic_trial_engine",
            {},
        )

        runtime_context[
            "evidence_accumulator_report"
        ] = runtime_context[
            "epistemic_trial_report"
        ].get(
            "evidence_accumulator",
            {},
        )

        runtime_context[
            "evidence_reinforcement_report"
        ] = runtime_context[
            "evidence_accumulator_report"
        ]

        runtime_context[
            "belief_registry_report"
        ] = epistemic_cognition_report.get(
            "belief_registry",
            {},
        )

        runtime_context[
            "belief_promotion_report"
        ] = epistemic_cognition_report.get(
            "belief_promotion_engine",
            {},
        )

        runtime_context[
            "truth_candidate_report"
        ] = epistemic_cognition_report.get(
            "truth_candidate_engine",
            {},
        )

        runtime_context[
            "identity_safe_truth_integration_report"
        ] = epistemic_cognition_report.get(
            "identity_safe_truth_integration_engine",
            {},
        )

        runtime_context[
            "adaptive_identity_integration_report"
        ] = epistemic_cognition_report.get(
            "adaptive_identity_integration_engine",
            {},
        )

        runtime_context[
            "truth_internalization_report"
        ] = epistemic_cognition_report.get(
            "truth_internalization_engine",
            {},
        )

        runtime_context[
            "identity_repair_report"
        ] = epistemic_cognition_report.get(
            "identity_repair_engine",
            {},
        )

        runtime_context[
            "semantic_spine_recovery_report"
        ] = epistemic_cognition_report.get(
            "semantic_spine_recovery_engine",
            {},
        )

        runtime_context[
            "reversible_rehearsal_executor_report"
        ] = epistemic_cognition_report.get(
            "reversible_rehearsal_executor",
            {},
        )

        runtime_context[
            "semantic_drift_controller_report"
        ] = epistemic_cognition_report.get(
            "semantic_drift_controller",
            {},
        )

        runtime_context[
            "trial_resolution_report"
        ] = epistemic_cognition_report.get(
            "trial_resolution_engine",
            {},
        )

        runtime_context[
            "causal_attestation_report"
        ] = epistemic_cognition_report.get(
            "causal_attestation_engine",
            {},
        )

        runtime_context[
            "causal_evidence_arbitration_report"
        ] = epistemic_cognition_report.get(
            "causal_evidence_arbitration_engine",
            {},
        )

        runtime_context[
            "epistemic_evidence_fusion_report"
        ] = epistemic_cognition_report.get(
            "epistemic_evidence_fusion_engine",
            {},
        )

        runtime_context[
            "contradiction_resolution_report"
        ] = epistemic_cognition_report.get(
            "contradiction_resolution_engine",
            {},
        )

        runtime_context[
            "contradiction_attribution_report"
        ] = epistemic_cognition_report.get(
            "contradiction_attribution_engine",
            {},
        )

        runtime_context[
            "truth_advancement_report"
        ] = epistemic_cognition_report.get(
            "truth_advancement_planner",
            {},
        )

        runtime_context[
            "experiment_hypothesis_report"
        ] = epistemic_cognition_report.get(
            "experiment_hypothesis_generator",
            {},
        )

        runtime_context[
            "active_knowledge_acquisition_report"
        ] = epistemic_cognition_report.get(
            "active_knowledge_acquisition_engine",
            {},
        )

        runtime_context[
            "evidence_gap_analyzer_report"
        ] = epistemic_cognition_report.get(
            "evidence_gap_analyzer",
            {},
        )

        runtime_context[
            "sandbox_experiment_executor_report"
        ] = epistemic_cognition_report.get(
            "sandbox_experiment_executor",
            {},
        )

        runtime_context[
            "sandbox_experiment_runner_report"
        ] = epistemic_cognition_report.get(
            "sandbox_experiment_runner",
            {},
        )

        runtime_context[
            "curriculum_manager_report"
        ] = epistemic_cognition_report.get(
            "curriculum_manager",
            {},
        )

        runtime_context[
            "learning_curriculum_manager_report"
        ] = epistemic_cognition_report.get(
            "learning_curriculum_manager",
            {},
        )

        runtime_context[
            "experience_replay_buffer_report"
        ] = epistemic_cognition_report.get(
            "experience_replay_buffer",
            {},
        )

        runtime_context[
            "experiment_result_evaluator_report"
        ] = epistemic_cognition_report.get(
            "experiment_result_evaluator",
            {},
        )

        runtime_context[
            "evidence_integration_engine_report"
        ] = epistemic_cognition_report.get(
            "evidence_integration_engine",
            {},
        )

        runtime_context[
            "causal_effect_analyzer_report"
        ] = epistemic_cognition_report.get(
            "causal_effect_analyzer",
            {},
        )

        runtime_context[
            "epistemic_weight_recalibration_report"
        ] = epistemic_cognition_report.get(
            "epistemic_weight_recalibration_engine",
            {},
        )

        runtime_context[
            "evidence_replication_report"
        ] = epistemic_cognition_report.get(
            "evidence_replication_engine",
            {},
        )

        runtime_context[
            "knowledge_replication_ledger_report"
        ] = epistemic_cognition_report.get(
            "knowledge_replication_ledger",
            {},
        )

        runtime_context[
            "knowledge_generalization_engine_report"
        ] = epistemic_cognition_report.get(
            "knowledge_generalization_engine",
            {},
        )

        runtime_context[
            "counterexample_engine_report"
        ] = epistemic_cognition_report.get(
            "counterexample_engine",
            {},
        )

        runtime_context[
            "boundary_refinement_engine_report"
        ] = epistemic_cognition_report.get(
            "boundary_refinement_engine",
            {},
        )

        runtime_context[
            "truth_gate_remediation_report"
        ] = epistemic_cognition_report.get(
            "truth_gate_remediation",
            {},
        )

        runtime_context[
            "epistemic_quarantine_report"
        ] = epistemic_cognition_report.get(
            "epistemic_quarantine",
            {},
        )

        runtime_context[
            "ambiguity_resolution_report"
        ] = epistemic_cognition_report.get(
            "ambiguity_resolution_engine",
            {},
        )

        runtime_context[
            "epistemic_promotion_grace_report"
        ] = {
            "system":
            "epistemic_promotion_grace",

            "traits":
            runtime_context[
                "epistemic_promotion_report"
            ].get(
                "promotion_grace_traits",
                [],
            ),

            "policy":
            "delay_extinction_while_epistemic_trial_is_active",
        }

        extinction_engine_report = (
            self.extinction_engine
            .run_cycle(runtime_context)
        )

        runtime_context[
            "extinction_engine_report"
        ] = extinction_engine_report

        runtime_context = (
            self.truth_graveyard_synchronizer
            .synchronize_context_reports(runtime_context)
        )

        extinction_engine_report = runtime_context.get(
            "extinction_engine_report",
            extinction_engine_report,
        )

        trait_recovery_report = (
            self.trait_recovery_engine
            .run_cycle(runtime_context)
        )

        runtime_context[
            "trait_recovery_report"
        ] = trait_recovery_report

        evolution_sandbox_report = (
            self.evolution_sandbox
            .run_cycle(runtime_context)
        )

        runtime_context[
            "evolution_sandbox_report"
        ] = evolution_sandbox_report

        stability_field_report = (
            self.stability_field
            .run_cycle(runtime_context)
        )

        runtime_context[
            "stability_field_report"
        ] = stability_field_report

        semantic_physics_report = (
            self.semantic_physics
            .run_cycle(runtime_context)
        )

        runtime_context[
            "semantic_physics_report"
        ] = semantic_physics_report

        semantic_field_dynamics_report = (
            self.semantic_field_dynamics
            .run_cycle(runtime_context)
        )

        runtime_context[
            "semantic_field_dynamics_report"
        ] = semantic_field_dynamics_report

        semantic_spine_report = (
            self.semantic_spine
            .run_cycle(runtime_context)
        )

        runtime_context[
            "semantic_spine_report"
        ] = semantic_spine_report

        identity_reasoner_report = (
            self.identity_reasoner
            .run_cycle(runtime_context)
        )

        runtime_context[
            "identity_reasoner_report"
        ] = identity_reasoner_report

        cognitive_immune_report = (
            self.cognitive_immune_system
            .run_cycle(runtime_context)
        )

        runtime_context[
            "cognitive_immune_report"
        ] = cognitive_immune_report

        immune_policy = cognitive_immune_report.get(
            "immune_policy",
            {},
        )

        if immune_policy.get(
            "freeze_new_fusions",
            False,
        ):

            runtime_context[
                "freeze_new_fusions"
            ] = True

        if immune_policy.get(
            "aggressive_compression",
            False,
        ):

            runtime_context[
                "emergency_compression_active"
            ] = True

        if immune_policy.get(
            "sandbox_only_mode",
            False,
        ):

            runtime_context[
                "sandbox_only_mode"
            ] = True

        concept_fusion_report = (
            self.concept_fusion_engine
            .run_cycle(runtime_context)
        )

        runtime_context[
            "concept_fusion_report"
        ] = concept_fusion_report

        concept_lineage_report = (
            self.concept_lineage
            .run_cycle(runtime_context)
        )

        runtime_context[
            "concept_lineage_report"
        ] = concept_lineage_report

        total_mutation_events = sum(
            len(
                record.get(
                    "mutations",
                    [],
                )
            )
            for record in concept_lineage_report.get(
                "lineage_records",
                [],
            )
        )

        runtime_context[
            "total_mutation_events"
        ] = total_mutation_events

        if total_mutation_events > 500:

            runtime_context[
                "freeze_new_fusions"
            ] = True

        evolutionary_graveyard_report = (
            self.evolutionary_graveyard
            .run_cycle(runtime_context)
        )

        runtime_context[
            "evolutionary_graveyard_report"
        ] = evolutionary_graveyard_report

        runtime_context = (
            self.truth_graveyard_synchronizer
            .synchronize_context_reports(runtime_context)
        )

        extinction_engine_report = runtime_context.get(
            "extinction_engine_report",
            extinction_engine_report,
        )

        trait_recovery_report = runtime_context.get(
            "trait_recovery_report",
            trait_recovery_report,
        )

        evolutionary_graveyard_report = runtime_context.get(
            "evolutionary_graveyard_report",
            evolutionary_graveyard_report,
        )

        truth_graveyard_consistency_report = runtime_context.get(
            "truth_graveyard_consistency_report",
            {},
        )

        ontological_boundary_report = (
            self.ontological_boundary_system
            .run_cycle(runtime_context)
        )

        runtime_context[
            "ontological_boundary_report"
        ] = ontological_boundary_report

        ontological_policy = (
            ontological_boundary_report.get(
                "ontological_policy",
                {},
            )
        )

        if ontological_policy.get(
            "freeze_new_fusions",
            False,
        ):

            runtime_context[
                "freeze_new_fusions"
            ] = True

        if ontological_policy.get(
            "freeze_high_risk_mutations",
            False,
        ):

            runtime_context[
                "freeze_high_risk_mutations"
            ] = True

        if ontological_policy.get(
            "increase_temporal_validation",
            False,
        ):

            runtime_context[
                "increase_temporal_validation"
            ] = True

        existential_economics_report = (
            self.cognitive_existential_economics
            .run_cycle(runtime_context)
        )

        runtime_context[
            "existential_economics_report"
        ] = existential_economics_report

        economic_policy = (
            existential_economics_report.get(
                "economic_policy",
                {},
            )
        )

        if economic_policy.get(
            "reduce_merge_frequency",
            False,
        ):

            runtime_context[
                "reduce_merge_frequency"
            ] = True

            runtime_context[
                "freeze_new_fusions"
            ] = True

        if economic_policy.get(
            "defer_noncritical_abstractions",
            False,
        ):

            runtime_context[
                "defer_noncritical_abstractions"
            ] = True

        if economic_policy.get(
            "reserve_continuity_budget",
            False,
        ):

            runtime_context[
                "reserve_continuity_budget"
            ] = True

        existential_homeostasis_report = (
            self.existential_homeostasis_system
            .run_cycle(runtime_context)
        )

        runtime_context[
            "existential_homeostasis_report"
        ] = existential_homeostasis_report

        homeostasis_policy = (
            existential_homeostasis_report.get(
                "homeostasis_policy",
                {},
            )
        )

        if homeostasis_policy.get(
            "prioritize_stability_cycles",
            False,
        ):

            runtime_context[
                "prioritize_stability_cycles"
            ] = True

        if homeostasis_policy.get(
            "increase_semantic_gravity",
            False,
        ):

            runtime_context[
                "increase_semantic_gravity"
            ] = True

        if homeostasis_policy.get(
            "run_drift_recovery",
            False,
        ):

            runtime_context[
                "run_drift_recovery"
            ] = True

        if homeostasis_policy.get(
            "pause_expansion_for_recovery",
            False,
        ):

            runtime_context[
                "pause_expansion_for_recovery"
            ] = True

            runtime_context[
                "freeze_new_fusions"
            ] = True

        existential_pressure_report = (
            self.existential_pressure_management
            .run_cycle(runtime_context)
        )

        runtime_context[
            "existential_pressure_report"
        ] = existential_pressure_report

        pressure_policy = (
            existential_pressure_report.get(
                "pressure_policy",
                {},
            )
        )

        if pressure_policy.get(
            "activate_self_damping",
            False,
        ):

            runtime_context[
                "activate_self_damping"
            ] = True

        if pressure_policy.get(
            "release_cognitive_pressure",
            False,
        ):

            runtime_context[
                "release_cognitive_pressure"
            ] = True

        if pressure_policy.get(
            "throttle_identity_sensitive_merges",
            False,
        ):

            runtime_context[
                "throttle_identity_sensitive_merges"
            ] = True

            runtime_context[
                "reduce_merge_frequency"
            ] = True

        if pressure_policy.get(
            "absorb_semantic_drift",
            False,
        ):

            runtime_context[
                "absorb_semantic_drift"
            ] = True

        if pressure_policy.get(
            "stabilize_resonance",
            False,
        ):

            runtime_context[
                "stabilize_resonance"
            ] = True

        if pressure_policy.get(
            "regulate_identity_strain",
            False,
        ):

            runtime_context[
                "regulate_identity_strain"
            ] = True

        adaptive_equilibrium_report = (
            self.adaptive_equilibrium_architecture
            .run_cycle(runtime_context)
        )

        runtime_context[
            "adaptive_equilibrium_report"
        ] = adaptive_equilibrium_report

        equilibrium_policy = (
            adaptive_equilibrium_report.get(
                "adaptive_equilibrium_policy",
                {},
            )
        )

        if equilibrium_policy.get(
            "run_adaptive_stability_cycles",
            False,
        ):

            runtime_context[
                "run_adaptive_stability_cycles"
            ] = True

        if equilibrium_policy.get(
            "assimilate_safe_drift",
            False,
        ):

            runtime_context[
                "assimilate_safe_drift"
            ] = True

        if equilibrium_policy.get(
            "allow_limited_topology_adaptation",
            False,
        ):

            runtime_context[
                "allow_limited_topology_adaptation"
            ] = True

        if equilibrium_policy.get(
            "constrain_abstraction_growth",
            False,
        ):

            runtime_context[
                "constrain_abstraction_growth"
            ] = True

            runtime_context[
                "defer_noncritical_abstractions"
            ] = True

        if equilibrium_policy.get(
            "activate_equilibrium_recovery",
            False,
        ):

            runtime_context[
                "activate_equilibrium_recovery"
            ] = True

        hybrid_governance_report = (
            self.hybrid_governance_architecture
            .run_cycle(runtime_context)
        )

        runtime_context[
            "hybrid_governance_report"
        ] = hybrid_governance_report

        hybrid_policy = (
            hybrid_governance_report.get(
                "hybrid_governance_policy",
                {},
            )
        )

        if hybrid_policy.get(
            "require_cross_paradigm_attestation",
            False,
        ):

            runtime_context[
                "require_cross_paradigm_attestation"
            ] = True

        if hybrid_policy.get(
            "sandbox_hybrid_fusion",
            False,
        ):

            runtime_context[
                "sandbox_hybrid_fusion"
            ] = True

            runtime_context[
                "freeze_new_fusions"
            ] = True

        if hybrid_policy.get(
            "route_multimodal_semantics",
            False,
        ):

            runtime_context[
                "route_multimodal_semantics"
            ] = True

        if hybrid_policy.get(
            "preserve_parallel_paradigms",
            False,
        ):

            runtime_context[
                "preserve_parallel_paradigms"
            ] = True

        if hybrid_policy.get(
            "regulate_structural_translation",
            False,
        ):

            runtime_context[
                "regulate_structural_translation"
            ] = True

        recursive_reflective_report = (
            self.recursive_reflective_governance
            .run_cycle(runtime_context)
        )

        runtime_context[
            "recursive_reflective_report"
        ] = recursive_reflective_report

        reflective_policy = (
            recursive_reflective_report.get(
                "recursive_reflective_policy",
                {},
            )
        )

        if reflective_policy.get(
            "reflect_before_recursion",
            False,
        ):

            runtime_context[
                "reflect_before_recursion"
            ] = True

        if reflective_policy.get(
            "localize_recursive_propagation",
            False,
        ):

            runtime_context[
                "localize_recursive_propagation"
            ] = True

        if reflective_policy.get(
            "cap_recursive_growth",
            False,
        ):

            runtime_context[
                "cap_recursive_growth"
            ] = True

        if reflective_policy.get(
            "control_semantic_pruning",
            False,
        ):

            runtime_context[
                "control_semantic_pruning"
            ] = True

        if reflective_policy.get(
            "enforce_reflective_recursion_limits",
            False,
        ):

            runtime_context[
                "enforce_reflective_recursion_limits"
            ] = True

        if reflective_policy.get(
            "balance_recursive_diffusion",
            False,
        ):

            runtime_context[
                "balance_recursive_diffusion"
            ] = True

        if reflective_policy.get(
            "organize_recursive_runtime",
            False,
        ):

            runtime_context[
                "organize_recursive_runtime"
            ] = True

        existential_governance_report = (
            self.existential_governance_core
            .run_cycle(runtime_context)
        )

        runtime_context[
            "existential_governance_report"
        ] = existential_governance_report

        existential_policy = (
            existential_governance_report.get(
                "existential_governance_policy",
                {},
            )
        )

        for key, enabled in existential_policy.items():

            if enabled:

                runtime_context[
                    key
                ] = True

        judicial_cognition_report = (
            self.judicial_cognitive_runtime
            .run_cycle(runtime_context)
        )

        runtime_context[
            "judicial_cognition_report"
        ] = judicial_cognition_report

        judicial_policy = (
            judicial_cognition_report.get(
                "judicial_policy",
                {},
            )
        )

        for key, enabled in judicial_policy.items():

            if enabled:

                runtime_context[
                    key
                ] = True

        execution_permission = (
            judicial_cognition_report.get(
                "execution_gatekeeper",
                {},
            ).get(
                "execution_permission",
                "granted",
            )
        )

        runtime_context[
            "judicial_execution_permission"
        ] = execution_permission

        if execution_permission in [
            "blocked",
            "sandbox_only",
        ]:

            runtime_context[
                "sandbox_only_mode"
            ] = True

        cognitive_constitution_report = (
            self.cognitive_constitution_layer
            .run_cycle(runtime_context)
        )

        runtime_context[
            "cognitive_constitution_report"
        ] = cognitive_constitution_report

        constitution_policy = (
            cognitive_constitution_report.get(
                "cognitive_constitution_policy",
                {},
            )
        )

        for key, enabled in constitution_policy.items():

            if enabled:

                runtime_context[
                    key
                ] = True

        if constitution_policy.get(
            "block_illegal_merges",
            False,
        ):

            runtime_context[
                "freeze_new_fusions"
            ] = True

        if constitution_policy.get(
            "filter_semantic_admissibility",
            False,
        ):

            runtime_context[
                "sandbox_only_mode"
            ] = True

        recursive_guardian_report = (
            self.recursive_guardian
            .run_cycle(runtime_context)
        )

        runtime_context[
            "recursive_guardian_report"
        ] = recursive_guardian_report

        memory_compression_report = (
            self.memory_compression_layer
            .run_cycle(runtime_context)
        )

        runtime_context[
            "memory_compression_report"
        ] = memory_compression_report

        memory_pressure_score = (
            1.0
            -
            memory_compression_report.get(
                "compression_ratio",
                1.0,
            )
        )

        runtime_context[
            "memory_pressure_score"
        ] = memory_pressure_score

        if memory_pressure_score > 0.95:

            runtime_context[
                "emergency_compression_active"
            ] = True

            runtime_context[
                "freeze_new_fusions"
            ] = True

        cognitive_dna_report = (
            self.cognitive_dna_engine
            .run_cycle(runtime_context)
        )

        runtime_context[
            "cognitive_dna_report"
        ] = cognitive_dna_report

        cognitive_physician_report = (
            self.cognitive_physician_engine
            .run_cycle(runtime_context)
        )

        runtime_context[
            "cognitive_physician_report"
        ] = cognitive_physician_report

        governance_kernel_report = (
            self.governance_kernel
            .run_cycle(runtime_context)
        )

        runtime_context[
            "governance_kernel_report"
        ] = governance_kernel_report

        runtime_context[
            "semantic_compression_report"
        ] = governance_kernel_report.get(
            "semantic_compression",
            {},
        )

        runtime_context[
            "runtime_energy_budget_report"
        ] = governance_kernel_report.get(
            "runtime_energy_budget",
            {},
        )

        runtime_context[
            "identity_core_lock_report"
        ] = governance_kernel_report.get(
            "identity_core_lock",
            {},
        )

        runtime_context[
            "epistemic_constitution_report"
        ] = governance_kernel_report.get(
            "epistemic_constitution",
            {},
        )

        runtime_context[
            "epistemic_cognition_report"
        ] = governance_kernel_report.get(
            "epistemic_cognition_layer",
            {},
        )

        runtime_context[
            "active_beliefs"
        ] = runtime_context[
            "epistemic_cognition_report"
        ].get(
            "beliefs",
            [],
        )

        runtime_context[
            "truth_commitments"
        ] = (
            runtime_context[
                "epistemic_cognition_report"
            ].get(
                "truth_commitments",
                [],
            )
            or runtime_context.get(
                "reusable_truth_commitments",
                [],
            )
        )

        runtime_context[
            "governance_physician_review"
        ] = governance_kernel_report.get(
            "physician_review",
            {},
        )

        cognitive_pharmacy_report = (
            self.cognitive_pharmacy_engine
            .run_cycle(runtime_context)
        )

        runtime_context[
            "cognitive_pharmacy_report"
        ] = cognitive_pharmacy_report

        compatibility_reports = (
            governance_kernel_report.get(
                "compatibility_reports",
                {},
            )
        )

        semantic_legitimacy_report = {
            "status":
            "compressed_into_governance_kernel",

            "module":
            "semantic_legitimacy",
        }

        adaptive_permissioning_report = compatibility_reports.get(
            "adaptive_permissioning_report",
            {},
        )

        constitutional_runtime_report = compatibility_reports.get(
            "constitutional_runtime_report",
            {},
        )

        constitutional_rehearsal_report = {
            "status":
            "compressed_into_governance_kernel",

            "module":
            "constitutional_rehearsal",
        }

        semantic_homeostasis_report = {
            "status":
            "compressed_into_governance_kernel",

            "module":
            "semantic_homeostasis",
        }

        constitutional_memory_report = {
            "status":
            "compressed_into_governance_kernel",

            "module":
            "constitutional_memory",
        }

        semantic_court_report = compatibility_reports.get(
            "semantic_court_report",
            {},
        )

        cognitive_immune_engine_report = compatibility_reports.get(
            "cognitive_immune_engine_report",
            {},
        )

        semantic_citizenship_registry_report = {
            "status":
            "compressed_into_governance_kernel",

            "module":
            "semantic_citizenship_registry",
        }

        meta_constitution_report = compatibility_reports.get(
            "meta_constitution_report",
            {},
        )

        civilizational_policy_report = {
            "status":
            "compressed_into_governance_kernel",

            "module":
            "civilizational_policy",

            "policy_state":
            "governance_kernel_managed",
        }

        runtime_context[
            "semantic_legitimacy_report"
        ] = semantic_legitimacy_report

        runtime_context[
            "adaptive_permissioning_report"
        ] = adaptive_permissioning_report

        runtime_context[
            "constitutional_runtime_report"
        ] = constitutional_runtime_report

        runtime_context[
            "constitutional_rehearsal_report"
        ] = constitutional_rehearsal_report

        runtime_context[
            "semantic_homeostasis_report"
        ] = semantic_homeostasis_report

        runtime_context[
            "constitutional_memory_report"
        ] = constitutional_memory_report

        runtime_context[
            "semantic_court_report"
        ] = semantic_court_report

        runtime_context[
            "cognitive_immune_engine_report"
        ] = cognitive_immune_engine_report

        runtime_context[
            "semantic_citizenship_registry_report"
        ] = semantic_citizenship_registry_report

        runtime_context[
            "meta_constitution_report"
        ] = meta_constitution_report

        runtime_context[
            "civilizational_policy_report"
        ] = civilizational_policy_report

        cognitive_spine_stabilizer_report = (
            self.cognitive_spine_stabilizer
            .run_cycle(runtime_context)
        )

        runtime_context[
            "cognitive_spine_stabilizer_report"
        ] = cognitive_spine_stabilizer_report

        identity_continuity_engine_report = (
            self.identity_continuity_engine
            .run_cycle(runtime_context)
        )

        civilization_report = compatibility_reports.get(
            "civilization_report",
            {},
        )

        civilization_report[
            "cognitive_spine_stabilizer"
        ] = cognitive_spine_stabilizer_report

        civilization_report[
            "identity_continuity_engine"
        ] = identity_continuity_engine_report

        runtime_context[
            "civilization_report"
        ] = civilization_report

        concept_lifecycle_report = (
            self.concept_lifecycle_manager
            .run_cycle(runtime_context)
        )

        runtime_context[
            "concept_lifecycle_report"
        ] = concept_lifecycle_report

        runtime_context[
            "semantic_gc_report"
        ] = concept_lifecycle_report.get(
            "semantic_gc",
            {},
        )

        runtime_context[
            "concept_energy_economics_report"
        ] = concept_lifecycle_report.get(
            "concept_energy_economics",
            {},
        )

        runtime_context[
            "bridge_hallucination_filter_report"
        ] = concept_lifecycle_report.get(
            "bridge_hallucination_filter",
            {},
        )

        runtime_context[
            "concept_admission_pipeline_report"
        ] = concept_lifecycle_report.get(
            "concept_admission_pipeline",
            {},
        )

        runtime_context[
            "concept_reputation_engine_report"
        ] = concept_lifecycle_report.get(
            "concept_reputation_engine",
            {},
        )

        runtime_context[
            "reputation_anchor_report"
        ] = concept_lifecycle_report.get(
            "reputation_anchor",
            {},
        )

        cognitive_stability_report = (
            runtime_context.get(
                "phase_5_cognitive_stability_report",
                {}
            )
        )

        controlled_safe_novelty_report = (
            runtime_context.get(
                "controlled_safe_novelty_report",
                {}
            )
        )

        cognitive_physics_report = (
            runtime_context.get(
                "cognitive_physics_report",
                {}
            )
        )

        runtime_context[
            "governance_reports"
        ] = {

            "runtime_governance":
            governance_report,

            "cognitive_governance":
            cognitive_governance_report,

            "hierarchical_memory":
            hierarchical_memory_report,

            "safe_concept_folding":
            safe_concept_folding_report,

            "semantic_pointer":
            semantic_pointer_report,

            "semantic_activation":
            semantic_activation_report,

            "cognitive_entropy":
            cognitive_entropy_report,

            "cognitive_energy_economy":
            cognitive_energy_economy_report,

            "memory_compression_runtime":
            memory_compression_runtime_report,

            "attention_kernel":
            attention_kernel_report,

            "cognitive_attention_router":
            cognitive_attention_router_report,

            "adaptive_semantic_control":
            adaptive_semantic_control_report,

            "cognitive_identity":
            cognitive_identity_report,

            "latent_reservoir":
            latent_reservoir_report,

            "executive_arbitration":
            executive_arbitration_report,

            "identity_core":
            identity_core_report,

            "identity_stability":
            identity_stability_report,

            "horizon_memory":
            horizon_memory_report,

            "cognitive_scheduler":
            cognitive_scheduler_report,

            "adaptive_executive_hierarchy":
            adaptive_executive_hierarchy_report,

            "cognitive_stability_infrastructure":
            cognitive_stability_report,

            "controlled_safe_novelty":
            controlled_safe_novelty_report,

            "cognitive_physics":
            cognitive_physics_report,

            "semantic_firewall":
            semantic_firewall_report,

            "causal_rehearsal":
            causal_rehearsal_report,

            "constructive_reasoning":
            constructive_reasoning_report,

            "evolutionary_memory":
            evolutionary_memory_report,

            "evolutionary_graveyard":
            evolutionary_graveyard_report,

            "truth_graveyard_consistency":
            truth_graveyard_consistency_report,

            "ontological_boundary":
            ontological_boundary_report,

            "existential_economics":
            existential_economics_report,

            "existential_homeostasis":
            existential_homeostasis_report,

            "existential_pressure":
            existential_pressure_report,

            "adaptive_equilibrium":
            adaptive_equilibrium_report,

            "hybrid_governance":
            hybrid_governance_report,

            "recursive_reflective":
            recursive_reflective_report,

            "existential_governance":
            existential_governance_report,

            "judicial_cognition":
            judicial_cognition_report,

            "cognitive_constitution":
            cognitive_constitution_report,

            "cognitive_ecology":
            cognitive_ecology_report,

            "cognitive_homeostasis":
            cognitive_homeostasis_report,

            "entropy_regulator":
            entropy_regulator_report,

            "cognitive_natural_selection":
            cognitive_natural_selection_report,

            "extinction_engine":
            extinction_engine_report,

            "trait_recovery":
            trait_recovery_report,

            "evolution_sandbox":
            evolution_sandbox_report,

            "stability_field":
            stability_field_report,

            "semantic_physics":
            semantic_physics_report,

            "semantic_field_dynamics":
            semantic_field_dynamics_report,

            "semantic_spine":
            semantic_spine_report,

            "identity_reasoner":
            identity_reasoner_report,

            "cognitive_immune":
            cognitive_immune_report,

            "concept_fusion":
            concept_fusion_report,

            "concept_lineage":
            concept_lineage_report,

            "recursive_guardian":
            recursive_guardian_report,

            "identity_continuity_guardian":
            identity_continuity_guardian_report,

            "semantic_legitimacy":
            semantic_legitimacy_report,

            "adaptive_permissioning":
            adaptive_permissioning_report,

            "constitutional_runtime":
            constitutional_runtime_report,

            "civilization":
            civilization_report,

            "memory_compression":
            memory_compression_report
        }

        compression_result = (
            self.context_compression_engine
            .compress_context(runtime_context)
        )

        compressed_context = (
            compression_result.get(
                "compressed_context",
                runtime_context
            )
        )

        compressed_context[
            "governance_report"
        ] = governance_report

        compressed_context[
            "cognitive_governance_report"
        ] = cognitive_governance_report

        compressed_context[
            "hierarchical_memory_architecture_report"
        ] = hierarchical_memory_report

        compressed_context[
            "safe_concept_folding_report"
        ] = safe_concept_folding_report

        compressed_context[
            "semantic_pointer_report"
        ] = semantic_pointer_report

        compressed_context[
            "semantic_activation_report"
        ] = semantic_activation_report

        compressed_context[
            "cognitive_entropy_report"
        ] = cognitive_entropy_report

        compressed_context[
            "cognitive_energy_economy_report"
        ] = cognitive_energy_economy_report

        compressed_context[
            "memory_compression_runtime_report"
        ] = memory_compression_runtime_report

        compressed_context[
            "attention_kernel_report"
        ] = attention_kernel_report

        compressed_context[
            "cognitive_attention_router_report"
        ] = cognitive_attention_router_report

        compressed_context[
            "adaptive_semantic_control_report"
        ] = adaptive_semantic_control_report

        compressed_context[
            "semantic_distance_fields_report"
        ] = runtime_context.get(
            "semantic_distance_fields_report",
            {}
        )

        compressed_context[
            "adaptive_semantic_compression_report"
        ] = runtime_context.get(
            "adaptive_semantic_compression_report",
            {}
        )

        compressed_context[
            "active_concept_decay_report"
        ] = runtime_context.get(
            "active_concept_decay_report",
            {}
        )

        compressed_context[
            "hierarchical_attention_collapse_report"
        ] = runtime_context.get(
            "hierarchical_attention_collapse_report",
            {}
        )

        compressed_context[
            "cognitive_predictive_routing_report"
        ] = runtime_context.get(
            "cognitive_predictive_routing_report",
            {}
        )

        compressed_context[
            "cognitive_identity_report"
        ] = cognitive_identity_report

        compressed_context[
            "latent_reservoir_report"
        ] = latent_reservoir_report

        compressed_context[
            "executive_arbitration_report"
        ] = executive_arbitration_report

        compressed_context[
            "identity_core_report"
        ] = identity_core_report

        compressed_context[
            "identity_stability_report"
        ] = identity_stability_report

        compressed_context[
            "horizon_memory_report"
        ] = horizon_memory_report

        compressed_context[
            "cognitive_scheduler_report"
        ] = cognitive_scheduler_report

        compressed_context[
            "adaptive_executive_hierarchy_report"
        ] = adaptive_executive_hierarchy_report

        compressed_context[
            "phase_5_cognitive_stability_report"
        ] = cognitive_stability_report

        compressed_context[
            "semantic_virtual_memory_report"
        ] = runtime_context.get(
            "semantic_virtual_memory_report",
            {}
        )

        compressed_context[
            "ontology_defragmenter_report"
        ] = runtime_context.get(
            "ontology_defragmenter_report",
            {}
        )

        compressed_context[
            "identity_anchor_core_report"
        ] = runtime_context.get(
            "identity_anchor_core_report",
            {}
        )

        compressed_context[
            "cognitive_garbage_collector_report"
        ] = runtime_context.get(
            "cognitive_garbage_collector_report",
            {}
        )

        compressed_context[
            "predictive_collapse_report"
        ] = runtime_context.get(
            "predictive_collapse_report",
            {}
        )

        compressed_context[
            "recursive_pressure_governor_report"
        ] = runtime_context.get(
            "recursive_pressure_governor_report",
            {}
        )

        compressed_context[
            "semantic_paging_report"
        ] = runtime_context.get(
            "semantic_paging_report",
            {}
        )

        compressed_context[
            "controlled_safe_novelty_report"
        ] = controlled_safe_novelty_report

        compressed_context[
            "cognitive_physics_report"
        ] = cognitive_physics_report

        compressed_context[
            "semantic_firewall_report"
        ] = semantic_firewall_report

        compressed_context[
            "causal_rehearsal_report"
        ] = causal_rehearsal_report

        compressed_context[
            "constructive_reasoning_report"
        ] = constructive_reasoning_report

        compressed_context[
            "evolutionary_memory_report"
        ] = evolutionary_memory_report

        compressed_context[
            "evolutionary_graveyard_report"
        ] = evolutionary_graveyard_report

        compressed_context[
            "truth_graveyard_consistency_report"
        ] = truth_graveyard_consistency_report

        compressed_context[
            "ontological_boundary_report"
        ] = ontological_boundary_report

        compressed_context[
            "existential_economics_report"
        ] = existential_economics_report

        compressed_context[
            "existential_homeostasis_report"
        ] = existential_homeostasis_report

        compressed_context[
            "existential_pressure_report"
        ] = existential_pressure_report

        compressed_context[
            "adaptive_equilibrium_report"
        ] = adaptive_equilibrium_report

        compressed_context[
            "hybrid_governance_report"
        ] = hybrid_governance_report

        compressed_context[
            "recursive_reflective_report"
        ] = recursive_reflective_report

        compressed_context[
            "existential_governance_report"
        ] = existential_governance_report

        compressed_context[
            "judicial_cognition_report"
        ] = judicial_cognition_report

        compressed_context[
            "cognitive_constitution_report"
        ] = cognitive_constitution_report

        compressed_context[
            "cognitive_ecology_report"
        ] = cognitive_ecology_report

        compressed_context[
            "cognitive_homeostasis_report"
        ] = cognitive_homeostasis_report

        compressed_context[
            "entropy_regulator_report"
        ] = entropy_regulator_report

        compressed_context[
            "cognitive_natural_selection_report"
        ] = cognitive_natural_selection_report

        compressed_context[
            "extinction_engine_report"
        ] = extinction_engine_report

        compressed_context[
            "trait_recovery_report"
        ] = trait_recovery_report

        compressed_context[
            "evolution_sandbox_report"
        ] = evolution_sandbox_report

        compressed_context[
            "stability_field_report"
        ] = stability_field_report

        compressed_context[
            "semantic_physics_report"
        ] = semantic_physics_report

        compressed_context[
            "semantic_field_dynamics_report"
        ] = semantic_field_dynamics_report

        compressed_context[
            "semantic_spine_report"
        ] = semantic_spine_report

        compressed_context[
            "identity_reasoner_report"
        ] = identity_reasoner_report

        compressed_context[
            "cognitive_immune_report"
        ] = cognitive_immune_report

        compressed_context[
            "concept_fusion_report"
        ] = concept_fusion_report

        compressed_context[
            "concept_lineage_report"
        ] = concept_lineage_report

        compressed_context[
            "recursive_guardian_report"
        ] = recursive_guardian_report

        compressed_context[
            "identity_continuity_guardian_report"
        ] = identity_continuity_guardian_report

        compressed_context[
            "semantic_legitimacy_report"
        ] = semantic_legitimacy_report

        compressed_context[
            "adaptive_permissioning_report"
        ] = adaptive_permissioning_report

        compressed_context[
            "constitutional_runtime_report"
        ] = constitutional_runtime_report

        compressed_context[
            "governance_kernel_report"
        ] = governance_kernel_report

        compressed_context[
            "semantic_compression_report"
        ] = runtime_context.get(
            "semantic_compression_report",
            {}
        )

        compressed_context[
            "runtime_energy_budget_report"
        ] = runtime_context.get(
            "runtime_energy_budget_report",
            {}
        )

        compressed_context[
            "identity_core_lock_report"
        ] = runtime_context.get(
            "identity_core_lock_report",
            {}
        )

        compressed_context[
            "epistemic_constitution_report"
        ] = runtime_context.get(
            "epistemic_constitution_report",
            {}
        )

        compressed_context[
            "cognitive_physician_report"
        ] = runtime_context.get(
            "cognitive_physician_report",
            {}
        )

        compressed_context[
            "cognitive_dna_report"
        ] = runtime_context.get(
            "cognitive_dna_report",
            {}
        )

        compressed_context[
            "governance_physician_review"
        ] = runtime_context.get(
            "governance_physician_review",
            {}
        )

        compressed_context[
            "cognitive_pharmacy_report"
        ] = runtime_context.get(
            "cognitive_pharmacy_report",
            {}
        )

        compressed_context[
            "civilization_report"
        ] = civilization_report

        compressed_context[
            "memory_compression_report"
        ] = memory_compression_report

        compressed_context[
            "epistemic_cognition_report"
        ] = runtime_context.get(
            "epistemic_cognition_report",
            {},
        )

        compressed_context[
            "epistemic_promotion_report"
        ] = runtime_context.get(
            "epistemic_promotion_report",
            {},
        )

        compressed_context[
            "epistemic_trial_report"
        ] = runtime_context.get(
            "epistemic_trial_report",
            {},
        )

        compressed_context[
            "evidence_accumulator_report"
        ] = runtime_context.get(
            "evidence_accumulator_report",
            {},
        )

        compressed_context[
            "evidence_reinforcement_report"
        ] = runtime_context.get(
            "evidence_reinforcement_report",
            {},
        )

        compressed_context[
            "belief_registry_report"
        ] = runtime_context.get(
            "belief_registry_report",
            {},
        )

        compressed_context[
            "belief_promotion_report"
        ] = runtime_context.get(
            "belief_promotion_report",
            {},
        )

        compressed_context[
            "truth_commitment_layer_report"
        ] = runtime_context.get(
            "truth_commitment_layer_report",
            {},
        )

        compressed_context[
            "truth_registry_report"
        ] = runtime_context.get(
            "truth_registry_report",
            {},
        )

        compressed_context[
            "provisional_truth_registry_report"
        ] = runtime_context.get(
            "provisional_truth_registry_report",
            {},
        )

        compressed_context[
            "provisional_truth_commit_engine_report"
        ] = runtime_context.get(
            "provisional_truth_commit_engine_report",
            {},
        )

        compressed_context[
            "truth_retrieval_engine_report"
        ] = runtime_context.get(
            "truth_retrieval_engine_report",
            {},
        )

        compressed_context[
            "truth_lineage_graph_report"
        ] = runtime_context.get(
            "truth_lineage_graph_report",
            {},
        )

        compressed_context[
            "truth_reinforcement_engine_report"
        ] = runtime_context.get(
            "truth_reinforcement_engine_report",
            {},
        )

        compressed_context[
            "reusable_truth_commitments"
        ] = runtime_context.get(
            "reusable_truth_commitments",
            [],
        )

        compressed_context[
            "truth_candidate_report"
        ] = runtime_context.get(
            "truth_candidate_report",
            {},
        )

        compressed_context[
            "identity_safe_truth_integration_report"
        ] = runtime_context.get(
            "identity_safe_truth_integration_report",
            {},
        )

        compressed_context[
            "adaptive_identity_integration_report"
        ] = runtime_context.get(
            "adaptive_identity_integration_report",
            {},
        )

        compressed_context[
            "truth_internalization_report"
        ] = runtime_context.get(
            "truth_internalization_report",
            {},
        )

        compressed_context[
            "identity_repair_report"
        ] = runtime_context.get(
            "identity_repair_report",
            {},
        )

        compressed_context[
            "semantic_spine_recovery_report"
        ] = runtime_context.get(
            "semantic_spine_recovery_report",
            {},
        )

        compressed_context[
            "reversible_rehearsal_executor_report"
        ] = runtime_context.get(
            "reversible_rehearsal_executor_report",
            {},
        )

        compressed_context[
            "semantic_drift_controller_report"
        ] = runtime_context.get(
            "semantic_drift_controller_report",
            {},
        )

        compressed_context[
            "trial_resolution_report"
        ] = runtime_context.get(
            "trial_resolution_report",
            {},
        )

        compressed_context[
            "causal_attestation_report"
        ] = runtime_context.get(
            "causal_attestation_report",
            {},
        )

        compressed_context[
            "causal_evidence_arbitration_report"
        ] = runtime_context.get(
            "causal_evidence_arbitration_report",
            {},
        )

        compressed_context[
            "epistemic_evidence_fusion_report"
        ] = runtime_context.get(
            "epistemic_evidence_fusion_report",
            {},
        )

        compressed_context[
            "contradiction_resolution_report"
        ] = runtime_context.get(
            "contradiction_resolution_report",
            {},
        )

        compressed_context[
            "contradiction_attribution_report"
        ] = runtime_context.get(
            "contradiction_attribution_report",
            {},
        )

        compressed_context[
            "truth_advancement_report"
        ] = runtime_context.get(
            "truth_advancement_report",
            {},
        )

        compressed_context[
            "experiment_hypothesis_report"
        ] = runtime_context.get(
            "experiment_hypothesis_report",
            {},
        )

        compressed_context[
            "active_knowledge_acquisition_report"
        ] = runtime_context.get(
            "active_knowledge_acquisition_report",
            {},
        )

        compressed_context[
            "evidence_gap_analyzer_report"
        ] = runtime_context.get(
            "evidence_gap_analyzer_report",
            {},
        )

        compressed_context[
            "sandbox_experiment_executor_report"
        ] = runtime_context.get(
            "sandbox_experiment_executor_report",
            {},
        )

        compressed_context[
            "sandbox_experiment_runner_report"
        ] = runtime_context.get(
            "sandbox_experiment_runner_report",
            {},
        )

        compressed_context[
            "curriculum_manager_report"
        ] = runtime_context.get(
            "curriculum_manager_report",
            {},
        )

        compressed_context[
            "learning_curriculum_manager_report"
        ] = runtime_context.get(
            "learning_curriculum_manager_report",
            {},
        )

        compressed_context[
            "experience_replay_buffer_report"
        ] = runtime_context.get(
            "experience_replay_buffer_report",
            {},
        )

        compressed_context[
            "experiment_result_evaluator_report"
        ] = runtime_context.get(
            "experiment_result_evaluator_report",
            {},
        )

        compressed_context[
            "evidence_integration_engine_report"
        ] = runtime_context.get(
            "evidence_integration_engine_report",
            {},
        )

        compressed_context[
            "causal_effect_analyzer_report"
        ] = runtime_context.get(
            "causal_effect_analyzer_report",
            {},
        )

        compressed_context[
            "epistemic_weight_recalibration_report"
        ] = runtime_context.get(
            "epistemic_weight_recalibration_report",
            {},
        )

        compressed_context[
            "evidence_replication_report"
        ] = runtime_context.get(
            "evidence_replication_report",
            {},
        )

        compressed_context[
            "knowledge_replication_ledger_report"
        ] = runtime_context.get(
            "knowledge_replication_ledger_report",
            {},
        )

        compressed_context[
            "knowledge_generalization_engine_report"
        ] = runtime_context.get(
            "knowledge_generalization_engine_report",
            {},
        )

        compressed_context[
            "counterexample_engine_report"
        ] = runtime_context.get(
            "counterexample_engine_report",
            {},
        )

        compressed_context[
            "boundary_refinement_engine_report"
        ] = runtime_context.get(
            "boundary_refinement_engine_report",
            {},
        )

        compressed_context[
            "cross_task_replication_collector_report"
        ] = runtime_context.get(
            "cross_task_replication_collector_report",
            {},
        )

        compressed_context[
            "truth_gate_remediation_report"
        ] = runtime_context.get(
            "truth_gate_remediation_report",
            {},
        )

        compressed_context[
            "epistemic_quarantine_report"
        ] = runtime_context.get(
            "epistemic_quarantine_report",
            {},
        )

        compressed_context[
            "ambiguity_resolution_report"
        ] = runtime_context.get(
            "ambiguity_resolution_report",
            {},
        )

        compressed_context[
            "memory_pressure_score"
        ] = runtime_context.get(
            "memory_pressure_score",
            0.0,
        )

        compressed_context[
            "total_mutation_events"
        ] = runtime_context.get(
            "total_mutation_events",
            0,
        )

        compressed_context[
            "freeze_new_fusions"
        ] = runtime_context.get(
            "freeze_new_fusions",
            False,
        )

        compressed_context[
            "emergency_compression_active"
        ] = runtime_context.get(
            "emergency_compression_active",
            False,
        )

        compressed_context[
            "concept_lifecycle_report"
        ] = runtime_context.get(
            "concept_lifecycle_report",
            {}
        )

        compressed_context[
            "semantic_gc_report"
        ] = runtime_context.get(
            "semantic_gc_report",
            {}
        )

        compressed_context[
            "concept_energy_economics_report"
        ] = runtime_context.get(
            "concept_energy_economics_report",
            {}
        )

        compressed_context[
            "bridge_hallucination_filter_report"
        ] = runtime_context.get(
            "bridge_hallucination_filter_report",
            {}
        )

        compressed_context[
            "concept_admission_pipeline_report"
        ] = runtime_context.get(
            "concept_admission_pipeline_report",
            {}
        )

        compressed_context[
            "concept_reputation_engine_report"
        ] = runtime_context.get(
            "concept_reputation_engine_report",
            {}
        )

        compressed_context[
            "reputation_anchor_report"
        ] = runtime_context.get(
            "reputation_anchor_report",
            {}
        )

        compressed_context[
            "semantic_immune_confidence_calibration_report"
        ] = runtime_context.get(
            "semantic_immune_confidence_calibration_report",
            {}
        )

        compressed_context[
            "safe_exploratory_sandbox_report"
        ] = runtime_context.get(
            "safe_exploratory_sandbox_report",
            {}
        )

        compressed_context[
            "conceptive_neurogenesis_report"
        ] = runtime_context.get(
            "conceptive_neurogenesis_report",
            {}
        )

        compressed_context[
            "recursive_simulation_worlds_report"
        ] = runtime_context.get(
            "recursive_simulation_worlds_report",
            {}
        )

        compressed_context[
            "identity_elasticity_layer_report"
        ] = runtime_context.get(
            "identity_elasticity_layer_report",
            {}
        )

        compressed_context[
            "novelty_promotion_gate_report"
        ] = runtime_context.get(
            "novelty_promotion_gate_report",
            {}
        )

        compressed_context[
            "cognitive_operating_system_report"
        ] = runtime_context.get(
            "cognitive_operating_system_report",
            {}
        )

        compressed_context[
            "dynamic_cognitive_swapping_report"
        ] = runtime_context.get(
            "dynamic_cognitive_swapping_report",
            {}
        )

        compressed_context[
            "predictive_attention_routing_v2_report"
        ] = runtime_context.get(
            "predictive_attention_routing_v2_report",
            {}
        )

        compressed_context[
            "recursive_budget_market_report"
        ] = runtime_context.get(
            "recursive_budget_market_report",
            {}
        )

        compressed_context[
            "distributed_cognitive_execution_report"
        ] = runtime_context.get(
            "distributed_cognitive_execution_report",
            {}
        )

        compressed_context[
            "cognitive_threading_report"
        ] = runtime_context.get(
            "cognitive_threading_report",
            {}
        )

        compressed_context[
            "semantic_dma_report"
        ] = runtime_context.get(
            "semantic_dma_report",
            {}
        )

        compressed_context[
            "predictive_cognitive_compilation_report"
        ] = runtime_context.get(
            "predictive_cognitive_compilation_report",
            {}
        )

        compressed_context[
            "distributed_semantic_execution_fabric_report"
        ] = runtime_context.get(
            "distributed_semantic_execution_fabric_report",
            {}
        )

        compressed_context[
            "semantic_thread_scheduler_report"
        ] = runtime_context.get(
            "semantic_thread_scheduler_report",
            {}
        )

        compressed_context[
            "cognitive_dma_report"
        ] = runtime_context.get(
            "cognitive_dma_report",
            {}
        )

        compressed_context[
            "semantic_cache_compiler_report"
        ] = runtime_context.get(
            "semantic_cache_compiler_report",
            {}
        )

        compressed_context[
            "entropy_field_regulator_report"
        ] = runtime_context.get(
            "entropy_field_regulator_report",
            {}
        )

        compressed_context[
            "cognitive_thermodynamics_report"
        ] = runtime_context.get(
            "cognitive_thermodynamics_report",
            {}
        )

        compressed_context[
            "entropy_field_engine_report"
        ] = runtime_context.get(
            "entropy_field_engine_report",
            {}
        )

        compressed_context[
            "semantic_cooling_system_report"
        ] = runtime_context.get(
            "semantic_cooling_system_report",
            {}
        )

        compressed_context[
            "attention_economics_report"
        ] = runtime_context.get(
            "attention_economics_report",
            {}
        )

        compressed_context[
            "cognitive_energy_router_report"
        ] = runtime_context.get(
            "cognitive_energy_router_report",
            {}
        )

        compressed_context[
            "semantic_heat_dissipation_report"
        ] = runtime_context.get(
            "semantic_heat_dissipation_report",
            {}
        )

        compressed_context[
            "cognitive_kernel_report"
        ] = runtime_context.get(
            "cognitive_kernel_report",
            {}
        )

        compressed_context[
            "causal_world_simulation_report"
        ] = runtime_context.get(
            "causal_world_simulation_report",
            {}
        )

        compressed_context[
            "cognitive_immune_system_v2_report"
        ] = runtime_context.get(
            "cognitive_immune_system_v2_report",
            {}
        )

        compressed_context[
            "semantic_operating_system_report"
        ] = runtime_context.get(
            "semantic_operating_system_report",
            {}
        )

        compressed_context[
            "identity_stability_report"
        ] = runtime_context.get(
            "identity_stability_report",
            {}
        )

        compressed_context[
            "cognitive_event_bus_report"
        ] = runtime_context.get(
            "cognitive_event_bus_report",
            {}
        )

        compressed_context[
            "goal_hierarchy_report"
        ] = runtime_context.get(
            "goal_hierarchy_report",
            {}
        )

        compressed_context[
            "recursive_self_model_report"
        ] = runtime_context.get(
            "recursive_self_model_report",
            {}
        )

        compressed_context[
            "meta_cognitive_executive_report"
        ] = runtime_context.get(
            "meta_cognitive_executive_report",
            {}
        )

        compressed_context[
            "governance_reports"
        ] = {

            "runtime_governance":
            governance_report,

            "cognitive_governance":
            cognitive_governance_report,

            "hierarchical_memory":
            hierarchical_memory_report,

            "safe_concept_folding":
            safe_concept_folding_report,

            "semantic_pointer":
            semantic_pointer_report,

            "semantic_activation":
            semantic_activation_report,

            "cognitive_entropy":
            cognitive_entropy_report,

            "cognitive_energy_economy":
            cognitive_energy_economy_report,

            "memory_compression_runtime":
            memory_compression_runtime_report,

            "attention_kernel":
            attention_kernel_report,

            "cognitive_attention_router":
            cognitive_attention_router_report,

            "adaptive_semantic_control":
            adaptive_semantic_control_report,

            "cognitive_identity":
            cognitive_identity_report,

            "latent_reservoir":
            latent_reservoir_report,

            "executive_arbitration":
            executive_arbitration_report,

            "identity_core":
            identity_core_report,

            "identity_stability":
            identity_stability_report,

            "horizon_memory":
            horizon_memory_report,

            "cognitive_scheduler":
            cognitive_scheduler_report,

            "adaptive_executive_hierarchy":
            adaptive_executive_hierarchy_report,

            "cognitive_stability_infrastructure":
            cognitive_stability_report,

            "controlled_safe_novelty":
            controlled_safe_novelty_report,

            "cognitive_physics":
            cognitive_physics_report,

            "semantic_firewall":
            semantic_firewall_report,

            "causal_rehearsal":
            causal_rehearsal_report,

            "constructive_reasoning":
            constructive_reasoning_report,

            "evolutionary_memory":
            evolutionary_memory_report,

            "evolutionary_graveyard":
            evolutionary_graveyard_report,

            "truth_graveyard_consistency":
            truth_graveyard_consistency_report,

            "ontological_boundary":
            ontological_boundary_report,

            "existential_economics":
            existential_economics_report,

            "existential_homeostasis":
            existential_homeostasis_report,

            "existential_pressure":
            existential_pressure_report,

            "adaptive_equilibrium":
            adaptive_equilibrium_report,

            "hybrid_governance":
            hybrid_governance_report,

            "recursive_reflective":
            recursive_reflective_report,

            "existential_governance":
            existential_governance_report,

            "judicial_cognition":
            judicial_cognition_report,

            "cognitive_constitution":
            cognitive_constitution_report,

            "cognitive_ecology":
            cognitive_ecology_report,

            "cognitive_homeostasis":
            cognitive_homeostasis_report,

            "entropy_regulator":
            entropy_regulator_report,

            "cognitive_natural_selection":
            cognitive_natural_selection_report,

            "extinction_engine":
            extinction_engine_report,

            "trait_recovery":
            trait_recovery_report,

            "evolution_sandbox":
            evolution_sandbox_report,

            "stability_field":
            stability_field_report,

            "semantic_physics":
            semantic_physics_report,

            "semantic_field_dynamics":
            semantic_field_dynamics_report,

            "semantic_spine":
            semantic_spine_report,

            "identity_reasoner":
            identity_reasoner_report,

            "cognitive_immune":
            cognitive_immune_report,

            "concept_fusion":
            concept_fusion_report,

            "concept_lineage":
            concept_lineage_report,

            "recursive_guardian":
            recursive_guardian_report,

            "identity_continuity_guardian":
            identity_continuity_guardian_report,

            "semantic_legitimacy":
            semantic_legitimacy_report,

            "adaptive_permissioning":
            adaptive_permissioning_report,

            "constitutional_runtime":
            constitutional_runtime_report,

            "civilization":
            civilization_report,

            "memory_compression":
            memory_compression_report
        }

        compressed_context = self._cleanup_truth_commit_reasons(
            compressed_context
        )
        compressed_context = self._apply_learning_saturation(
            compressed_context
        )
        compressed_context[
            "governance_cache_report"
        ] = self._store_governance_context(
            compressed_context,
            governance_cache_metadata,
        )
        compressed_context[
            "GOVERNANCE_CACHE_REPORT"
        ] = compressed_context[
            "governance_cache_report"
        ]
        compressed_context = (
            self._apply_dynamic_telemetry_reduction(
                compressed_context
            )
        )

        self.runtime.bulk_update_context(
            compressed_context
        )

    # ========================================
    # HEALTH
    # ========================================

    def run_health_cycle(self):

        runtime_context = (
            self.runtime.get_context()
        )

        if not self._layer_allowed(
            "context_discovery",
            runtime_context,
        ):

            runtime_context[
                "health_report"
            ] = self._router_skipped_report(
                "context_discovery",
                runtime_context,
            )
            self.runtime.bulk_update_context(
                runtime_context
            )
            return

        health_report = (
            self.context_health_monitor
            .run_health_cycle(
                self.context_bus
            )
        )

        runtime_context[
            "health_report"
        ] = health_report

        self.runtime.bulk_update_context(
            runtime_context
        )

    # ========================================
    # FINALIZATION
    # ========================================

    def _world_governance_report_for_finalization(
        self,
        runtime_context,
    ):

        report = runtime_context.get(
            "world_governance_report"
        )

        if not isinstance(report, dict):

            report = getattr(
                self.runtime,
                "world_governance_report",
                None,
            )

        if isinstance(report, dict):

            return report

        return {
            "WORLD_GOVERNANCE_REPORT": {},
            "finalization_state": "skipped",
            "reason": "world_governance_report_not_available",
        }

    def finalize_runtime(self):

        runtime_context = self.runtime.get_context()
        if (
            self.reasoning_budget.get("mode") == "fast"
            and self.reasoning_budget.get("report_level") == "minimal"
        ):

            return self.finalize_runtime_fast()

        mode = self.runtime_finalization_optimizer.choose_mode(
            reasoning_budget=self.runtime.current_reasoning_budget,
            invalidated_concepts=self.runtime.invalidated_concepts,
            runtime_context=runtime_context,
        )

        if mode == "fast":

            return self.finalize_runtime_fast()

        return self.finalize_runtime_deep()

    def finalize_runtime_fast(self):

        started_at = time.perf_counter()
        max_seconds = 3

        runtime_context = (
            self.runtime.get_context()
        )
        shutdown_security = self.execution_authority_guard.request_permission(
            "shutdown_runtime",
            runtime_context,
        )
        if shutdown_security.permission == "DENY":
            runtime_context[
                "runtime_finalization_report"
            ] = {
                "runtime_state": "shutdown_denied_by_security",
                "security_decision": shutdown_security.as_dict(),
            }
            runtime_context[
                "SECURITY_REPORT"
            ] = self.security_reporter.build_report()
            self.runtime.bulk_update_context(runtime_context)
            return runtime_context

        reused_concepts = list(
            self.runtime.reused_concepts
            or self.cognitive_cache_manager.reused_concepts
        )

        runtime_context[
            "cross_task_replication_collector_report"
        ] = runtime_context.get(
            "cross_task_replication_collector_report",
            {
                "finalization_state": "reused_or_skipped",
                "reason": "fast_finalization_stable_concepts",
            },
        )

        runtime_context[
            "knowledge_replication_ledger_report"
        ] = runtime_context.get(
            "knowledge_replication_ledger_report",
            {},
        )

        runtime_context[
            "knowledge_concept_lifecycle_report"
        ] = runtime_context.get(
            "knowledge_concept_lifecycle_report",
            {
                "finalization_state": "reused_or_skipped",
                "stable_truth_revalidation": "skipped",
            },
        )

        if "knowledge_generalization_engine_report" not in runtime_context:

            if (
                self.reasoning_budget.get("mode") == "fast"
                and self.reasoning_budget.get("report_level") == "minimal"
            ):

                runtime_context[
                    "knowledge_generalization_engine_report"
                ] = {
                    "finalization_state": "deferred",
                    "reason": "fast_minimal_terminal_projection",
                }

            else:

                runtime_context[
                    "knowledge_generalization_engine_report"
                ] = (
                    self.cross_task_replication_collector
                    .knowledge_generalization_engine
                    .report()
                )

        finalization_report = (
            self.runtime_finalization_optimizer
            .fast_report(
                reused_concepts=reused_concepts,
                started_at=started_at,
            )
        )
        shutdown_sequence = [
            "stop_background_tasks",
            "terminate_learning_loops",
            "flush_minimal_memory",
            "persist_essential_metrics",
            "finalize_runtime",
            "shutdown",
        ]
        finalization_report[
            "shutdown_sequence"
        ] = shutdown_sequence
        finalization_report[
            "background_tasks_stopped"
        ] = True
        finalization_report[
            "learning_loops_terminated"
        ] = True
        finalization_report[
            "minimal_memory_flushed"
        ] = True
        finalization_report[
            "essential_metrics_persisted"
        ] = True
        finalization_report[
            "shutdown_mode"
        ] = runtime_context.get(
            "shutdown_mode",
            "fast",
        )
        finalization_report[
            "termination_reason"
        ] = runtime_context.get(
            "termination_reason",
            finalization_report.get("reason"),
        )
        finalization_report[
            "security_decision"
        ] = shutdown_security.as_dict()

        runtime_context[
            "runtime_finalization_report"
        ] = finalization_report

        runtime_context[
            "finalization_report"
        ] = {
            "runtime_state": "completed",
            "timestamp": str(datetime.utcnow()),
            **finalization_report,
        }

        self.runtime.bulk_update_context(
            runtime_context
        )

        if time.perf_counter() - started_at < max_seconds:
            self.runtime.apply_world_governance_report(
                self._world_governance_report_for_finalization(
                    runtime_context
                )
            )
        else:
            runtime_context["finalization_warning"] = (
                "world_governance_application_deferred"
            )
            runtime_context["runtime_finalization_report"][
                "finalization_budget_exceeded"
            ] = True
            self.runtime.bulk_update_context(runtime_context)

        return runtime_context

    def finalize_runtime_deep(self):

        started_at = time.perf_counter()

        runtime_context = (
            self.runtime.get_context()
        )
        shutdown_security = self.execution_authority_guard.request_permission(
            "shutdown_runtime",
            runtime_context,
        )
        if shutdown_security.permission == "DENY":
            runtime_context[
                "runtime_finalization_report"
            ] = {
                "runtime_state": "shutdown_denied_by_security",
                "security_decision": shutdown_security.as_dict(),
            }
            runtime_context[
                "SECURITY_REPORT"
            ] = self.security_reporter.build_report()
            self.runtime.bulk_update_context(runtime_context)
            return runtime_context

        cross_task_replication_report = (
            self.cross_task_replication_collector
            .collect(runtime_context)
        )

        runtime_context[
            "cross_task_replication_collector_report"
        ] = cross_task_replication_report

        runtime_context[
            "knowledge_replication_ledger_report"
        ] = cross_task_replication_report.get(
            "knowledge_replication_ledger",
            {}
        )

        runtime_context[
            "knowledge_concept_lifecycle_report"
        ] = (
            self.concept_lifecycle_manager
            .update_knowledge_maturity(
                runtime_context[
                    "knowledge_replication_ledger_report"
                ],
                runtime_context,
            )
        )

        runtime_context[
            "knowledge_generalization_engine_report"
        ] = cross_task_replication_report.get(
            "knowledge_generalization",
            self.cross_task_replication_collector
            .knowledge_generalization_engine
            .report(),
        )

        runtime_context[
            "finalization_report"
        ] = {
            "runtime_state": "completed",
            "timestamp": str(datetime.utcnow())
        }

        finalization_report = (
            self.runtime_finalization_optimizer
            .deep_report(
                recomputed_concepts=list(
                    self.runtime.invalidated_concepts
                ),
                reused_concepts=list(
                    self.runtime.reused_concepts
                    or self.cognitive_cache_manager.reused_concepts
                ),
                started_at=started_at,
            )
        )

        runtime_context[
            "runtime_finalization_report"
        ] = finalization_report

        runtime_context[
            "finalization_report"
        ].update(finalization_report)

        self.runtime.bulk_update_context(
            runtime_context
        )

        return runtime_context

    # ========================================
    # BUILD PIPELINE REPORT
    # ========================================

    def build_pipeline_report(self):

        return {

            "pipeline_state":
            self.pipeline_state,

            "stage_count":
            len(
                self.pipeline_stages
            ),

            "stages":
            [
                {
                    "stage_name":
                    stage.get(
                        "stage_name"
                    ),

                    "function_name":
                    stage.get(
                        "function_name"
                    ),

                    "priority":
                    stage.get(
                        "priority"
                    ),

                    "category":
                    stage.get(
                        "category"
                    )
                }

                for stage in self.pipeline_stages
            ],

            "completed_stages":
            self.completed_stages,

            "failed_stages":
            self.failed_stages,

            "stage_history_size":
            len(
                self.stage_execution_history
            ),

            "governance":
            NEXRYN_STAGE_GOVERNANCE,

            "world_governance":
            self.world_governance_kernel.build_report(),

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # RUN PIPELINE
    # ========================================

    def run(
        self,
        task_path=None,
        arc_replication_candidates=None,
        mode=None,
        max_chain_depth=None,
        max_concepts=None,
        telemetry_enabled=None,
        cache_dependencies=None,
        report_level=None,
        post_success_mode="fast",
        profile=False,
        profile_level="minimal",
        audit_sections_requested=None,
        deep_budget_overrides=None,
        authoritative_execution_plan=None,
        experimental_budget_request=None,
        experimental_budget_grant=None,
        run_id=None,
    ):

        self.profiling_enabled = bool(profile)
        self.profile_level = (
            str(profile_level or "minimal").lower()
        )
        if self.profile_level not in {"minimal", "detailed"}:
            self.profile_level = "minimal"
        self.telemetry.configure(
            enabled=self.profiling_enabled,
        )
        if self.profiling_enabled:
            self.telemetry.clear()

        self.requested_budget_mode = mode
        post_success_mode = str(
            post_success_mode or "fast"
        ).lower()
        if post_success_mode not in {"fast", "normal", "deep"}:
            post_success_mode = "fast"
        self.post_success_mode = post_success_mode

        self.configure_reasoning_budget(
            mode=mode,
            max_chain_depth=max_chain_depth,
            max_concepts=max_concepts,
            telemetry_enabled=telemetry_enabled,
            cache_dependencies=cache_dependencies,
            report_level=report_level,
        )
        if self.execution_profile.name in {"deep", "full"}:
            deep_budget = deep_mode_budget_manager.build_budget(
                **(deep_budget_overrides or {})
            )
            self.reasoning_budget = (
                deep_mode_budget_manager.constrain_reasoning_budget(
                    self.reasoning_budget,
                    deep_budget,
                )
            )
            self.reasoning_budget["audit_sections_requested"] = list(
                audit_sections_requested or []
            )
            self.reasoning_budget["report_level"] = (
                deep_mode_budget_manager.bounded_report_level(
                    "deep",
                    self.reasoning_budget.get("report_level", "full"),
                    {
                        f"audit_{section}": True
                        for section in audit_sections_requested or []
                    },
                )
            )
        self.prepare_task_run()
        if run_id is not None:
            self.runtime.update_context(
                "run_id",
                str(run_id),
            )
            self.run_scoped_budget_authority_context[
                "run_id"
            ] = str(run_id)
        if isinstance(authoritative_execution_plan, dict):
            self.run_scoped_budget_authority_context[
                "authoritative_execution_plan"
            ] = dict(authoritative_execution_plan)
            self.run_scoped_budget_authority_context[
                "authoritative_execution_plan_reference"
            ] = {
                "run_id": authoritative_execution_plan.get("run_id"),
                "execution_plan_id": authoritative_execution_plan.get(
                    "execution_plan_id"
                ),
                "execution_plan_schema_version": (
                    authoritative_execution_plan.get(
                        "execution_plan_schema_version"
                    )
                ),
                "plan_scope": authoritative_execution_plan.get("plan_scope"),
                "temporal_authority_state": (
                    authoritative_execution_plan.get(
                        "temporal_authority_state"
                    )
                ),
            }
            self.runtime.update_context(
                "authoritative_execution_plan",
                self.run_scoped_budget_authority_context[
                    "authoritative_execution_plan"
                ],
            )
            self.runtime.update_context(
                "authoritative_execution_plan_reference",
                self.run_scoped_budget_authority_context[
                    "authoritative_execution_plan_reference"
                ],
            )
        if experimental_budget_request is not None:
            request_report = (
                experimental_budget_request.as_report()
                if hasattr(experimental_budget_request, "as_report")
                else dict(experimental_budget_request)
                if isinstance(experimental_budget_request, dict)
                else experimental_budget_request
            )
            self.run_scoped_budget_authority_context[
                "experimental_budget_request"
            ] = request_report
            self.runtime.update_context(
                "experimental_budget_request",
                request_report,
            )
        if experimental_budget_grant is not None:
            grant_report = (
                experimental_budget_grant.as_report()
                if hasattr(experimental_budget_grant, "as_report")
                else dict(experimental_budget_grant)
                if isinstance(experimental_budget_grant, dict)
                else experimental_budget_grant
            )
            self.run_scoped_budget_authority_context[
                "experimental_budget_grant"
            ] = grant_report
            self.runtime.update_context(
                "experimental_budget_grant",
                grant_report,
            )
        self.runtime.update_context(
            "execution_profile",
            self.execution_profile.as_runtime_metadata(),
        )
        self.runtime.update_context(
            "shared_cognitive_pipeline",
            self.execution_profile.pipeline_name,
        )

        if task_path is not None:

            self.runtime.update_context(
                "task_path",
                task_path
            )

        if arc_replication_candidates is not None:

            self.runtime.update_context(
                "arc_replication_candidates",
                arc_replication_candidates
            )

        reusable_truths = (
            self.epistemic_decision_engine
            .cognition_layer
            .truth_commit_engine
            .reusable_truths()
        )

        self.runtime.update_context(
            "reusable_truth_commitments",
            reusable_truths
        )
        self.runtime.update_context(
            "truth_commitments",
            reusable_truths
        )
        self.runtime.update_context(
            "truth_registry_report",
            self.epistemic_decision_engine
            .cognition_layer
            .truth_commit_engine
            .registry
            .report()
        )

        module_start = time.perf_counter()
        self.boot_runtime()
        self._record_module_timing("runtime_boot", module_start)

        context = self.runtime.get_context()
        module_start = time.perf_counter()
        if self._layer_allowed("adaptive_reuse", context):
            adaptive_reuse_report = (
                self.adaptive_reuse_engine.evaluate_reuse(context)
            )
        else:
            adaptive_reuse_report = self._router_skipped_report(
                "adaptive_reuse",
                context,
            )
        context["adaptive_reuse_report"] = adaptive_reuse_report
        context["ADAPTIVE_REUSE_REPORT"] = adaptive_reuse_report
        context["COGNITIVE_REUSE_REPORT"] = adaptive_reuse_report
        context["experience_reuse_report"] = adaptive_reuse_report.get(
            "experience_reuse_report",
            adaptive_reuse_report.get("ADAPTIVE_REUSE_REPORT", {}),
        )
        reused_assets = adaptive_reuse_report.get("reused_assets", {})
        self.performance_counters["estimated_runtime_saved"] += float(
            adaptive_reuse_report.get("estimated_runtime_saved", 0.0) or 0.0
        )
        self.performance_counters["estimated_compute_saved"] += float(
            adaptive_reuse_report.get("estimated_compute_saved", 0.0) or 0.0
        )
        if reused_assets:
            context["reusable_cognitive_assets"] = reused_assets
            context["skip_redundant_reasoning"] = adaptive_reuse_report.get(
                "skip_redundant_reasoning",
                False,
            )
            context["dependency_reasoning_skipped"] = (
                adaptive_reuse_report.get("dependency_reasoning_skipped", False)
            )
            self.performance_counters["cache_hits"] += int(
                adaptive_reuse_report.get("cache_hits", 0)
            )
            self.performance_counters["truth_hits"] += int(
                adaptive_reuse_report.get("truth_hits", 0)
            )
            self.performance_counters["strategy_hits"] += int(
                adaptive_reuse_report.get("strategy_hits", 0)
            )
            self.performance_counters["context_hits"] += int(
                adaptive_reuse_report.get("context_hits", 0)
            )
            self.performance_counters["program_hits"] += int(
                adaptive_reuse_report.get("program_hits", 0)
            )
            self.performance_counters["world_model_hits"] += int(
                adaptive_reuse_report.get("world_model_hits", 0)
            )
            self.performance_counters["dependency_snapshot_hits"] += int(
                adaptive_reuse_report.get("dependency_snapshot_hits", 0)
            )
            if "dependency_snapshot" in reused_assets:
                self.performance_counters["dependency_reasoning_skipped"] += 1
        else:
            self.performance_counters["cache_misses"] += int(
                adaptive_reuse_report.get("cache_misses", 0)
            )
            self.performance_counters["truth_misses"] += int(
                adaptive_reuse_report.get("truth_misses", 0)
            )
            self.performance_counters["strategy_misses"] += int(
                adaptive_reuse_report.get("strategy_misses", 0)
            )
            self.performance_counters["context_misses"] += int(
                adaptive_reuse_report.get("context_misses", 0)
            )
            self.performance_counters["program_misses"] += int(
                adaptive_reuse_report.get("program_misses", 0)
            )
            self.performance_counters["world_model_misses"] += int(
                adaptive_reuse_report.get("world_model_misses", 0)
            )
            self.performance_counters["dependency_snapshot_misses"] += int(
                adaptive_reuse_report.get("dependency_snapshot_misses", 0)
            )
        self.performance_counters["adaptive_reuse_evaluations"] += 1
        self.runtime.bulk_update_context(context)
        self._record_module_timing("adaptive_reuse", module_start)

        if self._layer_allowed("meta_cognition", context):
            self.run_meta_supervisor_cycle(context)
        else:
            context[
                "meta_supervisor_report"
            ] = self._router_skipped_report(
                "meta_cognition",
                context,
            )
            context[
                "META_SUPERVISOR_REPORT"
            ] = context["meta_supervisor_report"]
            self.runtime.bulk_update_context(context)

        module_start = time.perf_counter()
        stage_context = self.run_stage_cycle()
        self._record_module_timing("stage_cycle", module_start)

        context = (
            stage_context
            if isinstance(stage_context, dict)
            else self.runtime.get_context()
        )
        budget_report = context.get(
            "cognitive_budget_report",
            {},
        )
        if not isinstance(budget_report, dict):
            budget_report = {}
        minimal_report_requested = (
            self.reasoning_budget.get("report_level") == "minimal"
            or budget_report.get("report_level") == "minimal"
        )
        if (
            minimal_report_requested
            and context.get("fast_minimal_evaluation_closure", {}).get(
                "enabled"
            ) is True
        ):

            selected_mode = (
                budget_report.get("selected_mode")
                or self.reasoning_budget.get("mode")
            )

            context[
                "runtime_finalization_report"
            ] = {
                "runtime_state": "completed",
                "shutdown_mode": context.get("shutdown_mode", "fast"),
                "reason": "fast_minimal_post_evaluation_return",
                "post_evaluation_operations_skipped": [
                    "reasoning_cycle",
                    "dependency_reasoning_cycle",
                    "process_semantic_cycle",
                    "context_truth_advancement_cycle",
                    "governance_cycle",
                    "safe_self_repair_cycle",
                    "health_cycle",
                    "pipeline_cache_store",
                    "motivation_cycle",
                ],
                "success_preserved": context.get("episode_completed") is True,
                "timestamp": str(datetime.utcnow()),
            }
            context[
                "finalization_report"
            ] = context["runtime_finalization_report"]
            context[
                "performance_report"
            ] = {
                "system": "runtime_reasoning_budget",
                "mode": selected_mode,
                "report_level": (
                    budget_report.get("report_level")
                    or self.reasoning_budget.get("report_level")
                ),
                "module_timings": list(
                    self.performance_counters.get(
                        "module_timings",
                        [],
                    )
                ),
                "minimal_terminal_closure": True,
            }
            context[
                "cache_metrics_report"
            ] = {
                "report_state": "deferred",
                "reason": "fast_minimal_post_evaluation_return",
            }
            context[
                "cognitive_cache_report"
            ] = context["cache_metrics_report"]
            context[
                "pipeline_fast_minimal_return"
            ] = {
                "enabled": True,
                "reason": "fast_minimal_post_evaluation_return",
            }
            context = self._attach_runtime_topology_observation(
                context,
                context.get("execution_trace", []),
            )
            return context

        if self.cached_pipeline_result is not None:

            context = self.runtime.get_context()
            post_success_shutdown = context.get(
                "post_success_shutdown",
                {},
            )
            if (
                context.get("episode_completed") is True
                or (
                    isinstance(post_success_shutdown, dict)
                    and post_success_shutdown.get("enabled") is True
                )
            ):
                from runtime.shutdown import ShutdownController

                shutdown_controller = ShutdownController()
                context = shutdown_controller.execute_shutdown(
                    context,
                    exit_process=False,
                )
                context[
                    "runtime_finalization_report"
                ] = {
                    "runtime_state": "completed",
                    "shutdown_mode": context.get("shutdown_mode", "fast"),
                    "reason": "cached_success_shutdown_first",
                    "post_success_operations_skipped": [
                        "motivation_cycle",
                        "meta_decision_cycle",
                        "meta_supervisor_cycle",
                        "cache_save",
                    ],
                    "success_preserved": True,
                    "timestamp": str(datetime.utcnow()),
                }
                context[
                    "finalization_report"
                ] = context["runtime_finalization_report"]
                if "performance_report" not in context:
                    context["performance_report"] = self.performance_report()
                self.runtime.bulk_update_context(context)
                return self._compact_final_context(context)

            self.run_motivation_cycle(context)
            context = self.runtime.get_context()
            self.run_meta_decision_cycle(context)
            context = self.runtime.get_context()
            if self._layer_allowed("meta_cognition", context):
                self.run_meta_supervisor_cycle(context)
            else:
                context["meta_supervisor_report"] = (
                    self._router_skipped_report("meta_cognition", context)
                )
                context["META_SUPERVISOR_REPORT"] = (
                    context["meta_supervisor_report"]
                )
                self.runtime.bulk_update_context(context)
            context = self.runtime.get_context()
            performance_report = self.performance_report()
            cache_report = self.cognitive_cache_manager.build_report()
            context[
                "performance_report"
            ] = performance_report
            context[
                "cache_metrics_report"
            ] = cache_report
            context[
                "cognitive_cache_report"
            ] = cache_report
            self._save_cognitive_cache()
            cache_report = self.cognitive_cache_manager.build_report()
            performance_report = self.performance_report()
            context[
                "performance_report"
            ] = performance_report
            context[
                "cache_metrics_report"
            ] = cache_report
            context[
                "cognitive_cache_report"
            ] = cache_report
            self.runtime.update_cache_metrics(
                self.cognitive_cache_manager.metrics()
            )
            self.runtime.update_performance_state(
                execution_time=performance_report.get(
                    "total_runtime_seconds",
                    0.0,
                ),
                slowest_modules=performance_report.get(
                    "slowest_modules",
                    [],
                ),
            )
            context = self.attach_performance_intelligence(context)
            return self._compact_final_context(context)

        context = self.runtime.get_context()
        post_success_shutdown = context.get(
            "post_success_shutdown",
            {},
        )
        if (
            isinstance(post_success_shutdown, dict)
            and post_success_shutdown.get("enabled") is True
        ):

            from runtime.shutdown import ShutdownController

            shutdown_controller = ShutdownController()
            context = shutdown_controller.execute_shutdown(
                context,
                exit_process=False,
            )
            context[
                "runtime_finalization_report"
            ] = {
                "runtime_state": "completed",
                "shutdown_mode": post_success_shutdown.get("mode", "fast"),
                "reason": "episode_completed_shutdown_first",
                "post_success_operations_skipped": [
                    "motivation_cycle",
                    "meta_supervisor_cycle",
                    "safe_self_repair_cycle",
                    "world_governance_finalization",
                    "deep_finalization",
                ],
                "success_preserved": True,
                "timestamp": str(datetime.utcnow()),
            }
            context[
                "finalization_report"
            ] = context["runtime_finalization_report"]
            context[
                "performance_report"
            ] = context.get("performance_report")
            if context["performance_report"] is None:
                context["performance_report"] = self.performance_report()
            self.runtime.bulk_update_context(context)
            return self._compact_final_context(context)

        context = self.runtime.get_context()
        memory_decision = context.get(
            "cognitive_execution_decision",
            {},
        )

        if (
            isinstance(memory_decision, dict)
            and memory_decision.get("reasoning_required") is False
        ):

            self.run_motivation_cycle(context)
            context = self.runtime.get_context()
            self.run_meta_decision_cycle(context)
            context = self.runtime.get_context()
            if self._layer_allowed("meta_cognition", context):
                self.run_meta_supervisor_cycle(context)
            else:
                context["meta_supervisor_report"] = (
                    self._router_skipped_report("meta_cognition", context)
                )
                context["META_SUPERVISOR_REPORT"] = (
                    context["meta_supervisor_report"]
                )
                self.runtime.bulk_update_context(context)
            context = self.runtime.get_context()
            context[
                "reasoning_report"
            ] = {
                "system": "reasoning_orchestrator",
                "report_state": "skipped",
                "skipped": True,
                "status": "skipped_by_memory_first_reuse",
                "reasoning_invoked": False,
                "decision": memory_decision.get("decision"),
            }
            context[
                "dependency_reasoning_report"
            ] = {
                "system": "dependency_reasoning",
                "report_state": "skipped",
                "skipped": True,
                "status": "skipped_by_memory_first_reuse",
                "reasoning_invoked": False,
            }
            context[
                "process_semantic_report"
            ] = {
                "system": "process_semantic_engine",
                "report_state": "skipped",
                "skipped": True,
                "status": "skipped_by_memory_first_reuse",
                "reasoning_invoked": False,
            }
            context[
                "governance_cache_report"
            ] = {
                "cache_state": "memory_first_reuse",
                "skipped_governance": True,
                "reason": "stable_version_hash_unchanged",
            }
            context[
                "governance_reuse_skipped"
            ] = True
            self.performance_counters["governance_skips"] += 1
            self.runtime.bulk_update_context(context)

            context = self.runtime.get_context()
            context = self.run_safe_self_repair_cycle(
                context,
                trigger="before_shutdown",
            )
            module_start = time.perf_counter()
            self.finalize_runtime()
            self._record_module_timing("finalize_runtime", module_start)

            context = self.runtime.get_context()
            context[
                "performance_report"
            ] = self.performance_report()
            context[
                "cache_metrics_report"
            ] = self.cognitive_cache_manager.build_report()
            context[
                "cognitive_cache_report"
            ] = context[
                "cache_metrics_report"
            ]
            self.runtime.update_cache_metrics(
                self.cognitive_cache_manager.metrics()
            )
            self.runtime.update_performance_state(
                execution_time=context["performance_report"].get(
                    "total_runtime_seconds",
                    0.0,
                ),
                slowest_modules=context["performance_report"].get(
                    "slowest_modules",
                    [],
                ),
            )
            context = self.attach_performance_intelligence(context)
            return self._compact_final_context(context)

        module_start = time.perf_counter()
        if (
            self.meta_supervisor.is_action_allowed("reasoning")
            and self._layer_allowed("inference", self.runtime.get_context())
        ):
            self.performance_counters["reasoning_executions"] += 1
            self.run_reasoning_cycle()
            self._record_module_timing("reasoning_cycle", module_start)
        else:
            self.performance_counters["reasoning_avoided"] += 1
            context = self.runtime.get_context()
            router_blocked = not self._layer_allowed("inference", context)
            context[
                "reasoning_report"
            ] = {
                "system": "reasoning_orchestrator",
                "report_state": "skipped",
                "skipped": True,
                "status": "skipped_by_meta_supervisor",
                "reasoning_invoked": False,
                "reason": context.get(
                    "cognitive_directive",
                    {},
                ).get("reason"),
                "skip_reason": (
                    self._router_skipped_report(
                        "inference",
                        context,
                    )["skip_reason"]
                    if router_blocked
                    else "blocked_by_meta_supervisor"
                ),
                "reasoning_depth": 0,
                "active_routes": 0,
            }
            self.runtime.bulk_update_context(context)

        activation_report = self.runtime.get_context().get(
            "dependency_context_activation_report",
            {},
        )
        activation_already_ran = (
            isinstance(activation_report, dict)
            and (
                activation_report.get("dependency_runtime_invoked")
                or activation_report.get("process_semantic_runtime_invoked")
                or activation_report.get("context_truth_runtime_invoked")
            )
        )
        if not activation_already_ran:
            if self.meta_supervisor.is_action_allowed("reasoning"):
                self.run_dependency_reasoning_cycle()
            else:
                context = self.runtime.get_context()
                context[
                    "dependency_reasoning_report"
                ] = {
                    "system": "dependency_reasoning",
                    "report_state": "skipped",
                    "skipped": True,
                    "status": "skipped_by_meta_supervisor",
                    "reasoning_invoked": False,
                }
                self.runtime.bulk_update_context(context)

            if self.meta_supervisor.is_action_allowed("context_discovery"):
                self.run_process_semantic_cycle()
            else:
                context = self.runtime.get_context()
                context[
                    "process_semantic_report"
                ] = {
                    "system": "process_semantic_engine",
                    "report_state": "skipped",
                    "skipped": True,
                    "status": "skipped_by_meta_supervisor",
                    "context_discovery_invoked": False,
                }
                self.runtime.bulk_update_context(context)

            self.run_context_truth_advancement_cycle()

        if self.meta_supervisor.is_action_allowed("governance") and (
            self.runtime.is_meta_action_enabled("ESCALATE_TO_GOVERNANCE") or (
                self.runtime.current_meta_decision or {}
            ).get("enable_governance") is not False
        ):

            module_start = time.perf_counter()
            self.run_governance_cycle()
            self._record_module_timing("governance_cycle", module_start)
            context = self.runtime.get_context()
            self.run_safe_self_repair_cycle(
                context,
                trigger="after_governance",
            )

        else:

            context = self.runtime.get_context()
            skip_reason = (
                "blocked_by_meta_supervisor"
                if not self.meta_supervisor.is_action_allowed("governance")
                else "skipped_by_meta_decision"
            )
            context[
                "governance_report"
            ] = {
                "system": "deep_governance",
                "report_state": "skipped",
                "skipped": True,
                "status": skip_reason,
                "reason": context.get(
                    "cognitive_directive",
                    {},
                ).get(
                    "reason",
                    context.get("meta_decision_reason"),
                ),
            }
            context[
                "governance_cache_report"
            ] = {
                "cache_state": "meta_reuse",
                "skipped_governance": True,
                "reason": context.get(
                    "cognitive_directive",
                    {},
                ).get(
                    "reason",
                    context.get("meta_decision_reason"),
                ),
            }
            self.runtime.bulk_update_context(context)

        context = self.runtime.get_context()
        context = self.run_safe_self_repair_cycle(
            context,
            trigger="before_shutdown",
        )
        early_exit_decision = (
            self.early_exit_controller
            .evaluate(context)
        )
        early_exit_report = (
            self.early_exit_controller
            .build_report(early_exit_decision)
        )
        context[
            "early_exit_report"
        ] = early_exit_report
        context[
            "early_exit_triggered"
        ] = early_exit_decision.should_stop
        self.runtime.apply_early_exit(
            early_exit_decision
        )
        self.runtime.bulk_update_context(
            context
        )

        if early_exit_decision.should_stop:

            context[
                "health_report"
            ] = {
                "system": "context_health_monitor",
                "report_state": "skipped",
                "skipped": True,
                "status": "skipped_by_early_exit",
                "reason": early_exit_decision.reason,
            }
            context[
                "finalization_report"
            ] = {
                "runtime_state": "skipped_by_early_exit",
                "reason": early_exit_decision.reason,
            }

        else:

            module_start = time.perf_counter()
            self.run_health_cycle()
            self._record_module_timing("health_cycle", module_start)

            module_start = time.perf_counter()
            self.finalize_runtime()
            self._record_module_timing("finalize_runtime", module_start)

        reusable_truths = (
            self.epistemic_decision_engine
            .cognition_layer
            .truth_commit_engine
            .reusable_truths()
        )
        context = self.runtime.get_context()
        context[
            "reusable_truth_commitments"
        ] = reusable_truths
        context[
            "truth_commitments"
        ] = reusable_truths
        context[
            "performance_report"
        ] = self.performance_report()
        context[
            "cache_metrics_report"
        ] = self.cognitive_cache_manager.build_report()
        context[
            "cognitive_cache_report"
        ] = context[
            "cache_metrics_report"
        ]
        pipeline_store_context = (
            context
            if self.reasoning_budget.get("report_level") == "full"
            else self.compact_report_builder.compact_context(
                context,
                level=self.reasoning_budget.get("report_level", "normal"),
            )
        )
        context[
            "pipeline_cache_store_report"
        ] = self.store_pipeline_result(pipeline_store_context)
        self._save_cognitive_cache()
        context[
            "performance_report"
        ] = self.performance_report()
        context[
            "cache_metrics_report"
        ] = self.cognitive_cache_manager.build_report()
        context[
            "cognitive_cache_report"
        ] = context[
            "cache_metrics_report"
        ]
        self.run_motivation_cycle(context)
        context = self.runtime.get_context()
        performance_report = context[
            "performance_report"
        ]
        cache_report = context[
            "cache_metrics_report"
        ]
        context[
            "runtime_metrics_report"
        ] = (
            self.runtime_metrics_collector
            .record(
                context,
                performance_report,
                cache_report,
            )
        )
        self.runtime.update_cache_metrics(
            self.cognitive_cache_manager.metrics()
        )
        self.runtime.update_performance_state(
            execution_time=performance_report.get(
                "total_runtime_seconds",
                0.0,
            ),
            slowest_modules=performance_report.get(
                "slowest_modules",
                [],
            ),
        )
        context = self.attach_performance_intelligence(context)
        return self._compact_final_context(context)


# ============================================
# GLOBAL PIPELINE
# ============================================

pipeline = (
    AdaptiveCognitivePipeline()
)
