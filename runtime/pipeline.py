"""Compatibility wrapper for the modular pipeline package."""

from __future__ import annotations

from pathlib import Path


__path__ = [str(Path(__file__).with_suffix(""))]

from runtime.pipeline.pipeline_runner import (  # noqa: E402
    ModularPipelineRunner,
    run_modular_pipeline,
    run_pipeline,
)


class _LegacyPipelineProxy:
    def _target(self):
        from runtime.pipeline.legacy_pipeline import pipeline

        return pipeline

    def __getattr__(self, name):
        return getattr(self._target(), name)

    def run(self, *args, **kwargs):
        return self._target().run(*args, **kwargs)


pipeline = _LegacyPipelineProxy()


def __getattr__(name):
    if name == "AdaptiveCognitivePipeline":
        from runtime.pipeline.legacy_pipeline import AdaptiveCognitivePipeline

        return AdaptiveCognitivePipeline
    raise AttributeError(name)


__all__ = [
    "AdaptiveCognitivePipeline",
    "ModularPipelineRunner",
    "pipeline",
    "run_modular_pipeline",
    "run_pipeline",
]
