# ============================================
# NEXRYN COGNITIVE GENEALOGY
# ============================================

from datetime import datetime


class CognitiveGenealogy:

    def __init__(self):

        self.genealogy = {}

    def update(self, lineage_report, archive_report):

        archived_ids = {
            item.get(
                "pattern_id",
            )
            for item in archive_report.get(
                "archived_patterns",
                [],
            )
        }

        updates = []

        for entry in lineage_report.get(
            "new_lineage_entries",
            [],
        ):

            lineage_id = entry.get(
                "lineage_id",
                "unknown",
            )

            node = self.genealogy.get(
                lineage_id,
                {
                    "lineage_id":
                    lineage_id,

                    "parents":
                    [],

                    "children":
                    [],

                    "survival_count":
                    0,

                    "collapse_count":
                    0,
                },
            )

            if entry.get(
                "outcome_state",
            ) == "survived_rehearsal":

                node[
                    "survival_count"
                ] += 1

            else:

                node[
                    "collapse_count"
                ] += 1

            node[
                "archived"
            ] = lineage_id in archived_ids

            node[
                "last_generation"
            ] = entry.get(
                "generation",
                0,
            )

            self.genealogy[
                lineage_id
            ] = node

            updates.append(
                node,
            )

        return {
            "system":
            "cognitive_genealogy",

            "genealogy_size":
            len(
                self.genealogy,
            ),

            "updated_nodes":
            updates,

            "recent_genealogy":
            list(
                self.genealogy.values()
            )[-32:],

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
