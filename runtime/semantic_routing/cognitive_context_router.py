"""Prioritize semantic context before execution intent routing."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping


class CognitiveContextRouter:
    """Compress broad semantic context into execution-relevant concepts."""

    system_name = "cognitive_context_router"

    EXECUTION_PRIORITIES = {
        "bridge_creation": 1.00,
        "component_connection": 1.00,
        "connectivity_change": 0.94,
        "topology_change": 0.88,
        "topology_repair": 0.90,
        "hole_removal": 0.86,
        "path_finding": 0.88,
        "route_completion": 0.86,
        "path_construction": 0.88,
        "rotation": 0.92,
        "reflection": 0.90,
        "rotation_reflection": 0.94,
        "orientation_change": 0.84,
        "scaling": 0.86,
        "scale_transformation": 0.86,
        "size_transformation": 0.78,
        "noise_removal": 0.84,
        "artifact_filtering": 0.80,
        "object_removal": 0.82,
        "symbolic_remapping": 0.82,
        "color_mapping": 0.80,
        "relative_position": 0.76,
        "object_translation": 0.78,
        "directional_motion": 0.74,
        "growth": 0.76,
        "topological_growth": 0.78,
        "density_increase": 0.72,
        "region_filling": 0.76,
        "pattern_completion": 0.76,
    }
    INFORMATIONAL_MARKERS = {
        "preservation",
        "identity",
        "constant",
        "stability",
        "invariant",
    }

    def route(
        self,
        concepts: list[str] | None = None,
        *,
        runtime_context: Mapping[str, Any] | None = None,
        semantic_context_report: Mapping[str, Any] | None = None,
        max_routed_concepts: int = 6,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        semantic_context_report = (
            semantic_context_report if isinstance(semantic_context_report, Mapping) else {}
        )
        normalized = list(dict.fromkeys(
            self._normalize_token(item)
            for item in concepts or []
            if self._normalize_token(item)
        ))
        context_scores = self._context_scores(semantic_context_report, runtime_context)
        rows = []
        for concept in normalized:
            score, reasons = self._score_concept(concept, context_scores)
            rows.append({
                "concept": concept,
                "priority_score": round(score, 4),
                "priority_band": self._priority_band(score),
                "reasons": reasons,
            })

        rows.sort(key=lambda item: (-item["priority_score"], item["concept"]))
        max_count = max(1, int(max_routed_concepts or 1))
        primary = [
            row for row in rows
            if row["priority_band"] in {"HIGH", "MEDIUM"}
        ][:max_count]
        if not primary and rows:
            primary = rows[: min(max_count, len(rows))]

        routed = [row["concept"] for row in primary]
        suppressed = [
            row for row in rows
            if row["concept"] not in set(routed)
        ]
        overload = len(normalized) > max_count
        status = "COMPRESSED" if overload and routed else "ROUTED" if routed else "UNROUTED"
        return {
            "system": self.system_name,
            "context_routing_success": bool(routed),
            "context_routing_status": status,
            "context_overload_detected": overload,
            "input_concept_count": len(normalized),
            "routed_concept_count": len(routed),
            "suppressed_concept_count": len(suppressed),
            "routed_concepts": routed,
            "prioritized_concepts": primary,
            "suppressed_concepts": suppressed,
            "failure_causes": ["routing_overload"] if overload else [],
            "compression_ratio": round(len(routed) / max(len(normalized), 1), 4),
            "timestamp": str(datetime.utcnow()),
        }

    def _score_concept(
        self,
        concept: str,
        context_scores: Mapping[str, float],
    ) -> tuple[float, list[str]]:
        score = self.EXECUTION_PRIORITIES.get(concept, 0.35)
        reasons = []
        if concept in self.EXECUTION_PRIORITIES:
            reasons.append("known_execution_concept")
        if concept in context_scores:
            score = max(score, 0.55 + (context_scores[concept] * 0.35))
            reasons.append("context_strength_signal")
        if any(marker in concept for marker in self.INFORMATIONAL_MARKERS):
            score -= 0.25
            reasons.append("informational_or_preservation_context")
        if concept.endswith("_change") or concept.endswith("_creation"):
            score += 0.08
            reasons.append("state_change_signal")
        return max(0.0, min(1.0, score)), reasons or ["low_specificity_context"]

    def _context_scores(
        self,
        semantic_context_report: Mapping[str, Any],
        runtime_context: Mapping[str, Any],
    ) -> dict[str, float]:
        scores: dict[str, float] = {}

        def visit(value: Any, active_concept: str | None = None) -> None:
            if isinstance(value, str):
                return
            if isinstance(value, Mapping):
                concept = active_concept
                for key in ("concept", "semantic_context", "discovered_context"):
                    token = self._normalize_token(value.get(key))
                    if token:
                        concept = token
                        break
                score = self._first_number(
                    value.get("semantic_context_score"),
                    value.get("context_strength"),
                    value.get("contextual_truth_score"),
                    value.get("priority_score"),
                )
                if concept and score is not None:
                    scores[concept] = max(scores.get(concept, 0.0), min(score, 1.0))
                for item in value.values():
                    if isinstance(item, (Mapping, list, tuple, set)):
                        visit(item, concept)
                return
            if isinstance(value, (list, tuple, set)):
                for item in value:
                    visit(item, active_concept)

        visit(semantic_context_report)
        visit(runtime_context.get("semantic_context_report"))
        return scores

    def _priority_band(self, score: float) -> str:
        if score >= 0.80:
            return "HIGH"
        if score >= 0.55:
            return "MEDIUM"
        return "LOW"

    def _normalize_token(self, value: Any) -> str:
        return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")

    def _first_number(self, *values: Any) -> float | None:
        for value in values:
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if number >= 0.0:
                return number
        return None


cognitive_context_router = CognitiveContextRouter()
