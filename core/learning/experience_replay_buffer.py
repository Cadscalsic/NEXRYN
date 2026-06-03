class ExperienceReplayBuffer:
    def __init__(self, maximum_size=256):
        self.maximum_size = max(int(maximum_size), 1)
        self._experiences = []
        self._signatures = set()

    def _signature(self, experience):
        return (
            experience.get("experiment_id"),
            experience.get("generated_task_id"),
            experience.get("task_id"),
        )

    def add(self, experience):
        experience = dict(experience or {})
        signature = self._signature(experience)
        if signature in self._signatures:
            return False
        self._signatures.add(signature)
        self._experiences.append(experience)
        self._experiences = self._experiences[-self.maximum_size:]
        return True

    def add_many(self, experiences):
        return sum(self.add(item) for item in experiences or [])

    def replay(self, concept=None, limit=10):
        experiences = [
            item
            for item in self._experiences
            if concept is None or item.get("concept") == concept
        ]
        return experiences[-max(int(limit), 0):]

    def report(self):
        return {
            "system": "experience_replay_buffer",
            "learning_phase": "7-prelude",
            "experience_count": len(self._experiences),
            "synthetic_experience_count": sum(
                item.get("synthetic_sandbox_probe", False)
                for item in self._experiences
            ),
            "independent_experience_count": sum(
                item.get("independent_experience", False)
                for item in self._experiences
            ),
            "synthetic_experiences_are_not_independent": True,
        }


__all__ = [
    "ExperienceReplayBuffer",
]
