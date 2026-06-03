from core.epistemic_models import clamp


class SemanticDriftController:
    def _compression_ratio(self, context):
        return clamp(
            context.get(
                "memory_compression_report",
                {},
            ).get(
                "compression_ratio",
                0.0,
            )
        )

    def _drift_cluster_count(self, context):
        return context.get(
            "semantic_anchor_graph_report",
            context.get(
                "identity_continuity_guardian_report",
                {},
            ).get(
                "semantic_anchor_graph",
                {},
            ),
        ).get(
            "drift_clusters",
            {},
        ).get(
            "drift_cluster_count",
            0,
        )

    def regulate(self, rehearsal, context=None):
        context = context if isinstance(context, dict) else {}
        baseline_drift = clamp(
            rehearsal.get("baseline_semantic_drift", 1.0)
        )
        baseline_continuity = clamp(
            rehearsal.get("baseline_identity_continuity", 0.0)
        )
        compression_ratio = self._compression_ratio(context)
        drift_cluster_count = self._drift_cluster_count(context)
        interventions = [
            {
                "action": "reanchor_semantic_spine",
                "semantic_drift_reduction": 0.10,
                "identity_continuity_gain": 0.03,
            },
            {
                "action": "remove_contradictory_identity_edges",
                "semantic_drift_reduction":
                min(0.04 + drift_cluster_count * 0.005, 0.08),
                "identity_continuity_gain": 0.02,
            },
            {
                "action": "compress_non_core_memory",
                "semantic_drift_reduction":
                min(0.04 + compression_ratio * 0.04, 0.07),
                "identity_continuity_gain": 0.01,
            },
            {
                "action": "reinforce_causal_anchors",
                "semantic_drift_reduction": 0.07,
                "identity_continuity_gain": 0.03,
            },
        ]
        drift_reduction = sum(
            item["semantic_drift_reduction"]
            for item in interventions
        )
        continuity_gain = sum(
            item["identity_continuity_gain"]
            for item in interventions
        )
        semantic_drift = clamp(baseline_drift - drift_reduction)
        identity_continuity = clamp(
            baseline_continuity + continuity_gain
        )
        repair_inactive = (
            semantic_drift < 0.58
            and identity_continuity >= 0.62
        )

        return {
            "system": "semantic_drift_controller",
            "phase": "6.2",
            "baseline_semantic_drift": baseline_drift,
            "semantic_drift": semantic_drift,
            "semantic_drift_reduction": round(drift_reduction, 4),
            "baseline_identity_continuity": baseline_continuity,
            "identity_continuity": identity_continuity,
            "identity_continuity_gain": round(continuity_gain, 4),
            "drift_cluster_count": drift_cluster_count,
            "compression_ratio": compression_ratio,
            "interventions": interventions,
            "identity_repair_inactive": repair_inactive,
            "semantic_containment_inactive": repair_inactive,
            "semantic_spine_state": (
                "semantic_spine_recovering"
                if repair_inactive
                else "semantic_spine_repairing"
            ),
            "simulation_only": True,
            "persistent_identity_write_forbidden": True,
        }


__all__ = [
    "SemanticDriftController",
]
