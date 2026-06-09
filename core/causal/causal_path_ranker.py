from core.epistemic_models import clamp


class CausalPathRanker:
    """Ranks causal paths by edge strength, confidence, and depth."""

    def score_path(self, path, edges):
        if not edges:
            return {
                "evidence_score": 0.0,
                "stability_score": 0.0,
                "contradiction_resistance": 0.0,
                "cross_task_support": 0.0,
                "context_transferability": 0.0,
                "path_strength": 0.0,
                "path_confidence": 0.0,
                "depth": max(len(path) - 1, 0),
                "score": 0.0,
                "ranking": "LOW_CONFIDENCE",
            }
        evidence_items = [
            item
            for edge in edges
            for item in edge.evidence
            if isinstance(item, dict)
        ]
        support_count = sum(
            item.get("support_count", 1)
            for item in evidence_items
        ) or len(edges)
        contradiction_count = sum(
            item.get("contradiction_count", 0)
            for item in evidence_items
        )
        tasks = {
            task
            for item in evidence_items
            for task in item.get("tasks", [])
        }
        contexts = {
            context
            for item in evidence_items
            for context in item.get("contexts", [])
        }
        evidence_score = clamp(support_count / 5.0)
        contradiction_resistance = clamp(
            1.0 - contradiction_count / max(support_count + contradiction_count, 1)
        )
        cross_task_support = clamp(len(tasks) / 3.0) if tasks else evidence_score
        context_transferability = (
            clamp(len(contexts) / 3.0)
            if contexts
            else clamp(sum(edge.confidence for edge in edges) / len(edges))
        )
        path_strength = clamp(
            sum(edge.weight for edge in edges) / len(edges)
        )
        path_confidence = clamp(
            sum(edge.confidence for edge in edges) / len(edges)
        )
        stability_score = clamp((path_strength + path_confidence) / 2.0)
        depth = len(edges)
        depth_penalty = clamp(1.0 - max(depth - 4, 0) * 0.05)
        score = clamp(
            (
                evidence_score
                + stability_score
                + contradiction_resistance
                + cross_task_support
                + context_transferability
            )
            / 5.0
            * depth_penalty
        )
        if score >= 0.80:
            ranking = "HIGH_CONFIDENCE"
        elif score >= 0.55:
            ranking = "MEDIUM_CONFIDENCE"
        else:
            ranking = "LOW_CONFIDENCE"
        return {
            "evidence_score": evidence_score,
            "stability_score": stability_score,
            "contradiction_resistance": contradiction_resistance,
            "cross_task_support": cross_task_support,
            "context_transferability": context_transferability,
            "path_strength": path_strength,
            "path_confidence": path_confidence,
            "depth": depth,
            "score": score,
            "ranking": ranking,
        }

    def rank(self, paths):
        ranked = []
        for path, edges in paths:
            ranked.append({
                "causal_chain": path,
                **self.score_path(path, edges),
            })
        return sorted(
            ranked,
            key=lambda item: (
                item["score"],
                item["path_confidence"],
                -item["depth"],
            ),
            reverse=True,
        )


__all__ = [
    "CausalPathRanker",
]
