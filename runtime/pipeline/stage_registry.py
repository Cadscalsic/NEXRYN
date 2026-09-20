"""Registry and execution modes for modular pipeline stages."""

from __future__ import annotations

from collections import OrderedDict

from .base_stage import BaseStage


FAST_MODE = [
    "task_loading",
    "object_detection",
    "inference",
    "evaluation",
    "shutdown",
]

ADAPTIVE_MODE = [
    "task_loading",
    "preprocessing",
    "object_detection",
    "inference",
    "transformation",
    "evaluation",
    "governance",
    "learning",
    "reporting",
    "shutdown",
]


class StageRegistry:
    def __init__(self) -> None:
        self._stages: OrderedDict[str, BaseStage] = OrderedDict()
        self._enabled: dict[str, bool] = {}

    def register(self, stage: BaseStage) -> BaseStage:
        self._stages[stage.name] = stage
        self._enabled.setdefault(stage.name, True)
        return stage

    def enable(self, stage_name: str) -> None:
        self._enabled[stage_name] = True

    def disable(self, stage_name: str) -> None:
        self._enabled[stage_name] = False

    def stages_for_mode(self, mode: str = "adaptive") -> list[BaseStage]:
        names = FAST_MODE if str(mode).lower() == "fast" else ADAPTIVE_MODE
        return [
            self._stages[name]
            for name in names
            if name in self._stages and self._enabled.get(name, True)
        ]

    def registered_stage_names(self) -> list[str]:
        return list(self._stages.keys())


__all__ = ["ADAPTIVE_MODE", "FAST_MODE", "StageRegistry"]
