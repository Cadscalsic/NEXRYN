# ============================================
# NEXRYN CONTRADICTION ENGINE
# ============================================


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(
                value,
                maximum,
            ),
        ),
        4,
    )


class ContradictionEngine:

    def _build_trace(self, contradictions):

        if not isinstance(contradictions, list):
            return []

        trace = []
        for contradiction in contradictions:
            if not isinstance(contradiction, dict):
                continue

            trace.append(
                {
                    "source":
                    contradiction.get(
                        "source",
                        contradiction.get(
                            "origin",
                            "unknown",
                        ),
                    ),
                    "target":
                    contradiction.get(
                        "target",
                        contradiction.get(
                            "destination",
                            "unknown",
                        ),
                    ),
                    "type":
                    contradiction.get(
                        "type",
                        "semantic",
                    ),
                }
            )

        return trace

    def _detect_recursive_inconsistencies(self, causal_map):

        if not isinstance(causal_map, dict):
            return []

        loops = []
        for source, targets in causal_map.items():
            if not isinstance(targets, list):
                continue

            for target in targets:
                if target == source:
                    loops.append(
                        [source, target],
                    )
                elif isinstance(causal_map.get(target), list):
                    if source in causal_map.get(target, []):
                        loops.append(
                            [source, target, source],
                        )

        return loops

    def analyze(self, context):

        contradictions = context.get(
            "semantic_contradictions",
            context.get(
                "known_contradictions",
                [],
            ),
        )

        contradiction_trace = self._build_trace(
            contradictions,
        )

        causal_map = context.get(
            "causal_relation_map",
            context.get(
                "causal_dependency_map",
                {},
            ),
        )

        recursive_inconsistencies = self._detect_recursive_inconsistencies(
            causal_map,
        )

        contradiction_severity = _clamp(
            len(contradiction_trace) * 0.24
            + len(recursive_inconsistencies) * 0.28
            + _clamp(context.get("causal_conflict_intensity", 0.0))
        )

        conflict_propagation = _clamp(
            (len(contradiction_trace) * 0.18)
            + (len(recursive_inconsistencies) * 0.24)
            + _clamp(context.get("causal_conflict_intensity", 0.0)) * 0.16
        )

        return {
            "system":
            "contradiction_engine",

            "contradiction_trace":
            contradiction_trace,

            "recursive_inconsistencies":
            recursive_inconsistencies,

            "contradiction_severity":
            contradiction_severity,

            "causal_conflict_propagation":
            conflict_propagation,
        }
