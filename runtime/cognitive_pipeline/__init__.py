"""Cognitive solver pipeline primitives and report builder."""

from .context import CognitiveContext
from .orchestrator import CognitivePipelineOrchestrator
from .report import build_cognitive_pipeline_report
from .stages import DEFAULT_COGNITIVE_STAGE_IDS, build_default_stages

__all__ = [
    "CognitiveContext",
    "CognitivePipelineOrchestrator",
    "DEFAULT_COGNITIVE_STAGE_IDS",
    "build_cognitive_pipeline_report",
    "build_default_stages",
]
