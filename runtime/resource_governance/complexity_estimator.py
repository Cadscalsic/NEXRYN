"""Lightweight deterministic task complexity estimation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class ComplexityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


def score_to_level(score: float) -> ComplexityLevel:
    if score >= 0.85:
        return ComplexityLevel.EXTREME
    if score >= 0.60:
        return ComplexityLevel.HIGH
    if score >= 0.30:
        return ComplexityLevel.MEDIUM
    return ComplexityLevel.LOW


@dataclass(frozen=True)
class ComplexityEstimate:
    object_complexity: ComplexityLevel
    transformation_complexity: ComplexityLevel
    spatial_complexity: ComplexityLevel
    topology_complexity: ComplexityLevel
    dependency_complexity: ComplexityLevel
    semantic_complexity: ComplexityLevel
    execution_uncertainty: ComplexityLevel
    task_complexity: ComplexityLevel
    scores: Mapping[str, float]

    def as_dict(self) -> dict[str, Any]:
        return {
            "object_complexity": self.object_complexity.value,
            "transformation_complexity": self.transformation_complexity.value,
            "spatial_complexity": self.spatial_complexity.value,
            "topology_complexity": self.topology_complexity.value,
            "dependency_complexity": self.dependency_complexity.value,
            "semantic_complexity": self.semantic_complexity.value,
            "execution_uncertainty": self.execution_uncertainty.value,
            "task_complexity": self.task_complexity.value,
            "scores": dict(self.scores),
        }


class ComplexityEstimator:
    def estimate(self, task: Any) -> ComplexityEstimate:
        text, grid = _task_text_and_grid(task)
        tokens = _tokens(text)
        unique_values = _unique_grid_values(grid)
        object_count = _object_hint_count(task, tokens)

        scores = {
            "object": min(1.0, (object_count + len(unique_values)) / 12.0),
            "transformation": _keyword_score(tokens, {
                "transform",
                "rotate",
                "rotation",
                "scale",
                "scaling",
                "mirror",
                "reflect",
                "translate",
                "move",
                "shift",
                "map",
                "mapping",
                "remap",
                "replace",
            }),
            "spatial": _keyword_score(tokens, {
                "spatial",
                "position",
                "left",
                "right",
                "above",
                "below",
                "inside",
                "outside",
                "adjacent",
                "distance",
                "gravity",
                "fall",
                "drop",
            }),
            "topology": _keyword_score(tokens, {
                "topology",
                "connected",
                "connectivity",
                "enclosed",
                "hole",
                "loop",
                "boundary",
                "region",
                "graph",
            }),
            "dependency": _keyword_score(tokens, {
                "depends",
                "dependency",
                "sequence",
                "chain",
                "causal",
                "because",
                "before",
                "after",
                "if",
            }),
            "semantic": _keyword_score(tokens, {
                "semantic",
                "novel",
                "unknown",
                "ambiguous",
                "concept",
                "meaning",
                "infer",
                "analogy",
            }),
        }
        scores["uncertainty"] = min(
            1.0,
            _keyword_score(tokens, {
                "unknown",
                "ambiguous",
                "uncertain",
                "maybe",
                "possible",
                "hypothesis",
            })
            + (0.15 if not text and grid is None else 0.0),
        )
        scores["task"] = max(scores.values()) if scores else 0.0

        return ComplexityEstimate(
            object_complexity=score_to_level(scores["object"]),
            transformation_complexity=score_to_level(scores["transformation"]),
            spatial_complexity=score_to_level(scores["spatial"]),
            topology_complexity=score_to_level(scores["topology"]),
            dependency_complexity=score_to_level(scores["dependency"]),
            semantic_complexity=score_to_level(scores["semantic"]),
            execution_uncertainty=score_to_level(scores["uncertainty"]),
            task_complexity=score_to_level(scores["task"]),
            scores=scores,
        )


def _task_text_and_grid(task: Any) -> tuple[str, Any]:
    if isinstance(task, Mapping):
        text_parts = [
            str(task.get(key, ""))
            for key in ("description", "prompt", "task", "instruction", "notes")
            if task.get(key)
        ]
        grid = task.get("input_grid") or task.get("grid") or task.get("input")
        return " ".join(text_parts).lower(), grid
    return str(task or "").lower(), None


def _tokens(text: str) -> set[str]:
    normalized = "".join(char if char.isalnum() else " " for char in text.lower())
    return set(normalized.split())


def _keyword_score(tokens: set[str], keywords: set[str]) -> float:
    hits = len(tokens.intersection(keywords))
    return min(1.0, hits / 4.0)


def _unique_grid_values(grid: Any) -> set[Any]:
    values: set[Any] = set()
    if not isinstance(grid, list):
        return values
    for row in grid:
        if isinstance(row, list):
            values.update(row)
        else:
            values.add(row)
    return values


def _object_hint_count(task: Any, tokens: set[str]) -> int:
    if isinstance(task, Mapping):
        objects = task.get("objects") or task.get("detected_objects")
        if isinstance(objects, list):
            return len(objects)
    hints = {"object", "objects", "shape", "shapes", "component", "components"}
    return len(tokens.intersection(hints))


__all__ = [
    "ComplexityEstimate",
    "ComplexityEstimator",
    "ComplexityLevel",
    "score_to_level",
]
