# ============================================
# NEXRYN COGNITIVE FAILURE MEMORY
# ============================================

from datetime import datetime


# ============================================
# COGNITIVE FAILURE MEMORY
# ============================================

class CognitiveFailureMemory:

    def __init__(self):

        self.failure_events = []

        self.failure_weights = {}

    # ============================================
    # STORE FAILURE
    # ============================================

    def store_failure(
        self,
        contradiction_type,
        collapse_source,
        ontology_damage=0.0,
        recovery_action="stabilize"
    ):

        event = {
            "contradiction_type":
            contradiction_type,

            "collapse_source":
            collapse_source,

            "ontology_damage":
            round(
                ontology_damage,
                4
            ),

            "recovery_action":
            recovery_action,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.failure_events.append(
            event
        )

        self.failure_events = (
            self.failure_events[-128:]
        )

        self.failure_weights[
            collapse_source
        ] = min(
            self.failure_weights.get(
                collapse_source,
                0.0
            )
            +
            max(
                ontology_damage,
                0.05
            ),
            1.0
        )

        return event

    # ============================================
    # RECORD MERGE REJECTIONS
    # ============================================

    def record_merge_rejections(
        self,
        rejected_merges
    ):

        events = []

        for rejected in rejected_merges:

            if not isinstance(
                rejected,
                dict
            ):

                continue

            sources = rejected.get(
                "sources",
                []
            )

            first = rejected.get(
                "first",
                (
                    sources[0]
                    if len(sources) > 0
                    else rejected.get(
                        "strategy_a",
                        "unknown"
                    )
                )
            )

            second = rejected.get(
                "second",
                (
                    sources[1]
                    if len(sources) > 1
                    else rejected.get(
                        "strategy_b",
                        "unknown"
                    )
                )
            )

            source = (
                str(first)
                +
                "::"
                +
                str(second)
            )

            identity_report = rejected.get(
                "identity_overlap",
                {}
            )

            if isinstance(
                identity_report,
                dict
            ):

                overlap = identity_report.get(
                    "overlap",
                    0.0
                )

            else:

                overlap = rejected.get(
                    "semantic_similarity",
                    0.0
                )

            damage = 1.0 - overlap

            events.append(
                self.store_failure(
                    contradiction_type="unsafe_merge",
                    collapse_source=source,
                    ontology_damage=damage,
                    recovery_action="block_merge"
                )
            )

        return events

    # ============================================
    # RECORD SEMANTIC CONTRADICTIONS
    # ============================================

    def record_semantic_contradictions(
        self,
        semantic_abstractions
    ):

        events = []

        for abstraction in semantic_abstractions:

            if not isinstance(
                abstraction,
                dict
            ):

                continue

            if abstraction.get(
                "semantic_penalty",
                0
            ) <= 0:

                continue

            source = (
                str(
                    abstraction.get(
                        "primitive",
                        "unknown"
                    )
                )
                +
                "::"
                +
                str(
                    abstraction.get(
                        "semantic_concept",
                        "unknown"
                    )
                )
            )

            events.append(
                self.store_failure(
                    contradiction_type="semantic_contradiction",
                    collapse_source=source,
                    ontology_damage=0.35,
                    recovery_action="penalize_future_reasoning"
                )
            )

        return events

    # ============================================
    # PRIOR FAILURE WEIGHT
    # ============================================

    def prior_failure_weight(
        self,
        key
    ):

        key = str(
            key
        )

        direct = self.failure_weights.get(
            key,
            0.0
        )

        related = 0.0

        for source, weight in self.failure_weights.items():

            if key and key in source:

                related = max(
                    related,
                    weight * 0.5
                )

        return round(
            min(
                direct
                +
                related,
                1.0
            ),
            4
        )

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        return {
            "failure_memory_size":
            len(
                self.failure_events
            ),

            "tracked_failure_sources":
            len(
                self.failure_weights
            ),

            "latest_failure":
            (
                self.failure_events[-1]
                if self.failure_events
                else {}
            )
        }


# ============================================
# GLOBAL MEMORY
# ============================================

cognitive_failure_memory = (
    CognitiveFailureMemory()
)
