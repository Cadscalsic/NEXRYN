# ============================================
# NEXRYN MUTATION LINEAGE
# ============================================

from datetime import datetime

from core.cognition.mutation_firewall import (
    mutation_firewall,
)


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


class MutationLineage:

    def __init__(self):

        self.lineage = []
        self.mutation_firewall = mutation_firewall

    def _lineage_id(self, assessment, index):

        simulation = assessment.get(
            "simulation",
            {},
        )

        source = simulation.get(
            "source",
            {},
        )

        return ":".join([
            str(
                simulation.get(
                    "candidate_type",
                    "unknown",
                )
            ),
            str(
                source.get(
                    "first",
                    source.get(
                        "concept",
                        "unknown",
                    ),
                )
            ),
            str(
                source.get(
                    "second",
                    source.get(
                        "mutation_type",
                        index,
                    ),
                )
            ),
        ])

    def track(self, context):

        constructive = context.get(
            "constructive_reasoning_report",
            {},
        )

        assessments = constructive.get(
            "constructive_assessments",
            [],
        )

        identity = context.get(
            "identity_stability_report",
            {},
        )

        continuity = identity.get(
            "continuity_verifier",
            {},
        )

        entries = []

        for index, assessment in enumerate(
            assessments,
        ):

            signal = assessment.get(
                "constructive_signal",
                {},
            )

            simulation = assessment.get(
                "simulation",
                {},
            )

            lineage_entry = {
                "lineage_id":
                self._lineage_id(
                    assessment,
                    index,
                ),

                "generation":
                len(
                    self.lineage,
                )
                + 1,

                "mutation":
                simulation,

                "constructive_score":
                _clamp(
                    assessment.get(
                        "constructive_score",
                        signal.get(
                            "constructive_score",
                            0.0,
                        ),
                    ),
                ),

                "identity_continuity":
                _clamp(
                    continuity.get(
                        "continuity_score",
                        simulation.get(
                            "identity_continuity",
                            0.0,
                        ),
                    ),
                ),

                "outcome_state":
                (
                    "survived_rehearsal"
                    if signal.get(
                        "constructive_state",
                    )
                    in [
                        "constructive",
                        "promising",
                    ]
                    else "collapsed_in_rehearsal"
                ),

                "timestamp":
                str(
                    datetime.utcnow()
                ),
            }

            if not self.mutation_firewall.allow_rehearsal(
                lineage_entry.get(
                    "lineage_id",
                    "unknown",
                ),
                lineage_entry.get(
                    "constructive_score",
                    0.0,
                ),
                lineage_entry.get(
                    "identity_continuity",
                    0.0,
                ),
            ):

                continue

            self.lineage.append(
                lineage_entry,
            )

            entries.append(
                lineage_entry,
            )

        self.lineage = (
            self.lineage[-512:]
        )

        return {
            "system":
            "mutation_lineage",

            "new_lineage_entries":
            entries,

            "lineage_count":
            len(
                self.lineage,
            ),

            "survived_count":
            len([
                item
                for item in self.lineage
                if item.get(
                    "outcome_state",
                )
                == "survived_rehearsal"
            ]),

            "collapsed_count":
            len([
                item
                for item in self.lineage
                if item.get(
                    "outcome_state",
                )
                == "collapsed_in_rehearsal"
            ]),

            "recent_lineage":
            self.lineage[-32:],

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
