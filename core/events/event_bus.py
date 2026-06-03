# ============================================
# NEXRYN COGNITIVE EVENT BUS
# ============================================

from datetime import datetime


class CognitiveEventBus:

    def __init__(self):

        self.subscribers = {}
        self.event_log = []
        self.routed_events = []

    def subscribe(self, event_type, subscriber):

        if event_type not in self.subscribers:

            self.subscribers[
                event_type
            ] = []

        if subscriber not in self.subscribers[
            event_type
        ]:

            self.subscribers[
                event_type
            ].append(
                subscriber,
            )

        return {
            "event_type":
            event_type,

            "subscriber":
            subscriber,

            "subscriber_count":
            len(
                self.subscribers[
                    event_type
                ],
            ),
        }

    def publish(self, event):

        if not isinstance(
            event,
            dict,
        ):

            event = {
                "event_type":
                "unknown",

                "payload":
                event,
            }

        event_type = event.get(
            "event_type",
            "unknown",
        )

        enriched = dict(
            event,
        )

        enriched[
            "timestamp"
        ] = str(
            datetime.utcnow()
        )

        enriched[
            "subscribers"
        ] = list(
            self.subscribers.get(
                event_type,
                [],
            )
        )

        self.event_log.append(
            enriched,
        )

        self.event_log = (
            self.event_log[-256:]
        )

        return enriched

    def priority_route(self, event):

        published = self.publish(
            event,
        )

        priority = published.get(
            "priority",
            0.5,
        )

        if priority >= 0.85:

            route = "critical_signal_lane"

        elif priority >= 0.55:

            route = "priority_signal_lane"

        else:

            route = "background_signal_lane"

        routed = dict(
            published,
        )

        routed[
            "route"
        ] = route

        self.routed_events.append(
            routed,
        )

        self.routed_events = (
            self.routed_events[-256:]
        )

        return routed

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        emitted = []

        kernel = context.get(
            "cognitive_kernel_report",
            {},
        )

        if kernel:

            emitted.append(
                self.priority_route({
                    "event_type":
                    "kernel_mode_changed",

                    "priority":
                    0.90
                    if kernel.get(
                        "active_mode",
                    )
                    == "stabilization_mode"
                    else 0.60,

                    "payload":
                    {
                        "active_mode":
                        kernel.get(
                            "active_mode",
                        ),

                        "enabled_subsystems":
                        kernel.get(
                            "enabled_subsystems",
                            [],
                        ),
                    },
                })
            )

        immune = context.get(
            "cognitive_immune_system_v2_report",
            {},
        )

        if immune:

            emitted.append(
                self.priority_route({
                    "event_type":
                    "immune_signal",

                    "priority":
                    0.92
                    if immune.get(
                        "immune_state",
                    )
                    == "emergency_response"
                    else 0.55,

                    "payload":
                    immune.get(
                        "immune_response_actions",
                        [],
                    ),
                })
            )

        identity = context.get(
            "identity_core_report",
            {},
        )

        behavior_shift = identity.get(
            "behavior_shift",
            {},
        )

        if behavior_shift.get(
            "shift_detected",
            False,
        ):

            emitted.append(
                self.priority_route({
                    "event_type":
                    "identity_behavior_shift",

                    "priority":
                    0.95,

                    "payload":
                    behavior_shift,
                })
            )

        return {
            "system":
            "cognitive_event_bus",

            "emitted_events":
            emitted,

            "emitted_count":
            len(
                emitted,
            ),

            "subscriber_count":
            sum(
                len(
                    subscribers,
                )
                for subscribers in self.subscribers.values()
            ),

            "event_log_size":
            len(
                self.event_log,
            ),

            "routed_event_count":
            len(
                self.routed_events,
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }


cognitive_event_bus = (
    CognitiveEventBus()
)
