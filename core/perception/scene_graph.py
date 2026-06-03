# ============================================
# NEXRYN COGNITIVE SCENE GRAPH
# ============================================

from datetime import datetime

from core.perception.relations import (
    SpatialRelations
)


# ============================================
# SCENE NODE
# ============================================

class SceneNode:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(

        self,

        node_id,

        arc_object
    ):

        self.node_id = node_id

        self.arc_object = arc_object

        self.created_at = (
            str(datetime.utcnow())
        )

        self.neighbors = []

        self.semantic_state = {

            "graph_entity":
            True,

            "scene_integrated":
            True,

            "relational_ready":
            True
        }

    # ========================================
    # ADD NEIGHBOR
    # ========================================

    def add_neighbor(

        self,

        neighbor_id
    ):

        if neighbor_id not in self.neighbors:

            self.neighbors.append(
                neighbor_id
            )

    # ========================================
    # EXPORT
    # ========================================

    def export(self):

        return {

            "node_id":
            self.node_id,

            "object_summary":
            self.arc_object.summary(),

            "neighbor_count":
            len(self.neighbors),

            "neighbors":
            self.neighbors,

            "semantic_state":
            self.semantic_state
        }

    # ========================================
    # REPRESENTATION
    # ========================================

    def __repr__(self):

        return (

            f"SceneNode("
            f"id={self.node_id}, "
            f"neighbors={len(self.neighbors)}"
            f")"
        )


# ============================================
# COGNITIVE SCENE GRAPH
# ============================================

class SceneGraph:

    """
    ============================================
    NEXRYN WORLD MODEL ENGINE
    Cognitive Relational Scene Runtime
    ============================================
    """

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(

        self,

        objects
    ):

        self.objects = objects

        self.nodes = {}

        self.relations = []

        self.graph_state = {

            "world_model":
            True,

            "relational_cognition":
            True,

            "scene_intelligence":
            True,

            "semantic_graph":
            True
        }

        self.graph_metadata = {

            "created_at":
            str(datetime.utcnow()),

            "relation_count":
            0,

            "node_count":
            0
        }

        self.build_graph()

    # ========================================
    # BUILD GRAPH
    # ========================================

    def build_graph(self):

        self._build_nodes()

        self._build_relations()

        self._connect_neighbors()

    # ========================================
    # BUILD NODES
    # ========================================

    def _build_nodes(self):

        for index, obj in enumerate(
            self.objects
        ):

            node_id = (
                f"object_{index}"
            )

            node = SceneNode(

                node_id=node_id,

                arc_object=obj
            )

            self.nodes[
                node_id
            ] = node

        self.graph_metadata[
            "node_count"
        ] = len(self.nodes)

    # ========================================
    # BUILD RELATIONS
    # ========================================

    def _build_relations(self):

        object_list = list(
            self.nodes.values()
        )

        for i in range(len(object_list)):

            for j in range(len(object_list)):

                if i == j:
                    continue

                node_a = object_list[i]
                node_b = object_list[j]

                relations = (

                    SpatialRelations
                    .build_relation_graph(

                        [

                            node_a.arc_object,

                            node_b.arc_object
                        ]
                    )
                )

                for relation in relations:

                    self.relations.append({

                        "source":
                        node_a.node_id,

                        "target":
                        node_b.node_id,

                        "relation":
                        relation
                    })

        self.graph_metadata[
            "relation_count"
        ] = len(self.relations)

    # ========================================
    # CONNECT NEIGHBORS
    # ========================================

    def _connect_neighbors(self):

        for relation_data in (
            self.relations
        ):

            source = relation_data[
                "source"
            ]

            target = relation_data[
                "target"
            ]

            self.nodes[
                source
            ].add_neighbor(
                target
            )

    # ========================================
    # FIND CENTRAL OBJECT
    # ========================================

    def find_central_object(self):

        if not self.nodes:
            return None

        return max(

            self.nodes.values(),

            key=lambda node:
            len(node.neighbors)
        )

    # ========================================
    # FIND ISOLATED OBJECTS
    # ========================================

    def find_isolated_objects(self):

        return [

            node

            for node in self.nodes.values()

            if len(node.neighbors) == 0
        ]

    # ========================================
    # BUILD SCENE SUMMARY
    # ========================================

    def scene_summary(self):

        central_node = (
            self.find_central_object()
        )

        return {

            "node_count":

            self.graph_metadata[
                "node_count"
            ],

            "relation_count":

            self.graph_metadata[
                "relation_count"
            ],

            "isolated_objects":

            len(
                self.find_isolated_objects()
            ),

            "central_object":

            central_node.node_id

            if central_node
            else None,

            "graph_state":
            self.graph_state
        }

    # ========================================
    # EXPORT GRAPH
    # ========================================

    def export(self):

        return {

            "scene_summary":
            self.scene_summary(),

            "nodes": {

                node_id:
                node.export()

                for node_id, node
                in self.nodes.items()
            },

            "relations": [

                {

                    "source":
                    relation["source"],

                    "target":
                    relation["target"],

                    "relation":

                    relation[
                        "relation"
                    ].export()
                }

                for relation in self.relations
            ]
        }

    # ========================================
    # REPRESENTATION
    # ========================================

    def __repr__(self):

        summary = (
            self.scene_summary()
        )

        return (

            f"SceneGraph("
            f"nodes={summary['node_count']}, "
            f"relations="
            f"{summary['relation_count']}"
            f")"
        )