from core.epistemic_models import Belief, BeliefState, utcnow


class BeliefRegistry:
    def __init__(self):
        self.registry = {}

    def get_or_create(self, concept, claim=None):
        belief = self.registry.get(concept)
        if belief is None:
            belief = Belief(
                concept=concept,
                claim=claim or concept,
            )
            self.registry[concept] = belief
        return belief

    def beliefs(self):
        return list(self.registry.values())

    def revoke(self, concept):
        belief = self.registry[concept]
        belief.state = BeliefState.REJECTED
        belief.updated_at = utcnow()
        return belief

    def archive(self, concept):
        belief = self.registry[concept]
        belief.state = BeliefState.ARCHIVED
        belief.updated_at = utcnow()
        return belief

    def report(self):
        return {
            "system": "belief_registry",
            "belief_count": len(self.registry),
            "beliefs": [
                belief.as_dict()
                for belief in self.beliefs()
            ],
        }
