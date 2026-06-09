def evaluate_identity_governance(
    context,
    allow_fragile_semantic_spine_integration=False,
    recovery_confirmed=False,
):
    """Evaluates identity and semantic spine stability from one policy."""

    context = context if isinstance(context, dict) else {}
    identity_stability = context.get(
        "identity_stability_report",
        {},
    )
    identity_stability_state = identity_stability.get(
        "identity_stability_state",
    )
    spine_report = context.get(
        "cognitive_spine_stabilizer_report",
        {},
    )
    semantic_spine_report = context.get(
        "semantic_spine_report",
        {},
    )
    semantic_anchor_report = context.get(
        "semantic_anchor_graph_report",
        context.get(
            "identity_continuity_guardian_report",
            {},
        ).get(
            "semantic_anchor_graph",
            {},
        ),
    )
    semantic_anchor_spine_state = semantic_anchor_report.get(
        "identity_stability",
        {},
    ).get(
        "stability_state",
    )
    identity_runtime_report = context.get(
        "identity_runtime_report",
        context.get("identity_continuity_runtime_report", {}),
    )
    identity_continuity_engine_report = context.get(
        "identity_continuity_engine_report",
        {},
    )
    runtime_gates = identity_runtime_report.get(
        "identity_governance_gates",
        identity_continuity_engine_report.get(
            "identity_governance_gates",
            {},
        ),
    )
    runtime_identity_stable = runtime_gates.get("identity_stable") is True
    runtime_semantic_spine_stable = (
        runtime_gates.get("semantic_spine_stable") is True
    )
    runtime_continuity_supported = (
        runtime_gates.get("identity_continuity_above_limit") is True
        or identity_continuity_engine_report.get(
            "identity_continuity_preserved",
            False,
        )
        is True
        or identity_runtime_report.get(
            "identity_continuity_preserved",
            False,
        )
        is True
    )
    explicit_identity_block = context.get("identity_stable") is False
    identity_stable = (
        not explicit_identity_block
        and (
            runtime_identity_stable
            or
            identity_stability_state
            not in [
                "fragile_semantic_spine",
                "identity_branching_tracked",
                "identity_convergence_tracked",
                "identity_transformation_tracked",
                "rollback_required",
                "recovery_monitoring",
            ]
            or allow_fragile_semantic_spine_integration
            or recovery_confirmed
        )
    )
    semantic_spine_stable = (
        (
            runtime_semantic_spine_stable
            or identity_stability_state != "fragile_semantic_spine"
            or allow_fragile_semantic_spine_integration
        )
        and spine_report.get(
            "cognitive_spine_state",
        )
        not in [
            "cognitive_spine_fragile",
            "cognitive_spine_repairing",
        ]
        and semantic_spine_report.get(
            "semantic_spine_state",
        )
        not in [
            "semantic_spine_repairing",
            "semantic_spine_recovering",
        ]
        and semantic_anchor_spine_state
        not in [
            "fragile_semantic_spine",
            "semantic_spine_reconstruction_required",
            "semantic_spine_recovering",
        ]
    ) or recovery_confirmed
    return {
        "system": "identity_governance_policy",
        "identity_stable": identity_stable,
        "semantic_spine_stable": semantic_spine_stable,
        "explicit_identity_block": explicit_identity_block,
        "identity_stability_state": identity_stability_state,
        "cognitive_spine_state":
        spine_report.get("cognitive_spine_state"),
        "semantic_spine_state":
        semantic_spine_report.get("semantic_spine_state"),
        "semantic_anchor_spine_state":
        semantic_anchor_spine_state,
        "identity_runtime_supported":
        runtime_continuity_supported,
        "identity_runtime_gates":
        runtime_gates,
        "allow_fragile_semantic_spine_integration":
        allow_fragile_semantic_spine_integration,
        "recovery_confirmed": recovery_confirmed,
    }


__all__ = [
    "evaluate_identity_governance",
]
