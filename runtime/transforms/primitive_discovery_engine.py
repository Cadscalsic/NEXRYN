# ============================================
# NEXRYN PRIMITIVE DISCOVERY ENGINE
# EXECUTABLE SPATIAL OPERATOR DISCOVERY
# ============================================

from datetime import datetime

import numpy as np


# ============================================
# PRIMITIVE DISCOVERY ENGINE
# ============================================

class PrimitiveDiscoveryEngine:

    # ========================================
    # INITIALIZATION
    # ========================================

    def __init__(self):

        self.discovery_history = []

        self.primitive_statistics = {}

        self.operator_memory = []

        self.discovery_failures = []

    # ========================================
    # SAFE REPORTS
    # ========================================

    def safe_reports(
        self,
        reports
    ):

        if reports is None:

            return []

        if not isinstance(
            reports,
            list
        ):

            return []

        return reports

    # ========================================
    # REGISTER PRIMITIVE
    # ========================================

    def register_primitive(
        self,
        primitive
    ):

        if primitive not in (
            self.primitive_statistics
        ):

            self.primitive_statistics[
                primitive
            ] = 0

        self.primitive_statistics[
            primitive
        ] += 1

    # ========================================
    # BUILD PRIMITIVE
    # ========================================

    def build_primitive(

        self,

        primitive_name,

        primitive_type,

        confidence,

        source_reasoning,

        parameters=None
    ):

        primitive = {

            "primitive":
            primitive_name,

            "primitive_type":
            primitive_type,

            "confidence":
            round(
                confidence,
                4
            ),

            "execution_score":
            round(
                confidence * 0.95,
                4
            ),

            "source_reasoning":
            source_reasoning,

            "parameters":
            parameters or {},

            "timestamp":
            str(datetime.utcnow())
        }

        self.register_primitive(
            primitive_name
        )

        return primitive

    # ========================================
    # OBJECT DUPLICATION
    # ========================================

    def discover_object_duplication(

        self,
        report
    ):

        operator = report.get(
            "operator"
        )

        if operator != "duplicate_object":

            return None

        delta = report.get(
            "delta",
            0
        )

        if delta <= 0:

            return None

        return self.build_primitive(

            primitive_name=
            "duplicate_object",

            primitive_type=
            "object_operator",

            confidence=
            report.get(
                "confidence",
                0.9
            ),

            source_reasoning=
            report,

            parameters={

                "duplication_count":
                delta
            }
        )

    # ========================================
    # OBJECT REMOVAL
    # ========================================

    def discover_object_removal(

        self,
        report
    ):

        operator = report.get(
            "operator"
        )

        if operator != "remove_object":

            return None

        delta = report.get(
            "delta",
            0
        )

        if delta >= 0:

            return None

        return self.build_primitive(

            primitive_name=
            "remove_object",

            primitive_type=
            "object_operator",

            confidence=
            report.get(
                "confidence",
                0.88
            ),

            source_reasoning=
            report,

            parameters={

                "removal_count":
                abs(delta)
            }
        )

    # ========================================
    # OBJECT EXPANSION
    # ========================================

    def discover_object_expansion(

        self,
        report
    ):

        operator = report.get(
            "operator"
        )

        if operator not in [

            "expand_object",
            "shrink_object"
        ]:

            return None

        return self.build_primitive(

            primitive_name=
            operator,

            primitive_type=
            "object_operator",

            confidence=
            report.get(
                "confidence",
                0.9
            ),

            source_reasoning=
            report,

            parameters={

                "size_delta":
                report.get(
                    "delta",
                    0
                )
            }
        )

    # ========================================
    # SHAPE EXPANSION
    # ========================================

    def discover_shape_expansion(

        self,
        report
    ):

        operator = report.get(
            "operator"
        )

        if operator not in [

            "expand_grid",
            "horizontal_expansion",
            "vertical_expansion"
        ]:

            return None

        return self.build_primitive(

            primitive_name=
            operator,

            primitive_type=
            "shape_operator",

            confidence=
            report.get(
                "confidence",
                0.92
            ),

            source_reasoning=
            report,

            parameters={

                "height_growth":
                report.get(
                    "height_growth",
                    0
                ),

                "width_growth":
                report.get(
                    "width_growth",
                    0
                )
            }
        )

    # ========================================
    # GRID SHRINK
    # ========================================

    def discover_grid_shrink(

        self,
        report
    ):

        operator = report.get(
            "operator"
        )

        if operator != "shrink_grid":

            return None

        return self.build_primitive(

            primitive_name=
            "shrink_grid",

            primitive_type=
            "shape_operator",

            confidence=
            report.get(
                "confidence",
                0.88
            ),

            source_reasoning=
            report
        )

    # ========================================
    # TRANSLATION
    # ========================================

    def discover_translation(

        self,
        report
    ):

        operator = report.get(
            "operator"
        )

        valid = [

            "translate_left",
            "translate_right",
            "translate_up",
            "translate_down"
        ]

        if operator not in valid:

            return None

        return self.build_primitive(

            primitive_name=
            operator,

            primitive_type=
            "translation_operator",

            confidence=
            report.get(
                "confidence",
                0.91
            ),

            source_reasoning=
            report,

            parameters={

                "translation":
                report.get(
                    "dominant_translation"
                )
            }
        )

    # ========================================
    # COLOR REPLACEMENT
    # ========================================

    def discover_color_replacement(

        self,
        report
    ):

        operator = report.get(
            "operator"
        )

        if operator != "replace_color":

            return None

        return self.build_primitive(

            primitive_name=
            "replace_color",

            primitive_type=
            "color_operator",

            confidence=
            report.get(
                "confidence",
                0.90
            ),

            source_reasoning=
            report,

            parameters={

                "added_colors":
                report.get(
                    "added_colors",
                    []
                ),

                "removed_colors":
                report.get(
                    "removed_colors",
                    []
                )
            }
        )

    # ========================================
    # PATTERN EXPANSION
    # ========================================

    def discover_pattern_expansion(

        self,
        report
    ):

        operator = report.get(
            "operator"
        )

        if operator != "expand_pattern":

            return None

        return self.build_primitive(

            primitive_name=
            "expand_pattern",

            primitive_type=
            "pattern_operator",

            confidence=
            report.get(
                "confidence",
                0.91
            ),

            source_reasoning=
            report,

            parameters={

                "density_delta":
                report.get(
                    "density_delta",
                    0
                )
            }
        )

    # ========================================
    # TOPOLOGY GROWTH
    # ========================================

    def discover_topology_growth(

        self,
        report
    ):

        operator = report.get(
            "operator"
        )

        if operator != "grow_topology":

            return None

        return self.build_primitive(

            primitive_name=
            "grow_topology",

            primitive_type=
            "topology_operator",

            confidence=
            report.get(
                "confidence",
                0.89
            ),

            source_reasoning=
            report
        )

    # ========================================
    # SYMMETRY
    # ========================================

    def discover_symmetry_operator(

        self,
        report
    ):

        operator = report.get(
            "operator"
        )

        if operator != "modify_symmetry":

            return None

        return self.build_primitive(

            primitive_name=
            "mirror_object",

            primitive_type=
            "symmetry_operator",

            confidence=
            report.get(
                "confidence",
                0.84
            ),

            source_reasoning=
            report
        )

    # ========================================
    # DISCOVER FROM REPORT
    # ========================================

    def discover_from_report(
        self,
        report
    ):

        primitives = []

        discovery_functions = [

            self.discover_object_duplication,
            self.discover_object_removal,
            self.discover_object_expansion,
            self.discover_shape_expansion,
            self.discover_grid_shrink,
            self.discover_translation,
            self.discover_color_replacement,
            self.discover_pattern_expansion,
            self.discover_topology_growth,
            self.discover_symmetry_operator
        ]

        for function in discovery_functions:

            try:

                primitive = function(
                    report
                )

                if primitive is not None:

                    primitives.append(
                        primitive
                    )

            except Exception as error:

                self.discovery_failures.append({

                    "function":
                    function.__name__,

                    "error":
                    repr(error),

                    "timestamp":
                    str(datetime.utcnow())
                })

        return primitives

    # ========================================
    # RANK PRIMITIVES
    # ========================================

    def rank_primitives(
        self,
        primitives
    ):

        ranked = sorted(

            primitives,

            key=lambda x: (

                x.get(
                    "execution_score",
                    0.0
                ),

                x.get(
                    "confidence",
                    0.0
                )
            ),

            reverse=True
        )

        return ranked

    # ========================================
    # SELECT EXECUTABLE PRIMITIVES
    # ========================================

    def select_executable_primitives(
        self,
        ranked_primitives
    ):

        selected = []

        selected_names = set()

        primitive_names = [

            primitive.get(
                "primitive"
            )

            for primitive in ranked_primitives
        ]

        broad_growth_blocked = any(

            name in [

                "duplicate_object",
                "expand_object",
                "shrink_object"
            ]

            for name in primitive_names
        )

        object_count_changed = any(

            name in [

                "duplicate_object",
                "remove_object"
            ]

            for name in primitive_names
        )

        for primitive in ranked_primitives:

            primitive_name = primitive.get(
                "primitive"
            )

            if primitive_name in selected_names:

                continue

            if (

                primitive_name in [

                    "expand_object",
                    "shrink_object"
                ]

                and

                object_count_changed
            ):

                continue

            if (

                primitive_name in [

                    "expand_pattern",
                    "grow_topology"
                ]

                and

                broad_growth_blocked
            ):

                continue

            selected.append(
                primitive
            )

            selected_names.add(
                primitive_name
            )

        return selected

    # ========================================
    # BUILD EXECUTION GRAPH
    # ========================================

    def build_execution_graph(
        self,
        primitives
    ):

        nodes = []

        edges = []

        for index, primitive in enumerate(
            primitives
        ):

            node = {

                "node_id":
                index,

                "primitive":
                primitive.get(
                    "primitive"
                ),

                "primitive_type":
                primitive.get(
                    "primitive_type"
                ),

                "confidence":
                primitive.get(
                    "confidence"
                )
            }

            nodes.append(
                node
            )

            if index > 0:

                edges.append({

                    "source":
                    index - 1,

                    "target":
                    index,

                    "relation":
                    "execution_flow"
                })

        return {

            "nodes":
            nodes,

            "edges":
            edges,

            "node_count":
            len(nodes),

            "edge_count":
            len(edges)
        }

    # ========================================
    # BUILD DISCOVERY REPORT
    # ========================================

    def build_discovery_report(

        self,

        ranked_primitives,

        execution_graph
    ):

        top_primitive = None

        if ranked_primitives:

            top_primitive = (

                ranked_primitives[0]
                .get(
                    "primitive"
                )
            )

        return {

            "discovered_primitives":
            len(ranked_primitives),

            "top_primitive":
            top_primitive,

            "execution_nodes":
            execution_graph.get(
                "node_count",
                0
            ),

            "execution_edges":
            execution_graph.get(
                "edge_count",
                0
            ),

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # RUN DISCOVERY
    # ========================================

    def run_discovery(
        self,
        reasoning_reports
    ):

        reasoning_reports = (
            self.safe_reports(
                reasoning_reports
            )
        )

        discovered_primitives = []

        for report in reasoning_reports:

            primitives = (

                self.discover_from_report(
                    report
                )
            )

            discovered_primitives.extend(
                primitives
            )

        # ====================================
        # RANKING
        # ====================================

        ranked_primitives = (
            self.rank_primitives(
                discovered_primitives
            )
        )

        ranked_primitives = (
            self.select_executable_primitives(
                ranked_primitives
            )
        )

        # ====================================
        # EXECUTION GRAPH
        # ====================================

        execution_graph = (
            self.build_execution_graph(
                ranked_primitives
            )
        )

        # ====================================
        # MEMORY
        # ====================================

        self.discovery_history.append(
            ranked_primitives
        )

        self.operator_memory.append(
            execution_graph
        )

        # ====================================
        # FINAL REPORT
        # ====================================

        discovery_report = (

            self.build_discovery_report(

                ranked_primitives,

                execution_graph
            )
        )

        return {

            "ranked_primitives":
            ranked_primitives,

            "execution_graph":
            execution_graph,

            "discovery_report":
            discovery_report
        }


# ============================================
# GLOBAL ENGINE
# ============================================

primitive_discovery_engine = (
    PrimitiveDiscoveryEngine()
)
