import matplotlib.pyplot as plt
import numpy as np


class ARCVisualizer:

    def __init__(self):

        self.cmap = plt.cm.get_cmap("tab10", 10)

    # =====================================================
    # SHOW GRID
    # =====================================================

    def show_grid(self, grid_object, title="ARC GRID"):

        plt.figure(figsize=(5, 5))

        plt.imshow(
            grid_object.grid,
            cmap=self.cmap,
            interpolation="nearest"
        )

        plt.title(title)

        plt.xticks([])

        plt.yticks([])

        plt.show()

    # =====================================================
    # SAVE GRID
    # =====================================================

    def save_grid(self, grid_object, path="outputs/grid.png"):

        plt.figure(figsize=(5, 5))

        plt.imshow(
            grid_object.grid,
            cmap=self.cmap,
            interpolation="nearest"
        )

        plt.xticks([])

        plt.yticks([])

        plt.savefig(path)

        plt.close()

        print(f"Grid image saved to: {path}")