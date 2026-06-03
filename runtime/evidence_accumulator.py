from core.epistemic_models import clamp
from core.evidence_registry import EvidenceRegistry


class EvidenceAccumulator:
    def __init__(self, registry=None):
        self.registry = registry or EvidenceRegistry()

    def _trait_id(self, trait):
        return str(
            trait.get(
                "id",
                trait.get("trait", "unknown_trait"),
            )
        )

    def collect_trait_evidence(self, trait):
        concept = self._trait_id(trait)
        history = list(trait.get("survival_history", []))
        observations = history or [{}]

        for index, observation in enumerate(observations):
            constructive = clamp(
                observation.get(
                    "constructive_score",
                    trait.get("fitness", 0.0),
                )
            )
            identity_continuity = clamp(
                observation.get(
                    "identity_continuity",
                    trait.get("stability_score", 0.0),
                )
            )
            semantic_alignment = clamp(
                trait.get("semantic_alignment", 0.0)
            )
            stability = clamp(
                trait.get("stability_score", 0.0)
            )
            support = clamp(
                constructive * 0.34
                + identity_continuity * 0.26
                + semantic_alignment * 0.22
                + stability * 0.18
            )
            contradiction = clamp(
                (1.0 - constructive) * 0.30
                + (1.0 - identity_continuity) * 0.28
                + (1.0 - semantic_alignment) * 0.24
                + (1.0 - stability) * 0.18
            )
            self.registry.collect({
                "concept": concept,
                "source": "evolutionary_trait_survival_history",
                "support_score": support,
                "contradiction_score": contradiction,
                "reliability": clamp(
                    0.56
                    + min(len(history), 6) * 0.06
                ),
                "causal_alignment": semantic_alignment,
                "semantic_consistency": clamp(
                    stability * 0.58
                    + identity_continuity * 0.42
                ),
                "metadata": {
                    "evidence_id": (
                        f"trait_survival:{concept}:{index}:"
                        f"{constructive}:{identity_continuity}"
                    ),
                    "trait_state": trait.get(
                        "trait_state",
                        "emerging",
                    ),
                    "semantic_key":
                    concept,
                    "survival_is_not_truth": True,
                },
            })

        return self.registry.aggregate(concept)

    def _semantic_observations(self, context, concept):
        observations = list(
            context.get(
                "semantic_abstractions",
                [],
            )
        )
        observations.extend(
            context.get(
                "semantic_graph",
                {},
            ).get(
                "concept_nodes",
                [],
            )
        )
        return [
            item
            for item in observations
            if str(
                item.get(
                    "semantic_concept",
                    item.get("concept", ""),
                )
            )
            == concept
        ]

    def collect_semantic_evidence(self, context, concept):
        collected = 0
        for index, observation in enumerate(
            self._semantic_observations(
                context,
                concept,
            )
        ):
            confidence = clamp(
                observation.get(
                    "confidence",
                    0.0,
                )
            )
            consistent = (
                observation.get(
                    "semantic_consistency",
                    True,
                )
                is not False
            )
            semantic_consistency = (
                confidence
                if consistent
                else clamp(
                    confidence * 0.35
                )
            )
            self.registry.collect({
                "concept": concept,
                "source": "semantic_abstraction_observation",
                "support_score": clamp(
                    confidence * 0.72
                ),
                "contradiction_score": clamp(
                    (1.0 - confidence) * 0.35
                    + (
                        0.0
                        if consistent
                        else 0.45
                    )
                ),
                "reliability": 0.58,
                "causal_alignment": 0.50,
                "semantic_consistency": semantic_consistency,
                "metadata": {
                    "evidence_id": (
                        f"semantic_abstraction:{concept}:{index}:"
                        f"{confidence}"
                    ),
                    "raw_confidence": confidence,
                    "semantic_key":
                    concept,
                    "confidence_is_not_truth": True,
                    "semantic_observation_is_not_causal_proof": True,
                },
            })
            collected += 1
        return collected

    def collect_execution_validation_evidence(self, context, concept):
        evaluation = context.get(
            "evaluation_result",
            {},
        )
        if not evaluation or not self._semantic_observations(
            context,
            concept,
        ):
            return 0

        accuracy = clamp(
            evaluation.get(
                "accuracy",
                0.0,
            )
        )
        structural_score = clamp(
            evaluation.get(
                "structural_score",
                accuracy,
            )
        )
        final_score = clamp(
            evaluation.get(
                "final_score",
                accuracy,
            )
        )
        support = clamp(
            accuracy * 0.42
            + structural_score * 0.34
            + final_score * 0.24
        )
        contradiction = clamp(
            (1.0 - accuracy) * 0.48
            + (1.0 - structural_score) * 0.30
            + (1.0 - final_score) * 0.22
        )
        causal_alignment = clamp(
            accuracy * 0.58
            + structural_score * 0.28
            + final_score * 0.14
        )
        task_path = str(
            context.get(
                "task_path",
                "runtime_task",
            )
        )
        self.registry.collect({
            "concept": concept,
            "source": "execution_validation",
            "support_score": support,
            "contradiction_score": contradiction,
            "reliability": clamp(
                0.62
                + structural_score * 0.20
                + accuracy * 0.12
            ),
            "causal_alignment": causal_alignment,
            "semantic_consistency": structural_score,
            "metadata": {
                "evidence_id":
                f"execution_validation:{concept}:{task_path}",

                "semantic_key":
                concept,

                "task_path":
                task_path,

                "accuracy":
                accuracy,

                "structural_score":
                structural_score,

                "final_score":
                final_score,

                "execution_validation_is_not_truth":
                True,
            },
        })
        return 1

    def collect_candidate_evidence(self, context, trait):
        concept = self._trait_id(
            trait,
        )
        self.collect_trait_evidence(
            trait,
        )
        semantic_observation_count = self.collect_semantic_evidence(
            context,
            concept,
        )
        execution_validation_count = (
            self.collect_execution_validation_evidence(
                context,
                concept,
            )
        )
        return {
            "aggregate": self.registry.aggregate(
                concept,
            ),
            "semantic_observation_count": semantic_observation_count,
            "execution_validation_count": execution_validation_count,
        }

    def report(self):
        report = self.registry.report()
        report.update({
            "system": "evidence_accumulator",
            "accumulation_policy":
            "trait_observations_are_evidence_not_truth",
        })
        return report


evidence_accumulator = EvidenceAccumulator()
