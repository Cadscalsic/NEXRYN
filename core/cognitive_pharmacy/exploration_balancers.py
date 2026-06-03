class ExplorationBalancers:

    medication_id = "EXPLORATION_BALANCER"

    def protocol(self):

        return {
            "medication_id": self.medication_id,
            "purpose": "prevent_over_stabilization_and_evolution_paralysis",
        }
