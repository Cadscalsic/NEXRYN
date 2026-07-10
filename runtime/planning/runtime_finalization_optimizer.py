# ============================================
# NEXRYN RUNTIME FINALIZATION OPTIMIZER
# ============================================

import time


class RuntimeFinalizationOptimizer:

    FAST_SKIPPED_OPERATIONS = [
        "strategy_evolution",
        "failure_memory_update",
        "deep_validation",
        "temporal_promotion_checks",
        "full_memory_report",
        "historical_scans",
        "memory_compression",
        "ontology_reconciliation",
        "stable_truth_revalidation",
    ]

    def choose_mode(
        self,
        reasoning_budget=None,
        invalidated_concepts=None,
        runtime_context=None,
    ):

        invalidated_concepts = invalidated_concepts or []
        mode = getattr(reasoning_budget, "mode", None)
        runtime_context = runtime_context if isinstance(runtime_context, dict) else {}
        reuse_ready = (
            runtime_context.get("evidence_saturated") is True
            and float(runtime_context.get("dependency_chain_coverage", 0.0) or 0.0)
            > 0.95
            and float(runtime_context.get("dependency_explanation_quality", 0.0) or 0.0)
            > 0.95
        )

        finalization_mode = runtime_context.get("finalization_mode")
        execution_profile = runtime_context.get("execution_profile", {})
        if isinstance(execution_profile, dict):
            finalization_mode = (
                finalization_mode
                or execution_profile.get("finalization_mode")
            )

        if (
            mode == "fast"
            or finalization_mode == "fast"
            or reuse_ready
        ) and not invalidated_concepts:
            return "fast"

        return "deep"

    def fast_report(
        self,
        reused_concepts=None,
        started_at=None,
    ):

        return {
            "finalization_mode": "fast",
            "skipped_operations": list(self.FAST_SKIPPED_OPERATIONS),
            "recomputed_concepts": [],
            "reused_concepts": list(reused_concepts or []),
            "finalization_time": round(
                time.perf_counter() - started_at,
                4,
            ) if started_at is not None else 0.0,
            "estimated_cost_reduction": 0.70,
        }

    def deep_report(
        self,
        recomputed_concepts=None,
        reused_concepts=None,
        started_at=None,
    ):

        return {
            "finalization_mode": "deep",
            "skipped_operations": [],
            "recomputed_concepts": list(recomputed_concepts or []),
            "reused_concepts": list(reused_concepts or []),
            "finalization_time": round(
                time.perf_counter() - started_at,
                4,
            ) if started_at is not None else 0.0,
            "estimated_cost_reduction": 0.0,
        }


runtime_finalization_optimizer = RuntimeFinalizationOptimizer()
