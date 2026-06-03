def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class MergePressureBalancer:

    def balance(self, context):

        merge_cost = _clamp(
            context.get("existential_economics_report", {})
            .get("merge_cost", {})
            .get("merge_cost", 0.0)
        )
        rejected = context.get("concept_fusion_report", {}).get(
            "rejected_count",
            0,
        )
        blocked = context.get("ontological_boundary_report", {}).get(
            "identity_boundary",
            {},
        ).get("blocked_identity_fusions", 0)

        pressure = _clamp(merge_cost * 0.62 + rejected * 0.08 + blocked * 0.12)

        return {
            "system": "merge_pressure_balancer",
            "merge_cost": merge_cost,
            "rejected_merges": rejected,
            "blocked_identity_fusions": blocked,
            "merge_pressure": pressure,
            "merge_actions": [
                "throttle_identity_sensitive_merges",
                "require_merge_rehearsal",
            ]
            if pressure >= 0.34
            else [],
            "merge_pressure_state": (
                "merge_pressure_balancing_active"
                if pressure >= 0.34
                else "merge_pressure_balanced"
            ),
        }
