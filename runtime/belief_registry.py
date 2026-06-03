from core.belief_registry import BeliefRegistry as CoreBeliefRegistry


class BeliefRegistry(CoreBeliefRegistry):
    def report(self):
        report = super().report()
        report.update({
            "system": "runtime_belief_registry",
            "registry_policy":
            "belief_birth_requires_evidence_and_epistemic_trial",
        })
        return report


belief_registry = BeliefRegistry()
