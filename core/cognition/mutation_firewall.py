# ============================================
# NEXRYN MUTATION FIREWALL
# ============================================


def _rounded(value):

    try:
        return round(
            float(value),
            4,
        )
    except Exception:
        return 0.0


class MutationFirewall:

    def __init__(self, max_events=2048):

        self.max_events = max_events
        self.seen_events = set()
        self.rehearsal_memory = set()

    def _trim(self):

        if len(
            self.seen_events,
        ) > self.max_events:

            self.seen_events = set(
                list(
                    self.seen_events,
                )[
                    -self.max_events:
                ]
            )

        if len(
            self.rehearsal_memory,
        ) > self.max_events:

            self.rehearsal_memory = set(
                list(
                    self.rehearsal_memory,
                )[
                    -self.max_events:
                ]
            )

    def event_key(self, concept_id, mutation):

        return (
            concept_id,
            mutation.get(
                "type",
            ),
            _rounded(
                mutation.get(
                    "fusion_stability",
                    0,
                )
            ),
            mutation.get(
                "primitive",
            ),
        )

    def allow(self, concept_id, mutation):

        key = self.event_key(
            concept_id,
            mutation,
        )

        if key in self.seen_events:

            return False

        self.seen_events.add(
            key,
        )

        self._trim()

        return True

    def allow_rehearsal(
        self,
        concept_id,
        constructive_score,
        identity_continuity,
    ):

        rehearsal_signature = (
            concept_id,
            _rounded(
                constructive_score,
            ),
            _rounded(
                identity_continuity,
            ),
        )

        if rehearsal_signature in self.rehearsal_memory:

            return False

        self.rehearsal_memory.add(
            rehearsal_signature,
        )

        self._trim()

        return True


mutation_firewall = MutationFirewall()
