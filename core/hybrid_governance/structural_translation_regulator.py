def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class StructuralTranslationRegulator:

    def regulate(self, context, router):

        topology_flex = _clamp(
            context.get("adaptive_equilibrium_report", {})
            .get("contextual_topology_regulator", {})
            .get("contextual_topology_flexibility", 0.5)
        )
        route_count = len(router.get("semantic_routes", []))

        translation_load = _clamp(route_count * 0.08 + (1.0 - topology_flex) * 0.36)

        return {
            "system": "structural_translation_regulator",
            "translation_load": translation_load,
            "topology_flexibility": topology_flex,
            "translation_actions": [
                "limit_structural_translation_scope",
                "preserve_source_paradigm_structure",
            ]
            if translation_load >= 0.34
            else [],
            "translation_state": (
                "structural_translation_regulated"
                if translation_load >= 0.34
                else "structural_translation_open"
            ),
        }
