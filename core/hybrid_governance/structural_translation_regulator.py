def _clamp(value, minimum=0.0, maximum=1.0):
    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class StructuralTranslationRegulator:

    REGULATION_THRESHOLD = 0.34
    CRITICAL_THRESHOLD = 0.66
    MAX_ROUTE_LOAD = 0.18

    def regulate(self, context=None, router=None):
        context = context or {}
        router = router or {}

        topology_flex = _clamp(
            context.get("adaptive_equilibrium_report", {})
            .get("contextual_topology_regulator", {})
            .get("contextual_topology_flexibility", 0.5)
        )

        routes = router.get("semantic_routes", [])
        route_count = len(routes) if isinstance(routes, list) else 0

        route_load = min(route_count * 0.06, self.MAX_ROUTE_LOAD)

        translation_load = _clamp(
            route_load
            + (1.0 - topology_flex) * 0.36
        )

        fast_mode = (
            context.get("episode_completed") is True
            or context.get("shutdown_mode") == "fast"
            or context.get("post_success_mode") == "fast"
        )

        regulated = translation_load >= self.REGULATION_THRESHOLD
        critical = translation_load >= self.CRITICAL_THRESHOLD

        if fast_mode and regulated and not critical:
            return {
                "system": "structural_translation_regulator",
                "translation_load": translation_load,
                "topology_flexibility": topology_flex,
                "translation_state": "translation_regulation_deferred_in_fast_mode",
                "translation_actions": [],
                "deferred_actions": [
                    "limit_structural_translation_scope",
                    "preserve_source_paradigm_structure",
                ],
                "critical": False,
                "reason": "noncritical_translation_regulation_deferred_after_success",
                "scores": {
                    "route_count": route_count,
                    "route_load": round(route_load, 4),
                    "topology_flexibility": topology_flex,
                },
            }

        if critical:
            actions = [
                "limit_structural_translation_scope",
                "preserve_source_paradigm_structure",
                "block_structural_translation_commit",
            ]
            state = "structural_translation_critical"

        elif regulated:
            actions = [
                "limit_structural_translation_scope",
                "preserve_source_paradigm_structure",
            ]
            state = "structural_translation_regulated"

        else:
            actions = []
            state = "structural_translation_open"

        return {
            "system": "structural_translation_regulator",
            "translation_load": translation_load,
            "topology_flexibility": topology_flex,
            "translation_actions": actions,
            "translation_state": state,
            "critical": critical,
            "regulated": regulated,
            "scores": {
                "route_count": route_count,
                "route_load": round(route_load, 4),
                "topology_flexibility": topology_flex,
            },
        }