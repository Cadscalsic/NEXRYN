from core.epistemic_models import clamp
from runtime.epistemic_trial_engine import EpistemicTrialEngine


class EpistemicPromotionEngine:
    PROMOTABLE_STATES = {
        "candidate",
        "adaptive",
        "dominant",
        "decaying",
        "suppressed",
        "extinct",
    }

    def __init__(self):
        self.trial_engine = EpistemicTrialEngine()

    def _traits(self, context):
        natural_selection = context.get(
            "cognitive_natural_selection_report",
            {},
        )

        traits = []

        for key in [
            "selected_traits",
            "decaying_traits",
            "suppressed_traits",
            "extinct_traits",
        ]:

            traits.extend(
                natural_selection.get(
                    key,
                    [],
                )
            )

        if traits:

            return traits

        return (
            context.get("evolutionary_memory_report", {})
            .get("adaptive_trait_memory", {})
            .get("traits", [])
        )

    def _quality(self, trait):
        history = trait.get("survival_history", [])
        constructive_scores = [
            clamp(item.get("constructive_score", 0.0))
            for item in history
        ]
        continuity_scores = [
            clamp(item.get("identity_continuity", 0.0))
            for item in history
        ]
        constructive = clamp(
            sum(constructive_scores)
            / max(len(constructive_scores), 1)
        )
        identity_continuity = clamp(
            sum(continuity_scores)
            / max(len(continuity_scores), 1)
        )
        semantic_alignment = clamp(
            trait.get("semantic_alignment", 0.0)
        )
        stability = clamp(
            trait.get("stability_score", 0.0)
        )
        fitness = clamp(
            trait.get(
                "net_fitness",
                trait.get("fitness", 0.0),
            )
        )
        observations = int(
            trait.get(
                "observations",
                len(history),
            )
            or 0
        )
        evidence_strength = clamp(
            constructive * 0.30
            + identity_continuity * 0.24
            + semantic_alignment * 0.22
            + stability * 0.16
            + fitness * 0.08
        )
        return {
            "constructive_score": constructive,
            "identity_continuity": identity_continuity,
            "semantic_alignment": semantic_alignment,
            "stability_score": stability,
            "fitness": fitness,
            "observations": observations,
            "evidence_strength": evidence_strength,
        }

    def _promotion_state(self, trait, quality):
        trait_state = trait.get("trait_state", "emerging")
        if trait_state not in self.PROMOTABLE_STATES:
            return "NOT_PROMOTABLE"
        if trait_state in [
            "decaying",
            "suppressed",
            "extinct",
        ]:

            return (
                "RECOVERY_PROBATION"
                if quality["observations"] >= 2
                and quality["evidence_strength"] >= 0.68
                and quality["semantic_alignment"] >= 0.70
                and quality["stability_score"] >= 0.64
                else "NOT_PROMOTABLE"
            )
        if (
            quality["observations"] >= 4
            and quality["evidence_strength"] >= 0.78
            and quality["semantic_alignment"] >= 0.76
            and quality["stability_score"] >= 0.72
        ):
            return "TRUTH_CANDIDATE"
        if (
            quality["observations"] >= 3
            and quality["evidence_strength"] >= 0.68
        ):
            return "VALIDATED_BELIEF"
        if (
            quality["observations"] >= 2
            and quality["evidence_strength"] >= 0.58
        ):
            return "SUPPORTED_BELIEF"
        if (
            quality["observations"] >= 1
            and quality["evidence_strength"] >= 0.42
        ):
            return "PROBATIONARY_BELIEF"
        return "CANDIDATE"

    def _evidence(self, concept, trait, quality):
        trait_state = trait.get("trait_state", "emerging")
        observation_id = (
            f"{concept}:{quality['observations']}:"
            f"{quality['evidence_strength']}"
        )
        return {
            "concept": concept,
            "source": "evolutionary_trait_observation",
            "support_score": quality["evidence_strength"],
            "contradiction_score": clamp(
                (1.0 - quality["semantic_alignment"]) * 0.48
                + (1.0 - quality["stability_score"]) * 0.32
                + (1.0 - quality["identity_continuity"]) * 0.20
            ),
            "reliability": clamp(
                0.42
                + min(quality["observations"], 6) * 0.06
            ),
            "causal_alignment": quality["semantic_alignment"],
            "semantic_consistency": clamp(
                quality["stability_score"] * 0.58
                + quality["identity_continuity"] * 0.42
            ),
            "metadata": {
                "evidence_id":
                f"evolutionary_trait_observation:{observation_id}",

                "trait_state":
                trait_state,

                "survival_is_not_truth":
                True,
            },
        }

    def run_cycle(self, context):
        promotions = []
        hypotheses = []
        evidence = []
        trials = []

        for trait in self._traits(context):
            concept = str(
                trait.get(
                    "id",
                    trait.get("trait", "unknown_trait"),
                )
            )
            quality = self._quality(trait)
            promotion_state = self._promotion_state(
                trait,
                quality,
            )
            trial = self.trial_engine.run_trait_trial(
                context,
                trait,
                quality,
            )
            trials.append(
                trial,
            )
            if (
                promotion_state
                in [
                    "NOT_PROMOTABLE",
                    "CANDIDATE",
                ]
                and trial["execution_validation_count"] > 0
                and trial["trial"]["trial_result"] == "PASSED"
            ):
                promotion_state = "EVIDENCE_SUPPORTED_BELIEF"

            if (
                promotion_state
                in [
                    "NOT_PROMOTABLE",
                    "CANDIDATE",
                ]
                and trial["semantic_observation_count"] > 0
                and trial["trial"]["trial_result"] == "INCONCLUSIVE"
            ):
                promotion_state = "OBSERVATIONAL_PROBATION"

            promotable = (
                promotion_state
                not in [
                    "NOT_PROMOTABLE",
                    "CANDIDATE",
                ]
                and trial[
                    "eligible_for_extinction_grace"
                ]
            )
            promotions.append({
                "concept": concept,
                "trait_state": trait.get(
                    "trait_state",
                    "emerging",
                ),
                "promotion_state": promotion_state,
                "promote_to_epistemic_trial": promotable,
                "quality": quality,
                "epistemic_trial": trial,
                "survival_is_not_truth": True,
            })
            if not promotable:
                continue

            hypotheses.append({
                "concept": concept,
                "claim": f"{concept} is a reusable cognitive invariant",
                "prior_confidence": quality["evidence_strength"],
                "semantic_consistency": clamp(
                    quality["stability_score"] * 0.58
                    + quality["identity_continuity"] * 0.42
                ),
                "causal_alignment": quality["semantic_alignment"],
                "metadata": {
                    "origin": "epistemic_promotion_engine",
                    "promotion_state": promotion_state,
                    "trait_state": trait.get(
                        "trait_state",
                        "emerging",
                    ),
                    "survival_is_not_truth": True,
                },
            })
            evidence.append(
                self._evidence(
                    concept,
                    trait,
                    quality,
                )
            )
            evidence.extend(
                item.as_dict()
                for item in self.trial_engine
                .evidence_accumulator
                .registry
                .evidence_for(
                    concept,
                )
            )

        return {
            "system": "epistemic_promotion_engine",
            "promotions": promotions,
            "candidate_count": len(promotions),
            "promotion_count": len(hypotheses),
            "epistemic_trials": trials,
            "epistemic_trial_engine": self.trial_engine.report(),
            "promotion_grace_traits": [
                item["concept"]
                for item in promotions
                if item["promote_to_epistemic_trial"]
            ],
            "epistemic_hypotheses": hypotheses,
            "epistemic_evidence": evidence,
            "promotion_path": [
                "CANDIDATE",
                "PROBATIONARY_BELIEF",
                "SUPPORTED_BELIEF",
                "VALIDATED_BELIEF",
                "TRUTH_CANDIDATE",
                "RECOVERY_PROBATION",
                "OBSERVATIONAL_PROBATION",
                "EVIDENCE_SUPPORTED_BELIEF",
            ],
            "constitutional_invariants": {
                "survival_is_not_truth": True,
                "trait_state_is_not_belief_state": True,
                "promotion_requires_epistemic_trial": True,
            },
        }


epistemic_promotion_engine = EpistemicPromotionEngine()
