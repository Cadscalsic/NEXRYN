"""Modular, stage-oriented runtime pipeline architecture."""

class _LegacyPipelineProxy:
    def _target(self):
        from .legacy_pipeline import pipeline

        return pipeline

    def __getattr__(self, name):
        return getattr(self._target(), name)

    def run(self, *args, **kwargs):
        return self._target().run(*args, **kwargs)


pipeline = _LegacyPipelineProxy()


def __getattr__(name):
    if name == "AdaptiveCognitivePipeline":
        from .legacy_pipeline import AdaptiveCognitivePipeline

        return AdaptiveCognitivePipeline
    if name == "BaseStage":
        from .base_stage import BaseStage

        return BaseStage
    if name == "PipelineContext":
        from .pipeline_context import PipelineContext

        return PipelineContext
    if name == "StageResult":
        from .stage_result import StageResult

        return StageResult
    if name in {
        "ModularPipelineRunner",
        "default_stage_registry",
        "run_modular_pipeline",
        "run_pipeline",
    }:
        from . import pipeline_runner

        return getattr(pipeline_runner, name)
    if name in {"ADAPTIVE_MODE", "FAST_MODE", "StageRegistry"}:
        from . import stage_registry

        return getattr(stage_registry, name)
    raise AttributeError(name)


__all__ = [
    "ADAPTIVE_MODE",
    "AdaptiveCognitivePipeline",
    "FAST_MODE",
    "BaseStage",
    "ModularPipelineRunner",
    "PipelineContext",
    "StageRegistry",
    "StageResult",
    "default_stage_registry",
    "pipeline",
    "run_modular_pipeline",
    "run_pipeline",
]
