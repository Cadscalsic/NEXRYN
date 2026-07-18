# ============================================
# NEXRYN INTROSPECTION ENGINE
# ============================================

from runtime.semantics.semantic_abstraction import (
    SemanticAbstractionEngine,
)


# ============================================
# INTROSPECTION ENGINE
# ============================================

class IntrospectionEngine:

    def __init__(self):

        self.introspection_history = []
        self.semantic_abstraction_engine = SemanticAbstractionEngine()

    # ============================================
    # ANALYZE COGNITIVE CYCLE
    # ============================================

    def analyze_cycle(

        self,

        cognitive_cycle,

        evaluation_result,

        runtime_context=None
    ):

        reasoning = cognitive_cycle.get(
            "reasoning",
            {}
        )

        goals = cognitive_cycle.get(
            "goals",
            {}
        )

        semantics = cognitive_cycle.get(
            "semantics",
            {}
        )

        routing = cognitive_cycle.get(
            "routing",
            {}
        )

        control = cognitive_cycle.get(
            "control",
            {}
        )

        execution = cognitive_cycle.get(
            "execution",
            {}
        )

        contextual_concepts = (
            self.semantic_abstraction_engine
            .extract_contextual_concepts(
                runtime_context
            )
        )

        semantic_concept_count = semantics.get(
            "concept_count",
            0
        )

        if semantic_concept_count == 0:

            semantic_concept_count = contextual_concepts.get(
                "concept_count",
                0
            )

        inferred_activity = self._infer_pipeline_activity(
            runtime_context
        )
        reasoning_depth = reasoning.get(
            "reasoning_depth",
            0
        ) or inferred_activity.get(
            "reasoning_depth",
            0
        )
        route_count = routing.get(
            "route_count",
            0
        ) or inferred_activity.get(
            "route_count",
            0
        )
        execution_nodes = execution.get(
            "node_count",
            0
        ) or inferred_activity.get(
            "execution_nodes",
            0
        )

        introspection_report = {

            "reasoning_depth":
            reasoning_depth,

            "cognitive_complexity":
            reasoning.get(
                "cognitive_complexity",
                "unknown"
            ),

            "goal_confidence":
            goals.get(
                "confidence",
                0.0
            ),

            "semantic_concept_count":
            semantic_concept_count,

            "attributed_concepts":
            contextual_concepts.get(
                "concepts",
                []
            ),

            "semantic_attribution_evidence":
            self._compact_semantic_evidence(
                contextual_concepts.get(
                    "evidence",
                    {}
                )
            ),

            "semantic_attribution_source":
            contextual_concepts.get(
                "source"
            ),

            "active_routes":
            route_count,

            "execution_nodes":
            execution_nodes,

            "pipeline_activity":
            inferred_activity,

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

            "success_state":
            evaluation_result.get(
                "success_state",
                "FAILURE"
            ),

            "partial_success":
            evaluation_result.get(
                "partial_success",
                False
            )
        }

        return introspection_report

    def _infer_pipeline_activity(self, runtime_context):

        context = runtime_context if isinstance(runtime_context, dict) else {}

        activity_keys = (
            "task_loaded",
            "input_summary",
            "output_summary",
            "pattern_analysis",
            "pattern_analysis_report",
            "rule_analysis",
            "rule_analysis_report",
            "goal_arbitration",
            "goal_arbitration_report",
            "prediction_report",
            "predicted_output",
            "evaluation_result",
            "residual_analysis",
            "semantic_attribution_report",
        )
        active_stages = [
            key
            for key in activity_keys
            if context.get(key) is not None
        ]

        enabled_tools = context.get(
            "enabled_tools",
            []
        )
        if not isinstance(enabled_tools, (list, tuple, set)):
            enabled_tools = []

        execution_nodes = len([
            key
            for key in (
                "predicted_output",
                "prediction_report",
                "evaluation_result",
                "residual_analysis",
            )
            if context.get(key) is not None
        ])

        return {
            "active_stages": active_stages,
            "reasoning_depth": len(active_stages),
            "route_count": len(enabled_tools),
            "execution_nodes": execution_nodes,
        }

    # ============================================
    # BUILD INSIGHTS
    # ============================================

    def build_insights(

        self,

        introspection_report
    ):

        insights = []

        if introspection_report[
            "accuracy"
        ] < 1.0:

            insights.append(

                "Cognition requires improvement"
            )

        if introspection_report[
            "reasoning_depth"
        ] > 15:

            insights.append(

                "Reasoning depth is high"
            )

        if introspection_report[
            "semantic_concept_count"
        ] < 2:

            insights.append(

                "Low semantic abstraction richness"
            )

        if introspection_report[
            "active_routes"
        ] > 8:

            insights.append(

                "Routing complexity is increasing"
            )

        if not insights:

            insights.append(

                "Cognitive cycle is stable"
            )

        return insights

    # ============================================
    # STORE REPORT
    # ============================================

    def store_report(

        self,

        introspection_report
    ):

        self.introspection_history.append(
            self._compact_history_report(introspection_report)
        )

    # ============================================
    # BUILD SUMMARY
    # ============================================

    def build_summary(self):

        return {

            "history_size":
            len(
                self.introspection_history
            ),

            "latest_report":
            self.introspection_history[-1]

            if self.introspection_history

            else {}
        }

    def _compact_semantic_evidence(self, evidence):
        if not isinstance(evidence, dict):
            return {
                "evidence_type": type(evidence).__name__,
                "evidence_repr": self._truncate_scalar(evidence),
                "evidence_compacted": True,
            }

        compact = {
            "evidence_keys": sorted(str(key) for key in evidence.keys())[:12],
            "evidence_key_count": len(evidence),
            "evidence_compacted": True,
        }
        for key, value in evidence.items():
            key_name = str(key)
            if key_name in {
                "task_name",
                "task_id",
                "source",
                "concept_count",
                "semantic_concept_count",
            }:
                compact[key_name] = self._truncate_scalar(value, limit=120)
                continue
            if isinstance(value, (list, tuple, set)):
                compact[f"{key_name}_count"] = len(value)
                compact[f"{key_name}_sample"] = [
                    self._truncate_scalar(item, limit=80)
                    for item in list(value)[:3]
                ]
                continue
            if isinstance(value, dict):
                compact[f"{key_name}_keys"] = sorted(
                    str(item_key) for item_key in value.keys()
                )[:8]
                compact[f"{key_name}_key_count"] = len(value)
                continue
            compact[key_name] = self._truncate_scalar(value, limit=160)
        return compact

    def _compact_history_report(self, report):
        if not isinstance(report, dict):
            return report
        compact = dict(report)
        compact["attributed_concepts"] = [
            self._truncate_scalar(concept, limit=80)
            for concept in list(compact.get("attributed_concepts", []) or [])[:12]
        ]
        compact["semantic_attribution_evidence"] = self._compact_semantic_evidence(
            compact.get("semantic_attribution_evidence", {})
        )
        return compact

    def _truncate_scalar(self, value, limit=160):
        if isinstance(value, (int, float, bool)) or value is None:
            return value
        text = str(value)
        if len(text) <= limit:
            return text
        return f"{text[:limit]}...<truncated:{len(text) - limit}>"
