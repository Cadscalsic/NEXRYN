# ============================================
# NEXRYN SEMANTIC MEMORY
# ============================================

from datetime import datetime

from core.context_discovery import ContextDiscoveryEngine
from core.causal_graph import CausalGraph
from core.causal_validation import CausalValidationEngine
from core.contextual_truth import ContextualTruthEngine
from core.context_hierarchy import ContextDifferentiationEngine, ContextHierarchy
from core.semantic_context import SemanticContextReasoner


# ============================================
# SEMANTIC MEMORY
# ============================================

class SemanticMemory:

    def __init__(self):

        self.knowledge_base = {}
        self.context_discovery_engine = ContextDiscoveryEngine()
        self.causal_graph = CausalGraph()
        self.causal_validation_engine = CausalValidationEngine()
        self.contextual_truth_engine = ContextualTruthEngine()
        self.context_hierarchy = ContextHierarchy()
        self.context_differentiation_engine = ContextDifferentiationEngine(
            self.context_hierarchy
        )
        self.semantic_context_reasoner = SemanticContextReasoner()

        self.semantic_state = {

            "memory_type":
            "semantic_memory",

            "knowledge_abstraction":
            "enabled",

            "symbolic_reasoning":
            "enabled",

            "transfer_learning":
            "enabled",

            "causal_graph_enrichment":
            "enabled",

            "causal_validation":
            "enabled",

            "contextual_truth":
            "enabled",

            "context_discovery":
            "enabled",

            "context_hierarchy":
            "enabled",

            "semantic_context":
            "enabled"
        }

    # ============================================
    # STORE CONCEPT
    # ============================================

    def store_concept(

        self,

        concept_name,

        concept_data
    ):

        self.knowledge_base[
            concept_name
        ] = {

            "concept":
            concept_data,

            "usage_count":
            0,

            "created_at":
            str(
                datetime.utcnow()
            )
        }
        if isinstance(concept_data, dict):
            context_discovery = self.context_discovery_engine.discover_context(
                concept_data.get("context", concept_data)
            )
            context_hierarchy = (
                self.context_differentiation_engine.refine_clusters([
                    context_discovery
                ])
            )
            semantic_context = (
                self.semantic_context_reasoner.generate_semantic_profile(
                    context_discovery,
                    concept_data.get("supporting_evidence", []),
                )
            )
            evidence = concept_data.get(
                "supporting_evidence",
                concept_data.get("evidence", []),
            )
            task_ids = concept_data.get(
                "originating_tasks",
                concept_data.get("task_ids", []),
            )
            confidence = concept_data.get(
                "confidence",
                concept_data.get("causal_alignment", 0.0),
            )
            if evidence or task_ids:
                self.causal_graph.build_causal_spine(
                    concept_name,
                    observations=evidence,
                    confidence=confidence,
                    originating_tasks=task_ids,
                    truth_claim=concept_data.get("truth_claim"),
                    context=concept_data.get("context", {}),
                )
                self.causal_validation_engine.validate_hypothesis(
                    {
                        "source_concept": concept_name,
                        "target_concept": concept_name,
                        "confidence": confidence,
                    },
                    evidence,
                    {
                        **concept_data.get("context", {}),
                        "causal_graph_alignment":
                        self.causal_graph.compute_causal_alignment(
                            concept_name
                        ),
                        "identity_compatibility":
                        concept_data.get("identity_compatibility", 1.0),
                    },
                    self.causal_graph,
                )
                contextual_report = (
                    self.contextual_truth_engine
                    .generate_contextual_truth_report(
                        concept_name,
                        {
                            **concept_data.get("context", {}),
                            "context_discovery": context_discovery,
                            "discovered_context_signature":
                            context_discovery["context_signature"],
                        },
                        self.causal_validation_engine
                        .generate_validation_report()
                        .get("hypotheses", [{}])[-1]
                        if self.causal_validation_engine
                        .generate_validation_report()
                        .get("hypotheses")
                        else {},
                        concept_data.get("identity_compatibility", 1.0),
                    )
                )
                self.knowledge_base[concept_name][
                    "supporting_contexts"
                ] = contextual_report.get("valid_contexts", [])
                self.knowledge_base[concept_name][
                    "rejecting_contexts"
                ] = contextual_report.get("invalid_contexts", [])
                self.knowledge_base[concept_name][
                    "context_confidence_history"
                ] = contextual_report.get(
                    "context_confidence_history",
                    [],
                )
                self.knowledge_base[concept_name][
                    "context_evolution_history"
                ] = contextual_report.get(
                    "context_evolution_history",
                    [],
                )
                self.knowledge_base[concept_name][
                    "discovered_context"
                ] = context_discovery
                self.knowledge_base[concept_name][
                    "context_hierarchy"
                ] = context_hierarchy
                self.knowledge_base[concept_name][
                    "semantic_context"
                ] = semantic_context
                self.knowledge_base[concept_name][
                    "semantic_context_profile"
                ] = semantic_context.get("semantic_profile", {})
                self.knowledge_base[concept_name][
                    "context_capabilities"
                ] = semantic_context.get("capabilities", [])
                self.knowledge_base[concept_name][
                    "context_constraints"
                ] = semantic_context.get("constraints", [])
                self.knowledge_base[concept_name][
                    "context_implications"
                ] = semantic_context.get("implications", [])
                self.knowledge_base[concept_name][
                    "property_confidence_history"
                ] = semantic_context.get("property_confidence_history", [])
                self.knowledge_base[concept_name][
                    "context_inheritance"
                ] = context_hierarchy.get("inheritance", [])
                self.knowledge_base[concept_name][
                    "context_distance_profile"
                ] = [
                    {
                        "context": node.get("context_name"),
                        "parent_context": node.get("parent_context"),
                    }
                    for node in context_hierarchy.get("contexts", [])
                ]

    # ============================================
    # RETRIEVE CONCEPT
    # ============================================

    def retrieve_concept(

        self,

        concept_name
    ):

        concept = self.knowledge_base.get(

            concept_name
        )

        if concept:

            concept[
                "usage_count"
            ] += 1

        return concept

    # ============================================
    # UPDATE CONCEPT
    # ============================================

    def update_concept(

        self,

        concept_name,

        new_data
    ):

        if concept_name in self.knowledge_base:

            self.knowledge_base[
                concept_name
            ]["concept"] = new_data

    # ============================================
    # CAUSAL EXPLANATION
    # ============================================

    def get_causal_explanation(

        self,

        concept_name
    ):

        return self.causal_graph.explain_truth(

            concept_name
        )

    def validate_causal_memory(self):

        return self.causal_graph.validate_causal_graph()

    def validate_causal_hypothesis(

        self,

        source_concept,

        target_concept,

        evidence=None,

        context=None
    ):

        return self.causal_validation_engine.validate_hypothesis(

            {
                "source_concept": source_concept,
                "target_concept": target_concept,
            },

            evidence or [],

            context or {},

            self.causal_graph
        )

    def get_contextual_truth_report(

        self,

        concept_name,

        context=None
    ):

        return self.contextual_truth_engine.generate_contextual_truth_report(

            concept_name,

            context or {}
        )

    # ============================================
    # MOST USED CONCEPTS
    # ============================================

    def most_used_concepts(

        self,

        limit=10
    ):

        concepts = sorted(

            self.knowledge_base.items(),

            key=lambda x: x[1][
                "usage_count"
            ],

            reverse=True
        )

        return concepts[:limit]

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        return {

            "memory_type":
            "semantic_memory",

            "concept_count":
            len(
                self.knowledge_base
            ),

            "most_used_concepts":

            [

                concept[0]

                for concept in

                self.most_used_concepts(
                    limit=5
                )
            ],

            "state":
            "stable",

            "causal_graph_validation":
            self.validate_causal_memory(),

            "causal_validation_report":
            self.causal_validation_engine.generate_validation_report(),

            "contextual_truth_report": {
                concept: self.contextual_truth_engine
                .generate_contextual_truth_report(concept)
                for concept in self.knowledge_base
            },

            "context_discovery_report":
            self.context_discovery_engine.cluster_contexts(),

            "context_hierarchy_report":
            self.context_hierarchy.report(),

            "semantic_context_report":
            self.semantic_context_reasoner.report()
        }
