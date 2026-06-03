# ============================================
# NEXRYN RELATIONAL COGNITION SYSTEM
# ============================================

import math

from datetime import datetime


# ============================================
# RELATION ENTITY
# ============================================

class RelationEntity:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(

        self,

        relation_type,

        source_object,

        target_object,

        confidence=1.0,

        metadata=None
    ):

        self.relation_type = (
            relation_type
        )

        self.source_object = (
            source_object
        )

        self.target_object = (
            target_object
        )

        self.confidence = round(
            confidence,
            4
        )

        self.metadata = (
            metadata or {}
        )

        self.created_at = (
            str(datetime.utcnow())
        )

    # ========================================
    # EXPORT
    # ========================================

    def export(self):

        return {

            "relation_type":
            self.relation_type,

            "source":
            str(self.source_object),

            "target":
            str(self.target_object),

            "confidence":
            self.confidence,

            "metadata":
            self.metadata,

            "timestamp":
            self.created_at
        }

    # ========================================
    # REPRESENTATION
    # ========================================

    def __repr__(self):

        return (

            f"Relation("
            f"{self.relation_type}, "
            f"confidence={self.confidence}"
            f")"
        )


# ============================================
# SPATIAL RELATIONS
# ============================================

class SpatialRelations:

    """
    ============================================
    NEXRYN RELATIONAL COGNITION ENGINE
    Symbolic Spatial Intelligence Runtime
    ============================================
    """

    # ========================================
    # LEFT RELATION
    # ========================================

    @staticmethod
    def left_of(

        obj_a,

        obj_b
    ):

        result = (

            obj_a.centroid()["col"]
            <
            obj_b.centroid()["col"]
        )

        if not result:
            return None

        return RelationEntity(

            relation_type="left_of",

            source_object=obj_a,

            target_object=obj_b,

            confidence=1.0
        )

    # ========================================
    # RIGHT RELATION
    # ========================================

    @staticmethod
    def right_of(

        obj_a,

        obj_b
    ):

        result = (

            obj_a.centroid()["col"]
            >
            obj_b.centroid()["col"]
        )

        if not result:
            return None

        return RelationEntity(

            relation_type="right_of",

            source_object=obj_a,

            target_object=obj_b
        )

    # ========================================
    # ABOVE RELATION
    # ========================================

    @staticmethod
    def above(

        obj_a,

        obj_b
    ):

        result = (

            obj_a.centroid()["row"]
            <
            obj_b.centroid()["row"]
        )

        if not result:
            return None

        return RelationEntity(

            relation_type="above",

            source_object=obj_a,

            target_object=obj_b
        )

    # ========================================
    # BELOW RELATION
    # ========================================

    @staticmethod
    def below(

        obj_a,

        obj_b
    ):

        result = (

            obj_a.centroid()["row"]
            >
            obj_b.centroid()["row"]
        )

        if not result:
            return None

        return RelationEntity(

            relation_type="below",

            source_object=obj_a,

            target_object=obj_b
        )

    # ========================================
    # SAME COLOR
    # ========================================

    @staticmethod
    def same_color(

        obj_a,

        obj_b
    ):

        if obj_a.color != obj_b.color:

            return None

        return RelationEntity(

            relation_type="same_color",

            source_object=obj_a,

            target_object=obj_b
        )

    # ========================================
    # SAME SHAPE
    # ========================================

    @staticmethod
    def same_shape(

        obj_a,

        obj_b
    ):

        if (

            obj_a.classify_shape()
            !=
            obj_b.classify_shape()
        ):

            return None

        return RelationEntity(

            relation_type="same_shape",

            source_object=obj_a,

            target_object=obj_b
        )

    # ========================================
    # DISTANCE
    # ========================================

    @staticmethod
    def euclidean_distance(

        obj_a,

        obj_b
    ):

        row_distance = (

            obj_a.centroid()["row"]
            -
            obj_b.centroid()["row"]
        )

        col_distance = (

            obj_a.centroid()["col"]
            -
            obj_b.centroid()["col"]
        )

        distance = math.sqrt(

            row_distance ** 2
            +
            col_distance ** 2
        )

        return RelationEntity(

            relation_type=
            "euclidean_distance",

            source_object=obj_a,

            target_object=obj_b,

            confidence=1.0,

            metadata={

                "distance":
                round(distance, 4)
            }
        )

    # ========================================
    # TOUCHING
    # ========================================

    @staticmethod
    def touching(

        obj_a,

        obj_b
    ):

        cells_a = set(
            obj_a.cells
        )

        cells_b = set(
            obj_b.cells
        )

        directions = [

            (-1, 0),
            (1, 0),

            (0, -1),
            (0, 1)
        ]

        for row, col in cells_a:

            for dr, dc in directions:

                neighbor = (
                    row + dr,
                    col + dc
                )

                if neighbor in cells_b:

                    return RelationEntity(

                        relation_type=
                        "touching",

                        source_object=obj_a,

                        target_object=obj_b
                    )

        return None

    # ========================================
    # BUILD RELATION GRAPH
    # ========================================

    @staticmethod
    def build_relation_graph(

        objects
    ):

        relations = []

        relation_functions = [

            SpatialRelations.left_of,

            SpatialRelations.right_of,

            SpatialRelations.above,

            SpatialRelations.below,

            SpatialRelations.same_color,

            SpatialRelations.same_shape,

            SpatialRelations.touching,

            SpatialRelations.euclidean_distance
        ]

        for i in range(len(objects)):

            for j in range(len(objects)):

                if i == j:
                    continue

                obj_a = objects[i]
                obj_b = objects[j]

                for relation_function in (
                    relation_functions
                ):

                    relation = (

                        relation_function(

                            obj_a,
                            obj_b
                        )
                    )

                    if relation:

                        relations.append(
                            relation
                        )

        return relations

    # ========================================
    # EXPORT GRAPH
    # ========================================

    @staticmethod
    def export_graph(

        relations
    ):

        return [

            relation.export()

            for relation in relations
        ]