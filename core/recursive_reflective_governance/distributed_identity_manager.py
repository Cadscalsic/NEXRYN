def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class DistributedIdentityManager:

    def manage(self, context):

        distributed = context.get("distributed_cognitive_execution_report", {})
        fabric = context.get("distributed_semantic_execution_fabric_report", {})

        thread_count = distributed.get(
            "thread_count",
            len(distributed.get("threads", []))
            if isinstance(distributed.get("threads", []), list)
            else 0,
        )
        semantic_threads = fabric.get(
            "semantic_thread_count",
            len(fabric.get("semantic_threads", []))
            if isinstance(fabric.get("semantic_threads", []), list)
            else 0,
        )

        identity_strain = _clamp(
            context.get("existential_pressure_report", {})
            .get("identity_strain_regulator", {})
            .get("identity_strain", 0.0)
        )

        distributed_identity_risk = _clamp(
            thread_count * 0.05
            +
            semantic_threads * 0.04
            +
            identity_strain * 0.38
        )

        return {
            "system": "distributed_identity_manager",
            "thread_count": thread_count,
            "semantic_thread_count": semantic_threads,
            "distributed_identity_risk": distributed_identity_risk,
            "identity_actions": [
                "bind_distributed_threads_to_identity_anchor",
                "require_distributed_identity_attestation",
            ]
            if distributed_identity_risk >= 0.34
            else [],
            "distributed_identity_state": (
                "distributed_identity_management_active"
                if distributed_identity_risk >= 0.34
                else "distributed_identity_stable"
            ),
        }
