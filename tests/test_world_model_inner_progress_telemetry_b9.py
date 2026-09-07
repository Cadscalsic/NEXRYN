import json
import os
import subprocess
import sys
import textwrap

import numpy as np

from runtime.world.world_model import WorldModelEngine


def _read_events(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _run_prediction():
    return WorldModelEngine().anticipate_program(
        input_grid=np.array([[1, 0], [0, 0]]),
        target_grid=np.array([[0, 1], [0, 0]]),
        synthesized_program={
            "step_count": 1,
            "steps": [{
                "operation": "translate_right",
                "parameters": {"steps": 1},
            }],
        },
    )


def test_world_model_telemetry_emits_enter_exit_pairs(tmp_path, monkeypatch):
    telemetry_path = tmp_path / "world_model.jsonl"
    monkeypatch.setenv("NEXRYN_WORLD_MODEL_TELEMETRY_PATH", str(telemetry_path))
    monkeypatch.setenv("NEXRYN_WORLD_MODEL_TELEMETRY_TASK_ID", "b9_unit_task")

    _run_prediction()

    events = _read_events(telemetry_path)
    phases_by_subcall = {}
    for event in events:
        phases_by_subcall.setdefault(event["subcall_name"], set()).add(
            event["phase"]
        )

    assert phases_by_subcall["anticipate_program"] == {"ENTER", "EXIT"}
    assert phases_by_subcall["object_localization"] == {"ENTER", "EXIT"}
    assert phases_by_subcall["object_motion"] == {"ENTER", "EXIT"}
    assert phases_by_subcall["simulation"] == {"ENTER", "EXIT"}
    assert phases_by_subcall["prediction_evaluation"] == {"ENTER", "EXIT"}
    assert phases_by_subcall["confidence_scoring"] == {"ENTER", "EXIT"}


def test_world_model_telemetry_preserves_parent_child_lineage(
    tmp_path,
    monkeypatch,
):
    telemetry_path = tmp_path / "world_model.jsonl"
    monkeypatch.setenv("NEXRYN_WORLD_MODEL_TELEMETRY_PATH", str(telemetry_path))

    _run_prediction()

    events = _read_events(telemetry_path)
    root_enter = next(
        event
        for event in events
        if event["subcall_name"] == "anticipate_program"
        and event["phase"] == "ENTER"
    )
    child_enters = [
        event
        for event in events
        if event["phase"] == "ENTER"
        and event["subcall_name"] != "anticipate_program"
    ]

    assert child_enters
    assert all(
        event["parent_call_id"] == root_enter["call_id"]
        for event in child_enters
    )


def test_world_model_telemetry_survives_killed_worker(tmp_path):
    telemetry_path = tmp_path / "killed.jsonl"
    script = textwrap.dedent(
        f"""
        import os
        import sys
        import time
        import numpy as np
        sys.path.insert(0, {os.getcwd()!r})
        from runtime.world.world_model import WorldModelEngine

        class SlowLocalization:
            def localize_program(self, *args, **kwargs):
                time.sleep(5)
                return {{}}

        os.environ["NEXRYN_WORLD_MODEL_TELEMETRY_PATH"] = {str(telemetry_path)!r}
        engine = WorldModelEngine()
        engine.transformation_localization_engine = SlowLocalization()
        engine.anticipate_program(
            input_grid=np.zeros((2, 2), dtype=int),
            target_grid=np.zeros((2, 2), dtype=int),
            synthesized_program={{"steps": []}},
        )
        """
    )

    try:
        subprocess.run(
            [sys.executable, "-c", script],
            cwd=os.getcwd(),
            timeout=3,
            check=False,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired:
        pass

    events = _read_events(telemetry_path)
    assert events[-1]["subcall_name"] == "object_localization"
    assert events[-1]["phase"] == "ENTER"


def test_world_model_telemetry_enabled_disabled_result_parity(
    tmp_path,
    monkeypatch,
):
    without_telemetry = _run_prediction()
    telemetry_path = tmp_path / "parity.jsonl"
    monkeypatch.setenv("NEXRYN_WORLD_MODEL_TELEMETRY_PATH", str(telemetry_path))

    with_telemetry = _run_prediction()

    assert with_telemetry["prediction_report"] == without_telemetry[
        "prediction_report"
    ]
    assert with_telemetry["accepted"] == without_telemetry["accepted"]
    assert with_telemetry["localized_synthesized_program"] == without_telemetry[
        "localized_synthesized_program"
    ]


def test_world_model_telemetry_excludes_hidden_grid_values(tmp_path, monkeypatch):
    telemetry_path = tmp_path / "hidden.jsonl"
    monkeypatch.setenv("NEXRYN_WORLD_MODEL_TELEMETRY_PATH", str(telemetry_path))

    WorldModelEngine().anticipate_program(
        input_grid=np.array([[1, 2], [3, 4]]),
        target_grid=np.array([[9, 8], [7, 6]]),
        synthesized_program={"steps": []},
    )

    text = telemetry_path.read_text(encoding="utf-8")
    assert "[[9, 8], [7, 6]]" not in text
    assert '"target_shape": [2, 2]' in text
