# ============================================
# NEXRYN COGNITIVE STABILIZATION PROTOCOLS
# ============================================


class StabilizationProtocols:

    def build(self, diagnosis):

        state = diagnosis.get(
            "state",
            "HEALTHY_EXPLORATION",
        )

        protocols = []

        if state in [
            "IDENTITY_FRACTURE_RISK",
            "COGNITIVE_TRAUMA",
            "SEMANTIC_COLLAPSE_RISK",
        ]:

            protocols.extend([
                "reinforce_identity_anchors",
                "pause_core_memory_writes",
                "require_rollback_safe_rehearsal",
            ])

        if state in [
            "TEMPORARY_OVERLOAD",
            "SEMANTIC_INFLAMMATION",
            "MEMORY_CONGESTION",
        ]:

            protocols.extend([
                "reduce_parallel_branches",
                "prioritize_grounded_context",
                "defer_optional_fusions",
            ])

        if state in [
            "RECURSIVE_EXHAUSTION",
        ]:

            protocols.extend([
                "compress_recursive_depth",
                "collapse_low_value_hypotheses",
            ])

        if state in [
            "OVER_STABILIZATION",
            "EVOLUTION_PARALYSIS",
        ]:

            protocols.extend([
                "restore_safe_exploration",
                "lower_sedation_bias",
            ])

        return {
            "system":
            "stabilization_protocols",

            "protocols":
            protocols,
        }
