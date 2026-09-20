"""Canonical runtime pipeline namespace.

`runtime.pipeline` is owned by this package. Normal production execution is
delegated to `runtime.pipeline.legacy_pipeline.AdaptiveCognitivePipeline`
through the `pipeline` compatibility proxy below; the modular runner remains an
explicit alternate API and does not silently replace production behavior.
"""

PIPELINE_NAMESPACE_STATE = "PACKAGE_OWNS_NAMESPACE"
CANONICAL_PRODUCTION_PIPELINE = (
    "runtime.pipeline.legacy_pipeline.AdaptiveCognitivePipeline"
)
CANONICAL_ENTRY_SYMBOL = "pipeline"
CANONICAL_SOURCE_FILE = "runtime/pipeline/legacy_pipeline.py"
COMPATIBILITY_SURFACES = ("runtime.pipeline.pipeline",)
ALTERNATE_PIPELINE_SURFACES = (
    "runtime.pipeline.pipeline_runner.ModularPipelineRunner",
    "runtime.pipeline.pipeline_runner.run_modular_pipeline",
)

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
    "ALTERNATE_PIPELINE_SURFACES",
    "CANONICAL_ENTRY_SYMBOL",
    "CANONICAL_PRODUCTION_PIPELINE",
    "CANONICAL_SOURCE_FILE",
    "COMPATIBILITY_SURFACES",
    "FAST_MODE",
    "BaseStage",
    "ModularPipelineRunner",
    "PIPELINE_NAMESPACE_STATE",
    "PipelineContext",
    "StageRegistry",
    "StageResult",
    "default_stage_registry",
    "pipeline",
    "run_modular_pipeline",
    "run_pipeline",
]
