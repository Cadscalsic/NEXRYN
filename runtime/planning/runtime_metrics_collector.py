# ============================================
# NEXRYN RUNTIME METRICS COLLECTOR
# ============================================


class RuntimeMetricsCollector:

    def __init__(self):

        self.records = []

    def record(self, runtime_context, performance_report, cache_report):

        performance_report = performance_report or {}
        cache_report = cache_report or {}
        record = {
            "execution_time":
            performance_report.get("total_runtime_seconds", 0.0),
            "module_execution_time":
            performance_report.get("slowest_modules", []),
            "cache_hits":
            cache_report.get("cache_hits", 0),
            "cache_misses":
            cache_report.get("cache_misses", 0),
            "cache_hit_rate":
            cache_report.get("cache_hit_rate", 0.0),
            "early_exit_triggered":
            bool(runtime_context.get("early_exit_triggered", False)),
            "dependency_chains_executed":
            performance_report.get("dependency_chains_executed", 0),
            "explanation_paths_generated":
            runtime_context.get("explanation_paths_generated", 0),
            "new_reasoning":
            performance_report.get("new_reasoning", 0),
            "total_tasks":
            performance_report.get("total_tasks", 0),
            "reasoning_avoidance_ratio":
            performance_report.get("reasoning_avoidance_ratio", 0.0),
            "cognition_reuse_ratio":
            performance_report.get("cognition_reuse_ratio", 0.0),
            "governance_skip_ratio":
            performance_report.get("governance_skip_ratio", 0.0),
            "reused_concepts":
            performance_report.get("reused_concepts", []),
            "recomputed_concepts":
            performance_report.get("recomputed_concepts", []),
            "slowest_modules":
            performance_report.get("slowest_modules", []),
        }
        self.records.append(record)
        return record

    def build_report(self):

        return {
            "record_count": len(self.records),
            "latest_metrics":
            self.records[-1] if self.records else {},
        }


runtime_metrics_collector = RuntimeMetricsCollector()
