# ============================================
# NEXRYN ONTOLOGY INTRUSION DETECTION
# ============================================

from datetime import datetime


def _clamp(value, minimum=0.0, maximum=1.0):

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


def _nested_get(source, path, default=None):

    current = source

    for key in path:

        if not isinstance(
            current,
            dict,
        ):

            return default

        current = current.get(
            key,
            default,
        )

    return current


class OntologyIntrusionDetection:

    def collect_semantic_field(self, context):

        adaptive = context.get(
            "adaptive_semantic_control_report",
            {},
        )

        return (
            adaptive.get(
                "semantic_distance_fields",
                {},
            )
            or
            context.get(
                "semantic_distance_fields_report",
                {},
            )
        )

    def collect_compression_report(self, context):

        adaptive = context.get(
            "adaptive_semantic_control_report",
            {},
        )

        return (
            adaptive.get(
                "adaptive_semantic_compression",
                {},
            )
            or
            context.get(
                "adaptive_semantic_compression_report",
                {},
            )
        )

    def inspect(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        semantic_field = self.collect_semantic_field(
            context,
        )

        compression = self.collect_compression_report(
            context,
        )

        average_merge_risk = _clamp(
            semantic_field.get(
                "average_merge_risk",
                context.get(
                    "average_merge_risk",
                    0.0,
                ),
            ),
        )

        runtime_entropy = _clamp(
            context.get(
                "runtime_entropy",
                _nested_get(
                    context,
                    [
                        "cognitive_entropy_report",
                        "runtime_entropy",
                    ],
                    0.0,
                ),
            ),
        )

        defragmenter = context.get(
            "ontology_defragmenter_report",
            {},
        )

        fragmentation = _clamp(
            defragmenter.get(
                "semantic_fragmentation_before",
                defragmenter.get(
                    "semantic_fragmentation",
                    0.0,
                ),
            ),
        )

        risky_pairs = semantic_field.get(
            "high_risk_merge_pairs",
            [],
        )

        fold_candidates = compression.get(
            "fold_candidates",
            [],
        )

        alias_candidates = compression.get(
            "alias_candidates",
            [],
        )

        risky_event_pressure = _clamp(
            (
                len(
                    risky_pairs,
                )
                +
                len(
                    fold_candidates,
                )
                +
                len(
                    alias_candidates,
                )
            )
            /
            24
        )

        intrusion_score = _clamp(
            average_merge_risk * 0.50
            +
            runtime_entropy * 0.25
            +
            fragmentation * 0.15
            +
            risky_event_pressure * 0.10
        )

        intrusion_state = (
            "intrusion_detected"
            if intrusion_score >= 0.82
            or average_merge_risk >= 0.82
            else "quarantine"
            if intrusion_score >= 0.66
            else "monitoring"
            if intrusion_score >= 0.42
            else "clear"
        )

        return {
            "system":
            "ontology_intrusion_detection",

            "average_merge_risk":
            average_merge_risk,

            "runtime_entropy":
            runtime_entropy,

            "semantic_fragmentation":
            fragmentation,

            "risky_event_pressure":
            risky_event_pressure,

            "intrusion_score":
            intrusion_score,

            "intrusion_state":
            intrusion_state,

            "suspicious_merge_pairs":
            risky_pairs[:24],

            "suspicious_fold_candidates":
            fold_candidates[:24],

            "suspicious_alias_candidates":
            alias_candidates[:24],

            "recommended_controls":
            (
                [
                    "default_deny_semantic_merge",
                    "quarantine_bridge_concepts",
                    "require_identity_topology_attestation",
                    "disable_autonomous_ontology_write",
                ]
                if intrusion_state
                in [
                    "intrusion_detected",
                    "quarantine",
                ]
                else [
                    "audit_semantic_merge",
                ]
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
