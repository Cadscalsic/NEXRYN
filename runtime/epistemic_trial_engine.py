from core.epistemic_models import Hypothesis
from core.epistemic_trials import EpistemicTrialEngine as CoreTrialEngine
from runtime.causal_attestation_engine import CausalAttestationEngine
from runtime.contradiction_resolution_engine import (
    ContradictionResolutionEngine,
)
from runtime.evidence_accumulator import EvidenceAccumulator
from runtime.epistemic.belief_strength_model import BeliefStrengthModel


class EpistemicTrialEngine:
    def __init__(self, accumulator=None):
        self.evidence_accumulator = accumulator or EvidenceAccumulator()
        self.trial_engine = CoreTrialEngine(
            self.evidence_accumulator.registry,
        )
        self.belief_strength_model = BeliefStrengthModel()
        self.causal_attestation_engine = CausalAttestationEngine()
        self.contradiction_resolution_engine = (
            ContradictionResolutionEngine()
        )

    def run_trait_trial(self, context, trait, quality):
        concept = str(
            trait.get(
                "id",
                trait.get("trait", "unknown_trait"),
            )
        )
        accumulation = self.evidence_accumulator.collect_candidate_evidence(
            context,
            trait,
        )
        aggregate = accumulation["aggregate"]
        trial = self.trial_engine.run_trial(
            Hypothesis(
                concept=concept,
                claim=f"{concept} is a reusable cognitive invariant",
                prior_confidence=quality["evidence_strength"],
                semantic_consistency=quality["stability_score"],
                causal_alignment=quality["semantic_alignment"],
                metadata={
                    "origin": "epistemic_trial_engine",
                    "trait_state": trait.get(
                        "trait_state",
                        "emerging",
                    ),
                },
            )
        )
        strength = self.belief_strength_model.evaluate(
            aggregate,
            trial.trial_result.value,
        )
        causal_attestation = self.causal_attestation_engine.evaluate(
            concept,
            aggregate,
            self.evidence_accumulator.registry.evidence_for(
                concept,
            ),
            self.evidence_accumulator.registry.epistemic_partition(
                concept,
            ),
        )
        contradiction_resolution = (
            self.contradiction_resolution_engine.evaluate(
                concept,
                aggregate,
                self.evidence_accumulator.registry.evidence_for(
                    concept,
                ),
                self.evidence_accumulator.registry.effective_evidence_weight,
                self.evidence_accumulator.registry.epistemic_partition(
                    concept,
                ),
            )
        )
        return {
            "concept": concept,
            "trait_state": trait.get("trait_state", "emerging"),
            "trial": trial.as_dict(),
            "trial_resolution":
            self.trial_engine.latest_resolution(concept),
            "causal_attestation":
            causal_attestation,
            "contradiction_resolution":
            contradiction_resolution,
            "aggregate": aggregate.as_dict(),
            "semantic_observation_count":
            accumulation[
                "semantic_observation_count"
            ],
            "execution_validation_count":
            accumulation[
                "execution_validation_count"
            ],
            "belief_strength_model": strength,
            "eligible_for_extinction_grace": (
                trial.trial_result.value != "FAILED"
                and aggregate.evidence_count > 0
            ),
            "survival_is_not_truth": True,
        }

    def report(self):
        resolutions = [
            item
            for items in self.trial_engine.resolution_history.values()
            for item in items
        ]
        return {
            "system": "epistemic_trial_engine",
            "evidence_accumulator": self.evidence_accumulator.report(),
            "trialled_concept_count": len(
                self.trial_engine.trial_history,
            ),
            "trial_count": sum(
                len(items)
                for items in self.trial_engine.trial_history.values()
            ),
            "stalled_inconclusive_concepts": sorted({
                item["concept"]
                for item in resolutions
                if item["stalled_inconclusive_pattern"]
            }),
            "survival_is_not_truth": True,
        }


epistemic_trial_engine = EpistemicTrialEngine()
