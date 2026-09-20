"""Contracts for object-relative motion reasoning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SupportSurface:
    object_id: str
    row: int
    width: int
    support_type: str
    stability_score: float
    color: int | None = None
    columns: list[int] = field(default_factory=list)


@dataclass
class GravityResult:
    object_id: str
    translation: tuple[int, int]
    final_position: tuple[int, int]
    support_object: str | None
    iterations: int
    final_cells: list[list[int]] = field(default_factory=list)


@dataclass
class CollisionReport:
    collision_detected: bool
    collision_type: str
    collision_location: tuple[int, int] | None
    object_id: str | None = None


@dataclass
class ConstraintProfile:
    movable_objects: list[str]
    fixed_objects: list[str]
    support_objects: list[str]
    obstacles: list[str] = field(default_factory=list)
    anchors: list[str] = field(default_factory=list)


@dataclass
class MotionReport:
    motion_pattern: str
    translation_variance: float
    translation_per_object: dict[str, tuple[int, int]]
    support_count: int
    collision_count: int
    support_surfaces: list[dict[str, Any]] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)

