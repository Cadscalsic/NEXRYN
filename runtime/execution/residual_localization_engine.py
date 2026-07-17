from __future__ import annotations

from typing import Any


class ResidualLocalizationEngine:
    """Locate prediction residuals and infer missing execution operations."""

    def localize(
        self,
        predicted_output: list[list[int]] | None,
        target_grid: list[list[int]] | None,
        *,
        program: dict[str, Any] | None = None,
        grounding_report: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        predicted = self._grid(predicted_output)
        target = self._grid(target_grid)
        residual_cells = []
        max_rows = max(len(predicted), len(target))
        max_cols = max(
            max((len(row) for row in predicted), default=0),
            max((len(row) for row in target), default=0),
        )
        for row in range(max_rows):
            for col in range(max_cols):
                predicted_value = self._cell(predicted, row, col)
                target_value = self._cell(target, row, col)
                if predicted_value != target_value:
                    residual_cells.append({
                        "row": row,
                        "col": col,
                        "predicted": predicted_value,
                        "target": target_value,
                    })
        residual_regions = self._regions(residual_cells)
        missing = self._missing_primitives(residual_cells)
        total_cells = max_rows * max_cols if max_rows and max_cols else 0
        accuracy = 1.0 if total_cells == 0 else round((total_cells - len(residual_cells)) / total_cells, 6)
        return {
            "residual_cells": residual_cells,
            "residual_objects": self._residual_objects(residual_cells, grounding_report),
            "residual_regions": residual_regions,
            "residual_operations": self._residual_operations(missing),
            "missing_primitives": missing,
            "residual_count": len(residual_cells),
            "prediction_accuracy": accuracy,
            "failure_explanation": self._explanation(residual_cells, missing),
            "localized_execution_success": 1 if residual_cells else 0,
            "residual_localization_operational": True,
        }

    def _grid(self, grid: Any) -> list[list[int]]:
        return [list(row) for row in grid] if isinstance(grid, list) else []

    def _cell(self, grid: list[list[int]], row: int, col: int) -> int | None:
        if row >= len(grid) or col >= len(grid[row]):
            return None
        return grid[row][col]

    def _regions(self, cells: list[dict[str, Any]]) -> list[dict[str, int]]:
        if not cells:
            return []
        return [{
            "min_row": min(cell["row"] for cell in cells),
            "max_row": max(cell["row"] for cell in cells),
            "min_col": min(cell["col"] for cell in cells),
            "max_col": max(cell["col"] for cell in cells),
            "cell_count": len(cells),
        }]

    def _missing_primitives(self, cells: list[dict[str, Any]]) -> list[str]:
        if not cells:
            return []
        colors_changed = any(
            cell.get("predicted") not in {None, 0}
            and cell.get("target") not in {None, 0}
            and cell.get("predicted") != cell.get("target")
            for cell in cells
        )
        additions = any(cell.get("predicted") in {None, 0} and cell.get("target") not in {None, 0} for cell in cells)
        removals = any(cell.get("predicted") not in {None, 0} and cell.get("target") in {None, 0} for cell in cells)
        missing = []
        if colors_changed:
            missing.append("recolor")
        if additions:
            missing.append("propagate")
        if removals:
            missing.append("split")
        return missing or ["compose"]

    def _residual_operations(self, missing: list[str]) -> list[str]:
        mapping = {
            "recolor": "localized_recolor",
            "propagate": "localized_growth",
            "split": "localized_removal",
            "compose": "localized_composition",
        }
        return [mapping.get(item, item) for item in missing]

    def _residual_objects(
        self,
        cells: list[dict[str, Any]],
        grounding_report: dict[str, Any] | None,
    ) -> list[str]:
        grounding = grounding_report if isinstance(grounding_report, dict) else {}
        objects = grounding.get("candidate_objects") if isinstance(grounding.get("candidate_objects"), list) else []
        residual = []
        residual_points = {(cell["row"], cell["col"]) for cell in cells}
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            object_cells = {(cell[0], cell[1]) for cell in obj.get("cells", []) if isinstance(cell, list) and len(cell) == 2}
            if object_cells & residual_points:
                residual.append(obj.get("object_id"))
        return [item for item in residual if item]

    def _explanation(self, cells: list[dict[str, Any]], missing: list[str]) -> str:
        if not cells:
            return "prediction matches target"
        return f"{len(cells)} residual cell(s) remain; missing primitive(s): {', '.join(missing)}"


residual_localization_engine = ResidualLocalizationEngine()


__all__ = ["ResidualLocalizationEngine", "residual_localization_engine"]
