# ============================================
# NEXRYN COGNITIVE HEALTH DIAGNOSTIC MODELS
# ============================================


DIAGNOSTIC_STATES = [
    "HEALTHY_EXPLORATION",
    "PRODUCTIVE_DRIFT",
    "TEMPORARY_OVERLOAD",
    "SEMANTIC_INFLAMMATION",
    "ONTOLOGICAL_FEVER",
    "IDENTITY_FRACTURE_RISK",
    "RECURSIVE_EXHAUSTION",
    "SEMANTIC_COLLAPSE_RISK",
    "CAUSAL_DISINTEGRATION",
    "CONSTITUTIONAL_INSTABILITY",
    "COGNITIVE_TRAUMA",
    "MERGE_ADDICTION",
    "OVER_STABILIZATION",
    "EVOLUTION_PARALYSIS",
    "SEMANTIC_TOXICITY",
    "IMMUNE_OVERREACTION",
    "MEMORY_CONGESTION",
]


def clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(
                value,
                maximum,
            ),
        ),
        4,
    )


def nested(context, path, default=0.0):

    value = context

    for key in path:

        if not isinstance(
            value,
            dict,
        ):

            return default

        value = value.get(
            key,
            default,
        )

    return value


def collect_health_metrics(context):

    entropy = clamp(
        context.get(
            "runtime_entropy",
            context.get(
                "semantic_entropy",
                0.0,
            ),
        )
    )

    drift = clamp(
        context.get(
            "identity_drift",
            nested(
                context,
                [
                    "identity_core_report",
                    "identity_drift",
                ],
                nested(
                    context,
                    [
                        "identity_continuity_engine_report",
                        "semantic_drift",
                    ],
                    0.0,
                ),
            ),
        )
    )

    recursion = clamp(
        context.get(
            "recursion_pressure",
            nested(
                context,
                [
                    "recursive_guardian_report",
                    "recursion_pressure",
                ],
                context.get(
                    "raw_reasoning_depth",
                    0,
                )
                / 12,
            ),
        )
    )

    memory_pressure = clamp(
        context.get(
            "memory_pressure_score",
            context.get(
                "working_memory_pressure",
                0.0,
            ),
        )
    )

    fragmentation = clamp(
        context.get(
            "ontology_fragmentation",
            context.get(
                "semantic_fragmentation",
                0.0,
            ),
        )
    )

    latent_conflicts = clamp(
        context.get(
            "latent_conflict_density",
            nested(
                context,
                [
                    "cognitive_immune_system_report",
                    "latent_conflict_count",
                ],
                0,
            )
            / 64,
        )
    )

    topology = clamp(
        context.get(
            "topology_integrity",
            1.0
            -
            context.get(
                "topology_stress",
                0.0,
            ),
        )
    )

    anchor_integrity = clamp(
        context.get(
            "semantic_anchor_integrity",
            nested(
                context,
                [
                    "semantic_anchor_graph_report",
                    "identity_stability",
                    "average_anchor_strength",
                ],
                0.5,
            ),
        )
    )

    constitutional = clamp(
        context.get(
            "constitutional_stability",
            1.0
            if nested(
                context,
                [
                    "epistemic_constitution_report",
                    "constitutional_state",
                ],
                "",
            )
            == "constitutional_cognition_stable"
            else 0.42,
        )
    )

    merge_exhaustion = clamp(
        context.get(
            "merge_exhaustion",
            context.get(
                "fusion_failure_rate",
                0.0,
            ),
        )
    )

    exploration_overload = clamp(
        context.get(
            "exploration_overload",
            nested(
                context,
                [
                    "conceptive_neurogenesis_report",
                    "generated_count",
                ],
                0,
            )
            / 24,
        )
    )

    semantic_noise = clamp(
        context.get(
            "semantic_noise",
            entropy * 0.45
            +
            fragmentation * 0.35
            +
            latent_conflicts * 0.20,
        )
    )

    fatigue = clamp(
        context.get(
            "cognitive_fatigue",
            recursion * 0.35
            +
            memory_pressure * 0.30
            +
            entropy * 0.20
            +
            merge_exhaustion * 0.15,
        )
    )

    fever = clamp(
        entropy * 0.26
        +
        drift * 0.18
        +
        recursion * 0.16
        +
        fragmentation * 0.14
        +
        memory_pressure * 0.12
        +
        semantic_noise * 0.14
    )

    return {
        "cognitive_fever_score": fever,
        "semantic_entropy": entropy,
        "identity_drift": drift,
        "recursion_pressure": recursion,
        "merge_exhaustion": merge_exhaustion,
        "ontology_fragmentation": fragmentation,
        "latent_conflict_density": latent_conflicts,
        "semantic_instability": semantic_noise,
        "memory_pressure": memory_pressure,
        "causal_conflict_frequency": clamp(
            context.get(
                "causal_conflict_frequency",
                0.0,
            )
        ),
        "semantic_anchor_integrity": anchor_integrity,
        "continuity_ligament_stability": clamp(
            context.get(
                "continuity_ligament_stability",
                1.0 - drift,
            )
        ),
        "constitutional_stability": constitutional,
        "topology_integrity": topology,
        "cognitive_fatigue": fatigue,
        "exploration_overload": exploration_overload,
        "semantic_noise": semantic_noise,
        "fusion_failure_rate": clamp(
            context.get(
                "fusion_failure_rate",
                merge_exhaustion,
            )
        ),
    }
