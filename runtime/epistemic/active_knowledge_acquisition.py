from runtime.epistemic.active_knowledge_acquisition_engine import (
    ActiveKnowledgeAcquisitionEngine,
)


class ActiveKnowledgeAcquisition(ActiveKnowledgeAcquisitionEngine):
    """Backward-compatible alias for the active acquisition engine."""

    compatibility_alias = True


__all__ = [
    "ActiveKnowledgeAcquisition",
]
