# ============================================
# NEXRYN EXECUTION GRAPH
# ============================================

from datetime import datetime


# ============================================
# EXECUTION GRAPH
# ============================================

class ExecutionGraph:

    def __init__(self):

        # ====================================
        # GRAPH NODES
        # ====================================

        self.nodes = {}

        # ====================================
        # GRAPH EDGES
        # ====================================

        self.edges = {}

        # ====================================
        # EXECUTION METRICS
        # ====================================

        self.metrics = {

            "nodes":
            0,

            "edges":
            0,

            "cycles_detected":
            0,

            "executions":
            0,

            "graph_health":
            "stable"
        }

        # ====================================
        # EXECUTION HISTORY
        # ====================================

        self.execution_history = []

    # ============================================
    # ADD NODE
    # ============================================

    def add_node(

        self,

        stage_name,

        priority="medium"
    ):

        if stage_name not in self.nodes:

            self.nodes[
                stage_name
            ] = {

                "name":
                stage_name,

                "visited":
                False,

                "active":
                True,

                "priority":
                priority,

                "execution_count":
                0,

                "last_execution":
                None
            }

            self.edges[
                stage_name
            ] = []

            self.metrics[
                "nodes"
            ] += 1

    # ============================================
    # ADD EDGE
    # ============================================

    def add_edge(

        self,

        source_stage,

        target_stage,

        weight=1.0
    ):

        self.add_node(
            source_stage
        )

        self.add_node(
            target_stage
        )

        # ====================================
        # PREVENT DUPLICATES
        # ====================================

        existing_targets = [

            edge["target"]

            for edge in self.edges[
                source_stage
            ]
        ]

        if target_stage not in existing_targets:

            self.edges[
                source_stage
            ].append({

                "target":
                target_stage,

                "weight":
                weight
            })

            self.metrics[
                "edges"
            ] += 1

    # ============================================
    # GET NEXT STAGES
    # ============================================

    def get_next_stages(

        self,

        stage_name
    ):

        next_edges = self.edges.get(

            stage_name,

            []
        )

        return [

            edge["target"]

            for edge in next_edges
        ]

    # ============================================
    # HAS NODE
    # ============================================

    def has_node(

        self,

        stage_name
    ):

        return (
            stage_name in self.nodes
        )

    # ============================================
    # CONNECTION EXISTS
    # ============================================

    def connection_exists(

        self,

        source_stage,

        target_stage
    ):

        for edge in self.edges.get(

            source_stage,

            []
        ):

            if edge["target"] == target_stage:

                return True

        return False

    # ============================================
    # MARK VISITED
    # ============================================

    def mark_visited(

        self,

        stage_name
    ):

        if self.has_node(
            stage_name
        ):

            self.nodes[
                stage_name
            ]["visited"] = True

            self.nodes[
                stage_name
            ]["execution_count"] += 1

            self.nodes[
                stage_name
            ]["last_execution"] = str(
                datetime.utcnow()
            )

            self.metrics[
                "executions"
            ] += 1

    # ============================================
    # RESET VISITS
    # ============================================

    def reset_visits(self):

        for stage_name in (

            self.nodes.keys()
        ):

            self.nodes[
                stage_name
            ]["visited"] = False

    # ============================================
    # DETECT CYCLES
    # ============================================

    def detect_cycles(self):

        visited = set()

        recursion_stack = set()

        def visit(node):

            visited.add(node)

            recursion_stack.add(node)

            for edge in self.edges.get(

                node,

                []
            ):

                neighbor = edge["target"]

                if neighbor not in visited:

                    if visit(neighbor):

                        return True

                elif neighbor in recursion_stack:

                    return True

            recursion_stack.remove(node)

            return False

        for node in self.nodes:

            if node not in visited:

                if visit(node):

                    self.metrics[
                        "cycles_detected"
                    ] += 1

                    self.metrics[
                        "graph_health"
                    ] = "cyclic"

                    return True

        return False

    # ============================================
    # GET EXECUTION ORDER
    # ============================================

    def get_execution_order(self):

        if self.detect_cycles():

            return []

        visited = set()

        ordering = []

        def dfs(node):

            visited.add(node)

            for edge in self.edges.get(

                node,

                []
            ):

                neighbor = edge["target"]

                if neighbor not in visited:

                    dfs(neighbor)

            ordering.append(node)

        for node in self.nodes:

            if node not in visited:

                dfs(node)

        ordering.reverse()

        return ordering

    # ============================================
    # GRAPH HEALTH CHECK
    # ============================================

    def health_check(self):

        healthy = True

        if self.metrics[
            "cycles_detected"
        ] > 0:

            healthy = False

        return {

            "healthy":
            healthy,

            "graph_health":
            self.metrics[
                "graph_health"
            ],

            "nodes":
            self.metrics[
                "nodes"
            ],

            "edges":
            self.metrics[
                "edges"
            ]
        }

    # ============================================
    # GET ALL NODES
    # ============================================

    def get_nodes(self):

        return list(
            self.nodes.keys()
        )

    # ============================================
    # GET ALL EDGES
    # ============================================

    def get_edges(self):

        return self.edges

    # ============================================
    # BUILD GRAPH REPORT
    # ============================================

    def build_graph_report(self):

        return {

            "metrics":
            self.metrics,

            "health":
            self.health_check(),

            "execution_order":
            self.get_execution_order(),

            "node_count":
            len(
                self.nodes
            ),

            "edge_count":
            len(
                self.edges
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

    # ============================================
    # PRINT GRAPH
    # ============================================

    def print_graph(self):

        print(
            "\n=================================================="
        )

        print(
            "NEXRYN :: EXECUTION GRAPH"
        )

        print(
            "==================================================\n"
        )

        for source, targets in (

            self.edges.items()
        ):

            formatted_targets = [

                edge["target"]

                for edge in targets
            ]

            print(
                f"{source} -> {formatted_targets}"
            )

        print()