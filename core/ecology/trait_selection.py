# ============================================
# NEXRYN TRAIT SELECTION
# ============================================

from datetime import datetime


class TraitSelection:

    def select(self, competition_report):

        selected = []
        suppressed = []

        for competitor in competition_report.get(
            "competitors",
            [],
        ):

            state = competitor.get(
                "competition_state",
            )

            if state in [
                "dominant",
                "surviving",
            ]:

                selected.append(
                    competitor,
                )

            else:

                suppressed.append(
                    competitor,
                )

        return {
            "system":
            "trait_selection",

            "selected_traits":
            selected,

            "suppressed_traits":
            suppressed,

            "selected_count":
            len(
                selected,
            ),

            "suppressed_count":
            len(
                suppressed,
            ),

            "selection_state":
            (
                "traits_selected_under_pressure"
                if selected
                else "selection_waiting_for_fitness"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
