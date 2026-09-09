import copy

from runtime.experiments.route_order_deconfounding import (
    build_dependency_matrix,
    build_order_design,
    run_route_order_deconfounding_analysis,
)


PRODUCTION_ORDER = [
    "causal_validation",
    "color_mapping",
    "contradiction_checks",
    "dependency_reasoning",
    "identity_governance",
    "object_tracking",
    "process_semantics",
]


def _route(route_id, position, state="NO_OBSERVABLE_CONTRIBUTION"):
    return {
        "route_execution_id": f"{route_id}:{position}",
        "route_position": position,
        "route_id": route_id,
        "executed": True,
        "contribution_state": state,
    }


def _run(condition, task="elite_cognitive_task_03.json", positive=None):
    positive = positive or set()
    routes = [
        _route(route, index, "UNIQUE_USEFUL_CONTRIBUTION" if route in positive else "NO_OBSERVABLE_CONTRIBUTION")
        for index, route in enumerate(condition["marginal_routes"], start=3)
    ]
    return {
        "condition_id": condition["condition_id"],
        "order_id": condition["order_id"],
        "marginal_order": condition["marginal_routes"],
        "per_task": [
            {
                "task_id": task,
                "exact_success": False,
                "accuracy": 0.0,
                "final_score": 0.0,
                "success_state": "FAILED",
            }
        ],
        "route_manifests": [
            {
                "run_id": f"run_{condition['condition_id']}",
                "task_id": task,
                "lineage_continuity_state": "ROUTE_LINEAGE_CONTINUITY_VERIFIED",
                "routes": routes,
            }
        ],
    }


def test_balanced_route_position_coverage():
    design = build_order_design(PRODUCTION_ORDER)
    assert design["production_default_order_changed"] is False
    assert design["experimental_order_disabled_by_default"] is True
    for route, by_position in design["route_position_coverage"].items():
        assert set(by_position.values()) == {1}, route


def test_dependency_matrix_allows_balanced_no_explicit_dependencies():
    matrix = build_dependency_matrix(PRODUCTION_ORDER[2:6])
    assert matrix["explicit_dependency_violations"] == 0
    assert len(matrix["ordered_pairs"]) == 12
    assert {row["dependency_classification"] for row in matrix["ordered_pairs"]} == {"NO_DEPENDENCY"}


def test_causal_context_id_excludes_outcomes_and_counts_unique(tmp_path):
    design = build_order_design(PRODUCTION_ORDER)
    run = _run(design["conditions"][0], positive={"identity_governance"})
    changed = copy.deepcopy(run)
    changed["route_manifests"][0]["routes"][2]["contribution_state"] = "NO_OBSERVABLE_CONTRIBUTION"
    result = run_route_order_deconfounding_analysis(
        raw_runs=[run, changed],
        task_order=["elite_cognitive_task_03.json"],
        order_design=design,
        output_dir=tmp_path,
        seed=1,
    )
    assert result["raw_marginal_observations"] == 8
    assert result["unique_causal_context_count"] == 4
    dataset = (tmp_path / "deconfounding_canonical_dataset.json").read_text()
    assert '"causal_context_id_excludes_outcome_fields": true' in dataset


def test_p2_accepts_deconfounded_route_identity_signal(tmp_path):
    design = build_order_design(PRODUCTION_ORDER)
    runs = [
        _run(condition, positive={"identity_governance"})
        for condition in design["conditions"]
    ]
    result = run_route_order_deconfounding_analysis(
        raw_runs=runs,
        task_order=["elite_cognitive_task_03.json"],
        order_design=design,
        output_dir=tmp_path,
        seed=1,
    )
    assert result["route_position_balanced"] is True
    assert result["raw_unique_useful_events"] == 4
    assert result["p2_gate_passed"] is True
    assert result["strongest_deconfounded_signal"] == "ROUTE_IDENTITY_SIGNAL_SUPPORTED"


def test_p2_rejects_repeated_same_causal_context(tmp_path):
    design = build_order_design(PRODUCTION_ORDER)
    run = _run(design["conditions"][0], positive={"identity_governance"})
    duplicate = copy.deepcopy(run)
    duplicate["condition_id"] = "A2"
    result = run_route_order_deconfounding_analysis(
        raw_runs=[run, duplicate],
        task_order=["elite_cognitive_task_03.json"],
        order_design=design,
        output_dir=tmp_path,
        seed=1,
    )
    assert result["unique_positive_causal_contexts"] == 1
    assert result["p2_gate_passed"] is False


def test_required_artifacts_are_written(tmp_path):
    design = build_order_design(PRODUCTION_ORDER)
    result = run_route_order_deconfounding_analysis(
        raw_runs=[_run(condition) for condition in design["conditions"]],
        task_order=["elite_cognitive_task_03.json"],
        order_design=design,
        output_dir=tmp_path,
        seed=1,
    )
    assert result["real_experiment_completed"] is True
    required = {
        "deconfounding_system_fingerprint.json",
        "deconfounding_dependency_matrix.json",
        "deconfounding_order_design.json",
        "deconfounding_run_manifest.json",
        "deconfounding_canonical_dataset.json",
        "deconfounding_causal_contexts.json",
        "deconfounding_route_position_matrix.json",
        "deconfounding_route_task_matrix.json",
        "deconfounding_position_task_matrix.json",
        "deconfounding_task03_reconstruction.json",
        "deconfounding_prior_state_analysis.json",
        "deconfounding_internal_value_analysis.json",
        "deconfounding_final_outcome_analysis.json",
        "deconfounding_p2_gate.json",
        "route_order_deconfounding_report.md",
    }
    assert required.issubset({path.name for path in tmp_path.iterdir()})

