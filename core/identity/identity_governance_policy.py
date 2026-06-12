"""
NEXRYN :: Identity Governance Policy
"""


DEFAULT_IDENTITY_CONTINUITY_THRESHOLD = 0.75
RELAXED_STABLE_RUNTIME_CONTINUITY_THRESHOLD = 0.70
DEFAULT_SEMANTIC_DRIFT_LIMIT = 0.18
DEFAULT_SEMANTIC_SPINE_MIN_SCORE = 0.70


def _safe_dict(value):
    return value if isinstance(value, dict) else {}


def _first_number(*values, default=None):
    for value in values:
        if isinstance(value, (int, float)):
            return float(value)
    return default


def _state_in(state, blocked_states):
    return state in blocked_states


def evaluate_identity_governance(
    context,
    allow_fragile_semantic_spine_integration=False,
    recovery_confirmed=False,
):
    context = _safe_dict(context)

    thresholds = _safe_dict(context.get("identity_governance_thresholds"))

    identity_continuity_threshold = thresholds.get(
        "identity_continuity_threshold",
        DEFAULT_IDENTITY_CONTINUITY_THRESHOLD,
    )
    stable_runtime_continuity_threshold = thresholds.get(
        "stable_runtime_continuity_threshold",
        RELAXED_STABLE_RUNTIME_CONTINUITY_THRESHOLD,
    )
    semantic_drift_limit = thresholds.get(
        "semantic_drift_limit",
        DEFAULT_SEMANTIC_DRIFT_LIMIT,
    )
    semantic_spine_min_score = thresholds.get(
        "semantic_spine_min_score",
        DEFAULT_SEMANTIC_SPINE_MIN_SCORE,
    )

    identity_stability = _safe_dict(context.get("identity_stability_report"))
    identity_stability_state = identity_stability.get("identity_stability_state")

    spine_report = _safe_dict(context.get("cognitive_spine_stabilizer_report"))
    semantic_spine_report = _safe_dict(context.get("semantic_spine_report"))

    guardian_report = _safe_dict(context.get("identity_continuity_guardian_report"))
    semantic_anchor_report = _safe_dict(
        context.get(
            "semantic_anchor_graph_report",
            _safe_dict(guardian_report.get("semantic_anchor_graph")),
        )
    )

    semantic_anchor_spine_state = _safe_dict(
        semantic_anchor_report.get("identity_stability")
    ).get("stability_state")

    identity_runtime_report = _safe_dict(
        context.get(
            "identity_runtime_report",
            context.get("identity_continuity_runtime_report"),
        )
    )

    identity_continuity_engine_report = _safe_dict(
        context.get("identity_continuity_engine_report")
    )

    runtime_gates = _safe_dict(
        identity_runtime_report.get(
            "identity_governance_gates",
            identity_continuity_engine_report.get("identity_governance_gates"),
        )
    )

    semantic_drift_report = _safe_dict(context.get("semantic_drift_report"))
    epistemic_drift_report = _safe_dict(context.get("epistemic_drift_report"))
    epistemic_containment_report = _safe_dict(
        context.get(
            "epistemic_drift_containment_report",
            context.get("epistemic_containment_report"),
        )
    )

    identity_runtime_state = identity_runtime_report.get("runtime_state")
    identity_runtime_ready = identity_runtime_report.get("runtime_ready") is True
    identity_runtime_split = identity_runtime_report.get("identity_split") is True
    identity_runtime_merged = identity_runtime_report.get("identity_merged") is True

    identity_runtime_continuity = _first_number(
        identity_runtime_report.get("identity_runtime_continuity"),
        identity_runtime_report.get("identity_continuity"),
        identity_continuity_engine_report.get("identity_continuity"),
        identity_continuity_engine_report.get("continuity_score"),
        context.get("identity_runtime_continuity"),
    )

    semantic_drift_score = _first_number(
        semantic_drift_report.get("semantic_drift_score"),
        semantic_drift_report.get("drift_score"),
        context.get("semantic_drift_score"),
        default=0.0,
    )

    semantic_spine_score = _first_number(
        semantic_spine_report.get("semantic_spine_score"),
        semantic_spine_report.get("spine_score"),
        spine_report.get("cognitive_spine_score"),
        context.get("semantic_spine_score"),
        default=1.0,
    )

    explicit_identity_block = context.get("identity_stable") is False
    runtime_identity_stable = runtime_gates.get("identity_stable") is True
    runtime_semantic_spine_stable = (
        runtime_gates.get("semantic_spine_stable") is True
    )

    stable_runtime_continuity_supported = (
        identity_runtime_state == "IDENTITY_RUNTIME_STABLE"
        and identity_runtime_ready
        and not identity_runtime_split
        and not identity_runtime_merged
        and identity_runtime_continuity is not None
        and identity_runtime_continuity >= stable_runtime_continuity_threshold
    )

    identity_continuity_above_limit = (
        runtime_gates.get("identity_continuity_above_limit") is True
        or identity_continuity_engine_report.get("identity_continuity_preserved")
        is True
        or identity_runtime_report.get("identity_continuity_preserved") is True
        or (
            identity_runtime_continuity is not None
            and identity_runtime_continuity >= identity_continuity_threshold
        )
        or stable_runtime_continuity_supported
    )

    semantic_drift_below_limit = (
        runtime_gates.get("semantic_drift_below_limit") is True
        or semantic_drift_score <= semantic_drift_limit
    )

    semantic_spine_state_blocked = (
        identity_stability_state
        in {
            "fragile_semantic_spine",
            "rollback_required",
            "recovery_monitoring",
        }
        or _state_in(
            spine_report.get("cognitive_spine_state"),
            {
                "cognitive_spine_fragile",
                "cognitive_spine_repairing",
            },
        )
        or _state_in(
            semantic_spine_report.get("semantic_spine_state"),
            {
                "semantic_spine_repairing",
                "semantic_spine_recovering",
            },
        )
        or _state_in(
            semantic_anchor_spine_state,
            {
                "fragile_semantic_spine",
                "semantic_spine_reconstruction_required",
                "semantic_spine_recovering",
            },
        )
    )

    semantic_spine_stable = (
        runtime_semantic_spine_stable
        or (
            not semantic_spine_state_blocked
            and semantic_spine_score >= semantic_spine_min_score
        )
        or allow_fragile_semantic_spine_integration
        or recovery_confirmed
    )

    identity_stable = (
        not explicit_identity_block
        and (
            runtime_identity_stable
            or identity_continuity_above_limit
            or recovery_confirmed
        )
    )

    containment_active = (
        epistemic_containment_report.get("containment_active") is True
        or epistemic_containment_report.get("epistemic_drift_containment_active")
        is True
        or epistemic_drift_report.get("containment_active") is True
    )

    epistemic_drift_containment_inactive = not containment_active

    gates = {
        "identity_stable": identity_stable,
        "semantic_spine_stable": semantic_spine_stable,
        "semantic_drift_below_limit": semantic_drift_below_limit,
        "identity_continuity_above_limit": identity_continuity_above_limit,
    }

    failed_gates = [
        gate_name
        for gate_name, passed in gates.items()
        if passed is not True
    ]

    if epistemic_drift_containment_inactive:
        failed_gates.append("epistemic_drift_containment_inactive")

    return {
        "system": "identity_governance_policy",
        "identity_stable": identity_stable,
        "semantic_spine_stable": semantic_spine_stable,
        "semantic_drift_below_limit": semantic_drift_below_limit,
        "identity_continuity_above_limit": identity_continuity_above_limit,
        "epistemic_drift_containment_inactive":
            epistemic_drift_containment_inactive,
        "epistemic_drift_containment_active": containment_active,
        "governance_gates": gates,
        "failed_identity_governance_gates": failed_gates,
        "explicit_identity_block": explicit_identity_block,
        "identity_stability_state": identity_stability_state,
        "identity_runtime_state": identity_runtime_state,
        "identity_runtime_ready": identity_runtime_ready,
        "identity_runtime_split": identity_runtime_split,
        "identity_runtime_merged": identity_runtime_merged,
        "identity_runtime_supported": identity_continuity_above_limit,
        "identity_runtime_continuity": identity_runtime_continuity,
        "stable_runtime_continuity_supported":
            stable_runtime_continuity_supported,
        "semantic_drift_score": semantic_drift_score,
        "semantic_spine_score": semantic_spine_score,
        "thresholds": {
            "identity_continuity_threshold":
                identity_continuity_threshold,
            "stable_runtime_continuity_threshold":
                stable_runtime_continuity_threshold,
            "semantic_drift_limit": semantic_drift_limit,
            "semantic_spine_min_score": semantic_spine_min_score,
        },
        "cognitive_spine_state": spine_report.get("cognitive_spine_state"),
        "semantic_spine_state": semantic_spine_report.get("semantic_spine_state"),
        "semantic_anchor_spine_state": semantic_anchor_spine_state,
        "identity_runtime_gates": runtime_gates,
        "allow_fragile_semantic_spine_integration":
            allow_fragile_semantic_spine_integration,
        "recovery_confirmed": recovery_confirmed,
    }


__all__ = [
    "evaluate_identity_governance",
]