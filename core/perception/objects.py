# ============================================
# NEXRYN ARC OBJECT SYSTEM
# High-Level Symbolic Entity
# ============================================

from datetime import datetime

import numpy as np

from core.perception.connected_component import (
    ConnectedComponent
)


# ============================================
# ARC OBJECT
# ============================================

class ARCObject(

    ConnectedComponent
):

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(

        self,

        cells,

        color
    ):

        super().__init__(
            cells,
            color
        )

        # ====================================
        # OBJECT IDENTITY
        # ====================================

        self.object_id = (
            id(self)
        )

        self.created_at = (
            str(datetime.utcnow())
        )

        # ====================================
        # SYMBOLIC PROFILE
        # ====================================

        self.symbolic_profile = {

            "symbolic_object":
            True,

            "semantic_entity":
            True,

            "graph_ready":
            True,

            "relational_reasoning":
            True,

            "cognitive_entity":
            True
        }

        # ====================================
        # RELATIONAL MEMORY
        # ====================================

        self.relationships = []

        # ====================================
        # SEMANTIC TAGS
        # ====================================

        self.semantic_tags = []

    # ========================================
    # SHAPE CLASSIFICATION
    # ========================================

    def classify_shape(self):

        width = self.width()

        height = self.height()

        density = self.density()

        # ====================================
        # SINGLE CELL
        # ====================================

        if self.size() == 1:

            return "point"

        # ====================================
        # LINE
        # ====================================

        if width == 1 or height == 1:

            return "line"

        # ====================================
        # SOLID BLOCK
        # ====================================

        if density >= 0.9:

            return "solid"

        # ====================================
        # SPARSE STRUCTURE
        # ====================================

        if density <= 0.4:

            return "sparse"

        return "composite"

    # ========================================
    # SYMMETRY SCORE
    # ========================================

    def symmetry_score(self):

        matrix = self.shape_matrix()

        horizontal = np.array_equal(

            matrix,

            np.flipud(matrix)
        )

        vertical = np.array_equal(

            matrix,

            np.fliplr(matrix)
        )

        score = 0.0

        if horizontal:
            score += 0.5

        if vertical:
            score += 0.5

        return score

    # ========================================
    # SEMANTIC COMPLEXITY
    # ========================================

    def semantic_complexity(self):

        topology = (
            self.topology_profile()
        )

        return round(

            (
                topology["complexity"]
                *
                (1 + self.symmetry_score())
            ),

            4
        )

    # ========================================
    # RELATIONSHIP MANAGEMENT
    # ========================================

    def add_relationship(

        self,

        relationship
    ):

        self.relationships.append(
            relationship
        )

    # ========================================
    # SEMANTIC TAGGING
    # ========================================

    def add_semantic_tag(

        self,

        tag
    ):

        if tag not in self.semantic_tags:

            self.semantic_tags.append(
                tag
            )

    # ========================================
    # OBJECT SIGNATURE
    # ========================================

    def object_signature(self):

        return {

            "object_id":
            self.object_id,

            "shape":
            self.classify_shape(),

            "symmetry":
            self.symmetry_score(),

            "complexity":
            self.semantic_complexity(),

            "symbolic_signature":
            self.symbolic_signature()
        }

    # ========================================
    # EXPORT SUMMARY
    # ========================================

    def summary(self):

        base_summary = (
            super().summary()
        )

        base_summary.update({

            "object_id":
            self.object_id,

            "shape":
            self.classify_shape(),

            "symmetry_score":
            self.symmetry_score(),

            "semantic_complexity":
            self.semantic_complexity(),

            "semantic_tags":
            self.semantic_tags,

            "relationship_count":
            len(self.relationships),

            "symbolic_profile":
            self.symbolic_profile
        })

        return base_summary

    # ========================================
    # REPRESENTATION
    # ========================================

    def __repr__(self):

        return (

            f"ARCObject("
            f"id={self.object_id}, "
            f"shape={self.classify_shape()}, "
            f"color={self.color}, "
            f"size={self.size()}"
            f")"
        )