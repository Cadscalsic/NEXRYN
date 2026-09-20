"""Detect support surfaces and stable landing zones."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import numpy as np

from runtime.object_motion.contracts import SupportSurface


class SupportSurfaceDetector:
    def detect(self, grid: Any, objects: list[dict] | None = None) -> list[dict]:
        array = np.array(grid)
        if array.ndim != 2 or array.size == 0:
            return []
        surfaces = []
        for obj in objects or []:
            surface = self._surface_from_object(obj)
            if surface is not None:
                surfaces.append(asdict(surface))
        if surfaces:
            return surfaces[: self._max_surfaces()]
        for row_index, row in enumerate(array):
            colors = [int(value) for value in np.unique(row) if int(value) != 0]
            for color in colors:
                cols = np.argwhere(row == color).flatten().tolist()
                runs = self._runs(cols)
                for run in runs:
                    if len(run) >= max(2, array.shape[1] // 3):
                        surfaces.append(asdict(SupportSurface(
                            object_id=f"surface_{len(surfaces) + 1}",
                            row=row_index,
                            width=len(run),
                            stability_score=min(1.0, len(run) / max(array.shape[1], 1)),
                            support_type="support_surface",
                            color=color,
                            columns=run,
                        )))
        return surfaces[: self._max_surfaces()]

    def _surface_from_object(self, obj: dict) -> SupportSurface | None:
        bbox = obj.get("bbox", obj.get("bounding_box", {}))
        width = int(bbox.get("width", 0) or 0)
        height = int(bbox.get("height", 0) or 0)
        row = int(bbox.get("min_row", bbox.get("max_row", 0)) or 0)
        cells = obj.get("cells", []) or []
        if height <= 1 and width >= 2:
            return SupportSurface(
                object_id=str(obj.get("id", obj.get("object_id", ""))),
                row=row,
                width=width,
                stability_score=min(1.0, width / max(width, 1)),
                color=obj.get("color"),
                columns=sorted({int(cell[1]) for cell in cells if len(cell) >= 2}),
                support_type="support_surface",
            )
        return None

    def _max_surfaces(self) -> int:
        from runtime.object_motion.motion_budget_controller import MAX_SUPPORT_SURFACES

        return MAX_SUPPORT_SURFACES

    def _runs(self, cols: list[int]) -> list[list[int]]:
        if not cols:
            return []
        cols = sorted(cols)
        runs = [[cols[0]]]
        for col in cols[1:]:
            if col == runs[-1][-1] + 1:
                runs[-1].append(col)
            else:
                runs.append([col])
        return runs


support_surface_detector = SupportSurfaceDetector()


__all__ = [
    "SupportSurface",
    "SupportSurfaceDetector",
    "support_surface_detector",
]
