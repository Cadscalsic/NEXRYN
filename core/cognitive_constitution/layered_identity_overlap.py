def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class LayeredIdentityOverlap:

    def assess(self, context):

        identity_report = context.get("identity_reasoner_report", {})
        analyses = identity_report.get("identity_analyses", [])
        if not isinstance(analyses, list):
            analyses = []

        observed_layers = set()
        conflict_layers = 0

        for analysis in analyses:
            if not isinstance(analysis, dict):
                continue

            explanation = analysis.get("failure_explanation", {})
            hidden = explanation.get("hidden_conflicts", {})
            layers = hidden.get("conflict_layers", [])

            if not isinstance(layers, list):
                continue

            for layer in layers:
                observed_layers.add(str(layer))
                conflict_layers += 1

        overlap_pressure = _clamp(conflict_layers / 6.0)
        layered_overlap = _clamp(1.0 - overlap_pressure)

        actions = []
        if layered_overlap < 0.62:
            actions.extend([
                "preserve_layered_identity_boundaries",
                "separate_geometric_and_existential_overlap",
            ])

        return {
            "system": "layered_identity_overlap",
            "layered_identity_overlap": layered_overlap,
            "overlap_pressure": overlap_pressure,
            "observed_identity_layers": sorted(observed_layers),
            "overlap_actions": actions,
            "overlap_state": (
                "identity_layer_overlap_unstable"
                if actions
                else "identity_layer_overlap_clear"
            ),
        }
