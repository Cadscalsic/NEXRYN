import json
import os
import subprocess
import sys
import textwrap

import pytest

from runtime.spatial.transformation_localization_engine import (
    TransformationLocalizationEngine,
)


def _read_events(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_localization_telemetry_emits_nested_owner_events(tmp_path, monkeypatch):
    path = tmp_path / "localization.jsonl"
    monkeypatch.setenv("NEXRYN_LOCALIZATION_TELEMETRY_PATH", str(path))
    monkeypatch.setenv("NEXRYN_LOCALIZATION_TELEMETRY_TASK_ID", "unit_task")

    engine = TransformationLocalizationEngine()
    result = engine.localize_program(
        [[1, 0], [0, 0]],
        [[1, 1], [0, 0]],
        {"steps": [{"operation": "duplicate_object", "parameters": {}}]},
    )

    assert result["system"] == "transformation_localization_engine"
    events = _read_events(path)
    names = [(event["subcall_name"], event["phase"]) for event in events]
    assert ("localize_program", "ENTER") in names
    assert ("placement_reasoning", "ENTER") in names
    assert ("placement_reasoning", "EXIT") in names
    assert ("object_tracker_track", "ENTER") in names
    assert ("object_tracker_pair_scoring", "ENTER") in names
    assert all(event["authority"] == "OBSERVATION_ONLY" for event in events)
    assert all(event["behavioral_authority"] == "NONE" for event in events)


def test_localization_telemetry_parent_child_lineage(tmp_path, monkeypatch):
    path = tmp_path / "localization.jsonl"
    monkeypatch.setenv("NEXRYN_LOCALIZATION_TELEMETRY_PATH", str(path))

    engine = TransformationLocalizationEngine()
    engine.localize_program(
        [[1, 0], [0, 0]],
        [[1, 1], [0, 0]],
        {"steps": [{"operation": "duplicate_object", "parameters": {}}]},
    )

    events = _read_events(path)
    root = next(event for event in events if event["subcall_name"] == "localize_program")
    middle = next(
        event for event in events if event["subcall_name"] == "localize_from_grids"
    )
    child = next(event for event in events if event["subcall_name"] == "placement_reasoning")
    graph = next(
        event for event in events if event["subcall_name"] == "placement_graph_reasoning"
    )
    grandchild = next(event for event in events if event["subcall_name"] == "object_tracker_track")
    assert middle["parent_call_id"] == root["call_id"]
    assert child["parent_call_id"] == middle["call_id"]
    assert graph["parent_call_id"] == child["call_id"]
    assert grandchild["parent_call_id"] == graph["call_id"]


def test_localization_telemetry_survives_killed_inner_helper(tmp_path):
    script = tmp_path / "run_hanging_localization.py"
    trace = tmp_path / "localization.jsonl"
    script.write_text(
        textwrap.dedent(
            f"""
            import os
            import time

            from runtime.spatial.transformation_localization_engine import (
                TransformationLocalizationEngine,
            )

            class HangingPlacementReasoner:
                def reason(self, *args, **kwargs):
                    while True:
                        time.sleep(0.1)

            os.environ["NEXRYN_LOCALIZATION_TELEMETRY_PATH"] = {str(trace)!r}
            engine = TransformationLocalizationEngine(
                placement_reasoner=HangingPlacementReasoner()
            )
            engine.localize_program(
                [[1, 0], [0, 0]],
                [[1, 1], [0, 0]],
                {{"steps": [{{"operation": "duplicate_object", "parameters": {{}}}}]}},
            )
            """
        ),
        encoding="utf-8",
    )

    with pytest.raises(subprocess.TimeoutExpired):
        env = dict(os.environ)
        env["PYTHONPATH"] = os.getcwd()
        subprocess.run(
            [sys.executable, str(script)],
            cwd=os.getcwd(),
            env=env,
            timeout=2,
            check=True,
        )

    events = _read_events(trace)
    assert events[-1]["phase"] == "ENTER"
    assert events[-1]["subcall_name"] == "placement_reasoning"


def test_localization_telemetry_enabled_disabled_parity(tmp_path, monkeypatch):
    engine = TransformationLocalizationEngine()
    args = (
        [[1, 0], [0, 0]],
        [[1, 1], [0, 0]],
        {"steps": [{"operation": "duplicate_object", "parameters": {}}]},
    )
    monkeypatch.delenv("NEXRYN_LOCALIZATION_TELEMETRY_PATH", raising=False)
    off = engine.localize_program(*args)

    monkeypatch.setenv(
        "NEXRYN_LOCALIZATION_TELEMETRY_PATH",
        str(tmp_path / "localization.jsonl"),
    )
    on = engine.localize_program(*args)

    assert on == off


def test_localization_telemetry_excludes_grid_values(tmp_path, monkeypatch):
    path = tmp_path / "localization.jsonl"
    monkeypatch.setenv("NEXRYN_LOCALIZATION_TELEMETRY_PATH", str(path))

    engine = TransformationLocalizationEngine()
    engine.localize_program(
        [[7, 0], [0, 0]],
        [[7, 9], [0, 0]],
        {"steps": [{"operation": "duplicate_object", "parameters": {}}]},
    )

    text = path.read_text(encoding="utf-8")
    assert '"input_grid"' not in text
    assert '"target_grid"' not in text
    assert "[[7" not in text
    assert '"input_grid_shape"' in text
    assert '"target_grid_shape"' in text
