"""Observation-only localization progress telemetry."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import numpy as np


def telemetry_path() -> Path | None:
    path = os.environ.get("NEXRYN_LOCALIZATION_TELEMETRY_PATH")
    return Path(path) if path else None


def grid_shape(grid: Any) -> list[int] | None:
    if grid is None:
        return None
    if hasattr(grid, "grid"):
        grid = grid.grid
    try:
        array = np.array(grid)
    except Exception:
        return None
    if array.ndim != 2:
        return None
    return [int(array.shape[0]), int(array.shape[1])]


def stable_id(value: Any) -> str:
    text = json.dumps(
        safe_value(value),
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def safe_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return {"ndarray_shape": [int(item) for item in value.shape]}
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, dict):
        blocked = {
            "input_grid",
            "output_grid",
            "target_grid",
            "expected_grid",
            "predicted_grid",
            "predicted_output",
            "hidden_test_outputs",
        }
        return {
            str(key): safe_value(item)
            for key, item in value.items()
            if key not in blocked
        }
    if isinstance(value, (list, tuple)):
        if value and all(isinstance(row, (list, tuple, np.ndarray)) for row in value):
            shape = grid_shape(value)
            if shape is not None:
                return {"grid_shape": shape}
        return [safe_value(item) for item in list(value)[:20]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return type(value).__name__


def emit(
    *,
    event_type: str = "localization_inner_progress",
    phase: str,
    subcall_name: str,
    call_id: str,
    parent_call_id: str | None = None,
    started_at: float | None = None,
    parent_started_at: float | None = None,
    **fields: Any,
) -> None:
    path = telemetry_path()
    if path is None:
        return

    now = time.perf_counter()
    event = {
        "system": "transformation_localization_inner_progress_telemetry",
        "authority": "OBSERVATION_ONLY",
        "behavioral_authority": "NONE",
        "event_type": event_type,
        "phase": phase,
        "task_id": os.environ.get("NEXRYN_LOCALIZATION_TELEMETRY_TASK_ID")
        or os.environ.get("NEXRYN_WORLD_MODEL_TELEMETRY_TASK_ID"),
        "call_id": call_id,
        "parent_call_id": parent_call_id,
        "subcall_name": subcall_name,
        "monotonic_timestamp": round(now, 6),
        "elapsed_total_ms": (
            round((now - started_at) * 1000, 3)
            if started_at is not None
            else 0.0
        ),
        "elapsed_parent_ms": (
            round((now - parent_started_at) * 1000, 3)
            if parent_started_at is not None
            else 0.0
        ),
    }
    event.update({key: safe_value(value) for key, value in fields.items()})

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True, ensure_ascii=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
