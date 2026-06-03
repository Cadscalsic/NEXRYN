from core.epistemic_models import clamp


class EvidenceReinforcementEngine:
    def semantic_key(self, evidence):
        metadata = evidence.metadata
        return (
            evidence.concept,
            evidence.source,
            metadata.get(
                "semantic_key",
                metadata.get(
                    "trait_state",
                    metadata.get("observation_id", "stable_observation"),
                ),
            ),
        )

    def reinforce(self, evidence, previous_items):
        matches = [
            item
            for item in previous_items
            if self.semantic_key(item)
            == self.semantic_key(evidence)
        ]
        corroborating = [
            item
            for item in matches
            if abs(
                item.support_score
                - evidence.support_score
            )
            <= 0.12
            and abs(
                item.contradiction_score
                - evidence.contradiction_score
            )
            <= 0.12
        ]
        repeat_count = len(
            corroborating,
        )
        reinforcement_bonus = min(
            repeat_count,
            6,
        ) * 0.045
        evidence.reliability = clamp(
            evidence.reliability
            + reinforcement_bonus,
        )
        evidence.metadata[
            "reinforcement_count"
        ] = repeat_count
        evidence.metadata[
            "reinforcement_bonus"
        ] = round(
            reinforcement_bonus,
            4,
        )
        evidence.metadata[
            "reinforcement_applied"
        ] = repeat_count > 0
        evidence.metadata[
            "reinforcement_is_not_truth"
        ] = True
        return evidence


__all__ = [
    "EvidenceReinforcementEngine",
]
