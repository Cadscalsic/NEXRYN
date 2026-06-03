# ============================================
# NEXRYN IDENTITY ANCHORS
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


class IdentityAnchors:

    def build_causal_anchors(self, context):

        causal_memory = context.get(
            "identity_stability_report",
            {},
        ).get(
            "causal_memory",
            {},
        )

        recent_events = causal_memory.get(
            "recent_events",
            [],
        )

        return {
            "anchor_type":
            "causal",

            "anchor_strength":
            _clamp(
                min(
                    len(
                        recent_events,
                    ),
                    16,
                )
                / 16
                * 0.42
                +
                0.38
            ),

            "tracked_events":
            recent_events[-16:],
        }

    def build_semantic_anchors(self, context):

        semantic = context.get(
            "semantic_legitimacy_report",
            {},
        )

        score = _clamp(
            semantic.get(
                "semantic_legitimacy_score",
                context.get(
                    "semantic_attestation_score",
                    0.0,
                ),
            ),
        )

        return {
            "anchor_type":
            "semantic",

            "anchor_strength":
            _clamp(
                0.36
                +
                score * 0.54
            ),

            "semantic_legitimacy_score":
            score,
        }

    def build_memory_anchors(self, context):

        memory = context.get(
            "horizon_memory_report",
            {},
        )

        archive_count = memory.get(
            "archive_count",
            memory.get(
                "permanent_pattern_count",
                0,
            ),
        )

        return {
            "anchor_type":
            "memory",

            "anchor_strength":
            _clamp(
                0.34
                +
                min(
                    archive_count,
                    32,
                )
                / 32
                * 0.48
            ),

            "archive_count":
            archive_count,
        }

    def build_lineage_anchors(self, context):

        evolutionary = context.get(
            "evolutionary_memory_report",
            {},
        )

        lineage = evolutionary.get(
            "mutation_lineage",
            {},
        )

        survived = lineage.get(
            "survived_count",
            0,
        )

        collapsed = lineage.get(
            "collapsed_count",
            0,
        )

        survival_ratio = _clamp(
            survived
            /
            max(
                survived + collapsed,
                1,
            )
        )

        return {
            "anchor_type":
            "lineage",

            "anchor_strength":
            _clamp(
                0.32
                +
                survival_ratio * 0.52
            ),

            "survival_ratio":
            survival_ratio,
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        anchors = [
            self.build_causal_anchors(
                context,
            ),
            self.build_semantic_anchors(
                context,
            ),
            self.build_memory_anchors(
                context,
            ),
            self.build_lineage_anchors(
                context,
            ),
        ]

        identity_continuity = _clamp(
            context.get(
                "identity_stability_report",
                {},
            ).get(
                "continuity_verifier",
                {},
            ).get(
                "continuity_score",
                context.get(
                    "identity_continuity",
                    0.0,
                ),
            ),
        )

        anchor_strength = _clamp(
            (
                sum(
                    item.get(
                        "anchor_strength",
                        0.0,
                    )
                    for item in anchors
                )
                /
                max(
                    len(
                        anchors,
                    ),
                    1,
                )
            )
            * 0.70
            +
            identity_continuity
            * 0.30
        )

        return {
            "system":
            "identity_anchors",

            "causal_anchors":
            anchors[0],

            "semantic_anchors":
            anchors[1],

            "memory_anchors":
            anchors[2],

            "lineage_anchors":
            anchors[3],

            "identity_continuity":
            identity_continuity,

            "anchor_strength":
            anchor_strength,

            "anchor_state":
            (
                "collapse_resistant"
                if anchor_strength >= 0.70
                else "reinforcing"
                if anchor_strength >= 0.48
                else "fragile"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }


identity_anchors = (
    IdentityAnchors()
)
