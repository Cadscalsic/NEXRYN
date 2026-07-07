"""Rank retrieved experiences by reusable cognitive similarity."""

from __future__ import annotations

from dataclasses import dataclass

from runtime.adaptive_reuse.experience_index import Experience


@dataclass(frozen=True)
class RankedExperience:
    experience: Experience
    score: float
    components: dict[str, float]


class StrategyRanker:
    weights = {
        "semantic_similarity": 0.24,
        "structural_similarity": 0.14,
        "concept_overlap": 0.18,
        "dependency_similarity": 0.12,
        "program_similarity": 0.14,
        "execution_similarity": 0.10,
        "truth_similarity": 0.04,
        "context_similarity": 0.04,
    }

    def rank(
        self,
        query: Experience,
        experiences: list[Experience],
        minimum_score: float = 0.18,
        top_k: int = 5,
    ) -> list[RankedExperience]:
        ranked = []
        for experience in experiences:
            components = {
                "semantic_similarity": _jaccard(
                    query.signature_tokens("semantic_signature"),
                    experience.signature_tokens("semantic_signature"),
                ),
                "structural_similarity": _jaccard(
                    query.signature_tokens("visual_signature"),
                    experience.signature_tokens("visual_signature"),
                ),
                "concept_overlap": _jaccard(
                    query.signature_tokens("concept_signature"),
                    experience.signature_tokens("concept_signature"),
                ),
                "dependency_similarity": _jaccard(
                    query.signature_tokens("dependency_signature"),
                    experience.signature_tokens("dependency_signature"),
                ),
                "program_similarity": _jaccard(
                    query.signature_tokens("program_signature"),
                    experience.signature_tokens("program_signature"),
                ),
                "execution_similarity": _jaccard(
                    query.signature_tokens("execution_signature"),
                    experience.signature_tokens("execution_signature"),
                ),
                "truth_similarity": _jaccard(
                    query.signature_tokens("truth_signature"),
                    experience.signature_tokens("truth_signature"),
                ),
                "context_similarity": _jaccard(
                    query.signature_tokens("context_signature"),
                    experience.signature_tokens("context_signature"),
                ),
            }
            weighted = sum(
                components[name] * weight
                for name, weight in self.weights.items()
            )
            quality = (
                experience.performance_score * 0.08
                + experience.success_rate * 0.06
                + experience.confidence * 0.04
                + min(experience.reuse_count / 10.0, 1.0) * 0.02
            )
            score = round(min(1.0, weighted + quality), 4)
            if score >= minimum_score:
                ranked.append(RankedExperience(experience, score, components))
        ranked.sort(
            key=lambda item: (
                item.score,
                item.experience.success_rate,
                item.experience.confidence,
                item.experience.experience_id,
            ),
            reverse=True,
        )
        return ranked[:top_k]


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 0.0
    if not left or not right:
        return 0.0
    return round(len(left & right) / len(left | right), 4)
