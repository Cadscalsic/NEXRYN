# ============================================
# NEXRYN BENEFICIAL PATTERN ARCHIVE
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


class BeneficialPatternArchive:

    def __init__(self):

        self.archive = []

    def archive_patterns(self, lineage_report):

        archived = []

        for entry in lineage_report.get(
            "new_lineage_entries",
            [],
        ):

            score = _clamp(
                entry.get(
                    "constructive_score",
                    0.0,
                ),
            )

            continuity = _clamp(
                entry.get(
                    "identity_continuity",
                    0.0,
                ),
            )

            if score < 0.34:

                continue

            item = {
                "pattern_id":
                entry.get(
                    "lineage_id",
                    "unknown",
                ),

                "constructive_score":
                score,

                "identity_continuity":
                continuity,

                "survival_state":
                entry.get(
                    "outcome_state",
                    "unknown",
                ),

                "mutation":
                entry.get(
                    "mutation",
                    {},
                ),

                "archive_state":
                (
                    "elite_pattern"
                    if score >= 0.62
                    and continuity >= 0.62
                    else "promising_pattern"
                ),

                "timestamp":
                str(
                    datetime.utcnow()
                ),
            }

            self.archive.append(
                item,
            )

            archived.append(
                item,
            )

        self.archive = (
            self.archive[-512:]
        )

        return {
            "system":
            "beneficial_pattern_archive",

            "archived_patterns":
            archived,

            "archive_size":
            len(
                self.archive,
            ),

            "elite_count":
            len([
                item
                for item in self.archive
                if item.get(
                    "archive_state",
                )
                == "elite_pattern"
            ]),

            "recent_archive":
            self.archive[-32:],

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
