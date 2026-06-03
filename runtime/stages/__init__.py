# ============================================
# NEXRYN STAGE IMPORTS
# ============================================

# ============================================
# TASK LOADING
# ============================================

from runtime.stages.task_loading import (
    task_loading_stage
)

# ============================================
# GRID ANALYSIS
# ============================================

from runtime.stages.grid_analysis import (
    grid_analysis_stage
)

# ============================================
# OBJECT DETECTION
# ============================================

from runtime.stages.object_detection import (
    object_detection_stage
)

# ============================================
# PATTERN & RULE ANALYSIS
# ============================================

from runtime.stages.pattern_rule import (
    pattern_rule_stage
)

# ============================================
# INFERENCE
# ============================================

from runtime.stages.inference import (
    inference_stage
)

# ============================================
# TRANSFORMATION
# ============================================

from runtime.stages.transformation import (
    transformation_stage
)

# ============================================
# EVALUATION
# ============================================

from runtime.stages.evaluation import (
    evaluation_stage
)

# ============================================
# SELF IMPROVEMENT
# ============================================

from runtime.stages.self_improvement import (
    self_improvement_stage
)

# ============================================
# STAGE EXECUTION ORDER
# ============================================

NEXRYN_STAGE_SEQUENCE = [

    # ========================================
    # TASK INITIALIZATION
    # ========================================

    task_loading_stage,

    # ========================================
    # STRUCTURAL ANALYSIS
    # ========================================

    grid_analysis_stage,

    # ========================================
    # OBJECT REASONING
    # ========================================

    object_detection_stage,

    # ========================================
    # PATTERN DISCOVERY
    # ========================================

    pattern_rule_stage,

    # ========================================
    # COGNITIVE INFERENCE
    # ========================================

    inference_stage,

    # ========================================
    # TRANSFORMATION EXECUTION
    # ========================================

    transformation_stage,

    # ========================================
    # REFLECTIVE EVALUATION
    # ========================================

    evaluation_stage,

    # ========================================
    # SELF EVOLUTION
    # ========================================

    self_improvement_stage
]

# ============================================
# STAGE NAME MAPPING
# ============================================

NEXRYN_STAGE_MAP = {

    stage.__name__: stage

    for stage in NEXRYN_STAGE_SEQUENCE
}

# ============================================
# STAGE CATEGORIES
# ============================================

NEXRYN_STAGE_CATEGORIES = {

    "task_loading_stage":
    "initialization",

    "grid_analysis_stage":
    "structural_analysis",

    "object_detection_stage":
    "object_reasoning",

    "pattern_rule_stage":
    "symbolic_analysis",

    "inference_stage":
    "cognitive_reasoning",

    "transformation_stage":
    "execution",

    "evaluation_stage":
    "reflection",

    "self_improvement_stage":
    "self_evolution"
}

# ============================================
# STAGE PRIORITIES
# ============================================

NEXRYN_STAGE_PRIORITIES = {

    "task_loading_stage":
    "critical",

    "grid_analysis_stage":
    "high",

    "object_detection_stage":
    "high",

    "pattern_rule_stage":
    "high",

    "inference_stage":
    "critical",

    "transformation_stage":
    "critical",

    "evaluation_stage":
    "critical",

    "self_improvement_stage":
    "medium"
}

# ============================================
# STAGE GOVERNANCE
# ============================================

NEXRYN_STAGE_GOVERNANCE = {

    "runtime_mode":
    "adaptive_cognitive_execution",

    "governed_execution":
    True,

    "recursive_monitoring":
    True,

    "cognitive_pressure_tracking":
    True,

    "self_improvement_enabled":
    True,

    "world_model_execution":
    True
}