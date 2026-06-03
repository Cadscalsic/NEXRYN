# ============================================
# NEXRYN HIERARCHICAL CONTEXT CONSOLIDATOR
# ============================================

from datetime import datetime


# ============================================
# HIERARCHICAL CONTEXT CONSOLIDATOR
# ============================================

class HierarchicalContextConsolidator:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # CONSOLIDATION STATE
        # ====================================

        self.consolidation_state = {

            "hierarchical_compression":
            True,

            "semantic_clustering":
            True,

            "recursive_pruning":
            True,

            "abstraction_fusion":
            True,

            "compression_cycles":
            0
        }

        # ====================================
        # CONSOLIDATION HISTORY
        # ====================================

        self.consolidation_history = []

    # ========================================
    # BUILD SEMANTIC SUMMARY
    # ========================================

    def build_semantic_summary(

        self,

        runtime_context
    ):

        semantic_graph = (

            runtime_context.get(
                "semantic_graph"
            )

            or {}
        )

        concept_nodes = (

            semantic_graph.get(
                "concept_nodes",
                []
            )
        )

        concepts = []

        for node in concept_nodes:

            concept = node.get(
                "concept"
            )

            if concept:

                concepts.append(
                    concept
                )

        return {

            "summary_type":
            "semantic_hierarchy",

            "concept_count":
            len(concepts),

            "core_concepts":
            concepts[:5],

            "generated_at":
            str(datetime.utcnow())
        }

    # ========================================
    # BUILD REASONING SUMMARY
    # ========================================

    def build_reasoning_summary(

        self,

        runtime_context
    ):

        inference_report = (

            runtime_context.get(
                "inference_report"
            )

            or {}
        )

        return {

            "reasoning_depth":
            inference_report.get(
                "reasoning_depth",
                0
            ),

            "global_confidence":
            inference_report.get(
                "global_confidence",
                0.0
            ),

            "search_paths":
            inference_report.get(
                "search_path_count",
                0
            ),

            "cognitive_pressure":
            inference_report.get(
                "cognitive_pressure",
                0.0
            )
        }

    # ========================================
    # BUILD EXECUTION SUMMARY
    # ========================================

    def build_execution_summary(

        self,

        runtime_context
    ):

        evaluation_result = (

            runtime_context.get(
                "evaluation_result"
            )

            or {}
        )

        return {

            "accuracy":
            evaluation_result.get(
                "accuracy",
                0.0
            ),

            "success":
            evaluation_result.get(
                "success",
                False
            ),

            "final_score":
            evaluation_result.get(
                "final_score",
                0.0
            )
        }

    # ========================================
    # CONSOLIDATE CONTEXT
    # ========================================

    def consolidate_context(

        self,

        runtime_context
    ):

        semantic_summary = (

            self.build_semantic_summary(
                runtime_context
            )
        )

        reasoning_summary = (

            self.build_reasoning_summary(
                runtime_context
            )
        )

        execution_summary = (

            self.build_execution_summary(
                runtime_context
            )
        )

        consolidated = {

            "semantic_summary":
            semantic_summary,

            "reasoning_summary":
            reasoning_summary,

            "execution_summary":
            execution_summary,

            "compression_timestamp":
            str(datetime.utcnow())
        }

        runtime_context[
            "hierarchical_context_summary"
        ] = consolidated

        self.consolidation_history.append({

            "context_size":
            len(runtime_context),

            "timestamp":
            str(datetime.utcnow())
        })

        self.consolidation_state[
            "compression_cycles"
        ] += 1

        return runtime_context

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "compression_cycles":
            self.consolidation_state[
                "compression_cycles"
            ],

            "history_size":
            len(
                self.consolidation_history
            ),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL CONSOLIDATOR
# ============================================

hierarchical_context_consolidator = (
    HierarchicalContextConsolidator()
)