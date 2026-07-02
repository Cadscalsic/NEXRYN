import pytest

from runtime.context.context_integrity_guard import ContextIntegrityGuard
from runtime.stages.grid_analysis import grid_analysis_stage


class _GridData:
    def __init__(self, shape):
        self.shape = shape


class _FakeGrid:
    def __init__(self, shape, colors):
        self.grid = _GridData(shape)
        self._colors = colors

    def grid_summary(self):
        return {
            "shape": self.grid.shape,
            "colors": self._colors,
        }


def test_grid_analysis_repairs_grids_from_train_example():
    input_grid = _FakeGrid((2, 2), [0, 1])
    output_grid = _FakeGrid((2, 2), [0, 2])
    context = {
        "task_path": "task_041.json",
        "task_loaded": True,
        "train_example": {
            "input": input_grid,
            "output": output_grid,
        },
    }

    result = grid_analysis_stage(context)
    report = result["runtime_context_integrity_report"]

    assert result["input_grid"] is input_grid
    assert result["output_grid"] is output_grid
    assert result["grid_analysis_complete"] is True
    assert report["integrity_ok"] is True
    assert report["repairs"] == [
        "input_grid_from_train_example",
        "output_grid_from_train_example",
    ]
    assert result["grid_analysis_stage_report"][
        "runtime_context_integrity_report"
    ]["integrity_ok"] is True


def test_context_integrity_guard_reports_missing_grid_trace():
    context = {
        "task_path": "task_041.json",
        "task_loaded": True,
    }

    with pytest.raises(ValueError, match="Missing runtime context fields"):
        ContextIntegrityGuard.require(
            context,
            "grid_analysis",
            ("input_grid", "output_grid"),
        )

    report = context["runtime_context_integrity_report"]

    assert report["integrity_ok"] is False
    assert report["missing_fields"] == [
        "input_grid",
        "output_grid",
    ]
    assert report["input_grid_status"]["present"] is False
    assert report["output_grid_status"]["present"] is False
