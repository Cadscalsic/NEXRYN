from core.cognitive_security.semantic_firewall import (
    SemanticFirewall,
)


def test_semantic_firewall_seals_on_extreme_merge_risk():

    firewall = SemanticFirewall()

    context = {
        "runtime_entropy": 0.6749,
        "adaptive_semantic_control_report": {
            "semantic_distance_fields": {
                "average_merge_risk": 0.8814,
                "high_risk_merge_pairs": [
                    {
                        "first": "object_identity",
                        "second": "shape_identity",
                        "merge_risk": 0.91,
                    },
                    {
                        "first": "topology_preservation",
                        "second": "symbolic_remapping",
                        "merge_risk": 0.88,
                    },
                ],
            },
            "adaptive_semantic_compression": {
                "fold_candidates": [
                    {
                        "first": "position_shift",
                        "second": "directional_motion",
                        "merge_risk": 0.74,
                    },
                ],
                "alias_candidates": [
                    {
                        "first": "object_identity",
                        "second": "shape_identity",
                        "merge_risk": 0.83,
                    },
                ],
            },
        },
        "causal_world_simulation_report": {
            "identity_risk_prediction": {
                "predicted_identity_risk": 0.76,
            },
        },
        "identity_stability_report": {
            "identity_diff": {
                "identity_drift": 0.41,
            },
        },
        "identity_anchor_core_report": {
            "anchor_state": "reinforced",
        },
    }

    report = firewall.run_cycle(
        context,
    )

    assert report["firewall_state"] == "sealed"
    assert report["decision"] == "deny"

    assert (
        report["ontology_intrusion_detection"][
            "intrusion_state"
        ]
        ==
        "intrusion_detected"
    )

    assert (
        report["concept_sandboxing"][
            "sandbox_state"
        ]
        ==
        "locked"
    )

    assert (
        "semantic_merge"
        in report["blocked_operations"]
    )

    assert (
        "identity_topology_write"
        in report["blocked_operations"]
    )
