from core.epistemic_models import EpistemicTrial, Hypothesis, TrialResult
from runtime.trial_resolution_engine import TrialResolutionEngine


class EpistemicTrialEngine:
    def __init__(self, evidence_registry):
        self.evidence_registry = evidence_registry
        self.trial_history = {}
        self.resolution_history = {}
        self.resolution_engine = TrialResolutionEngine()

    def run_trial(self, hypothesis):
        if isinstance(hypothesis, dict):
            hypothesis = Hypothesis(**hypothesis)
        aggregate = self.evidence_registry.aggregate(hypothesis.concept)
        trial_number = len(self.trial_history.get(hypothesis.concept, [])) + 1

        resolution = self.resolution_engine.resolve(
            aggregate,
            self.trial_history.get(hypothesis.concept, []),
        )
        result = TrialResult(resolution["trial_result"])

        trial = EpistemicTrial(
            concept=hypothesis.concept,
            support_score=aggregate.support_score,
            contradiction_score=aggregate.contradiction_score,
            evidence_strength=aggregate.evidence_strength,
            semantic_consistency=aggregate.semantic_consistency,
            causal_alignment=aggregate.causal_alignment,
            trial_result=result,
            evidence_count=aggregate.evidence_count,
            trial_number=trial_number,
        )
        self.trial_history.setdefault(hypothesis.concept, []).append(trial)
        self.resolution_history.setdefault(
            hypothesis.concept,
            [],
        ).append(resolution)
        return trial

    def trials_for(self, concept):
        return list(self.trial_history.get(concept, []))

    def resolutions_for(self, concept):
        return list(self.resolution_history.get(concept, []))

    def latest_resolution(self, concept):
        resolutions = self.resolutions_for(concept)
        return resolutions[-1] if resolutions else {}
