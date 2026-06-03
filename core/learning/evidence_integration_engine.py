class LearningEvidenceIntegrationEngine:
    def __init__(self, replay_buffer):
        self.replay_buffer = replay_buffer

    def record(self, integrated_evidence):
        recorded = self.replay_buffer.add_many(
            {
                **item,
                "experience_class": (
                    "measured_synthetic_probe"
                    if item.get("metadata", {}).get(
                        "synthetic_sandbox_probe",
                        False,
                    )
                    else "measured_sandbox_experience"
                ),
                "synthetic_sandbox_probe":
                item.get("metadata", {}).get(
                    "synthetic_sandbox_probe",
                    False,
                ),
                "generated_task_id":
                item.get("metadata", {}).get("generated_task_id"),
                "independent_experience": False,
            }
            for item in integrated_evidence or []
        )
        return {
            "system": "learning_evidence_integration_engine",
            "learning_phase": "7-prelude",
            "recorded_experience_count": recorded,
            "experience_replay_buffer": self.replay_buffer.report(),
            "synthetic_experiences_are_not_independent": True,
            "automatic_truth_promotion_forbidden": True,
        }


__all__ = [
    "LearningEvidenceIntegrationEngine",
]
