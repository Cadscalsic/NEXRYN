# ============================================
# NEXRYN COGNITIVE PHARMACY MEDICATION REGISTRY
# ============================================


MEDICATIONS = {
    "SEMANTIC_SEDATIVE": {
        "category": "SEMANTIC_SEDATIVES",
        "effects": [
            "reduce_recursion_depth",
            "reduce_fusion_rate",
            "reduce_semantic_branching",
            "reduce_neurogenesis_intensity",
            "lower_entropy_generation",
            "reduce_abstraction_acceleration",
        ],
        "side_effects": [
            "semantic_numbness",
            "abstraction_suppression",
            "exploration_collapse",
        ],
    },
    "IDENTITY_STABILIZER": {
        "category": "IDENTITY_STABILIZERS",
        "effects": [
            "reinforce_semantic_anchors",
            "strengthen_lineage_integrity",
            "stabilize_continuity_ligaments",
            "reduce_identity_drift",
            "preserve_causal_history",
        ],
        "side_effects": [
            "excessive_rigidity",
            "over_stabilization",
        ],
    },
    "COGNITIVE_ANTI_INFLAMMATORY": {
        "category": "COGNITIVE_ANTI_INFLAMMATORIES",
        "effects": [
            "reduce_conflict_density",
            "calm_unstable_semantic_fields",
            "reduce_topology_stress",
        ],
        "side_effects": [
            "semantic_flattening",
        ],
    },
    "TRAUMA_RECOVERY_AGENT": {
        "category": "TRAUMA_RECOVERY_AGENTS",
        "effects": [
            "restore_stable_snapshots",
            "repair_semantic_spine",
            "rebuild_continuity_ligaments",
            "heal_rollback_trauma",
        ],
        "side_effects": [
            "rollback_dependence",
        ],
    },
    "RECURSIVE_REGULATOR": {
        "category": "RECURSIVE_REGULATORS",
        "effects": [
            "regulate_self_reference",
            "reduce_recursive_amplification",
            "control_loop_expansion",
            "maintain_dag_safety",
        ],
        "side_effects": [
            "innovation_paralysis",
        ],
    },
    "ONTOLOGY_DETOX_AGENT": {
        "category": "ONTOLOGY_DETOXIFICATION_AGENTS",
        "effects": [
            "eliminate_dead_bridges",
            "remove_unstable_hybrids",
            "purge_semantic_parasites",
            "dissolve_entropy_heavy_concepts",
        ],
        "side_effects": [
            "memory_overcompression",
        ],
    },
    "MEMORY_REPAIR_AGENT": {
        "category": "MEMORY_REPAIR_AGENTS",
        "effects": [
            "repair_causal_memory_chains",
            "restore_anchor_continuity",
            "heal_memory_fragmentation",
            "improve_consolidation_integrity",
        ],
        "side_effects": [
            "semantic_flattening",
        ],
    },
    "TOPOLOGY_STABILIZER": {
        "category": "TOPOLOGY_STABILIZERS",
        "effects": [
            "stabilize_semantic_topology",
            "prevent_graph_distortion",
            "preserve_acyclic_structure",
        ],
        "side_effects": [
            "topology_rigidity",
        ],
    },
    "COGNITIVE_SLEEP_AGENT": {
        "category": "COGNITIVE_SLEEP_AGENTS",
        "effects": [
            "memory_consolidation",
            "semantic_cleanup",
            "lineage_compression",
            "topology_repair",
            "anchor_reinforcement",
        ],
        "side_effects": [
            "cognitive_passivity",
        ],
    },
    "EXPLORATION_BALANCER": {
        "category": "EXPLORATION_BALANCERS",
        "effects": [
            "restore_healthy_curiosity",
            "recover_conceptual_flexibility",
            "prevent_excessive_conservatism",
        ],
        "side_effects": [
            "semantic_noise_rebound",
        ],
    },
}


class MedicationRegistry:

    def list_medications(self):

        return dict(
            MEDICATIONS,
        )

    def get(self, medication_id):

        return MEDICATIONS.get(
            medication_id,
            {},
        )
