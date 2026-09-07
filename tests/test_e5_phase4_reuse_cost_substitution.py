from copy import deepcopy

from tests.test_e5_phase3b_post_repair_quality_efficiency import (
    _condition,
    _source_experience_for,
)


def _decompose(condition):
    reuse = condition["reuse"]["experience_reuse_report"]
    behavior = condition["behavior"]
    production = condition["production"]
    return {
        "C_retrieval": int(reuse.get("retrieval_attempts", 0) or 0),
        "C_reuse_materialization": len(behavior["synthesis_actions"]),
        "C_candidate_generation": behavior["candidate_count"],
        "C_search": "UNAVAILABLE",
        "C_synthesis": len(behavior["synthesis_actions"]),
        "C_repair": 0,
        "C_arena": "UNAVAILABLE",
        "C_validation": (
            1 if production.get("execution_state") == "PRODUCTION_EXECUTED" else 0
        ),
        "C_execution": production.get("result", {}).get("operation_call_count", 0),
        "C_reporting_if_in_scope": "UNAVAILABLE",
        "C_total_realized_operation_units": condition["cost"][
            "realized_operation_units"
        ],
        "wall_time": condition["cost"]["wall_time"],
        "active_compute_time": condition["cost"]["active_compute_time"],
    }


def _delta(left, right, key):
    if isinstance(left[key], (int, float)) and isinstance(right[key], (int, float)):
        return right[key] - left[key]
    return "UNAVAILABLE"


def test_phase4_reuse_is_additive_without_safe_substitution_path(tmp_path):
    _, _, experience = _source_experience_for(tmp_path / "source", 1, 2)
    control = _condition(tmp_path / "control", "phase4_control", 1, 2)
    treatment = _condition(
        tmp_path / "treatment",
        "phase4_treatment",
        1,
        2,
        experience=experience,
    )
    removal = _condition(tmp_path / "removal", "phase4_removal", 1, 2)

    cost_a = _decompose(control)
    cost_b = _decompose(treatment)

    assert treatment["quality"]["exact_success"] is True
    assert control["quality"]["exact_success"] is False
    assert removal["quality"] == control["quality"]
    assert treatment["reuse"]["skip_redundant_reasoning"] is True
    assert treatment["reuse"]["experience_reuse_report"][
        "executable_reuse_available"
    ] is True
    assert treatment["behavior"]["selected_candidate"] == "COMPOSED_FROM_EXPERIENCE"
    assert cost_b["C_total_realized_operation_units"] > cost_a[
        "C_total_realized_operation_units"
    ]
    assert cost_b["C_candidate_generation"] > cost_a["C_candidate_generation"]
    assert cost_b["C_execution"] > cost_a["C_execution"]


def test_phase4_multi_case_cost_decomposition_shows_no_l5(tmp_path):
    cases = [(1, 2), (1, 3), (2, 4)]
    rows = []
    for source_color, target_color in cases:
        _, _, experience = _source_experience_for(
            tmp_path / f"source_{source_color}_{target_color}",
            source_color,
            target_color,
        )
        for repeat in range(3):
            control = _condition(
                tmp_path / f"control_{source_color}_{target_color}_{repeat}",
                f"phase4_control:{source_color}:{target_color}:{repeat}",
                source_color,
                target_color,
            )
            treatment = _condition(
                tmp_path / f"treatment_{source_color}_{target_color}_{repeat}",
                f"phase4_treatment:{source_color}:{target_color}:{repeat}",
                source_color,
                target_color,
                experience=experience,
            )
            cost_a = _decompose(control)
            cost_b = _decompose(treatment)
            rows.append((control, treatment, cost_a, cost_b))

            assert treatment["quality"]["exact_success"] is True
            assert treatment["quality"]["accuracy"] > control["quality"]["accuracy"]
            assert cost_b["C_total_realized_operation_units"] > cost_a[
                "C_total_realized_operation_units"
            ]
            assert _delta(cost_a, cost_b, "C_retrieval") == 0
            assert _delta(cost_a, cost_b, "C_reuse_materialization") == 1
            assert _delta(cost_a, cost_b, "C_candidate_generation") == 2
            assert _delta(cost_a, cost_b, "C_execution") == 1

    assert len(rows) == 9
    assert all(item[1]["quality"]["exact_success"] for item in rows)
    assert all(
        item[3]["C_total_realized_operation_units"]
        > item[2]["C_total_realized_operation_units"]
        for item in rows
    )


def test_phase4_warm_null_conflict_and_failure_cost_controls(tmp_path):
    _, _, experience = _source_experience_for(tmp_path / "source_1_2", 1, 2)
    cold = _condition(tmp_path / "cold", "phase4_cold", 1, 2)
    warm = _condition(tmp_path / "warm", "phase4_warm", 1, 2)
    assert warm["quality"] == cold["quality"]
    assert warm["behavior"] == cold["behavior"]

    unrelated = deepcopy(experience)
    unrelated["experience_id"] = "phase4_translate_placebo"
    unrelated["winner_hypothesis"]["type"] = "translate"
    unrelated["winner_hypothesis"]["operation"] = "translate"
    unrelated["winner_hypothesis"]["parameters"] = {"vector": [1, 0]}
    unrelated["winner_hypothesis"]["executable_payload"] = {
        "operation": "translate",
        "steps": [
            {
                "operation": "translate",
                "parameters": {"vector": [1, 0]},
                "parameter_provenance": {"vector": "ORIGINAL_EXECUTION"},
            }
        ],
        "execution_authority": "NONE",
        "reusable_execution_authority": False,
    }
    unrelated["semantic_graph"]["concept_nodes"] = [{"concept": "translate"}]
    unrelated["execution_plan"]["nodes"] = [{"operation": "translate"}]
    unrelated["program"]["steps"] = [
        {
            "operation": "translate",
            "parameters": {"vector": [1, 0]},
            "parameter_provenance": {"vector": "ORIGINAL_EXECUTION"},
        }
    ]
    null = _condition(tmp_path / "null", "phase4_null", 1, 2, experience=unrelated)
    assert null["quality"]["exact_success"] is False
    assert null["behavior"]["execution_operation"] != "replace_color"

    conflict = _condition(
        tmp_path / "conflict",
        "phase4_conflict",
        1,
        3,
        experience=experience,
    )
    assert conflict["production"]["real_execution_performed"] is True
    assert conflict["quality"]["output_grid"] == [[2]]
    assert conflict["quality"]["exact_success"] is False
    assert conflict["cost"]["realized_operation_units"] > cold["cost"][
        "realized_operation_units"
    ]

    failure = deepcopy(experience)
    failure["experience_id"] = "phase4_failure_parameterized_experience"
    failure["evaluation_result"]["success"] = False
    failure["performance_score"] = 0.0
    failure["success_rate"] = 0.0
    failure_run = _condition(
        tmp_path / "failure",
        "phase4_failure",
        1,
        2,
        experience=failure,
    )
    assert failure_run["behavior"]["selected_candidate"] == "COMPOSED_FROM_EXPERIENCE"
    assert failure_run["cost"]["realized_operation_units"] > cold["cost"][
        "realized_operation_units"
    ]
    assert failure["execution_authority"] == "NONE"
