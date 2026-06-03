# ============================================
# NEXRYN SAFE CONCEPT FOLDING ENGINE
# ============================================

from datetime import datetime

from runtime.semantics.semantic_identity import (
    build_semantic_identity,
    identity_overlap
)


class SafeConceptFoldingEngine:

    def __init__(self):

        self.fold_history = []

    def normalize_sources(
        self,
        rejected_merge
    ):

        sources = rejected_merge.get(
            "sources",
            []
        )

        if len(sources) >= 2:

            return sources[0], sources[1]

        return (
            rejected_merge.get(
                "first",
                "unknown"
            ),
            rejected_merge.get(
                "second",
                "unknown"
            )
        )

    def assess_fold(
        self,
        first,
        second
    ):

        first_identity = build_semantic_identity(
            first
        )

        second_identity = build_semantic_identity(
            second
        )

        overlap = identity_overlap(
            first_identity,
            second_identity
        )

        shared_archetype = (
            str(first).split("_")[-1]
            ==
            str(second).split("_")[-1]
        )

        safe_to_fold = (
            overlap.get(
                "overlap",
                0.0
            ) >= 0.75
            and
            overlap.get(
                "conflict",
                1.0
            ) <= 0.10
        )

        soft_fold_candidate = (
            not safe_to_fold
            and
            shared_archetype
            and
            overlap.get(
                "conflict",
                1.0
            ) <= 0.25
        )

        return {
            "first":
            first,

            "second":
            second,

            "identity_overlap":
            overlap,

            "safe_to_fold":
            safe_to_fold,

            "soft_fold_candidate":
            soft_fold_candidate,

            "fold_policy":
            (
                "fold"
                if safe_to_fold
                else "alias_only"
                if soft_fold_candidate
                else "preserve_separation"
            )
        }

    def analyze_rejected_merges(
        self,
        rejected_merges
    ):

        fold_candidates = []
        alias_candidates = []
        preserved_separations = []

        for rejected_merge in rejected_merges:

            if not isinstance(
                rejected_merge,
                dict
            ):

                continue

            first, second = self.normalize_sources(
                rejected_merge
            )

            assessment = self.assess_fold(
                first,
                second
            )

            if assessment.get(
                "safe_to_fold",
                False
            ):

                fold_candidates.append(
                    assessment
                )

            elif assessment.get(
                "soft_fold_candidate",
                False
            ):

                alias_candidates.append(
                    assessment
                )

            else:

                preserved_separations.append(
                    assessment
                )

        report = {
            "engine":
            "safe_concept_folding",

            "rejected_merge_count":
            len(
                rejected_merges
            ),

            "fold_candidates":
            fold_candidates,

            "alias_candidates":
            alias_candidates,

            "preserved_separations":
            preserved_separations[:24],

            "folding_pressure":
            round(
                min(
                    len(rejected_merges)
                    /
                    100,
                    1.0
                ),
                4
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.fold_history.append(
            report
        )

        self.fold_history = self.fold_history[-32:]

        return report

    def build_report(self):

        latest = (
            self.fold_history[-1]
            if self.fold_history
            else {}
        )

        return {
            "folding_cycles":
            len(
                self.fold_history
            ),

            "latest_rejected_merge_count":
            latest.get(
                "rejected_merge_count",
                0
            ),

            "latest_folding_pressure":
            latest.get(
                "folding_pressure",
                0.0
            )
        }


safe_concept_folding_engine = (
    SafeConceptFoldingEngine()
)
