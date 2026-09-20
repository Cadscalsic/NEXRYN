from runtime.governance.cache.validation_hash_engine import (
    validation_hash_engine,
)


class DependencyVersionTracker:

    def dependency_hash(self, runtime_context):

        return validation_hash_engine.stable_hash({
            "process_dependency_memory":
            runtime_context.get("process_dependency_memory", {}),
            "process_dependency_chains":
            runtime_context.get("process_dependency_chains", {}),
            "dependency_execution_trace":
            runtime_context.get("dependency_execution_trace", []),
            "dependency_chain_coverage":
            runtime_context.get("dependency_chain_coverage", 0.0),
            "dependency_coherence_average":
            runtime_context.get("dependency_coherence_average", 0.0),
        })

    def context_hash(self, runtime_context):

        return validation_hash_engine.stable_hash({
            "semantic_context":
            runtime_context.get("semantic_context", {}),
            "semantic_context_reports":
            runtime_context.get("semantic_context_reports", {}),
            "contextual_truth":
            runtime_context.get("contextual_truth", {}),
            "contextual_truth_reports":
            runtime_context.get("contextual_truth_reports", {}),
            "context_hierarchy":
            runtime_context.get("context_hierarchy", {}),
            "context_discovery":
            runtime_context.get("context_discovery", {}),
        })

    def identity_hash(self, runtime_context):

        return validation_hash_engine.stable_hash({
            "identity_runtime_state":
            runtime_context.get("identity_runtime_state"),
            "identity_runtime_continuity":
            runtime_context.get("identity_runtime_continuity"),
            "identity_core_report":
            runtime_context.get("identity_core_report", {}),
            "identity_stability_report":
            runtime_context.get("identity_stability_report", {}),
            "identity_safe_truth_integration_report":
            runtime_context.get(
                "identity_safe_truth_integration_report",
                {},
            ),
        })


dependency_version_tracker = DependencyVersionTracker()


__all__ = [
    "DependencyVersionTracker",
    "dependency_version_tracker",
]
