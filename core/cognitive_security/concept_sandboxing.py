# ============================================
# NEXRYN CONCEPT SANDBOXING
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


class ConceptSandboxing:

    def _adaptive_report(self, context, key):

        adaptive = context.get(
            "adaptive_semantic_control_report",
            {},
        )

        return (
            adaptive.get(
                key,
                {},
            )
            or
            context.get(
                f"{key}_report",
                {},
            )
        )

    def collect_events(self, context):

        events = []

        semantic_field = self._adaptive_report(
            context,
            "semantic_distance_fields",
        )

        compression = self._adaptive_report(
            context,
            "adaptive_semantic_compression",
        )

        for item in semantic_field.get(
            "high_risk_merge_pairs",
            [],
        ):

            events.append({
                "event_type":
                "merge",

                "source":
                item,
            })

        for item in compression.get(
            "fold_candidates",
            [],
        ):

            events.append({
                "event_type":
                "abstraction",

                "source":
                item,
            })

        for item in compression.get(
            "alias_candidates",
            [],
        ):

            events.append({
                "event_type":
                "bridge_concept",

                "source":
                item,
            })

        for item in context.get(
            "rejected_merges",
            [],
        ):

            events.append({
                "event_type":
                "merge",

                "source":
                item,
            })

        for item in context.get(
            "semantic_abstractions",
            [],
        ):

            events.append({
                "event_type":
                "abstraction",

                "source":
                item,
            })

        mutation_detected = (
            context.get(
                "mutation_applied",
                False,
            )
            or
            context.get(
                "mutation_detected",
                False,
            )
        )

        if mutation_detected:

            events.append({
                "event_type":
                "mutation",

                "source":
                {
                    "mutation_source":
                    context.get(
                        "mutation_source",
                        "unknown",
                    ),
                },
            })

        return events[:96]

    def sandbox_event(self, event, index, average_merge_risk, runtime_entropy):

        event_type = event.get(
            "event_type",
            "unknown",
        )

        source = event.get(
            "source",
            {},
        )

        source_risk = _clamp(
            source.get(
                "merge_risk",
                source.get(
                    "risk",
                    average_merge_risk,
                ),
            ),
        )

        sandbox_pressure = _clamp(
            source_risk * 0.55
            +
            average_merge_risk * 0.30
            +
            runtime_entropy * 0.15
        )

        return {
            "sandbox_id":
            f"concept_sandbox:{index + 1}",

            "event_type":
            event_type,

            "source":
            source,

            "sandbox_memory":
            "isolated_copy",

            "core_memory_access":
            "read_only_snapshot",

            "write_barrier":
            "enabled",

            "commit_to_core":
            False,

            "promotion_requirements":
            [
                "semantic_firewall_allow",
                "ontology_intrusion_clear",
                "identity_attack_clear",
                "bounded_entropy_delta",
            ],

            "sandbox_pressure":
            sandbox_pressure,

            "sandbox_policy":
            (
                "deny_commit"
                if sandbox_pressure >= 0.72
                else "quarantine_then_review"
                if sandbox_pressure >= 0.45
                else "observe_only"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        semantic_field = self._adaptive_report(
            context,
            "semantic_distance_fields",
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
                0.0,
            ),
        )

        events = self.collect_events(
            context,
        )

        sandboxes = [
            self.sandbox_event(
                event,
                index,
                average_merge_risk,
                runtime_entropy,
            )
            for index, event in enumerate(
                events,
            )
        ]

        locked_count = len([
            item
            for item in sandboxes
            if item.get(
                "sandbox_policy",
            )
            == "deny_commit"
        ])

        return {
            "system":
            "concept_sandboxing",

            "zero_trust_default":
            "sandbox_before_commit",

            "observed_event_count":
            len(
                events,
            ),

            "sandboxed_events":
            sandboxes,

            "locked_sandbox_count":
            locked_count,

            "sandbox_state":
            (
                "locked"
                if average_merge_risk >= 0.82
                or runtime_entropy >= 0.67
                or locked_count
                else "guarded"
                if sandboxes
                else "idle"
            ),

            "write_barrier_architecture":
            True,

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
