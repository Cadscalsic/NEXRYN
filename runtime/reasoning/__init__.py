# ============================================
# NEXRYN REASONING SYSTEM
# ============================================


# ============================================
# REASONING ORCHESTRATOR
# ============================================

from runtime.reasoning.reasoning_orchestrator import (

    ReasoningOrchestrator,

    reasoning_orchestrator
)

from runtime.reasoning.spatial_translation_engine import (

    SpatialTranslationEngine,

    spatial_translation_engine
)

# ============================================
# SPATIAL REASONING
# ============================================

from runtime.reasoning.spatial_reasoning_engine import (

    SpatialReasoningEngine,

    spatial_reasoning_engine
)

# ============================================
# SPATIAL ABSTRACTION
# ============================================

from runtime.reasoning.spatial_abstraction_engine import (

    SpatialAbstractionEngine,

    spatial_abstraction_engine
)

# ============================================
# ANALOGICAL REASONING
# ============================================

from runtime.reasoning.analogical_reasoning_engine import (

    AnalogicalReasoningEngine,

    analogical_reasoning_engine
)

# ============================================
# CAUSAL REASONING
# ============================================

from runtime.reasoning.causal_reasoning_engine import (

    CausalReasoningEngine,

    causal_reasoning_engine
)

# ============================================
# SYMBOLIC REASONING
# ============================================

from runtime.reasoning.symbolic_reasoning_engine import (

    SymbolicReasoningEngine,

    symbolic_reasoning_engine
)

# ============================================
# RECURSIVE REASONING
# ============================================

from runtime.reasoning.recursive_reasoning_engine import (

    RecursiveReasoningEngine,

    recursive_reasoning_engine
)

# ============================================
# HYPOTHESIS ARBITRATION
# ============================================

from runtime.reasoning.hypothesis_arbitration_engine import (

    HypothesisArbitrationEngine,

    hypothesis_arbitration_engine
)

from runtime.reasoning.change_detection_engine import (

    ChangeDetectionEngine,

    change_detection_engine
)

from runtime.reasoning.transformation_salience_engine import (

    TransformationSalienceEngine,

    transformation_salience_engine
)

from runtime.reasoning.transformation_synthesis_engine import (

    TransformationSynthesisEngine,

    transformation_synthesis_engine
)

from runtime.reasoning.color_mapping_engine import (

    ColorMappingMatrix,

    ColorMappingReasoningEngine,

    color_mapping_engine
)

from runtime.reasoning.invariant_filter import (

    InvariantFilter,

    invariant_filter
)

from runtime.reasoning.object_centric_reasoner import (

    ObjectCentricReasoner,

    object_centric_reasoner
)

# ============================================
# COGNITIVE PRESSURE
# ============================================

from runtime.reasoning.cognitive_pressure_engine import (

    CognitivePressureEngine,

    cognitive_pressure_engine
)

from runtime.reasoning.generalization import (

    ARCGeneralizationEngine,

    generalization_engine
)

from runtime.reasoning.residual_reasoning_engine import (

    ResidualReasoningEngine,

    residual_reasoning_engine
)

from runtime.reasoning.spatial_residual_repair import (

    SpatialResidualRepair,

    spatial_residual_repair
)

from runtime.reasoning.object_residual_repair import (

    ObjectResidualRepair,

    object_residual_repair
)

from runtime.reasoning.counterfactual_repair_engine import (

    CounterfactualRepairEngine,

    counterfactual_repair_engine
)

from runtime.reasoning.reasoning_graph_report import (

    ReasoningGraphReportBuilder,

    reasoning_graph_report_builder
)

# ============================================
# EXPORTS
# ============================================

__all__ = [

    # ========================================
    # ORCHESTRATION
    # ========================================

    "ReasoningOrchestrator",

    "reasoning_orchestrator",

    # ========================================
    # SPATIAL REASONING
    # ========================================

    "SpatialReasoningEngine",

    "spatial_reasoning_engine",

    # ========================================
    # SPATIAL ABSTRACTION
    # ========================================

    "SpatialAbstractionEngine",

    "spatial_abstraction_engine",

    # ========================================
    # ANALOGICAL REASONING
    # ========================================

    "AnalogicalReasoningEngine",

    "analogical_reasoning_engine",

    # ========================================
    # CAUSAL REASONING
    # ========================================

    "CausalReasoningEngine",

    "causal_reasoning_engine",

    # ========================================
    # SYMBOLIC REASONING
    # ========================================

    "SymbolicReasoningEngine",

    "symbolic_reasoning_engine",

    # ========================================
    # RECURSIVE REASONING
    # ========================================

    "RecursiveReasoningEngine",

    "recursive_reasoning_engine",

    # ========================================
    # HYPOTHESIS ARBITRATION
    # ========================================

    "HypothesisArbitrationEngine",

    "hypothesis_arbitration_engine",

    "ChangeDetectionEngine",

    "change_detection_engine",

    "TransformationSalienceEngine",

    "transformation_salience_engine",

    "TransformationSynthesisEngine",

    "transformation_synthesis_engine",

    "ColorMappingMatrix",

    "ColorMappingReasoningEngine",

    "color_mapping_engine",

    "InvariantFilter",

    "invariant_filter",

    "ObjectCentricReasoner",

    "object_centric_reasoner",

    # ========================================
    # COGNITIVE PRESSURE
    # ========================================

    "CognitivePressureEngine",

    "cognitive_pressure_engine",

    # ========================================
    # ARC GENERALIZATION
    # ========================================

    "ARCGeneralizationEngine",

    "generalization_engine",

    # ========================================
    # SPATIAL REASONING
    # ========================================

    "SpatialTranslationEngine",

    "spatial_translation_engine",

    "SpatialReasoningEngine",

    "spatial_reasoning_engine",

    # ========================================
    # RESIDUAL REPAIR
    # ========================================

    "ResidualReasoningEngine",

    "residual_reasoning_engine",

    "SpatialResidualRepair",

    "spatial_residual_repair",

    "ObjectResidualRepair",

    "object_residual_repair",

    "CounterfactualRepairEngine",

    "counterfactual_repair_engine",

    "ReasoningGraphReportBuilder",

    "reasoning_graph_report_builder",
]
