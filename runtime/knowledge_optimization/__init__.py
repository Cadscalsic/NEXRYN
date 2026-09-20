"""Evidence saturation, contradiction resolution, and knowledge reuse optimization."""

from runtime.knowledge_optimization.adaptive_validation_thresholds import (
    AdaptiveValidationThresholds,
    adaptive_validation_thresholds,
)
from runtime.knowledge_optimization.concept_commit_engine import (
    ConceptCommitEngine,
    concept_commit_engine,
)
from runtime.knowledge_optimization.confidence_plateau_detector import (
    ConfidencePlateauDetector,
    confidence_plateau_detector,
)
from runtime.knowledge_optimization.contradiction_ledger import (
    EVIDENCE_WEIGHT,
    ContradictionLedger,
    EvidenceRecord,
    contradiction_ledger,
)
from runtime.knowledge_optimization.evidence_saturation_controller import (
    MAX_EVIDENCE_COLLECTION_TIME,
    MAX_SUPPORT_SAMPLES,
    MAX_VALIDATION_CYCLES,
    SATURATION_DECISIONS,
    EvidenceSaturationController,
    evidence_saturation_controller,
)
from runtime.knowledge_optimization.knowledge_optimization_reporter import (
    KnowledgeOptimizationReporter,
    knowledge_optimization_reporter,
)
from runtime.knowledge_optimization.knowledge_reuse_gate import (
    KnowledgeReuseGate,
    knowledge_reuse_gate,
)
from runtime.knowledge_optimization.memory_confidence_tracker import (
    MemoryConfidenceTracker,
    memory_confidence_tracker,
)
from runtime.knowledge_optimization.strategy_reuse_engine import (
    SEARCH_ORDER,
    KnowledgeStrategyReuseEngine,
    strategy_reuse_engine,
)


__all__ = [
    "AdaptiveValidationThresholds",
    "ConceptCommitEngine",
    "ConfidencePlateauDetector",
    "ContradictionLedger",
    "EVIDENCE_WEIGHT",
    "EvidenceRecord",
    "EvidenceSaturationController",
    "KnowledgeOptimizationReporter",
    "KnowledgeReuseGate",
    "KnowledgeStrategyReuseEngine",
    "MAX_EVIDENCE_COLLECTION_TIME",
    "MAX_SUPPORT_SAMPLES",
    "MAX_VALIDATION_CYCLES",
    "MemoryConfidenceTracker",
    "SATURATION_DECISIONS",
    "SEARCH_ORDER",
    "adaptive_validation_thresholds",
    "concept_commit_engine",
    "confidence_plateau_detector",
    "contradiction_ledger",
    "evidence_saturation_controller",
    "knowledge_optimization_reporter",
    "knowledge_reuse_gate",
    "memory_confidence_tracker",
    "strategy_reuse_engine",
]
