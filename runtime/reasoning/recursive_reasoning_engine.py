# ============================================
# NEXRYN RECURSIVE REASONING ENGINE
# ============================================

from datetime import datetime

import copy


# ============================================
# RECURSIVE REASONING ENGINE
# ============================================

class RecursiveReasoningEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        self.recursive_history = []

        self.recursive_paths = []

        self.engine_state = {

            "recursive_expansion":
            True,

            "hierarchical_reasoning":
            True,

            "multi_depth_reasoning":
            True,

            "self_reflection":
            True,

            "recursive_refinement":
            True
        }

    # ========================================
    # BUILD RECURSIVE PATH
    # ========================================

    def build_recursive_path(

        self,

        hypotheses,

        depth
    ):

        recursive_nodes = []

        for index, hypothesis in enumerate(
            hypotheses
        ):

            recursive_node = {

                "depth":
                depth,

                "node_index":
                index,

                "reasoning_type":

                hypothesis.get(
                    "type",
                    "unknown"
                ),

                "confidence":

                hypothesis.get(
                    "confidence",
                    0.0
                ),

                "recursive_state":
                "active"
            }

            recursive_nodes.append(
                recursive_node
            )

        return recursive_nodes

    # ========================================
    # RECURSIVE EXPANSION
    # ========================================

    def recursive_expand(

        self,

        hypotheses,

        max_depth=3
    ):

        recursive_paths = []

        for depth in range(max_depth):

            recursive_path = (

                self.build_recursive_path(

                    hypotheses,

                    depth
                )
            )

            recursive_paths.append({

                "depth":
                depth,

                "nodes":
                recursive_path,

                "node_count":
                len(recursive_path)
            })

        return recursive_paths

    # ========================================
    # BUILD HIERARCHY REPORT
    # ========================================

    def build_hierarchy_report(

        self,

        recursive_paths
    ):

        hierarchy_levels = {

            "low_level":
            0,

            "mid_level":
            0,

            "high_level":
            0,

            "meta_level":
            0
        }

        for path in recursive_paths:

            depth = path.get(
                "depth",
                0
            )

            if depth == 0:

                hierarchy_levels[
                    "low_level"
                ] += 1

            elif depth == 1:

                hierarchy_levels[
                    "mid_level"
                ] += 1

            elif depth == 2:

                hierarchy_levels[
                    "high_level"
                ] += 1

            else:

                hierarchy_levels[
                    "meta_level"
                ] += 1

        return hierarchy_levels

    # ========================================
    # BUILD RECURSIVE REPORT
    # ========================================

    def build_recursive_report(

        self,

        hypotheses,

        max_depth=3
    ):

        # ====================================
        # BUILD PATHS
        # ====================================

        recursive_paths = (

            self.recursive_expand(

                hypotheses,

                max_depth
            )
        )

        # ====================================
        # BUILD HIERARCHY
        # ====================================

        hierarchy_report = (

            self.build_hierarchy_report(

                recursive_paths
            )
        )

        # ====================================
        # BUILD REPORT
        # ====================================

        report = {

            "recursive_depth":
            max_depth,

            "path_count":
            len(recursive_paths),

            "recursive_paths":
            recursive_paths,

            "hierarchy_levels":
            hierarchy_report,

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.recursive_history.append(
            copy.deepcopy(report)
        )

        self.recursive_paths.extend(
            recursive_paths
        )

        return report

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_report = {}

        if self.recursive_history:

            latest_report = (

                self.recursive_history[-1]
            )

        return {

            "recursive_cycles":

            len(
                self.recursive_history
            ),

            "stored_paths":

            len(
                self.recursive_paths
            ),

            "engine_state":
            self.engine_state,

            "latest_report":
            latest_report
        }


# ============================================
# GLOBAL ENGINE
# ============================================

recursive_reasoning_engine = (
    RecursiveReasoningEngine()
)