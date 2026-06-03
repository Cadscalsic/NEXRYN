# ============================================
# NEXRYN CAUSAL MEMORY
# ============================================

from datetime import datetime


class CausalMemory:

    def __init__(self):

        self.causal_history = []

    def collect_events(self, context):

        events = []

        firewall = context.get(
            "semantic_firewall_report",
            {},
        )

        sandbox = firewall.get(
            "concept_sandboxing",
            {},
        )

        for event in sandbox.get(
            "sandboxed_events",
            [],
        ):

            events.append({
                "event_type":
                event.get(
                    "event_type",
                    "unknown",
                ),

                "source":
                event.get(
                    "source",
                    {},
                ),

                "sandbox_policy":
                event.get(
                    "sandbox_policy",
                    "unknown",
                ),
            })

        mutation_plan = context.get(
            "mutation_plan",
            {},
        )

        for item in mutation_plan.get(
            "mutation_candidates",
            [],
        ):

            events.append({
                "event_type":
                "mutation",

                "source":
                item,

                "sandbox_policy":
                "pending_identity_spine_check",
            })

        return events[:96]

    def record(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        events = self.collect_events(
            context,
        )

        for event in events:

            self.causal_history.append({
                "event":
                event,

                "identity_drift":
                context.get(
                    "identity_drift",
                    context.get(
                        "identity_core_report",
                        {},
                    ).get(
                        "identity_drift",
                        0.0,
                    ),
                ),

                "runtime_entropy":
                context.get(
                    "runtime_entropy",
                    0.0,
                ),

                "timestamp":
                str(
                    datetime.utcnow()
                ),
            })

        self.causal_history = (
            self.causal_history[-256:]
        )

        return {
            "system":
            "causal_memory",

            "recorded_event_count":
            len(
                events,
            ),

            "causal_history_size":
            len(
                self.causal_history,
            ),

            "recent_events":
            self.causal_history[-32:],

            "memory_state":
            (
                "tracking_evolution"
                if events
                else "stable_observation"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
