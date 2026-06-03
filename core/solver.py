import numpy as np


class ARCSolver:

    def __init__(self, input_grid, rules):

        self.input_grid = input_grid
        self.rules = rules

    # =========================================
    # APPLY RULES
    # =========================================

    def solve(self):

        predicted = np.copy(self.input_grid.grid)

        for rule in self.rules:

            # ---------------------------------
            # COLOR CHANGE
            # ---------------------------------

            if rule["rule"] == "color_changes":

                removed = rule["removed_colors"]
                added = rule["added_colors"]

                if len(removed) > 0 and len(added) > 0:

                    old_color = removed[0]
                    new_color = added[0]

                    predicted[predicted == old_color] = new_color

        return predicted