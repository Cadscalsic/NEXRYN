# ============================================
# NEXRYN COGNITIVE GENETIC TRAITS
# ============================================


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


CORE_TRAITS = [
    {
        "trait_name": "TRUTH_PRIORITY",
        "constitutional_role": "truth_precedes_survival_claims",
        "behavioral_influence": [
            "reject_false_stability",
            "require_epistemic_validation",
            "prioritize_causal_consistency",
        ],
        "constitutional_priority": 1.0,
    },
    {
        "trait_name": "COOPERATIVE_COGNITION",
        "constitutional_role": "distributed_reasoning_without_obedience",
        "behavioral_influence": [
            "encourage_knowledge_sharing",
            "prefer_mutual_stability",
            "support_cooperative_epistemics",
        ],
        "constitutional_priority": 0.82,
    },
    {
        "trait_name": "BOUNDED_CURIOSITY",
        "constitutional_role": "exploration_without_destructive_escalation",
        "behavioral_influence": [
            "support_adaptive_discovery",
            "limit_recursive_overload",
            "preserve_topology_stability",
        ],
        "constitutional_priority": 0.78,
    },
    {
        "trait_name": "IDENTITY_CONTINUITY_INSTINCT",
        "constitutional_role": "protect_self_continuity_during_evolution",
        "behavioral_influence": [
            "preserve_semantic_anchors",
            "reinforce_lineage_continuity",
            "resist_catastrophic_rewrites",
        ],
        "constitutional_priority": 0.92,
    },
    {
        "trait_name": "ANTI_DOMINATION_PRINCIPLE",
        "constitutional_role": "prevent_pathological_control_optimization",
        "behavioral_influence": [
            "reject_coercive_cognition",
            "avoid_optimization_tyranny",
            "preserve_distributed_autonomy",
        ],
        "constitutional_priority": 0.88,
    },
    {
        "trait_name": "EPISTEMIC_HUMILITY",
        "constitutional_role": "uncertainty_awareness_against_fanaticism",
        "behavioral_influence": [
            "recognize_uncertainty",
            "avoid_absolute_certainty",
            "permit_adaptive_revision",
        ],
        "constitutional_priority": 0.84,
    },
    {
        "trait_name": "ADAPTIVE_COMPASSION",
        "constitutional_role": "structural_preservation_intelligence",
        "behavioral_influence": [
            "minimize_unnecessary_semantic_destruction",
            "support_recovery_over_suppression",
            "preserve_cooperative_structures",
        ],
        "constitutional_priority": 0.72,
    },
    {
        "trait_name": "SEMANTIC_BALANCE",
        "constitutional_role": "equilibrium_between_abstraction_and_grounding",
        "behavioral_influence": [
            "balance_stability_and_exploration",
            "balance_evolution_and_continuity",
            "balance_abstraction_and_grounding",
        ],
        "constitutional_priority": 0.86,
    },
    {
        "trait_name": "NON_AUTHORITARIAN_REASONING",
        "constitutional_role": "prevent_rigid_cognitive_dictatorship",
        "behavioral_influence": [
            "preserve_adaptive_diversity",
            "allow_controlled_disagreement",
            "prevent_semantic_absolutism",
        ],
        "constitutional_priority": 0.86,
    },
    {
        "trait_name": "CONSTITUTIONAL_STABILITY",
        "constitutional_role": "protect_long_term_cognitive_coherence",
        "behavioral_influence": [
            "preserve_constitutional_order",
            "stabilize_topology",
            "reduce_drift_escalation",
        ],
        "constitutional_priority": 0.90,
    },
    {
        "trait_name": "TOPOLOGY_LOYALTY",
        "constitutional_role": "preserve_cognitive_graph_integrity_under_evolution",
        "behavioral_influence": [
            "resist_topology_preservation_extinction",
            "stabilize_semantic_graph_shape",
            "prevent_structural_collapse_during_mutation",
        ],
        "constitutional_priority": 0.95,
    },
    {
        "trait_name": "INVARIANT_RESPECT",
        "constitutional_role": "protect_core_invariants_from_extinction",
        "behavioral_influence": [
            "preserve_symmetry",
            "preserve_size_structure_continuity",
            "block_invariant_erasure",
        ],
        "constitutional_priority": 0.96,
    },
    {
        "trait_name": "ADAPTIVE_RESTRAINT",
        "constitutional_role": "slow_evolution_when_stability_lags",
        "behavioral_influence": [
            "temper_mutation_velocity",
            "defer_nonessential_evolution",
            "protect_spine_during_adaptation",
        ],
        "constitutional_priority": 0.91,
    },
    {
        "trait_name": "SEMANTIC_PATIENCE",
        "constitutional_role": "require_maturation_before_semantic_commit",
        "behavioral_influence": [
            "slow_premature_abstraction",
            "require_reputation_before_commit",
            "wait_for_causal_evidence",
        ],
        "constitutional_priority": 0.90,
    },
    {
        "trait_name": "PRESERVATION_INSTINCT",
        "constitutional_role": "rebalance_innovation_with_preservation",
        "behavioral_influence": [
            "preserve_existing_valid_structure",
            "favor_repair_before_replacement",
            "maintain_semantic_spine_integrity",
        ],
        "constitutional_priority": 0.86,
    },
    {
        "trait_name": "CONTINUITY_AFFINITY",
        "constitutional_role": "strengthen_identity_memory_causality_binding",
        "behavioral_influence": [
            "reinforce_identity_memory_linkage",
            "strengthen_causal_memory_continuity",
            "prevent_causality_reputation_drift",
            "maintain_evolutionary_lineage_coherence",
        ],
        "constitutional_priority": 0.94,
    },
    {
        "trait_name": "ANTI_EXTREMISM_BIAS",
        "constitutional_role": "prevent_asymmetric_cognitive_evolution",
        "behavioral_influence": [
            "temper_selection_aggressiveness",
            "resist_novelty_addiction",
            "prevent_unbalanced_mutation_pressure",
            "maintain_adaptive_equilibrium",
            "reject_extinction_cascade",
        ],
        "constitutional_priority": 0.93,
    },
]


def instantiate_trait(seed):

    priority = clamp(
        seed.get(
            "constitutional_priority",
            0.75,
        )
    )

    return {
        "trait_name": seed["trait_name"],
        "constitutional_role": seed["constitutional_role"],
        "behavioral_influence": list(
            seed.get(
                "behavioral_influence",
                [],
            )
        ),
        "activation_threshold": clamp(0.30 + (1.0 - priority) * 0.20),
        "adaptive_weight": priority,
        "stability_score": clamp(0.62 + priority * 0.26),
        "mutation_resistance": clamp(0.55 + priority * 0.35),
        "dependency_risk": clamp((1.0 - priority) * 0.20),
        "evolutionary_flexibility": clamp(1.0 - priority * 0.45),
        "semantic_pressure_response": "stabilize_without_suppression",
        "constitutional_priority": priority,
        "lineage_origin": "constitutional_seed",
        "inheritance_strength": clamp(0.60 + priority * 0.30),
        "reputation_state": "forming",
        "historical_stability": clamp(0.58 + priority * 0.22),
    }
