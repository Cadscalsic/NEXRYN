class CognitiveSleepAgents:

    medication_id = "COGNITIVE_SLEEP_AGENT"

    def protocol(self):

        return {
            "medication_id": self.medication_id,
            "sleep_states": [
                "light_recovery",
                "deep_consolidation",
                "emergency_stabilization_sleep",
                "trauma_recovery_sleep",
            ],
        }
